# Lab 05.6 — Solution to the extension (durable replace)

```bash
gcc -Wall -Wextra -O2 -o solution/durable_save solution/durable_save.c    # zero warnings
bash solution/crash-fixed.sh     # crash-demo.sh, with the config save done by durable_save
```

`durable_save PATH CONTENTS` = `open(PATH.tmp, O_TRUNC)` → `write` → **`fsync(tmp)`** → `close` → **`rename(tmp, PATH)`** → `open(dir)` → **`fsync(dir)`**.

Real output (aos-lab, Linux 6.18.63, dm-flakey v1.5.0, 2026-11-15), last lines:

```text
  EXT4-fs (dm-0): recovery complete
  EXT4-fs (dm-0): mounted filesystem e9e4b0ed-7595-40e8-9bda-6aab1806988b r/w with ordered data mode. Quota mode: none.
== after the crash:
  A        19 bytes: A: written + fsync
  B         0 bytes:
  config   13 bytes: new contents
```

Interpretation:

- **`config` = new contents.** `fsync(tmp)` made the new data and inode durable; `rename()` swapped the name atomically; `fsync(dir)` committed the directory change. After any crash the name points at either the old or the new complete file.
- **`B` now exists with 0 bytes.** Nobody synced `B`, but ext4 has **one journal for the whole filesystem**. `B`'s creation (inode + directory entry) was in the same running transaction that `durable_save`'s `fsync()` forced to commit. `B`'s *data*, however, was delayed-allocated: no blocks, so nothing in the transaction, so a 0-byte file. This is the classic "zero-length file after crash" seen by applications that write without `fsync()`.
- The side effect also shows why `fsync()` on ext4 can be slow when other processes have lots of metadata changes pending: you pay for committing *their* transaction too (the "fsync of one file syncs everything" behaviour that `fast_commit` was designed to reduce).
- Without step 1 (`fsync(tmp)`), ext4's `auto_da_alloc` heuristic would normally still write the data before the rename commits, but that is an ext4 courtesy, not a guarantee; XFS and others make no such promise.
