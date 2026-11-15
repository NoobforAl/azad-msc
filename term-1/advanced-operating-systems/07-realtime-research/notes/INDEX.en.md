# 07 — Notes index (Real-Time & Research Topics)

Read in order; each note has the 7 sections (summary, explanation, diagram, worked example, pitfalls, key points, links). Farsi: [`INDEX.fa.md`](INDEX.fa.md).

| # | Note | Main kernel files | Lab | Quiz |
|---|---|---|---|---|
| 01 | [Hard, firm and soft real-time; WCET and latency](01-hard-soft-realtime-wcet.en.md) | `kernel/sched/core.c` (`try_to_wake_up`, `__schedule`) | 01 | 1, 2, 7 |
| 02 | [RT scheduling: RMS, EDF and `SCHED_DEADLINE`](02-rt-scheduling-rms-edf-deadline.en.md) | `kernel/sched/deadline.c`, `Documentation/scheduler/sched-deadline.rst` | 01 (ext.) | 3, 8, 12 |
| 03 | [Priority inversion and inheritance (Mars Pathfinder)](03-priority-inversion-inheritance.en.md) | `kernel/locking/rtmutex.c`, `kernel/futex/pi.c`, `kernel/sched/core.c` | 02 | 4, 9, 13 |
| 04 | [`PREEMPT_RT`](04-preempt-rt.en.md) | `kernel/Kconfig.preempt`, `kernel/locking/spinlock_rt.c`, `init/Makefile` | 01 | 5, 10, O1 |
| 05 | [seccomp-BPF, LSM and Landlock](05-seccomp-lsm-landlock.en.md) | `kernel/seccomp.c`, `kernel/entry/syscall-common.c`, `security/landlock/` | 03, 04 | 6, 11, 14, O3 |
| 06 | [How to read an OS research paper](06-reading-os-papers.en.md) | `kernel/sched/fair.c`, `include/linux/dcache.h` (paper mapping) | 05 | 15, O2 |

Total reading time ≈ 2.5 h. Prerequisites: Module 02 notes on scheduling classes and Module 03 notes on futex and mutex.
