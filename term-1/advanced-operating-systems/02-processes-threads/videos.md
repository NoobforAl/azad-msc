# 02 — Processes & Threads: videos

All URLs were checked on 2026-11-15 through YouTube's oEmbed endpoint (`https://www.youtube.com/oembed?url=...`), which returns the exact title and channel. Each source page is named. oEmbed does not report length, so a duration appears only where another source states it. Otherwise it says `duration: not verified`. Open the video to see the real length.

| # | Title | Channel | Duration | Level | For |
|---|---|---|---|---|---|
| 1 | 6.S081 Fall 2020 Lecture 3: OS Organization and System Calls | David Morejon (MIT 6.S081 recordings) | not verified | Beginner | notes 01, 02; lab 02.1 |
| 2 | 6.S081 Fall 2020 Lecture 11: Thread Switching | David Morejon (MIT 6.S081 recordings) | not verified | Intermediate | lesson §2.8, notes 04, 05; lab 02.3 |
| 3 | GopherCon 2018: The Scheduler Saga - Kavya Joshi | Gopher Academy | ~31 min (Class Central listing) | Intermediate | note 05; lab 02.6 |
| 4 | Give me 15 minutes and I'll change your view of Linux tracing | Brendan Gregg | 15–18 min (author's blog) | Intermediate | lab 02.4 |
| 5 | Use the slice duration of fair task in CPU selection - Vincent Guittot (OSPM26) | OSPM summit | not verified | Advanced | note 07; lab 02.5 |
| 6 | Evolving sched_ext - Changwoo Min and Gavin Guo | OSPM summit | not verified | Advanced | note 06 |

## 1. MIT 6.S081 Lecture 3: OS Organization and System Calls

- **URL:** https://youtu.be/o44d---Dk4o (linked as "video" for LEC 3 on the official schedule, https://pdos.csail.mit.edu/6.828/2020/schedule.html)
- **Channel:** David Morejon · **Language:** English · **Level:** Beginner · **Duration:** not verified
- **Why:** this lecture covers the kernel/user boundary in xv6 and how the first process starts, and gives intuition for "a process = address space + kernel state". xv6's `fork()` (`kernel/proc.c`) is a 40-line version of what `copy_process()` does, so watch this lecture before notes 01 and 02.
- **Watch:** full video.

## 2. MIT 6.S081 Lecture 11: Thread Switching

- **URL:** https://youtu.be/vsgrTHY5tkg (LEC 11 on the same official schedule)
- **Channel:** David Morejon · **Language:** English · **Level:** Intermediate · **Duration:** not verified
- **Why:** Robert Morris steps through `swtch.S` and `sched()` in xv6 under gdb. It is the clearest picture of "save registers, switch stack, return in another thread", which Linux does in `context_switch()` → `switch_to()`. Watch it before lab 02.3.
- **Note:** xv6 switches through a separate per-CPU scheduler thread, and Linux does not (`__schedule()` runs in the context of `prev`). The course notes (`l-threads.txt`) point out this difference.
- **Watch:** full video.

## 3. The Scheduler Saga (GopherCon 2018)

- **URL:** https://www.youtube.com/watch?v=YHRO5WQGh0k
- **Channel:** Gopher Academy · **Language:** English · **Level:** Intermediate · **Duration:** ~31 min (Class Central listing, not checked on YouTube)
- **Why:** it builds Go's G/M/P scheduler step by step: run queues, work stealing, handoff of the P when a goroutine blocks in a syscall. That handoff is exactly the thread growth lab 02.6 measures in `syscall` mode. Note 05 covers the same material.
- **VERSION-DEPENDENT:** the talk predates Go 1.14. It describes only cooperative preemption, and Go has used asynchronous preemption since 1.14.
- **Watch:** full video.

## 4. Give me 15 minutes and I'll change your view of Linux tracing

- **URL:** https://www.youtube.com/watch?v=GsMs3n8CB6g (linked from https://www.brendangregg.com/blog/2016-12-27/linux-tracing-in-15-minutes.html)
- **Channel:** Brendan Gregg · **Language:** English · **Level:** Intermediate · **Duration:** 15–18 min ("My 15 (18) minute demo", per the author's blog)
- **Why:** a live demo that moves from ftrace to perf to bcc/BPF on a real kernel. It shows the same workflow as lab 02.4 (`perf sched`, tracepoints, `runqlat`-style histograms).
- **OUTDATED in details:** it is from 2016 (Linux 4.x). The tools still exist, but bpftrace has replaced many of the hand-written bcc scripts, and `bpftrace` syntax is what the labs use.
- **Watch:** full video.

## 5. Use the slice duration of fair task in CPU selection (OSPM 2026)

- **URL:** https://youtu.be/fsOy3M_HkVM (linked from LWN's OSPM 2026 coverage, https://lwn.net/Articles/1078696/)
- **Channel:** OSPM summit · **Language:** English · **Level:** Advanced · **Duration:** not verified
- **Why:** an EEVDF maintainer (Vincent Guittot) talks about the per-task **slice**, the knob that lab 02.5 sets with `sched_setattr()`. He covers where EEVDF fails to preempt and how the slice could steer CPU selection. It shows the current development edge beyond v6.18.
- **VERSION-DEPENDENT:** the talk discusses proposals that may not be in v6.18.63. Check them against `kernel/sched/fair.c` before you assume anything is merged.
- **Watch:** full video. Read the LWN summary first.

## 6. Evolving sched_ext (OSPM 2026)

- **URL:** https://youtu.be/VrsRUlAttFo (same LWN article)
- **Channel:** OSPM summit · **Language:** English · **Level:** Advanced · **Duration:** not verified
- **Why:** sched_ext is the `ext` class in note 06's class table (`kernel/sched/ext.c`). This talk explains how BPF schedulers such as LAVD are built and used, so you can see why a pluggable class sits between fair and idle.
- **Watch:** full video.

## Written sources (read alongside)

- LWN, "An EEVDF CPU scheduler for Linux": https://lwn.net/Articles/925371/ (cited by `sched-eevdf.rst`)
- LWN, "Completing the EEVDF scheduler": https://lwn.net/Articles/969062/ (cited by `sched-eevdf.rst`)
- `Documentation/scheduler/sched-eevdf.rst` in the local checkout (v6.18.63)
- LWN OSPM 2026 coverage with all video links: https://lwn.net/Articles/1078696/

Not listed because no verified video was found: a dedicated EEVDF talk by Peter Zijlstra, a Berkeley CS162 scheduling lecture on an official channel, and the CMU 15-213 ECF/processes lectures. The CMU videos are linked from the course schedule pages, not from YouTube.
