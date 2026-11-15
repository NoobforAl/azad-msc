# Lab 05.2 — Solution to the extension

```bash
gcc -Wall -Wextra -O2 -o ra_window ra_window.c      # zero warnings
./ra_window ../big.bin normal
./ra_window ../big.bin random
cat /sys/block/sda/queue/read_ahead_kb
```

Real output (aos-lab, Linux 6.18.63, 2026-11-15):

```text
normal: read 4 KiB -> 4 pages (16 KiB) resident
random: read 4 KiB -> 1 pages (4 KiB) resident
8192
```

Why:

- **normal:** the first read misses, so `filemap_get_pages()` calls `page_cache_sync_ra()`. For a fresh file the initial window comes from `get_init_ra_size()` (`mm/readahead.c` L373): a small request is rounded up to a power of two and multiplied by 4 when it is ≤ 1/32 of the maximum window (here `read_ahead_kb` = 8192 KiB, so max = 2048 pages). 1 page × 4 = **4 pages = 16 KiB**. Lab 05.1 step 3 saw the same thing from the block layer: one bio of 16 384 bytes for a 4 KiB `read()`.
- **random:** `POSIX_FADV_RANDOM` sets `FMODE_RANDOM` on the `struct file` (`mm/fadvise.c` L87). `page_cache_sync_ra()` (L558) then uses *forced* readahead limited to the requested range: exactly **1 page**.
- The window is per **open file** (`file->f_ra`), so another process reading the same file keeps its own readahead state; the cached pages themselves are shared through the inode's page cache.

Takeaway: `FADV_RANDOM` (or `MADV_RANDOM` for mappings) is right for databases doing their own caching with random access; for sequential scans the adaptive window wins (Lab 05.2: 34 async readaheads kept the reader from ever waiting again after the first miss).
