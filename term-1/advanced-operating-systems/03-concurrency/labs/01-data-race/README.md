# Lab 03.1 — Data race → ThreadSanitizer → mutex → atomic → `perf stat`

**Goal:** see `count++` lose updates on real threads, let ThreadSanitizer name the race, fix it twice (mutex, atomic) and measure what each fix costs.

Runs on: the `aos-lab` VM or any Linux box (user space only). Notes: [01](../../notes/01-race-conditions-critical-sections.en.md), [02](../../notes/02-atomics-c11-memory-model.en.md). Lesson §4.1.

## Steps

```bash
mkdir -p ~/work/03-concurrency && cd ~/work/03-concurrency/01-data-race   # copy this folder here
gcc -Wall -Wextra -O2 -pthread race.c -o race
gcc -Wall -Wextra -O1 -g -fsanitize=thread -pthread race.c -o race-tsan

./race race   4 1000000        # plain volatile ++ : wrong
./race mutex  4 1000000        # pthread_mutex around ++
./race atomic 4 1000000        # atomic_fetch_add (lock xadd)
./race race   1 1000000        # one thread: always right

./race-tsan race 2 1000        # TSan names the two racing accesses
./race-tsan atomic 2 1000      # no report

for m in race mutex atomic; do
  sudo perf stat -e task-clock,context-switches,cpu-migrations,page-faults ./race $m 4 1000000
done
```

If TSan aborts with `FATAL: ThreadSanitizer: unexpected memory mapping`, run it as `setarch x86_64 -R ./race-tsan race 2 1000` (TSan's shadow layout vs. the kernel's high ASLR entropy; VERSION-DEPENDENT on gcc/kernel).

## Code

`race.c` (one file, three modes). The whole point is the loop body:

```c
case MODE_RACE:
    g_plain++;                      // load, add, store: 3 steps
    break;
case MODE_MUTEX:
    pthread_mutex_lock(&g_lock);
    g_plain++;
    pthread_mutex_unlock(&g_lock);
    break;
case MODE_ATOMIC:
    atomic_fetch_add_explicit(&g_atomic, 1, memory_order_relaxed);
    break;
```

`g_plain` is `volatile long`: `volatile` stops the compiler from folding the loop into one `+= iters`, so every iteration really loads and stores memory. It does **not** make the increment atomic.

## Expected output

> Captured on `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, 8 vCPU, gcc 13.3.0), 2026-11-15. The VM is shared with other users: timings are noisy; the *shape* (lost vs. not lost, which mode is slower) is what must match.

```
$ for m in race mutex atomic; do ./race $m 4 1000000; done
mode=race   threads=4 expected=4000000 got=2498418 lost=1501582 time=0.025s ns/inc=6.2
mode=mutex  threads=4 expected=4000000 got=4000000 lost=0 time=0.358s ns/inc=89.6
mode=atomic threads=4 expected=4000000 got=4000000 lost=0 time=0.098s ns/inc=24.4
$ ./race race 1 1000000
mode=race   threads=1 expected=1000000 got=1000000 lost=0 time=0.003s ns/inc=3.3
$ for i in 1 2 3; do ./race race 4 1000000; done
mode=race   threads=4 expected=4000000 got=2382457 lost=1617543 time=0.030s ns/inc=7.5
mode=race   threads=4 expected=4000000 got=1968677 lost=2031323 time=0.030s ns/inc=7.5
mode=race   threads=4 expected=4000000 got=1949763 lost=2050237 time=0.019s ns/inc=4.7
```

ThreadSanitizer (paths shortened, BuildIds cut):

```
$ ./race-tsan race 2 1000
==================
WARNING: ThreadSanitizer: data race (pid=4446)
  Read of size 8 at 0x55912d33b070 by thread T2:
    #0 worker .../01-data-race/race.c:33 (race-tsan+0x1470)

  Previous write of size 8 at 0x55912d33b070 by thread T1:
    #0 worker .../01-data-race/race.c:33 (race-tsan+0x1483)

  Location is global 'g_plain' of size 8 at 0x55912d33b070 (race-tsan+0x4070)

  Thread T2 (tid=4452, running) created by main thread at:
    #0 pthread_create ... (libtsan.so.2+0x5ac1a)
    #1 main .../01-data-race/race.c:76 (race-tsan+0x171e)
...
SUMMARY: ThreadSanitizer: data race .../01-data-race/race.c:33 in worker
==================
ThreadSanitizer: reported 1 warnings
mode=race   threads=2 expected=2000 got=2000 lost=0 time=1.391s ns/inc=695728.7
$ setarch x86_64 -R ./race-tsan atomic 2 1000
mode=atomic threads=2 expected=2000 got=2000 lost=0 time=0.051s ns/inc=25534.1
```

(The `atomic` run first aborted with `FATAL: ThreadSanitizer: unexpected memory mapping`; the `setarch -R` rerun is shown. The tsan wrapper in our run script does this automatically.)

`perf stat` (software events only; this guest has no PMU):

| mode | result | task-clock | CPUs utilized | context-switches | cpu-migrations | elapsed |
|---|---|---|---|---|---|---|
| race | lost=342494 | 60.71 ms | 0.691 | 11 | 3 | 0.088 s |
| mutex | lost=0 | 1002.69 ms | 1.327 | 349 | 43 | 0.756 s |
| atomic | lost=0 | 262.96 ms | 2.308 | 54 | 6 | 0.114 s |

```
$ sudo perf stat -e task-clock,context-switches,cpu-migrations,page-faults ./race mutex 4 1000000
mode=mutex  threads=4 expected=4000000 got=4000000 lost=0 time=0.702s ns/inc=175.4
 Performance counter stats for './race mutex 4 1000000':
           1002.69 msec task-clock                       #    1.327 CPUs utilized
               349      context-switches                 #  348.064 /sec
                43      cpu-migrations                   #   42.885 /sec
                73      page-faults                      #   72.804 /sec
       0.755678142 seconds time elapsed
       0.457252000 seconds user
       0.565441000 seconds sys
```

## What to observe

1. **Lost updates: 37–51% of the increments vanished** with 4 threads, and a different amount every run. With 1 thread nothing is lost: the bug needs real parallelism. `volatile` made every iteration load and store memory and still did not help.
2. **TSan names both sides** of the race: a *read* and a *previous write* of the same 8 bytes (`g_plain`), both at `race.c:33`, from threads T1 and T2, and where each thread was created. It found it in a run of only 2,000 increments that happened to give the right answer: TSan detects the *missing happens-before*, not a wrong result.
3. **Atomic is ~4× cheaper than the mutex here** (24 vs 90 ns per increment) but ~4× slower than the racy version: every `lock xadd` pulls the cache line exclusive to its core, so the four cores take turns on one line.
4. **The mutex burns system time.** `sys` 0.57 s of 1.0 s CPU and 349 context switches: contended `pthread_mutex_lock` goes to `futex(FUTEX_WAIT)` (lab 04 shows exactly how). The atomic version never enters the kernel (54 switches are just the scheduler on a shared VM).
5. **CPUs utilized** tells the same story: atomic keeps 2.3 CPUs busy spinning on the line; the mutex version sleeps a lot (1.3); the racy version finishes before all threads even start (0.7).

## Common pitfalls

| Symptom | Fix |
|---|---|
| `race` mode gives the right answer | too few iterations or 1 thread; use ≥ 1,000,000 and 4 threads |
| TSan: `unexpected memory mapping` | `setarch x86_64 -R ./race-tsan ...` |
| `perf stat`: `Access to performance monitoring ... paranoid` | use `sudo`, or `sysctl kernel.perf_event_paranoid=1` (restore it afterwards) |
| `cycles`/`instructions` `<not supported>` | no hardware PMU in this VirtualBox guest; use software events as above |

## Extension

Remove sharing altogether: give each thread its own counter and sum at the end. Measure two layouts: counters packed next to each other in one array, and each counter padded to its own 64-byte cache line. Explain the difference with the cache-coherence protocol (false sharing). Solution: [`solution/sharded.c`](solution/sharded.c) and [`solution/README.md`](solution/README.md).
