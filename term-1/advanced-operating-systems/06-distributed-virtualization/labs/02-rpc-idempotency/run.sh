#!/usr/bin/env bash
# run.sh: three runs of the same 20 deposits against a server that loses 30% of replies.
#   A) no retries                 -> at-most-once: some deposits have an unknown outcome
#   B) 5 retries, no dedup        -> at-least-once: duplicates inflate the balance
#   C) 5 retries, dedup by req id -> exactly-once effect
set -euo pipefail
cd "$(dirname "$0")"
go build -o rpcbank rpcbank.go
PORT=9650
one() {  # $1 = label, $2 = dedup, $3 = retries
  ./rpcbank server -addr 127.0.0.1:$PORT -lose 0.3 -dedup="$2" -seed 7 2>/dev/null &
  local pid=$!
  sleep 0.3
  echo "== $1"
  ./rpcbank client -addr 127.0.0.1:$PORT -n 20 -timeout 200ms -retries "$3"
  kill "$pid"; wait "$pid" 2>/dev/null || true
  PORT=$((PORT + 1))
}
one "A: retries=0 dedup=false (at-most-once)" false 0
one "B: retries=5 dedup=false (at-least-once)" false 5
one "C: retries=5 dedup=true  (exactly-once effect)" true 5
