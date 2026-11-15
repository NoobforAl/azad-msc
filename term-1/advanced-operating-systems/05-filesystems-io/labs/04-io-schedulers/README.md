# Lab 05.4 — Compare I/O schedulers with `fio`

> **VM only.** Creates a loop device, loads the `bfq` and `kyber-iosched` modules, and switches the loop device's scheduler. It never touches the scheduler of a disk other people use.

**Goal:** on the same device, measure (A) small random-read throughput and (B) the tail latency of a lone reader competing with a heavy sequential writer, under `none`, `mq-deadline`, `bfq` and `kyber`.

Runs on: the lab VM, `~/work/05-filesystems-io/labs/04-io-schedulers`. Disk use: 512 MiB, removed at the end. Time: ~20 min (each full run ≈ 80 s).

## Steps

```bash
cd ~/work/05-filesystems-io/labs/04-io-schedulers
bash sched-bench.sh              # RUNTIME=8 s per job by default
RUNTIME=5 bash sched-bench.sh    # quicker
cat /sys/block/loop0/queue/scheduler            # while it runs, from another shell
ls /sys/block/loop0/queue/iosched/              # the active scheduler's tunables
```

What the script does:

1. Creates a 512 MiB file and attaches it with `losetup --direct-io=on`, so the loop driver issues `O_DIRECT` I/O to the backing file and the requests really reach the virtual disk instead of the page cache.
2. `modprobe bfq kyber-iosched`, then for every scheduler listed in `/sys/block/loopN/queue/scheduler`:
   - **Job A:** `fio` 4 KiB random reads, `iodepth=32`, `ioengine=io_uring`, `direct=1`.
   - **Job B:** two jobs at once: a reader (4 KiB random reads, `iodepth=1`, `psync`) and a writer (1 MiB sequential writes, `iodepth=16`, `io_uring`).
3. Parses fio's JSON with a few lines of Python and prints one row per scheduler; resets the scheduler to `none` and detaches the loop device.

## Code

[`sched-bench.sh`](sched-bench.sh). Build command: none (fio 3.36 from Ubuntu).

## Expected output

Two real runs, back to back, `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. The loop file lives on the VM's virtual disk, which lives in a file on the Windows host shared with six other busy guests: **compare shapes, not values**.

```text
$ bash sched-bench.sh
device /dev/loop0: scheduler file = [none] mq-deadline bfq kyber
nr_hw_queues=1 nr_requests=128 rotational=1

scheduler        A:IOPS    A:p99(us) |   B:rd p50(us)   B:rd p99(us)   B:wr MiB/s
none               3548        31064 |          23462         219152        331.0
mq-deadline        4706        13828 |          50070         283116        174.5
bfq                3446        78119 |          13697         162529        648.6
kyber              3543        25559 |          21627         198181        353.2

$ bash sched-bench.sh            # second run
scheduler        A:IOPS    A:p99(us) |   B:rd p50(us)   B:rd p99(us)   B:wr MiB/s
none               3988        14877 |          17170         101188        609.7
mq-deadline        4643        12386 |          43778         219152        208.4
bfq                4310        15008 |            522           1057         10.6
kyber              4108        14746 |          23724         223347        373.3
```

## What to observe

- **The default is `none` here, not `mq-deadline`.** A loop device has one hardware queue, which would normally get `mq-deadline` (`elevator_set_default()`, note 06), but the loop driver sets `BLK_MQ_F_NO_SCHED_BY_DEFAULT` (`drivers/block/loop.c` L2042): it is a stacking device and the real scheduling happens on the backing disk. `sda` itself shows `[mq-deadline]`.
- **Job A (pure random reads):** all four are within ~30 % of each other, and the order changes between runs. With one queue of random 4 KiB reads there is nothing useful to reorder, so the scheduler's CPU cost and the host's noise dominate. `mq-deadline` was highest in both runs, likely from merging and sector-sorting of the 32 queued reads before they reach the host.
- **Job B (reader vs writer) is where they differ:**
  - `mq-deadline` gave the reader the *worst* latency (p50 44–50 ms) in both runs: it sends writes in `fifo_batch` = 16-request batches, and with 1 MiB writes one batch is 16 MiB in front of the next read. Its 500 ms read deadline is a guarantee against starvation, not a latency target.
  - `bfq` is the only one that can make the reader **fast**: in run 2 it served it at p50 0.5 ms / p99 1 ms by idling for the reader's next request and giving the writer only 10.6 MiB/s. In run 1 it did not (p50 13.7 ms, writer 649 MiB/s). bfq's idling decisions depend on measured think times and device speed, which a noisy virtual disk makes unstable.
  - `kyber` stays close to `none`: it throttles the write domain only when read latency misses its 2 ms target, and here the latency is dominated by the host, not by the guest's queue depth.
- **Trade-off made visible:** reader latency and writer bandwidth move in opposite directions (bfq run 2 vs none run 2). A scheduler chooses where on that curve you are.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| only `[none] mq-deadline` listed | bfq/kyber are modules, not loaded | `sudo modprobe bfq kyber-iosched` |
| `echo bfq > .../scheduler: Invalid argument` | name not in the list, or a typo | copy a name from the bracket list |
| loop device numbers huge and identical for all schedulers | `--direct-io=on` missing: you are benchmarking the page cache | check `cat /sys/block/loopN/loop/dio` = 1 |
| results flip between runs | shared VM + host disk cache | run 2–3 times; report all runs, as above |
| `losetup` leftovers after Ctrl-C | the trap did not run | `losetup -a`, then `sudo losetup -d /dev/loopN` |

## Extension task

Under `bfq`, put the writer in a cgroup with `io.bfq.weight` = 10 and the reader in one with 1000. Does the reader's p99 improve over plain `bfq`? What does `mq-deadline` do with the same cgroups?

Solution: [`solution/cgroup-weights.sh`](solution/cgroup-weights.sh) and [`solution/README.md`](solution/README.md).
