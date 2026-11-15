# Lab 07.2 — answers

## What to observe

1. **H's wait.** `none`: ≈ 800 ms (M) + ≈ 180 ms (rest of L's 200 ms of CPU) ≈ 980 ms. `inherit`: ≈ 180 ms. The difference is exactly M's run time: with PI, M is never runnable at a higher priority than the lock holder.
2. **Order.** `none`: `M done` is printed before `L unlock`. `inherit`: `L unlock` → `H got the lock` → `M done`.
3. **Kernel priorities.** `sched_pi_setprio` shows L (`comm` = `inversion`) going from prio 89 (FIFO 10: `99 − 10`) to 69 (FIFO 30) when H blocks, and back to 89 at unlock. That's `rt_mutex_setprio()` (core.c L7352) firing `trace_sched_pi_setprio()` (L7407).
4. **Futex ops.** PI mutex: `FUTEX_LOCK_PI_PRIVATE` / `FUTEX_UNLOCK_PI_PRIVATE`; the futex word holds the owner's TID, so the kernel can find whom to boost (`futex_lock_pi()`, pi.c L983). Default mutex: `FUTEX_WAIT_PRIVATE` / `FUTEX_WAKE_PRIVATE`; the kernel only sees "a waiter".

## Extension: `PTHREAD_PRIO_PROTECT`

`solution/inversion-protect.c` adds `protect` with ceiling 30.

Real run on the VM:

```text
$ sudo taskset -c 7 ./inversion-protect protect
protocol=protect cpu=7
     0.2 ms  L  locked (now FIFO 10), working 200 ms (CPU time)
   200.2 ms  L  unlock
   202.1 ms  H  wants the lock
   202.1 ms  H  got the lock after 0.0 ms
   203.8 ms  M  start, burning 800 ms (no lock)
  1003.8 ms  M  done
$ sudo strace -f -e trace=sched_setscheduler,futex taskset -c 7 ./inversion-protect protect 2>&1 | grep sched_setscheduler
sched_setscheduler(0, SCHED_FIFO, [50]) = 0              # main
[pid  8347] sched_setscheduler(8357, SCHED_FIFO, [10]) = 0   # pthread_create: L at 10
[pid  8357] sched_setscheduler(8357, SCHED_FIFO, [30]) = 0   # L locks: raised to the ceiling
[pid  8347] sched_setscheduler(8363, SCHED_FIFO, [30]) = 0   # pthread_create: H at 30
...
```

- **When L's priority changes:** at **lock time**, not at contention: glibc itself calls `sched_setscheduler(tid, SCHED_FIFO, [30])` inside `pthread_mutex_lock()`, before H exists. No futex PI operation is involved.
- **H's wait: 0 ms.** H (30) is created while L runs at 30; equal-priority `SCHED_FIFO` does not preempt, so H only starts running when L has unlocked and dropped back to 10. H never blocks at all. M (20) waits behind both.
- **Pitfall in the output:** `pthread_getschedparam()` still reports `FIFO 10` inside the critical section: glibc returns the thread's own base priority, not the temporary ceiling boost. Trust `strace`, not the getter.
- **Tracepoint:** `sched_pi_setprio` should stay silent for `protect`: no rt_mutex boost is involved (strace shows no `FUTEX_LOCK_PI`), the change is an ordinary `sched_setscheduler()`. `UNVERIFIED` on the VM (it became unreachable before this run); check with the bpftrace one-liner from the README.
- **Trade-off:** PCP pays a priority change on **every** lock/unlock, even uncontended, and you must know the highest user (30) in advance. In return, L can never be preempted by anything ≤ 30 inside the critical section, which also prevents chained blocking and deadlock between ceiling-protected locks.
