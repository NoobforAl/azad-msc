# 03 — Quiz: Concurrency & Synchronization

> 15 questions: 6 conceptual (40%), 5 read-the-code-or-output (≈30%), 4 debug/design (≈30%), then 3 oral-exam questions. Answers are at the end. Farsi: [`quiz.fa.md`](quiz.fa.md).
> Code excerpts are from Linux **v6.18.63**; outputs are real runs on `aos-lab` (Linux 6.18.63, 8 vCPU VirtualBox guest, 2026-11-15).

## Conceptual

**Q1.** Define *race condition*, *data race* and *critical section*. Give an example of a race condition that is **not** a data race.

**Q2.** A producer writes `data = 42;` then sets `ready = 1;`. A consumer spins `while (!ready);` then reads `data`. Using C11 atomics, which memory orders are needed on `ready` (store and load) and why is `relaxed` not enough even on a machine where it happens to work?

**Q3.** Which of these reorderings can another CPU observe on x86-64? (a) store→store (b) load→load (c) store→later load of a different address (d) load→later store. Name the hardware structure responsible.

**Q4.** Give three reasons why the kernel's `spin_lock()` must not be held across a call that can sleep, and say what `__raw_spin_lock()` does before touching the lock word and why.

**Q5.** In RCU, what is a *grace period* and what is a *quiescent state*? Why can a writer free the old version after `synchronize_rcu()` returns even though readers took no lock?

**Q6.** State the four Coffman conditions. For each, give one practical technique that breaks it, and say which one lockdep is designed to catch.

## Read the code / output

**Q7.** Explain every line:

```c
// linux/kernel/locking/mutex.c · __mutex_trylock_fast() · v6.18.63 · L150-161
static __always_inline bool __mutex_trylock_fast(struct mutex *lock)
{
	unsigned long curr = (unsigned long)current;
	unsigned long zero = 0UL;

	MUTEX_WARN_ON(lock->magic != lock);

	if (atomic_long_try_cmpxchg_acquire(&lock->owner, &zero, curr))
		return true;

	return false;
}
```

Why can `__mutex_unlock_fast()` fail even when the caller really owns the mutex?

**Q8.** Why is `queued_spin_unlock()` a plain store and not an atomic RMW? What would break if it used `WRITE_ONCE()` (no release ordering) on a weakly ordered CPU?

```c
// linux/include/asm-generic/qspinlock.h · queued_spin_unlock() · v6.18.63 · L123-129
static __always_inline void queued_spin_unlock(struct qspinlock *lock)
{
	/*
	 * unlock() needs release semantics:
	 */
	smp_store_release(&lock->locked, 0);
}
```

**Q9.** Lab 04 printed (real run, aos-lab):

```
$ sudo bpftrace futex-ops.bt -c './futex_mutex 4 200000'
threads=4 counter=800000 expected=800000 OK futex_wait=6680 futex_wake=8949
@calls[9]: 3
@calls[0]: 6680
@calls[1]: 8949
@usecs[0]:
[0]                 6559 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[1]                   26 |                                                    |
...
[64, 128)             32 |                                                    |
[128, 256)            15 |                                                    |
...
[8K, 16K)              1 |                                                    |
```

(a) What are ops 0, 1 and 9, and who issued op 9? (b) 98% of the FUTEX_WAIT calls took under 1 µs. Did those threads sleep? Which lines of `futex_wait_setup()` explain it? (c) Why are there more WAKEs than WAITs? (d) The same program under `strace -f -c` reported `futex_wait=0` in its own counters. Why?

**Q10.** `futex_wait_setup()` takes the hash-bucket lock **before** reading the user word, and the comment says *"If we locked the hash-bucket after testing \*uaddr, that would open a race condition where we could block indefinitely"*. Draw the bad interleaving (waiter and waker, 2 CPUs) that this prevents. Then explain how `futex_wake()` can still skip the lock entirely when `!futex_hb_waiters_pending(hb)`.

**Q11.** Explain this real ThreadSanitizer report from lab 01. Why does TSan report a race in a run whose result was correct (`lost=0`)? Name two different fixes and say which one TSan would still flag if you only made `g_plain` `volatile`.

```
$ ./race-tsan race 2 1000
WARNING: ThreadSanitizer: data race (pid=4446)
  Read of size 8 at 0x55912d33b070 by thread T2:
    #0 worker .../01-data-race/race.c:33 (race-tsan+0x1470)
  Previous write of size 8 at 0x55912d33b070 by thread T1:
    #0 worker .../01-data-race/race.c:33 (race-tsan+0x1483)
  Location is global 'g_plain' of size 8 at 0x55912d33b070 (race-tsan+0x4070)
...
SUMMARY: ThreadSanitizer: data race .../01-data-race/race.c:33 in worker
mode=race   threads=2 expected=2000 got=2000 lost=0 time=1.391s ns/inc=695728.7
```

## Debug / design

**Q12.** A service hangs. You capture (real lab 06 output):

```
$ ps -L -o pid,lwp,stat,wchan:20,comm -p 27823
    PID     LWP STAT WCHAN                COMMAND
  27823   27826 Sl   futex_do_wait        deadlock
  27823   27827 Sl   futex_do_wait        deadlock
$ sudo gdb -p 27823 -batch -ex "thread apply all bt"
Thread 3 (Thread 0x7c4ab39ff6c0 (LWP 27826) "deadlock"):
#0  futex_wait (private=0, expected=2, futex_word=0x646ef2c58020 <g_acc_b>) ...
#4  transfer (from=...0x646ef2c58060 <g_acc_a>, to=...0x646ef2c58020 <g_acc_b>, amount=10) at deadlock.c:39
#5  a_to_b (arg=<optimized out>) at deadlock.c:49
Thread 2 (Thread 0x7c4ab31fe6c0 (LWP 27827) "deadlock"):
#0  futex_wait (private=0, expected=2, futex_word=0x646ef2c58060 <g_acc_a>) ...
#4  transfer (from=...0x646ef2c58020 <g_acc_b>, to=...0x646ef2c58060 <g_acc_a>, amount=20) at deadlock.c:39
#5  b_to_a (arg=<optimized out>) at deadlock.c:56
```

What happened? Which line in which function holds which lock? Is the process consuming CPU? Propose a fix that does not change the API of `transfer()`, and a tool that would have found the bug in CI on a run that does not hang.

**Q13.** Lab 03 printed:

```
pref=reader readers=4 secs=3 reads=161806 writes=0 (+1 after stop) writer_wait max=4.281s avg=4.281458s
pref=writer readers=4 secs=3 reads=270250 writes=188 (+1 after stop) writer_wait max=0.036s avg=0.003488s
```

Explain the numbers. Design two different fixes and give one cost of each.

**Q14.** A colleague's bounded buffer works with 1 producer and 1 consumer but corrupts data with 2 consumers. The consumer is:

```c
pthread_mutex_lock(&m);
if (count == 0)
    pthread_cond_wait(&not_empty, &m);
v = buf[tail]; tail = (tail + 1) % CAP; count--;
pthread_cond_signal(&not_full);
pthread_mutex_unlock(&m);
```

Give the exact interleaving that breaks it and the one-word fix. Why must the mutex be passed to `pthread_cond_wait`?

**Q15.** You implement Dekker/Peterson-style mutual exclusion for two threads with `flag[me] = 1; turn = other; while (flag[other] && turn == other);` using relaxed atomics, and lab 05 shows how it fails on x86. Where exactly must a fence go, what does gcc emit for it on x86-64, and what does it cost compared with using a `lock cmpxchg` lock?

## Oral exam

**O1.** "Linux's mutex spins, so it is really a spinlock." Defend or refute, using `mutex_spin_on_owner()` and `osq_lock()`.

**O2.** Compare Linux RCU's grace-period detection with OpenBSD's `smr_grace_wait()`. Which scales better to 512 CPUs and why? Which is easier to prove correct?

**O3.** Why does the futex protocol need the user-space word to be re-checked by the kernel at all? Could a design with only `FUTEX_SLEEP` (no value) and `FUTEX_WAKE` work? Relate your answer to lost wake-ups and condition variables.

---

## Answers

**A1.** Race condition: the outcome depends on relative timing (a *semantic* property). Data race: two concurrent accesses to the same location, at least one a write, not ordered by synchronization (a *language* property; UB in C11). Critical section: code that accesses shared state and must be mutually excluded. Race but not data race: two threads each do `lock; x = read(); unlock; lock; write(x + 1); unlock` — every access is locked, yet an update can be lost because the read-modify-write spans two critical sections (a check-then-act / TOCTOU race).

**A2.** Store `ready` with `memory_order_release`, load it with `memory_order_acquire`. The release store makes all earlier writes (`data = 42`) visible to any thread whose acquire load reads `ready == 1` (synchronizes-with → happens-before). With `relaxed` the compiler may reorder the two stores or hoist the `data` load, and Arm/POWER may reorder them in hardware. On x86 it often "works" because TSO keeps store→store and load→load order, but the compiler still may reorder, and the program has a data race on `data` = UB. Lab 05's `mp.c` shows the forbidden outcome never appears on x86 — that is luck of the hardware, not correctness.

**A3.** Only (c). Each core has a FIFO **store buffer**; a store sits there while later loads to other addresses read from cache, so the store becomes globally visible after the load. Store→store, load→load and load→store order are preserved by x86-TSO. Lab 05 measures (c); `mfence`, any `lock`-prefixed instruction or `xchg` drains the buffer.

**A4.** (1) The holder would be scheduled out while other CPUs spin for the whole time — wasted CPUs and possibly a deadlock if the waiter is on the same CPU with preemption off; (2) spinlocks may be taken in interrupt context, which can never sleep; (3) sleeping with preemption disabled triggers "BUG: scheduling while atomic" and breaks RCU-sched quiescent-state accounting. `__raw_spin_lock()` calls `preempt_disable()` first (`spinlock_api_smp.h` L132) so the holder cannot be preempted on its own CPU while others spin on the lock, then informs lockdep (`spin_acquire`), then takes the lock.

**A5.** Grace period: an interval during which every pre-existing RCU reader finishes. Quiescent state: a point at which a CPU (or task) is guaranteed not to be inside a reader — context switch, idle, user mode; with preemptible RCU, a preempted reader is tracked on `blkd_tasks` until its outermost `rcu_read_unlock()`. After `rcu_assign_pointer()`, new readers can only see the new version; once every CPU has passed a quiescent state, no reader that could hold the old pointer remains, so freeing it is safe.

**A6.** Mutual exclusion → make the resource shareable (RCU readers, lock-free data); hold-and-wait → acquire all locks at once or `trylock` and back off; no preemption → allow lock stealing/abort (`ww_mutex` wound/wait, transaction rollback); circular wait → a global lock order (by address, by lock class level). Lockdep checks circular wait: it records "A held while acquiring B" edges per lock *class* and reports any edge that would close a cycle (`check_noncircular()`, `lockdep.c` L2176).

**A7.** L152: the owner word holds the `task_struct *` of the holder. L153: expected value is exactly 0 (unlocked, no flags). L155: debug sanity check (compiles away without `CONFIG_DEBUG_MUTEXES`). L157: one `lock cmpxchg`: if owner == 0 store `current`, with **acquire** ordering so the critical section cannot move above it; on success the lock is taken with no further work. L160: otherwise the caller goes to `__mutex_lock_slowpath()`. `__mutex_unlock_fast()` does `cmpxchg_release(owner, current → 0)`; it fails when any flag bit is set — `MUTEX_FLAG_WAITERS` (someone is queued), `HANDOFF` or `PICKUP` — so the slow path must wake/hand off to a waiter.

**A8.** Only the owner writes `locked` on unlock, and x86 (and every Linux arch) makes an aligned byte store atomic, so no RMW is needed; the other bits (pending, tail) are left untouched because `locked` is a separate byte. The **release** ordering guarantees that all loads and stores of the critical section are visible before the lock appears free. With a plain `WRITE_ONCE` on Arm64/POWER, a store from inside the critical section could become visible after the unlock, so the next owner would read stale data. On x86 `smp_store_release` compiles to a compiler barrier plus `mov`, because TSO already orders it.

**A9.** (a) `op & 127`: 0 = `FUTEX_WAIT`, 1 = `FUTEX_WAKE` (from our mutex), 9 = `FUTEX_WAIT_BITSET`, issued by glibc's `pthread_join` in `main` (3 calls, 3 joins that had to wait). (b) No. They returned `EAGAIN` immediately: `futex_wait_setup()` locks the bucket, re-reads the word (L632) and returns `-EWOULDBLOCK` when it is no longer 2 (L647–649), i.e. the lock was released between the user-space `xchg` and the syscall. Only the 64 µs–16 ms tail actually slept. (c) The unlocker sees state 2 and issues a WAKE even when the contender has already taken the lock in user space or not yet slept; state 2 is sticky because a woken thread re-locks with `xchg 2`. (d) `strace` uses ptrace: every thread stops at every syscall (including `clone`), so the threads barely overlap and the lock is never contended. Tracing changed the experiment; bpftrace does not stop the threads.

**A10.** Bad interleaving if the kernel read the word first: waiter reads `*uaddr == 2` (decides to sleep) → waker stores 0 and calls `futex_wake()`, finds the bucket empty, returns → waiter takes the bucket lock, queues itself, sleeps forever. Taking the lock first means the waker either runs before (and the waiter sees the changed value → `-EWOULDBLOCK`) or after the waiter is queued (and wakes it). The lockless `futex_wake()` check is safe because of the barrier pair in the file's top comment: waiter `waiters++; smp_mb(); read *futex` vs waker `*futex = new; smp_mb(); read waiters` — the store-buffering pattern, where the two full barriers make `waiters == 0 && futex == old` impossible.

**A11.** Two accesses to the same 8 bytes (`g_plain`), at least one a write (the *previous write* by T1), from different threads (T1, T2), with no happens-before between them: a data race, both at `race.c:33` (`g_plain++`). TSan tracks happens-before with vector clocks, so it detects the *missing synchronization*, not a wrong result; a correct-looking run is still undefined behaviour. Fixes: wrap the increment in `pthread_mutex_lock/unlock` (lock/unlock create happens-before edges), or make it `atomic_fetch_add` (atomic accesses never race). `volatile` alone is still flagged: it is not an atomic and creates no ordering.

**A12.** An AB-BA deadlock. LWP 27826 runs `a_to_b` → `transfer(A, B)`: it holds `g_acc_a` (taken at line 36) and waits at line 39 for `g_acc_b`. LWP 27827 runs `b_to_a` → `transfer(B, A)`: it holds `g_acc_b` and waits at line 39 for `g_acc_a`. `expected=2` is glibc's "locked with waiters" state. All threads are in state `S` in `futex_do_wait`: no CPU is consumed; it is not a livelock. Fix inside `transfer()`: always lock the two accounts in a global order, e.g. lower address first (lab 06 `ordered`), or `trylock` the second and back off. CI: ThreadSanitizer (`lock-order-inversion`) or helgrind (`lock order ... violated`) on any run that takes both orders, even sequentially.

**A13.** glibc's default rwlock prefers readers: a new reader is admitted while a writer waits, and four overlapping 100 µs readers keep the read count above zero forever. So the writer gets in **0 times** during the run and its single write happens after the readers stop (wait 4.3 s for a 3 s run): writer starvation, the first readers-writers problem. With `PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP` new readers block while a writer waits: 188 writes, max wait 36 ms. Fix 1: writer-preferring lock — cost: readers wait more, and recursive read locking can deadlock. Fix 2: a fair/turnstile lock (FIFO between readers and writers, lab 03 extension) — cost: extra synchronization per read section (lower read throughput). Fix 3 (design): RCU-style publish so readers take no lock — cost: copies and deferred freeing.

**A14.** Interleaving: buffer empty; C1 and C2 both wait. Producer puts one item and signals → C1 is woken but, before it reacquires the mutex, C2 (which just arrived, or was also woken, or wakes spuriously) takes the mutex, sees `count == 1`, consumes the item. C1 then returns from `pthread_cond_wait` holding the mutex, does **not** re-check `count`, and reads `buf[tail]` from an empty buffer and drives `count` to −1. Fix: `if` → `while`. The mutex is passed so that "check predicate, then sleep" is atomic with respect to the signaller: `pthread_cond_wait` releases the mutex and enqueues the waiter in one step (glibc implements it on a futex), so a `signal` between the check and the sleep cannot be lost.

**A15.** Peterson needs the store to `flag[me]` (and `turn`) to be visible before the load of `flag[other]`: that is exactly the store→load order x86 does **not** guarantee, so put `atomic_thread_fence(memory_order_seq_cst)` between the stores and the spin loop (or make all of them `seq_cst`). gcc 13 on x86-64 emits a locked no-op on the stack (`lock orq $0x0,(%rsp)`, see lab 05 disassembly) — a full barrier that drains the store buffer, tens of cycles. A `lock cmpxchg` lock costs about the same (it is also a full barrier) and is simpler and works for N threads, which is why real locks use RMW instructions instead of Peterson.

**O1 (key points).** Spinning is only the optimistic phase: it runs only while the owner is on a CPU and the spinner has no `need_resched()`, only one task spins at a time (`osq_lock`, an MCS queue), and anyone who cannot spin goes to a FIFO `wait_list` and sleeps in `schedule_preempt_disabled()`. The holder may sleep; spinlock holders may not. It is an *adaptive* mutex.

**O2 (key points).** Linux: per-CPU quiescent-state reports aggregated up a tree of `rcu_node`s by `rcu_gp_kthread`; no thread migration, cost O(log N) contention, supports preemptible readers and expedited GPs. OpenBSD: one thread pegs itself to each CPU in turn (`sched_peg_curproc`), O(N) sequential migrations per GP, simple and obviously correct for non-sleeping readers. Linux scales better; SMR is easier to verify.

**O3 (key points).** Without the value check, a waiter could decide to sleep, then the unlocker releases and wakes nobody, then the waiter sleeps forever — the lost wake-up. The value is the condition, checked atomically under the bucket lock. A value-less sleep would need an extra lock around "check + sleep", which is what condition variables do with their mutex; the futex embeds that check into the syscall instead.
