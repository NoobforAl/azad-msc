#!/usr/bin/env bash
# map-syscalls.sh: turn an strace log into "syscall -> number -> kernel entry symbol".
#
#   strace -f -o cat.trace cat /etc/hostname
#   bash map-syscalls.sh cat.trace [syscall_64.tbl]
#
# For each syscall name in the log it prints: how often it was called, its x86-64
# number and entry point from syscall_64.tbl (v6.18.63), the __x64_sys_* stub that
# x64_sys_call() jumps to, and whether that symbol exists in the running kernel.
set -euo pipefail

trace="${1:?usage: map-syscalls.sh <strace-log> [syscall_64.tbl]}"
tbl="${2:-$(dirname "$0")/syscall_64.tbl}"
[ -f "$tbl" ] || { echo "missing $tbl (copy it from _shared/sources/linux/arch/x86/entry/syscalls/)" >&2; exit 1; }

# Names of the syscalls in the log. With -f every line starts with a PID.
# "<... read resumed>" lines are the second half of an interrupted call: skip them.
names="$(sed -E 's/^[0-9]+ +//' "$trace" \
  | grep -vE '^(<\.\.\.|\+\+\+|---)' \
  | grep -oE '^[a-z_0-9]+\(' | tr -d '(' )"

kallsyms="$(mktemp)"; trap 'rm -f "$kallsyms"' EXIT
awk '{print $3}' /proc/kallsyms > "$kallsyms"

printf '%5s  %-18s %4s  %-20s %-26s %s\n' count syscall nr "tbl entry" "kernel symbol" "in kallsyms"
echo "$names" | sort | uniq -c | sort -rn | while read -r cnt name; do
  # Only the 64-bit ABI rows ("common" or "64"); x32 rows are a different ABI.
  # tr -d '\r': a table checked out on Windows may have CRLF line endings.
  row="$(tr -d '\r' < "$tbl" | awk -v n="$name" '($2=="common"||$2=="64") && $3==n {print $1, $4; exit}')"
  if [ -z "$row" ]; then
    printf '%5s  %-18s %4s  %-20s %-26s %s\n' "$cnt" "$name" "?" "?" "?" "-"; continue
  fi
  nr="${row%% *}"; entry="${row#* }"
  sym="__x64_${entry}"
  if grep -qx "$sym" "$kallsyms"; then ok=yes; else ok=no; fi
  printf '%5s  %-18s %4s  %-20s %-26s %s\n' "$cnt" "$name" "$nr" "$entry" "$sym" "$ok"
done
