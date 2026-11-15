# 01 · Architecture & Kernel Structure — slide outlines

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced OS (user = teal, kernel = amber, hardware = violet, data = green).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 18 |
| Lab 01.1 strace map | [`labs/01-strace-map.en.html`](labs/01-strace-map.en.html) | [`labs/01-strace-map.fa.html`](labs/01-strace-map.fa.html) | 7 |
| Lab 01.2 raw syscall | [`labs/02-raw-syscall.en.html`](labs/02-raw-syscall.en.html) | [`labs/02-raw-syscall.fa.html`](labs/02-raw-syscall.fa.html) | 7 |
| Lab 01.3 interrupts | [`labs/03-interrupts.en.html`](labs/03-interrupts.en.html) | [`labs/03-interrupts.fa.html`](labs/03-interrupts.fa.html) | 7 |
| Lab 01.4 syscall cost | [`labs/04-syscall-cost.en.html`](labs/04-syscall-cost.en.html) | [`labs/04-syscall-cost.fa.html`](labs/04-syscall-cost.fa.html) | 7 |
| Lab 01.5 ftrace vfs_read | [`labs/05-ftrace-vfs-read.en.html`](labs/05-ftrace-vfs-read.en.html) | [`labs/05-ftrace-vfs-read.fa.html`](labs/05-ftrace-vfs-read.fa.html) | 7 |

Lab decks are generated: `python _shared/tools/labdeck.py term-1/advanced-operating-systems/01-architecture/slides/labs.content.py`. Open decks through a local web server at the repo root (`python -m http.server`). Press `S` for speaker notes; add `?print-pdf` for PDF export.

Shared SVGs (`assets/`, language-neutral labels): `kernel-types.svg`, `idt-paths.svg`, `context-switch.svg`.

---

## Lesson deck

## Slide 1 — TITLE
Title: One read(), from user space into the kernel and back · Fields: placeholders from §3.4 (never invented)

## Slide 2 — SECTION
Eyebrow: Module 01 · Title: Architecture & Kernel Structure · Why: every fault, scheduling decision and file read starts with a ring 3 → ring 0 crossing · Pills: rings & CPL · syscall · IDT · context switch

## Slide 3 — AGENDA
Five questions: what runs in ring 0 · how code gets in · entry code line by line · task switch · cost (current = 1)

## Slide 4 — CONCEPT_DIAGRAM
Title: Monolithic kernels call, microkernels message
Diagram: `assets/kernel-types.svg`. ① monolithic: app (role-1) → one syscall (accent arrow) → one kernel address space (role-2) with VFS → ext4 → driver. ② microkernel: app, FS server and driver as user processes (role-1), IPC arrows through a small kernel (role-2). Dashed boundary labelled "Ring 3 / Ring 0".
Takeaway (notes): Linux modules run in ring 0; modular ≠ micro · Source: fs/read_write.c L569 · Motion: pop

## Slide 5 — LAYER_STACK
Title: A 2-bit number separates you from the kernel
Bands: Ring 3 user (CS=0x33, cat, glibc, [vdso]) · boundary "syscall · IDT gate → CPL 0" · Ring 0 kernel (CS=0x10, entry_SYSCALL_64, vfs_read, schedule) · Hardware (MSR_LSTAR, IDT, CR3, APIC)
Takeaway: cli or mov %cr3 at CPL 3 → #GP → SIGSEGV · Example: cpl.c

## Slide 6 — BENTO
Three ways into ring 0: system call (role-1), exception (role-2), interrupt (role-3) · Takeaway: all end in the same pt_regs

## Slide 7 — FLOW_TIMELINE
glibc wrapper → CPU (RIP=LSTAR) → asm entry (pt_regs) → do_syscall_64 → x64_sys_call → vfs_read; fragment moves the highlight · Takeaway: return path = signals, maybe schedule(), sysretq

## Slide 8 — CODE_WALKTHROUGH
linux/arch/x86/entry/entry_64.S · v6.18.63 · L91-106 (long PER_CPU_VAR operands cut with "...")
Callouts: ① swapgs ② park rsp, PTI CR3, kernel stack ③ fake hardware frame (rcx=RIP, r11=RFLAGS) ④ orig_ax for strace

## Slide 9 — CODE_WALKTHROUGH
linux/arch/x86/entry/syscall_64.c · v6.18.63 · L34-100 (elided with /* ... */)
Callouts: ① .tbl → case labels ② noinstr ③ ptrace · seccomp · tracepoint ④ unknown nr → -ENOSYS

## Slide 10 — TERMINAL_DEMO
Real output of `map-syscalls.sh cat.trace` (lab 01), top rows highlighted · Captured 2026-11-15 on aos-lab

## Slide 11 — CONCEPT_DIAGRAM
Title: Exceptions and IRQs share the IDT; syscall doesn't · Diagram: `assets/idt-paths.svg`: ① syscall → MSR_LSTAR → entry_SYSCALL_64; ② exception → IDT 0–31 → asm_exc_* → exc_*(); ③ interrupt → APIC → IDT 32–255 → common_interrupt() → handle_irq_event(); vertical dashed "→ Ring 0" boundary

## Slide 12 — TERMINAL_DEMO
Title: With nothing of ours running, CPUs are still interrupted · real output of `irq-delta.sh 5 8` (lab 03, shared VM)

## Slide 13 — CONCEPT_DIAGRAM
Title: A context switch swaps one stack pointer · Diagram: `assets/context-switch.svg`: two kernel stacks (pt_regs role-4, context_switch frame role-2, six saved registers accent), CPU box (role-3) with rsp/CR3/current_task; ① push 6, save rsp ② rsp = B->thread.sp, pop 6 ③ __switch_to()

## Slide 14 — BIG_STAT
The measured ratio between a real syscall and a vDSO clock_gettime from lab 04 (real numbers, captured on the shared VM)

## Slide 15 — TWO_COLUMN_COMPARE
Linux v6.18.63 vs OpenBSD 8cada8c: numbering, dispatch, error return, who may call, kernel lock

## Slide 16 — QUIZ
Which register carries the 4th syscall argument? A rcx · B r10 · C user stack · D r11

## Slide 17 — QUIZ answer (DEFINITION)
B: syscall already used rcx for the return address · Source: syscall_wrapper.h SC_X86_64_REGS_TO_ARGS L56-59

## Slide 18 — SUMMARY
① CPU enforces CPL, kernel picks the doors ② every entry builds pt_regs, every exit may schedule ③ context switch = new rsp, maybe new CR3 · Next: Module 02

---

## Lab decks (generated, 7 slides each)

Goal (SECTION) → Setup (4 cards) → Steps (TERMINAL_DEMO, exact commands from the README) → Expected output (real VM output, "Captured on …") → What to observe → Common pitfalls → Extension task. No solutions on slides.

| Lab | Steps shown | Expected (real) | Observe |
|---|---|---|---|
| 01.1 strace map | strace -f / -c, map-syscalls.sh, kallsyms grep | mapping table rows | loader dominates · fstat → sys_newfstat · stubs exist |
| 01.2 raw syscall | build, run, strace, cpl, gdb | returns, errno, CS=0x33, SIGSEGV | three identical writes · wrapper asm · CPL 3 |
| 01.3 interrupts | irq-delta idle + dd, perf stat -a | top deltas, tracepoint counts | LOC dominates · IPIs · faults ≠ interrupts |
| 01.4 syscall cost | build, run, maps, strace -c, time | ns/call table | vDSO ≪ syscall · strace multiplies cost |
| 01.5 ftrace | script, filter-functions grep | vfs_read summary + tree | ext4_file_read_iter path · noinstr absent |
