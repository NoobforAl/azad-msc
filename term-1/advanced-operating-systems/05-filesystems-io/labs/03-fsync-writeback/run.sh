#!/usr/bin/env bash
# run.sh: (1) cost of fsync/O_SYNC vs buffered writes, (2) watch dirty pages being
# written back, (3) throttle ONE device's dirty budget via its per-BDI knobs
# (a loop-mounted ext4), so the global vm.dirty_* sysctls are never changed.
set -euo pipefail
cd "$(dirname "$0")"
[ -x wbench ] || gcc -Wall -Wextra -O2 -o wbench wbench.c
PARTS=${PARTS:-"1 2 3"}           # e.g. PARTS="2 3" bash run.sh skips the slow part 1
has() { [[ " $PARTS " == *" $1 "* ]]; }

if has 1; then
echo "== 1. durability policies, 2000 x 4 KiB on $(findmnt -no SOURCE,FSTYPE -T .)"
for m in buffered fdatasync fsync odsync osync; do ./wbench $m t.dat 2000 4096; done
rm -f t.dat
fi

if has 2; then
echo
echo "== 2. global writeback knobs (read-only here)"
for k in dirty_ratio dirty_background_ratio dirty_bytes dirty_background_bytes \
         dirty_expire_centisecs dirty_writeback_centisecs; do
  printf '  vm.%-26s %s\n' "$k" "$(cat /proc/sys/vm/$k)"
done
echo "== 2b. 384 MiB buffered write (below dirty_background_ratio); Dirty/Writeback every 3 s"
rm -f w.dat; sync -f .                 # start from a clean filesystem
( dd if=/dev/zero of=w.dat bs=1M count=384 status=none; echo "  [dd returned]" ) &
for i in $(seq 0 19); do
  awk -v t="$i" '/^Dirty:/ {d=$2} /^Writeback:/ {w=$2} END {printf "  t=%3ds Dirty=%7d kB Writeback=%6d kB\n", t*3, d, w}' /proc/meminfo
  sleep 3
done
wait; rm -f w.dat
fi
has 3 || exit 0

echo
echo "== 3. per-BDI limit on a loop device (only this device is throttled)"
truncate -s 1G bdi.img
LOOP=$(sudo losetup -f --show bdi.img)
BDI=/sys/class/bdi/$(lsblk -no MAJ:MIN $LOOP | tr -d ' ')
# BDI knobs outlive the loop device: always put the defaults back (strict_limit=0, max_ratio=100)
trap 'echo 0 | sudo tee $BDI/strict_limit >/dev/null; echo 100 | sudo tee $BDI/max_ratio >/dev/null
      sudo umount -q mnt 2>/dev/null || true; sudo losetup -d $LOOP 2>/dev/null || true; rm -f bdi.img' EXIT
sudo mkfs.ext4 -q -F $LOOP
mkdir -p mnt && sudo mount $LOOP mnt && sudo chown "$USER" mnt
echo "  $LOOP -> $BDI"
run_dd() {
  sudo bpftrace -q -e 'tracepoint:writeback:balance_dirty_pages /comm == "dd"/ { @throttle_events = count(); @max_pause_ms = max(args->pause); }' \
       -c "dd if=/dev/zero of=mnt/f bs=1M count=256 conv=fsync" 2>&1 | grep -v '^$'
}
echo "  -- default limits: max_bytes=$(cat $BDI/max_bytes) strict_limit=$(cat $BDI/strict_limit)"
run_dd
rm -f mnt/f
echo 8388608 | sudo tee $BDI/max_bytes >/dev/null      # 8 MiB dirty budget for this bdi
echo 1 | sudo tee $BDI/strict_limit >/dev/null
echo "  -- limited:      max_bytes=$(cat $BDI/max_bytes) strict_limit=$(cat $BDI/strict_limit)"
run_dd
