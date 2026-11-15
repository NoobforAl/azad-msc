#!/usr/bin/env bash
# crash-demo.sh: simulate a power cut under ext4 with dm-flakey on a loop file.
# VM ONLY. Needs sudo and the dm-flakey target. Touches nothing but its own 256 MiB image.
#   bash crash-demo.sh                 # data=ordered (ext4 default)
#   MODE=writeback bash crash-demo.sh  # data=writeback
set -euo pipefail
cd "$(dirname "$0")"
MODE=${MODE:-ordered}
IMG=$PWD/flakey.img; MNT=$PWD/mnt; DM=aos05flakey
sudo modprobe dm-flakey
truncate -s 256M "$IMG"
LOOP=$(sudo losetup -f --show "$IMG")
SECT=$(sudo blockdev --getsz "$LOOP")
cleanup() {
  sudo umount -q "$MNT" 2>/dev/null || true
  sudo dmsetup remove $DM 2>/dev/null || true
  sudo losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$IMG"
}
trap cleanup EXIT
# flakey table: <start> <len> flakey <dev> <offset> <up_secs> <down_secs> [features]
UP="0 $SECT flakey $LOOP 0 180 0"                       # always up: a normal disk
DROP="0 $SECT flakey $LOOP 0 0 180 1 drop_writes"      # always down: writes silently vanish

sudo mkfs.ext4 -q -F "$LOOP"
sudo dmsetup create $DM --table "$UP"
mkdir -p "$MNT"
sudo mount -o data=$MODE /dev/mapper/$DM "$MNT"
sudo chown "$USER" "$MNT"
echo "== mounted: $(findmnt -no OPTIONS "$MNT")"

# Three writes with three durability levels.
printf 'old contents\n' > "$MNT/config"; sync                 # a file that already existed
printf 'A: written + fsync\n' > "$MNT/A"; sync "$MNT/A"       # sync FILE = fsync(2)
printf 'B: written, no fsync\n' > "$MNT/B"
printf 'new contents\n' > "$MNT/config.tmp"; mv "$MNT/config.tmp" "$MNT/config"   # replace by rename, no fsync
echo "== before the crash:"; (cd "$MNT" && for f in A B config; do printf '  %-7s %3s bytes: %s\n' $f "$(stat -c %s $f)" "$(cat $f)"; done)

# Power cut: from now on every write to the device is dropped (reads still work).
# --nolockfs is essential: a plain "dmsetup suspend" FREEZES the filesystem first, which
# syncs it, and then nothing is left to lose.
sudo dmsetup load $DM --table "$DROP"; sudo dmsetup suspend --nolockfs $DM; sudo dmsetup resume $DM
sync                                          # writeback + journal commit go nowhere
sudo umount "$MNT"                            # page cache for this fs is gone, as after a reboot
sudo dmsetup suspend $DM; sudo dmsetup load $DM --table "$UP"; sudo dmsetup resume $DM

echo "== fsck -n right after the crash (read-only check):"
sudo e2fsck -fn /dev/mapper/$DM 2>&1 | sed 's/^/  /' | head -8 || true
n0=$(sudo dmesg | wc -l)                      # shared VM: never clear the ring buffer
sudo mount -o data=$MODE /dev/mapper/$DM "$MNT"
echo "== kernel log at remount (journal replay):"
sudo dmesg | tail -n +$((n0 + 1)) | grep -E "EXT4-fs \(dm-|jbd2" | sed 's/^\[[^]]*\] /  /' || true
echo "== after the crash:"
(cd "$MNT" && for f in A B config; do
   if [ -e $f ]; then printf '  %-7s %3s bytes: %s\n' $f "$(stat -c %s $f)" "$(tr -d '\0' < $f)"; else printf '  %-7s MISSING\n' $f; fi
 done)
