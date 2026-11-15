# Lab 05.2 — Page-cache hit vs miss

**Goal:** measure a cold (miss) and a warm (hit) read of the same 256 MiB file, see how many folios the kernel inserts into the page cache, and do it **without** `echo 3 > /proc/sys/vm/drop_caches`, by evicting only this file.

Runs on: the lab VM or any Linux machine (bpftrace step needs `sudo`). Disk use: 256 MiB. Time: ~20 min.

## Steps

```bash
cd ~/work/05-filesystems-io/labs/02-page-cache
gcc -Wall -Wextra -O2 -o pcache pcache.c          # zero warnings
dd if=/dev/urandom of=big.bin bs=1M count=256 status=none; sync big.bin
./pcache evict big.bin      # posix_fadvise(POSIX_FADV_DONTNEED) for this file only
./pcache resident big.bin   # mmap + mincore: how many pages are cached
./pcache read big.bin       # cold
./pcache read big.bin       # warm
bash run.sh                 # the same, plus bpftrace counts of folios added and readahead calls
```

## Code

[`pcache.c`](pcache.c), three subcommands:

- `resident`: `mmap()` the file (this does not read it) and call `mincore()`, which reports one bit per page: in the page cache or not. This is what `fincore(1)` and `vmtouch` do.
- `evict`: `fdatasync()` (dirty pages cannot be dropped) then `posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED)`, which ends in `mapping_try_invalidate()` for that inode only.
- `read`: 1 MiB `read()`s until EOF, timed with `CLOCK_MONOTONIC`.

[`run.sh`](run.sh) adds a bpftrace probe on the `filemap:mm_filemap_add_to_page_cache` tracepoint and kprobes on `page_cache_sync_ra` / `page_cache_async_ra`.

## Expected output

Real run, `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Shared 8-vCPU guest: expect different absolute numbers.

```text
$ bash run.sh
== evict this file only
evict: POSIX_FADV_DONTNEED done
== residency after evict
resident: 0/65536 pages (0.0%), 0 KiB of 262144 KiB
(fincore not installed: pcache resident is the same mincore() check)
== cold read (page-cache miss), counting folios inserted into the page cache
read: 256 MiB in 0.745 s = 344 MiB/s

@added_folios: 1049
@async_ra: 34
@sync_ra: 1
Cached: grew by 256 MiB (system-wide, noisy on a shared VM)
== residency after cold read
resident: 65536/65536 pages (100.0%), 262144 KiB of 262144 KiB
== warm read (page-cache hit)
read: 256 MiB in 0.079 s = 3256 MiB/s

@added_folios: 0
== warm read x3 (variance)
read: 256 MiB in 0.098 s = 2605 MiB/s
read: 256 MiB in 0.161 s = 1590 MiB/s
read: 256 MiB in 0.094 s = 2719 MiB/s
```

## What to observe

- **Cold 344 MiB/s vs warm ~1.6–3.3 GiB/s**: about 5–10× here. On the cold path every folio is allocated, read by the block layer and then copied; on the warm path `filemap_get_pages()` finds everything in the xarray and the cost is one `memcpy` per byte (note 04).
- **65 536 pages but only 1 049 folios added**: readahead allocates **large folios** (on average ~250 KiB each here), not 4 KiB pages. That is the folio work of Module 04 paying off in the page cache: fewer xarray entries, fewer LRU operations, bigger bios.
- **1 synchronous readahead, 34 asynchronous**: only the very first miss blocks the reader. After that, the `PG_readahead` marker triggers async readahead of the next window while the reader is still copying the current one.
- **Warm read adds 0 folios**: nothing was inserted, so nothing was read from the disk.
- `Cached:` in `/proc/meminfo` grew by exactly the file size. That memory is still "available" (`MemAvailable`): it can be reclaimed at any time.
- The VM's virtual disk is backed by a file on the Windows host, which has its own cache. A "cold" read here may be served from host RAM, so real hardware can show an even bigger gap.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `evict` does not drop anything | the pages are dirty (just written) or mapped by a process | `sync big.bin` / `fdatasync` first; close mappings |
| you used `echo 3 > drop_caches` | drops every process's cache on a shared machine and causes an I/O storm | evict one file: `pcache evict`, `dd if=F iflag=nocache count=0`, `vmtouch -e F` |
| `fincore: command not found` | `util-linux` build without it on this image | `pcache resident` gives the same answer |
| warm speed varies 2× between runs | other VM users, CPU frequency, cache misses in the CPU | run 3–5 times and report the median |

## Extension task

Evict the file, then read **only the first 4 KiB**, once normally and once after `posix_fadvise(POSIX_FADV_RANDOM)`. How many pages are resident after each? Explain with `page_cache_sync_ra()` and `FMODE_RANDOM`.

Solution: [`solution/ra_window.c`](solution/ra_window.c) and [`solution/README.md`](solution/README.md).
