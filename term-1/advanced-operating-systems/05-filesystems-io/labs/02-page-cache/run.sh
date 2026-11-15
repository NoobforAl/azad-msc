#!/usr/bin/env bash
# run.sh: page-cache miss vs hit for one 256 MiB file. Evicts ONLY this file
# (posix_fadvise DONTNEED); never touches /proc/sys/vm/drop_caches.
set -euo pipefail
cd "$(dirname "$0")"
[ -x pcache ] || gcc -Wall -Wextra -O2 -o pcache pcache.c
F=big.bin
[ -f $F ] || { dd if=/dev/urandom of=$F bs=1M count=256 status=none; sync $F; }

cached_kb() { awk '/^Cached:/ {print $2}' /proc/meminfo; }

echo "== evict this file only";        ./pcache evict $F
echo "== residency after evict";       ./pcache resident $F
if command -v fincore >/dev/null; then fincore $F; else echo "(fincore not installed: pcache resident is the same mincore() check)"; fi
c0=$(cached_kb)
echo "== cold read (page-cache miss), counting folios inserted into the page cache"
sudo bpftrace -q -e '
tracepoint:filemap:mm_filemap_add_to_page_cache /comm == "pcache"/ { @added_folios = count(); }
kprobe:page_cache_sync_ra  /comm == "pcache"/ { @sync_ra = count(); }
kprobe:page_cache_async_ra /comm == "pcache"/ { @async_ra = count(); }
' -c "./pcache read $F"
c1=$(cached_kb)
echo "Cached: grew by $(( (c1 - c0) / 1024 )) MiB (system-wide, noisy on a shared VM)"
echo "== residency after cold read";   ./pcache resident $F
echo "== warm read (page-cache hit)"
sudo bpftrace -q -e '
tracepoint:filemap:mm_filemap_add_to_page_cache /comm == "pcache"/ { @added_folios = count(); }
' -c "./pcache read $F"
echo "== warm read x3 (variance)"
for _ in 1 2 3; do ./pcache read $F; done
