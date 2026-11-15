# Lab 02.5 — nice weights, `SCHED_FIFO` vs the fair server, EEVDF custom slices

> **VM only.** This lab runs a `SCHED_FIFO` busy loop. It is pinned to one CPU and limited to 3 s, but an RT spinner on the wrong CPU can freeze a shell or a small machine. Do not run it on a production server.

**Goal:** check three scheduler rules against measurement: (1) CPU share follows `sched_prio_to_weight[]`, (2) an RT task beats every fair task but the fair server still leaves ~5%, (3) `sched_setattr()` sets an EEVDF slice clamped to 0.1–100 ms.

Runs on: the lab VM. Uses CPU 3 for 3 s per run (`-c` to change).

## Steps

```bash
cd ~/work/02-processes-threads && cp -r <repo>/.../labs/05-sched-policies . && cd 05-sched-policies
gcc -Wall -Wextra -O2 -o share share.c
gcc -Wall -Wextra -O2 -o slice slice.c

# 1. weights
./share 0 0                 # equal
./share 0 5                 # 1024 vs 335
./share 0 0 10              # 1024 : 1024 : 110

# 2. RT vs fair (root for SCHED_FIFO)
sudo ./share fifo 0
sudo cat /sys/kernel/debug/sched/fair_server/cpu3/runtime /sys/kernel/debug/sched/fair_server/cpu3/period
cat /proc/sys/kernel/sched_rt_runtime_us /proc/sys/kernel/sched_rt_period_us

# 3. EEVDF slice
sudo cat /sys/kernel/debug/sched/base_slice_ns
./slice 50000 3000000 0
```

## Code

- [`share.c`](share.c): forks one child per argument, all pinned to the same CPU. Each child sets its nice value (or `SCHED_FIFO` priority 10), waits for a common start flag, spins until a common end time 3 s later, and reports the CPU time it got in between (`CLOCK_PROCESS_CPUTIME_ID`). The common end time matters: a starved fair task would otherwise keep running alone after the FIFO task exits and report a far too large share. A first version of this program had exactly that bug and reported 23% for the fair task. The parent prints each share next to the fair prediction from the weight table.
- [`slice.c`](slice.c): calls `sched_setattr(SCHED_OTHER, sched_runtime = N)` through `syscall()` (Ubuntu 24.04's glibc has no wrapper) and reads the slice back with `sched_getattr()` and from `/proc/self/sched` (`se.slice`).

## Expected output

Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15:

```text
$ ./share 0 0
CPU 3, 3.0 s wall, 2 busy tasks
task   policy      cpu_s    share  fair_pred
0      nice:0      1.498    50.0%      50.0%
1      nice:0      1.499    50.0%      50.0%
$ ./share 0 5
CPU 3, 3.0 s wall, 2 busy tasks
task   policy      cpu_s    share  fair_pred
0      nice:0      2.258    75.2%      75.3%
1      nice:5      0.743    24.8%      24.7%
$ ./share 0 0 10
CPU 3, 3.0 s wall, 3 busy tasks
task   policy      cpu_s    share  fair_pred
0      nice:0      1.422    47.4%      47.5%
1      nice:0      1.425    47.5%      47.5%
2      nice:10     0.154     5.1%       5.1%
$ sudo ./share fifo 0
CPU 3, 3.0 s wall, 2 busy tasks
task   policy      cpu_s    share  fair_pred
0      FIFO:10     2.825    94.2%          -
1      nice:0      0.174     5.8%     100.0%
```

```text
$ sudo cat /sys/kernel/debug/sched/fair_server/cpu3/runtime /sys/kernel/debug/sched/fair_server/cpu3/period
50000000
1000000000
$ cat /proc/sys/kernel/sched_rt_runtime_us /proc/sys/kernel/sched_rt_period_us
950000
1000000
$ sudo cat /sys/kernel/debug/sched/base_slice_ns
2800000
```

```text
$ ./slice 50000 3000000 0
default                policy=0 nice=0 sched_runtime=2800000 ns  /proc se.slice=2800000 ns
request 50000 ns       policy=0 nice=0 sched_runtime=100000 ns  /proc se.slice=100000 ns
request 3000000 ns     policy=0 nice=0 sched_runtime=3000000 ns  /proc se.slice=3000000 ns
request 0 ns           policy=0 nice=0 sched_runtime=2800000 ns  /proc se.slice=2800000 ns
```

## What to observe

- **Weights.** `0 5` gives about 75/25, the 1024 : 335 ratio. One nice step is ~10% of CPU, because adjacent weights differ by ×1.25. Shares are close to the prediction, not exact: the VM's CPU 3 also runs other tasks and host steal.
- **FIFO vs fair.** The FIFO task gets ~95% and the fair task ~5%, not 0%. On 6.18 the **fair server** (`fair_server/cpu3`: runtime 50 ms per 1000 ms period) is a `SCHED_DEADLINE` entity. The dl class outranks rt, so the server runs and hands its budget to fair tasks. (`fair_pred` = 100% for the fair task only means it is the only *fair* task; the prediction ignores the RT class.)
- **Slice.** The default is 2.8 ms = 0.7 ms × (1 + log2 8). A 50 µs request is clamped up to 100 µs (`__setparam_fair()`), 3 ms is accepted, and `0` returns to the default. The slice changes **latency** (how soon the task gets the CPU), not share. Running `./share` with one task given a small slice would still give ~50/50.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `SCHED_FIFO (root?): Operation not permitted` | needs `CAP_SYS_NICE` or `RLIMIT_RTPRIO` | `sudo` |
| shares far from prediction | another process is busy on the same CPU | pick a quieter CPU with `-c`, check with `mpstat -P ALL 1` |
| `setpriority: Permission denied` for negative nice | unprivileged users can only raise nice | use 0..19, or `sudo` |
| fair task gets 0% under FIFO | kernel < 6.12 without the fair server and RT throttling disabled (`sched_rt_runtime_us = -1`) | check `/proc/sys/kernel/sched_rt_runtime_us` |
| `/sys/kernel/debug` empty | debugfs not mounted | `sudo mount -t debugfs none /sys/kernel/debug` |

## Extension task

Measure **wakeup latency** instead of share: a task that sleeps 1 ms in a loop and records how late it wakes up, competing on one CPU with two `nice 0` spinners. Compare the default slice with a 0.1 ms custom slice for the sleeper (median and 99th percentile over ~2,000 wakeups). Explain the result with `vd = v + slice/w`.

Solution: [`solution/wakelat.c`](solution/wakelat.c).
