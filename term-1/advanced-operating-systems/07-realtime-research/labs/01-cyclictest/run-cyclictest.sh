#!/usr/bin/env bash
# run-cyclictest.sh: measure wake-up latency on 2 CPUs, idle and under load.
# Usage: sudo bash run-cyclictest.sh [seconds=60] [cpus=2,3]
# Writes idle.hist / load.hist (cyclictest histogram, 1 us buckets) next to this script.
set -euo pipefail
secs="${1:-60}"; cpus="${2:-2,3}"
here="$(cd "$(dirname "$0")" && pwd)"
[ "$(id -u)" -eq 0 ] || { echo "run with sudo (SCHED_FIFO + mlockall)"; exit 1; }
command -v cyclictest >/dev/null || { echo "apt install rt-tests"; exit 1; }

echo "== kernel: $(uname -v)"
echo "== preempt mode: $(cat /sys/kernel/debug/sched/preempt 2>/dev/null || echo 'n/a (no debugfs)')"

run() {   # $1 = label
  # -m mlockall, -p 80 SCHED_FIFO prio, -i 1000 us period, -a pin threads, -t one thread per CPU
  # -h 400: histogram up to 400 us; -q quiet; -D duration
  cyclictest -m -p 80 -i 1000 -a "$cpus" -t 2 -h 400 -q -D "${secs}s" > "$here/$1.hist"
  grep -E '^# (Min|Avg|Max) Latencies|^# Histogram Overflows' "$here/$1.hist" | sed "s/^/[$1] /"
}

run idle
# Load on the same CPUs: CPU hogs + filesystem churn (syscalls, page cache, I/O completions).
stress-ng --cpu 2 --cpu-method int64 --iomix 1 --iomix-bytes 32M --taskset "$cpus" --timeout "$((secs + 5))s" -q &
load=$!
sleep 2
run load
wait "$load" || true
echo "histograms: $here/idle.hist $here/load.hist"
