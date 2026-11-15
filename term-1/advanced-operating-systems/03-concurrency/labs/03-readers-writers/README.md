# Lab 03.3 — Readers-Writers with `pthread_rwlock` and writer starvation

**Goal:** show that glibc's default `pthread_rwlock` prefers readers and can starve a writer for as long as readers keep overlapping, then fix it with the writer-preferring kind.

Runs on: the `aos-lab` VM or any Linux/glibc box. Notes: [10](../../notes/10-classic-problems.en.md), [06](../../notes/06-semaphores-condition-variables.en.md). Lesson §4.5, §4.7.

## Steps

```bash
cd ~/work/03-concurrency/03-readers-writers
gcc -Wall -Wextra -O2 -pthread rw.c -o rw
./rw reader 4 3     # glibc default: PTHREAD_RWLOCK_PREFER_READER_NP
./rw writer 4 3     # PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP
```

## Code

`rw.c`: 4 readers each hold the read lock for 100 µs back to back, so at any instant at least one reader is inside. One writer tries `pthread_rwlock_wrlock()` every millisecond and records how long it waited. After `<seconds>` the main thread sets a stop flag; `writes` counts only the writes that got in **before** the stop, `(+N after stop)` the ones that only succeeded because the readers quit.

```c
pthread_rwlockattr_setkind_np(&at, writer_pref ? PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP
                                               : PTHREAD_RWLOCK_PREFER_READER_NP);
```

## Expected output

> Captured on `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, glibc 2.39), 2026-11-15. The VM was shared and heavily loaded during the first run; more runs are shown to give the spread.

```
$ ./rw reader 4 3
pref=reader readers=4 secs=3 reads=1179165 writes=0 (+1 after stop) writer_wait max=28.114s avg=28.113754s
$ ./rw writer 4 3
pref=writer readers=4 secs=3 reads=270250 writes=188 (+1 after stop) writer_wait max=0.036s avg=0.003488s
$ ./fair_rw 4 3                      # extension solution
pref=fair   readers=4 secs=3 reads=193285 writes=6 writer_wait max=0.004s avg=0.001080s
```

More runs (same commands, later):

```
pref=reader readers=4 secs=3 reads=1463204 writes=0 (+1 after stop) writer_wait max=39.254s avg=39.254045s
pref=reader readers=4 secs=3 reads=161806 writes=0 (+1 after stop) writer_wait max=4.281s avg=4.281458s
pref=writer readers=4 secs=3 reads=561540 writes=7 (+0 after stop) writer_wait max=0.009s avg=0.002410s
pref=writer readers=4 secs=3 reads=72530 writes=1421 (+1 after stop) writer_wait max=0.007s avg=0.000393s
pref=writer readers=4 secs=3 reads=279557 writes=11 (+0 after stop) writer_wait max=0.002s avg=0.000520s
pref=fair   readers=4 secs=3 reads=481154 writes=304 writer_wait max=0.009s avg=0.000421s
```

## What to observe

1. **Reader preference starves the writer completely**: `writes=0` before the stop flag in all three reader-preference runs. Its one write (`+1 after stop`) happened only when the readers quit, after waiting the *whole run* (4.3 s for a 3 s run; 28 s and 39 s when the loaded VM also delayed the readers' exit).
2. **Writer preference fixes starvation**: the writer's **maximum** wait drops to 2–36 ms, i.e. it gets in as soon as the readers inside drain. Readers pay: they now queue behind every waiting writer.
3. **Starvation is not deadlock**: during the reader-preference runs the readers completed 0.16–1.46 million read sections. The system made progress; one thread did not.
4. **The write count under writer preference varies wildly (7 to 1,421)** although each wait is short: the writer sleeps 1 ms between attempts, and on this shared VM a sleeping thread's wake-up depends on the host scheduling its vCPU. The *waits* (max 2–36 ms vs. the whole run) are the stable signal.

## Common pitfalls

| Symptom | Fix |
|---|---|
| `PTHREAD_RWLOCK_PREFER_WRITER_NP` changes nothing | glibc ignores it; use `..._WRITER_NONRECURSIVE_NP` |
| no starvation seen | readers must overlap; with 1 reader or a gap between read sections the writer slips in |
| writer-preferring lock deadlocks | a thread that holds a read lock and takes it again while a writer waits blocks forever: the "NONRECURSIVE" in the name |

## Extension

Implement a starvation-free readers-writers lock from three semaphores (a "turnstile" that a waiting writer holds so new readers queue behind it) and compare its numbers with both glibc kinds. Solution: [`solution/fair_rw.c`](solution/fair_rw.c), notes in [`solution/README.md`](solution/README.md).
