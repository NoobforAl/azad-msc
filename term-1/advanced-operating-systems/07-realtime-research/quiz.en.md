# 07 — Quiz: Real-Time & Research Topics

15 questions: 6 conceptual (40 %), 5 read-the-code/output (30 %, rounded), 4 debugging/design (30 %), plus 3 oral-exam questions. Answers at the end. Farsi: [`quiz.fa.md`](quiz.fa.md).

## A. Conceptual

**1.** Classify as hard, firm or soft real-time, and justify in one line each: (a) audio playback on a laptop, (b) a car's ABS controller, (c) a radar tracker that discards samples older than one sweep.

**2.** Why is measured WCET on a modern x86 CPU not a proof of a bound? Name two hardware features responsible.

**3.** Task set `τ1 = (C=1, T=4)`, `τ2 = (2, 6)`, `τ3 = (1, 8)`, deadlines = periods. (a) Compute U. (b) Is it schedulable under RMS by the Liu–Layland test? (c) Under EDF?

**4.** Explain, with three tasks, the difference between *bounded* and *unbounded* priority inversion. Which one does priority inheritance remove?

**5.** List three things `PREEMPT_RT` changes compared with a `PREEMPT_DYNAMIC` kernel in `full` mode.

**6.** Why must both seccomp and Landlock require `no_new_privs` (or `CAP_SYS_ADMIN`) before installing restrictions?

## B. Read the code / output

**7.** On the course VM, `cyclictest` under load printed `# Min Latencies: 00032 00031`, `# Avg Latencies: 09389 09364`, `# Max Latencies: 26624226 26624344` (µs, lab 01). What do you report as the result, and what two caveats do you attach?

**8.** In `__dl_overflow()`:

```c
return dl_b->bw != -1 &&
       cap_scale(dl_b->bw, cap) < dl_b->total_bw - old_bw + new_bw;
```

(a) What does `dl_b->bw == -1` mean? (b) What error does `sched_setattr()` return to user space when this function returns true?

**9.** In `task_blocks_on_rt_mutex()`:

```c
if (waiter == rt_mutex_top_waiter(lock)) {
	rt_mutex_dequeue_pi(owner, top_waiter);
	rt_mutex_enqueue_pi(owner, waiter);
	rt_mutex_adjust_prio(lock, owner);
	if (owner->pi_blocked_on)
		chain_walk = 1;
}
```

Why is the boost done only when the new waiter is the *top* waiter, and what case does `owner->pi_blocked_on` handle?

**10.** `uname -v` on two machines prints `#1 SMP PREEMPT_DYNAMIC ...` and `#1 SMP PREEMPT_RT ...`. Using `init/Makefile` L28-30, explain why an RT kernel never prints `PREEMPT_DYNAMIC` last, and how you would check the first machine's current mode.

**11.** `seccomp_run_filters()` loops `for (; f; f = f->prev)` and keeps the result with the lowest `ACTION_ONLY()`. A process has two filters: filter A returns `ALLOW` for `mkdir`, filter B returns `ERRNO(EPERM)`. What happens on `mkdir()`? Could a third filter turn it back into `ALLOW`?

## C. Debugging / design

**12.** A video pipeline uses `SCHED_DEADLINE` with `runtime = 4 ms, deadline = period = 10 ms` per thread on a 4-CPU box. The 10th thread's `sched_setattr()` fails with `EBUSY`. Explain, and give two ways to make room.

**13.** A colleague's RT control loop has a 30 ms spike every few minutes. `perf sched` shows the loop thread blocked on a `pthread_mutex_t` shared with a logging thread at nice 0. Diagnose and fix.

**14.** You sandbox a PDF converter with a seccomp deny-list (`open`, `socket`, `execve` → `KILL_PROCESS`). A pentester still reads `/etc/passwd` and starts a shell. Give two likely reasons and a better design.

**15.** You must review *The Linux Scheduler: a Decade of Wasted Cores* (EuroSys '16) for a reading group. Outline your pass-1 output (five Cs) in five lines and one concrete experiment for pass 3 on v6.18.63.

## D. Oral-exam questions

**O1.** "Linux is now a real-time OS because `PREEMPT_RT` is in mainline." Argue for and against.

**O2.** Compare priority inheritance and priority ceiling. Which would you choose for a safety-certified system, and why does Linux user space default to inheritance?

**O3.** pledge/unveil vs seccomp/Landlock: which design would you rather maintain for ten years, and what does your answer assume about who writes the policy?

---

## Answers

**1.** (a) Soft: a late buffer is a click, quality degrades, nothing fails. (b) Hard: a missed control deadline can cause a crash; must be bounded and certified. (c) Firm: a late sample is discarded (worthless) but occasional misses are tolerated.

**2.** Measurement only shows the worst case observed; there is no guarantee that a rarer path or hardware state doesn't occur. Responsible features: caches (shared L3, eviction by other cores), branch prediction / out-of-order speculation, SMT siblings, DRAM refresh, frequency scaling, SMIs. Static analysis is impractical on such CPUs.

**3.** (a) `U = 1/4 + 2/6 + 1/8 = 0.250 + 0.333 + 0.125 = 0.708`. (b) Bound for n = 3: `3(2^(1/3) − 1) ≈ 0.780`; `0.708 ≤ 0.780` → schedulable under RMS. (c) Yes, `U ≤ 1`.

**4.** L holds a lock; H blocks on it. *Bounded*: H waits at most for L's critical section. *Unbounded*: M (priority between L and H, does not need the lock) preempts L, so H waits for M too, without limit. PI removes the **unbounded** part: L runs at H's priority, so M cannot preempt it; H still waits for the rest of L's critical section.

**5.** Any three of: `spinlock_t`/`rwlock_t`/`local_lock` become sleeping `rt_mutex` locks with PI (only `raw_spinlock_t` spins); all IRQ handlers are forced into threads (`force_irqthreads()` is `true`); softirqs run in thread context with per-CPU local locks; RCU read sides are preemptible; long non-preemptible sections are broken up. It is chosen at compile time and cannot be switched at runtime.

**6.** Both restrictions survive `execve()`. Without `no_new_privs`, an unprivileged user could restrict a **setuid-root** program (e.g. make `setuid()` or a file open fail) and steer it into an unsafe path while it runs with root rights. With NNP, `execve()` cannot gain privileges, so the restriction can only hurt the user's own processes. Code: `seccomp_prepare_filter()` (seccomp.c L691) and `landlock_restrict_self()` (syscalls.c L495).

**7.** Report the **max (26.6 s for both threads)** together with the run length, load and the histogram tail, not the average. Caveats: (1) it is a VM on a shared host, so the spike is probably hypervisor descheduling, not Linux; (2) one short run under one load proves nothing about the true worst case. (Plus: kernel is not RT.)

**8.** (a) Bandwidth control disabled: `sched_rt_runtime_us = -1` (`RUNTIME_INF`, deadline.c L518-519) → no admission test. (b) `EBUSY`.

**9.** Each owner's `pi_waiters` tree holds only the top waiter **of each lock** it owns; the owner's priority depends only on these. If the new waiter isn't the top of this lock, the owner's effective priority can't change. `owner->pi_blocked_on` non-NULL means the owner is itself waiting on another rt_mutex, so the boost must propagate to *that* lock's owner: transitive inheritance via `rt_mutex_adjust_prio_chain()` (which also detects deadlock cycles).

**10.** The three `preempt-flag-$(CONFIG_...) :=` lines are evaluated in order; `preempt-flag-y` keeps the last assignment whose config is `y`. `PREEMPT_RT` is assigned last (L30), so an RT kernel prints `PREEMPT_RT` even if `PREEMPT_BUILD`/`PREEMPT_DYNAMIC` are also set. On the first machine: `sudo cat /sys/kernel/debug/sched/preempt` (the active mode is in parentheses), or the `preempt=` boot parameter in `/proc/cmdline`.

**11.** `ERRNO(EPERM)` is lower than `ALLOW`, so `mkdir()` returns `-1` with `errno = EPERM` without running. No: results are combined by minimum, so adding a filter can only make the outcome equally or more restrictive.

**12.** Each thread asks `4/10 = 0.4` CPU. The default limit is 95 % per CPU: `4 × 0.95 = 3.8`. Nine threads use 3.6, the tenth would make 4.0 > 3.8 → `__dl_overflow()` → `EBUSY`. Ways: reduce `runtime` (measure WCET more precisely, optimize), lengthen `period` (if the deadline allows), add CPUs, or (carefully) raise `sched_rt_runtime_us` (leaves less for non-RT tasks). Not: disable admission control in production.

**13.** Unbounded priority inversion: the RT loop blocks on a mutex held by the nice-0 logger, which is preempted by other (medium) work. Fix: initialize the mutex with `pthread_mutexattr_setprotocol(&a, PTHREAD_PRIO_INHERIT)` (logger is boosted to RT while holding it), and better, remove the shared lock from the RT path (lock-free ring buffer to the logger). Verify with bpftrace on `tracepoint:sched:sched_pi_setprio`.

**14.** (1) Deny-list gaps: `openat`/`openat2` instead of `open`, `execveat` instead of `execve`, `clone3`/`vfork`; (2) no arch check: the i386 ABI (`int 0x80`) uses different numbers. Also, seccomp cannot inspect paths. Better: allow-list (only the syscalls the converter needs after start-up, default `ERRNO(ENOSYS)` or kill), libseccomp (handles arch), plus Landlock: read-only access to the input file's directory, write only to the output directory, no exec rights; restrict after loading fonts/libraries.

**15.** Category: analysis + bug study of an existing system. Context: CFS (Linux 3.17–4.3) load balancing, scheduling domains/groups on NUMA. Correctness: invariant "no idle core while threads wait" is reasonable as a definition of work conservation; tests on 64-core NUMA machines. Contributions: four bugs with fixes, an online sanity checker, a visualizer. Clarity: good, figures of per-core runqueue heatmaps. Pass-3 experiment: on the VM (or a NUMA box) run a `taskset`-pinned multi-threaded workload plus a single-threaded hog in another cgroup/autogroup (the Group Imbalance setup), sample per-CPU idle time with `mpstat`/`perf sched` and check whether cores stay idle while threads wait; relate it to `update_sd_pick_busiest()` (fair.c L10740) in v6.18.63.

**O1.** For: the mechanism (sleeping locks, threaded IRQs, PI everywhere) is in mainline and selectable on x86-64/arm64; demonstrated bounds of tens of µs on suitable hardware. Against: guarantees are demonstrated, not proven (no static WCET of the kernel); depends on hardware, firmware (SMIs), drivers and configuration; most distributions don't ship RT by default; it is not certified for hard safety-critical use. A balanced answer: Linux is a credible **firm/soft** RT platform and can meet many industrial hard requirements with validation, but it is not a certified hard RTOS.

**O2.** PI: no static knowledge, boosts only on contention, but chains and deadlock detection complicate analysis, and blocking can be chained. Ceiling (immediate PCP): each lock raises to its ceiling at acquisition; prevents deadlock and chained blocking, gives a tight analyzable bound (at most one critical section of blocking), but requires knowing all users of each lock in advance and costs a priority change on every lock. Safety-certified systems prefer ceiling (analyzability, e.g. as in many RTOS profiles). Linux user space prefers PI because programs don't declare their lock users, and PI costs nothing when uncontended (futex fast path).

**O3.** pledge/unveil: the kernel maintains the syscall→promise map, policies are one line, crashes loudly — easy for every programmer, low maintenance for application authors, but limited to what kernel authors anticipated and tied to one OS. seccomp/Landlock: expressive, composable with container runtimes, but filters must track new syscalls and libc changes, and BPF filters are easy to get subtly wrong. If application developers write the policy, pledge-style wins on maintenance; if platform teams write generic policies for unknown binaries, seccomp/Landlock's flexibility is required.
