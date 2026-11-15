# 03 — TLB, ASID/PCID and shootdowns

> Module 04 · Memory Management · Linux v6.18.63 · `ARCH-SPECIFIC (x86-64)` · Farsi: [`03-tlb-pcid-shootdown.fa.md`](03-tlb-pcid-shootdown.fa.md)

## 1. Summary

- The TLB caches recent VA→PA translations; a hit costs ~0 extra cycles, a miss costs a page walk (note 02). Its **reach** (entries × page size) is only a few MiB with 4 KiB pages.
- PCID (x86's ASID) tags entries with an address-space id so a context switch does not have to flush; Linux keeps **6** dynamic PCIDs per CPU and recycles them round-robin.
- Changing a PTE that other CPUs may have cached requires a **TLB shootdown**: an IPI to every CPU in `mm_cpumask(mm)` (or a hardware broadcast with INVLPGB on new AMD CPUs).

## 2. Detailed explanation

**Intuition.** The page table lives in RAM; walking it on every load would multiply memory traffic by up to 5. The TLB is a small, fast, set-associative cache *inside the core* keyed by virtual page number. Typical sizes on a modern x86 core (vendor-specific, check `cpuid`): L1 dTLB ~64 entries for 4 KiB pages plus ~32 for 2 MiB, a unified L2 TLB (STLB) of ~1.5–3 K entries. With 4 KiB pages, 1536 entries cover **6 MiB**; with 2 MiB pages the same entries cover **3 GiB**. Programs with random access over large heaps (hash tables, graph code, databases, JVM GC) are TLB-bound — Lab 04 shows the cliff.

**What invalidates TLB entries?**
1. Writing `CR3` without the "no-flush" bit flushes all non-global entries of the old PCID.
2. `INVLPG addr` drops one page's entry on the current CPU.
3. `INVPCID` drops entries for a given PCID (single address, all, all-but-global).
4. Global entries (`_PAGE_GLOBAL`, kernel mappings) survive CR3 writes.

The TLB is **not coherent** with memory: if the kernel changes a PTE, CPUs that cached the old translation keep using it until they flush. Correctness rules therefore say: after making a mapping *less* permissive (unmap, write-protect for COW, migrate, reclaim), flush every CPU that might hold it *before* reusing the old page.

**PCID in Linux.** Without PCID, every context switch to a different `mm` flushes the TLB. With PCID, Linux gives each CPU a tiny cache of recently-run address spaces: `cpu_tlbstate.ctxs[0..TLB_NR_DYN_ASIDS-1]`, with `TLB_NR_DYN_ASIDS = 6` (`arch/x86/include/asm/tlbflush.h` L66). `switch_mm_irqs_off()` calls `choose_new_asid()` (walkthrough §7): if the next `mm` already owns a slot on this CPU, its entries are reused, and a flush is needed only if the `mm`'s **tlb_gen** advanced while it was away. With KPTI, each address space needs two PCIDs (kernel and user page tables), hence the "kPCID/uPCID" naming in `tlb.c` L63–90.

**Shootdown mechanics.** `flush_tlb_mm_range(mm, start, end, …)`:
1. `inc_mm_tlb_gen(mm)` — new generation number.
2. If other CPUs are in `mm_cpumask(mm)` → `flush_tlb_multi()`: send an IPI; each target runs `flush_tlb_func()`, which compares generations and flushes either individual pages (`INVLPG` up to `tlb_single_page_flush_ceiling` = 33 pages) or everything.
3. Otherwise flush locally.
4. New in 6.15+: `mm_global_asid()` + `broadcast_tlb_flush()` uses AMD INVLPGB to flush on all CPUs with one instruction, no IPIs (`VERSION-DEPENDENT`, hardware-dependent).

CPUs running other processes are trimmed lazily from `mm_cpumask`; CPUs in **lazy TLB** mode (running a kernel thread that borrowed the previous `mm`) may skip the IPI and flush when they next switch.

**Costs.** An IPI round-trip is microseconds; a multi-threaded program spread over 64 CPUs that calls `munmap`/`madvise(MADV_DONTNEED)` in a loop can spend most of its time in shootdowns. Remedies: batch unmaps (`mmu_gather`), keep threads of one process on fewer CPUs, reuse memory instead of returning it (allocators like jemalloc's decay), or hardware broadcast.

## 3. Diagram

```mermaid
sequenceDiagram
  participant C0 as CPU0 (munmap caller)
  participant MM as mm->tlb_gen
  participant C1 as CPU1 (same mm)
  participant C2 as CPU2 (other mm, lazy)
  C0->>C0: clear PTEs (page table lock)
  C0->>MM: inc_mm_tlb_gen() → gen 42
  C0->>C1: IPI flush_tlb_func(info gen 42)
  C1->>C1: INVLPG × n (or full flush), local gen = 42
  C1-->>C0: done
  Note over C2: not in mm_cpumask → no IPI; flushes on next switch_mm if behind
  C0->>C0: free the pages (safe now)
```

## 4. Worked example

The source for the PCID cache — `linux/arch/x86/mm/tlb.c · choose_new_asid() · v6.18.63 · L252-260` ([Elixir](https://elixir.bootlin.com/linux/v6.18.63/source/arch/x86/mm/tlb.c#L224)):

```c
	for (asid = 0; asid < TLB_NR_DYN_ASIDS; asid++) {
		if (this_cpu_read(cpu_tlbstate.ctxs[asid].ctx_id) !=
		    next->context.ctx_id)
			continue;

		ns.asid = asid;
		ns.need_flush = (this_cpu_read(cpu_tlbstate.ctxs[asid].tlb_gen) < next_tlb_gen);
		return ns;
	}
```

| Line | Meaning |
|---|---|
| `TLB_NR_DYN_ASIDS` | 6 slots per CPU. |
| `ctx_id` | a 64-bit id that is unique for the lifetime of the `mm` (never reused, unlike PCIDs). |
| `need_flush = tlb_gen < next_tlb_gen` | the slot is ours, but our page tables changed while we were away → flush this PCID now. |

**On the VM** (no PMU counters, so we count software events and kernel counters):

```bash
grep -o -w -E 'pcid|invpcid|invlpgb' /proc/cpuinfo | sort | uniq -c
grep -E 'nr_tlb_(remote|local)' /proc/vmstat
cat /sys/kernel/debug/x86/tlb_single_page_flush_ceiling   # sudo
```

```
      8 invpcid
      8 pcid
$ sudo cat /sys/kernel/debug/x86/tlb_single_page_flush_ceiling
33
```

There are no `nr_tlb_*` lines, because those counters exist only with `CONFIG_DEBUG_TLBFLUSH`, which is off in this kernel (`/boot/config-6.18.63-061863-generic`). `invlpgb` is absent, so the hardware-broadcast path is not used here.

Lab 04 then measures TLB reach directly: ns per access of a random pointer chase over N pages, with 4 KiB vs 2 MiB pages. The `perf stat -e dTLB-load-misses` variant is **UNVERIFIED** here because the VirtualBox guest exposes no hardware PMU.

## 5. Edge cases & pitfalls

- **The TLB is per core (shared by SMT siblings)**, not per process; "flushing a process's TLB" means flushing a PCID on each CPU where it ran.
- **Spurious faults.** Linux sometimes makes a PTE *more* permissive without flushing; a CPU with the stale read-only entry faults and the kernel just retries (`flush_tlb_fix_spurious_fault`, walkthrough §3).
- **KPTI doubles PCID use** and, on CPUs without PCID, makes every syscall flush the TLB — a large slowdown measured in 2018.
- **Huge pages have separate, smaller TLBs** on many CPUs; mixing sizes is fine, but don't expect 512× reach in every level.
- **Virtualization**: TLB misses become 2-D walks (EPT/NPT); huge pages on *both* host and guest matter. Absolute numbers from our VM are not bare-metal numbers.

## 6. Exam-style key points

- TLB reach = entries × page size; 4 KiB pages → MiB, 2 MiB pages → GiB.
- PCID tags TLB entries; Linux: 6 dynamic ASIDs per CPU, round-robin, `tlb_gen` decides if a flush is needed.
- Shootdown = IPIs to `mm_cpumask(mm)`; ≤ 33 pages → `INVLPG` each, more → full flush.
- TLB entries must be flushed before a freed page is reused — the ordering is what `mmu_gather` enforces.
- INVLPGB (AMD) / RAR (Intel) give hardware broadcast flushes; Linux uses global ASIDs for them since 6.15.

## 7. Links

- Lesson: [§2.3](../lesson.en.md#23-why-isnt-every-memory-access-four-extra-memory-reads)
- Walkthrough: [§7](../kernel-walkthrough.en.md#7-tlb-pcid-reuse-and-shootdowns--arch-specific-x86-64)
- Labs: [04.4 TLB reach and huge pages](../labs/04-tlb-hugepages/README.md)
- Quiz: Q3, Q9
