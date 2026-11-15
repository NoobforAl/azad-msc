#!/usr/bin/env bash
# compare-preempt.sh: same cyclictest run under each PREEMPT_DYNAMIC mode.
# Needs CONFIG_PREEMPT_DYNAMIC (check: uname -v shows PREEMPT_DYNAMIC) and debugfs.
# Always restores the original mode, even on Ctrl-C.  VM only: this is a global kernel switch.
# Usage: sudo bash compare-preempt.sh [seconds=30] [cpus=2,3] [modes="none voluntary full"]
set -euo pipefail
secs="${1:-30}"; cpus="${2:-2,3}"; modes="${3:-none voluntary full}"
knob=/sys/kernel/debug/sched/preempt
[ -w "$knob" ] || { echo "$knob not writable: not PREEMPT_DYNAMIC, or not root"; exit 1; }

# The file prints all modes with the active one in parentheses, e.g. "none voluntary (full) lazy".
orig="$(sed -E 's/.*\(([a-z]+)\).*/\1/' "$knob")"
trap 'echo "$orig" > "$knob"; echo "restored: $(cat $knob)"' EXIT
echo "original: $(cat $knob)"

for m in $modes; do
  echo "$m" > "$knob"
  stress-ng --cpu 2 --cpu-method int64 --iomix 1 --iomix-bytes 32M --taskset "$cpus" --timeout "$((secs + 4))s" -q &
  load=$!
  sleep 2
  out="$(cyclictest -m -p 80 -i 1000 -a "$cpus" -t 2 -h 400 -q -D "${secs}s")"
  wait "$load" || true
  max="$(echo "$out" | awk '/^# Max Latencies/ {print $4, $5}')"
  avg="$(echo "$out" | awk '/^# Avg Latencies/ {print $4, $5}')"
  printf "%-10s avg_us=[%s]  max_us=[%s]\n" "$(cat $knob)" "$avg" "$max"
done
