# Lab 03.4 — solution notes

## Why the three states

| State | Meaning | Who sets it |
|---|---|---|
| 0 | unlocked | `unlock` (`atomic_store(m, 0)` or the `fetch_sub` 1→0) |
| 1 | locked, nobody waits | `lock` fast path (`cas 0→1`) |
| 2 | locked, someone *may* wait | a contender (`xchg 2`) before it sleeps |

With only two states (0/1) `unlock` cannot know whether to call `FUTEX_WAKE`, so it must call it every time (one syscall per unlock) — Drepper's "mutex 1". The third state lets an uncontended unlock stay in user space. A woken thread re-takes the lock with `xchg 2` (not `cas 0→1`), because it cannot know whether others are still sleeping: "2" is sticky, which is why WAKE calls can outnumber WAIT calls.

`FUTEX_WAIT(m, 2)` is the critical step: the kernel compares `*m` with 2 under the hash-bucket lock (`futex_wait_setup()`, `kernel/futex/waitwake.c` L630–650). If the unlocker stored 0 in between, the call returns `EAGAIN` at once and the loop retries; no wake-up can be lost.

## Extension: spin before sleeping (`futex_spin_mutex.c`)

```bash
gcc -Wall -Wextra -O2 -pthread solution/futex_spin_mutex.c -o futex_spin_mutex
for s in 0 100 1000; do ./futex_spin_mutex 4 1000000 $s; done
```

Captured on aos-lab, 2026-11-15:

```
spin=0     threads=4 OK futex_wait=68589 futex_wake=93501 time=0.238s
spin=100   threads=4 OK futex_wait=760 futex_wake=978 time=0.398s
spin=1000  threads=4 OK futex_wait=78 futex_wake=91 time=0.486s
```

- 100 spins remove **99%** of the `FUTEX_WAIT` calls (68,589 → 760); 1,000 spins leave 78. The critical section (`g_counter++`) is a few nanoseconds, so the owner almost always releases while the contender is still spinning.
- But the run got **slower** (0.24 s → 0.49 s). With 4 threads hammering one lock, spinners keep the lock's cache line busy and steal CPU time from the owner; on a shared 8-vCPU VM a spinning vCPU may even be descheduled by the host. Fewer syscalls ≠ faster.
- This is why the kernel's `mutex_spin_on_owner()` spins only **while the owner is running** (`owner_on_cpu()`), lets only one spinner at a time watch the owner (`osq_lock`), and stops on `need_resched()`. glibc's `PTHREAD_MUTEX_ADAPTIVE_NP` uses a bounded, self-tuning spin count for the same reason.
