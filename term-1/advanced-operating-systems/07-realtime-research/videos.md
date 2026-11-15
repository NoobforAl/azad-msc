# 07 — Videos: Real-Time & Research Topics

All entries were found by search on 2026-11-15, and each watch page was opened to confirm the title, channel, upload date and chapters. Durations come from the YouTube search listing, because the player data was blocked by a bot check. All videos are in English.

**Kernel-version caveat:** `PREEMPT_RT` became selectable in mainline in **v6.12** (autumn 2024). Talks recorded before that describe an out-of-tree patch set; the concepts still hold, but "apply the RT patch" steps no longer apply to our v6.18.63 tree.

| # | Title | Channel | URL | Duration | Uploaded | Level | Why it fits | Watch |
|---|---|---|---|---|---|---|---|---|
| 1 | Kernel Recipes 2024 - Making the kernel suck less! (Steven Rostedt) | Kernel Recipes | <https://www.youtube.com/watch?v=AjFTVxAU3Vg> | 55:33 | 2024-10-01 | Intermediate–Advanced | RT history, priority inheritance, threaded IRQs and lazy preemption, from a PREEMPT_RT maintainer. Recorded around the 6.12 merge | 0:00–17:06 (PI at 12:35, threaded IRQs at 14:25); 29:40–37:50 (preemption models, lazy) |
| 2 | News from PREEMPT_RT - Sebastian Siewior | Linux Plumbers Conference | <https://www.youtube.com/watch?v=8_dxY4C9iug> | 38:15 | 2025-12-18 | Advanced | The only fully post-merge RT talk here: what changed after 6.12 (local bottom-half locks, futex private hash). Matches `PREEMPT_RT_NEEDS_BH_LOCK` in our `Kconfig.preempt` | whole talk |
| 3 | Real-Time Linux: What Is Next? (Bristot de Oliveira, Gleixner, Siewior, Stewart) | The Linux Foundation | <https://www.youtube.com/watch?v=x_jBs-FSc1I> | 47:19 | 2024-04-26 | Intermediate | The RT maintainers on why the merge took 20 years and what "real-time" means for Linux. **Pre-merge** | whole talk |
| 4 | Using SCHED_DEADLINE (Steven Rostedt, Red Hat) | The Linux Foundation | <https://www.youtube.com/watch?v=TDR-rgWopgM> | 50:08 | 2017-04-04 | Intermediate | EDF + CBS in Linux, with RMS, Dhall's effect and WCET: links note 02 to `kernel/sched/deadline.c`. **Old (2017)**; API unchanged | 9:17–32:47 |
| 5 | Lecture 12 - ECE 350 - Real-time Operating Systems - 10/26/2020 | Seyed Majid Zahedi | <https://www.youtube.com/watch?v=Kmx1YjZBnTk> | 1:25:36 | 2020-10-26 | Intermediate | University lecture (Waterloo ECE 350): RT task model, RMS, EDF, schedulability tests | 55:52–end (RMS at 66:42, EDF at 76:26) |
| 6 | Introduction to RTOS Part 11 - Priority Inversion \| Digi-Key Electronics | DigiKey | <https://www.youtube.com/watch?v=C2xKhxROmhA> | 12:35 | 2021-03-29 | Beginner–Intermediate | Bounded vs unbounded inversion and inheritance, demonstrated on FreeRTOS. Same scenario as lab 02 | whole video |
| 6b | L19 08 Mars Pathfinder Incident | Phil Koopman | <https://www.youtube.com/watch?v=pr9J0pxHI6c> | 2:08 | 2021-07-27 | Beginner | Short CMU lecture clip on the Pathfinder priority-inversion bug (note 03) | whole clip |
| 7 | Linux Sandboxing with Landlock - Mickaël Salaün, Microsoft | The Linux Foundation | <https://www.youtube.com/watch?v=d85TDpv8L9U> | 31:49 | 2024-10-04 | Intermediate | The Landlock author on unprivileged self-sandboxing: design, ABI versions, adoption (lab 04) | 7:41–19:25 |
| 8 | Linux's SECCOMP, its usecases and problems (Miroslav Franc) | SUSE Labs | <https://www.youtube.com/watch?v=2S2tgDrFCiU> | 31:51 | 2024-06-10 | Intermediate | seccomp API, history, uses and limits (no pointer dereference, new-syscall drift) (lab 03) | whole talk |
| 9 | Hackfest 2015: Theo de Raadt presented "Pledge: A new security technology in openbsd" | Hackfest Communication | <https://www.youtube.com/watch?v=F_7S1eqKsFk> | 53:53 | 2015-11-23 | Intermediate | pledge's design by its author, compared with systrace and Capsicum. **Old (2015)**: promise names have changed since; check `pledge.2` in the checkout | 8:07–36:52 |
| 10 | Unveil in OpenBSD … by Bob Beck | BSDCan | <https://www.youtube.com/watch?v=gvmGfpMgny4> | 55:20 | 2019-06-21 | Intermediate | unveil semantics, pledge vs unveil, Chrome case study. **Old (2019)** | 1:33–15:58; 29:31–35:00 |
| 11 | [Research] Show and Tell: How to Read an Academic Paper Using Keshav's Approach | Lighton Phiri | <https://www.youtube.com/watch?v=Cq_jg4iQ4lk> | 13:58 | 2020-06-05 | Beginner | Keshav's three-pass method (note 06, lab 05). General, not systems-specific | 7:10–end |

Chapters are the ones shown on each watch page; some may be YouTube's automatic chapters.

## Backups (found in search, page partly checked)

- *SCHED_DEADLINE: It's Alive!* — Juri Lelli, ARM (The Linux Foundation, 49:33, 2017-02-28; page opened, has chapters): <https://www.youtube.com/watch?v=wzrcWNIneWY>
- *Update on Landlock: Scoping, …* — Mickaël Salaün & Günther Noack (The Linux Foundation, 38:05, 2026-11-02; page opened): <https://www.youtube.com/watch?v=uSs6FQYCawY>. Newest Landlock status, closest to ABI 7 in our tree.

## Not found / not verified

- No confirmed talk on *reading systems papers* specifically (OSDI/SOSP style). Use the written source instead: S. Keshav, "How to Read a Paper", ACM SIGCOMM CCR 37(3), 2007, doi:10.1145/1273445.1273458.
- No substantive conference talk on Mars Pathfinder. The primary written account is Glenn Reeves' email "What really happened on Mars?" (1997). Text, not video.
- Sebastian Siewior's Kernel Recipes 2024 talk "PREEMPT_RT over the years": the schedule page exists, but no video link was found.
