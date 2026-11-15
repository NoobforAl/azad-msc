# Lab 04.2 — Watch copy-on-write through `pagemap` and `smaps`

**Goal:** prove that after `fork()` parent and child share the same physical frames until one of them writes, and that each first write costs exactly one fault and one new frame.

Runs on: the aos-lab VM (`~/work/04-memory/02-cow-pagemap`). It needs `sudo` because since Linux 4.2 unprivileged readers get PFN = 0 from `/proc/self/pagemap`. Nothing in this lab is destructive.

## Steps

```bash
mkdir -p ~/work/04-memory/02-cow-pagemap && cd ~/work/04-memory/02-cow-pagemap
gcc -Wall -Wextra -O2 -o cow cow.c
sudo ./cow 64          # 64 MiB region; the child writes the first 32 MiB
./cow 16 | head -3     # without root, PFNs read as 0
```

## Code

[`cow.c`](cow.c):

1. `mmap` 64 MiB of private anonymous memory, set `MADV_NOHUGEPAGE` so each page is 4 KiB and one write means one COW, then `memset` it.
2. Print the pagemap entry of page 0 (present, "exclusively mapped" bit 56, PFN) and the VMA's `Rss`, `Shared_Dirty` and `Private_Dirty` from `/proc/self/smaps`.
3. `fork()`. The child prints the same values, writes one byte into every page of the first half while counting `ru_minflt`, and prints them again.
4. The parent waits on a pipe, then prints its own PFN and the byte it sees.

pagemap format: `Documentation/admin-guide/mm/pagemap.rst` (bit 63 present, bit 62 swapped, bit 56 exclusively mapped, bits 0–54 PFN).

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. This is a shared 8-vCPU guest, so expect different absolute numbers on your machine.

```
$ sudo ./cow 64
parent before fork  va=0x7de3eda00000 present=1 excl=1 pfn=0x11e516
parent before fork  Rss=65536 kB  Shared_Dirty=0 kB  Private_Dirty=65536 kB
child  after fork   va=0x7de3eda00000 present=1 excl=0 pfn=0x11e516
child  after fork   Rss=65536 kB  Shared_Dirty=65536 kB  Private_Dirty=0 kB
child  after write  va=0x7de3eda00000 present=1 excl=1 pfn=0x11d498
child  after write  Rss=65536 kB  Shared_Dirty=32768 kB  Private_Dirty=32768 kB
child  wrote 8192 pages -> 8193 minor faults (COW)
parent child wrote  va=0x7de3eda00000 present=1 excl=1 pfn=0x11e516
parent byte[0]=0xaa (child wrote 0x55 into its own copy)
parent child exited va=0x7de3eda00000 present=1 excl=1 pfn=0x11e516
```

```
$ ./cow 16 | head -3      # not root: PFN hidden
parent before fork  va=0x78402a800000 present=1 excl=1 pfn=0x0
parent before fork  Rss=16384 kB  Shared_Dirty=0 kB  Private_Dirty=16384 kB
child  after fork   va=0x78402a800000 present=1 excl=0 pfn=0x0
```

## What to observe

- **Same PFN after `fork`**: one frame is mapped in two page tables. `excl` drops to 0.
- `Shared_Dirty` ≈ 64 MiB in the child right after `fork`, even though the child has written nothing. These are the parent's dirty pages, now shared.
- After the writes, `Private_Dirty` ≈ 32 MiB and there are 8193 minor faults: one COW fault for each of the 8192 pages written, plus one more. Each one went through `do_wp_page()` → `wp_page_copy()`.
- The child's PFN for page 0 **changed**. The parent's did not, and `excl` is back to 1 on both sides. The writer gets the copy.
- The parent still reads `0xaa`. The child's `0x55` went into its private copy.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `pfn=0x0` everywhere | not root (PFN hidden since 4.2) | `sudo ./cow 64` |
| `Shared_Dirty` is 0 after `fork` | THP gave you 2 MiB pages and `smaps` counts them differently, or the VMA merged with a neighbour | keep `MADV_NOHUGEPAGE`. `cow.c` finds the VMA by address. |
| minor faults ≠ 8192 | a few extra faults come from `printf`/stack pages | the difference should be small (< 10) |

## Extension task

Turn THP on for the region (`MADV_HUGEPAGE`) and repeat. How many COW faults are there now, and does the child get 2 MiB copies or a split into 4 KiB pages? Use `AnonHugePages` in `smaps` and `thp_split_pmd` / `thp_fault_alloc` in `/proc/vmstat` (before and after) to decide. No solution is given.

Solution notes: [`solution/answers.md`](solution/answers.md).
