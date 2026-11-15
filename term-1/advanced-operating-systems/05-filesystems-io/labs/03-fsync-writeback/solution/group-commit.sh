#!/usr/bin/env bash
# group-commit.sh: extension solution. 1 writer vs 4 concurrent writers, each fsync()ing after
# every 4 KiB record. Count fsync calls vs jbd2 commits.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -x wbench ] || gcc -Wall -Wextra -O2 -o wbench wbench.c
for n in 1 4; do
  echo "== $n writer(s) x 300 fsync'd records each"
  # bpftrace -c does not understand shell quoting, so the workload goes into a script file
  printf 'for i in $(seq 1 %d); do ./wbench fsync g$i.dat 300 4096 & done; wait\n' "$n" > writers.sh
  sudo timeout 200 bpftrace -q -e '
tracepoint:ext4:ext4_sync_file_enter /comm == "wbench"/ { @fsync_calls = count(); }
tracepoint:jbd2:jbd2_commit_flushing { @jbd2_commits = count(); }
' -c "bash writers.sh"
  rm -f g*.dat writers.sh
done
echo "(jbd2 commits are counted for every journal on the system: expect a little noise)"
