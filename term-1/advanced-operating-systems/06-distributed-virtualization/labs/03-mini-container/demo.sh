#!/bin/sh
# demo.sh: runs INSIDE the container (busybox sh). Copied to rootfs/usr/local/bin by the README steps.
echo "== identity"
echo "my pid: $$   hostname: $(hostname)"
ps -o pid,comm
echo "cgroup: $(cat /proc/self/cgroup)"
ip -o link | cut -d' ' -f2,9
ls /.oldroot 2>&1 | head -1

echo "== pids.max: try to start 30 sleepers"
# A child shell does the forking: when fork() fails it dies, not this script.
# Below, only shell builtins (no fork) are used until the sleepers are gone.
sh -c 'i=0; while [ $i -lt 30 ]; do sleep 10 & i=$((i + 1)); done' 2>/tmp/fork.err
n=0
for d in /proc/[0-9]*; do read -r c < "$d/comm" 2>/dev/null && [ "$c" = sleep ] && n=$((n + 1)); done
echo "sleepers running: $n"
while read -r l; do echo "$l"; done < /tmp/fork.err
for d in /proc/[0-9]*; do read -r c < "$d/comm" 2>/dev/null && [ "$c" = sleep ] && kill "${d#/proc/}"; done
sleep 1

echo "== cpu.max: busy loop for 2 s of wall time"
timeout 2 sh -c 'while :; do :; done'

echo "== memory.max: touch up to 256 MiB"
hog 256
echo "hog exit status: $?"
