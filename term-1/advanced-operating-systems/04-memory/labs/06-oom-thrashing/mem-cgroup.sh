#!/usr/bin/env bash
# mem-cgroup.sh: VM ONLY. Run a command inside a throw-away cgroup v2 with a
# hard memory limit, then print what the cgroup recorded.
#   bash mem-cgroup.sh <memory.max> <command...>
#   bash mem-cgroup.sh 128M ./hog 512          # -> OOM kill inside the cgroup
#   bash mem-cgroup.sh 64M  ./thrash big.bin 3 # -> refaults (thrashing)
# Only this cgroup is affected; the rest of the machine never sees the limit.
set -uo pipefail
LIMIT="${1:?memory.max, e.g. 128M}"; shift
CG=/sys/fs/cgroup/aos04-$$

grep -qw memory /sys/fs/cgroup/cgroup.subtree_control || \
  echo +memory | sudo tee /sys/fs/cgroup/cgroup.subtree_control >/dev/null
sudo mkdir "$CG"
trap 'sudo rmdir "$CG" 2>/dev/null' EXIT
echo "$LIMIT" | sudo tee "$CG/memory.max"      >/dev/null
echo 0        | sudo tee "$CG/memory.swap.max" >/dev/null   # no swap escape hatch

echo "== cgroup $CG  memory.max=$(cat "$CG/memory.max")"
# Move a child shell into the cgroup, then exec the command there.
sudo sh -c "echo \$\$ > $CG/cgroup.procs && exec sudo -u $USER $*"
echo "== exit status: $?"
echo "== memory.events";   sed 's/^/  /' "$CG/memory.events"
echo "== memory.peak:  $(cat "$CG/memory.peak" 2>/dev/null)"
echo "== memory.stat (selected)"
grep -E '^(anon|file|workingset_refault_file|workingset_activate_file|pgmajfault) ' "$CG/memory.stat" | sed 's/^/  /'
echo "== memory.pressure"; sed 's/^/  /' "$CG/memory.pressure"
