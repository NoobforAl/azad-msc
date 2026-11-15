#!/usr/bin/env bash
# run.sh: read()/write() loop vs io_uring copy of a 512 MiB file.
# Source is evicted from the page cache (this file only) before every cold run.
set -euo pipefail
cd "$(dirname "$0")"
gcc -Wall -Wextra -O2 -o copy_rw copy_rw.c
gcc -Wall -Wextra -O2 -o copy_uring copy_uring.c -luring
SRC=src.bin; DST=dst.bin
[ -f $SRC ] || { dd if=/dev/urandom of=$SRC bs=1M count=512 status=none; sync $SRC; }
PERF=$(command -v /usr/local/bin/perf || ls /usr/lib/linux-tools-*/perf | head -1)
evict() { dd if=$SRC iflag=nocache count=0 status=none; rm -f $DST; sync; }

echo "== 1. cold source, wall time + software counters"
for p in "./copy_rw $SRC $DST" "./copy_uring $SRC $DST 131072 8"; do
  evict
  $PERF stat -e task-clock,context-switches,cpu-migrations -- $p 2>&1 \
     | grep -E 'copy_|task-clock|context-switches|seconds time elapsed|seconds user|seconds sys'
  cmp $SRC $DST && echo "  cmp: identical"
done

echo
echo "== 2. syscall counts (strace -c -f), warm source"
for p in "./copy_rw $SRC $DST" "./copy_uring $SRC $DST 131072 8"; do
  rm -f $DST
  strace -c -f -o strace.txt $p >/dev/null
  grep -E 'calls|read|write|io_uring|total' strace.txt | sed 's/^/  /'
done
rm -f strace.txt

echo
echo "== 3. who did the work? io_uring tracepoints during a cold copy"
evict
sudo bpftrace -q -e '
tracepoint:io_uring:io_uring_submit_req  /comm == "copy_uring"/ { @submitted[args->opcode] = count(); }
tracepoint:io_uring:io_uring_queue_async_work { @punted_to_io_wq[args->opcode] = count(); }
tracepoint:io_uring:io_uring_complete    { @completed = count(); }
' -c "./copy_uring $SRC $DST 131072 8"
echo "(opcode numbers: see enum io_uring_op in include/uapi/linux/io_uring.h; 22=READ 23=WRITE)"
rm -f $DST
