#!/usr/bin/env bash
# trace.sh: show the kernel call chain of one read(2), twice: with ftrace (function_graph)
# and with bpftrace (kernel stack at filemap_read). VM recommended; needs sudo.
#   bash trace.sh            # uses ./data.bin (created if missing, 1 MiB)
set -euo pipefail
cd "$(dirname "$0")"
# -static: no dynamic loader, so the only read() calls in the trace are ours
gcc -Wall -Wextra -O2 -static -o readone readone.c
[ -f data.bin ] || { head -c 1048576 /dev/urandom > data.bin; sync data.bin; }

echo "== 1. ftrace function_graph rooted at vfs_read, only our pid (-F), only 10 functions (-l)"
# SAFETY: -l limits ftrace to the listed functions. Enabling function_graph for ALL kernel
# functions on a busy VirtualBox guest caused a 26 s soft lockup in trace-cmd (2026-11-15).
FUNCS="vfs_read rw_verify_area ext4_file_read_iter generic_file_read_iter filemap_read
       filemap_get_pages page_cache_sync_ra page_cache_async_ra copy_page_to_iter touch_atime"
FILTER=(); for fn in $FUNCS; do FILTER+=(-l "$fn"); done
sudo timeout 10 trace-cmd record -q -p function_graph -g vfs_read --max-graph-depth 6 \
     "${FILTER[@]}" -F ./readone data.bin 4096 1 > /dev/null || true
sudo trace-cmd report -q 2>/dev/null | grep -v '^\s*$' | sed -n '1,45p'
sudo trace-cmd reset > /dev/null 2>&1          # leave the tracer off for everyone else

echo
echo "== 2. bpftrace: kernel stack every time filemap_read() runs for comm=readone"
sudo bpftrace -q -e '
kprobe:filemap_read /comm == "readone"/ { @[kstack(10)] = count(); }
' -c "./readone data.bin 4096 1"

echo
echo "== 3. cold read: evict data.bin from the page cache (this file only) and count bios"
# POSIX_FADV_DONTNEED via dd's iflag=nocache drops clean pages of THIS file only
# (dirty pages are kept, so write them back first).
sync data.bin
dd if=data.bin iflag=nocache count=0 status=none
sudo bpftrace -q -e '
tracepoint:block:block_bio_queue /comm == "readone"/ { @bios = count(); @bytes = sum(args->nr_sector * 512); }
kprobe:filemap_read /comm == "readone"/ { @filemap_read = count(); }
kprobe:page_cache_sync_ra /comm == "readone"/ { @sync_readahead = count(); }
' -c "./readone data.bin 4096 1"

echo
echo "== 4. VFS objects: three superblocks, and the open file behind an fd"
stat -c 'inode=%-8i dev=%-6D type=%-22F %n' /etc/hostname /proc/uptime /dev/null
df --output=fstype,target /etc/hostname /proc/uptime /dev/null | tail -n +2
exec 3</etc/hostname; head -c3 <&3 >/dev/null
echo "-- /proc/$$/fdinfo/3 after reading 3 bytes:"; cat /proc/$$/fdinfo/3
exec 3<&-

echo
echo "== 5. negative dentry: 5 stat()s of a missing name, how many reach ext4_lookup?"
name=/etc/no-such-file-$$-$RANDOM            # a name nobody has looked up yet
printf 'for i in 1 2 3 4 5; do stat %s >/dev/null 2>&1; done\n' "$name" > five-stats.sh
sudo bpftrace -q -e 'kprobe:ext4_lookup /comm == "stat"/ { @ext4_lookup = count(); }' -c "sh five-stats.sh"
rm -f five-stats.sh
