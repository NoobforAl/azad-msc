# Lab 05.3 — Solution to the extension (group commit)

```bash
bash solution/group-commit.sh
```

Real output (aos-lab, Linux 6.18.63, 2026-11-15; the VM was quieter than during part 1, so fsync is ~3 ms here):

```text
== 1 writer(s) x 300 fsync'd records each
fsync       300 x 4096 B: total    954.8 ms | per record: mean   3182.6 us  p50   3008.5 us  p99   5506.1 us  max   6030.8 us

@fsync_calls: 300
@jbd2_commits: 300
== 4 writer(s) x 300 fsync'd records each
fsync       300 x 4096 B: total   1617.2 ms | per record: mean   5390.5 us  p50   5133.2 us  p99  11202.8 us  max  13091.9 us
fsync       300 x 4096 B: total   1620.2 ms | per record: mean   5400.8 us  p50   5112.7 us  p99  11827.1 us  max  13743.5 us
fsync       300 x 4096 B: total   1622.1 ms | per record: mean   5407.1 us  p50   5127.9 us  p99  11412.2 us  max  14802.0 us
fsync       300 x 4096 B: total   1623.6 ms | per record: mean   5411.8 us  p50   5133.8 us  p99  11550.0 us  max  14981.8 us

@fsync_calls: 1200
@jbd2_commits: 602
```

Interpretation:

- **One writer:** 300 `fsync()` → 300 journal commits. Each `fsync()` forces the running transaction to commit and waits for it (`ext4_fsync_journal()` → `ext4_fc_commit()`, which without the fast_commit feature calls `jbd2_complete_transaction()`).
- **Four writers:** 1 200 `fsync()` → only **602** commits, about 2 fsyncs per commit. While one commit is being written, the other writers' updates join the *next* running transaction; when it commits, every `fsync()` waiting on it returns together. That is **group commit**: one journal write + one flush pays for several callers.
- **Latency vs throughput:** each writer's p50 went from 3.0 ms to 5.1 ms (it often waits for a commit that is already in flight, then for its own), but the system did 1 200 durable records in 1.62 s = **741/s** instead of 300 in 0.95 s = **314/s**: 2.4× the throughput.
- Databases do the same thing in user space (PostgreSQL `commit_delay`, InnoDB group commit) to batch their own `fsync()`s.
- jbd2 has its own knob for this: it may wait briefly before committing when many handles are active (`j_min_batch_time` / `j_max_batch_time`, mount options `min_batch_time=` / `max_batch_time=` in µs).
