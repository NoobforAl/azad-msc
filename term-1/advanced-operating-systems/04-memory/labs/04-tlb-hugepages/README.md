# Lab 04.4 — TLB reach and huge pages, measured without hardware counters

**Goal:** measure the cost of TLB misses as ns per access for a random pointer chase over a growing number of pages. Compare 4 KiB pages with 2 MiB THP, and confirm with `smaps` that THP was actually used.

Runs on: the aos-lab VM (`~/work/04-memory/04-tlb-hugepages`). Total allocation is 512 MiB, safe on the 12 GB VM. User space only.

> **Why no `perf stat -e dTLB-load-misses`?** The VirtualBox guest exposes no hardware PMU: `perf stat -e cycles true` prints `<not supported>`. The counter-based variant is therefore **UNVERIFIED** here. The commands for a bare-metal machine are given at the end.

## Steps

```bash
mkdir -p ~/work/04-memory/04-tlb-hugepages && cd ~/work/04-memory/04-tlb-hugepages
gcc -Wall -Wextra -O2 -o tlbchase tlbchase.c
cat /sys/kernel/mm/transparent_hugepage/enabled      # need [madvise] or [always]
perf stat -e cycles true 2>&1 | grep cycles           # proves: no PMU in this guest

taskset -c 2 ./tlbchase 4k  512 | tee 4k.txt
taskset -c 2 ./tlbchase thp 512 | tee thp.txt
paste 4k.txt thp.txt | awk 'NR>2 {printf "%8s pages %8s MiB   4k %7s ns   thp %7s ns\n", $1, $2, $3, $6}'
```

`taskset` pins the run to one CPU, so migrations don't add noise.

## Code

[`tlbchase.c`](tlbchase.c):

- Allocates 512 MiB, aligned to 2 MiB, with `MADV_NOHUGEPAGE` or `MADV_HUGEPAGE`, and faults it all in.
- For N = 16, 32, …, 131072 pages it builds a random cyclic permutation over N pages. It stores **one pointer per page**, at a cache-line offset that varies with the page index, and follows the chain 20 M times.
- The data footprint is N × 64 B in both modes. The only difference between the two runs is how many pages, and so TLB entries and page walks, the chain spans.
- It prints `AnonHugePages` for the region from `/proc/self/smaps`.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. This is a shared 8-vCPU guest, so expect different absolute numbers on your machine. Single run. The 4k numbers at 128–512 MiB are noisy (948 ns at 128 MiB, 476 ns at 256 MiB), but they are always 3–6× the thp value.

```
$ cat /sys/kernel/mm/transparent_hugepage/enabled
always [madvise] never
$ perf stat -e cycles true 2>&1 | grep cycles
   <not supported>      cycles                                                                
$ taskset -c 2 ./tlbchase 4k  512
# mode=4k region=512 MiB AnonHugePages=0 kB
#    pages   span_MiB    ns/access
        16        0.1         5.58
        32        0.1         4.45
        64        0.2         5.95
       128        0.5        11.90
       256        1.0         8.19
       512        2.0        10.52
      1024        4.0        21.76
      2048        8.0        70.37
      4096       16.0        97.22
      8192       32.0       181.54
     16384       64.0       603.09
     32768      128.0       948.90
     65536      256.0       476.12
    131072      512.0       815.02
$ taskset -c 2 ./tlbchase thp 512
# mode=thp region=512 MiB AnonHugePages=524288 kB
#    pages   span_MiB    ns/access
        16        0.1         3.58
        32        0.1         4.08
        64        0.2         3.02
       128        0.5         6.45
       256        1.0         8.52
       512        2.0         9.96
      1024        4.0        20.81
      2048        8.0        90.49
      4096       16.0        99.03
      8192       32.0        75.12
     16384       64.0       157.67
     32768      128.0       149.66
     65536      256.0       152.53
    131072      512.0       172.45
$ paste 4k.txt thp.txt | awk ...
      16 pages      0.1 MiB   4k    5.58 ns   thp    3.58 ns
      32 pages      0.1 MiB   4k    4.45 ns   thp    4.08 ns
      64 pages      0.2 MiB   4k    5.95 ns   thp    3.02 ns
     128 pages      0.5 MiB   4k   11.90 ns   thp    6.45 ns
     256 pages      1.0 MiB   4k    8.19 ns   thp    8.52 ns
     512 pages      2.0 MiB   4k   10.52 ns   thp    9.96 ns
    1024 pages      4.0 MiB   4k   21.76 ns   thp   20.81 ns
    2048 pages      8.0 MiB   4k   70.37 ns   thp   90.49 ns
    4096 pages     16.0 MiB   4k   97.22 ns   thp   99.03 ns
    8192 pages     32.0 MiB   4k  181.54 ns   thp   75.12 ns
   16384 pages     64.0 MiB   4k  603.09 ns   thp  157.67 ns
   32768 pages    128.0 MiB   4k  948.90 ns   thp  149.66 ns
   65536 pages    256.0 MiB   4k  476.12 ns   thp  152.53 ns
  131072 pages    512.0 MiB   4k  815.02 ns   thp  172.45 ns
```

## What to observe

- **Up to 16 MiB of span (4096 pages)** both modes cost about the same: 4–10 ns while the chased lines fit in L1/L2, then ~70–100 ns at 8–16 MiB. That rise is data-cache and memory latency, which both runs share. At these sizes the L2 TLB (STLB) still covers most of the 4k pages.
- **From 32 MiB on the curves split.** 4k climbs to 180–950 ns, while thp stays at 75–170 ns. With 4 KiB pages every access now misses the TLB and needs a page walk. Under VirtualBox's nested paging (EPT/NPT) that walk is 2-D, and the PTE lines themselves miss in cache. With 2 MiB pages, 512 MiB is only 256 TLB entries.
- The gap at the same N (e.g. 603 vs 158 ns at 64 MiB) is the TLB-miss plus page-walk cost. This is what `dTLB-load-misses` would show directly on bare metal.
- `AnonHugePages` should be ≈ 524288 kB for `thp` and 0 for `4k`. If it isn't, THP didn't happen and the comparison is meaningless.
- The absolute numbers come from a shared 8-vCPU VirtualBox guest, so expect different numbers on your machine and between runs. The *shape* of the curve is the result.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `thp` same as `4k`, `AnonHugePages=0` | THP is `never`, or defrag couldn't find 2 MiB blocks | check `enabled`/`defrag`. Look at `thp_fault_fallback` in `/proc/vmstat`. |
| very noisy numbers | other agents/tenants on the host | run 3×, use the median, and pin with `taskset` |
| flat curve in both | the compiler optimized the loop away | the result `p` is printed (`!` on NULL), so the chase stays live |

## Counter-based variant (UNVERIFIED on this VM)

```bash
# bare metal only: hardware events needed
perf stat -e dTLB-loads,dTLB-load-misses,dtlb_load_misses.walk_completed ./tlbchase 4k 512
perf stat -e dTLB-loads,dTLB-load-misses,dtlb_load_misses.walk_completed ./tlbchase thp 512
```

Expected (not captured): misses per access near 0 below the TLB size, rising toward 1 for 4k at large N, and far lower for thp.

## Extension task

Add a third mode that uses **hugetlbfs** (`MAP_HUGETLB` after `sudo sysctl vm.nr_hugepages=256`, then **restore it to 0**), and a fourth that uses 1 GiB pages if `pdpe1gb` is in `/proc/cpuinfo`. Plot all curves on one chart and explain each knee. No solution is given.

Solution notes: [`solution/answers.md`](solution/answers.md).
