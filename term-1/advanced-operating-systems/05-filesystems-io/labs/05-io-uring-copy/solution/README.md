# Lab 05.5 — Solution to the extension (SQPOLL + registered buffers)

```bash
gcc -Wall -Wextra -O2 -o copy_uring_sqpoll copy_uring_sqpoll.c -luring    # zero warnings
strace -c -f ./copy_uring_sqpoll src.bin dst.bin 131072 8; cmp src.bin dst.bin
perf stat -e task-clock,context-switches -- ./copy_uring_sqpoll src.bin dst.bin 131072 8
```

Real output (aos-lab, Linux 6.18.63, 2026-11-15, warm source):

```text
copy_uring_sqpoll: 512 MiB, 0.356 s, 1438 MiB/s, 978 blocking waits
% time     seconds  usecs/call     calls    errors syscall
 95.82    0.263645         269       978           io_uring_enter
  0.25    0.000698         698         1           io_uring_setup
  0.10    0.000274         274         1           io_uring_register
100.00    0.275141         262      1049         1 total
identical

copy_uring_sqpoll: 512 MiB, 0.404 s, 1268 MiB/s, 2377 blocking waits
            641.89 msec task-clock                       #    1.570 CPUs utilized
              2852      context-switches                 #    4.443 K/sec
       0.408826362 seconds time elapsed
```

Interpretation:

- **Submission is free:** with `IORING_SETUP_SQPOLL`, a kernel thread (`iou-sqp-<pid>`) polls the SQ tail. `io_uring_submit()` only writes the ring and calls `io_uring_enter()` if the poller has gone to sleep (`IORING_SQ_NEED_WAKEUP`); here it never did, so **none** of the 978 enters were for submission.
- **Waiting is not free:** every `io_uring_enter()` that remains is `io_uring_wait_cqe()` sleeping because the next completion had not arrived yet (978 under strace, 2 377 under perf: the number depends on timing). To reach truly zero syscalls, the application must spin on the CQ instead of sleeping, which burns a CPU.
- **CPU cost:** 642 ms task-clock for a 0.41 s run = 1.57 CPUs: the SQ poller spins while there is work (and for `sq_thread_idle` = 2 s after). It is faster (1 268–1 438 MiB/s vs ~1 050 MiB/s for the plain version) because it trades a dedicated core for latency.
- **Registered buffers** (`READ_FIXED`/`WRITE_FIXED`) skip pinning and mapping the user pages on every request; with 128 KiB blocks and buffered I/O the effect is small next to the memcpy, but it matters for `O_DIRECT` small-block workloads.
- SQPOLL needs no special privilege on modern kernels, but it costs a CPU per ring: use it only when that core would otherwise be spent in syscalls.
