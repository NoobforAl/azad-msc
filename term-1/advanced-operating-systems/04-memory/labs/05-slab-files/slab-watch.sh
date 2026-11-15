#!/usr/bin/env bash
# slab-watch.sh: show how creating and deleting N empty files moves the
# dentry and inode slab caches. Needs sudo for /proc/slabinfo.
#   bash slab-watch.sh [N=200000]
set -euo pipefail
N="${1:-200000}"
DIR="$HOME/work/04-memory/slabtest"
FS="$(stat -f -c %T "$HOME")"                 # ext2/ext3 => ext4 inode cache
CACHES='^(dentry|ext4_inode_cache|inode_cache|xfs_inode|btrfs_inode|shmem_inode_cache) '

snap() {  # name active_objs num_objs objsize -> also KiB in use
  sudo awk -v re="$CACHES" '$0 ~ re { printf "  %-18s active=%8d total=%8d objsize=%4d  ~%7.1f MiB\n", $1, $2, $3, $4, $3*$4/1048576 }' /proc/slabinfo
}

[ -x ./mkfiles ] || gcc -Wall -Wextra -O2 -o mkfiles mkfiles.c
rm -rf "$DIR"
echo "== filesystem of \$HOME: $FS ; N=$N"
echo "== before";        snap
./mkfiles create "$DIR" "$N"
echo "== after create";  snap
ls "$DIR" | wc -l | sed 's/^/  files listed: /'
./mkfiles delete "$DIR" "$N"
echo "== after delete";  snap
echo "== top caches by size (slabtop -o -s c)"
sudo slabtop -o -s c | head -14
