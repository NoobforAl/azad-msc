#!/usr/bin/env bash
# irq-delta.sh: which interrupt sources fired during an interval, summed over all CPUs.
#
#   bash irq-delta.sh [seconds=5] [top=12]
#   bash irq-delta.sh 5 12 -- <command ...>     # run a load while measuring
#
# Reads /proc/interrupts twice and prints the rows whose total count changed,
# sorted by delta. The first column is the IRQ number (device interrupts) or a
# three-letter name for architecture vectors (LOC = local APIC timer, RES =
# rescheduling IPI, CAL = function-call IPI, TLB = TLB-shootdown IPI, ...).
set -euo pipefail

secs="${1:-5}"; top="${2:-12}"
shift $(( $# >= 2 ? 2 : $# ))
[ "${1:-}" = "--" ] && shift

snap() {
  # Output: "<irq> <total> <description>"; the CPU columns are the numeric fields after the label.
  awk 'NR==1 { ncpu = NF; next }
       { irq = $1; sub(":", "", irq); total = 0; desc = "";
         for (i = 2; i <= NF; i++) {
           if (i <= ncpu + 1 && $i ~ /^[0-9]+$/) total += $i; else desc = desc " " $i
         }
         print irq, total, desc }' /proc/interrupts
}

before="$(mktemp)"; after="$(mktemp)"; trap 'rm -f "$before" "$after"' EXIT
snap > "$before"
if [ $# -gt 0 ]; then
  "$@" >/dev/null 2>&1 &
  load=$!
  sleep "$secs"
  kill "$load" 2>/dev/null || true; wait "$load" 2>/dev/null || true
else
  sleep "$secs"
fi
snap > "$after"

echo "interrupts during ${secs}s on $(nproc) CPUs (sum over CPUs):"
printf '%8s  %-6s %s\n' delta irq source
awk 'NR==FNR { b[$1] = $2; next }
     { d = $2 - b[$1]; if (d > 0) { $2 = ""; irq = $1; $1 = ""; sub(/^ +/, "");
       printf "%8d  %-6s %s\n", d, irq, $0 } }' "$before" "$after" \
  | sort -rn | head -n "$top"
