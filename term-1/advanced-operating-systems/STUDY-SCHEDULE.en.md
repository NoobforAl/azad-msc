# Study schedule — Advanced Operating Systems

Two plans over the same material: **10-week relaxed**, which covers everything, and **4-week intensive**, which follows the core path. Both assume **60–90 min a day**. Each day has one deliverable: something you produce or run, not just read.

The **Day** column means *study day*. If you skip a day, pick up where you stopped; don't skip ahead.

## How the budget works

| Module | Folder | Notes | Labs | Full hours (PLAN) | 10-week | 4-week core |
|---|---|---|---|---|---|---|
| 00 Setup | `00-setup/` | guide | 3 | 4 | W1 | D1–2 |
| 01 Architecture & Kernel Structure | `01-architecture/` | 6 | 5 | 13 | W1–W2 | D3–6 |
| 02 Processes & Threads | `02-processes-threads/` | 8 | 6 | 16 | W2–W3 | D7–10 |
| 03 Concurrency & Synchronization | `03-concurrency/` | 10 | 6 | 18 | W4–W5 | D11–14 |
| 04 Memory Management | `04-memory/` | 10 | 6 | 18 | W5–W6 | D15–18 |
| 05 File Systems & I/O | `05-filesystems-io/` | 9 | 6 | 16 | W7–W8 | D19–22 |
| 06 Distributed OS & Virtualization | `06-distributed-virtualization/` | 8 | 5 | 14 | W8–W9 | D23–25 |
| 07 Real-Time & Research | `07-realtime-research/` | 6 | 5 | 11 | W10 | D26–27 |
| Review | `CHEATSHEET.*`, all `quiz.*` | — | — | — | W10 | D28 |

- **10-week:** 70 days × 60–90 min ≈ 70–105 h. That fits the ~110 h plan only if you watch videos at 1.25× and skip some extension tasks. Extensions are marked *(ext)*; do them if you're ahead.
- **4-week:** 28 days × 90 min ≈ 42 h. It covers each module's lesson, the notes marked ★ and 2–3 labs. Everything else is the "second pass" list at the end.

**Daily rhythm (both plans):**
1. **10 min:** re-read yesterday's exam-style key points.
2. **50–70 min:** the day's task.
3. **5–10 min:** write 3 lines in your own notebook: what you ran, what surprised you, one open question.

**Where the labs run:**
- Labs that need root, a custom kernel, cgroups that may OOM, or crash tests run **in the VM** (`00-setup`). Their README carries a "VM only" banner.
- Before every VM session, check `uname -r` and roll back to the snapshot if something is off.

---

## 10-week relaxed plan (everything)

### Week 1 — Setup + Architecture I
| Day | Task | Deliverable |
|---|---|---|
| 1 | `00-setup/guide.en.md` §1–3; lab 00.1 (create the VM; on Windows use `create-vm-virtualbox.ps1`) | VM answers `ssh`, snapshot `fresh` exists |
| 2 | Lab 00.2 install + `verify-tools.sh` | exit code 0 (only the RT and `/dev/kvm` WARNs) |
| 3 | Lab 00.3 build v6.18.63 (or the mainline .deb route in lab 00.1's README) | `uname -r` shows 6.18.63 |
| 4 | `00-setup/guide` §4 (ctags/cscope/`cite.sh`) + M01 `lesson.en.md` | `cite.sh linux arch/x86/entry/syscall_64.c do_syscall_64` works |
| 5 | M01 notes 01 kernel types, 02 privilege rings/CPL | one-page table: monolithic vs micro vs hybrid |
| 6 | M01 lab 01 `strace-map` | your own syscall → kernel-function table for `cat` |
| 7 | Review: M01 quiz Q1–5, rewatch one video from `01-architecture/videos.md` | quiz answers checked |

### Week 2 — Architecture II + Processes I
| Day | Task | Deliverable |
|---|---|---|
| 8 | M01 note 03 interrupts/exceptions/IDT + lab 03 interrupts | IRQ delta table from `/proc/interrupts` |
| 9 | M01 note 04 syscall path + `kernel-walkthrough` §syscall entry | draw `entry_SYSCALL_64 → do_syscall_64 → x64_sys_call` from memory |
| 10 | M01 lab 02 raw syscall + lab 04 syscall cost | vDSO vs real syscall ns/call |
| 11 | M01 notes 05 context switch, 06 source tree map; lab 05 ftrace `vfs_read` *(filtered! see lab README)* | function_graph trace of one `read()` |
| 12 | M01 quiz (all) + oral questions out loud | answers checked; 3 weak spots listed |
| 13 | M02 lesson + note 01 `task_struct` | 10 fields you can explain |
| 14 | M02 note 02 fork/vfork/clone + lab 01 fork-exec-pipe | `/proc/<pid>/{status,maps,fd}` screenshots in your notes |

### Week 3 — Processes & Threads II
| Day | Task | Deliverable |
|---|---|---|
| 15 | M02 note 03 execve/ELF + lab 02 clone flags | table: flag → what is shared |
| 16 | M02 notes 04 states/wait, 05 threads share an `mm` | state diagram from memory |
| 17 | M02 note 06 scheduling classes + walkthrough `__schedule` / `context_switch` | call chain on one page |
| 18 | M02 note 07 **EEVDF** (lag, eligibility, virtual deadline) | work the note's example by hand |
| 19 | M02 lab 03 ctxsw ping-pong + lab 04 `perf sched` / bpftrace | pinned vs unpinned median |
| 20 | M02 lab 05 sched policies (VM) + lab 06 goroutines vs threads; note 08 IPC | `GOMAXPROCS` vs thread count table |
| 21 | M02 quiz + oral questions; OpenBSD `sched_bsd.c` comparison | trade-off table in your own words |

### Week 4 — Concurrency I
| Day | Task | Deliverable |
|---|---|---|
| 22 | M03 lesson + note 01 races/critical sections | — |
| 23 | M03 lab 01 data race → TSan → mutex → atomics | `perf stat` cost of each fix |
| 24 | M03 note 02 atomics & C11 memory model | — |
| 25 | M03 note 03 x86-TSO & barriers + lab 05 store-buffering litmus | count of reordered outcomes |
| 26 | M03 note 04 spinlocks/qspinlock + walkthrough `queued_spin_lock` | — |
| 27 | M03 note 05 mutex optimistic spinning + walkthrough `mutex_lock` → `__mutex_lock_common` | fast path vs slow path on one page |
| 28 | Review: M03 quiz Q1–7 | — |

### Week 5 — Concurrency II + Memory I
| Day | Task | Deliverable |
|---|---|---|
| 29 | M03 note 06 semaphores/condvars + lab 02 producer-consumer | three versions agree on totals |
| 30 | M03 note 07 futex + lab 04 raw futex mutex | `strace -f` shows `FUTEX_WAIT`/`FUTEX_WAKE` only under contention |
| 31 | M03 note 08 RCU (+ OpenBSD SMR) + lab 03 readers-writers | writer-starvation numbers |
| 32 | M03 notes 09 deadlock/lockdep, 10 classic problems + lab 06 deadlock | gdb thread dump showing the cycle |
| 33 | M03 full quiz + oral | — |
| 34 | M04 lesson + note 01 virtual address space | annotated `/proc/self/maps` |
| 35 | M04 note 02 page tables + note 03 TLB/PCID | 4-level walk of one address on paper |

### Week 6 — Memory II
| Day | Task | Deliverable |
|---|---|---|
| 36 | M04 note 04 page fault path + walkthrough `exc_page_fault → handle_mm_fault` | call chain from memory |
| 37 | M04 lab 01 page faults | minor/major counts per mode |
| 38 | M04 note 05 demand paging & COW + lab 02 COW via pagemap | same PFN before, new PFN after write |
| 39 | M04 note 09 mmap + lab 03 mmap shared | — |
| 40 | M04 notes 06 buddy, 07 SLUB + lab 05 slab | `slabtop` before/after |
| 41 | M04 note 08 reclaim/MGLRU + note 10 huge pages/NUMA/OOM; lab 04 TLB/huge pages | ns/access curve, 4k vs THP |
| 42 | M04 lab 06 OOM & thrashing in a cgroup (VM) + quiz | `oom_kill 1` in `memory.events` |

### Week 7 — File Systems & I/O I
| Day | Task | Deliverable |
|---|---|---|
| 43 | M05 lesson + note 01 VFS objects | superblock/inode/dentry/file diagram |
| 44 | M05 notes 02 path lookup, 03 fd tables | — |
| 45 | M05 lab 01 `read()` call chain (filtered ftrace + bpftrace) | `vfs_read → filemap_read` trace |
| 46 | M05 note 04 page cache & writeback + lab 02 page cache | cold vs warm MiB/s |
| 47 | M05 lab 03 fsync & writeback | fsync latency table |
| 48 | M05 notes 05 block layer/blk-mq, 06 I/O schedulers | — |
| 49 | Review: M04 quiz again (spaced repetition), M05 quiz Q1–5 | — |

### Week 8 — File Systems & I/O II + Distributed I
| Day | Task | Deliverable |
|---|---|---|
| 50 | M05 lab 04 I/O schedulers with fio | IOPS/latency per scheduler |
| 51 | M05 note 08 io_uring + lab 05 io_uring copy | syscall counts read() vs io_uring |
| 52 | M05 note 07 journaling + lab 06 ext4 crash (VM, dm-flakey) | fsync'd file survives, unsynced one doesn't |
| 53 | M05 note 09 drivers/char devices + full quiz | — |
| 54 | M06 lesson + notes 01 RPC semantics, 02 Lamport/vector clocks | — |
| 55 | M06 lab 01 Lamport & vector clocks | clock-condition check passes |
| 56 | M06 note 03 clock sync + lab 02 RPC idempotency | balance correct under retries |

### Week 9 — Distributed & Virtualization II
| Day | Task | Deliverable |
|---|---|---|
| 57 | M06 notes 04 distributed deadlock/snapshots, 05 fault tolerance | — |
| 58 | M06 note 06 hypervisors (VT-x, EPT) + note 07 KVM | — |
| 59 | M06 note 08 namespaces + cgroups v2 + walkthrough `nsproxy.c`, `cgroup.c` | — |
| 60 | M06 lab 03 mini container (VM) | PID 1 inside, `pids.max` enforced |
| 61 | M06 lab 04 KVM client (needs real `/dev/kvm`) + lab 05 VM-exit cost | `cpuid` exit cost vs syscall |
| 62 | M06 quiz + oral | — |
| 63 | Spaced review: M01–M03 quizzes, wrong answers only | — |

### Week 10 — Real-Time & Research + final review
| Day | Task | Deliverable |
|---|---|---|
| 64 | M07 lesson + notes 01 hard/soft RT, 02 RMS/EDF/`SCHED_DEADLINE` | — |
| 65 | M07 note 03 priority inversion + lab 02 priority inversion | H's wait time: `none` vs `inherit` |
| 66 | M07 note 04 `PREEMPT_RT` + lab 01 cyclictest (RT kernel: lab 00.3 `--rt`) | latency histogram |
| 67 | M07 note 05 seccomp/LSM/Landlock + labs 03, 04 | sandbox kills / EACCES as expected |
| 68 | M07 note 06 reading papers + lab 05 paper review (1 paper) | 1-page review |
| 69 | `CHEATSHEET.en.md` end to end; redo every oral-exam question out loud | — |
| 70 | Mock exam: 2 random quizzes, timed (60 min), no notes | score + weak list |

---

## 4-week intensive plan (core path)

★ = core note. The 4-week plan reads only these notes; the rest go to the second-pass list.

| Day | Task |
|---|---|
| 1 | 00-setup labs 00.1 + 00.2 (VirtualBox: `create-vm-virtualbox.ps1`) |
| 2 | 00.3 build kernel or mainline .deb; `cite.sh` + ctags workflow |
| 3 | M01 lesson + ★ notes 02 rings/CPL, 04 syscall path |
| 4 | M01 lab 01 strace map + walkthrough (syscall entry) |
| 5 | M01 ★ note 05 context switch + lab 04 syscall cost |
| 6 | M01 quiz + oral |
| 7 | M02 lesson + ★ notes 01 `task_struct`, 02 fork/clone |
| 8 | M02 lab 01 fork-exec-pipe + lab 02 clone flags |
| 9 | M02 ★ notes 06 sched classes, 07 EEVDF + walkthrough `__schedule` |
| 10 | M02 lab 03 ping-pong + quiz |
| 11 | M03 lesson + ★ notes 01 races, 02 atomics/C11 + lab 01 data race |
| 12 | M03 ★ notes 03 TSO/barriers, 07 futex + lab 04 raw futex |
| 13 | M03 ★ note 08 RCU, 09 deadlock + lab 02 producer-consumer |
| 14 | M03 quiz + oral |
| 15 | M04 lesson + ★ notes 02 page tables, 03 TLB |
| 16 | M04 ★ note 04 page fault path + lab 01 page faults |
| 17 | M04 ★ notes 05 COW, 09 mmap + lab 02 COW |
| 18 | M04 ★ note 10 huge pages/OOM + lab 06 OOM (VM) + quiz |
| 19 | M05 lesson + ★ notes 01 VFS objects, 04 page cache |
| 20 | M05 lab 01 read call chain + lab 02 page cache |
| 21 | M05 ★ notes 07 journaling, 08 io_uring + lab 05 io_uring |
| 22 | M05 quiz |
| 23 | M06 lesson + ★ notes 02 clocks, 08 namespaces/cgroups |
| 24 | M06 lab 03 mini container (VM) + ★ note 07 KVM |
| 25 | M06 quiz |
| 26 | M07 lesson + ★ notes 03 priority inversion, 05 seccomp/Landlock + lab 02 |
| 27 | M07 lab 03 seccomp + quiz |
| 28 | Mock exam (2 quizzes, 60 min) + `CHEATSHEET` |

**Second pass after the 4 weeks:**
- M01 notes 01, 03, 06 and labs 02, 03, 05.
- M02 notes 03, 04, 05, 08 and labs 04–06.
- M03 notes 04–06, 10 and labs 03, 05, 06.
- M04 notes 01, 06–08 and labs 03–05.
- M05 notes 02, 03, 05, 06, 09 and labs 03, 04, 06.
- M06 notes 01, 03–06 and labs 01, 02, 04, 05.
- M07 notes 01, 02, 04, 06 and labs 01, 04, 05.

## Rules that make either plan work

- **Run before you read the solution.** Each lab's `solution/` is for after your own attempt.
- **One quiz per module, twice:** once at the end of the module, and once two weeks later (spaced repetition). Only re-study the questions you missed.
- **Say the oral questions out loud.** Azad oral exams reward a clear 2-minute answer with a diagram.
- **When a number on your machine differs from the README:** the README numbers were captured on a shared VirtualBox guest. Compare the *shape* (ratios, which is bigger), not absolute values.
