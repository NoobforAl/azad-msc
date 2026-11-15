#!/usr/bin/env bash
# run.sh: build clocks.go, start 3 processes on localhost (UDP 9600-9602), analyze their logs.
set -euo pipefail
cd "$(dirname "$0")"
SEED="${SEED:-1}"
EVENTS="${EVENTS:-6}"
go build -o clocks clocks.go
for i in 0 1 2; do
  ./clocks -id "$i" -n 3 -events "$EVENTS" -seed "$SEED" > "p$i.log" &
done
wait
wc -l p0.log p1.log p2.log
./clocks -analyze p0.log p1.log p2.log
