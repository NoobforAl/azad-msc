# 04 — Memory Management: quiz

15 questions: 6 conceptual (Q1, Q2, Q3, Q7, Q12, Q14), 5 read-the-code/output (Q4, Q5, Q6, Q8, Q11), and 4 debug/design (Q9, Q10, Q13, Q15). Three oral-exam questions follow, and answers are at the end. Farsi: [`quiz.fa.md`](quiz.fa.md).

## Questions

**Q1 (conceptual).** On x86-64 with 4-level paging, split the virtual address `0x00007f3a12345678` into PGD, PUD, PMD and PTE indexes and the page offset. If the address lies in a 2 MiB THP, what is the offset inside that huge page?

**Q2 (conceptual).** Why does Linux define `PGDIR_SHIFT` as the variable `pgdir_shift` on x86-64 instead of a constant, and what does `p4d_alloc()` do on a machine without LA57?

**Q3 (conceptual).** A context switch from process A to process B and back to A happens on one CPU. With PCID enabled, when does Linux still have to flush A's TLB entries? Name the two conditions from `choose_new_asid()`.

**Q4 (read code).** In this excerpt from `handle_pte_fault()` (v6.18.63, L6209–6226), name the user-space action that reaches each `return`:

```c
	if (!vmf->pte)
		return do_pte_missing(vmf);
	if (!pte_present(vmf->orig_pte))
		return do_swap_page(vmf);
	if (pte_protnone(vmf->orig_pte) && vma_is_accessible(vmf->vma))
		return do_numa_page(vmf);
	/* ... */
		if (!pte_write(entry))
			return do_wp_page(vmf);
```

**Q5 (read output).** Lab 04.1 on the VM printed:

```
mode=anon      pages=65536  minflt=65539  majflt=0  rss: 1540 -> 263816 KiB  131.5 ms
mode=anon-read pages=65536  minflt=65539  majflt=0  rss: 1540 -> 1672 KiB  62.9 ms
mode=thp       pages=65536  minflt=131  majflt=0  rss: 1536 -> 263812 KiB  67.1 ms
mode=file      pages=65536  minflt=537  majflt=1  rss: 1540 -> 263816 KiB  321.9 ms
mode=file-rand pages=65536  minflt=3  majflt=65536  rss: 1540 -> 263816 KiB  149234.3 ms
```

Explain each line: why `anon` and `anon-read` have the same fault count but different RSS, why `thp` has so few faults, and why `file-rand` has far more major faults and takes far longer than `file`.

**Q6 (read code).** In `do_wp_page()`, the reuse branch is taken when `PageAnonExclusive(vmf->page) || wp_can_reuse_anon_folio(folio, vma)`. After `fork()`, the parent writes to page X first, then the child writes to page X. How many copies happen, and which process gets each copy?

**Q7 (conceptual).** A block of order 2 starts at PFN `0x2a4`. What is the PFN of its buddy? If both are free, at what PFN does the merged order-3 block start?

**Q8 (read code).** SLUB's fast path does `__update_cpu_freelist_fast(s, object, next_object, tid)` without taking any lock. What could go wrong without `tid`, and what does the code do when the `cmpxchg` fails?

**Q9 (design).** A key-value store with a 40 GiB hash table runs on a 64-core machine. Random lookups are slow, and a profile shows much time in page walks. Propose two memory-management changes, explain how each helps, and name one risk of each.

**Q10 (debug).** A service in a cgroup with `memory.max=2G` and no swap is restarted every few hours. `memory.events` shows `oom_kill 3` and `max 9124`. `memory.pressure` shows `full avg60=35.00`. Which events happened in what order, and what is the earliest signal you could alert on?

**Q11 (read output).** Lab 04.3 printed:

```
file-shared  children=4 iters=1000000  expected=4000000  parent sees=4000000  file has=4000000
file-private children=4 iters=1000000  expected=4000000  parent sees=0  file has=0
anon-shared  children=4 iters=1000000  expected=4000000  parent sees=4000000
anon-private children=4 iters=1000000  expected=4000000  parent sees=0
```

Which line would change if the children used `(*ctr)++` instead of `__atomic_fetch_add`, and how? Why does `file-private` print 0 for both values?

**Q12 (conceptual).** List three different user-visible outcomes of a page fault that does *not* end with a successful mapping, and the kernel condition behind each.

**Q13 (debug).** A Redis-like server forks a child every 5 minutes to write a snapshot. During the snapshot, RSS of parent + child nearly doubles and latency spikes. THP is set to `always`. Explain the mechanism, and give two mitigations.

**Q14 (design).** A driver allocates a 64 KiB buffer with `kmalloc(GFP_KERNEL)` on every device open. After a week of uptime, opens start failing even though `MemAvailable` shows 6 GiB. Explain, and fix it.

**Q15 (debug).** A batch job in a 64 MiB cgroup reads the same 128 MiB file three times. Each pass takes as long as the first, and `workingset_refault_file` grows by ~32 000 per pass, but there is no swap. Is this a leak, thrashing or an OOM? What will happen if you set `memory.max=256M`?

## Oral-exam questions

**O1.** Walk me through everything that happens, hardware and kernel, between a user program's first `*p = 1` on freshly `malloc`ed memory and the store completing. Name the functions.

**O2.** Compare how Linux and OpenBSD's UVM represent anonymous memory and decide whether a write fault must copy. What does each design gain?

**O3.** "Huge pages are always good." Argue against it with three concrete costs, and say when you would still turn them on.

---

## Answers

**A1.** PGD 254, PUD 232, PMD 145, PTE 325, offset `0x678` (computed: `(va>>39)&511` and so on). In a 2 MiB page the offset is `va & 0x1fffff` = `0x145678`. [note 02]

**A2.** The number of levels is chosen at boot: with LA57 the top level shifts by 48, without it by 39. One kernel binary must support both, so the value is a variable. Without LA57 the p4d level is "folded": `p4d_alloc()` allocates nothing and returns the PGD entry viewed as a p4d. [note 02, `pgtable_64_types.h` L50]

**A3.** (1) A's mm no longer owns one of the CPU's 6 dynamic ASID slots (`TLB_NR_DYN_ASIDS`), because other address spaces evicted it round-robin, so it gets a new slot with `need_flush = true`. (2) A still owns its slot but its page tables changed while it was away: `ctxs[asid].tlb_gen < next_tlb_gen`. [note 03, walkthrough §7]

**A4.**
- `do_pte_missing`: the first touch of a never-mapped page, through `do_anonymous_page` for heap or stack and `do_fault` for an mmapped file or program text.
- `do_swap_page`: touching a page that was swapped out (or is under migration).
- `do_numa_page`: a NUMA-balancing hinting fault on a page the kernel made `PROT_NONE`.
- `do_wp_page`: writing to a COW-shared page after `fork`, writing to a zero-page mapping, or a write to a `MAP_SHARED` page that dirty tracking had write-protected.

[note 04]

**A5.**
- `anon`: one write fault per 4 KiB page, each allocating a zeroed page, so RSS grows by the full size.
- `anon-read`: one fault per page too, but each maps the shared zero page, so RSS stays flat.
- `thp`: about pages / 512 faults, because each fault maps a 2 MiB folio with one PMD.
- `file`: readahead brings in large batches, so there is only 1 major fault. The page cache holds large folios on ext4, and each minor fault maps a whole folio or a 64 KiB fault-around window, about 120 pages per fault here.
- `file-rand`: `MADV_RANDOM` turns readahead and fault-around off, so every page is its own synchronous read. That means ≈ 1 major fault per page and a much longer run.

[Lab 04.1, note 04]

**A6.** Two copies or one, depending on order and exit:
- When the parent writes X first, `PageAnonExclusive` is clear and the refcount is 2, so the parent gets a **copy** (`wp_page_copy`). The original frame is now mapped only by the child.
- When the child writes X, `wp_can_reuse_anon_folio()` sees it is the last user, so it **reuses** the original frame without copying.

Total: one copy, which goes to the first writer. [walkthrough §3.2]

**A7.** Buddy = `0x2a4 ^ (1 << 2)` = `0x2a4 ^ 0x4` = `0x2a0`. The merged block starts at `0x2a4 & 0x2a0` = `0x2a0` with order 3. [note 06]

**A8.** Between reading `c->freelist` and doing the `cmpxchg`, the task can be preempted and migrated, or an interrupt on the same CPU can allocate and free objects. The freelist head might then hold the *same pointer value* again with a different `next`, which is the ABA problem. The per-CPU transaction id is bumped on every operation, so a stale `tid` makes the double-word `cmpxchg` fail. On failure the code calls `note_cmpxchg_failure()` and jumps to `redo`, rereading the CPU pointer, `tid` and freelist. [note 07]

**A9.**
1. Back the table with 2 MiB THP (`MADV_HUGEPAGE`) or hugetlbfs (1 GiB if available). One TLB entry then covers 512× (or 262 144×) more memory and page walks become rare. Risk: compaction stalls and RSS bloat for THP; reserved, non-swappable memory for hugetlbfs.
2. Make it NUMA-aware: allocate each shard on the node of the threads that use it (`mbind`/`numactl --interleave` for a shared table), or pin threads. Risk: imbalance, or OOM on one node with `--membind`.

A third option is to reduce TLB shootdowns: avoid frequent `munmap`/`MADV_DONTNEED` and reuse memory.

[notes 03, 10; Lab 04.4]

**A10.**
1. The cgroup repeatedly hit `memory.max`: `max 9124` counts the times usage reached the limit and forced reclaim.
2. Reclaim kept the workload stalled, which shows as PSI `full avg60=35`: 35 % of the time all tasks waited on memory. This is thrashing on file pages.
3. Three times nothing could be reclaimed, and the memcg OOM killer fired (`oom_kill 3`).

Earliest signal: PSI `some`/`full` rising, or `memory.events` `high`/`max` counters (set `memory.high` below `max` to get throttling plus a `high` event before any kill). [notes 08, 10; Lab 04.6]

**A11.** `anon-shared` (and `file-shared`) would print less than 4 000 000, because `++` is a load-add-store and concurrent increments overwrite each other: lost updates (Module 03). `file-private` prints 0 because each child's first write COW-copied the page into its own anonymous memory (`do_cow_fault`/`wp_page_copy`). The parent's mapping and the file never saw any of it. [note 09, Lab 04.3]

**A12.**
- `SIGSEGV`, `SEGV_MAPERR`: there is no VMA at the address (`bad_area_nosemaphore`).
- `SIGSEGV`, `SEGV_ACCERR`: there is a VMA, but it forbids the access, e.g. a write to a read-only mapping (`access_error`).
- `SIGBUS`: the access is to a file mapping beyond EOF, or to a hardware-poisoned page (`VM_FAULT_SIGBUS`/`HWPOISON`).
- OOM kill or `SIGKILL`: allocation failed (`VM_FAULT_OOM` → `pagefault_out_of_memory()` or memcg OOM).
- For kernel-mode `copy_from_user`: `-EFAULT`, through the exception table.

[note 04]

**A13.** `fork()` shares all pages read-only. While the child is writing the snapshot, the parent keeps serving writes, and every first write to a page triggers a COW copy. With THP `always` each copy can be 2 MiB (or a split), so memory grows by up to the whole dataset. Each COW is also a fault, which adds latency, and huge COWs add compaction and zeroing on top. Mitigations:
- set THP to `madvise`/`never` (Redis's own warning);
- reduce the write rate during the snapshot, or snapshot from a replica;
- use a snapshot method that avoids `fork` (e.g. incremental or log-based);
- make sure there is RAM headroom, with `overcommit_memory=1` as Redis recommends.

[note 05]

**A14.** `kmalloc(64 KiB)` is larger than the biggest `kmalloc-8k` cache. It goes straight to the page allocator as an **order-4** contiguous block. After long uptime physical memory is fragmented: plenty of free pages, but no free 16-page runs (`/proc/buddyinfo` shows zeros at order ≥ 4). Fixes:
- `kvmalloc()`, which falls back to `vmalloc`, so it needs only order-0 pages, virtually contiguous;
- allocate the buffer once at probe time and reuse it;
- use scatter-gather.

Compaction may help temporarily. [notes 06, 07]

**A15.** It is thrashing: the working set (128 MiB) is bigger than the limit (64 MiB), so each pass evicts the pages the next pass needs. That is ~32 768 pages per pass, which matches the refault count. It is not a leak (usage is flat at the limit) and not an OOM (file pages can always be reclaimed). With `memory.max=256M`, pass 1 still faults everything in, passes 2–3 hit the page cache with ~0 major faults, and they are much faster. [notes 08, 10; Lab 04.6 part C]

**O1 (outline).**
1. `malloc` → `mmap`/`brk` created a VMA only.
2. The store misses the TLB, the MMU walk finds no PTE, and the CPU raises #PF (error code W|U, CR2 = VA).
3. `exc_page_fault` → `handle_page_fault` → `do_user_addr_fault`: `lock_vma_under_rcu`, then `access_error` is ok.
4. `handle_mm_fault`: memcg and MGLRU hooks.
5. `__handle_mm_fault`: allocate the PUD, PMD and PTE tables if they are missing, and try THP.
6. `handle_pte_fault` → `do_pte_missing` → `do_anonymous_page`: `pte_alloc`, `alloc_anon_folio` (buddy, via PCP lists) zeroed, rmap, `set_pte`, `MM_ANONPAGES++`.
7. `mm_account_fault` (`min_flt++`), `iret`, and the store re-executes and hits the TLB after the walk.

**O2 (outline).** Linux:
- anon folios plus an `anon_vma` reverse map;
- COW decided by `PageAnonExclusive` and the refcount (`wp_can_reuse_anon_folio`);
- VMAs in a maple tree with per-VMA locks.

This uses little metadata and scales well for multi-threaded faults.

UVM:
- an explicit `vm_anon` per private page, with `an_ref`, collected in a per-entry `amap` (the upper layer) above the `uvm_object` (the lower layer);
- COW iff `an_ref > 1`, with "promotion" of lower-layer pages into new anons;
- an `ERESTART` retry loop.

This is simpler to reason about and audit, but costs per-page anon structures.

**O3 (outline).** Costs:
1. Fault latency: zeroing 2 MiB, plus compaction or direct reclaim to find a free 2 MiB block.
2. Internal fragmentation and RSS bloat: touching 1 byte commits 2 MiB, and sparse heaps balloon.
3. Expensive COW and splits: `fork`-heavy servers copy 2 MiB at a time, and a partial `mprotect`/`munmap` splits the PMD.
4. khugepaged CPU use.

Turn them on (`madvise` per region, or hugetlbfs) for large, dense, long-lived, randomly accessed memory: databases' buffer pools, JVM heaps, VM guest RAM, HPC arrays. Lab 04.4 shows the gain.
