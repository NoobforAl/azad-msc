# Lab 03.1 — solution notes

## Fixes in the main program

| Fix | Code | Why it is correct | Cost seen on aos-lab |
|---|---|---|---|
| Lock | `pthread_mutex_lock(&g_lock); g_plain++; pthread_mutex_unlock(&g_lock);` | the three steps run as one critical section; lock = acquire, unlock = release | 89.6 ns/inc, 349 context switches |
| Atomic RMW | `atomic_fetch_add_explicit(&g_atomic, 1, memory_order_relaxed)` → `lock xadd` | one indivisible instruction; `relaxed` is enough because nothing else is published through the counter | 24.4 ns/inc |

## Extension: don't share (`sharded.c`)

```bash
gcc -Wall -Wextra -O2 -pthread solution/sharded.c -o sharded
./sharded packed 4 100000000
./sharded padded 4 100000000
```

Captured on aos-lab, 2026-11-15:

```
layout=packed threads=4 sum=400000000 time=6.489s ns/inc=16.22
layout=padded threads=4 sum=400000000 time=3.997s ns/inc=9.99
```

- Both sums are exact: each thread owns its slot, so there is no race. The program still uses relaxed atomic adds so the compiler cannot keep the slot in a register (which would hide the effect).
- **Packed**: the four 8-byte slots share one 64-byte cache line. Each core's write invalidates the line in the other three caches (MESI), so the line bounces between cores: **false sharing**. 16.2 ns per increment.
- **Padded**: each slot is `_Alignas(64)` on its own line; every core keeps its line in Modified state and never has to ask for it. 10.0 ns per increment (≈1.6× faster here; on bare metal the gap is usually much bigger — the VM's vCPUs share host cores and are noisy).
- The kernel does the same thing with `____cacheline_aligned_in_smp` (e.g. `struct futex_hash_bucket`, `kernel/futex/futex.h` L147) and per-CPU counters (`percpu_counter`).
