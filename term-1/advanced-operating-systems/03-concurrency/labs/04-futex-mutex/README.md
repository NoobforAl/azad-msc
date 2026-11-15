# Lab 03.4 — A mutex on raw `futex()` in ~60 lines, traced with `strace` and `bpftrace`

**Goal:** implement Drepper's three-state futex mutex, prove it correct under contention, and show that the kernel is entered only when a thread must sleep or wake another.

Runs on: the `aos-lab` VM (bpftrace needs root and BTF). Notes: [07](../../notes/07-futex-user-kernel-split.en.md), [05](../../notes/05-mutex-optimistic-spinning.en.md). Lesson §4.4. Walkthrough §3.

## Steps

```bash
cd ~/work/03-concurrency/04-futex-mutex
gcc -Wall -Wextra -O2 -pthread futex_mutex.c -o futex_mutex

./futex_mutex 1 1000000                                 # no contention
./futex_mutex 4 1000000                                 # 4 threads fight
strace -f -c -e trace=futex ./futex_mutex 1 1000000     # count syscalls
strace -f -c -e trace=futex ./futex_mutex 4 200000
strace -f -e trace=futex ./futex_mutex 4 2000 2>&1 | head
sudo bpftrace futex-ops.bt -c './futex_mutex 4 200000'  # per-op counts + latency
```

## Code

State word: `0` unlocked, `1` locked, `2` locked and maybe waiters.

```c
static void fmutex_lock(atomic_uint *m)
{
    uint32_t c = cas(m, 0, 1);                   // fast path: 0 -> 1
    if (c == 0)
        return;
    if (c != 2)
        c = atomic_exchange(m, 2);               // announce "there may be waiters"
    while (c != 0) {
        atomic_fetch_add(&g_wait_calls, 1);
        futex(m, FUTEX_WAIT_PRIVATE, 2);         // sleeps only if *m is still 2
        c = atomic_exchange(m, 2);               // woke up: try to take it, keep "2"
    }
}

static void fmutex_unlock(atomic_uint *m)
{
    if (atomic_fetch_sub(m, 1) != 1) {           // was 2: someone may sleep
        atomic_store(m, 0);
        atomic_fetch_add(&g_wake_calls, 1);
        futex(m, FUTEX_WAKE_PRIVATE, 1);         // wake exactly one waiter
    }
}
```

`futex-ops.bt` counts `sys_enter_futex` by `op & 127` (strip `FUTEX_PRIVATE_FLAG` = 128; 0 = WAIT, 1 = WAKE) for the child process only (`pid == cpid`) and makes a latency histogram per op.

Kernel side of the same call: `do_futex()` → `futex_wait()` → `futex_wait_setup()` (lock bucket, re-read `*uaddr`, `-EWOULDBLOCK` if it changed, else queue and `schedule()`), and `futex_wake()` (skip if no waiters, else wake one). See the [walkthrough §3](../../kernel-walkthrough.en.md).

## Expected output

> Captured on `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, gcc 13.3.0, strace, bpftrace), 2026-11-15. Shared 8-vCPU guest.

```
$ ./futex_mutex 1 1000000
threads=1 counter=1000000 expected=1000000 OK futex_wait=0 futex_wake=0
$ ./futex_mutex 4 1000000
threads=4 counter=4000000 expected=4000000 OK futex_wait=37928 futex_wake=48919
$ ./futex_mutex 4 1000000                       # second run
threads=4 counter=4000000 expected=4000000 OK futex_wait=78843 futex_wake=103767
```

`strace` (counts every futex call, including glibc's own `pthread_join` waits):

```
$ strace -f -c -e trace=futex ./futex_mutex 1 1000000
threads=1 counter=1000000 expected=1000000 OK futex_wait=0 futex_wake=0
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
100.00    0.002002        2001         1           futex
$ strace -f -c -e trace=futex ./futex_mutex 4 1000000
threads=4 counter=4000000 expected=4000000 OK futex_wait=306 futex_wake=479
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
100.00    0.154894         196       788       306 futex
$ strace -f -c -e trace=futex ./futex_mutex 4 200000
threads=4 counter=800000 expected=800000 OK futex_wait=0 futex_wake=0
...
100.00    0.004321        2160         2           futex
$ strace -f -e trace=futex ./futex_mutex 4 2000 2>&1 | grep futex
27268 futex(0x71feef7fc990, FUTEX_WAIT_BITSET|FUTEX_CLOCK_REALTIME, 27274, NULL, FUTEX_BITSET_MATCH_ANY) = 0
```

`bpftrace` (does not stop the threads, so contention stays realistic):

```
$ sudo bpftrace futex-ops.bt -c './futex_mutex 4 200000'
Attaching 3 probes...
threads=4 counter=800000 expected=800000 OK futex_wait=6680 futex_wake=8949

@calls[9]: 3
@calls[0]: 6680
@calls[1]: 8949

@usecs[0]:
[0]                 6559 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[1]                   26 |                                                    |
[2, 4)                 9 |                                                    |
[4, 8)                18 |                                                    |
...
[64, 128)             32 |                                                    |
[128, 256)            15 |                                                    |
...
[8K, 16K)              1 |                                                    |

@usecs[1]:
[0]                 8832 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[1]                   24 |                                                    |
...
```

## What to observe

1. **No contention, no kernel.** One thread did a million lock/unlock pairs with `futex_wait=0 futex_wake=0`; `strace` saw exactly one futex call, and that one is glibc's `pthread_join` (`FUTEX_WAIT_BITSET`, op 9), not the mutex.
2. **Under contention the kernel sees a small fraction**: 4 threads × 1,000,000 lock/unlock pairs = 8,000,000 operations, but only 38–79 k WAITs and 49–104 k WAKEs: about 1–2% of operations enter the kernel.
3. **Most FUTEX_WAITs return immediately.** In the bpftrace histogram 6,559 of 6,680 WAIT calls (98%) took under 1 µs: the kernel re-read the word under the bucket lock, saw it was no longer 2, and returned `EAGAIN` without sleeping (`futex_wait_setup()` L647–649). Only a few dozen actually slept (the 64 µs–16 ms tail).
4. **WAKE > WAIT** (8,949 vs 6,680): an unlocker that sees state 2 always issues a WAKE, even if the would-be sleeper already got the lock in user space. That is the price of the sticky "2".
5. **`strace` changes the experiment.** Under `strace -f` the 200,000-iteration run had *zero* contention (`futex_wait=0`) and the 1,000,000 run only 306 WAITs: ptrace stops each thread at every syscall and at thread creation, so the threads mostly ran one after another. Use bpftrace (or the program's own counters) to measure contention; use strace to see *which* calls are made.

## Common pitfalls

| Symptom | Fix |
|---|---|
| hangs under contention | unlock must wake when the old value was 2; and lock must set 2 *before* waiting |
| `FUTEX_WAIT` returns `EAGAIN` | normal: the word changed between your CAS and the syscall; just loop |
| more WAKE than WAIT calls | normal for this design: an unlocker that sees 2 wakes even if the waiter had already given up sleeping (the "2" is sticky) |
| `bpftrace`: `ERROR: ... args->op` | needs BTF/tracepoint format; run as root on the VM kernel |

## Extension

Add a bounded spin phase to `lock()` before it goes to sleep (the user-space analogue of the kernel mutex's optimistic spin) and measure, for spin = 0, 100, 1000, how many `FUTEX_WAIT` calls remain and how the run time changes. Solution: [`solution/futex_spin_mutex.c`](solution/futex_spin_mutex.c), notes in [`solution/README.md`](solution/README.md).
