# Lab 07.1 — Measure wake-up latency with `cyclictest` (and a ~70-line clone)

> **VM only.** `compare-preempt.sh` flips a **global** kernel switch (`/sys/kernel/debug/sched/preempt`) and restores it on exit; `cyclictest` runs `SCHED_FIFO` 80 threads. Never do this on a production server. Snapshot first if your VM is not disposable.

**Goal:** measure scheduling latency as a histogram, see what load does to the **maximum**, compare the `PREEMPT_DYNAMIC` modes, and know exactly how to get the `PREEMPT_RT` numbers.

Runs on: the `aos-lab` VM (Ubuntu 24.04, mainline 6.18.63 `PREEMPT_DYNAMIC`, 8 vCPU, VirtualBox on Hyper-V, **shared with other users**). Expect different absolute numbers on your machine; on a VM the hypervisor dominates the tail.

## Files

| File | What |
|---|---|
| `latency.c` | ~70-line mini-cyclictest: `SCHED_FIFO`, `mlockall`, `clock_nanosleep(TIMER_ABSTIME)`, histogram |
| `run-cyclictest.sh` | `cyclictest` on 2 CPUs, idle and under `stress-ng`, histograms to `idle.hist` / `load.hist` |
| `compare-preempt.sh` | same loaded run under each `PREEMPT_DYNAMIC` mode, restores the original mode |
| `solution/latency-dl.c` | extension solution: the same loop under `SCHED_DEADLINE` |
| `solution/answers.md` | answers to "what to observe" and the extension |

## Steps

```bash
cd ~/work/07-realtime-research/01-cyclictest
uname -v                                  # PREEMPT_DYNAMIC or PREEMPT_RT?
sudo cat /sys/kernel/debug/sched/preempt  # active mode in parentheses

# 1. Our own measurement loop
gcc -Wall -Wextra -O2 -o latency latency.c
sudo ./latency 80 1000 10000              # FIFO 80, 1 ms period, 10 s

# 2. cyclictest: idle vs loaded, 60 s each, pinned to CPUs 2,3
sudo bash run-cyclictest.sh 60 2,3

# 3. Preemption models (VM only; restores the original mode)
sudo bash compare-preempt.sh 30 2,3 "none voluntary full"
```

## Code

`latency.c` (core loop; full file in this folder):

```c
clock_gettime(CLOCK_MONOTONIC, &next);
for (long i = 0; i < loops; i++) {
    ts_add_ns(&next, interval_us * 1000);
    /* TIMER_ABSTIME: no drift, the deadline is fixed in advance. */
    clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL);
    clock_gettime(CLOCK_MONOTONIC, &now);
    int64_t lat = ts_ns(&now) - ts_ns(&next);
    ...
}
```

`cyclictest` flags used: `-m` mlockall · `-p 80` `SCHED_FIFO` 80 · `-i 1000` 1 ms period · `-a 2,3 -t 2` one thread pinned per CPU · `-h 400` histogram up to 400 µs · `-q` summary only · `-D 60s`.

## Expected output

> Captured on aos-lab (VirtualBox on Hyper-V, Ubuntu 24.04, Linux 6.18.63 `PREEMPT_DYNAMIC`, 8 vCPU, shared with other users), 2026-11-15. Your numbers will differ.

```text
$ sudo ./latency 80 1000 10000
policy=SCHED_FIFO prio=80 interval=1000us loops=10000 overruns=6323
latency us: min=35 avg=1012 max=159033
  <     5 us : 0
  <    10 us : 0
  <    20 us : 0
  <    50 us : 7
  <   100 us : 84
  <   500 us : 5379
  <  1000 us : 1543
  >= 1000 us : 2987

$ sudo bash run-cyclictest.sh 60 2,3
== kernel: #202611101835 SMP PREEMPT_DYNAMIC Tue Nov 10 19:12:55 UTC 2026
== preempt mode: none (voluntary) full lazy
[idle] # Min Latencies: 00030 00026
[idle] # Avg Latencies: 01236 01165
[idle] # Max Latencies: 395586 395126
[idle] # Histogram Overflows: 20086 22111
[load] # Min Latencies: 00032 00031
[load] # Avg Latencies: 09389 09364
[load] # Max Latencies: 26624226 26624344
[load] # Histogram Overflows: 04197 04139
histograms: /home/fred/work/07-realtime-research/01-cyclictest/idle.hist /home/fred/work/07-realtime-research/01-cyclictest/load.hist
$ grep '^# Total' idle.hist load.hist
idle.hist:# Total: 000012387 000011977
load.hist:# Total: 000002019 000002087

$ sudo bash compare-preempt.sh 30 2,3 "none voluntary full"
original: none (voluntary) full lazy
(none) voluntary full lazy  avg_us=[02205 02541]  max_us=[433118 1363610]
none (voluntary) full lazy  avg_us=[03492 03606]  max_us=[998221 997993]
none voluntary (full) lazy  avg_us=[02602 02526]  max_us=[1484984 1484192]
restored: none (voluntary) full lazy
# ^ printed minutes later: the restoring write blocked (see pitfalls)
$ sudo cat /sys/kernel/debug/sched/preempt
none (voluntary) full lazy
```

**Reading our run.** The minimum (26–36 µs) is the real floor of this virtual CPU. Everything else is the host: during the loaded cyclictest run the guest's vCPUs were stopped for up to **26.6 s** (max 26624226 µs), and only about 6 200 of the expected 60 000 wake-ups per thread happened at all (2 019 inside the 400 µs histogram + 4 197 overflows). `latency` counted 6323 skipped periods out of 10 000. The shape — load moves the maximum and the tail, not the minimum — is the lesson; the numbers are not Linux's.

## What to observe

1. **Min vs Avg vs Max.** The min is the hardware/kernel floor (timer + wake-up + switch). The max is what a real-time designer budgets for. Which one changes most between idle and loaded?
2. **Histogram tail.** `grep -v '^#' load.hist | awk '$2+$3>0' | tail` lists the slowest buckets. How many samples are above 100 µs? (Each sample is one millisecond of a real control loop.)
3. **Preemption models.** Under load, `none` should show the worst maximum and `full` the best, because the waiting step 3 (lesson slide 5) can end sooner. On a VM the difference can drown in hypervisor noise: say so instead of over-reading it.
4. **Where is `PREEMPT_RT`?** `uname -v` shows `PREEMPT_DYNAMIC`, and `/sys/kernel/realtime` does not exist (`ls` fails). The RT kernel is a different build: see below.

## `PREEMPT_RT` comparison — `UNVERIFIED` here

The shared VM may not change its kernel. To complete the comparison on **your own** VM:

```bash
# 00-setup lab 03, RT flavor (sets EXPERT + PREEMPT_RT and checks .config)
bash ../../00-setup/labs/03-build-kernel/build-kernel.sh --rt
sudo reboot
uname -v | grep -o PREEMPT_RT              # must print PREEMPT_RT
ps -eo pid,cls,rtprio,comm | grep 'irq/' | head   # threaded IRQs, FF 50
sudo bash run-cyclictest.sh 300 2,3        # 5 min idle + 5 min loaded
```

Fill this table with your numbers. Ours (µs, loaded 30 s runs from `compare-preempt.sh`, thread 0 / thread 1, captured on the shared VM — meaningless as bounds, see note 04):

| Kernel | Mode | Avg | Max |
|---|---|---|---|
| 6.18.63 generic | `PREEMPT_DYNAMIC` none | 2205 / 2541 | 433118 / 1363610 |
| 6.18.63 generic | `PREEMPT_DYNAMIC` full | 2602 / 2526 | 1484984 / 1484192 |
| 6.18.63-aos-rt | `PREEMPT_RT` | `UNVERIFIED` | `UNVERIFIED` |

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `sched_setscheduler(SCHED_FIFO, 80): Operation not permitted` | not root, no `CAP_SYS_NICE`, or `RLIMIT_RTPRIO` = 0 | `sudo`, or `ulimit -r 99` for your user via `/etc/security/limits.conf` |
| `/sys/kernel/debug/sched/preempt: No such file` | debugfs not mounted, or kernel without `PREEMPT_DYNAMIC` | `sudo mount -t debugfs none /sys/kernel/debug`; check `uname -v` |
| Max in the tens of milliseconds | VM vCPU descheduled by the host | normal on a shared VM; pin the VM's vCPUs on the host, or run on bare metal |
| Max is tiny without load | you measured the easy case | always report the loaded run |
| `mlockall: Cannot allocate memory` | `RLIMIT_MEMLOCK` too low | run as root, or raise `memlock` in limits.conf |
| `echo voluntary > /sys/kernel/debug/sched/preempt` hangs for minutes (process in `R` state, unkillable) | `sched_dynamic_update()` (`kernel/sched/core.c` L7746) flips the static calls/keys for `cond_resched`, `preempt_schedule` and friends (`__sched_dynamic_update()`, L7684), which patches kernel text on all CPUs; on an overloaded VM with 8 busy vCPUs this took minutes (seen on aos-lab) | switch modes only on an idle machine, never in a loop; or use the `preempt=` boot parameter instead |
| `stress-ng: ... stressor terminated with unexpected signal signal 4 'SIGILL'` | the `--hdd` stressor hits an instruction this VirtualBox guest doesn't support | use `--iomix` (what the scripts now do); check with `--metrics-brief` that every stressor `passed` |

## Extension task

Rewrite `latency.c` to run under `SCHED_DEADLINE` (runtime 200 µs, deadline = period = 1 ms) using `sched_setattr()`, where each loop iteration ends the current job with `sched_yield()`. Compare its period jitter with the `SCHED_FIFO` version under the same `stress-ng` load. Then (a) start it with runtime 1100 µs and period 1000 µs, and (b) reserve 900 µs/1000 µs for idle tasks (`chrt -d --sched-runtime 900000 --sched-deadline 1000000 --sched-period 1000000 0 sleep 30 &`) until one fails. Which error does each case return, which kernel function produced it, and why does (b) fail at exactly that count on an 8-CPU VM?

Solution: [`solution/latency-dl.c`](solution/latency-dl.c) and [`solution/answers.md`](solution/answers.md).
