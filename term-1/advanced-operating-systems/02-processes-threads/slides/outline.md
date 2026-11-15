# 02 · Processes & Threads — slide outlines

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced OS (user = teal, kernel = amber, hardware = violet, data = green).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 17 |
| Lab 02.1 fork-exec-pipe | [`labs/01-fork-exec-pipe.en.html`](labs/01-fork-exec-pipe.en.html) | [`labs/01-fork-exec-pipe.fa.html`](labs/01-fork-exec-pipe.fa.html) | 7 |
| Lab 02.2 clone-flags | [`labs/02-clone-flags.en.html`](labs/02-clone-flags.en.html) | [`labs/02-clone-flags.fa.html`](labs/02-clone-flags.fa.html) | 7 |
| Lab 02.3 ctxsw-pingpong | [`labs/03-ctxsw-pingpong.en.html`](labs/03-ctxsw-pingpong.en.html) | [`labs/03-ctxsw-pingpong.fa.html`](labs/03-ctxsw-pingpong.fa.html) | 7 |
| Lab 02.4 perf-sched-bpftrace | [`labs/04-perf-sched-bpftrace.en.html`](labs/04-perf-sched-bpftrace.en.html) | [`labs/04-perf-sched-bpftrace.fa.html`](labs/04-perf-sched-bpftrace.fa.html) | 7 |
| Lab 02.5 sched-policies | [`labs/05-sched-policies.en.html`](labs/05-sched-policies.en.html) | [`labs/05-sched-policies.fa.html`](labs/05-sched-policies.fa.html) | 7 |
| Lab 02.6 goroutines-vs-threads | [`labs/06-goroutines-vs-threads.en.html`](labs/06-goroutines-vs-threads.en.html) | [`labs/06-goroutines-vs-threads.fa.html`](labs/06-goroutines-vs-threads.fa.html) | 7 |

Open a deck through a local web server so the relative theme path resolves: run `python -m http.server` at the repo root, then open `http://127.0.0.1:8000/term-1/advanced-operating-systems/02-processes-threads/slides/lesson.en.html`. Press `S` for speaker notes. Add `?print-pdf` for PDF export. Lab decks are generated from [`labs.content.py`](labs.content.py) with `python _shared/tools/labdeck.py`; do not edit the HTML by hand.

---

## Lesson deck

## Slide 1 — TITLE
Title: One task_struct per thread, one scheduler for all of them · Fields: placeholders from §3.4

## Slide 2 — SECTION
Eyebrow: Module 02 · Title: Processes & Threads · Why: latency bugs, thread explosions, zombies all come down to fork/exec/wait and the scheduler · Pills: kernel_clone() · EEVDF · context switch

## Slide 3 — AGENDA
task & sharing → fork/exec/wait → class order → EEVDF → switch cost (current = 1)

## Slide 4 — CONCEPT_DIAGRAM
Title: A thread is a task that points at the same objects
Diagram: `assets/task-sharing.svg`: user-space band (role-1), syscall boundary (dashed), three task_structs (role-2), mm/files/signal objects (role-4); the thread's pointers drawn as thick accent arrows
Takeaway: CLONE_VM | CLONE_FILES | CLONE_THREAD share the pointers · Motion: pop

## Slide 5 — CODE_WALKTHROUGH
`linux/kernel/fork.c · copy_mm() · v6.18.63 · L1540`. ① kernel thread ② CLONE_VM → mmget ③ dup_mm → COW. One fragment per region.

## Slide 6 — TERMINAL_DEMO
Real `./cloneflags` output from aos-lab: one row per flag set; only the pthread row has child_tgid=same.

## Slide 7 — FLOW_TIMELINE
bprm_execve → search_binary_handler → begin_new_exec (no return) → de_thread / CLOEXEC → exec_mmap → START_THREAD. Takeaway: kept vs gone.

## Slide 8 — STATE_MACHINE
`assets/states.svg`: R on rq ↔ R on CPU (pick_next / preempt nivcsw++), → S/D (schedule nvcsw++), try_to_wake_up back, → Z (do_exit) → reaped (wait). Current state filled brand.

## Slide 9 — LAYER_STACK
stop · dl (+fair_server 50 ms/1 s) · rt (FIFO/RR 1-99) · fair (EEVDF) · ext (BPF) · idle. Kernel bands = role-2, fair = role-1, ext = role-4, idle = role-3.

## Slide 10 — CODE_WALKTHROUGH
`linux/kernel/sched/core.c · __schedule() · L6858`: nivcsw default → blocking branch → nvcsw. Callouts ①②③.

## Slide 11 — CONCEPT_DIAGRAM
`assets/eevdf.svg`: virtual-time axis, V line, eligible zone, tasks A/B/C with vruntime dot and deadline bar; B (short slice) picked. Callouts: eligibility, vd formula, nice = share / slice = latency.

## Slide 12 — CODE_WALKTHROUGH
`linux/kernel/sched/fair.c · update_deadline() · L1127`: deadline not reached → custom_slice → vd = v + slice/w.

## Slide 13 — TERMINAL_DEMO
Real `run.sh` medians (same / split / free) from aos-lab, with the shared-VM caveat in the caption.

## Slide 14 — TWO_COLUMN_COMPARE
Linux (task_struct + CLONE_*, classes, EEVDF O(log n)) vs OpenBSD (process + proc, fork1/thread_fork, one scheduler, 32 queues ffs O(1)).

## Slide 15 — QUIZ
Which counter goes up when a task blocks in read() on an empty pipe? A nivcsw · B nvcsw · C neither · D both.

## Slide 16 — QUIZ answer (DEFINITION)
Answer B; quote: wait_event sets TASK_INTERRUPTIBLE, __schedule dequeues and increments nvcsw. Source: core.c L6874–6883, pipe.c L388.

## Slide 17 — SUMMARY
① task_struct / tgid / mm ② fork/clone share-or-copy, exec replaces the program ③ class order + EEVDF (weight = share, slice = latency). Next: Module 03.

---

## Lab decks (generated)

Each lab deck has the same 7 slides from `labs.content.py`: Goal (SECTION) → Setup (BENTO, 4 role cards) → Steps (TERMINAL_DEMO, the README commands) → Expected output (TERMINAL_DEMO, real aos-lab output, `captured=` caption) → What to observe (SUMMARY list) → Common pitfalls (symptom → fix) → Extension task (no solution).

| Lab | Setup cards | Expected output shown |
|---|---|---|
| 02.1 | user: fep.c · kernel: fork/exec · data: pipe · hardware: /proc | fd table after exec, zombie before/after waitpid |
| 02.2 | user: clone() · kernel: copy_process · data: mm/files/fs · hardware: futex wait | cloneflags table |
| 02.3 | user: two processes · kernel: pipe wakeups · hardware: CPU 0/1 pinning · data: medians | run.sh medians |
| 02.4 | kernel: sched_switch · user: stress-ng + pingpong · data: perf.data · hardware: CPU 2 | perf sched latency + bpftrace split |
| 02.5 | kernel: classes · user: share.c / slice.c · hardware: CPU 3 · data: weight table | nice shares, FIFO vs fair server, slice clamp |
| 02.6 | user: goroutines · kernel: tasks in /proc/<pid>/task · data: VmRSS · hardware: GOMAXPROCS | thread counts per mode |
