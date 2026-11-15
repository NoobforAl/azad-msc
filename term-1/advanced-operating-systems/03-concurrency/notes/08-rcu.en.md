# 08 — RCU: readers with no lock at all

> Module 03 · Concurrency & Synchronization · Linux v6.18.63 · OpenBSD 8cada8c · Farsi: [08-rcu.fa.md](08-rcu.fa.md)

## 1. Summary

- **RCU** (Read-Copy-Update) lets readers traverse shared data with **no locks, no atomic RMW, and no writes to shared memory**; writers publish a new copy and free the old one later.
- "Later" = after a **grace period**: every CPU has passed a **quiescent state** (e.g. a context switch), so no reader can still hold a pointer to the old copy.
- It fits read-mostly data (routing tables, the dentry cache, `task_struct` lists, module lists). OpenBSD's equivalent is **SMR**.

## 2. Explanation

### 2.1 Intuition: why a reader-writer lock is not enough

A `rwlock` lets readers run in parallel, but every `read_lock()` still **writes** the lock word (a reader counter). On 64 CPUs, that cache line bounces between all readers; the "parallel" readers serialize on the cache-coherence protocol. RCU removes the shared write from the read side entirely.

### 2.2 The three pieces

| Piece | Who | Linux API | What it guarantees |
|---|---|---|---|
| **Publish** | writer | `rcu_assign_pointer(p, new)` | `new`'s fields are visible before `p` points to it (release store) |
| **Subscribe** | reader | `rcu_read_lock()`; `q = rcu_dereference(p)`; ...; `rcu_read_unlock()` | reads through `q` see the initialized object; the object will not be freed until unlock |
| **Reclaim** | writer | `synchronize_rcu()` (blocks) or `call_rcu(head, fn)` (callback) | waits until all readers that **might** have seen the old pointer are done |

The writer's sequence for an update:

1. Allocate `new`, copy `old`, modify `new` (**copy**).
2. `rcu_assign_pointer(gp, new)` (**update**: new readers now see `new`).
3. `synchronize_rcu()` — wait one grace period. Pre-existing readers may still be using `old`.
4. `kfree(old)` — safe: no reader can reach it.

Writers still need mutual exclusion **among themselves** (usually a spinlock or mutex). RCU only removes the reader/writer conflict.

### 2.3 Grace periods and quiescent states

A **quiescent state** for a CPU is any point where it is certainly not inside an RCU read-side critical section. For classic (non-preemptible) RCU, `rcu_read_lock()` just disables preemption, so a **context switch** on a CPU proves that any reader on that CPU has finished. A grace period ends when every CPU has reported at least one quiescent state since the grace period began. The kernel tracks this in a tree of `rcu_node` structures (`kernel/rcu/tree.c`) so that 1000s of CPUs do not all touch one counter.

### 2.4 Preemptible RCU

With `CONFIG_PREEMPT_RCU` (`default y if (PREEMPT || PREEMPT_RT || PREEMPT_DYNAMIC)` in `kernel/rcu/Kconfig` L19–21; check `grep PREEMPT_RCU /boot/config-$(uname -r)`), a reader may be **preempted** inside `rcu_read_lock()`. A context switch is then not proof of anything. Instead:

- `rcu_read_lock()` increments a per-task counter `current->rcu_read_lock_nesting`;
- if the task is switched out with a non-zero counter, `rcu_note_context_switch()` puts it on the `rcu_node`'s `blkd_tasks` list;
- the grace period cannot end until that list drains, i.e. until the preempted reader calls its outermost `rcu_read_unlock()`.

### 2.5 Why `rcu_dereference()` exists

On x86 a plain load would work. On Alpha, a CPU could load `p` and then load a **stale** `p->field`. `rcu_dereference()` is a `READ_ONCE()` that also documents the address dependency and lets lockdep/sparse check that you are inside a read-side section (`include/linux/rcupdate.h` L529–535, `__rcu_dereference_check`). It also stops the compiler from re-loading `p` twice.

## 3. Diagram

```mermaid
sequenceDiagram
  participant R1 as Reader on CPU0
  participant W as Writer on CPU1
  participant R2 as Reader on CPU2
  R1->>R1: rcu_read_lock(); q = rcu_dereference(gp) (old)
  W->>W: new = copy(old); modify new
  W->>W: rcu_assign_pointer(gp, new)
  R2->>R2: rcu_read_lock(); q = rcu_dereference(gp) (new)
  W->>W: synchronize_rcu() ... waiting
  R1->>R1: use old; rcu_read_unlock()
  Note over R1: context switch = quiescent state
  Note over R2: R2 started after publish, it is not waited for
  W->>W: grace period over: kfree(old)
```

## 4. Worked example

### 4.1 Publish: `rcu_assign_pointer()`

`linux/include/linux/rcupdate.h · rcu_assign_pointer() · v6.18.63` — [L588](https://elixir.bootlin.com/linux/v6.18.63/source/include/linux/rcupdate.h#L588)

```c
  588  #define rcu_assign_pointer(p, v)					      \
  589  do {									      \
  590  	uintptr_t _r_a_p__v = (uintptr_t)(v);				      \
  591  	rcu_check_sparse(p, __rcu);					      \
  592  									      \
  593  	if (__builtin_constant_p(v) && (_r_a_p__v) == (uintptr_t)NULL)	      \
  594  		WRITE_ONCE((p), (typeof(p))(_r_a_p__v));		      \
  595  	else								      \
  596  		smp_store_release(&p, RCU_INITIALIZER((typeof(p))_r_a_p__v)); \
  597  } while (0)
```

- L591: sparse check that `p` is annotated `__rcu`.
- L593–594: storing `NULL` publishes no data, so no ordering is needed: a plain `WRITE_ONCE`.
- L596: otherwise a **release store**: all earlier writes (the new object's fields) are visible before the pointer. On x86-64 this is a plain `mov` plus a compiler barrier, because TSO already orders store→store (ARCH-SPECIFIC; see [note 03](03-x86-tso-and-barriers.en.md)).

### 4.2 Read side: almost nothing

`linux/include/linux/rcupdate.h · rcu_read_lock() · v6.18.63` — [L863](https://elixir.bootlin.com/linux/v6.18.63/source/include/linux/rcupdate.h#L863)

```c
  863  static __always_inline void rcu_read_lock(void)
  864  {
  865  	__rcu_read_lock();
  866  	__acquire(RCU);
  867  	rcu_lock_acquire(&rcu_lock_map);
  868  	RCU_LOCKDEP_WARN(!rcu_is_watching(),
  869  			 "rcu_read_lock() used illegally while idle");
  870  }
  871  
  872  /*
  873   * So where is rcu_write_lock()?  It does not exist, as there is no
  874   * way for writers to lock out RCU readers.  This is a feature, not
  875   * a bug -- this property is what provides RCU's performance benefits.
```

- L865: the real work (below). L866: sparse annotation only. L867–869: lockdep bookkeeping; compiled out without `CONFIG_DEBUG_LOCK_ALLOC`.
- L872–875: the design statement. Writers cannot exclude readers; they can only **wait for them**.

With preemptible RCU, `__rcu_read_lock()` is: `linux/kernel/rcu/tree_plugin.h · __rcu_read_lock() · v6.18.63` — [L412](https://elixir.bootlin.com/linux/v6.18.63/source/kernel/rcu/tree_plugin.h#L412)

```c
  412  void __rcu_read_lock(void)
  413  {
  414  	rcu_preempt_read_enter();
  415  	if (IS_ENABLED(CONFIG_PROVE_LOCKING))
  416  		WARN_ON_ONCE(rcu_preempt_depth() > RCU_NEST_PMAX);
  417  	if (IS_ENABLED(CONFIG_RCU_STRICT_GRACE_PERIOD) && rcu_state.gp_kthread)
  418  		WRITE_ONCE(current->rcu_read_unlock_special.b.need_qs, true);
  419  	barrier();  /* critical section after entry code. */
  420  }
```

- L414: `rcu_preempt_read_enter()` (L389–391) is `current->rcu_read_lock_nesting++` — a write to **the task's own** memory, never to a shared cache line.
- L415–418: debug options only.
- L419: compiler barrier so the critical section's loads are not hoisted above the increment. No CPU fence.

### 4.3 A reader that gets preempted

`linux/kernel/rcu/tree_plugin.h · rcu_note_context_switch() · v6.18.63` — [L324](https://elixir.bootlin.com/linux/v6.18.63/source/kernel/rcu/tree_plugin.h#L324)

```c
  324  void rcu_note_context_switch(bool preempt)
  325  {
  326  	struct task_struct *t = current;
  327  	struct rcu_data *rdp = this_cpu_ptr(&rcu_data);
  328  	struct rcu_node *rnp;
  329  
  330  	trace_rcu_utilization(TPS("Start context switch"));
  331  	lockdep_assert_irqs_disabled();
  332  	WARN_ONCE(!preempt && rcu_preempt_depth() > 0, "Voluntary context switch within RCU read-side critical section!");
  333  	if (rcu_preempt_depth() > 0 &&
  334  	    !t->rcu_read_unlock_special.b.blocked) {
  335  
  336  		/* Possibly blocking in an RCU read-side critical section. */
  337  		rnp = rdp->mynode;
  338  		raw_spin_lock_rcu_node(rnp);
  339  		t->rcu_read_unlock_special.b.blocked = true;
  340  		t->rcu_blocked_node = rnp;
```

- Called from `__schedule()` (Module 02) on every context switch.
- L332: **sleeping** voluntarily inside a read section is a bug (only preemption is allowed).
- L333–340: a preempted reader is marked `blocked` and attached to its CPU's `rcu_node`; the grace period now waits for this task, not for the CPU.

### 4.4 Waiting: `synchronize_rcu()` and `call_rcu()`

`linux/kernel/rcu/tree.c · synchronize_rcu() · v6.18.63` — [L3341](https://elixir.bootlin.com/linux/v6.18.63/source/kernel/rcu/tree.c#L3341)

```c
 3341  void synchronize_rcu(void)
 3342  {
 3343  	unsigned long flags;
 3344  	struct rcu_node *rnp;
 3345  
 3346  	RCU_LOCKDEP_WARN(lock_is_held(&rcu_bh_lock_map) ||
 3347  			 lock_is_held(&rcu_lock_map) ||
 3348  			 lock_is_held(&rcu_sched_lock_map),
 3349  			 "Illegal synchronize_rcu() in RCU read-side critical section");
 3350  	if (!rcu_blocking_is_gp()) {
 3351  		if (rcu_gp_is_expedited())
 3352  			synchronize_rcu_expedited();
 3353  		else
 3354  			synchronize_rcu_normal();
 3355  		return;
 3356  	}
```

- L3346–3349: calling it **inside** a read section would wait for itself: guaranteed deadlock, so lockdep warns.
- L3350: `rcu_blocking_is_gp()` is true only in the early-boot single-CPU case, where any call is trivially a grace period (the code after L3356).
- L3351–3354: normal path; the expedited variant forces quiescent states with IPIs (fast, but disturbs every CPU).

`call_rcu()` ([L3241](https://elixir.bootlin.com/linux/v6.18.63/source/kernel/rcu/tree.c#L3241)) is the non-blocking form: it queues `head` and calls `func(head)` after a grace period, from softirq or an `rcuo` kthread. It is one line: `__call_rcu_common(head, func, enable_rcu_lazy)`; "lazy" callbacks may be batched for power saving (VERSION-DEPENDENT, `CONFIG_RCU_LAZY`).

### 4.5 Seeing it on a machine

```bash
ps -eo pid,comm | grep -E 'rcu_(preempt|sched)|rcuo'   # grace-period kthread + offload threads
grep -E 'PREEMPT_RCU|TREE_RCU|RCU_LAZY' /boot/config-$(uname -r)
sudo bpftrace -e 'kprobe:synchronize_rcu { @[comm] = count(); }'  # who waits for grace periods
```

The output depends on the kernel config; run it on the VM and compare with your `uname -v` (the Kconfig default makes `PREEMPT_DYNAMIC` kernels build preemptible RCU; on aos-lab the grep returns `CONFIG_PREEMPT_RCU=y` and `CONFIG_PREEMPT_DYNAMIC=y`, verified 2026-11-15).

## 5. Edge cases & pitfalls

| Pitfall | Consequence | Rule |
|---|---|---|
| Sleeping in `rcu_read_lock()` section | grace period stalls; "RCU stall" warnings | use SRCU (`srcu_read_lock()`) if you must sleep |
| `synchronize_rcu()` while holding a lock that readers need | readers can't finish → deadlock | call it after dropping the lock, or use `call_rcu()` |
| Using the pointer after `rcu_read_unlock()` | use-after-free | take a reference (`refcount_inc_not_zero`) inside the section |
| Two `rcu_dereference()` calls of the same pointer | can see two different versions | load once into a local |
| Writer-heavy data | every update copies + waits | use a lock; RCU is for read-mostly |
| `synchronize_rcu()` in a hot loop | each call blocks ~ms | batch with `call_rcu()` or `kfree_rcu()` |
| Expecting readers to see the update immediately | old readers keep the old copy | RCU gives **consistency per object**, not instant global visibility |

## 6. Exam key points

- RCU = publish (release store) + subscribe (dependency-ordered load) + wait for a grace period before reclaim.
- Read side: no locks, no atomics, no shared writes; cost ≈ 0 (non-preemptible: preempt_disable; preemptible: per-task counter).
- Grace period ends when every CPU passes a quiescent state; in preemptible RCU, also when every **blocked reader** has left (`blkd_tasks`).
- `synchronize_rcu()` blocks; `call_rcu()` / `kfree_rcu()` defer.
- No `rcu_write_lock()`: writers synchronize with each other by other means.
- Fits read-mostly; does not fit write-heavy or "must see latest" data.
- OpenBSD SMR = same idea; grace period detected by migrating the waiting thread to every CPU.

### OpenBSD comparison: SMR

`openbsd/sys/kern/kern_smr.c · smr_read_enter() · 8cada8c` — [L178](https://github.com/openbsd/src/blob/8cada8c/sys/kern/kern_smr.c#L178)

```c
  178  smr_read_enter(void)
  179  {
  180  #ifdef DIAGNOSTIC
  181  	struct schedstate_percpu *spc = &curcpu()->ci_schedstate;
  182  
  183  	spc->spc_smrdepth++;
  184  #endif
  185  }
```

- The read side is **empty** on a production kernel: SMR readers must not sleep and are not preempted in the kernel, so being on a CPU is enough. The depth counter exists only for `DIAGNOSTIC` assertions.

`openbsd/sys/kern/kern_smr.c · smr_grace_wait() · 8cada8c` — [L146](https://github.com/openbsd/src/blob/8cada8c/sys/kern/kern_smr.c#L146)

```c
  153  	smrgp = READ_ONCE(smr_grace_period) + 1;
  154  	WRITE_ONCE(smr_grace_period, smrgp);
  155  
  156  	curcpu()->ci_schedstate.spc_smrgp = smrgp;
  157  
  158  	CPU_INFO_FOREACH(cii, ci) {
  159  		if (!CPU_IS_RUNNING(ci))
  160  			continue;
  161  		if (READ_ONCE(ci->ci_schedstate.spc_smrgp) == smrgp)
  162  			continue;
  163  		sched_peg_curproc(ci);
  164  		KASSERT(ci->ci_schedstate.spc_smrgp == smrgp);
  165  	}
  166  	sched_unpeg_curproc();
```

- L153–156: announce a new grace-period number; the current CPU is trivially quiescent.
- L161–162: skip CPUs that already recorded this number (an idle CPU records it in `smr_idle()`, L242–245).
- L163: **pin the SMR thread onto that CPU**. To run there, the CPU must context-switch, which ends any reader on it. This is the textbook "wait for each CPU to schedule" RCU, implemented literally.
- `smr_thread()` ([L82](https://github.com/openbsd/src/blob/8cada8c/sys/kern/kern_smr.c#L82)) collects deferred callbacks, sleeps up to `SMR_PAUSE` to batch them, calls `smr_grace_wait()`, then runs every callback (L120–125).

| Design choice | Linux RCU v6.18.63 | OpenBSD SMR 8cada8c | Trade-off |
|---|---|---|---|
| Read-side cost | preempt_disable or per-task counter | nothing (DIAGNOSTIC: counter) | both ≈ free |
| Preemptible readers | yes (`PREEMPT_RCU`, `blkd_tasks`) | no | Linux supports RT/low-latency kernels; OpenBSD keeps it simple |
| Grace-period detection | per-CPU QS reports up an `rcu_node` tree, kthread `rcu_preempt` | one thread migrates to each CPU in turn | tree scales to thousands of CPUs; pegging costs one migration per CPU |
| Expedited GP | IPIs (`synchronize_rcu_expedited`) | `smr_expedite` skips the batching pause | IPIs are fast but disturb all CPUs |
| Callback execution | softirq or offloaded `rcuo` kthreads, lazy batching | single `smr` kthread | Linux spreads load; OpenBSD one serial queue |
| Variants | RCU, SRCU (sleepable), Tasks RCU | SMR only | Linux has more tools, more to learn |
| Code size | `kernel/rcu/tree.c` alone: 4923 lines | `kern_smr.c`: 296 lines | complexity buys scalability |

## 7. Links

- Lesson: [4.6 How can readers run with no lock at all?](../lesson.en.md#46-how-can-readers-run-with-no-lock-at-all)
- Walkthrough: [kernel-walkthrough.en.md](../kernel-walkthrough.en.md) (RCU vs SMR section)
- Related notes: [03 — x86-TSO and barriers](03-x86-tso-and-barriers.en.md) (why `rcu_assign_pointer` is a release store), [04 — spinlocks](04-spinlocks-qspinlock.en.md) (writer-side lock), [09 — deadlock](09-deadlock-coffman-lockdep.en.md) (`synchronize_rcu()` under a lock)
- Lab: [04 — futex mutex](../labs/04-futex-mutex/README.md) (bpftrace workflow reused in 4.5)
- Quiz: [Q5](../quiz.en.md) (grace period)
- Primary sources: P. McKenney, "What is RCU, Fundamentally?" (LWN 262464); `Documentation/RCU/` in the kernel tree
