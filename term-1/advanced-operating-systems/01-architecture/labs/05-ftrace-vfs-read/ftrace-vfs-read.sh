#!/usr/bin/env bash
# ftrace-vfs-read.sh: function_graph trace of the vfs_read() calls made by one `cat FILE`.
#
#   sudo bash ftrace-vfs-read.sh [file=/etc/hostname] [out=cat.graph]
#   sudo N=4 bash ftrace-vfs-read.sh             # print the 4th vfs_read() tree
#
# VM only (root). ftrace is a global kernel facility, so this script follows strict rules:
#   * filtered:  -g vfs_read  (set_graph_function: graphs start only at vfs_read)
#                -l <list>    (set_ftrace_filter: only ~120 read-path functions are patched;
#                              without it, enabling function_graph patches every kernel function,
#                              which took ~40 s of system time on this 8-vCPU guest)
#                -F           (set_ftrace_pid: only the cat process)
#   * bounded:   --max-graph-depth 6, and the record runs under `timeout 10`
#   * cleaned:   `trace-cmd reset` on every exit path
# Never drop the filters: an unfiltered function trace can soft-lock a busy machine.
set -uo pipefail

file="${1:-/etc/hostname}"; out="${2:-cat.graph}"
[ "$(id -u)" -eq 0 ] || { echo "run with sudo" >&2; exit 1; }
command -v trace-cmd >/dev/null || { echo "install trace-cmd" >&2; exit 1; }

cleanup() { trace-cmd reset >/dev/null 2>&1 || true; rm -f trace.dat; }
trap cleanup EXIT

# The functions we allow ftrace to patch: the VFS read path and the common ->read_iter targets.
# Every pattern must match something in available_filter_functions, or trace-cmd refuses to run
# (new_sync_read and copy_page_to_iter are inlined in this build, so they can't be listed).
FILTER=(-l vfs_read -l rw_verify_area -l security_file_permission
        -l '*_read_iter' -l 'filemap_*' -l touch_atime
        -l 'fsnotify*' -l 'seq_read*' -l anon_pipe_read -l fifo_pipe_read)

# trace-cmd may not notice cat's exit inside this guest; timeout ends the record and
# trace-cmd still writes trace.dat on SIGTERM.
timeout 10 trace-cmd record -q -p function_graph -g vfs_read --max-graph-depth 6 \
  "${FILTER[@]}" -F cat "$file" > /dev/null 2> record.err
rc=$?
[ "$rc" -eq 0 ] || [ "$rc" -eq 124 ] || { echo "trace-cmd record failed (rc=$rc):"; tail -3 record.err; exit 1; }
trace-cmd report -q 2>/dev/null | grep -E 'funcgraph_(entry|exit)' > "$out"

echo "full trace: $out ($(wc -l < "$out") lines)"
echo "vfs_read() calls (n, lines, total time, first ->read_iter/->read reached):"
# Brace counting: "fn() {" opens, a line with only "}" closes.
awk '/\| *vfs_read\(\) \{/ && !on { n++; on = 1; depth = 0; lines = 0; op = "-" }
     on { lines++
          if ($0 ~ /\{ *$/) depth++
          else if ($0 ~ /\| *\} *$/) depth--
          if (op == "-" && match($0, /[a-z0-9_]+_read(_iter)?\(\)/) && $0 !~ /vfs_read\(\)/) op = substr($0, RSTART, RLENGTH)
          if (depth == 0) { t = $0; sub(/^.*funcgraph_exit: */, "", t); sub(/ *\|.*/, "", t)
                            printf "  #%d  %3d lines  %10s  %s\n", n, lines, t, op; on = 0 } }' "$out"

pick="${N:-1}"
echo "call tree of vfs_read() #$pick (set N=<k> to pick another):"
awk -v want="$pick" '/\| *vfs_read\(\) \{/ && !on { n++; if (n == want) { on = 1; depth = 0 } }
     on { sub(/^.*funcgraph_entry: /, ""); sub(/^.*funcgraph_exit:  /, ""); print
          if ($0 ~ /\{ *$/) depth++; else if ($0 ~ /\| *\} *$/) depth--
          if (depth == 0) exit }' "$out"
