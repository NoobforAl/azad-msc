# Lab 04.1 — solution notes

## Explaining each count

- **`anon`**: `pages + 3` minor faults. 65 536 of them are the touches. The 3 extra come from code run between the two `getrusage()` calls (`clock_gettime` via the vDSO, plus one stack and one data page). Each fault runs `do_anonymous_page()` → `alloc_anon_folio()` and zeroes 4 KiB. RSS grows by 256 MiB.
- **`anon-read`**: the same number of faults, but `do_anonymous_page()` takes the zero-page branch (`mm/memory.c` L5169–5191). RSS grows by about 0.
- **`thp`**: roughly `256 MiB / 2 MiB = 128` faults plus a few. Each fault is a `create_huge_pmd()` → `do_huge_pmd_anonymous_page()` that zeroes 2 MiB. In the captured run THP took 67 ms against 131 ms for `anon`, with `thp_fault_alloc 128` and `thp_fault_fallback 0`. An earlier run under heavy load took 1831 ms for the same 128 faults, because each fault zeroes 2 MiB and may have to compact memory to find a free 2 MiB block (`defrag=madvise` allows direct compaction for `MADV_HUGEPAGE` regions). Fewer faults does not mean less time.
- **`file`**: `filemap_fault()` starts readahead. The very first access is the only major fault. After that the pages are already in the page cache, and on v6.18 ext4 the cache holds them as **large folios** (`ext4_should_enable_large_folio()`, `fs/ext4/inode.c` L5183). A minor fault then maps a whole folio at once (`finish_fault()` uses `folio_nr_pages()`, `mm/memory.c` L5550) or a fault-around window (`fault_around_bytes` = 64 KiB). The captured run needed 537 faults for 65 536 pages, about 122 pages per fault. With 4 KiB folios only, fault-around alone would give about 4 096 faults. `VERSION-DEPENDENT`
- **`file-rand`**: `MADV_RANDOM` sets `VM_RAND_READ`. That disables readahead and fault-around, so each page is a separate synchronous 4 KiB read: about 65 536 major faults, and very slow on a virtual disk.

## perf vs getrusage

`perf stat -e page-faults` counts the perf software event emitted by `mm_account_fault()` for the whole process lifetime, including the dynamic loader and libc start-up. So it is a little higher (65 600 vs 65 539, about 60 more) than the `minflt` printed between the two `getrusage()` calls.

## Cost of one minor fault

`anon` time / 65 536 is about 2 µs on this VM (131.5 ms / 65 536). This number includes zeroing 4 KiB and the cost of the trap under VirtualBox.
