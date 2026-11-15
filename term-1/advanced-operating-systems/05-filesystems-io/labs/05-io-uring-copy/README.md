# Lab 05.5 — `read()`/`write()` loop vs `io_uring`

**Goal:** copy the same 512 MiB file with a classic `read()`/`write()` loop and with io_uring (liburing), then compare syscall counts, time, CPU, and *where in the kernel* each operation ran.

Runs on: the lab VM (`liburing-dev` installed), `~/work/05-filesystems-io/labs/05-io-uring-copy`. `sudo` only for the bpftrace step. Disk use: 1 GiB. Time: ~30 min.

## Steps

```bash
cd ~/work/05-filesystems-io/labs/05-io-uring-copy
gcc -Wall -Wextra -O2 -o copy_rw copy_rw.c                     # zero warnings
gcc -Wall -Wextra -O2 -o copy_uring copy_uring.c -luring       # zero warnings; -luring last
dd if=/dev/urandom of=src.bin bs=1M count=512 status=none; sync src.bin
./copy_rw src.bin dst.bin && cmp src.bin dst.bin
./copy_uring src.bin dst.bin 131072 8 && cmp src.bin dst.bin
bash run.sh      # 1: perf stat on a cold source  2: strace -c  3: io_uring tracepoints
```

## Code

- [`copy_rw.c`](copy_rw.c): `read(128 KiB)` → `write()` loop (handles short writes). Two syscalls per block.
- [`copy_uring.c`](copy_uring.c): for each of `qd` buffers, a `READ` SQE linked (`IOSQE_IO_LINK`) to a `WRITE` SQE of the same buffer and offset; `io_uring_submit_and_wait(2·k)` submits all pairs **and** waits for all completions in one `io_uring_enter()`. Each CQE's `res` is checked against the expected length (a short read cancels the linked write with `-ECANCELED`).
- [`run.sh`](run.sh): evicts `src.bin` only (`dd iflag=nocache count=0`) before the cold runs; `perf stat -e task-clock,context-switches,cpu-migrations`; `strace -c -f`; bpftrace on `io_uring:io_uring_submit_req`, `io_uring_queue_async_work`, `io_uring_complete`.

## Expected output

Real run, `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, perf 6.8), 2026-11-15. Shared 8-vCPU guest; the "cold" source is probably still in the Windows host's file cache, so both copies run at memory-ish speed.

```text
$ bash run.sh
== 1. cold source, wall time + software counters
copy_rw:    512 MiB, block 128 KiB, 8193 read/write syscalls, 0.438 s, 1168 MiB/s
            211.11 msec task-clock                       #    0.479 CPUs utilized
                68      context-switches                 #  322.105 /sec
       0.440743110 seconds time elapsed
       0.053150000 seconds user
       0.159452000 seconds sys
  cmp: identical
copy_uring: 512 MiB, block 128 KiB, qd 8, 512 io_uring_enter calls, 0.487 s, 1052 MiB/s
            410.58 msec task-clock                       #    0.838 CPUs utilized
              2066      context-switches                 #    5.032 K/sec
       0.489727894 seconds time elapsed
       0.433924000 seconds user
       0.000000000 seconds sys
  cmp: identical

== 2. syscall counts (strace -c -f), warm source
  % time     seconds  usecs/call     calls    errors syscall
    0.00    0.000000           0      4098           read
    0.00    0.000000           0      4097           write
  100.00    0.000000           0      8233         2 total
  % time     seconds  usecs/call     calls    errors syscall
   99.61    0.236119         461       512           io_uring_enter
    0.00    0.000000           0         1           io_uring_setup
  100.00    0.237047         407       582         2 total

== 3. who did the work? io_uring tracepoints during a cold copy
copy_uring: 512 MiB, block 128 KiB, qd 8, 512 io_uring_enter calls, 0.511 s, 1001 MiB/s

@completed: 8192
@punted_to_io_wq[23]: 4096
@submitted[23]: 4096
@submitted[22]: 4096
(opcode numbers: see enum io_uring_op in include/uapi/linux/io_uring.h; 22=READ 23=WRITE)
```

(`perf stat` header lines and the loader's `pread64`/`mmap` rows of `strace` are trimmed with no number changed.)

## What to observe

- **Syscalls: 8 193 vs 512.** 512 MiB / 128 KiB = 4 096 blocks. The loop does 4 096 `read` + 4 096 `write` + 1 final `read` returning 0. io_uring submits 8 pairs per `io_uring_enter()`: 4 096 / 8 = 512. 16× fewer syscalls.
- **But io_uring was *not* faster here** (0.487 s vs 0.438 s), and it used **twice the CPU** (411 vs 211 ms task-clock) with **30× the context switches** (2 066 vs 68). The tracepoints explain why:
  - all 4 096 **reads** (opcode 22) completed without help: ext4 has `FOP_BUFFER_RASYNC`, so a page-cache miss uses the async buffered-read callback instead of a thread;
  - all 4 096 **writes** (opcode 23) were **punted to io-wq**: the first, non-blocking attempt (`IOCB_NOWAIT`) of a buffered ext4 write returns `-EAGAIN`, so each one is handed to an `iou-wrk-<pid>` kernel thread. Each hand-off is a wake-up and a context switch.
- `perf stat` charges the io-wq workers' CPU time to the process (they are its threads), which is why `sys` shows 0 for `copy_uring` while `user + workers` is 0.43 s.
- For a copy of large blocks the real work is two memcpys per byte (page cache → user → page cache); saving 7 681 syscalls of ~1 µs each saves less than 10 ms. io_uring pays off with many **small** operations, deep queues on fast devices (`O_DIRECT` + `IORING_SETUP_IOPOLL`), and network servers. `copy_file_range(2)` would avoid the user-space copy entirely.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `undefined reference to io_uring_queue_init` | `-luring` before the source file | put `-luring` at the end of the gcc command |
| `write failed: res=-125` | `-ECANCELED`: the linked read was short, so the write was cancelled | handle short reads (only happens at EOF or on errors here) |
| `io_uring_setup: Operation not permitted` | `kernel.io_uring_disabled = 2`, a container/seccomp policy, or `io_uring_group` | `sysctl kernel.io_uring_disabled`; run on the VM, not in a restricted container |
| bpftrace `@punted_to_io_wq` empty | the comm filter: workers are named `iou-wrk-*` | the script counts that tracepoint without a comm filter |
| io_uring "slower than expected" | buffered writes punted to io-wq; memcpy-bound workload | measure, don't assume; see above |

## Extension task

Add `IORING_SETUP_SQPOLL` and registered buffers (`io_uring_register_buffers()` + `io_uring_prep_read_fixed()`/`write_fixed()`). How many `io_uring_enter()` calls remain, why not zero, and what does the `iou-sqp` thread cost in CPU?

Solution: [`solution/copy_uring_sqpoll.c`](solution/copy_uring_sqpoll.c) and [`solution/README.md`](solution/README.md).
