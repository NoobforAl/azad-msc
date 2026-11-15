# Lab 02.3 — Context-switch cost with a pipe ping-pong

**Goal:** measure the cost of a blocking round trip between two processes when both share one CPU (two real context switches) and when they sit on two CPUs (cross-CPU wakeups), and explain the difference.

Runs on: the lab VM. User space only. **Timing lab**: the VM is a shared 8-vCPU VirtualBox guest, so run several repetitions and report the median. Your absolute numbers will differ, but the comparison between the modes should look the same.

## Steps

```bash
cd ~/work/02-processes-threads && cp -r <repo>/.../labs/03-ctxsw-pingpong . && cd 03-ctxsw-pingpong
gcc -Wall -Wextra -O2 -o pingpong pingpong.c
./pingpong same 200000            # one run
bash run.sh                       # 5 runs per mode + medians
# what the kernel counted
perf stat -e context-switches,cpu-migrations,task-clock ./pingpong same 200000
perf stat -e context-switches,cpu-migrations,task-clock ./pingpong split 20000
# the same thing with taskset instead of sched_setaffinity in the code
taskset -c 2 ./pingpong free 200000
```

## Code

- [`pingpong.c`](pingpong.c): parent and child exchange one byte over two pipes `iters` times. `same` pins both to CPU 0 with `sched_setaffinity()`, `split` puts them on CPU 0 and CPU 1, `free` leaves the choice to the scheduler. Prints the mean round trip and the parent's voluntary/involuntary switch counts from `getrusage()`.
- [`run.sh`](run.sh): 5 runs per mode, prints the median round trip. `split` uses 20,000 round trips instead of 200,000 (`SPLIT_ITERS`), because on this VM each cross-vCPU round trip takes milliseconds.

## Expected output

Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Shared VM: medians of 5 runs.

```text
$ bash run.sh
mode=same  iters=199999  round_trip=3608 ns  per_switch~1804 ns  parent vcsw=111887 ivcsw=88116
mode=same  iters=199999  round_trip=3064 ns  per_switch~1532 ns  parent vcsw=113258 ivcsw=86745
mode=same  iters=199999  round_trip=2655 ns  per_switch~1327 ns  parent vcsw=113826 ivcsw=86174
mode=same  iters=199999  round_trip=2714 ns  per_switch~1357 ns  parent vcsw=114231 ivcsw=85771
mode=same  iters=199999  round_trip=2717 ns  per_switch~1359 ns  parent vcsw=115381 ivcsw=84623
== same: median round_trip 2717 ns over 5 runs
mode=split iters=19999  round_trip=181469 ns  per_switch~90735 ns  parent vcsw=19987 ivcsw=3
mode=split iters=19999  round_trip=208929 ns  per_switch~104464 ns  parent vcsw=19980 ivcsw=4
mode=split iters=19999  round_trip=197418 ns  per_switch~98709 ns  parent vcsw=19985 ivcsw=5
mode=split iters=19999  round_trip=184377 ns  per_switch~92189 ns  parent vcsw=19986 ivcsw=3
mode=split iters=19999  round_trip=195549 ns  per_switch~97775 ns  parent vcsw=19989 ivcsw=1
== split: median round_trip 195549 ns over 5 runs
mode=free  iters=199999  round_trip=12871 ns  per_switch~6435 ns  parent vcsw=119204 ivcsw=80789
mode=free  iters=199999  round_trip=41754 ns  per_switch~20877 ns  parent vcsw=128660 ivcsw=71306
mode=free  iters=199999  round_trip=12510 ns  per_switch~6255 ns  parent vcsw=118433 ivcsw=81450
mode=free  iters=199999  round_trip=20619 ns  per_switch~10309 ns  parent vcsw=122909 ivcsw=77052
mode=free  iters=199999  round_trip=22720 ns  per_switch~11360 ns  parent vcsw=116681 ivcsw=83255
== free: median round_trip 20619 ns over 5 runs
```

`perf stat`:

```text
$ perf stat -e context-switches,cpu-migrations,task-clock ./pingpong same 200000
mode=same  iters=199999  round_trip=4464 ns  per_switch~2232 ns  parent vcsw=112255 ivcsw=87748

 Performance counter stats for './pingpong same 200000':

            400003      context-switches                 #  446.673 K/sec
                 2      cpu-migrations                   #    2.233 /sec
            895.52 msec task-clock                       #    0.998 CPUs utilized

       0.897345934 seconds time elapsed

$ perf stat -e context-switches,cpu-migrations,task-clock ./pingpong split 20000
mode=split iters=19999  round_trip=270830 ns  per_switch~135415 ns  parent vcsw=19973 ivcsw=3

 Performance counter stats for './pingpong split 20000':

             39947      context-switches                 #   18.000 K/sec
                 2      cpu-migrations                   #    0.901 /sec
           2219.28 msec task-clock                       #    0.409 CPUs utilized

       5.421598670 seconds time elapsed
```

## What to observe

- **`same`:** 2.7 µs per round trip = two context switches plus four pipe syscalls. `perf stat` counts 400,003 switches for 200,000 round trips, exactly 2 per round trip. The parent's counters split about 57% voluntary / 43% involuntary (`vcsw=115381 ivcsw=84623`). Often the parent never reaches its blocking `read()`: its `write()` wakes the child, the child's EEVDF deadline is earlier, and the wakeup preempts the parent while it is still runnable (`prev_state == 0` → `nivcsw`). The parent sleeps voluntarily only when it does reach `read()` first.
- **`split`:** 196 µs per round trip, about 70× slower, although neither task has to switch out for the other to run. Every wakeup goes to another vCPU that has gone idle (halted): the waker sends an IPI, and in VirtualBox on Hyper-V the host must reschedule that vCPU's thread. `ivcsw` is ~0 here, because nobody else wants the CPU, so each switch is to idle (voluntary). Under heavy load from other users of the VM the same test gave ~1.4 ms per round trip. On bare metal the gap is far smaller; with `idle=poll` it reverses.
- **`free`:** 12–42 µs, between the two. The scheduler sometimes keeps both on one CPU (wake-affine, `WF_SYNC` from the pipe code) and sometimes spreads them; the variance between runs shows it.
- **`perf stat`:** `context-switches` counts both tasks, and `cpu-migrations` stays at 2 (the initial pinning). In `split`, `task-clock` shows 0.41 CPUs utilized: most of the time both vCPUs are idle, waiting for wakeups.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| numbers jump 2× between runs | other agents/VMs use the same CPUs | use `run.sh` medians; pin to a quiet CPU |
| `sched_setaffinity: Invalid argument` | CPU 1 doesn't exist (1-vCPU VM) | `nproc`; use `free` mode only |
| `perf: <not supported>` for cycles | no hardware PMU in this VM | use software events (`context-switches`, `task-clock`) |
| round trip ≈ 100 ns | both sides spinning, not blocking | make sure the reads are blocking (no `O_NONBLOCK`) |

## Extension task

Compare the round trip over **three** IPC mechanisms: two pipes, one `AF_UNIX` `socketpair`, and a shared page with `FUTEX_WAIT`/`FUTEX_WAKE`. Run each `same` and `split`, 5 runs each, report medians, and explain why the gap between mechanisms nearly disappears in `split` mode.

Solution: [`solution/ipc_rtt.c`](solution/ipc_rtt.c).
