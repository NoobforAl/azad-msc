# Lab 07.1 — answers

## What to observe

1. **Min/Avg/Max.** Under load the **max** moves most; min and avg barely change. The min is the fixed path (timer IRQ, `try_to_wake_up()`, `__schedule()`); the max is the time the CPU spent unable to switch to the woken task (non-preemptible sections, softirq processing, and on a VM, the host not running our vCPU).
2. **Histogram tail.** Count samples above 100 µs with
   `grep -v '^#' load.hist | awk '$1>=100 {n+=$2+$3} END {print n}'`
   (columns: latency µs, count thread 0, count thread 1). Every one of them is a missed 100 µs deadline for a control loop with that budget.
3. **Preemption models.** Expected order on bare metal under kernel-heavy load: `none` ≥ `voluntary` ≥ `full` for the max. If the VM shows no clear order, the hypervisor's scheduling noise is larger than the kernel's preemption effect; that is a valid finding, not a failure.
4. **`PREEMPT_RT`.** `uname -v` shows `PREEMPT_DYNAMIC` (from `init/Makefile` L29); an RT build would show `PREEMPT_RT` (L30). `ls /sys/kernel/realtime` → "No such file or directory" in v6.18.63.

## Extension

`solution/latency-dl.c` uses `sched_setattr(SCHED_DEADLINE, runtime 200 µs, deadline = period = 1 ms)` and ends each job with `sched_yield()`, which for a deadline task means "throttle me until my next period" (`dl_yielded` in `update_curr_dl_se()`, deadline.c L1481). It measures the period jitter between consecutive wake-ups.

(a) `runtime 1100 µs, period 1000 µs` → `sched_setattr: Invalid argument` (`EINVAL`) from `__checkparam_dl()` (deadline.c L3585-3587: `deadline < runtime`).

(b) Each idle `chrt -d` reservation takes 0.9 CPU of bandwidth. The limit is `sched_rt_runtime_us / sched_rt_period_us` = 0.95 per CPU, scaled by the root domain's capacity: 8 × 0.95 = 7.6. Eight reservations use 7.2; the ninth would make 8.1 > 7.6, so `__dl_overflow()` returns true and `sched_setattr()` fails with `EBUSY` ("Device or resource busy"). The tasks only *sleep*: admission control reserves bandwidth, it does not measure use.

Comparison FIFO vs DEADLINE: under `stress-ng` on the same CPUs, the deadline task runs **above** all `SCHED_FIFO` tasks, so it is not disturbed by FIFO load; against `SCHED_OTHER` load both behave similarly. Its jitter is still bounded below by the same IRQ/preemption latency: `SCHED_DEADLINE` changes *who* runs first, not *how fast* the kernel can switch.
