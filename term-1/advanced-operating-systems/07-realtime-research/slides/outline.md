# 07 · Real-Time & Research Topics — slide outlines

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced OS (user = teal, kernel = amber, hardware = violet, data = green).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 18 |
| Lab 07.1 cyclictest | [`labs/01-cyclictest.en.html`](labs/01-cyclictest.en.html) | [`labs/01-cyclictest.fa.html`](labs/01-cyclictest.fa.html) | 7 |
| Lab 07.2 Priority inversion | [`labs/02-priority-inversion.en.html`](labs/02-priority-inversion.en.html) | [`labs/02-priority-inversion.fa.html`](labs/02-priority-inversion.fa.html) | 7 |
| Lab 07.3 seccomp-BPF | [`labs/03-seccomp-bpf.en.html`](labs/03-seccomp-bpf.en.html) | [`labs/03-seccomp-bpf.fa.html`](labs/03-seccomp-bpf.fa.html) | 7 |
| Lab 07.4 Landlock | [`labs/04-landlock.en.html`](labs/04-landlock.en.html) | [`labs/04-landlock.fa.html`](labs/04-landlock.fa.html) | 7 |
| Lab 07.5 Paper review | [`labs/05-paper-review.en.html`](labs/05-paper-review.en.html) | [`labs/05-paper-review.fa.html`](labs/05-paper-review.fa.html) | 7 |

Open through a local web server (`python -m http.server` at the repo root), e.g. `http://127.0.0.1:8000/term-1/advanced-operating-systems/07-realtime-research/slides/lesson.en.html`. `S` = speaker notes, `?print-pdf` = PDF export. Lab decks are generated: `python _shared/tools/labdeck.py term-1/advanced-operating-systems/07-realtime-research/slides/labs.content.py`.

---

## Lesson deck

## Slide 1 — TITLE
Title: Guarantees in time and in reach · Fields: placeholders from §3.4

## Slide 2 — SECTION
Module 07 · Real-Time & Research Topics · Why: average speed is not a guarantee · Pills: PREEMPT_RT · priority inheritance · seccomp · Landlock

## Slide 3 — AGENDA
Five questions (real-time & latency · RMS/EDF/SCHED_DEADLINE · Pathfinder/PI · sandboxing · reading papers), current = 1

## Slide 4 — BENTO
Hard (danger) · Firm (kernel/amber) · Soft (user/teal) · Task model `(C, D, T)` (data/green) · Takeaway: maximum, never average

## Slide 5 — FLOW_TIMELINE
Timer → `try_to_wake_up()` → **wait to preempt** (current, the unbounded step) → `__schedule()` → task runs · Takeaway: PREEMPT_RT shrinks step 3

## Slide 6 — TERMINAL_DEMO
Real `run-cyclictest.sh` summary lines (idle vs loaded), VM caveat in the caption

## Slide 7 — CODE_WALKTHROUGH
`linux/kernel/sched/deadline.c · __dl_overflow() · v6.18.63 · L212-217` · ① new_bw ② -1 = admission off ③ EBUSY · data table RMS vs EDF (τ = (2,5)(2,7)(2,9), U = 0.908)

## Slide 8 — CONCEPT_DIAGRAM
`assets/inversion-timeline.svg`: ① no protocol (H waits through M's 800 ms) ② PTHREAD_PRIO_INHERIT (L boosted 10 → 30, amber = kernel-changed priority) · H waiting = dashed danger pattern

## Slide 9 — CODE_WALKTHROUGH
`linux/kernel/locking/rtmutex.c · task_blocks_on_rt_mutex() · v6.18.63 · L1265-1272` · ① top waiter only ② rt_mutex_adjust_prio → rt_mutex_setprio ③ chain walk

## Slide 10 — TERMINAL_DEMO
Real `inversion none` vs `inversion inherit` runs (H's wait), pinned with `taskset -c 7`

## Slide 11 — TWO_COLUMN_COMPARE
PREEMPT_DYNAMIC (full) vs PREEMPT_RT: spin_lock, IRQs, softirqs, runtime switch · Takeaway: only raw_spinlock_t spins · RT numbers UNVERIFIED (notes)

## Slide 12 — CONCEPT_DIAGRAM
`assets/sandbox-path.svg`: user process → syscall boundary → ① seccomp (deny before) → ② do_sys_openat2 path lookup → ③ LSM Landlock (deny after lookup)

## Slide 13 — CODE_WALKTHROUGH
`linux/kernel/seccomp.c · seccomp_run_filters() · v6.18.63 · L413-430` (comment L419-422 elided) · ① fail closed ② stack via f->prev ③ lowest action wins

## Slide 14 — TWO_COLUMN_COMPARE
seccomp + Landlock vs pledge + unveil · Takeaway: `pledge_syscall()` is one bitwise AND (`openbsd/sys/kern/kern_pledge.c` L537-554 · 8cada8c, in notes)

## Slide 15 — FLOW_TIMELINE
Pass 1 (five Cs) → pass 2 (figures) → map to v6.18.63 (`git grep`) → pass 3 (re-create) · Takeaway: Wasted Cores → `sched_balance_rq()` fair.c L12052

## Slide 16 — QUIZ
FIFO 30 waits on a default mutex held by FIFO 10: what bounds the wait? A critical section · **B nothing** · C futex timeout · D deadline admission

## Slide 17 — DEFINITION (answer)
Default mutex = PTHREAD_PRIO_NONE → unbounded; A becomes true with PTHREAD_PRIO_INHERIT

## Slide 18 — SUMMARY
① worst case, measure max ② lock protocols + CBS ③ sandboxes only tighten · Next: STUDY-SCHEDULE & CHEATSHEET

---

## Lab decks (generated from `labs.content.py`, 7 slides each)

| # | Layout | Content |
|---|---|---|
| 1 | SECTION | lab number, goal, "Runs on" pill |
| 2 | BENTO (4 cards) | preconditions by role |
| 3 | TERMINAL_DEMO | steps copied from the README |
| 4 | TERMINAL_DEMO | real VM output (`captured=`) or EXPECTED caption |
| 5 | SUMMARY-style list | what to observe |
| 6 | symptom → fix rows | pitfalls (labeled tags, never color alone) |
| 7 | highlight | extension task, no solution |

## Build notes

- **Deck-local CSS** (in both lesson decks' `<style>`): a small `.dt` data table (theme has no table style), `white-space:nowrap` on inline code (in RTL, `p->prio` wrapped at the hyphen), ligatures off for code (JetBrains Mono rendered `->` and `!=` as arrows/≠), and `.diagram.short` (max-height 600 px) so tall SVGs don't hit the footer.
- **Logo:** `_shared/brand/azad-logo.svg` is still missing → dashed placeholder.
- **Screenshots:** headless Edge 1920×1080 at port 8107: title, diagram (8, 12), code (7, 9), FA code (9), FA compare (14), terminal slides, lab decks.
