# Module 05 — Quiz: File Systems & I/O

> 15 questions: Q1–Q6 conceptual (40 %), Q7–Q10 read code/output (27 %), Q11–Q15 debugging/design (33 %), then 3 oral-exam questions. Answers at the end.
> Farsi: [`quiz.fa.md`](quiz.fa.md) · Source pin: Linux v6.18.63

## Part A — Conceptual

**Q1.** Why does the VFS keep `struct dentry` and `struct inode` as separate objects? Give two situations that would be impossible or expensive if a name were a field of the inode.

**Q2.** Linux had `epoll` and Linux AIO (`io_submit`) before io_uring. Name two limitations of each for *regular-file* I/O that io_uring removes.

**Q3.** ext4 is mounted with the default `data=ordered`. A program appends 1 MiB to an existing log file with `write()` and does not call `fsync()`. Power fails 2 s later. List what the filesystem guarantees after reboot and what it does not.

**Q4.** `write()` returned 4096. Name three different ways those bytes can reach the disk later, and for each one the kernel component or knob that triggers it.

**Q5.** Why is the kernel's default I/O scheduler `none` for an NVMe SSD but `mq-deadline` for a single-queue virtio disk? Refer to the function that makes the choice.

**Q6.** A shell runs `exec 3<data; head -c 10 <&3; (head -c 10 <&3)`. Which 10 bytes does the subshell print, and which kernel object explains it?

## Part B — Read the code / output

**Q7.** In `vfs_read()`:

```c
	if (file->f_op->read)
		ret = file->f_op->read(file, buf, count, pos);
	else if (file->f_op->read_iter)
		ret = new_sync_read(file, buf, count, pos);
```

For `read()` on (a) an ext4 regular file, (b) `/dev/null`, (c) an ext4 directory: which branch runs and which function is finally called? (Hint: `drivers/char/mem.c` L644, `fs/ext4/dir.c` L698.)

**Q8.** In `lookup_fast()`:

```c
	if (nd->flags & LOOKUP_RCU) {
		dentry = __d_lookup_rcu(parent, &nd->last, &nd->next_seq);
		if (unlikely(!dentry)) {
			if (!try_to_unlazy(nd))
				return ERR_PTR(-ECHILD);
			return NULL;
		}
		if (read_seqcount_retry(&parent->d_seq, nd->seq))
			return ERR_PTR(-ECHILD);
```

(a) What does returning `NULL` cause the caller to do? (b) What does `-ECHILD` cause `do_filp_open()` to do? (c) Which concurrent operation makes `read_seqcount_retry()` return true?

**Q9.** Lab 05.5 ran `strace -c -f` on both copy programs for the same 512 MiB file with 128 KiB blocks. strace showed 4 098 `read` + 4 097 `write` calls for the read/write version and exactly 512 `io_uring_enter` calls for the io_uring version (QD 8). Explain both numbers from the code. Then explain the measured result: io_uring took 0.487 s vs 0.438 s, used 411 ms vs 211 ms of CPU, and had 2 066 vs 68 context switches. A bpftrace on `io_uring:io_uring_queue_async_work` counted 4 096 events, all for opcode 23 (WRITE).

**Q10.** mq-deadline has `writes_starved = 2`. Reads and writes are both queued continuously. Using `__dd_dispatch_request()`, describe the dispatch pattern of batches (ignore deadlines expiring), and what `fifo_batch = 16` changes.

## Part C — Debugging & design

**Q11.** `df` says `/var` is 100 % full, but `du -sh /var` shows only 40 % used. A daemon was rotating logs with `rm`. Explain the cause in terms of VFS objects, give one command to prove it, and two ways to free the space without rebooting.

**Q12.** After a power cut, a desktop app's settings file is **zero bytes**. The app saves with `open(O_TRUNC)` + `write()` + `close()`. Explain why (two mechanisms), and rewrite the save sequence so that after any crash the file is either the old or the new version.

**Q13.** A data-ingest service writes at 1.5 GB/s into a filesystem whose disk sustains 400 MB/s. Every few seconds its write latency jumps from microseconds to hundreds of milliseconds. Which kernel function is responsible, which knobs set the thresholds, and how would you confirm it with a tracepoint? Propose one fix that does not change global sysctls.

**Q14.** You run a PostgreSQL server (small random reads, `fsync` at commit) and a nightly backup (large sequential reads) on the same single SATA SSD exposed as one hardware queue. Users complain that queries are slow during the backup. Which scheduler(s) would you test, with which fio jobs, and what metric decides?

**Q15.** You write a character device driver `/dev/ring` whose `read()` returns bytes from a ring buffer filled by an interrupt handler. List what `read()` must do when the buffer is empty (blocking and non-blocking cases), what the IRQ handler must do, which `file_operations` member makes `epoll` work, and one thing that would crash the kernel.

## Oral exam

**O1.** Walk me through every layer a 4 KiB `read()` crosses on a cache miss on ext4 over NVMe, naming the data structure that represents the I/O at each layer (user buffer, `iov_iter`/`kiocb`, folio, bio, request, NVMe command).

**O2.** Compare Linux's page cache with OpenBSD's buffer cache: what is cached, where the filesystem sits on a hit, how size is controlled, and one advantage of each.

**O3.** "Journaling makes `fsync()` unnecessary." Argue against this statement using the jbd2 commit sequence and delayed allocation.

---

## Answers

**A1.** Names belong to directories, not files. (1) **Hard links**: one inode, several names; with the name in the inode you would need a list of (dir, name) pairs in every inode. (2) **Unlinked-but-open files**: the name is gone, the inode lives on. (3) **Negative dentries**: caching "this name does not exist" needs a name object with no inode. (4) The dcache can be searched by (parent, name) without reading inodes from disk. (Any two.)

**A2.** `epoll`: readiness-based, and regular files are always "ready", so a read still blocks on a page-cache miss; also one syscall per op plus `epoll_wait`. Linux AIO: only truly async with `O_DIRECT` (buffered I/O silently blocks in `io_submit`); a syscall to submit and another to reap; limited op set (no `openat`, `statx`, `fsync` well integrated). io_uring: completion-based, async buffered reads (`FOP_BUFFER_RASYNC`) and io-wq for the rest, batching and SQPOLL to remove syscalls, many opcodes.

**A3.** Guaranteed: the filesystem is consistent (journal replay); metadata never points at blocks containing stale data from other files (ordered mode); either the old size or a committed new size. Not guaranteed: that any of the 1 MiB is there. With delalloc, the blocks were not even allocated until writeback; if the 5 s commit / 30 s dirty expiry had not yet written them, the append is simply lost. Partial appends (some blocks) are possible if writeback ran partway.

**A4.** (1) Background flusher (`wb_workfn`) when dirty pages exceed `dirty_background_ratio` (10 %) or are older than `dirty_expire_centisecs` (30 s, checked every `dirty_writeback_centisecs` = 5 s). (2) Writer throttling in `balance_dirty_pages()` when dirty pages approach `dirty_ratio` (20 %) or a per-BDI limit (`max_ratio`/`max_bytes`/`strict_limit`). (3) Explicit `fsync`/`fdatasync`/`sync_file_range`/`syncfs`/`sync`. Also: memory reclaim writing back dirty folios, and `O_SYNC` for later writes.

**A5.** `elevator_set_default()` (`block/elevator.c` L728) installs `mq-deadline` only if `q->nr_hw_queues == 1` or the tag set is shared; otherwise it leaves `none`. Multi-queue devices are fast flash with internal scheduling, where the CPU cost and serialization of a scheduler outweigh reordering; single-queue devices are more likely rotational or slow, where ordering and read preference matter. Distros may override with udev rules.

**A6.** Bytes 11–20. fd 3 in the parent and child both point to the **same `struct file`** (fork copies fd table pointers), and `f_pos` lives in `struct file`. The parent's `head` advanced it to 10. (`head` may read more than 10 bytes into its buffer; GNU `head -c` on a seekable file seeks back to the exact position, so the next reader starts at 10.)

**A7.** (a) ext4 regular file: `ext4_file_operations` has no `.read`, only `.read_iter` → `new_sync_read()` → `ext4_file_read_iter()` → `generic_file_read_iter()` → `filemap_read()`. (b) `/dev/null`: `null_fops` has `.read = read_null` → first branch → returns 0 (EOF). (c) ext4 directory: `ext4_dir_operations.read = generic_read_dir` → first branch → `-EISDIR`.

**A8.** (a) `walk_component()` calls `lookup_slow()`: lock the directory inode and ask the filesystem (`i_op->lookup`, e.g. `ext4_lookup`); `try_to_unlazy()` already switched the walk to ref-walk mode. (b) `do_filp_open()` reruns `path_openat()` from the start **without** `LOOKUP_RCU` (ref-walk). (c) A rename (or other change) touching the parent directory, which bumps `parent->d_seq` between the RCU lookup and the check.

**A9.** read/write: 512 MiB / 128 KiB = 4096 blocks → 4096 `read` + 4096 `write`, plus one final `read` returning 0, plus a few from the dynamic loader's startup. io_uring: each `io_uring_submit_and_wait()` submits 8 linked READ→WRITE pairs and waits for 16 CQEs: 4096 / 8 = 512 enters (plus a few if a CQE was not yet visible and `io_uring_wait_cqe()` had to enter again). (The extra `read` and `write` in strace come from the dynamic loader and the final `printf`.) Why it is not faster: a large-block copy is dominated by two memcpys per byte (cache → user → cache), identical in both programs, and ~7 700 saved syscalls of ~1 µs each are worth < 10 ms. Worse, ext4 does not support non-blocking buffered writes (no `FOP_BUFFER_WASYNC` in `ext4_file_operations`), so every WRITE fails its `IOCB_NOWAIT` attempt and is **punted to an io-wq worker** (the 4 096 `queue_async_work` events, opcode 23): each block costs a wake-up and two context switches (≈ 2 066), and the workers' CPU is charged to the process (411 ms). Reads were not punted: ext4 has `FOP_BUFFER_RASYNC`, so page-cache misses complete via async callbacks.

**A10.** With reads and writes always pending, the read branch is taken, `dd->starved` increments each time a write could have been chosen; after it reaches `writes_starved` (2), the next choice goes to writes and resets `starved`. So the pattern is roughly: read batch, read batch, write batch, repeat. `fifo_batch = 16` means each "batch" can be up to 16 requests dispatched in sector order in the same direction before the direction decision is made again (`dd->batching < dd->fifo_batch`). Expired deadlines would interrupt sector order to serve the oldest request.

**A11.** The rotated log was unlinked (dentry removed, link count 0) but the daemon still holds an open `struct file`, which pins the inode and its blocks. `du` walks names, `df` asks the superblock for free blocks. Prove: `sudo lsof +L1 /var` or `ls -l /proc/*/fd 2>/dev/null | grep deleted`. Free: truncate through the descriptor (`: > /proc/<pid>/fd/<n>`), or make the daemon reopen its log (`SIGHUP`, `logrotate copytruncate`/`postrotate`), or restart it.

**A12.** (1) `O_TRUNC` + `write()` without `fsync`: the truncate (metadata) is committed by the journal within ~5 s, but the new data is delalloc and not yet written, so after the crash the file has size 0. (ext4's `auto_da_alloc` starts writeback on close after truncate, which narrows but does not close the window.) (2) Overwriting in place means there is no moment where an old complete copy exists. Fix: write `settings.tmp`, `fsync(tmp_fd)`, `close`, `rename("settings.tmp", "settings")`, then `fsync()` the directory fd. `rename()` is atomic, and each fsync orders data before the name switch.

**A13.** `balance_dirty_pages()` (`mm/page-writeback.c`) pauses the writing task once dirty memory nears the throttle threshold between `dirty_background_ratio` and `dirty_ratio` (or `*_bytes`), proportionally to the measured device bandwidth. Confirm with `tracepoint:writeback:balance_dirty_pages` (fields `pause`, `paused` in ms, `dirty`, `limit`), e.g. `bpftrace -e 'tracepoint:writeback:balance_dirty_pages { @pause_ms = hist(args->pause); }'`. Fixes: rate-limit the producer to disk speed; write with `O_DIRECT` and your own buffering; use `sync_file_range()` to start writeback early in small chunks; cap this device with `/sys/class/bdi/<maj:min>/max_bytes` + `strict_limit` so throttling is smooth and early; or put the service in a cgroup with `io.max`/`memory.high`.

**A14.** Test `mq-deadline` (read preference, deadlines) and `bfq` (per-process fairness; give the backup a low weight with `ionice -c3` or cgroup `io.weight`), plus `none` as the baseline, and `kyber` if available. fio: job 1 = 8 KiB random reads, iodepth 1–4, with `fsync` writes mimicking commits (`--rw=randrw --rwmixread=90 --fsync=1`); job 2 = sequential 1 MiB reads at high depth, running concurrently. Decide on the **p99/p99.9 completion latency of job 1** under load (not throughput), and check that the backup still finishes in its window (job 2 bandwidth). Lab 05.4's script has this structure.

**A15.** Empty buffer: if `file->f_flags & O_NONBLOCK`, return `-EAGAIN`; otherwise sleep on a wait queue with `wait_event_interruptible()` and return `-ERESTARTSYS` if interrupted by a signal; after waking, copy with `copy_to_user()` and return the byte count (short counts are fine). IRQ handler: acknowledge the device, put data in the ring (with a spinlock shared with `read`, using `spin_lock_irqsave` on the read side), `wake_up_interruptible()` the queue; no sleeping, no `copy_to_user`. `->poll` (calling `poll_wait()` and returning `EPOLLIN` when data is available) makes `select`/`poll`/`epoll` work. Crashes: dereferencing the user pointer directly, sleeping (or `copy_to_user`) while holding a spinlock or in the IRQ handler, or unloading the module while a file is open without proper `owner = THIS_MODULE`.

**O1 (outline).** user buffer + count → `ksys_read` (fd → `struct file`) → `vfs_read` → `new_sync_read` builds **`kiocb` + `iov_iter`** → `ext4_file_read_iter` → `filemap_read` → miss in **`address_space` xarray** → `page_cache_sync_ra` allocates **folios**, ext4 `->readahead` maps logical → physical blocks (extent tree) and builds **bios** → `submit_bio` → `blk_mq_submit_bio` → **`struct request` + tag** (plug, maybe scheduler) → nvme `queue_rq` builds an **NVMe command** in the SQ, rings the doorbell → completion IRQ (CQ entry) → `blk_mq_end_request` → `bio_endio` → folio uptodate, unlock → reader wakes in `filemap_update_page`/folio wait → `copy_folio_to_iter` → return bytes, update `f_pos`.

**O2 (outline).** Linux caches file pages per inode, unified with `mmap`; a hit never calls the filesystem; size = all free memory, reclaimed by LRU; advantage: speed and no double caching. OpenBSD caches filesystem blocks (`buf(9)`), `ffs_read` calls `bread()` for every block even on a hit; `mmap` pages live in UVM separately; size = `kern.bufcachepercent` (fallback 10 %); advantage: simple, predictable memory use, filesystem-block granularity suits metadata. See walkthrough §9.

**O3 (outline).** The journal makes **metadata** updates atomic and, in ordered mode, orders data before metadata, but only for data that is *in the transaction*. Delalloc data has no blocks until writeback, so it is not in any transaction; the commit timer (5 s) and dirty expiry (30 s) only bound the loss window. `fsync()` forces writeback, waits, forces the commit, and issues a device flush; it is also the only place a writeback error is reported. Without it, "consistent but stale or empty" is a valid post-crash state.
