# Lab 04.1 — Count page faults

**Goal:** count the faults it costs to touch every page of a mapping, and explain each count with demand paging, the zero page, readahead/fault-around, and THP.

Runs on: the aos-lab VM (`~/work/04-memory/01-page-faults`). This lab is user-space only; nothing in it is destructive.

## Steps

```bash
mkdir -p ~/work/04-memory/01-page-faults && cd ~/work/04-memory/01-page-faults
gcc -Wall -Wextra -O2 -o touch touch.c            # zero warnings expected

./touch anon      256                             # write 1 byte per 4 KiB page
./touch anon-read 256                             # read only
./touch thp       256                             # MADV_HUGEPAGE
dd if=/dev/urandom of=data.bin bs=1M count=256 status=none
./touch file      256 data.bin                    # file mapping, readahead on
./touch file-rand 256 data.bin                    # MADV_RANDOM: no readahead

# the same counts, from perf's software events (no PMU needed)
perf stat -e page-faults,minor-faults,major-faults ./touch anon 256
rm -f data.bin
```

## Code

[`touch.c`](touch.c) maps the region, aligns it to 2 MiB, applies `MADV_NOHUGEPAGE`, `MADV_HUGEPAGE` or `MADV_RANDOM`, and touches one byte per 4 KiB. It reads `ru_minflt`/`ru_majflt` from `getrusage()` before and after, and RSS from `/proc/self/statm`. For file modes it first drops the file's own clean pages with `posix_fadvise(POSIX_FADV_DONTNEED)`, so it never has to touch the global `drop_caches`.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. This is a shared 8-vCPU guest, so expect different absolute times on your machine. `thp_fault_alloc` was read from `/proc/vmstat` after the runs.

```
$ ./touch anon 256 ; ./touch anon-read 256 ; ./touch thp 256
$ ./touch file 256 data.bin ; ./touch file-rand 256 data.bin
mode=anon      pages=65536  minflt=65539  majflt=0  rss: 1540 -> 263816 KiB  131.5 ms
mode=anon-read pages=65536  minflt=65539  majflt=0  rss: 1540 -> 1672 KiB  62.9 ms
mode=thp       pages=65536  minflt=131  majflt=0  rss: 1536 -> 263812 KiB  67.1 ms
mode=file      pages=65536  minflt=537  majflt=1  rss: 1540 -> 263816 KiB  321.9 ms
mode=file-rand pages=65536  minflt=3  majflt=65536  rss: 1540 -> 263816 KiB  149234.3 ms

$ perf stat -e page-faults,minor-faults,major-faults ./touch anon 256
mode=anon      pages=65536  minflt=65539  majflt=0  rss: 1540 -> 263816 KiB  260.0 ms
 Performance counter stats for './touch anon 256':
             65600      page-faults
             65600      minor-faults
                 0      major-faults
       0.306792689 seconds time elapsed
       0.038942000 seconds user
       0.230539000 seconds sys

$ grep -E '^thp_fault_(alloc|fallback) ' /proc/vmstat
thp_fault_alloc 128
thp_fault_fallback 0
```

The `thp` time varies a lot on this shared VM: one earlier run under load took 1831 ms for the same 128 faults, because each fault zeroes 2 MiB.

## What to observe

| Mode | Faults ≈ | Why (kernel path) |
|---|---|---|
| `anon` | 1 per page (65 536 for 256 MiB) | `do_anonymous_page()` allocates one zeroed page per write fault |
| `anon-read` | 1 per page, **RSS unchanged** | reads map the shared zero page (walkthrough §3.1) |
| `thp` | ≈ pages / 512 | `create_huge_pmd()` maps 2 MiB with one PMD entry |
| `file` | 1 major, ~540 minor (≈ 120 pages per fault) | readahead fills the page cache with **large folios** (ext4 enables them, `fs/ext4/inode.c` L5183), and each minor fault maps a whole folio (`finish_fault()`, `mm/memory.c` L5550) or a fault-around window. The batch size is `VERSION-DEPENDENT`. |
| `file-rand` | 1 **major** per page (65 536), ~150 s here | `MADV_RANDOM` disables readahead and fault-around, so every page is a separate I/O |

- `perf stat`'s `page-faults` should match `minflt + majflt` to within a few. The extra faults come from process start-up (the loader, libc, the stack).
- The time for `anon` is mostly zeroing pages plus the cost of each trap. Divide the time by the number of faults to get the cost of one minor fault on this VM.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `thp` shows as many faults as `anon` | THP is `never`, or the region isn't 2 MiB-aligned | `cat /sys/kernel/mm/transparent_hugepage/enabled`. `touch.c` already aligns the region. |
| `file` shows 0 major faults | the file's pages were still in the page cache (they were dirty, so `DONTNEED` skipped them) | the program calls `fdatasync()` first; run it again |
| `perf: ... not supported` | you asked for a hardware event | use only software events here (no PMU in this VM) |

## Extension task

Make `anon` mode take **one** fault per 64 KiB instead of one per 4 KiB **without** using THP. Hint: look at mTHP (`/sys/kernel/mm/transparent_hugepage/hugepages-64kB/enabled`) or `MAP_POPULATE`. Then explain which one really removes faults and which one just moves them to `mmap()` time. Measure both. No solution is given.

Solution notes for the main lab: [`solution/answers.md`](solution/answers.md).
