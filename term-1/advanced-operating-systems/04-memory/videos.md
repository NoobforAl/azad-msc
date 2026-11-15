# 04 — Memory Management: videos

Verified on 2026-11-15. Each watch page and its oEmbed record were opened, which confirmed the title, channel and upload date. YouTube served the watch pages behind a login check, so durations come from YouTube's search listing. Chapter times come from the chapter list embedded in the page, and they look auto-generated. The two MIT entries are also linked from the official course schedule, `pdos.csail.mit.edu/6.828/2020/schedule.html`. All videos are in English.

| # | Title · channel | URL | Duration | Level | Why it fits / what to watch |
|---|---|---|---|---|---|
| 1 | **6.S081 Lecture 4: Page Tables** · David Morejon (upload linked by the MIT schedule, 2020) | https://www.youtube.com/watch?v=f1Hpjty3TT8 | not confirmed | Intermediate | Multi-level page tables (Sv39), the TLB and the kernel/user mappings, all in real xv6 code. Watch before note 02. This is RISC-V xv6, not Linux: the idea is the same, the level count and bit layout differ. |
| 2 | **6.S081 Fall 2020 Lecture 8: Page Faults** · David Morejon (2020) | https://www.youtube.com/watch?v=KSYO-gTZo0A | not confirmed | Intermediate | Lazy allocation, zero-fill-on-demand, COW fork, demand paging and mmap, each built from the fault handler. Pairs with Labs 01–02. xv6, not Linux. |
| 3 | **CS162 Lecture 13: Memory 1: Address Translation and Virtual Memory** · John Kubiatowicz (uploaded 2021) | https://www.youtube.com/watch?v=1SJeLcI8otk | 1:28:41 | Beginner–Intermediate | Goes from base-and-bound to page tables. Watch **10:17–1:28:41** (the first 10 minutes review deadlock). Paging starts at ~1:12:16, and a Linux memory layout slide is at ~1:25:53. |
| 4 | **CS162 Lecture 15: Memory 3: Caching and TLBs (Con't), Demand Paging** · John Kubiatowicz (uploaded 2021) | https://www.youtube.com/watch?v=IBgkKX6DUTM | 1:27:15 | Intermediate | TLB organisation (33:38), what happens to the TLB on a context switch (44:18), demand paging (53:46), page-fault handling (1:01:08), thrashing (1:13:07). Covers notes 03–05 and 10. |
| 5 | **SREcon19 Asia/Pacific – Linux Memory Management at Scale: Under the Hood** · USENIX (Chris Down, 2019) | https://www.youtube.com/watch?v=beefUhRH5lU | 52:36 | Intermediate–Advanced | Swap (16:13), the OOM killer (18:59), reclaim (22:10), pre-OOM detection with PSI (29:30), cgroup v2 limits (34:43) and protection (44:59). This is the theory behind Lab 06. **Dated:** it predates MGLRU and systemd-oomd as defaults, but the ideas still hold. |
| 6 | **Kernel Recipes 2025 – Where does my memory come from?** · Kernel Recipes (Lorenzo Stoakes, 2025) | https://www.youtube.com/watch?v=vZBXXyBpK_M | 35:17 | Advanced | The best single tour of current Linux mm: VMAs (3:01), fault handling (6:57), physical allocation (7:56), folios (10:37), anonymous vs file memory (11:21), rmap (14:03), reclaim (15:43), swap and COW (19:29), compaction (20:43). Watch it after the walkthrough. |
| 7 | **SLUB: what's next?** · The Linux Foundation (Vlastimil Babka, 2024) | https://www.youtube.com/watch?v=KuUHyAS0Aag | 30:13 | Advanced | The SLUB maintainer on the allocator's direction after SLAB was removed in 6.8. Supports note 07. |
| 8 | **The slab allocator sheaves post-mortem** · Linux Plumbers Conference (Vlastimil Babka, 2026) | https://www.youtube.com/watch?v=HmGzVlULnPw | 40:17 | Advanced | Sheaves: per-CPU object arrays. The video description says they were merged in 6.18 for the maple-node/VMA caches, and that in 7.0 they became the default for all caches and the old cpu-slab layer was removed. **VERSION-DEPENDENT:** our pin, v6.18.63, still uses the `cpu_slab` fast path described in walkthrough §6. |
| 9 | **Multi-Gen LRU updates** · Linux Plumbers Conference (Rasmussen, Anbalagane, Xu, Xie; Google, 2024) | https://www.youtube.com/watch?v=gyWsmwqX1V4 | 14:17 | Advanced | A short status report on MGLRU in production. Supports note 08. No recorded MGLRU talk by its original author, Yu Zhao, was found. |

## Optional (also verified)

| Title · channel | URL | Duration | Use |
|---|---|---|---|
| Folios – Matthew Wilcox · The Linux Foundation (2022) | https://www.youtube.com/watch?v=URTuP6wXYPA | 59:43 | Why `struct folio` replaces many uses of `struct page` (notes 05, 07). |
| CS162 Lecture 16: Memory 4: Demand Paging Policies · John Kubiatowicz | https://www.youtube.com/watch?v=THoYkBItSkk | 1:29:40 | Replacement policies, clock and LRU (note 08). |
| [2014] Automatic NUMA Balancing by Rik van Riel · KVM Forum (2014) | https://www.youtube.com/watch?v=mjVw_oe1hEA | 45:30 | NUMA hinting faults (`do_numa_page`, note 10). **Old (2014):** the mechanism is still there, but details have changed. |
| Kernel Recipes 2025 – Filesystem and memory reclaim · Kernel Recipes (Matthew Wilcox) | https://www.youtube.com/watch?v=d2HvN0v7V24 | 49:59 | Reclaim vs filesystem deadlocks (`GFP_NOFS`, scoped allocation); a bridge to Module 05. |

## Gaps

- Neither the buddy allocator nor THP has a dedicated talk that passed verification. Use walkthrough §5, note 06 and the kernel documentation (`Documentation/mm/transhuge.rst` in the local checkout, and `docs.kernel.org/admin-guide/mm/transhuge.html`).
- CMU 15-213 virtual-memory lectures exist on YouTube only as unofficial re-uploads, so they are left out.
