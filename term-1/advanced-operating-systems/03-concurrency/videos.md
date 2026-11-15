# 03 — Concurrency & Synchronization: videos

> Verified 2026-11-15 by opening each page.
> How it was verified: each URL was found through web search. Its **title and channel** were then confirmed from YouTube's public oEmbed endpoint (`https://www.youtube.com/oembed?url=<video>`). The course and talk pages that link to it were opened as well (MIT 6.S081 schedule, Brendan Gregg's flame-graph page, herbsutter.com, Linux Foundation webinar page).
> **Durations:** YouTube refused the automated page reads ("LOGIN_REQUIRED"), so we could not read any duration from YouTube itself. Where a duration is given, its source is named. Otherwise the entry says "not shown on page". Check the length on the player before you plan your time.
> All videos are in English.

## How to use

| Note | Watch | Why |
|---|---|---|
| 01 race conditions & critical sections | V1 | lost updates in a real kernel (`kfree` race), what a lock guarantees |
| 02 atomics & C11 memory model | V3, V4 | acquire/release, seq_cst, what the hardware really does |
| 03 x86-TSO vs weaker models; barriers | V3 (part 2), V4 | code generation per architecture, fences |
| 04 spinlocks | V1 | test-and-set spinlock, interrupts off while holding |
| 05 mutex / 06 semaphores & condvars | V1 (spin vs. block) | when to spin and when to sleep |
| 07 futex | V6 | why the futex syscall is limited, and futex2 / `futex_waitv` |
| 08 RCU | V2, V5 | publish/subscribe + wait-for-readers, from xv6 to Linux |
| 09 deadlock | V1 | `rename()` lock-order deadlock, global lock order |
| 10 classic problems / lock contention in practice | V7 | off-CPU time = time blocked on locks |

## V1 — 6.S081 Fall 2020 Lecture 10: Multiprocessors and Locks

| | |
|---|---|
| Channel | David Morejon (the upload linked as "2020 video" from the official MIT 6.S081 Fall 2021 schedule) |
| URL | https://youtu.be/NGXu3vN7yAk |
| Duration | not shown on page |
| Level | Beginner → Intermediate |
| Notes it serves | 01, 04, 09 (also 05/06 for spin vs. block) |

**Why it fits:** Frans Kaashoek's xv6 locking lecture. It removes the locks from `kalloc.c`, shows pages being lost in a `kfree()` race, and builds a test-and-set spinlock. It then covers why interrupts are disabled while a spinlock is held, the barriers needed in acquire and release, `rename()` deadlock, and global lock order. This follows the lecture notes `pdos.csail.mit.edu/6.1810/2024/lec/l-lockv2.txt`, which we opened.
**Time ranges:** watch whole. Prepare with the xv6 book chapter "Locking" and `kernel/spinlock.c`.
**Outdated?** xv6 on RISC-V, not Linux. The ideas are timeless. Linux replaces the plain TAS spinlock with qspinlock (note 04).

## V2 — 6.S081 Fall 2020 Lecture 23: RCU

| | |
|---|---|
| Channel | David Morejon (linked as the video for "Multi-Core scalability and RCU" on the official 6.S081 Fall 2021 schedule) |
| URL | https://youtu.be/KUwyCGMTeq8 |
| Duration | not shown on page |
| Level | Intermediate |
| Notes it serves | 08 |

**Why it fits:** an academic introduction to RCU, built around the paper "RCU usage in the Linux kernel: one decade later" (a 6.S081 reading). It explains why reader-writer locks don't scale, and covers publish with a barrier, grace periods and `synchronize_rcu` vs. `call_rcu`.
**Time ranges:** watch whole.
**Outdated?** Read it alongside note 08. The details of the preemptible RCU in v6.18 (`rcu_read_lock_nesting`, `blkd_tasks`) are newer than the paper's description.

## V3 — C++ and Beyond 2012: Herb Sutter — atomic<> Weapons (parts 1 and 2)

| | |
|---|---|
| Channel | alexsmail (re-upload. The two YouTube URLs are linked from Sutter's own post at herbsutter.com/2013/02/11/atomic-weapons-the-c-memory-model-and-modern-hardware/) |
| URL part 1 | https://www.youtube.com/watch?v=A8eCGOqgvH4 |
| URL part 2 | https://www.youtube.com/watch?v=KeLBd2EJLOU |
| Duration | not shown on page (Sutter's post gives no length) |
| Level | Intermediate → Advanced |
| Notes it serves | 02, 03 |

**Why it fits:** the standard explanation of the C11/C++11 memory model. Part 1 (topics per Sutter's post): "optimizations, races, and the memory model; acquire and release ordering; mutexes vs. atomics vs. fences". Part 2: restrictions on compilers and hardware, code generation and performance on several architectures (x86 vs. Arm/POWER), relaxed atomics, volatile. Part 2 is the right companion to lab 05 (store buffering), because it shows which C11 orderings turn into which fences on x86.
**Time ranges:** part 1 whole, then part 2 for the hardware mapping.
**Outdated?** 2012. The C11 model it describes is still current (C++20 later changed some details of seq_cst and `consume`). The hardware numbers are old.

## V4 — CppCon 2017: Fedor Pikus, "C++ atomics, from basic to advanced. What do they really do?"

| | |
|---|---|
| Channel | CppCon |
| URL | https://www.youtube.com/watch?v=ZQFzMfHIxng |
| Duration | about 1 h 14 min, from a third-party podcast listing (podwise.ai) seen in search. Not confirmed on YouTube |
| Level | Intermediate |
| Notes it serves | 02, 03, 04 |

**Why it fits:** a measurement-driven talk. It shows when atomics beat a mutex and when they don't, and what `lock`-prefixed instructions cost. It explains memory barriers on x86, why compare-exchange loops get slow under contention, and why sharing a cache line is the real cost (lab 01 and its `sharded.c` extension).
**Time ranges:** watch whole.
**Outdated?** Absolute nanosecond numbers depend on the CPU of 2017. The conclusions still hold.

## V5 — Mentorship Session: Unraveling RCU-Usage Mysteries (Fundamentals) — Paul E. McKenney

| | |
|---|---|
| Channel | The Linux Foundation |
| URL | https://www.youtube.com/watch?v=K-4TI5gFsig |
| Duration | not shown on page (the Linux Foundation webinar page gives no length) |
| Level | Intermediate → Advanced |
| Notes it serves | 08 |

**Why it fits:** RCU's maintainer reduces RCU to two components, both of which note 08 quotes from v6.18.63. The first is pointer publish/subscribe (`rcu_assign_pointer()` / `rcu_dereference()`). The second is waiting for pre-existing readers (`synchronize_rcu()`, `rcu_read_lock()` / `rcu_read_unlock()`). The talk then shows how to combine RCU with other mechanisms to replace a reader-writer lock. Recorded 7 December 2021, according to linuxfoundation.org/webinars/unraveling-rcu-usage-mysteries. A follow-up, "Additional Use Cases" (February 2022), is listed on the same site.
**Time ranges:** watch whole.
**Outdated?** Recorded on 5.x-era kernels. The API is unchanged in v6.18, but lazy `call_rcu` (`enable_rcu_lazy`, visible in `kernel/rcu/tree.c` `call_rcu()`) came later.

## V6 — "State of futex2" — André Almeida (LCA 2022 Online)

| | |
|---|---|
| Channel | linux.conf.au |
| URL | https://www.youtube.com/watch?v=6NltTDULqss |
| Duration | about 21 min, from a Class Central listing seen in search. Not confirmed on YouTube |
| Level | Advanced |
| Notes it serves | 07 |

**Why it fits:** explains why the single multiplexed `futex()` syscall limits modern workloads (Wine/Proton wait-on-many, NUMA, sizes other than 32-bit) and how the work was split into new syscalls. Pair it with note 07: the lab uses classic `FUTEX_WAIT`/`FUTEX_WAKE` through `do_futex()` (`kernel/futex/syscalls.c` L112). v6.18.63 also carries the newer syscalls (`SYSCALL_DEFINE6(futex_wait, ...)` at L398 of the same file).
**Related, same speaker (title/channel confirmed via oEmbed):** "A New Futex2() System Call — André Almeida, Collabora", The Linux Foundation, https://www.youtube.com/watch?v=GmqW7GHPxJ0 · "futex2: An update" (LCA 2021), linux.conf.au, https://www.youtube.com/watch?v=eK8lBmtX8Bg.
**Outdated?** 2022 is before the v6.16 process-private futex hash (`futex_private_hash`, `PR_FUTEX_HASH`), so the talk doesn't cover it. Status statements in the talk ("not merged yet") are out of date. **VERSION-DEPENDENT.**

## V7 — USENIX ATC '17: Visualizing Performance with Flame Graphs — Brendan Gregg

| | |
|---|---|
| Channel | USENIX |
| URL | https://youtu.be/D53T1Ejig1Q?t=50m16s |
| Duration | not shown on page |
| Level | Intermediate |
| Notes it serves | 05, 07, 10 (lock contention in practice) |

**Why it fits:** a contended mutex shows up as **off-CPU** time: threads blocked in `futex_wait`, not burning CPU. Gregg's off-CPU flame graphs show where that blocking comes from, which complements the `bpftrace` futex latency histogram in lab 04.
**Time ranges:** from **50:16** (the off-CPU section). That start time comes from Gregg's own page, brendangregg.com/FlameGraphs/offcpuflamegraphs.html.
**Outdated?** The 2017 tooling (perf + early BPF) still works. Today `offcputime-bpfcc` (bcc) is the easiest way to collect the stacks, and it is installed in the course VM.

## Searched but not listed

| Candidate | Why it is not listed |
|---|---|
| Berkeley CS162 synchronization lectures (Kubiatowicz) | found slide PDFs (e.g. cs162.org Lecture 8 "Lock Implementation, Atomic Instructions, Futex") but no video URL we could confirm |
| Mara Bos, *Rust Atomics and Locks* talk | found the book (mara.nl/atomics) and a EuroRust 2023 speaker page, but no video URL we could confirm |
| Jeff Preshing memory-ordering talk | not searched to a confirmed URL; his blog posts are a good written source |
