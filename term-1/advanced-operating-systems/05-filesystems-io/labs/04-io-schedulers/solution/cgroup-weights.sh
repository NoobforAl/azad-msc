#!/usr/bin/env bash
# cgroup-weights.sh: extension solution. Under bfq, give the reader cgroup io.bfq.weight=1000
# and the writer cgroup 10, then rerun job B. Compare with plain bfq and with mq-deadline.
# VM only; creates and removes two cgroups under /sys/fs/cgroup (cgroup v2).
set -euo pipefail
cd "$(dirname "$0")/.."
RUNTIME=${RUNTIME:-8}
IMG=$PWD/sched.img
[ -f "$IMG" ] || dd if=/dev/zero of="$IMG" bs=1M count=512 status=none
LOOP=$(sudo losetup -f --show --direct-io=on "$IMG")
CG=/sys/fs/cgroup
cleanup() {
  for g in aos05-rd aos05-wr; do [ -d $CG/$g ] && sudo rmdir $CG/$g; done
  sudo losetup -d "$LOOP"; rm -f "$IMG"
}
trap cleanup EXIT
grep -qw io $CG/cgroup.subtree_control || echo +io | sudo tee $CG/cgroup.subtree_control >/dev/null
sudo mkdir -p $CG/aos05-rd $CG/aos05-wr
Q=/sys/block/$(basename "$LOOP")/queue
sudo modprobe -q bfq || true

# shellcheck disable=SC2024  # sudo starts fio inside the cgroup; its JSON is meant to stay user-owned
run_b() {   # $1 = label; reader and writer started inside their cgroups
  sudo sh -c "echo \$\$ > $CG/aos05-wr/cgroup.procs; exec fio --name=w --filename=$LOOP --rw=write --bs=1M --iodepth=16 \
      --ioengine=io_uring --direct=1 --runtime=$RUNTIME --time_based --size=448M --output-format=json" > w.json &
  sudo sh -c "echo \$\$ > $CG/aos05-rd/cgroup.procs; exec fio --name=r --filename=$LOOP --rw=randread --bs=4k --iodepth=1 \
      --ioengine=psync --direct=1 --runtime=$RUNTIME --time_based --size=448M --output-format=json" > r.json
  wait
  python3 - "$1" <<'EOF'
import json, sys
r = json.load(open("r.json"))["jobs"][0]["read"]; w = json.load(open("w.json"))["jobs"][0]["write"]
p = r["clat_ns"]["percentile"]
print(f"{sys.argv[1]:<28} reader p50 {p['50.000000']/1000:8.0f} us  p99 {p['99.000000']/1000:8.0f} us | writer {w['bw']/1024:7.1f} MiB/s")
EOF
  rm -f r.json w.json
}

echo bfq | sudo tee $Q/scheduler >/dev/null
echo 100 | sudo tee $CG/aos05-rd/io.bfq.weight $CG/aos05-wr/io.bfq.weight >/dev/null
run_b "bfq, equal weights"
echo 1000 | sudo tee $CG/aos05-rd/io.bfq.weight >/dev/null
echo 10 | sudo tee $CG/aos05-wr/io.bfq.weight >/dev/null
run_b "bfq, reader 1000 / writer 10"
echo mq-deadline | sudo tee $Q/scheduler >/dev/null
run_b "mq-deadline (weights ignored)"
