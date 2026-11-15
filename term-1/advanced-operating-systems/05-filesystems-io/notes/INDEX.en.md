# Module 05 — Notes index

> Read in order; each note has Summary → Explanation → Diagram → Worked example → Pitfalls → Key points → Links. Farsi: [`INDEX.fa.md`](INDEX.fa.md)

| # | Note | Core question | Main source | Lab |
|---|---|---|---|---|
| 01 | [VFS objects: superblock, inode, dentry, file](01-vfs-objects.en.md) | How does one `read()` work on every filesystem? | `include/linux/fs.h`, `include/linux/dcache.h` | 05.1 |
| 02 | [Path lookup: namei, RCU-walk, ref-walk](02-path-lookup.en.md) | How does a string become a dentry, fast, on 64 CPUs? | `fs/namei.c`, `fs/dcache.c` | 05.1 |
| 03 | [File descriptor tables and `struct file`](03-fd-tables.en.md) | What is an fd, and why do forked processes share offsets? | `include/linux/fdtable.h`, `fs/file.c`, `fs/open.c` | 05.1 |
| 04 | [Page cache and writeback](04-page-cache-writeback.en.md) | Why is the second read 5–10× faster, and when does a write reach the disk? | `mm/filemap.c`, `mm/page-writeback.c`, `fs/sync.c` | 05.2, 05.3 |
| 05 | [The block layer and blk-mq](05-block-layer-blk-mq.en.md) | How does a bio become a hardware command without a global lock? | `block/blk-mq.c`, `drivers/block/loop.c` | 05.4 |
| 06 | [I/O schedulers](06-io-schedulers.en.md) | none, mq-deadline, bfq, kyber: which, when, at what cost? | `block/mq-deadline.c`, `block/elevator.c` | 05.4 |
| 07 | [Journaling and crash consistency](07-journaling-crash-consistency.en.md) | What survives a power cut, and why does `fsync` matter? | `fs/jbd2/commit.c`, `fs/ext4/fsync.c` | 05.6 |
| 08 | [io_uring](08-io-uring.en.md) | How do shared rings remove syscalls from the I/O path? | `io_uring/io_uring.c`, `io_uring/rw.c` | 05.5 |
| 09 | [Device drivers and character devices](09-device-drivers-char-devices.en.md) | How does `open("/dev/null")` reach driver code? | `fs/char_dev.c`, `drivers/char/mem.c` | 05.1 (ext.) |

Related: [lesson](../lesson.en.md) · [kernel walkthrough](../kernel-walkthrough.en.md) · [labs](../labs/) · [quiz](../quiz.en.md) · [videos](../videos.md)
