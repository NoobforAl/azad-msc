# Module 05 — Videos

> Each URL was verified on 2026-11-15: the title and channel come from YouTube's oEmbed endpoint for that exact ID, and the duration from YouTube search metadata. Where the official upload's duration was not exposed, the duration of an identical mirror is given with `~`. All videos are in English.
> Watch order: 1 → 2 → 3 (fundamentals), then 4–8 for Linux internals.

| # | Title | Channel | URL | Duration | Level | Why it fits / what to watch |
|---|---|---|---|---|---|---|
| 1 | 6.S081 Fall 2020 Lecture 14: File Systems | MIT 6.S081 (uploaded by David Morejon; linked from the official schedule `pdos.csail.mit.edu/6.S081/2020/schedule.html`) | <https://youtu.be/ADzLv1nRtR8> | ~1:25 | Beginner | inode, directory, block layers of the xv6 file system. Maps directly to notes 01–02, with xv6's much simpler design to contrast with VFS + dcache. |
| 2 | 6.S081 Fall 2020 Lecture 15: Crash Recovery | MIT 6.S081 (same) | <https://youtu.be/7Hk2dIorDkk> | ~1:30 | Intermediate | The crash-consistency problem and xv6's write-ahead log: the mental model for jbd2 (note 07, Lab 05.6). |
| 3 | 6.S081 Fall 2020 Lecture 16: File System Performance and Fast Crash Recovery | MIT 6.S081 (same) | <https://youtu.be/CmDcf6rjFb4> | ~1:39 | Intermediate | Robert Morris on the ext3 journaling paper (Tweedie 1998): batching transactions, ordered data, why commits are asynchronous. This is ext4's ancestor; watch it before note 07 §2.3. |
| 4 | Kernel Recipes 2015 - Solving the Linux storage scalability bottlenecks - by Jens Axboe | Kernel Recipes | <https://www.youtube.com/watch?v=VIdKBD9-Ozg> | 1:02:54 | Advanced | The blk-mq maintainer explains why the single-queue block layer stopped scaling and how per-CPU software queues + hardware queues + tags fix it (note 05). 2015: the legacy path still existed then (removed in 5.0), and the elevators were not yet ported to blk-mq. |
| 5 | Understanding the Linux Block Layer-From Single Queue to Multi-Queue Architecture | DevConf | <https://www.youtube.com/watch?v=5HCbfOw7Dz8> | 42:12 | Intermediate | A recent (2025) overview of the same transition including the current mq schedulers; good companion to notes 05–06 and Lab 05.4. |
| 6 | Linux Storage Stack Explained - Werner Fischer, Thomas-Krenn.AG | The Linux Foundation | <https://www.youtube.com/watch?v=hCKruOlLPIQ> | 45:02 | Beginner | Walk from VFS through page cache, block layer, scheduler and drivers, based on the Linux Storage Stack Diagram. Use it as a map for the lesson's big-picture diagram. |
| 7 | Folios - Matthew Wilcox | The Linux Foundation | <https://www.youtube.com/watch?v=URTuP6wXYPA> | 59:43 | Advanced | Why the page cache moved from `struct page` to folios, by the author of the conversion. Explains the `folio_*` calls in `filemap_read()` (note 04, walkthrough §4). Watch the first ~30 min for motivation and page-cache impact. |
| 8 | Kernel Recipes 2022 - What's new with io_uring | Kernel Recipes | <https://www.youtube.com/watch?v=ToSRCSijRuE> | 45:58 | Advanced | Jens Axboe on the ring design, async buffered I/O, io-wq, registered resources and multishot (note 08, Lab 05.5). For a broader retrospective see also "The Design and Evolution of io_uring by Jens Axboe" (TigerBeetle, <https://www.youtube.com/watch?v=y4cb39pBp0I>, 41:36). |

Notes:
- Videos 1–3 use xv6, not Linux. The concepts transfer; the code does not.
- Video 4 predates the removal of the legacy request path (Linux 5.0) and the move of all I/O schedulers to blk-mq: treat its "future work" as history. `VERSION-DEPENDENT`.
- Not found: a recorded talk focused specifically on ext4/jbd2 internals by an ext4 maintainer. Searches returned only short explainer clips, so none is listed.
