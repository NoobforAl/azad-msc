# Lab 03.3 — solution notes

## Answers to "What to observe"

1. **Reader preference starves the writer.** glibc's default kind lets a new reader in whenever the lock is read-held, even if a writer is waiting. With 4 readers holding 100 µs sections back to back the read count never drops to 0, so `wrlock()` waits until the readers stop: the writer's maximum wait is about the whole run, and almost all of its writes happen only after the stop flag.
2. **Writer preference.** `PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP` blocks new readers once a writer waits; the writer gets in as soon as the current readers drain (≈ one 100 µs section), so it completes about one write per millisecond. The cost: readers lose throughput, and a thread that already holds a read lock deadlocks if it read-locks again while a writer waits (hence "NONRECURSIVE").
3. **Starvation ≠ deadlock.** Readers kept making progress the whole time; only one thread was denied. The Coffman conditions don't apply.

## Extension: `fair_rw.c`

Three semaphores (Downey, *The Little Book of Semaphores*, §4.2.6):

| Semaphore | Role |
|---|---|
| `turnstile` | every reader passes through it (`wait; post`); a writer *holds* it while waiting, so readers that arrive later queue behind the writer |
| `room_empty` | 1 while nobody is inside; the first reader takes it, the last returns it; the writer takes it to enter |
| `mutex` | protects the reader count |

```bash
gcc -Wall -Wextra -O2 -pthread solution/fair_rw.c -o fair_rw
./fair_rw 4 3
```

Captured on aos-lab, 2026-11-15 (two runs; shared, noisy VM):

```
pref=fair   readers=4 secs=3 reads=193285 writes=6 writer_wait max=0.004s avg=0.001080s
pref=fair   readers=4 secs=3 reads=481154 writes=304 writer_wait max=0.009s avg=0.000421s
```

The writer's maximum wait is 4–9 ms (one or two read sections), against the whole run under glibc's reader preference.

Arrival order is (roughly) FIFO through the turnstile, so neither side starves. It costs two extra semaphore operations per read section, which is visible in the lower read count.
