# 03 — Concurrency & Synchronization: slide outline

> Format: design system §14. Decks: `lesson.en.html` / `lesson.fa.html` (18 slides, hand-written) and `labs/NN-*.{en,fa}.html` (7 slides each, rendered from `labs.content.py` with `python _shared/tools/labdeck.py`). Shared SVGs in `assets/`: `store-buffer.svg`, `futex-split.svg`, `rcu-grace.svg`, `deadlock-cycle.svg`. Visual slides: 13 of 18 (72%).

## Lesson deck

## Slide 1 — TITLE
Title: Concurrency & Synchronization · Subtitle: from count++ to qspinlock, futex and RCU
Fields: placeholders from §3.4 (never invented)
Notes: SAY two threads, one counter, wrong answer · TIME 30

## Slide 2 — SECTION
Eyebrow: Module 03 · Numeral 03 · Why: every kernel structure is shared by many CPUs; one wrong ordering corrupts it silently
Pills: memory ordering · locks & futex · RCU · deadlock
Notes: dependencies M01, M02; used by M04, M05, M07 · TIME 30

## Slide 3 — AGENDA
Rows: count++ · x86 reordering · spin or sleep · futex · RCU + deadlock (row 1 current)
TIME 20

## Slide 4 — TERMINAL_DEMO
Title: count++ on four threads loses most increments
Terminal: real lab 01 output from aos-lab (race / mutex / atomic)
Takeaway (caption): captured on the shared 8-vCPU VM; numbers vary
TIME 90

## Slide 5 — LAYER_STACK
Title: Every lock is an atomic instruction plus a waiting policy
Bands: User (role-1) pthread_mutex, cond, sem_t, Go chan · boundary "futex() syscall" · Kernel (role-2) spinlock_t, mutex, semaphore, RCU, futex buckets · Hardware (role-3) lock cmpxchg, lock xadd, xchg, store buffer
Motion: bands rise d1–d3, boundary fade
TIME 60

## Slide 6 — CONCEPT_DIAGRAM
Title: x86 lets a store wait in the buffer while a later load runs
Diagram: assets/store-buffer.svg (CPU0/CPU1 code → store buffers → memory, hot dashed loads)
Callouts: ① stores buffered ② loads read 0 ③ drain later
Takeaway: result 0/0 impossible under SC, legal on TSO
TIME 90

## Slide 7 — TERMINAL_DEMO
Title: A million runs: 0/0 appears, until a full fence
Terminal: real lab 05 output, relaxed vs fence (C) + Rust relaxed
TIME 90

## Slide 8 — TWO_COLUMN_COMPARE
Title: Spin when the wait is short and you may not sleep
Rows (5): waiter behaviour · preemption · may sleep · IRQ context · owner field
TIME 75

## Slide 9 — CODE_WALKTHROUGH
Title: A spinlock is one acquire CAS and one release store
Source: linux/include/asm-generic/qspinlock.h · queued_spin_lock()/queued_spin_unlock() · v6.18.63 · L107-128
Callouts: ① lock cmpxchg ② pending → MCS queue ③ release byte store
Motion: one fragment per highlighted group
TIME 120

## Slide 10 — CODE_WALKTHROUGH
Title: mutex_lock() is the same CAS, storing the owner task
Source: linux/kernel/locking/mutex.c · __mutex_trylock_fast() L150, mutex_lock() L269 · v6.18.63
Callouts: ① owner = task_struct * + 3 flags ② unlocked = 0 ③ optimistic spin then wait_list
TIME 120

## Slide 11 — CONCEPT_DIAGRAM
Title: A futex enters the kernel only when someone must wait
Diagram: assets/futex-split.svg (user band: lock / word / unlock; syscall boundary; kernel band: futex_wait_setup / futex_wake)
Callouts ①–⑤ in the SVG
TIME 90

## Slide 12 — CODE_WALKTHROUGH
Title: The kernel re-reads the word under the bucket lock
Source: linux/kernel/futex/waitwake.c · futex_wait_setup() · v6.18.63 · L630-665
Callouts: ① waiters++ + hb lock ② value changed → EAGAIN ③ state before queue
TIME 120

## Slide 13 — TERMINAL_DEMO
Title: One thread: zero futex calls. Four threads: only on contention
Terminal: real lab 04 output (strace -c -f, program counters)
TIME 90

## Slide 14 — CONCEPT_DIAGRAM
Title: RCU readers take no lock; the writer waits a grace period
Diagram: assets/rcu-grace.svg (3 CPU lanes, writer lane, quiescent dots, grace-period band)
Source: kernel/rcu/tree.c synchronize_rcu() L3341; openbsd kern_smr.c smr_grace_wait() L146
TIME 120

## Slide 15 — CONCEPT_DIAGRAM
Title: AB-BA: a cycle in the wait-for graph stops both threads
Diagram: assets/deadlock-cycle.svg · Callouts: Coffman conditions ①②③
TIME 90

## Slide 16 — QUIZ
Question: Which reordering does x86-TSO allow? A store→store · B load→load · C store→later load · D none
TIME 45

## Slide 17 — QUOTE / DEFINITION (answer)
Answer C · Quote: a full barrier drains the store buffer · Source: barrier.h __smp_mb() L53
TIME 60

## Slide 18 — SUMMARY
① atomicity ≠ ordering ② lock = acquire CAS + waiting policy ③ futex / RCU / ordering
Next: Module 04 · Memory Management
TIME 30

## Lab decks (7 slides each: SECTION/goal → Setup → Steps → Expected → Observe → Pitfalls → Extension)

| Deck | Lab | Expected output source |
|---|---|---|
| `labs/01-data-race.{en,fa}.html` | 03.1 data race → TSan → mutex → atomic → perf stat | aos-lab capture |
| `labs/02-producer-consumer.{en,fa}.html` | 03.2 semaphores → condvars → Go channel | aos-lab capture |
| `labs/03-readers-writers.{en,fa}.html` | 03.3 rwlock writer starvation | aos-lab capture |
| `labs/04-futex-mutex.{en,fa}.html` | 03.4 raw futex mutex + strace/bpftrace | aos-lab capture |
| `labs/05-litmus-sb.{en,fa}.html` | 03.5 store-buffering litmus, C11 + Rust | aos-lab capture |
| `labs/06-deadlock.{en,fa}.html` | 03.6 AB-BA deadlock, gdb, TSan, helgrind; lockdep (VM-with-lockdep kernel) | aos-lab capture; lockdep part UNVERIFIED |
