# 04 — Memory Management: notes index

Read the notes in order. Each one has the same seven sections: summary, explanation, diagram, worked example, pitfalls, key points, and links. Farsi index: [`INDEX.fa.md`](INDEX.fa.md).

| # | Note | Core question | Lab | Quiz |
|---|---|---|---|---|
| 01 | [Virtual address space layout](01-virtual-address-space.en.md) | What is in a process's 128 TiB, and how does the kernel describe it? | 04.2 | Q1, Q11 |
| 02 | [4- and 5-level page tables](02-page-tables.en.md) | How does the MMU turn a VA into a PA? | 04.4 | Q1, Q2 |
| 03 | [TLB, ASID/PCID, shootdowns](03-tlb-pcid-shootdown.en.md) | Why is translation usually free, and when is it expensive? | 04.4 | Q3, Q9 |
| 04 | [The page fault path](04-page-fault-path.en.md) | What runs between the faulting instruction and its retry? | 04.1 | Q4, Q5, Q12 |
| 05 | [Demand paging & COW](05-demand-paging-cow.en.md) | When does RAM really get allocated, and what does `fork` copy? | 04.1, 04.2 | Q5, Q6, Q13 |
| 06 | [Buddy allocator](06-buddy-allocator.en.md) | Where do physical pages come from? | 04.6 | Q7, Q14 |
| 07 | [SLUB](07-slub.en.md) | How does the kernel allocate small objects without a lock? | 04.5 | Q8, Q14 |
| 08 | [Reclaim: LRU / MGLRU, kswapd](08-reclaim-lru-mglru.en.md) | What gets evicted when RAM is full? | 04.6 | Q10, Q15 |
| 09 | [`mmap`](09-mmap.en.md) | File vs anonymous, private vs shared: who sees the writes? | 04.3 | Q11, Q13 |
| 10 | [Huge pages, NUMA, thrashing & OOM](10-hugepages-numa-oom.en.md) | What happens at the limits? | 04.4, 04.6 | Q9, Q10, Q15 |

Suggested pairing: notes 01–03 → Lab 04.4; notes 04–05 → Labs 04.1 and 04.2; note 09 → Lab 04.3; note 07 → Lab 04.5; notes 06, 08 and 10 → Lab 04.6.
