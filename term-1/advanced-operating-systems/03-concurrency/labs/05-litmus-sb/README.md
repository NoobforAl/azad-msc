# Lab 03.5 — Memory-ordering litmus test: store buffering (SB) in C11 and Rust

**Goal:** observe, on a real x86-64 CPU, the one reordering x86-TSO allows (store → later load), count it over a million runs, and make it disappear with a full fence.

Runs on: the `aos-lab` VM (needs ≥ 2 CPUs). ARCH-SPECIFIC (x86-64): the numbers and the instructions are for x86; on Arm64 more outcomes appear. Notes: [03](../../notes/03-x86-tso-and-barriers.en.md), [02](../../notes/02-atomics-c11-memory-model.en.md). Lesson §4.2.

## Steps

```bash
cd ~/work/03-concurrency/05-litmus-sb
gcc -Wall -Wextra -O2 -pthread sb.c -o sb
rustc -O sb.rs -o sb_rs

./sb relaxed 1000000 0 1      # threads pinned to CPU 0 and CPU 1
./sb fence   1000000 0 1
./sb seqcst  1000000 0 1
./sb_rs relaxed 1000000
./sb_rs fence   1000000

# what did the compiler emit between the store and the load?
objdump -d --no-show-raw-insn sb | awk '/<thread_fn>:/,/^$/' | grep -E 'mfence|lock|xchg'
```

## Code

The test, per iteration `i`, with fresh variables `x[i] = y[i] = 0` (no reset race):

```text
T0: x[i] = 1; r0 = y[i];        T1: y[i] = 1; r1 = x[i];
```

Under sequential consistency at least one thread must see the other's store, so `r0 == 0 && r1 == 0` is impossible. A two-thread sense-reversing spin barrier starts both threads together for each iteration.

```c
case RELAXED:
    atomic_store_explicit(&mine[i], 1, memory_order_relaxed);
    atomic_signal_fence(memory_order_seq_cst);   // compiler barrier only
    out[i] = atomic_load_explicit(&other[i], memory_order_relaxed);
    break;
case FENCE:
    atomic_store_explicit(&mine[i], 1, memory_order_relaxed);
    atomic_thread_fence(memory_order_seq_cst);   // full barrier (StoreLoad)
    out[i] = atomic_load_explicit(&other[i], memory_order_relaxed);
    break;
```

`atomic_signal_fence` stops the *compiler* from swapping the store and the load, so any `0/0` in `relaxed` mode comes from the *hardware* (the store buffer). `sb.rs` does the same with `compiler_fence(SeqCst)` vs `fence(SeqCst)`.

## Expected output

> Captured on `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, 8 vCPU, gcc 13.3.0, rustc 1.75.0), 2026-11-15. Counts are timing-dependent; the zero/non-zero pattern is what must match.

```
$ ./sb relaxed 1000000 0 1
mode=relaxed iters=1000000 cpus=0,1
  r0=0 r1=0 :     35320  (3.5320%)  <- forbidden under SC
  r0=0 r1=1 :    481390
  r0=1 r1=0 :    478033
  r0=1 r1=1 :      5257
$ ./sb fence 1000000 0 1
mode=fence   iters=1000000 cpus=0,1
  r0=0 r1=0 :         0  (0.0000%)  <- forbidden under SC
  r0=0 r1=1 :    280164
  r0=1 r1=0 :    267923
  r0=1 r1=1 :    451913
$ ./sb seqcst 1000000 0 1
mode=seqcst  iters=1000000 cpus=0,1
  r0=0 r1=0 :         0  (0.0000%)  <- forbidden under SC
  r0=0 r1=1 :    428812
  r0=1 r1=0 :    438420
  r0=1 r1=1 :    132768
$ for i in 1 2 3; do ./sb relaxed 1000000 2 5 | sed -n 2p; done
  r0=0 r1=0 :     23155  (2.3155%)  <- forbidden under SC
  r0=0 r1=0 :     28274  (2.8274%)  <- forbidden under SC
  r0=0 r1=0 :     34254  (3.4254%)  <- forbidden under SC
$ ./sb_rs relaxed 1000000
rust mode=relaxed iters=1000000
  r0=0 r1=0 :     17318  (1.7318%)  <- forbidden under SC
  r0=0 r1=1 :    481123
  r0=1 r1=0 :    496039
  r0=1 r1=1 :      5520
$ ./sb_rs fence 1000000
rust mode=fence   iters=1000000
  r0=0 r1=0 :         0  (0.0000%)  <- forbidden under SC
  ...
$ ./sb_rs seqcst 1000000
rust mode=seqcst  iters=1000000
  r0=0 r1=0 :         0  (0.0000%)  <- forbidden under SC
  ...
$ objdump -d --no-show-raw-insn sb | awk '/<thread_fn>:/,/^$/' | grep -E 'mfence|lock|xchg'
    16a8:	lock xadd %eax,0x2984(%rip)        # 4034 <g_bar_count>
    1733:	xchg   %eax,(%rsi)
    1746:	lock orq $0x0,(%rsp)
    175b:	xchg   %eax,0x28d3(%rip)        # 4034 <g_bar_count>
    1763:	xchg   %eax,0x28c7(%rip)        # 4030 <g_bar_sense>
```

**Result: 7 relaxed runs, 7 × non-zero (1.7%–3.5% of a million iterations, i.e. 17,318–35,320 forbidden outcomes per run); 4 fenced or seq_cst runs, 0 each.**

## What to observe

1. **The "impossible" outcome is real.** In C, 35,320 of 1,000,000 iterations (3.5%) ended with both threads reading 0, on CPUs 0/1 and again on CPUs 2/5. Rust, same hardware, 17,318 (1.7%). Under any interleaving of the four instructions at least one thread must see a 1.
2. **It is the hardware, not the compiler**: the compiler barrier (`atomic_signal_fence` / `compiler_fence`) kept the store before the load in the program text. Each store waited in its core's store buffer while the following load read the other variable from cache.
3. **One fence removes it completely.** `atomic_thread_fence(seq_cst)` compiled to `lock orq $0x0,(%rsp)` (address `1746`), a locked no-op on the stack that drains the store buffer — the same trick as the kernel's `__smp_mb()` (`lock addl $0,-4(%rsp)`, `arch/x86/include/asm/barrier.h` L53). No `mfence` appears. The `seqcst` mode puts the barrier in the store instead: `xchg %eax,(%rsi)` (address `1733`; `xchg` with memory is implicitly locked).
4. **The other three outcomes shift with the fence**: with the barrier, `r0=1 r1=1` jumps from ~0.5% to 9–45%, because each thread now waits for its store to become visible before it loads.
5. **The kernel relies on exactly this.** The futex wake path skips the bucket lock when `waiters == 0`; it is safe only because of an `smp_mb()` on each side (`kernel/futex/waitwake.c` L58–96: "x==0 && y==0 is impossible"). Without those barriers the kernel would hit the outcome you just measured, and a waiter would sleep forever.

## Common pitfalls

| Symptom | Fix |
|---|---|
| `relaxed` shows 0 reorderings | both threads ran on one CPU (pinning failed, or a 1-vCPU VM): check `nproc`, pass two different CPU numbers |
| huge counts in `relaxed` without the compiler barrier | you are also measuring compiler reordering; keep `atomic_signal_fence` |
| looking for `mfence` in the disassembly | gcc 13 emits `lock orq $0x0,(%rsp)` for a seq_cst fence: also a full barrier |
| counts vary run to run | expected: timing-dependent; compare orders of magnitude, not exact numbers |

## Extension

Write the message-passing (MP) litmus test (`data = 1; flag = 1` ‖ `r0 = flag; r1 = data`) with relaxed atomics and only compiler barriers. C11 allows `flag=1, data=0`; does x86 ever produce it? Explain with the TSO rules, and say what would change on Arm64. Solution: [`solution/mp.c`](solution/mp.c), notes in [`solution/README.md`](solution/README.md).
