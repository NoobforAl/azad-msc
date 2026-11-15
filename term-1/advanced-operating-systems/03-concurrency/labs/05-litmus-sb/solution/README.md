# Lab 03.5 — solution notes

## Extension: message passing (`mp.c`)

```bash
gcc -Wall -Wextra -O2 -pthread solution/mp.c -o mp
./mp 1000000
```

Captured on aos-lab, 2026-11-15:

```
MP iters=1000000
  flag=0 data=0 :    476480
  flag=0 data=1 :     89213
  flag=1 data=0 :         0  <- allowed by C11 relaxed, never on x86-TSO
  flag=1 data=1 :    434307
```

- `flag=1, data=0` ("saw the flag, missed the data") needs either the writer's two stores to become visible out of order, or the reader's two loads to be satisfied out of order. x86-TSO forbids both: stores leave the store buffer in FIFO order, and loads are not reordered with other loads. So 0 in a million, and it would stay 0 in a billion.
- `flag=0, data=1` *is* allowed by TSO and appears (8.9%): the reader read `flag` before the writer's stores arrived, then `data` after.
- C11 with `memory_order_relaxed` **allows** `flag=1, data=0`, and Arm64/POWER produce it (weak store→store and load→load ordering). Relaxed MP code that "works" on x86 is still a bug. The portable fix is `atomic_store_explicit(&flag, 1, memory_order_release)` + `atomic_load_explicit(&flag, memory_order_acquire)`, which on x86-64 is still a plain `mov` each — free — and on Arm64 becomes `stlr` / `ldar`. ARCH-SPECIFIC: the Arm64 behaviour is not measured here (no Arm machine in this course).
- Compare with SB: TSO allows SB's forbidden-under-SC outcome but not MP's. "TSO = SC minus store→load".
