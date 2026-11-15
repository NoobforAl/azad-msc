# Lab 04.6 — solution notes

## A — OOM kill inside the cgroup

1. `hog` faults in 16 MiB chunks. Each fault charges the memcg through `mem_cgroup_charge()`, called from `alloc_anon_folio()`.
2. Near 128 MiB the charge fails. With `memory.swap.max=0`, memcg reclaim can only take file pages, and there are almost none, so reclaim fails.
3. `handle_mm_fault()` had armed memcg OOM handling, so `mem_cgroup_out_of_memory()` runs. `oom_badness()` picks the largest task in the cgroup (the hog).
4. The hog gets `SIGKILL`, the shell reports exit status 137, the `oom_reaper` frees its anonymous memory, and `memory.events` records `oom 1` and `oom_kill 1`.

The last "touched" line is below 128 MiB, because the binary, libc and page tables are charged too.

## B — 64 MiB limit, 128 MiB file

- `MADV_RANDOM` disables readahead, so every page not in the cache is one major fault.
- The cgroup can cache at most about 60 MiB of the file. Reading pages in order evicts the oldest ones, which are exactly the ones needed first in the next pass. So every pass has about 32 768 major faults.
- `workingset_refault_file` counts evicted-then-refaulted pages: the shadow entries left in the page cache by eviction. It grows by about one pass's worth of pages per pass after the first.
- PSI `some`/`full` is non-zero, because the task spends its time stalled on page-cache I/O.

## C — 256 MiB limit

The whole file fits. Pass 1 faults the pages in (major), and passes 2 and 3 find them in the page cache, still mapped. That gives about 0 faults per pass and pass times in milliseconds.

## Why no swap was needed

The pages being thrashed are clean file pages. Reclaim drops them for free and they come back through `filemap_fault()`.
