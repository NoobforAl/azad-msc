#!/usr/bin/env bash
# shellcheck disable=SC2024  # sudo runs the tool; the transcript is meant to stay user-owned
# capture-all.sh: build every lab of Module 02, re-run labs 02.3-02.6, save each transcript to out/<name>.txt.
# Used to capture the "Expected output" sections on the lab VM. Run from labs/:
#   bash capture-all.sh            (takes ~4 min; uses CPUs 0-3, sudo for tracing and SCHED_FIFO)
set -u
cd "$(dirname "$0")" || exit 1
mkdir -p out
OUT="$(pwd)/out"
# build everything first (zero warnings expected)
for f in */*.c */solution/*.c; do gcc -Wall -Wextra -O2 -pthread -o "${f%.c}" "$f" || exit 1; done
(cd 06-goroutines-vs-threads && go build -o gvt gvt.go && cd solution && go build -o netpoll netpoll.go) || exit 1
PERF=$(command -v perf || ls /usr/lib/linux-tools-*/perf | head -1)
START="${1:-0}"   # bash capture-all.sh 4  -> skip labs 02.3 and earlier
run() { local name=$1; shift; echo "== $name"; { "$@"; } > "$OUT/$name.txt" 2>&1; }

[ "$START" -le 0 ] && run ctx-info bash -c 'uname -rv; nproc; uptime;
  echo -n "base_slice_ns: "; sudo cat /sys/kernel/debug/sched/base_slice_ns;
  echo -n "preempt: "; sudo cat /sys/kernel/debug/sched/preempt;
  echo -n "fair_server cpu3 runtime/period: "; sudo cat /sys/kernel/debug/sched/fair_server/cpu3/runtime /sys/kernel/debug/sched/fair_server/cpu3/period | tr "\n" " "; echo;
  echo -n "sched_rt_runtime_us/period_us: "; cat /proc/sys/kernel/sched_rt_runtime_us /proc/sys/kernel/sched_rt_period_us | tr "\n" " "; echo;
  echo -n "sched_rr_timeslice_ms: "; cat /proc/sys/kernel/sched_rr_timeslice_ms;
  echo -n "pid_max: "; cat /proc/sys/kernel/pid_max;
  echo -n "sched_ext state: "; cat /sys/kernel/sched_ext/state 2>&1'

[ "$START" -le 0 ] && run classes bash -c 'echo "\$ ps -eo pid,cls,rtprio,ni,pri,comm | awk ..."; ps -eo pid,cls,rtprio,ni,pri,comm | awk "NR==1 || \$2!=\"TS\"" | head -8;
  echo "\$ chrt -p 1"; chrt -p 1;
  echo "\$ sudo grep -E \"^(policy|prio|se.slice)\" /proc/1/sched"; sudo grep -E "^(policy|prio|se.slice)" /proc/1/sched'

if [ "$START" -le 3 ]; then
cd 03-ctxsw-pingpong || exit 1
run pingpong-run bash run.sh
run pingpong-perf bash -c "$PERF stat -e context-switches,cpu-migrations,task-clock ./pingpong same 200000; $PERF stat -e context-switches,cpu-migrations,task-clock ./pingpong split 20000"
run ipc-rtt bash -c 'for m in pipe unix shm; do for s in "" -s; do n=200000; [ -n "$s" ] && n=20000; for i in 1 2 3 4 5; do ./solution/ipc_rtt $m $n $s; done; done; done'
cd .. || exit 1

fi
if [ "$START" -le 4 ]; then
cd 04-perf-sched-bpftrace || exit 1
cp ../03-ctxsw-pingpong/pingpong .
for _ in 1 2; do timeout 8 taskset -c 2 sh -c 'while :; do :; done' & done
timeout 8 taskset -c 2 ./pingpong free 3000000 > /dev/null &
sleep 1
sudo $PERF sched record -C 2 -o /tmp/m02-perf.data -- sleep 3 > $OUT/perf-record.txt 2>&1
wait
sudo $PERF sched latency -i /tmp/m02-perf.data --sort max > $OUT/perf-sched-latency.txt 2>&1
sudo $PERF sched timehist -i /tmp/m02-perf.data > $OUT/perf-sched-timehist.txt 2>&1
sudo rm -f /tmp/m02-perf.data
for _ in 1 2; do timeout 8 taskset -c 2 sh -c 'while :; do :; done' & done
timeout 8 taskset -c 2 ./pingpong free 3000000 > /dev/null &
sleep 1
sudo timeout 20 bpftrace switch_kinds.bt > $OUT/switch-kinds.txt 2>&1
wait
for _ in 1 2; do timeout 8 taskset -c 2 sh -c 'while :; do :; done' & done
sleep 1
timeout 8 taskset -c 2 ./pingpong free 3000000 > /dev/null &
sleep 1
sudo timeout 20 bpftrace solution/runqlat.bt > $OUT/runqlat.txt 2>&1
wait
cd .. || exit 1

fi
cd 05-sched-policies || exit 1
run share-00 ./share 0 0
run share-05 ./share 0 5
run share-0010 ./share 0 0 10
run share-fifo sudo ./share fifo 0
run slice ./slice 50000 3000000 0
run wakelat bash -c './solution/wakelat; ./solution/wakelat 100000'
cd .. || exit 1

cd 06-goroutines-vs-threads || exit 1
run gvt bash -c './gvt sleep 10000; echo; GOMAXPROCS=2 ./gvt cpu 100; echo; ./gvt cpu 100; echo; ./gvt syscall 200'
run threads ./threads 10000
run gvt-proc bash -c './gvt syscall 50 > /dev/null & sleep 0.5; P=$(pgrep -n gvt);
  echo "\$ grep -E \"Threads|voluntary\" /proc/\$P/status"; grep -E "Threads|voluntary" /proc/$P/status;
  echo "\$ ls /proc/\$P/task | wc -l"; ls /proc/$P/task | wc -l;
  echo "\$ ps -L -o pid,lwp,stat,wchan:20,comm -p \$P | head -6"; ps -L -o pid,lwp,stat,wchan:20,comm -p $P | head -6; wait'
run netpoll ./solution/netpoll 200
cd .. || exit 1
echo "done"
