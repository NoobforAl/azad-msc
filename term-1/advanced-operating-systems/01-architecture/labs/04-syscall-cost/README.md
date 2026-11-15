# Lab 01.4 — What does a syscall cost? `getpid` vs vDSO `clock_gettime` vs strace

**Goal:** measure in nanoseconds the price of crossing the user/kernel boundary, show that the vDSO avoids it, and show what ptrace (strace) adds to every call.

Runs on: the `aos-lab` VM (user space). The guest has **no hardware PMU counters** (`perf stat -e cycles` → `<not supported>`), so all timing uses `clock_gettime(CLOCK_MONOTONIC)` in C. Time: 40 min.

## Steps

```bash
scp -r term-1/advanced-operating-systems/01-architecture/labs/04-syscall-cost aos-lab:~/work/01-architecture/lab04
ssh aos-lab
cd ~/work/01-architecture/lab04
gcc -Wall -Wextra -O2 -o syscost syscost.c
taskset -c 2 ./syscost                                   # 7 rounds x 2,000,000 calls each
grep -E 'vdso|vvar' /proc/self/maps                      # the vDSO pages in a process
strace -f -c -e trace=getpid,clock_gettime ./syscost 200000 > /dev/null   # which calls entered the kernel?
time ./syscost 200000 > /dev/null; time strace -o /dev/null ./syscost 200000 > /dev/null
```

## Code

- [`syscost.c`](syscost.c): four benchmarks, each with a warm-up and 7 timed rounds, reporting the min and median ns/call. It also prints where the vDSO is mapped (`getauxval(AT_SYSINFO_EHDR)`), the clocksource, and the Meltdown/PTI status.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. The 8-vCPU guest was shared with other users. The first `syscost` run below was taken while the load average was about 12, the second a few minutes later, so expect different absolute numbers. Numbers are unedited.

```text
$ taskset -c 2 ./syscost            # load average ~12
vDSO mapped at         0x77e5da0b6000
clocksource            tsc
meltdown (PTI)         Not affected
calls per round        2000000 x 7 rounds

empty loop                         min     8.3  median     9.8 ns/call
clock_gettime() via vDSO           min    62.7  median    74.4 ns/call
syscall(SYS_clock_gettime)         min   458.4  median   577.7 ns/call
syscall(SYS_getpid)                min   412.8  median   483.3 ns/call

$ taskset -c 2 ./syscost            # a few minutes later
...
empty loop                         min     2.2  median     3.2 ns/call
clock_gettime() via vDSO           min    14.5  median    14.8 ns/call
syscall(SYS_clock_gettime)         min   110.3  median   123.9 ns/call
syscall(SYS_getpid)                min    91.4  median    96.8 ns/call

$ grep -E 'vdso|vvar' /proc/self/maps
725f9b9e4000-725f9b9e8000 r--p 00000000 00:00 0                          [vvar]
725f9b9e8000-725f9b9ea000 r--p 00000000 00:00 0                          [vvar_vclock]
725f9b9ea000-725f9b9ec000 r-xp 00000000 00:00 0                          [vdso]

$ strace -f -c -e trace=getpid,clock_gettime ./syscost 200000 > /dev/null
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 68.71   21.308826          15   1420000           clock_gettime
 31.29    9.703157           6   1420000           getpid
------ ----------- ----------- --------- --------- ----------------
100.00   31.011983          10   2840000           total

$ time ./syscost 200000 > /dev/null
real	0m1.351s
user	0m0.325s
sys	0m0.663s

$ time strace -o /dev/null ./syscost 200000 > /dev/null
real	1m10.384s
user	0m3.648s
sys	0m46.337s
```

## What to observe

- **Each step costs roughly 5–10× the previous one.** In the calmer run, an empty loop iteration costs ~3 ns, a vDSO `clock_gettime()` ~15 ns, and a real syscall ~100–125 ns. That makes the vDSO about **8× cheaper** than the same call made through `syscall` (14.8 vs 123.9 ns median). The ratio stays about the same under load (74 vs 578 ns, 7.8×), even though every absolute number grew about 4×.
- **The vDSO never entered the kernel.** strace counted 1,420,000 `clock_gettime` calls, exactly the number of *forced* calls: 200,000 per round × 7 rounds plus the 20,000 warm-up calls, i.e. only the `syscall(SYS_clock_gettime)` benchmark. The 1,420,000 vDSO calls made by the other benchmark are absent, because they ran entirely in ring 3 using the TSC (`clocksource tsc`) and the `[vvar]`/`[vvar_vclock]` data pages.
- **No PTI here.** `meltdown: Not affected`, so no `CR3` switch on entry/exit. On a Meltdown-affected CPU with PTI, the syscall rows grow, and the vDSO row does not.
- **strace costs ~50× the program.** 1.35 s → 70.4 s, with `sys` time going from 0.66 s to 46 s. Every traced syscall stops in `ptrace_report_syscall_entry()` / `…_exit()` and wakes the tracer (`kernel/entry/syscall-common.c` L20–67). Never benchmark under strace.
- **getpid ≈ clock_gettime as a syscall.** Both bodies are tiny. What you measure is the fixed price of `syscall` + entry/exit work + `sysret`.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| vDSO `clock_gettime` costs as much as a syscall | the clocksource isn't vDSO-capable (`hpet`, `acpi_pm`), so the vDSO falls back to `syscall` | `cat /sys/devices/system/clocksource/clocksource0/current_clocksource` |
| numbers change 2× between runs | shared VM, other tenants, frequency | use min/median, pin with `taskset`, compare in one run |
| empty loop reports 0 ns | the compiler deleted the loop | keep the `volatile` sink |
| `perf stat -e cycles` → `<not supported>` | no PMU in this guest | that's why this lab times in C |

## Extension task

Measure the cost of a syscall number that **doesn't exist** (`syscall(1000)` → `-ENOSYS`) against `getpid`. Trace in `arch/x86/entry/syscall_64.c` which code runs for it, and explain why it is barely cheaper.

Solution: [`solution/enosys.c`](solution/enosys.c).
