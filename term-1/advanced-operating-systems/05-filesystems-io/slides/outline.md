# 05 · File Systems & I/O — slide outlines

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced OS (user = teal, kernel = amber, hardware = violet, data = green).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 18 |
| Lab 05.1 read() call chain | [`labs/01-read-call-chain.en.html`](labs/01-read-call-chain.en.html) | [`labs/01-read-call-chain.fa.html`](labs/01-read-call-chain.fa.html) | 7 |
| Lab 05.2 Page cache | [`labs/02-page-cache.en.html`](labs/02-page-cache.en.html) | [`labs/02-page-cache.fa.html`](labs/02-page-cache.fa.html) | 7 |
| Lab 05.3 fsync & writeback | [`labs/03-fsync-writeback.en.html`](labs/03-fsync-writeback.en.html) | [`labs/03-fsync-writeback.fa.html`](labs/03-fsync-writeback.fa.html) | 7 |
| Lab 05.4 I/O schedulers | [`labs/04-io-schedulers.en.html`](labs/04-io-schedulers.en.html) | [`labs/04-io-schedulers.fa.html`](labs/04-io-schedulers.fa.html) | 7 |
| Lab 05.5 io_uring copy | [`labs/05-io-uring-copy.en.html`](labs/05-io-uring-copy.en.html) | [`labs/05-io-uring-copy.fa.html`](labs/05-io-uring-copy.fa.html) | 7 |
| Lab 05.6 ext4 crash | [`labs/06-ext4-crash.en.html`](labs/06-ext4-crash.en.html) | [`labs/06-ext4-crash.fa.html`](labs/06-ext4-crash.fa.html) | 7 |

Lab decks are generated: `python _shared/tools/labdeck.py term-1/advanced-operating-systems/05-filesystems-io/slides/labs.content.py`. Edit `labs.content.py`, never the generated HTML.

Open through a local web server so the relative theme path resolves: `python -m http.server` at the repo root, then `http://127.0.0.1:8000/term-1/advanced-operating-systems/05-filesystems-io/slides/lesson.en.html`. `S` = speaker notes, `?print-pdf` = PDF export.

---

## Lesson deck

## Slide 1 — TITLE
Title: One read() from syscall to disk, and back · Fields: placeholders (§3.4)

## Slide 2 — SECTION
Eyebrow: Module 05 · Title: File Systems & I/O · Why: databases/logs/containers depend on what page cache, block layer and journal promise · Pills: VFS & page cache · blk-mq & schedulers · journaling & io_uring

## Slide 3 — AGENDA
VFS objects & fd table (current) → read() chain → page cache/writeback/fsync → blk-mq & schedulers → journaling → io_uring & OpenBSD

## Slide 4 — LAYER_STACK
Title: A cache hit stops at the page cache
Bands: user (role-1) · syscall boundary · VFS (role-2) · page cache (role-4) · block layer (role-2) · driver + device (role-3)
Notes: O_DIRECT skips the page-cache band

## Slide 5 — CONCEPT_DIAGRAM
Title: fd → open file → name → object · Diagram `assets/vfs-objects.svg` (process A + forked child, two struct files, dentry, inode, address_space, super_block, block device; syscall boundary)
Callouts: ① fork/dup share a struct file ② dentry = name, inode = object ③ one superblock per mount

## Slide 6 — FLOW_TIMELINE
ksys_read → vfs_read → new_sync_read → ext4 read_iter → filemap_read → filemap_get_pages · Takeaway: a miss starts readahead and a bio

## Slide 7 — CODE_WALKTHROUGH
`linux/fs/read_write.c · vfs_read() · v6.18.63` (L552-581, elided) · ① mode bits ② rw_verify_area / LSM ③ .read vs .read_iter dispatch

## Slide 8 — CODE_WALKTHROUGH
`linux/mm/filemap.c · filemap_get_pages() · v6.18.63` (L2640-2654) · ① RCU xarray batch ② empty = miss ③ page_cache_sync_ra

## Slide 9 — TERMINAL_DEMO
Real output of Lab 05.2 (`pcache evict / resident / read` cold vs warm) · caption: shared VM

## Slide 10 — CONCEPT_DIAGRAM
Title: blk-mq picks one of three paths · `assets/blk-mq.svg` (bio → submit_bio → request+tag → plug / elevator / direct → driver; completion dashed) · hot path = none + idle

## Slide 11 — TERMINAL_DEMO
Real output of Lab 05.4 scheduler table (job A throughput, job B reader latency vs writer)

## Slide 12 — FLOW_TIMELINE
jbd2 commit: lock → data (ordered) → metadata to journal → flush → commit (FUA) → checkpoint · Takeaway: crash before ⑤ = ignored

## Slide 13 — TERMINAL_DEMO
Real output of Lab 05.6 (A fsync'd survives, B unsynced lost, config rename result, journal replay message)

## Slide 14 — CONCEPT_DIAGRAM
Title: Two shared rings replace syscalls · `assets/io-uring-rings.svg` (SQ, io_uring_enter boundary, issue NOWAIT, io-wq/poll, CQ)

## Slide 15 — TWO_COLUMN_COMPARE
Linux (page cache, lock-free hit, RCU-walk, blk-mq, jbd2) vs OpenBSD (buf(9), bread + vnode lock, locked VOP_LOOKUP, N-step SCAN, fsck)

## Slide 16 — QUIZ
write() returned 4096 on ext4 data=ordered, power fails 2 s later: on disk? A journal · B ordered · C not guaranteed · D close()

## Slide 17 — QUIZ answer (DEFINITION)
Answer C · durable replace sequence · source notes/07, commit.c L546, fsync.c L141

## Slide 18 — SUMMARY
① VFS dispatch + page cache ② blk-mq/scheduler shape, fsync makes durable ③ journal = consistency, io_uring = fewer syscalls · Next: Module 06

---

## Lab decks (7 slides each, generated)

Goal (SECTION) → Setup (4 role cards) → Steps (TERMINAL_DEMO, commands from the README) → Expected output (real VM capture, `captured=` set) → What to observe (3) → Common pitfalls (symptom → fix) → Extension task. No solutions on slides.
