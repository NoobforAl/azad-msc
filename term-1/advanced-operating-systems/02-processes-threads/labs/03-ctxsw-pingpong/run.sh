#!/usr/bin/env bash
# run.sh: 5 runs per mode, print every run and the median round trip.
# Timing on a shared VM is noisy; the median of several runs is the number to report.
set -euo pipefail
cd "$(dirname "$0")"
[ -x pingpong ] || gcc -Wall -Wextra -O2 -o pingpong pingpong.c
REPS="${REPS:-5}"; ITERS="${ITERS:-200000}"
# split mode is ~100x slower on a VM (cross-vCPU wakeups), so it gets fewer round trips
SPLIT_ITERS="${SPLIT_ITERS:-20000}"
for mode in same split free; do
  vals=()
  for _ in $(seq "$REPS"); do
    n="$ITERS"; [ "$mode" = split ] && n="$SPLIT_ITERS"
    line="$(./pingpong "$mode" "$n")"
    echo "$line"
    vals+=("$(sed -E 's/.*round_trip=([0-9]+) ns.*/\1/' <<<"$line")")
  done
  med="$(printf '%s\n' "${vals[@]}" | sort -n | awk '{a[NR]=$1} END {print a[int((NR+1)/2)]}')"
  echo "== $mode: median round_trip ${med} ns over $REPS runs"
done
