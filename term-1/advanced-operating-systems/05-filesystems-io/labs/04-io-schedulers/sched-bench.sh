#!/usr/bin/env bash
# sched-bench.sh: compare blk-mq I/O schedulers on a loop device (512 MiB backing file,
# direct I/O so requests really reach the virtual disk). VM only; needs sudo.
#   bash sched-bench.sh            # all schedulers this kernel offers for the device
#   RUNTIME=5 bash sched-bench.sh  # shorter runs
set -euo pipefail
cd "$(dirname "$0")"
RUNTIME=${RUNTIME:-8}
IMG=$PWD/sched.img

[ -f "$IMG" ] || dd if=/dev/zero of="$IMG" bs=1M count=512 status=none
LOOP=$(sudo losetup -f --show --direct-io=on "$IMG")
trap 'sudo losetup -d $LOOP; rm -f "$IMG"' EXIT
DEV=$(basename "$LOOP")
Q=/sys/block/$DEV/queue
sudo modprobe -q bfq 2>/dev/null || true
sudo modprobe -q kyber-iosched 2>/dev/null || true
echo "device $LOOP: scheduler file = $(cat $Q/scheduler)"
echo "nr_hw_queues=$(ls /sys/block/$DEV/mq | wc -l) nr_requests=$(cat $Q/nr_requests) rotational=$(cat $Q/rotational)"
SCHEDS=$(tr -d '[]' < $Q/scheduler)

# Job A: random 4 KiB reads, 32 in flight, throughput test.
# Job B: one random-read job (QD1) competing with a buffered sequential writer that issues
#        large writes: what does each scheduler do to the reader's tail latency?
fio_json() { sudo fio --output-format=json "$@" 2>/dev/null; }

printf '\n%-12s %10s %12s | %14s %14s %12s\n' scheduler "A:IOPS" "A:p99(us)" "B:rd p50(us)" "B:rd p99(us)" "B:wr MiB/s"
for s in $SCHEDS; do
  echo "$s" | sudo tee $Q/scheduler >/dev/null
  A=$(fio_json --name=A --filename=$LOOP --rw=randread --bs=4k --iodepth=32 --ioengine=io_uring \
        --direct=1 --runtime=$RUNTIME --time_based --size=448M)
  B=$(fio_json --filename=$LOOP --direct=1 --runtime=$RUNTIME --time_based --size=448M \
        --name=reader --rw=randread --bs=4k --iodepth=1 --ioengine=psync \
        --name=writer --rw=write --bs=1M --iodepth=16 --ioengine=io_uring --offset=0)
  python3 - "$s" "$A" "$B" <<'EOF'
import json, sys
s, a, b = sys.argv[1], json.loads(sys.argv[2]), json.loads(sys.argv[3])
ja = a["jobs"][0]["read"]
rd = [j for j in b["jobs"] if j["jobname"] == "reader"][0]["read"]
wr = [j for j in b["jobs"] if j["jobname"] == "writer"][0]["write"]
p = lambda x, k: x["clat_ns"]["percentile"][k] / 1000
print(f"{s:<12} {ja['iops']:10.0f} {p(ja,'99.000000'):12.0f} | {p(rd,'50.000000'):14.0f} {p(rd,'99.000000'):14.0f} {wr['bw']/1024:12.1f}")
EOF
done
echo "none" | sudo tee $Q/scheduler >/dev/null
