# Lab 05.4 — Solution to the extension (cgroup weights under bfq)

```bash
bash solution/cgroup-weights.sh      # VM only: creates/removes /sys/fs/cgroup/aos05-{rd,wr}
```

Real output (aos-lab, Linux 6.18.63, 2026-11-15, RUNTIME = 8 s):

```text
bfq, equal weights           reader p50      420 us  p99      995 us | writer    21.5 MiB/s
bfq, reader 1000 / writer 10 reader p50      485 us  p99      905 us | writer     8.2 MiB/s
mq-deadline (weights ignored) reader p50    14615 us  p99   193987 us | writer   332.8 MiB/s
```

Interpretation:

- With **bfq**, the reader was already well protected with equal weights (p99 < 1 ms): bfq idles on the synchronous reader's queue, so the writer can only use the device between reads. Raising the reader to 1000 and lowering the writer to 10 cut the writer's share further (21.5 → 8.2 MiB/s) but barely changed the reader (p99 995 → 905 µs): the reader was not short of bandwidth, only of latency, and idling already fixed that.
- With **mq-deadline**, `io.bfq.weight` means nothing: weights are a bfq feature (`block/bfq-cgroup.c`, file `bfq.weight`, shown as `io.bfq.weight` in cgroup v2). The reader is back to tens of milliseconds behind write batches, while the writer gets 333 MiB/s.
- For proportional control that works with any scheduler, cgroup v2 offers `io.max` (absolute limits) and `io.latency` / `io.cost` (blk-iolatency, blk-iocost: QoS policies in the block layer, independent of the elevator).
- The cgroup files must be enabled on the parent first: `echo +io > /sys/fs/cgroup/cgroup.subtree_control` (the script does it if needed).
