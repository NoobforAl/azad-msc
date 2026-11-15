#!/usr/bin/env bash
# minictr.sh: a container without Docker. VM ONLY (needs root, mounts, cgroup writes).
#   1. cgroup v2 group with memory.max, pids.max, cpu.max
#   2. unshare: new mount, UTS, IPC, net, PID and cgroup namespaces
#   3. pivot_root into an Alpine minirootfs, mount /proc, drop the old root
# Usage: bash minictr.sh [command...]      (default: /bin/sh)
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD/rootfs"
CG="/sys/fs/cgroup/aos-m06-ctr"
MEM="${MEM:-64M}"
PIDS="${PIDS:-20}"
CPU="${CPU:-20000 100000}"        # 20 ms of CPU per 100 ms period = 20% of one CPU

[ -x "$ROOT/bin/busybox" ] || { echo "run get-rootfs.sh first" >&2; exit 1; }

# --- 1. cgroup v2 -----------------------------------------------------------
for c in memory pids cpu; do
  grep -qw "$c" /sys/fs/cgroup/cgroup.subtree_control \
    || echo "+$c" | sudo tee /sys/fs/cgroup/cgroup.subtree_control >/dev/null
done
sudo mkdir -p "$CG"
echo "$MEM"  | sudo tee "$CG/memory.max"      >/dev/null
echo 0       | sudo tee "$CG/memory.swap.max" >/dev/null
echo "$PIDS" | sudo tee "$CG/pids.max"        >/dev/null
echo "$CPU"  | sudo tee "$CG/cpu.max"         >/dev/null
echo "cgroup $CG: memory.max=$(cat $CG/memory.max) pids.max=$(cat $CG/pids.max) cpu.max=$(cat $CG/cpu.max)"

# --- 2+3. join the cgroup, then unshare and pivot_root ------------------------
# The inner script runs as PID 1 of the new PID namespace, still on the host's files.
INNER='
set -e
ROOT="$1"; shift
mount --make-rprivate /                 # our mounts must not propagate back to the host
mount --bind "$ROOT" "$ROOT"            # pivot_root needs new_root to be a mount point
mkdir -p "$ROOT/.oldroot"
cd "$ROOT"
pivot_root . .oldroot                   # / is now the rootfs; the host / is /.oldroot
hash -r                                 # forget host paths like /usr/bin/mount
mount -t proc  proc /proc               # a /proc that shows only this PID namespace
mount -t tmpfs tmp  /tmp
mount -t tmpfs -o mode=755,size=64k dev /dev   # a minimal /dev: only what we create
mknod -m 666 /dev/null c 1 3
mknod -m 666 /dev/zero c 1 5
umount -l /.oldroot && rmdir /.oldroot  # host files are no longer reachable
hostname aos-ctr
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
exec "$@"
'
[ $# -gt 0 ] || set -- /bin/sh
sudo bash -c 'echo $$ > "$1/cgroup.procs"; shift; exec "$@"' _ "$CG" \
  unshare --mount --uts --ipc --net --pid --cgroup --fork \
  bash -c "$INNER" inner "$ROOT" "$@" || echo "container exited with status $?"

# --- after exit: what the kernel counted ---------------------------------------
echo "== host view of $CG after exit"
grep -E '^(oom|oom_kill) ' "$CG/memory.events"
echo "pids.events: $(cat $CG/pids.events)   pids.peak: $(cat $CG/pids.peak 2>/dev/null || echo n/a)"
grep -E '^(usage_usec|nr_throttled|throttled_usec) ' "$CG/cpu.stat"
