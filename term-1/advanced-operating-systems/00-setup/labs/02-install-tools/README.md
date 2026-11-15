# Lab 00.2 — Install and verify the tool set

**Goal:** every tool used in Modules 1–7 is installed on the **server and the VM**, and `perf`/`bpftrace` actually work against the running kernel.

## Steps

```bash
bash install-tools.sh        # apt packages + perf for the running kernel + sysctl for tracing
bash verify-tools.sh         # one line per tool; exit code = number of problems
echo $?                      # expect 0
```

Then the **smoke test**, which shows each tool works on the real kernel, not just that it's installed:

```bash
strace -c -f ls / >/dev/null                          # syscall summary table
perf stat -e task-clock,context-switches,page-faults ls >/dev/null
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { @[comm] = count(); } interval:s:3 { exit(); }'
sudo trace-cmd record -p function_graph -g vfs_read -F cat /etc/hostname >/dev/null && trace-cmd report | head -30
sudo execsnoop-bpfcc -t &  sleep 1; ls >/dev/null; sleep 1; sudo kill %1
```

## Tool → module map

| Tool | First used in | For |
|---|---|---|
| `strace`, `ltrace` | M1 | syscall/library-call traces |
| `perf` | M1 | counters, `perf sched` (M2), `perf kvm` (M6) |
| `bpftrace`, bcc (`*-bpfcc`) | M1 | kernel tracing without recompiling |
| `trace-cmd` / ftrace | M1 | function-graph call chains |
| `gdb`, `valgrind` | M3, M4 | thread dumps, memory errors |
| `lsof`, `/proc`, `/sys` | M2 | fds, process state |
| `vmstat`, `iostat`, `pidstat` (sysstat) | M4, M5 | memory and I/O pressure |
| `numactl`, `lstopo` (hwloc) | M4 | NUMA topology |
| `fio`, `liburing-dev` | M5 | I/O benchmarks, `io_uring` |
| `cyclictest` (rt-tests) | M7 | latency |
| `libseccomp-dev` | M7 | seccomp filters |
| `ctags`, `cscope` | all | code navigation (see guide, section 4) |

## Expected output

Captured on the course test VM `aos-lab` (VirtualBox 7.2.22, Ubuntu 24.04, mainline Linux 6.18.63) on 2026-11-15, after `sudo bash install-tools.sh`. Exit code 0. 31 lines are `OK`, and the 24 tool lines in the middle are cut:

```
$ bash verify-tools.sh
== tools
  OK      gcc            /usr/bin/gcc
  OK      clang          /usr/bin/clang
  OK      gdb            /usr/bin/gdb
  ...
== perf works against the running kernel
  OK      perf stat      6.18.63-061863-generic
== kernel features
  OK      CONFIG_DEBUG_INFO_BTF bpftrace struct access (all modules)
  OK      CONFIG_FUNCTION_GRAPH_TRACER ftrace function_graph (M1, M5)
  OK      CONFIG_DEBUG_FS /sys/kernel/debug/sched (M2); SCHED_DEBUG no longer exists in v6.18
  OK      CONFIG_KVM     KVM (M6)
  WARN    CONFIG_PREEMPT_RT real-time kernel (M7, VM only) (not set)
  OK      BTF            /sys/kernel/btf/vmlinux
  OK      cgroup v2      cpuset cpu io memory hugetlb pids rdma misc dmem
  WARN    /dev/kvm       absent (expected inside the VM without nesting)
== sysctl
  perf_event_paranoid    -1
  kptr_restrict          0
== host
  kernel                 6.18.63-061863-generic
  cpus                   8
  virt                   oracle

all required tools present
```

- **`PREEMPT_RT` WARN:** expected on any non-RT kernel. Lab 03 `--rt` builds the RT flavor.
- **`/dev/kvm` WARN:** expected inside a VM without nested virtualization, which is the case for VirtualBox on a Hyper-V host.
- **`perf_event_paranoid -1`:** that VM also has its own `90-aos.conf` that sets -1. With only this lab's file you get `1`.
- **`install-tools.sh` also printed** `note: no Ubuntu perf package for kernel 6.18.63-061863-generic (self-built kernel?)`. On a non-Ubuntu kernel, the `perf` binary from `linux-tools-6.8` works for software events and tracepoints; the test VM links it to `/usr/local/bin/perf`.

## What to observe

- In `strace -c ls`, which syscall is called most often? (Usually `mmap`/`openat`/`newfstatat` from the dynamic loader. That's Module 1 material.)
- In `perf stat`, `ls` causes **~100 page faults** even though it's tiny. Why? (Module 4: demand paging of the binary and its libraries.)
- `trace-cmd` shows `vfs_read()` calling down into `->read_iter()`. This is the call chain you'll walk in Module 5.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `perf: WARNING: perf not found for kernel X` | the `linux-tools-$(uname -r)` package is missing, or this is a self-built kernel | `apt install linux-tools-$(uname -r)`, or lab 03 step 6 |
| `bpftrace: ERROR: ... BTF` | the kernel was built without `CONFIG_DEBUG_INFO_BTF` | use the stock Ubuntu kernel, or the lab 03 kernel |
| `perf_event_open ... paranoid` | `perf_event_paranoid` is 4 (Ubuntu default) | the script sets 1. Check with `sysctl kernel.perf_event_paranoid` |

## Extension task

Write a **one-line `bpftrace`** program that prints, every 2 seconds, the top 5 processes by number of **context switches *out*** (`sched:sched_switch`, keyed by `prev_comm`), then clears the map. Run `stress-ng --cpu 4 --cpu-method int64 --timeout 10` next to it (plain `--cpu` dies with SIGILL on some VirtualBox vCPUs) and explain the result.

Solution: [`solution/top-switchers.bt`](solution/top-switchers.bt).
