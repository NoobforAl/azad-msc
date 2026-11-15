# 00 · Setup — slide outlines

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced OS (user = teal, kernel = amber, hardware = violet, data = green).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 13 |
| Lab 00.1 Create the VM | [`labs/01-create-vm.en.html`](labs/01-create-vm.en.html) | [`labs/01-create-vm.fa.html`](labs/01-create-vm.fa.html) | 7 |
| Lab 00.2 Install tools | [`labs/02-install-tools.en.html`](labs/02-install-tools.en.html) | [`labs/02-install-tools.fa.html`](labs/02-install-tools.fa.html) | 7 |
| Lab 00.3 Build kernel | [`labs/03-build-kernel.en.html`](labs/03-build-kernel.en.html) | [`labs/03-build-kernel.fa.html`](labs/03-build-kernel.fa.html) | 7 |

Open a deck through a local web server so the relative theme path resolves: `python -m http.server` at the repo root, then `http://127.0.0.1:8000/term-1/advanced-operating-systems/00-setup/slides/lesson.en.html`. Press `S` for speaker notes, and add `?print-pdf` to the URL for PDF export.

---

## Lesson deck

## Slide 1 — TITLE
Title: Lab machines, tools, and real kernel source · Fields: placeholders from §3.4 (never invented)

## Slide 2 — SECTION
Eyebrow: Module 00 · Title: Setup · Why: wrong machine / wrong kernel / quoting from memory makes later results untrustworthy · Pills: libvirt VM · tracing tools · v6.18.63 build

## Slide 3 — AGENDA
Two machines → tools → kernel build → read & cite source (current = 1)

## Slide 4 — CONCEPT_DIAGRAM
Title: Observe on the server, break things in the VM
Diagram: `assets/host-vm.svg`, with host (user-space labs = role-1, Ubuntu kernel = role-2, sources = role-4), VM inside a dashed "VM boundary" (kernel-level labs, 6.18.63-aos-lab, snapshot), and a hardware band (role-3)
Callouts (in the SVG): ① host ② VM ③ snapshot · Motion: pop
Notes: vCPU = thread (`ps -o nlwp`) · WSL2 is not a substitute

## Slide 5 — TWO_COLUMN_COMPARE
Server (strace, perf, bpftrace, /proc) vs VM only (modules, RT/lockdep, OOM/cgroups, FS crash)

## Slide 6 — BENTO
Tracing (role-2) 7 cols · Inspection (role-1) 5 · Debug & memory (role-4) 5 · Load & latency (role-3) 7 · Takeaway: verify-tools.sh exits 0

## Slide 7 — FLOW_TIMELINE
clone tag → olddefconfig → localmodconfig → BTF/ftrace → bindeb-pkg → uname -r (fragment moves the highlight; all steps always visible)

## Slide 8 — CODE_WALKTHROUGH
Source: `linux/kernel/Kconfig.preempt · config PREEMPT_RT · v6.18.63` (4 lines, verified)
Highlights: ① `depends on EXPERT && ...` ② `select PREEMPTION` · Callouts: silent drop / forced preemption / --rt sets both

## Slide 9 — CODE_WALKTHROUGH (wide)
Source: `linux/arch/x86/entry/syscall_64.c · do_syscall_64() · v6.18.63 · L87-100` (lines 91–98 elided with `/* ... */`; full excerpt in guide §4.3)
Highlights: ① `noinstr` ② `syscall_enter_from_user_mode` ③ `syscall_exit_to_user_mode`

## Slide 10 — TERMINAL_DEMO
Real output: `git grep` for `kernel_clone` and `SYSCALL_DEFINE3(read,` (fs/read_write.c:722), plus `cite.sh`. Long lines are cut with "...", and the caption says so.

## Slide 11 — QUIZ
Why is do_syscall_64 missing from ftrace's traceable functions? A inlined · **B noinstr** · C BTF off · D modules only

## Slide 12 — DEFINITION (answer)
noinstr → `.noinstr.text`, built without ftrace hooks · Source: `include/linux/compiler_types.h · L417 · v6.18.63`

## Slide 13 — SUMMARY
① observe on server, change kernel in VM ② tools verified on the running kernel ③ VM runs v6.18.63, quotes come from cite.sh · Next: Module 01

---

## Lab decks (all three use the same 7-slide structure)

| # | Layout | Content |
|---|---|---|
| 1 | SECTION | Lab number, goal sentence, "Runs on" pill |
| 2 | BENTO (4 cards) | Preconditions, colored by role |
| 3 | TERMINAL_DEMO | Steps copied from the lab README |
| 4 | TERMINAL_DEMO | Expected output, with the caption "EXPECTED: not yet captured" until a real run replaces it |
| 5 | SUMMARY-style list | What to observe (each item points to a later module) |
| 6 | Symptom → fix rows | Common pitfalls (danger tag → ok tag, labeled, never color alone) |
| 7 | Highlight | Extension task. **No solution on slides** (it's in `solution/`) |

## Build notes

- **Logo:** `_shared/brand/azad-logo.svg` is missing, so `azad-deck.js` shows the dashed `[University logo]` placeholder (§3.2). Drop the official file in and every deck picks it up.
- **Brand blue:** the `--brand` value is still the documented approximation. Sample it from the logo (§3.3) once the file exists.
- **Screenshots:** taken with headless Edge at 1920×1080 (title, diagram, code, terminal, quiz, RTL code, lab pitfall). The Playwright MCP browser failed to launch (Chrome exit 13).
- **Lab "Expected output":** representative, not yet captured, and marked as such on the slide and in the README (quality rule 2).
