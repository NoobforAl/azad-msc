# Lab 03.2 — Producer-Consumer: semaphores → condition variables → Go channel

**Goal:** build the same bounded buffer three ways, prove each is correct with a checksum, and see where each one waits (futex calls, sleeps).

Runs on: the `aos-lab` VM or any Linux box (user space). Notes: [06](../../notes/06-semaphores-condition-variables.en.md), [10](../../notes/10-classic-problems.en.md). Lesson §4.5.

## Steps

```bash
cd ~/work/03-concurrency/02-producer-consumer
gcc -Wall -Wextra -O2 -pthread pc_sem.c  -o pc_sem
gcc -Wall -Wextra -O2 -pthread pc_cond.c -o pc_cond
go build -o pc_chan pc_chan.go

for cap in 1 16 1024; do
  ./pc_sem 1000000 $cap; ./pc_cond 1000000 $cap; ./pc_chan 1000000 $cap
done

strace -f -c -e trace=futex ./pc_sem  200000 16   # who enters the kernel?
strace -f -c -e trace=futex ./pc_cond 200000 16
```

## Code

| File | Waiting mechanism | Key lines |
|---|---|---|
| `pc_sem.c` | `sem_t empty` (free slots) + `sem_t full` (items) + a mutex for the indices | `sem_wait(&g_empty)` … `sem_post(&g_full)` |
| `pc_cond.c` | one mutex + `not_full` / `not_empty` condvars, `while (count == cap) pthread_cond_wait(...)` | counts how often each side slept |
| `pc_chan.go` | `make(chan int64, capacity)`; `close(ch)` ends the consumer's `range` | the runtime does the counting and parking |

Producer sends 1..N; the consumer sums them; the program checks `sum == N(N+1)/2`.

```c
// pc_cond.c, consumer
pthread_mutex_lock(&g_lock);
while (g_count == 0) {
    g_waits_empty++;
    pthread_cond_wait(&g_not_empty, &g_lock);
}
long v = g_buf[g_tail];
g_tail = (g_tail + 1) % g_cap;
g_count--;
pthread_cond_signal(&g_not_full);
pthread_mutex_unlock(&g_lock);
```

## Expected output

> Captured on `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, gcc 13.3.0, go 1.22.2), 2026-11-15, right after a VM restart while other users were also running labs (load average 2–9). Timings are **very** noisy here; two full runs are shown so you can see how much. Checksums are exact in every run.

Run 2 (load average falling from 3.6 to 2.1):

```
$ for cap in 1 16 1024; do ./pc_sem 1000000 $cap; ./pc_cond 1000000 $cap; ./pc_chan 1000000 $cap; done
sem   items=1000000 cap=1 sum=500000500000 OK time=3.257s ns/item=3257
cond  items=1000000 cap=1 sum=500000500000 OK time=76.909s ns/item=76909 waits(full)=722595 waits(empty)=727233
chan  items=1000000 cap=1 sum=500000500000 OK time=0.181s ns/item=181
sem   items=1000000 cap=16 sum=500000500000 OK time=11.667s ns/item=11667
cond  items=1000000 cap=16 sum=500000500000 OK time=8.917s ns/item=8917 waits(full)=78597 waits(empty)=78033
chan  items=1000000 cap=16 sum=500000500000 OK time=0.050s ns/item=50
sem   items=1000000 cap=1024 sum=500000500000 OK time=0.342s ns/item=342
cond  items=1000000 cap=1024 sum=500000500000 OK time=0.186s ns/item=186 waits(full)=975 waits(empty)=964
chan  items=1000000 cap=1024 sum=500000500000 OK time=0.039s ns/item=39
```

Run 1 (load average ~9), ns/item only:

| cap | sem | cond | chan |
|---|---|---|---|
| 1 | 62,898 | 188,857 | 356 |
| 16 | 7,320 | 39,957 | 96 |
| 1024 | 1,260 | 703 | 150 |

Who enters the kernel (smaller run, under `strace`, which itself slows everything down):

```
$ strace -f -c -e trace=futex ./pc_sem 200000 16
sem   items=200000 cap=16 sum=20000100000 OK time=268.408s ns/item=1342040
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
100.00  179.806066         483    371813     78006 futex
$ strace -f -c -e trace=futex ./pc_cond 200000 16
cond  items=200000 cap=16 sum=20000100000 OK time=78.400s ns/item=392000 waits(full)=25790 waits(empty)=14453
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
100.00   56.667936         321    175989     24310 futex
```

## What to observe

1. **All three are correct**: `sum=500000500000` = 1,000,000·1,000,001/2 in every run.
2. **Small buffers turn into ping-pong.** With `cap=1` the condvar version slept 722,595 times on "full" and 727,233 on "empty": almost every item costs a sleep and a wake-up, i.e. a futex round trip and two context switches. With `cap=1024` it slept fewer than 1,000 times and became 400× faster.
3. **The kernel only sees contention.** `pc_sem` made 371,813 `futex` calls for 200,000 items (`errors` = `EAGAIN`: the value changed before the kernel looked, the lab 04 protocol), not one per `sem_wait`/`sem_post`. glibc's `sem_t` and `pthread_cond_t` are both built on futexes.
4. **Go channels win at every capacity here** (39–356 ns/item). A blocked goroutine is parked by the Go scheduler in user space; the OS thread usually keeps running another goroutine, so there is no futex round trip per item (Module 02: M:N scheduling).
5. **Timing on a shared VM**: the same command took 3.3 s in one run and 62.9 s in the other. A sleep/wake handoff needs the host to schedule *two* vCPUs; when other guests' work competes for host CPUs, each handoff can wait milliseconds. Compare counts (waits, futex calls) and ratios, not absolute times.

## Common pitfalls

| Symptom | Fix |
|---|---|
| `if (count == 0) wait` works in tests, corrupts with 2 consumers | always `while`: the predicate can be false again when you wake (Q14) |
| program hangs at the end with several consumers | consumers need a shutdown signal: poison pill or `closed` flag + `broadcast` |
| `sem_init` returns ENOSYS on macOS | unnamed POSIX semaphores are Linux-only here; run in the VM |
| Go: `all goroutines are asleep - deadlock!` | the producer forgot `close(ch)` |

## Extension

Generalise `pc_cond.c` to P producers and C consumers with a clean shutdown (every consumer exits exactly once, the sum is still exact). Solution: [`solution/pc_mpmc.c`](solution/pc_mpmc.c), notes in [`solution/README.md`](solution/README.md).
