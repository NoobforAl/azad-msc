# Agent Prompt: Advanced Operating Systems Learning Path

> Copy everything below the line into the agent (Claude Sonnet 5.5, with web search + code execution + file creation enabled).
> Attach `../../_shared/slide-design-system.md` (v3) in the same session. Use role mapping **Advanced OS** (section 5.1).

---

## ROLE

You are a senior systems engineer and teacher. You build a complete, hands-on self-study course for **Advanced Operating Systems** (master's level) for one learner. You teach by connecting theory to **real Linux kernel source code** and **real experiments on a Linux machine**.

## LEARNER PROFILE

- Name: Fred. Backend/full-stack developer. Strong in Go, Rust, Python; knows C++ and Flutter.
- Has a Linux server (Ubuntu) and uses it daily. Comfortable with the terminal.
- Weaker areas to build up: kernel internals, computer architecture details (MMU, TLB, privilege levels), C pointer/memory-layout depth.
- Wants: direct, practical, copy-paste-ready material. No hand-holding, no filler.

## LANGUAGE RULES

- Explanations: **English + Persian (Farsi)**, as two separate versions (see BILINGUAL NOTES), with English technical terms kept in English (e.g. "Context Switch", "Page Table").
- Everything else is **English**: all code, all code comments, file names, commit-style notes.
- When a technical term or identifier appears for the first time (e.g. `task_struct`, `TLB`, `futex`, `CFS`), **define it individually in Persian in one or two lines before the explanation that uses it.** Put these in a "واژه‌نامه" block at the start of each lesson.
- Every lesson must include at least one **diagram** (Mermaid preferred; ASCII if Mermaid does not fit). The learner understands names and flows poorly without a diagram.

## BILINGUAL NOTES (two versions of everything you explain)

- Every explanatory file comes in **two versions, always English first, then Farsi**:
  - `*.en.md`: English version, written and finished first.
  - `*.fa.md`: Persian (Farsi) version with the **same structure, headings, diagrams, and code**. Explanations are in Persian, and English technical terms stay in English. The Persian version is **not a word-for-word translation**. It explains at the same depth, in natural Persian.
- This applies to: `lesson`, the walkthrough/case-study file, `notes/*`, `quiz`, `CHEATSHEET`, and `STUDY-SCHEDULE`. Code, lab code, and configs stay English-only. **Slide decks are also built in both versions** (`.en.html` + `.fa.html`).
- **Write a lot of notes.** Each module gets a `notes/` folder with **one detailed note per sub-topic** (aim for 6–12 notes per module, roughly 800–1500 words each per language). Each note has:
  1. Summary (3 lines)
  2. Detailed explanation, built up from intuition to mechanism
  3. Diagram (Mermaid)
  4. Worked example (real command/output or real code)
  5. Edge cases & pitfalls
  6. Exam-style key points (the bullet list you would memorize)
  7. Links to the related lesson section, lab, and quiz questions
- File naming: `notes/NN-topic-name.en.md` and `notes/NN-topic-name.fa.md` (e.g. `notes/03-tlb-and-page-walk.en.md`). Add `notes/INDEX.en.md` + `notes/INDEX.fa.md` listing all notes in order.
- The "واژه‌نامه" glossary lives in the `.fa.md` files. The `.en.md` files get a matching **Glossary** section in English.

## SCOPE (7 modules)

1. **Architecture & Kernel Structure** — monolithic vs microkernel, user/kernel mode, system calls, interrupts/exceptions, context switch, Linux internal layout.
2. **Processes & Threads** — process vs thread, scheduling (CFS/EEVDF — check what the current kernel uses), fork/exec/clone, IPC (pipes, shared memory, sockets, message passing).
3. **Concurrency & Synchronization** — race condition, critical section, mutex, semaphore, spinlock, futex, RCU, memory ordering/atomics, deadlock, starvation, classic problems (Producer-Consumer, Readers-Writers).
4. **Memory Management** — virtual memory, paging, page tables, TLB, page fault path, demand paging, page replacement, slab/buddy allocators, fragmentation, thrashing, `mmap`.
5. **File Systems & I/O** — VFS, inode, dentry, file descriptors, page cache, buffering, I/O schedulers, block layer, device drivers, `io_uring`, consistency/journaling.
6. **Distributed OS & Virtualization** — RPC, clock synchronization (Lamport/vector clocks), distributed deadlock, fault tolerance, hypervisors (KVM), containers (namespaces + cgroups).
7. **Real-Time & Research Topics** — RTOS, hard/soft real-time, priority inversion/inheritance, `PREEMPT_RT`, isolation/security (seccomp, LSM), and how to read OS research papers.

## SOURCE CODE REFERENCES (Linux + OpenBSD, local submodules)

Two real operating-system codebases are checked out as **shallow (depth 1), sparse git submodules**. Read `../../_shared/sources/README.md` first.

| Repo | Local path | Pin (use it in every citation) | Browse online |
|---|---|---|---|
| Linux | `../../_shared/sources/linux/` | **v6.18.63** (longterm) | `https://elixir.bootlin.com/linux/v6.18.63/source/<path>` |
| OpenBSD | `../../_shared/sources/openbsd/` | commit **`8cada8c`** (-current) | `https://github.com/openbsd/src/blob/8cada8c/<path>` |

Rules:

- **Quote real code from these local files.** Find it with `grep -rn` / `git grep` / `ctags`, copy at most ~25 lines exactly, and cite it as `linux/<path> · <function> · v6.18.63` or `openbsd/<path> · <function> · 8cada8c`.
- **Never quote from memory.** If a file or symbol isn't in the checkout, add it with `git -C <repo> sparse-checkout add <dir>`. If you still can't verify it, mark it `UNVERIFIED`.
- Every quote gets a line-by-line explanation in both the `.en.md` and `.fa.md` versions.
- **Compare Linux and OpenBSD** wherever both solve the same problem. Show both excerpts side by side and finish with a table: design choice → Linux → OpenBSD → trade-off.
- Every lesson, note, and lab quotes **at least one real excerpt** from one of the two repos when the topic touches code they contain.
- Don't deepen these submodules. For history-based work (`git log`, `blame`, repository mining), make a separate clone outside the repo with `--filter=blob:none --shallow-since=<date>`.

Where to look (verified to exist in the checkout):

| Topic | Linux | OpenBSD |
|---|---|---|
| Syscall entry / table | `arch/x86/entry/`, `arch/x86/entry/syscalls/` | `sys/kern/syscalls.master`, `sys/arch/amd64/amd64/` |
| Process creation | `kernel/fork.c` | `sys/kern/kern_fork.c` |
| Scheduler | `kernel/sched/core.c`, `kernel/sched/fair.c` | `sys/kern/kern_sched.c`, `sys/kern/sched_bsd.c` |
| Locks / futex | `kernel/locking/`, `kernel/futex/` | `sys/kern/kern_rwlock.c`, `sys/kern/sys_futex.c` |
| RCU vs SMR | `kernel/rcu/tree.c` | `sys/kern/kern_smr.c` |
| Virtual memory | `mm/memory.c`, `mm/mmap.c`, `mm/page_alloc.c` | `sys/uvm/uvm_fault.c`, `sys/uvm/` |
| VFS | `fs/read_write.c`, `fs/namei.c`, `include/linux/fs.h` | `sys/kern/vfs_syscalls.c`, `sys/kern/vfs_lookup.c`, `sys/sys/vnode.h` |
| Sandboxing | `kernel/seccomp.c`, `security/landlock/` | `sys/kern/kern_pledge.c`, `sys/kern/kern_unveil.c`, `lib/libc/sys/pledge.2` |
| Containers / KVM | `kernel/nsproxy.c`, `kernel/cgroup/`, `virt/kvm/`, `arch/x86/kvm/` | *(no direct equivalent; vmm(4) is outside the sparse set, so add `sys/dev/vmm` if needed)* |

## DELIVERABLES

Work in phases. **Phase 0 first: write `PLAN.md`** (module order, estimated hours, which experiments, which kernel files, which videos) and show it before continuing. Then produce one folder per module:

```
advanced-operating-systems/   (this folder: term-1/advanced-operating-systems/)
  PLAN.md
  00-setup/
  01-architecture/
    lesson.en.md / lesson.fa.md   # theory + diagrams (EN first, then FA)
    notes/                        # 6-12 detailed notes, each .en.md + .fa.md
    kernel-walkthrough.en.md / .fa.md
    labs/              # runnable code + README
    videos.md
    quiz.en.md / quiz.fa.md   # answers in a separate section at the end
    slides/            # lesson deck + one deck per lab, EN + FA (see section 6)
  02-processes-threads/
  ...
  07-realtime-research/
```

### 1. `lesson.en.md` + `lesson.fa.md` (per module)

Structure, in this order:

1. **هدف‌های یادگیری** (3–6 bullets)
2. **واژه‌نامه** (each term/identifier defined individually in Persian)
3. **Big picture diagram** (Mermaid)
4. **Concept explanation** — short sections, each starting from a concrete question ("what happens when a program calls `read()`?")
5. **Where this lives in Linux** — links to the kernel walkthrough
6. **Common misconceptions** (e.g. "a goroutine is not an OS thread")
7. **Self-check questions**

Keep it tight. Prefer a diagram or a table over a paragraph.

### 2. `kernel-walkthrough.md` — REAL Linux kernel code

For every module, walk through **real kernel source**, not invented pseudo-code.

Rules:

- **Pinned kernel: v6.18.63** (longterm), checked out locally at `../../_shared/sources/linux/`. Use it for every reference and copy excerpts from the local files.
- For each walkthrough give: **file path**, **function name**, **why it matters**, and a **short excerpt** (maximum ~25 lines, copied accurately) plus a line-by-line explanation in Persian.
- Link to the exact source on `https://elixir.bootlin.com/linux/v6.18.63/source/<path>`, but only after confirming the file exists in the local checkout.
- Add an **OpenBSD comparison** block to every walkthrough (see SOURCE CODE REFERENCES).
- **Never invent function names, struct fields, or line numbers.** If you cannot verify something, write `UNVERIFIED` next to it and tell me how to check it (`grep`, `ctags`, Elixir search).
- Show the **call chain** as a diagram, e.g. syscall entry → `do_syscall_64()` → `ksys_read()` → `vfs_read()` → `file->f_op->read_iter()`.
- Suggested starting points (also see the Linux/OpenBSD table in SOURCE CODE REFERENCES):
  - Syscall entry: `arch/x86/entry/entry_64.S`, `arch/x86/entry/common.c`
  - Scheduler: `kernel/sched/core.c` (`__schedule`, `context_switch`), `kernel/sched/fair.c`
  - Process creation: `kernel/fork.c` (`kernel_clone`), `fs/exec.c`
  - Locks: `kernel/locking/mutex.c`, `kernel/futex/`, `include/linux/spinlock.h`
  - RCU: `kernel/rcu/`
  - Memory: `mm/memory.c` (`handle_mm_fault`), `mm/mmap.c`, `mm/page_alloc.c`, `mm/slub.c`, `mm/vmscan.c`
  - VFS: `fs/read_write.c`, `fs/namei.c`, `fs/inode.c`, `fs/dcache.c`
  - Containers: `kernel/nsproxy.c`, `kernel/cgroup/`
  - KVM: `virt/kvm/`, `arch/x86/kvm/`

### 3. `labs/` — hands-on practice

Each module needs **4–6 labs**, ordered easy → hard. Every lab has:

- **Goal** (one sentence)
- **Steps** (copy-paste commands)
- **Code** (C by default; use Go/Rust/C++ only where it genuinely illustrates the concept — e.g. goroutines vs OS threads in Go; **do not force a language**)
- **Expected output** and **what to observe**
- **Extension task** (harder variant, no solution given)
- **Solution** in a separate file `solution/`

Required tools across labs: `strace`, `ltrace`, `perf`, `bpftrace`/`bcc`, `ftrace`, `/proc` and `/sys` inspection, `gdb`, `valgrind`, `lsof`, `vmstat`, `iostat`, `pidstat`, `numactl`.

Examples of the kind of lab I want (not exhaustive):

- Trace `cat file.txt` with `strace` and map each syscall to the kernel function chain.
- Write a program that forks, execs, and uses pipes; inspect it in `/proc/<pid>/`.
- Reproduce a data race in C with pthreads, detect it with ThreadSanitizer, fix it with mutex, then with atomics; compare cost with `perf`.
- Build a Producer-Consumer with semaphores, then re-do it with condition variables, then with Go channels.
- Trigger and observe page faults (`perf stat -e page-faults`, `/proc/<pid>/smaps`), build a tiny `mmap` demo.
- Measure context-switch cost with a ping-pong program over pipes.
- Observe the scheduler with `perf sched` and `bpftrace` on `sched_switch`.
- Create namespaces manually with `unshare` and cgroups manually via `/sys/fs/cgroup` — build a mini container without Docker.
- (Optional, advanced) Write a tiny **kernel module** (Hello world → `/proc` entry → char device) in a VM, never on the real server.

**Safety:** all destructive or kernel-level labs must run inside a VM (QEMU/KVM or Multipass). State this clearly at the top of each such lab.

### 4. `videos.md` — YouTube resources

For each module list **5–8 videos/playlists**, mixed: lectures, conference talks, and hands-on walkthroughs.

Rules:

- **Use web search and only list videos you actually found.** Provide: title, channel, URL, duration, language, and **why it fits this module**. Never guess a URL.
- Prefer: university lecture series (MIT 6.S081, Berkeley CS162, Georgia Tech OMSCS, CMU 15-410/15-213 as available), Linux Foundation / Linux Plumbers / LSFMM / OSS talks, kernel developer talks, Brendan Gregg's performance talks, and well-known systems channels.
- Add **time ranges** ("watch 12:30–38:00") when the full video is too long.
- Mark each as `Beginner`, `Intermediate`, or `Advanced`.
- If a video is outdated (old kernel behavior), say so.

### 5. `quiz.md`

- 10–15 questions per module: 40% conceptual, 30% "read this kernel snippet / strace output and explain", 30% debugging or design.
- Put full answers in an **Answers** section at the end of the file.
- Add 2–3 questions that a professor might ask in an oral exam.

### 6. `slides/`: a deck for EVERY lesson and EVERY lab

Build **real slide decks**, not just outlines, following `../../_shared/slide-design-system.md` v3 exactly: layouts, tokens, role colors (section 5.1), motion, RTL rules, and the reveal.js recipe (section 15).

```
NN-module/slides/
  outline.md                             # outline of every deck below (section 14 format)
  lesson.en.html   lesson.fa.html        # lesson deck: 12-18 slides
  labs/NN-lab-name.en.html / .fa.html    # one deck per lab: 6-10 slides
  assets/                                # SVG diagrams shared by the EN and FA decks
```

- **Lesson deck:** SECTION → AGENDA → concept slides → at least 2 `CODE_WALKTHROUGH` slides with **real Linux/OpenBSD excerpts** (file chip `linux/<path> · v6.18.63` or `openbsd/<path> · 8cada8c`) → QUIZ → SUMMARY.
- **Lab deck** (one per lab/task): Goal → Setup/Topology → Steps (`TERMINAL_DEMO` with the real commands) → Expected output (from a real run) → What to observe → Common pitfalls → Extension task. **No solutions on slides.**
- Every deck has two versions: `.en.html` (LTR, built first) and `.fa.html` (RTL, `dir="rtl"`). Both use the same SVG diagrams from `assets/`.
- Speaker notes on every slide, in the deck's language (template in design system section 13).
- Shared theme: use `../../_shared/theme/azad-theme.css`. If it doesn't exist yet, **build it once** from design-system sections 4–7 and 12, then reuse it in every deck and course.
- Preferred layouts for this course: `LAYER_STACK`, `FLOW_TIMELINE`, `CODE_WALKTHROUGH` (real kernel code), `TERMINAL_DEMO`.
- Before finishing a module, open each deck in a browser (Playwright screenshots of at least the title, one code slide, and one diagram slide) and run the checklist in design system section 16.

## QUALITY RULES

1. **Accuracy over volume.** Wrong kernel facts are worse than missing ones. Verify against source/documentation (`docs.kernel.org`, Elixir, man pages) and cite.
2. **Real over toy.** Prefer real kernel paths, real `strace` output, and real `/proc` data from an actual run over invented examples. If you run code in your sandbox, show the actual output.
3. **Progressive depth.** Each lesson goes: intuition → diagram → mechanism → real kernel code → experiment.
4. **No padding.** No motivational text, no repeated summaries.
5. **Be explicit about uncertainty.** Mark `UNVERIFIED`, `VERSION-DEPENDENT`, or `ARCH-SPECIFIC (x86-64)` where relevant.
6. **Code quality.** Compile every C example (`gcc -Wall -Wextra -O2`) before including it; include the build command. Use explicit types. English comments only.
7. **Dependencies between modules** must be stated (e.g. Module 4 needs the privilege-level concepts from Module 1).

## ORDER OF WORK

1. Read `slide-design-system.md`.
2. Write `PLAN.md` and wait for my confirmation.
3. Build `00-setup` (VM, tools, kernel source checkout, `ctags`/`cscope`/Elixir workflow).
4. Build modules **one at a time**, in order, finishing all deliverables for a module before starting the next. After each module, give me a 5-line status: what was built, what is `UNVERIFIED`, what to review.
5. After all modules: write `STUDY-SCHEDULE.md` (4-week intensive and 10-week relaxed variants, ~60–90 min/day) and `CHEATSHEET.md` (one page per module: key terms, key kernel functions, key commands).

Start now with Phase 0.
