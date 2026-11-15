# Lab 02.4 — Watch the scheduler: `perf sched` and bpftrace on `sched_switch`

**Goal:** record real scheduler events under load, read per-task scheduling latency with `perf sched latency` / `timehist`, and classify every context switch as voluntary or involuntary with a bpftrace script built on the `prev_state` test in `__schedule()`.

Runs on: the lab VM (needs root for tracing). Observation only, no kernel changes. Load is kept small (two shell busy loops and a ping-pong on CPU 2, 8 s) because the VM is shared.

## Steps

```bash
cd ~/work/02-processes-threads && cp -r <repo>/.../labs/04-perf-sched-bpftrace . && cd 04-perf-sched-bpftrace
cp ../03-ctxsw-pingpong/pingpong .            # from lab 02.3
PERF=$(command -v perf || ls /usr/lib/linux-tools-*/perf | head -1)

# 1. load: two CPU hogs and a ping-pong, all pinned to CPU 2
for i in 1 2; do timeout 8 taskset -c 2 sh -c 'while :; do :; done' & done   # two CPU hogs
timeout 8 taskset -c 2 ./pingpong free 3000000 > /dev/null &
sleep 1

# 2. record 3 s of scheduler events on CPU 2
sudo $PERF sched record -C 2 -- sleep 3
sudo $PERF sched latency --sort max | head -15
sudo $PERF sched timehist | head -20

# 3. voluntary vs involuntary, whole machine, 5 s (start a fresh load first)
wait
for i in 1 2; do timeout 8 taskset -c 2 sh -c 'while :; do :; done' & done   # two CPU hogs
timeout 8 taskset -c 2 ./pingpong free 3000000 > /dev/null &
sleep 1
sudo bpftrace switch_kinds.bt
wait
```

## Code

[`switch_kinds.bt`](switch_kinds.bt): attaches to `tracepoint:sched:sched_switch`. The tracepoint is called in `__schedule()` with `prev_state`. If `prev_state == 0` (`TASK_RUNNING`), the outgoing task was still runnable, so it was **preempted** (involuntary). Otherwise it went to sleep (voluntary). These are the same two counters as `nivcsw` / `nvcsw` in `/proc/<pid>/status`.

## Expected output

Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15:

```text
$ sudo perf sched latency --sort max | head -9

 -------------------------------------------------------------------------------------------------------------------------------------------
  Task                  |   Runtime ms  | Switches | Avg delay ms    | Max delay ms    | Max delay start           | Max delay end          |
 -------------------------------------------------------------------------------------------------------------------------------------------
  sh:(2)                |   2083.096 ms |      179 | avg:  18.576 ms | max: 101.378 ms | max start:    74.628078 s | max end:    74.729456 s
  pingpong:(2)          |    676.888 ms |   187804 | avg:   0.014 ms | max:  92.529 ms | max start:    74.064690 s | max end:    74.157219 s
  gdbus:(4)             |      0.702 ms |        5 | avg:   1.510 ms | max:   7.312 ms | max start:    75.290155 s | max end:    75.297467 s
  kworker/2:0-mm_:31    |      0.341 ms |       11 | avg:   0.248 ms | max:   2.522 ms | max start:    75.350262 s | max end:    75.352784 s
 ...
  TOTAL:                |   2788.375 ms |   188014 |
```

```text
$ sudo perf sched timehist | sed -n '1,4p;525,536p'
Samples of sched_switch event do not have callchains.
           time    cpu  task name                       wait time  sch delay   run time
                        [tid/pid]                          (msec)     (msec)     (msec)
--------------- ------  ------------------------------  ---------  ---------  ---------
      72.572512 [0002]  sh[2388]                            0.000      0.000     42.345
      72.572541 [0002]  pingpong[2389]                     42.348     42.347      0.028
      72.587169 [0002]  sh[2387]                            0.000      0.000     14.628
      72.587202 [0002]  pingpong[2390]                     57.001     14.636      0.033
      72.597553 [0002]  sh[2387]                            0.033      0.000     10.351
      72.597579 [0002]  pingpong[2389]                     25.012     10.363      0.025
      72.597588 [0002]  pingpong[2390]                     10.376      0.007      0.008
      72.597591 [0002]  pingpong[2389]                      0.008      0.002      0.003
      72.607908 [0002]  sh[2387]                            0.037      0.000     10.316
      72.607930 [0002]  pingpong[2390]                     10.319     10.318      0.022
      72.607939 [0002]  pingpong[2389]                     10.339      0.006      0.008
      72.607943 [0002]  pingpong[2390]                      0.008      0.002      0.003
```

```text
$ sudo bpftrace switch_kinds.bt
Attaching 2 probes...
@involuntary[systemd-journal]: 3
@involuntary[dbus-daemon]: 4
@involuntary[sh]: 402
@involuntary[pingpong]: 3260
@voluntary[kworker/u37:0]: 29
@voluntary[rcu_preempt]: 38
@voluntary[sshd]: 39
@voluntary[kworker/u37:2]: 39
@voluntary[kworker/4:1]: 58
@voluntary[pingpong]: 703563
```

## What to observe

- **`perf sched latency`**: `Avg delay` / `Max delay` is the time from wakeup to actually running. `pingpong` (187,804 switches) waits 0.014 ms on average: it wakes with lag ≥ 0 and preempts the hogs at once. The two `sh` busy loops wait 18.6 ms on average (max 101 ms): they are runnable all the time and only get the CPU when the other hog and the ping-pong let them.
- **`timehist`**: `wait time` = time on the run queue before this run, `sch delay` = wakeup → run, `run time` = how long it ran. `pingpong` runs last 3–30 µs. The hog runs here last **10–42 ms**, much longer than the 2.8 ms `base_slice_ns`. The likely cause is that the VM's vCPU is itself time-sliced by the host, so guest timestamps include host-side gaps. VirtualBox reports no steal time (`/proc/stat` steal = 0), so this is **UNVERIFIED**. On bare metal, expect runs close to one slice.
- **bpftrace**: the `sh` hogs appear only in `@involuntary`: they never block, so every switch-out is a preemption (`prev_state == 0`). `pingpong` is overwhelmingly `@voluntary` (703,563 vs 3,260): it blocks in `read()` every round trip. Without the hogs, lab 02.3's `same` mode shows ~43% involuntary switches for `pingpong`, because the woken partner preempts the writer before the writer reaches `read()`.
- `swapper/N` (the idle task) is filtered out (`prev_pid != 0`). Other tasks of the shared VM show up too; that is real data, not noise to delete.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `perf sched record` fails with "No permission" | `perf_event_paranoid` > 1 | run with `sudo` |
| `perf sched latency` is empty | nothing ran on `-C 2` during recording | start the load first; check `taskset -c 2` |
| perf warnings about unknown tracepoint fields | perf 6.8 userspace on a 6.18 kernel | harmless for `sched` events; fields used here are stable |
| bpftrace: `ERROR: ... prev_state` | very old bpftrace or kernel without BTF | use the VM's bpftrace; check `/sys/kernel/btf/vmlinux` |
| `stress-ng` workers die with `caught SIGILL ... ILL_ILLOPN` | some `--cpu` methods use instructions this VirtualBox vCPU does not expose | use a shell busy loop (as above) or `stress-ng --cpu-method int64` |
| `perf.data` owned by root | recorded with sudo | `sudo chown $USER perf.data` or keep using sudo |

## Extension task

Write a bpftrace script that measures **run-queue latency** (wakeup → actually on CPU) as a histogram, and compare it for `pingpong` vs everything else while the load above is running. Handle preempted tasks, which re-enter the queue at `sched_switch` with `prev_state == 0` and are never woken.

Solution: [`solution/runqlat.bt`](solution/runqlat.bt).
