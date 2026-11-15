# Lab 04.4 — solution notes

## Reading the curve

- **Small N (≤ 64 pages):** every page has an L1 dTLB entry, so the cost is about one L1-cache hit per step, a few ns.
- **64 < N ≤ ~1.5 K:** L1 dTLB misses hit the L2 TLB (STLB). There is a small step up.
- **N > STLB reach:** every access needs a page walk.
  - In 4k mode the PTE lines for N pages also have to come from cache: 8 B per PTE, so one 64 B line covers 8 pages.
  - Under VirtualBox with nested paging, the guest walk is itself translated by the host: a 2-D walk. That is why the 4k curve keeps climbing to tens of ns at 512 MiB.
- **THP mode:** 512 MiB = 256 PMD-mapped pages, so the TLB covers the whole chase. What remains is data-cache and memory latency for N × 64 B lines, which is the same in both runs. The gap between the two curves at the same N is the TLB / page-walk cost.

## Checks

- `AnonHugePages` ≈ region size in thp mode. If it is 0, look at `thp_fault_fallback` in `/proc/vmstat`; a non-zero delta means THP fell back to 4 KiB pages.
- Run each mode three times and compare medians. The VM is shared, so single runs are noisy.

## The counter-based variant

The counter-based variant is UNVERIFIED because this VM has no PMU. On bare metal, `dTLB-load-misses / dTLB-loads` should go from about 0 to about 1 for 4k at large N, and stay low for thp.
