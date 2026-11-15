# 02 — Processes & Threads: quiz

> Persian: [`quiz.fa.md`](quiz.fa.md) · 14 questions (6 conceptual, 4 read-code/output, 4 debug/design) + 3 oral-exam questions · Answers at the end.

## Part A — Conceptual

**Q1.** In Linux, what kernel object represents a thread, and what object represents a process? Which `clone()` flag makes a new task a thread of the caller's process rather than a new process, and which other flags must come with it?

**Q2.** `fork()` of a process with 4 GiB RSS takes a few milliseconds, not seconds. Why? What work does it still do that grows with the process size? How is `vfork()` different?

**Q3.** After a successful `execve()`, say for each item whether it is kept or lost: (a) PID, (b) PPID, (c) fd 4 opened with `O_CLOEXEC`, (d) fd 5 opened without it, (e) a `SIGINT` handler installed with `sigaction`, (f) `SIGINT` set to `SIG_IGN`, (g) nice value, (h) the other 7 threads of the process.

**Q4.** What is a zombie, and what is an orphan? Which kernel function makes a task a zombie, and which call removes it? When is a child reaped without the parent calling `wait()`?

**Q5.** List the Linux scheduling classes in priority order and the user-space policies that map to each. Why does a busy `SCHED_FIFO` task on CPU 3 not freeze the fair tasks on CPU 3 completely on v6.18?

**Q6.** Under EEVDF, define lag, eligibility and virtual deadline. Task A has `nice 0` and the default slice; task B has `nice 0` and a 0.3 ms slice. Both are CPU-bound on one CPU. Which one gets more CPU time in the long run, and which one gets the CPU sooner after waking?

## Part B — Read the code / output

**Q7.** From `__schedule()` (`kernel/sched/core.c`, v6.18.63):

```c
	switch_count = &prev->nivcsw;
	/* ... */
	prev_state = READ_ONCE(prev->__state);
	if (sched_mode == SM_IDLE) {
		/* ... */
	} else if (!preempt && prev_state) {
		try_to_block_task(rq, prev, &prev_state,
				  !task_is_blocked(prev));
		switch_count = &prev->nvcsw;
	}
```

A task calls `read()` on an empty pipe. Another task is CPU-bound and gets preempted by a wakeup. For each one: which branch runs, which counter is incremented, and which line of `/proc/<pid>/status` shows it?

**Q8.** From `copy_mm()` (`kernel/fork.c`):

```c
	oldmm = current->mm;
	if (!oldmm)
		return 0;

	if (clone_flags & CLONE_VM) {
		mmget(oldmm);
		mm = oldmm;
	} else {
		mm = dup_mm(tsk, current->mm);
		if (!mm)
			return -ENOMEM;
	}
```

(a) When is `current->mm` NULL, and what does the new task run on in that case? (b) What does `mmget()` change, and why is it needed? (c) Which of `fork()`, `vfork()`, `pthread_create()` take the `CLONE_VM` branch?

**Q9.** Lab 02.1 under `strace -f` (real output, trimmed):

```text
$ strace -f -e trace=pipe2,clone,clone3,dup2,execve,wait4,exit_group ./fep >/dev/null
execve("./fep", ["./fep"], 0x7ffcde0c5fe8 /* 17 vars */) = 0
pipe2([3, 4], O_CLOEXEC)                = 0
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7ffb68ecea10) = 4284
[pid  4284] dup2(4, 1)                  = 1
[pid  4284] execve("/usr/local/sbin/ls", ["ls", "-l", "/proc/self/fd"], 0x7fff1e5aae98 /* 17 vars */) = -1 ENOENT (No such file or directory)
...
[pid  4284] execve("/usr/bin/ls", ["ls", "-l", "/proc/self/fd"], 0x7fff1e5aae98 /* 17 vars */) = 0
[pid  4284] exit_group(0)               = ?
[pid  4284] +++ exited with 0 +++
--- SIGCHLD {si_signo=SIGCHLD, si_code=CLD_EXITED, si_pid=4284, si_uid=1000, si_status=0, si_utime=0, si_stime=0} ---
wait4(4284, [{WIFEXITED(s) && WEXITSTATUS(s) == 0}], 0, NULL) = 4284
exit_group(0)                           = ?
+++ exited with 0 +++
```

Explain each line: why `clone` and not `fork`, why `dup2` happens in the child, which fds the exec'd `ls` has, and why the parent's `read` returns 0 at the end.

**Q10.** Lab 02.3 on the 8-vCPU VM (real medians):

```text
== same: median round_trip 2717 ns over 5 runs     (both tasks on CPU 0, 200 000 round trips)
== split: median round_trip 195549 ns over 5 runs  (CPU 0 and CPU 1, 20 000 round trips)
== free: median round_trip 20619 ns over 5 runs    (no pinning)
```

Why is `split` (two CPUs) slower than `same` (one CPU), although `same` needs two full context switches per round trip? What would you expect on bare metal with `idle=poll`?

## Part C — Debug / design

**Q11.** This program hangs forever after printing the child's output. Find the bug and fix it.

```c
int fds[2];
pipe(fds);
if (fork() == 0) {
    dup2(fds[1], 1);
    execlp("ls", "ls", NULL);
    _exit(127);
}
char buf[4096];
ssize_t n;
while ((n = read(fds[0], buf, sizeof buf)) > 0)
    write(1, buf, n);
wait(NULL);
```

**Q12.** A Go service on a 16-core box shows `Threads: 2400` in `/proc/<pid>/status`, while `runtime.NumGoroutine()` is 3000 and `GOMAXPROCS` is 16. Give two likely causes, how you would confirm each with `/proc` or a tracer, and a fix.

**Q13.** You run a latency-sensitive request handler next to CPU-heavy batch jobs on the same 8-CPU host (kernel 6.18). Compare these options and say which you would choose: (a) `nice -n 10` the batch jobs, (b) a 0.5 ms EEVDF slice for the handler via `sched_setattr()`, (c) `SCHED_FIFO` for the handler, (d) separate CPU cgroups with `cpu.weight`. Mention one risk for each.

**Q14.** A long-running server forks a worker per request. After a day, `ps` shows 30,000 entries in state `Z` and new `fork()` calls fail with `EAGAIN`. Explain the failure and give two different correct fixes in the server code.

## Oral-exam questions

**O1.** Compare process and thread creation in Linux (`kernel_clone()` with `CLONE_*` flags, one `task_struct`) and OpenBSD (`fork1()` vs `__tfork()`/`thread_fork()`, `struct process` + `struct proc`). What does each design make easy, and what does it make hard?

**O2.** Explain why Linux replaced CFS with EEVDF. What could CFS not express, and what new user-visible knob did EEVDF add?

**O3.** Walk through everything that happens, from user space to the other task running, when task A writes one byte into a pipe on which task B (same CPU) is blocked in `read()`.

---

## Answers

**A1.** Both are `struct task_struct`; there is one per thread. A "process" is the set of tasks with the same `tgid` that share `mm`, `files`, `signal` etc.; the group leader has `pid == tgid`. `CLONE_THREAD` puts the new task in the caller's thread group (same `tgid`, `exit_signal = -1`). `copy_process()` requires `CLONE_SIGHAND` with it, and `CLONE_SIGHAND` requires `CLONE_VM` (`-EINVAL` otherwise, `kernel/fork.c` L1963–1972). In practice glibc also passes `CLONE_FS`, `CLONE_FILES`, `CLONE_SYSVSEM`, `CLONE_SETTLS`, `CLONE_PARENT_SETTID`, `CLONE_CHILD_CLEARTID`.

**A2.** `dup_mm()` copies the VMA tree and page tables but not the data pages; private writable pages are write-protected in both parent and child (copy-on-write), and a page is copied only when one side writes to it. The work that remains proportional to size is walking and copying **page tables** (and refcounting pages); with 4 GiB of 4 KiB pages that is ~8 MiB of PTEs. `vfork()` passes `CLONE_VM | CLONE_VFORK`: no `mm` copy at all, the child runs on the parent's memory and the parent sleeps until the child calls `execve()` or `_exit()`.

**A3.** (a) kept, (b) kept, (c) lost (`do_close_on_exec()`), (d) kept, (e) lost: caught handlers are reset to `SIG_DFL` (`flush_signal_handlers()`), (f) kept: ignored signals stay ignored, (g) kept, (h) lost: `de_thread()` kills them, and if a non-leader called exec it takes over the leader's PID.

**A4.** Zombie: a task that has exited (`exit_state = EXIT_ZOMBIE`, set in `exit_notify()`) whose parent has not collected its status; only the `task_struct` and exit info remain. Orphan: a live task whose parent has exited; `find_new_reaper()` re-parents it to another thread of the same process, else to the nearest `PR_SET_CHILD_SUBREAPER` ancestor, else to the namespace's init. The parent's `wait4()`/`waitid()` → `wait_task_zombie()` → `release_task()` removes it. It is reaped automatically if the parent's `SIGCHLD` action is `SIG_IGN` or has `SA_NOCLDWAIT` (`do_notify_parent()`), and non-leader threads are always autoreaped.

**A5.** stop → dl (`SCHED_DEADLINE`) → rt (`SCHED_FIFO`, `SCHED_RR`) → fair (`SCHED_OTHER`, `SCHED_BATCH`, `SCHED_IDLE`; EEVDF) → ext (`SCHED_EXT`, sched_ext BPF) → idle. A FIFO task outranks fair tasks, but (1) RT throttling limits RT to 950 ms per 1 s and (2) since 6.12 the per-CPU fair server, a `SCHED_DEADLINE` entity with 50 ms runtime per 1000 ms period, runs fair tasks when they are starved. Lab 02.5 measures about 5% for the fair task.

**A6.** `V` = weighted average vruntime of the queue. Lag `= w_i (V − v_i)`: positive means owed service. Eligible ⇔ lag ≥ 0 ⇔ `v_i ≤ V`. Virtual deadline `vd_i = v_i + r_i / w_i` (in weight-scaled time). Long-run share depends only on weight: equal nice ⇒ ~50/50 for A and B. B, with the shorter request, gets earlier deadlines and is picked sooner after it becomes eligible, so it has lower latency, but its turns are shorter and it switches more often.

**A7.** The pipe reader: `anon_pipe_read()` sets `TASK_INTERRUPTIBLE` via `wait_event_interruptible_exclusive()` and calls `schedule()` with `SM_NONE`, so `preempt` is false and `prev_state` is non-zero → `try_to_block_task()` dequeues it and `nvcsw` is incremented → `voluntary_ctxt_switches`. The CPU-bound task is preempted (`SM_PREEMPT`, `preempt` true; also its state is `TASK_RUNNING` = 0) → the branch is skipped, it stays on the run queue, `nivcsw` is incremented → `nonvoluntary_ctxt_switches`.

**A8.** (a) In kernel threads (they have no user address space); `copy_mm()` returns 0 and the thread later runs on a borrowed `active_mm` (lazy TLB in `context_switch()`). (b) It increments `mm->mm_users`, the count of users of the address space, so the `mm` is not torn down while any sharing task still uses it. (c) `vfork()` and `pthread_create()` take it; `fork()` goes to `dup_mm()`.

**A9.** glibc implements `fork()` with the `clone` syscall (`flags=CLONE_CHILD_SETTID|CLONE_CHILD_CLEARTID|SIGCHLD`), so strace prints `clone`. The child calls `dup2(4, 1)` so that fd 1 refers to the pipe's write end; it must happen in the child, after `fork()` and before `execve()`, because the fd table is what survives exec. The pipe was made with `O_CLOEXEC`, so the original fds 3 and 4 disappear at `execve()`; `ls` has 0, 1 (the pipe), 2 and the directory it opens itself. The parent's `read` returns 0 once no write end is left open: the child's fd 1 closed when `ls` exited, and the parent closed its own copy of fd 4 right after `fork()`.

**A10.** In `same`, a round trip is: write → wake the other task on the same CPU (`WF_SYNC`) → the writer blocks in `read` → switch → and back. All in one CPU's caches, no IPIs. In `split`, each wakeup targets another CPU that is usually idle: the waker sends an IPI (or the target exits a halt/`mwait` idle state), and on a VM the target vCPU may itself be descheduled by the host and must be woken by the hypervisor. That wakeup latency dominates. With `idle=poll` on bare metal the other CPU spins instead of halting, and `split` becomes faster than `same`, since no context switch is needed at all.

**A11.** The parent never closes `fds[1]`. `anon_pipe_read()` returns EOF only when `pipe->writers == 0`; the parent itself is a writer, so after `ls` exits the parent blocks in `read()` forever. Fix: `close(fds[1]);` in the parent right after `fork()` (and `close(fds[0]); close(fds[1]);` in the child after `dup2`, or create the pipe with `pipe2(fds, O_CLOEXEC)`).

**A12.** (1) Goroutines blocked in **blocking syscalls** that the netpoller cannot handle: file I/O on slow disks or NFS, pipes/devices read with `syscall.Read`, `flock`, DNS through the cgo resolver. Each holds an M; the runtime creates new Ms for the Ps. Confirm: `cat /proc/<pid>/task/*/stat` (most threads in `S`/`D`), `/proc/<pid>/task/<tid>/wchan` or `stack`, or `bpftrace` on `sys_enter_*` by tid; `GODEBUG=schedtrace=1000`. (2) **cgo** calls or `runtime.LockOSThread()`: a G locked to an M, each cgo call in progress pins a thread. Confirm with a goroutine dump (`SIGQUIT` or pprof `goroutine?debug=2`) showing `cgocall` / `syscall`. Fixes: bound the concurrency of blocking calls with a semaphore/worker pool, use async APIs (netpoller-backed fds, `io_uring` libraries), use the pure-Go DNS resolver (`GODEBUG=netdns=go`), and set `debug.SetMaxThreads` as a safety limit. `GOMAXPROCS` does not limit threads.

**A13.** (a) nice 10 on batch: weight 110 vs 1024, handler gets ~90% when competing; simple, but a wakeup may still wait up to a batch task's slice. Risk: batch throughput drops; does not bound latency. (b) Short slice: earlier virtual deadline, the handler preempts sooner after waking, no share change. Risk: more context switches, still competes on share; 6.6+ only. (c) `SCHED_FIFO`: always runs first on its CPU; best latency. Risk: a bug or load spike starves everything on that CPU (only the fair server's 5% remains), needs privileges. (d) cgroups with `cpu.weight`: isolates groups, survives new batch processes, can combine with `cpuset` to give the handler its own CPUs. Risk: more configuration; weights do not bound latency unless CPUs are partitioned. Typical choice: (d) with dedicated CPUs or a high weight, plus (b) for the handler threads; avoid (c) unless the handler is small, bounded, and tested.

**A14.** The server never reaps its children. Each exited worker stays a zombie holding a PID (and counts against `RLIMIT_NPROC` / the cgroup's `pids.max`), so `fork()` fails with `EAGAIN` when a limit is hit. Fixes: (1) a `SIGCHLD` handler that loops `while (waitpid(-1, &st, WNOHANG) > 0) {}` (signals coalesce, so one signal may mean many children); (2) if exit statuses are not needed, `signal(SIGCHLD, SIG_IGN)` or `sigaction` with `SA_NOCLDWAIT`, so the kernel autoreaps (`do_notify_parent()`); (3) a pidfd per child in the event loop and `waitid(P_PIDFD, ...)` when it becomes readable. Killing the zombies does nothing; killing the parent makes init reap them.

**O1 (outline).** Linux: one object, one path. `kernel_clone()` → `copy_process()`; flags choose per resource. Easy: threads, `vfork`, `posix_spawn`, containers (`CLONE_NEW*`), odd mixes such as sharing files but not memory. Hard: every resource needs refcounting and sharing semantics; many invalid combinations must be rejected; `exec` in a thread group and signals are intricate (`de_thread`). OpenBSD: `struct process` (address space, fds, creds, thread list) and `struct proc` (thread); `fork1()` with a few `FORK_*` flags for processes, `thread_fork()` only for threads; resources reserved before the "cannot fail" part. Easy: clear invariants, simpler auditing (fits OpenBSD's security focus). Hard: no partial sharing, no namespace-style isolation primitives.

**O2 (outline).** CFS picked the smallest vruntime and used heuristics (`sched_latency`, `min_granularity`, wakeup granularity, sleeper credit) to trade latency vs throughput; there was no way for a task to say "I need short, frequent turns" without also asking for more CPU (`nice`), and the heuristics had corner cases. EEVDF has a defined fairness criterion (lag, eligibility) and a separate latency parameter (the request size/slice): virtual deadline = vruntime + slice/weight. New knob: `sched_setattr()` with `sched_runtime` on a fair task (clamped 0.1–100 ms). The old CFS tunables were removed; `base_slice_ns` remains.

**O3 (outline).** A: `write()` → `anon_pipe_write()` → copy into a `pipe_buffer` → `wake_up_interruptible_sync_poll(&pipe->rd_wait)` → `try_to_wake_up(B)`: set B `TASK_RUNNING`, `enqueue_task_fair()` (`place_entity()` restores B's lag), `wakeup_preempt` / `check_preempt_wakeup_fair()` may set `need_resched` on A. A returns from `write()` and enters `read()` on the reply pipe, sleeps (`wait_event_interruptible_exclusive`) → `schedule()` → `__schedule()`: A is dequeued (`nvcsw++`), `pick_next_task()` → fair fast path → `pick_eevdf()` returns B → `trace_sched_switch` → `context_switch()`: different `mm` → `switch_mm_irqs_off()` (CR3 write, PCID), `switch_to()` swaps stacks and registers → B resumes inside `wait_event_*` in `anon_pipe_read()`, re-takes `pipe->mutex`, copies the byte to user space, returns through `syscall_exit_to_user_mode()`.
