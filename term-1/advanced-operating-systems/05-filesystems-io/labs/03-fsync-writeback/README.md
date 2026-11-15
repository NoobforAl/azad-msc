# Lab 05.3 — The cost of `fsync`, and writeback in action

> **VM only for part 3** (it creates a loop device and changes that device's writeback limits). The script restores the limits on exit. Never change the global `vm.dirty_*` sysctls on the shared VM.

**Goal:** measure what each durability policy costs per write, watch buffered data sit dirty in RAM until the flusher writes it, and throttle a single device's dirty budget with per-BDI knobs.

Runs on: the lab VM, `~/work/05-filesystems-io/labs/03-fsync-writeback`. Disk use: < 1.5 GiB, all removed at the end. Time: ~30 min (part 1 alone takes 4–5 min on the shared VM).

## Steps

```bash
cd ~/work/05-filesystems-io/labs/03-fsync-writeback
gcc -Wall -Wextra -O2 -o wbench wbench.c        # zero warnings
./wbench fsync t.dat 2000 4096                   # one policy by hand
bash run.sh                                      # parts 1, 2, 3
PARTS="2 3" bash run.sh                          # skip the slow part 1
```

1. **Policies:** `wbench` writes 2000 × 4 KiB records with `buffered`, `fdatasync` after each, `fsync` after each, `O_DSYNC`, `O_SYNC`, and reports the per-record latency distribution.
2. **Writeback:** prints the global knobs (read-only), then writes 384 MiB with `dd` in the background and samples `Dirty`/`Writeback` from `/proc/meminfo` every 3 s for 60 s.
3. **Per-BDI limit:** makes an ext4 filesystem on a 1 GiB loop file, writes 256 MiB with `conv=fsync` twice (default limits, then `max_bytes = 8 MiB` + `strict_limit = 1` for that device only), counting `writeback:balance_dirty_pages` throttle events with bpftrace.

## Code

- [`wbench.c`](wbench.c): `open()` with `O_SYNC`/`O_DSYNC` or plain, then a write loop with optional `fsync()`/`fdatasync()`; per-record latency with `CLOCK_MONOTONIC`, sorted for p50/p99/max.
- [`run.sh`](run.sh): the three parts (`PARTS=` selects them). Part 3's `trap` puts `strict_limit=0` and `max_ratio=100` back, because BDI settings belong to the loop *device* and survive `losetup -d`.

## Expected output

Real runs, `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Part 1 is from `bash run.sh`, parts 2–3 from `PARTS="2 3" bash run.sh`. The VM was shared with six other agents doing I/O at the same time, so the fsync latencies are very noisy: an earlier run the same day measured p50 = 3.5 ms for `fdatasync` and 17.7 ms for `fsync`.

```text
== 1. durability policies, 2000 x 4 KiB on /dev/sda1 ext4
buffered   2000 x 4096 B: total      6.6 ms | per record: mean      3.3 us  p50      1.9 us  p99     75.5 us  max    202.7 us
fdatasync  2000 x 4096 B: total  74069.5 ms | per record: mean  37034.7 us  p50  22035.2 us  p99 190857.6 us  max 1904077.1 us
fsync      2000 x 4096 B: total  67909.6 ms | per record: mean  33954.8 us  p50  30950.5 us  p99 111781.8 us  max 343933.2 us
odsync     2000 x 4096 B: total  77118.2 ms | per record: mean  38559.1 us  p50  36943.3 us  p99 104343.8 us  max 142206.3 us
osync      2000 x 4096 B: total  54109.3 ms | per record: mean  27054.6 us  p50  21660.6 us  p99 108410.6 us  max 299432.7 us

== 2. global writeback knobs (read-only here)
  vm.dirty_ratio                20
  vm.dirty_background_ratio     10
  vm.dirty_bytes                0
  vm.dirty_background_bytes     0
  vm.dirty_expire_centisecs     3000
  vm.dirty_writeback_centisecs  500
== 2b. 384 MiB buffered write (below dirty_background_ratio); Dirty/Writeback every 3 s
  t=  0s Dirty=  15460 kB Writeback=     4 kB
  [dd returned]
  t=  3s Dirty= 339976 kB Writeback=     0 kB
  t=  6s Dirty= 340936 kB Writeback=     0 kB
  t=  9s Dirty= 290212 kB Writeback=     0 kB
  ...
  t= 27s Dirty= 288368 kB Writeback=     0 kB
  t= 30s Dirty=   1652 kB Writeback=     0 kB
  t= 33s Dirty=    108 kB Writeback=     0 kB
  ...

== 3. per-BDI limit on a loop device (only this device is throttled)
  /dev/loop0 -> /sys/class/bdi/7:0
  -- default limits: max_bytes=2393366528 strict_limit=0
268435456 bytes (268 MB, 256 MiB) copied, 0.577718 s, 465 MB/s
@throttle_events: 0
  -- limited:      max_bytes=8388384 strict_limit=1
268435456 bytes (268 MB, 256 MiB) copied, 1.0009 s, 268 MB/s
@max_pause_ms: 9
@throttle_events: 50
```

## What to observe

- **Buffered vs synced: ~4 orders of magnitude.** A buffered 4 KiB `write()` is a 2 µs memcpy into the page cache. Every synced variant waits for the virtual disk, the ext4 journal commit and a cache flush: tens of milliseconds here (the host disk is shared and backs seven guests' workloads). On a real NVMe SSD with power-loss protection, `fdatasync` is typically tens of µs; on consumer SSDs without it, often 1 ms or more.
- **`fdatasync` ≈ `O_DSYNC` and `fsync` ≈ `O_SYNC`** in principle; with this much noise, the ordering between them is not reliable in one run. The rule from the source: `fdatasync` skips a journal commit when only timestamps changed, but an *appending* writer changes `i_size` every time, so it still commits. Appending is the worst case for both.
- **Dirty data waits for 30 s.** 384 MiB is far below `dirty_background_ratio` (10 % of ~11 GiB), so the flusher does not start; the data sits dirty until it is `dirty_expire_centisecs` = 3000 (30 s) old, and then disappears almost at once (`t = 27 s → 30 s`). The small drop at 9 s is other activity (and this root fs is mounted with `commit=30`). `Writeback` stays near 0 because the burst finishes between 3 s samples. A crash at `t = 20 s` would have lost all 384 MiB (note 07).
- **The per-BDI limit only affects this device.** With an 8 MiB budget and `strict_limit`, `dd` on the loop filesystem was paused 50 times in `balance_dirty_pages()` (max pause 9 ms) and ran at ~268 MB/s instead of ~465 MB/s, while nothing else on the VM was throttled.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `fsync` costs microseconds | the file is on tmpfs, or the fs is mounted `nobarrier`, or the "disk" is RAM-backed | `findmnt -T .`; run on a real disk-backed fs |
| huge spread between runs | shared VM and shared host disk | run 3×, compare medians, report the environment |
| `Dirty` never drops in 7 s | you are below the background threshold; expiry is 30 s | sample for 60 s (as the script does) |
| other loop users suddenly slow | an earlier run was killed before restoring the BDI knobs | `echo 0 > /sys/class/bdi/7:N/strict_limit; echo 100 > .../max_ratio` |
| `losetup: failed to set up loop device` | no free loop devices / leftover from a crash | `losetup -a`, `sudo losetup -d /dev/loopN` |

## Extension task

Run 4 writers at once, each `fsync()`ing after every record. Count `fsync` calls (`ext4:ext4_sync_file_enter`) against journal commits (`jbd2:jbd2_commit_flushing`). What is **group commit**, and what does it do to per-writer latency and total throughput?

Solution: [`solution/group-commit.sh`](solution/group-commit.sh) and [`solution/README.md`](solution/README.md).
