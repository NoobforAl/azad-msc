# 04 · Memory Management — slide outlines

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced OS (user = teal, kernel = amber, hardware = violet, data = green).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 18 |
| Lab 04.1 Count page faults | [`labs/01-page-faults.en.html`](labs/01-page-faults.en.html) | [`labs/01-page-faults.fa.html`](labs/01-page-faults.fa.html) | 7 |
| Lab 04.2 COW through pagemap | [`labs/02-cow-pagemap.en.html`](labs/02-cow-pagemap.en.html) | [`labs/02-cow-pagemap.fa.html`](labs/02-cow-pagemap.fa.html) | 7 |
| Lab 04.3 mmap shared vs private | [`labs/03-mmap-shared.en.html`](labs/03-mmap-shared.en.html) | [`labs/03-mmap-shared.fa.html`](labs/03-mmap-shared.fa.html) | 7 |
| Lab 04.4 TLB reach & huge pages | [`labs/04-tlb-hugepages.en.html`](labs/04-tlb-hugepages.en.html) | [`labs/04-tlb-hugepages.fa.html`](labs/04-tlb-hugepages.fa.html) | 7 |
| Lab 04.5 Slab caches | [`labs/05-slab-files.en.html`](labs/05-slab-files.en.html) | [`labs/05-slab-files.fa.html`](labs/05-slab-files.fa.html) | 7 |
| Lab 04.6 Thrashing & OOM | [`labs/06-oom-thrashing.en.html`](labs/06-oom-thrashing.en.html) | [`labs/06-oom-thrashing.fa.html`](labs/06-oom-thrashing.fa.html) | 7 |

Lab decks are generated from [`labs.content.py`](labs.content.py) with `python _shared/tools/labdeck.py term-1/advanced-operating-systems/04-memory/slides/labs.content.py`.

Open a deck through a local web server so the relative theme path resolves: run `python -m http.server` at the repo root, then open `http://127.0.0.1:8000/term-1/advanced-operating-systems/04-memory/slides/lesson.en.html`. Press `S` for speaker notes, and add `?print-pdf` to the URL for PDF export.

---

## Lesson deck

## Slide 1 — TITLE
Title: From a faulting instruction to a mapped page · Fields: placeholders from §3.4

## Slide 2 — SECTION
Eyebrow: Module 04 · Title: Memory Management · Why: RAM is allocated on first touch, shared until written, reclaimed under pressure · Pills: page faults · TLB & huge pages · buddy · SLUB · reclaim

## Slide 3 — AGENDA
Address space / page tables / TLB (current) → fault path → demand paging & COW → buddy, SLUB, reclaim → huge pages, thrashing, OOM, UVM

## Slide 4 — LAYER_STACK
Bands: user (role-1) → boundary "#PF: Ring 3 → Ring 0" → kernel mm (role-2) → hardware TLB/MMU/CR3 (role-3) → data frames/page cache/swap (role-4)

## Slide 5 — MEMORY_LAYOUT
Title: A process sees 128 TiB, described by VMAs · memmap kernel/hole/stack/mmap/heap/ELF · Callouts: maps line = VMA; maple tree; VMA is a promise

## Slide 6 — CONCEPT_DIAGRAM
Title: Four 9-bit indexes plus a 12-bit offset · `assets/page-walk.svg` (VA fields, CR3 → PGD → PUD → PMD → PTE → frame; MMU band) · Source: `pgtable_64_types.h` L50-80

## Slide 7 — TERMINAL_DEMO
Title: Huge pages flatten the TLB-miss curve · real `tlbchase` output 4k vs thp (Lab 04.4) · caption: no PMU, counters UNVERIFIED

## Slide 8 — FLOW_TIMELINE
#PF/CR2 → exc_page_fault → lock_vma_under_rcu → handle_mm_fault → __handle_mm_fault → handle_pte_fault (fragments move the highlight)

## Slide 9 — CODE_WALKTHROUGH
`linux/mm/memory.c · handle_pte_fault() · L6209-6226` · highlights: missing → swap → write-protect

## Slide 10 — CODE_WALKTHROUGH
`linux/mm/memory.c · do_wp_page() · L4133-4155` · highlights: reuse condition → wp_page_reuse → wp_page_copy

## Slide 11 — TERMINAL_DEMO
Title: Same frame after fork, new frame on write · real `sudo ./cow 64` output (Lab 04.2)

## Slide 12 — CONCEPT_DIAGRAM
Title: Buddy allocation: find the partner with XOR · `assets/buddy.svg` · caption `__find_buddy_pfn` L678

## Slide 13 — BENTO
SLUB (role-2, 7) · Reclaim (role-4, 5) · Huge pages (role-3, 5) · OOM killer (role-1, 7) · Takeaway: without swap only file pages and slab are reclaimable

## Slide 14 — TERMINAL_DEMO
Title: The OOM kill stays inside the cgroup · real `mem-cgroup.sh 128M ./hog 512` output (Lab 04.6)

## Slide 15 — TWO_COLUMN_COMPARE
Linux v6.18.63 vs OpenBSD UVM 8cada8c: entry, region tree/lock, COW rule, retry protocol

## Slide 16 — QUIZ
Reading 256 MiB of fresh malloc memory: what happens to RSS? (A/B/C/D)

## Slide 17 — DEFINITION (answer C)
"Use the zero-page for reads", `do_anonymous_page()` L5169

## Slide 18 — SUMMARY
① translation is hardware ② first touch / first write ③ buddy, SLUB, reclaim, OOM · Next: Module 05

---

## Lab decks (generated, 7 slides each)

Goal → Setup (4 role cards) → Steps (TERMINAL_DEMO, exact commands) → Expected output (real VM output, `captured` set) → What to observe → Common pitfalls → Extension task. Content per lab is in `labs.content.py`; solutions are never on slides.
