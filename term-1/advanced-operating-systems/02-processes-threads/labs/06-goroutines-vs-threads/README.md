# Lab 02.6 — Goroutines vs OS threads

**Goal:** show that the kernel sees only OS threads (one `task_struct` each, listed in `/proc/<pid>/task`) and that Go multiplexes many goroutines onto few of them, except when goroutines block in syscalls.

Runs on: the lab VM (Go from Ubuntu 24.04) or any Linux box with Go ≥ 1.21. User space only.

## Steps

```bash
cd ~/work/02-processes-threads && cp -r <repo>/.../labs/06-goroutines-vs-threads . && cd 06-goroutines-vs-threads
go version
go build -o gvt gvt.go
gcc -Wall -Wextra -O2 -pthread -o threads threads.c

./gvt sleep 10000                 # 10k parked goroutines
GOMAXPROCS=2 ./gvt cpu 100        # 100 spinning goroutines, 2 Ps
./gvt cpu 100                     # GOMAXPROCS = NumCPU
./gvt syscall 200                 # 200 goroutines blocked in read(2)
./threads 10000                   # 10k pthreads, for comparison

# the kernel's view of a running Go program
./gvt syscall 50 & sleep 0.5; P=$!
grep -E 'Threads|voluntary' /proc/$P/status; ls /proc/$P/task | wc -l
ps -L -o pid,lwp,stat,wchan:20,comm -p $P | head -8
wait
```

## Code

- [`gvt.go`](gvt.go): starts N goroutines in one of three modes and prints `runtime.NumGoroutine()`, the number of entries in `/proc/self/task` (OS threads) and `VmRSS`, before and 1 s after. `syscall` mode uses `syscall.Read` on a pipe. That is a real blocking syscall the netpoller does not manage, so each blocked goroutine keeps its M (OS thread) inside the kernel.
- [`threads.c`](threads.c): N pthreads (64 KiB stacks) that just sleep. Each one is a `clone3(CLONE_THREAD ...)`, so a new kernel task.

## Expected output

Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15:

```text
$ ./gvt sleep 10000
pid=3158 GOMAXPROCS=8 NumCPU=8
start:   goroutines=1      os_threads=5    VmRSS=2068 kB
spawned 10000 goroutines in 241.032481ms (24.10 us each)
after 1s: goroutines=10001  os_threads=10   VmRSS=28760 kB

$ GOMAXPROCS=2 ./gvt cpu 100
pid=3168 GOMAXPROCS=2 NumCPU=8
start:   goroutines=1      os_threads=5    VmRSS=1972 kB
spawned 100 goroutines in 153.651µs (1.53 us each)
after 1s: goroutines=101    os_threads=5    VmRSS=2264 kB

$ ./gvt cpu 100
pid=3173 GOMAXPROCS=8 NumCPU=8
start:   goroutines=1      os_threads=5    VmRSS=2044 kB
spawned 100 goroutines in 258.17µs (2.58 us each)
after 1s: goroutines=101    os_threads=9    VmRSS=2480 kB

$ ./gvt syscall 200
pid=3157 GOMAXPROCS=8 NumCPU=8
start:   goroutines=1      os_threads=5    VmRSS=2040 kB
spawned 200 goroutines in 544.936µs (2.72 us each)
after 1s: goroutines=201    os_threads=204  VmRSS=5776 kB

$ ./threads 10000
start:   os_threads=1      VmRSS=1480 kB
created: os_threads=10001  VmRSS=84680 kB  in 3188.5 ms (318.9 us/thread)
```

```text
$ ./gvt syscall 50 > /dev/null &  P=$!
$ grep -E 'Threads|voluntary' /proc/$P/status
Threads:	52
voluntary_ctxt_switches:	2
nonvoluntary_ctxt_switches:	0
$ ls /proc/$P/task | wc -l
52
$ ps -L -o pid,lwp,stat,wchan:20,comm -p $P | head -6
    PID     LWP STAT WCHAN                COMMAND
  13522   13522 Sl   anon_pipe_read       gvt
  13522   13524 Sl   futex_do_wait        gvt
  13522   13525 Sl   anon_pipe_read       gvt
  13522   13526 Sl   anon_pipe_read       gvt
  13522   13527 Sl   anon_pipe_read       gvt
```

## What to observe

- **sleep**: 10,000 goroutines on 10 OS threads. A sleeping goroutine is a parked G in the runtime, not a sleeping task in the kernel. RSS grows by ~26 MiB, about 2.7 KiB per goroutine (its stack plus runtime bookkeeping).
- **cpu**: 100 spinning goroutines use 5 threads with `GOMAXPROCS=2` and 9 with `GOMAXPROCS=8`: at most `GOMAXPROCS` Ms run Go code, plus a few runtime threads (sysmon, GC workers). Only `GOMAXPROCS` goroutines execute at a time.
- **syscall**: 204 threads for 200 blocked goroutines, about 1 OS thread per blocked goroutine. When an M blocks in the kernel, the runtime hands its P to another M and creates threads as needed. `GOMAXPROCS` does **not** cap this; `debug.SetMaxThreads` (default 10,000) does.
- **threads.c**: `os_threads` = N + 1 = 10,001 kernel tasks. On this shared VM each `pthread_create()` cost ~320 µs (stack `mmap` + `clone3` + guard page), vs ~24 µs per goroutine *including* its first run, and RSS grew by ~83 MiB vs ~26 MiB.
- **`ps -L`**: the blocked threads are in state `S` with `wchan` `pipe_read` / `anon_pipe_read`. This is the kernel's view of the same goroutines.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `syscall` mode shows few threads | used `os.File.Read`, which goes through the netpoller for pipes | use `syscall.Read` on a raw fd (as in the code) |
| `pthread_create: Resource temporarily unavailable` | `ulimit -u` or `pids.max` of your cgroup | lower N or raise the limit |
| `cpu` mode freezes the shell | `GOMAXPROCS` = all CPUs, all spinning | it exits after 1 s; or use `GOMAXPROCS=2` |
| `go: command not found` | Go not installed | `sudo apt install golang-go` |

## Extension task

Make the syscall mode **not** create threads, by changing only how the pipe is read: put the fd in non-blocking mode and read it through `os.NewFile`, so the runtime's netpoller (epoll) parks the goroutines. Show the thread count before and after, and find the epoll fd in `/proc/<pid>/fd`.

Solution: [`solution/netpoll.go`](solution/netpoll.go).
