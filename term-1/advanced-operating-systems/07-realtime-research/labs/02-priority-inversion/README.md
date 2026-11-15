# Lab 07.2 — Reproduce priority inversion, then fix it with `PTHREAD_PRIO_INHERIT`

> **VM only.** The program runs three `SCHED_FIFO` threads that busy-loop for about one second on one CPU. On a shared machine that CPU is unavailable to normal tasks for that second.

**Goal:** make unbounded priority inversion happen on demand, measure how long the high-priority thread waits, remove the inversion with one mutex attribute, and watch the kernel boost the lock owner.

Runs on: the `aos-lab` VM (6.18.63, 8 vCPU). All three threads are pinned to **one** CPU with `taskset`: with free CPUs, L would simply run elsewhere and nothing would invert.

## Scenario

| Thread | Policy / prio | Does |
|---|---|---|
| L | `SCHED_FIFO` 10 | takes the mutex, needs 200 ms of **its own CPU time** inside it |
| H | `SCHED_FIFO` 30 | wants the mutex 20 ms later, blocks |
| M | `SCHED_FIFO` 20 | starts right after H blocks, burns 800 ms of CPU, never touches the mutex |
| main | `SCHED_FIFO` 50 | creates the threads, then waits |

CPU time is measured with `CLOCK_THREAD_CPUTIME_ID`, so time L spends preempted does not count as work.

## Steps

```bash
cd ~/work/07-realtime-research/02-priority-inversion
gcc -Wall -Wextra -O2 -pthread -o inversion inversion.c

sudo taskset -c 7 ./inversion none      # default protocol
sudo taskset -c 7 ./inversion inherit   # PTHREAD_PRIO_INHERIT

# Which syscall does a PI mutex use under contention?
sudo strace -f -e trace=futex taskset -c 7 ./inversion inherit 2>&1 | grep -m3 LOCK_PI

# Watch the kernel boost L (second terminal, or background it)
sudo bpftrace -e 'tracepoint:sched:sched_pi_setprio { printf("%s pid=%d prio %d -> %d\n", str(args.comm), args.pid, args.oldprio, args.newprio); }' &
sleep 3; sudo taskset -c 7 ./inversion inherit >/dev/null; sleep 1; sudo kill %1
```

## Code

The only difference between the two runs (`inversion.c`):

```c
pthread_mutexattr_t ma;
pthread_mutexattr_init(&ma);
if (strcmp(mode, "inherit") == 0)
    pthread_mutexattr_setprotocol(&ma, PTHREAD_PRIO_INHERIT);
else
    pthread_mutexattr_setprotocol(&ma, PTHREAD_PRIO_NONE);
pthread_mutex_init(&lock, &ma);
```

Kernel side: glibc turns a contended PI mutex into `futex(FUTEX_LOCK_PI_PRIVATE)` → `futex_lock_pi()` (`kernel/futex/pi.c` L983) → `task_blocks_on_rt_mutex()` → `rt_mutex_adjust_prio()` → `rt_mutex_setprio()` (walkthrough §2).

## Expected output

> Captured on aos-lab (VirtualBox on Hyper-V, Ubuntu 24.04, Linux 6.18.63 `PREEMPT_DYNAMIC`, 8 vCPU, shared with other users), 2026-11-15. Your numbers will differ.

```text
$ sudo taskset -c 7 ./inversion none
protocol=none cpu=7
     0.1 ms  L  locked, working 200 ms (CPU time)
    23.1 ms  H  wants the lock
    25.1 ms  M  start, burning 800 ms (no lock)
   825.2 ms  M  done
  1000.7 ms  L  unlock
  1000.7 ms  H  got the lock after 977.6 ms
$ sudo taskset -c 7 ./inversion inherit
protocol=inherit cpu=7
     0.1 ms  L  locked, working 200 ms (CPU time)
    20.7 ms  H  wants the lock
   202.2 ms  L  unlock
   202.2 ms  H  got the lock after 181.6 ms
   202.3 ms  M  start, burning 800 ms (no lock)
  1002.3 ms  M  done
$ sudo strace -f -e trace=futex taskset -c 7 ./inversion inherit 2>&1 | grep LOCK_PI
[pid  8157] futex(0x5d44546f2060, FUTEX_LOCK_PI_PRIVATE, NULL ...
[pid  8151] futex(0x5d44546f2060, FUTEX_UNLOCK_PI_PRIVATE <unfinished ...>
$ sudo strace -f -e trace=futex taskset -c 7 ./inversion none 2>&1 | grep futex
[pid  8340] futex(0x7487b07ffcd8, FUTEX_WAIT_PRIVATE, 2, NULL <unfinished ...>
[pid  8321] futex(0x7487b07ffcd8, FUTEX_WAKE_PRIVATE, 1) = 1
$ sudo bpftrace -e 'tracepoint:sched:sched_pi_setprio { printf("%s pid=%d prio %d -> %d\n", str(args.comm), args.pid, args.oldprio, args.newprio); }'
Attaching 1 probe...
inversion pid=9760 prio 89 -> 69
inversion pid=9760 prio 69 -> 89
```

## What to observe

1. **H's wait.** `none`: roughly M's 800 ms plus L's remaining ~180 ms. `inherit`: roughly L's remaining work only.
2. **Order of events.** With `none`, M finishes **before** L unlocks. With `inherit`, L unlocks and H runs **before** M finishes: M was kept off the CPU while L was boosted.
3. **Kernel priorities.** The tracepoint prints kernel `prio` values: `prio = 99 − rt_priority`, so `89` = FIFO 10 (L) and `69` = FIFO 30 (H). The boost is `89 -> 69`, the de-boost on unlock `69 -> 89`.
4. **`FUTEX_LOCK_PI`.** Only the PI mutex uses it; the default mutex uses `FUTEX_WAIT`/`FUTEX_WAKE`, and the kernel never learns who the owner is.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| H waits ~180 ms even with `none` | threads ran on different CPUs | run under `taskset -c N` (all threads inherit the mask) |
| `pthread_create(prio 10): Operation not permitted` | not root / no `CAP_SYS_NICE` | `sudo` |
| H waits ~1 s even with `inherit` | `pthread_mutexattr_setprotocol` failed or was called after `pthread_mutex_init` | set the protocol on the attr **before** init; check the return value |
| bpftrace: `%s specifier expects a value of type string (integer supplied)` | `comm` is a `__data_loc char[]` field in this tracepoint | wrap it: `str(args.comm)`; list fields with `sudo bpftrace -lv tracepoint:sched:sched_pi_setprio` |
| times longer than expected | RT throttling / fair server or other load on that CPU | pick an idle CPU; see `/proc/sys/kernel/sched_rt_runtime_us` |

## Extension task

Add a third mode, `protect`, that uses `PTHREAD_PRIO_PROTECT` with a priority ceiling of 30 (`pthread_mutexattr_setprioceiling`). Predict, then measure: how long does H wait, when does L's priority change (at lock time or at contention?), and how many `sched_pi_setprio` events or `sched_setscheduler`-type changes do you see? Explain the difference from `inherit` in terms of when the boost happens.

Solution: [`solution/answers.md`](solution/answers.md) and [`solution/inversion-protect.c`](solution/inversion-protect.c).
