# Lab 03.2 — solution notes

## Answers to the design questions

- **Semaphores vs. condition variables.** A semaphore *is* the counter: `empty` starts at `cap`, `full` at 0, and P/V move tokens between them. The mutex is still needed for the indices `head`/`tail` (with one producer and one consumer they are disjoint, but it is required as soon as there are two of either). With condvars the count lives in your own variable and the predicate (`count == cap`, `count == 0`) is re-checked in a `while` loop after every wake-up.
- **Why `while`, not `if`.** `pthread_cond_wait` may return spuriously, and between `signal` and the waiter re-acquiring the mutex another thread can consume the item ("stolen wake-up"). With one consumer the bug is invisible; with two it corrupts the buffer (quiz Q14).
- **Go channel.** `make(chan T, cap)` is the same bounded buffer with the counting, locking and parking done by the Go runtime. Blocked goroutines are parked on the channel's wait queue in user space; an OS thread is not blocked, so there is no futex round-trip per item — which is why it wins at small capacities.

## Extension: P producers, C consumers (`pc_mpmc.c`)

```bash
gcc -Wall -Wextra -O2 -pthread solution/pc_mpmc.c -o pc_mpmc
./pc_mpmc 4 4 250000 64
```

Captured on aos-lab, 2026-11-15:

```
P=4 C=4 items=1000000 sum=500000500000 OK
```

- Producer `p` sends `p*per+1 … p*per+per`, so the values are exactly 1…P·per and the expected sum is known.
- Shutdown: `main` joins all producers, then puts **one poison pill (0) per consumer**. Each consumer exits on the first 0 it gets, so every consumer exits exactly once and no real item is lost (the pills are queued after all real items, FIFO).
- Alternative: a `closed` flag set under the mutex plus `pthread_cond_broadcast(&not_empty)`; consumers exit when `count == 0 && closed`.
