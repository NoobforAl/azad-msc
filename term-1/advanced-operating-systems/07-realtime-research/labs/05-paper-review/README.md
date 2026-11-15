# Lab 07.5 — Read two OS papers and write one-page reviews

**Goal:** read two classic Linux papers with the three-pass method and write a one-page review of each that maps the paper onto the v6.18.63 source.

Runs on: your laptop (reading) + the repo's source checkout (`git grep`). No VM needed.

## Papers (both confirmed by web search on 2026-11-15)

| # | Paper | Venue | Link |
|---|---|---|---|
| A | Boyd-Wickizer, Clements, Mao, Pesterev, Kaashoek, Morris, Zeldovich. *An Analysis of Linux Scalability to Many Cores* | OSDI '10 | <https://www.usenix.org/conference/osdi10/analysis-linux-scalability-many-cores> · PDF <https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Boyd-Wickizer.pdf> |
| B | Lozi, Lepers, Funston, Gaud, Quéma, Fedorova. *The Linux Scheduler: a Decade of Wasted Cores* | EuroSys '16 | <https://people.ece.ubc.ca/~sasha/papers/eurosys16-final29.pdf> · code <https://github.com/jplozi/wastedcores> |

Method reference: S. Keshav, "How to Read a Paper", ACM SIGCOMM CCR 37(3), 2007 (doi:10.1145/1273445.1273458) and [note 06](../../notes/06-reading-os-papers.en.md).

## Steps

```bash
# 0. Get the PDFs (any PDF viewer works; pdftotext helps grep)
curl -sLo osdi10.pdf  https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Boyd-Wickizer.pdf
curl -sLo wasted.pdf  https://people.ece.ubc.ca/~sasha/papers/eurosys16-final29.pdf
pdftotext osdi10.pdf - | head -20          # abstract

# 1. Pass 1 (10 min each): title, abstract, headings, conclusion -> fill "five Cs" in a copy of the template
cp review-template.md review-A.md; cp review-template.md review-B.md

# 2. Pass 2 (1 h each): figures + axes, baselines, workloads -> sections 1-5 of the template

# 3. Map onto today's kernel (from the repo root)
cd _shared/sources/linux
git grep -n "^static int sched_balance_rq" kernel/sched/fair.c         # paper B: load balancer
git grep -n "^static bool update_sd_pick_busiest" kernel/sched/fair.c  # paper B: busiest-group choice
git grep -n "struct lockref d_lockref" include/linux/dcache.h          # paper A: dentry refcount today
ls lib/percpu_counter.c lib/lockref.c                                   # paper A: per-CPU counting today
```

## Expected output (the source-mapping step)

Captured on the repo checkout (Linux v6.18.63), 2026-11-15:

```text
$ git grep -n "^static int sched_balance_rq" kernel/sched/fair.c
kernel/sched/fair.c:12052:static int sched_balance_rq(int this_cpu, struct rq *this_rq,
$ git grep -n "^static bool update_sd_pick_busiest" kernel/sched/fair.c
kernel/sched/fair.c:10740:static bool update_sd_pick_busiest(struct lb_env *env,
$ git grep -n "struct lockref d_lockref" include/linux/dcache.h
include/linux/dcache.h:113:	struct lockref d_lockref;	/* per-dentry lock and refcount
$ ls lib/percpu_counter.c lib/lockref.c
lib/lockref.c  lib/percpu_counter.c
```

The reviews themselves have no "expected output": compare yours with [`solution/`](solution/).

## What to observe

- Paper A's abstract states its own limits ("speculative conclusion"); find where §6 narrows the claim.
- Paper B's bugs are in code paths you can still find in v6.18.63, under new names. CFS's pick has been replaced by EEVDF (Module 02), but load balancing across scheduling domains is still the same design.
- Both papers evaluate on large NUMA machines (48 / 64 cores). Ask what changes on today's chiplet CPUs and on an 8-vCPU VM.

## Common pitfalls

| Symptom | Fix |
|---|---|
| Review summarizes the paper section by section | write problem / insight / mechanism in **one sentence each** first |
| "Linux is 138× slower" in the review | that's one corner case in paper B; quote the typical range (13–24 % per the paper's intro) with context |
| Can't find `load_balance()` in v6.18.63 | it isn't there under that name; search `sched_balance_` |
| No question for the authors | you haven't finished pass 2 |

## Extension task

Pick **one** of paper B's four bugs. Using only v6.18.63 source and a VM with `numactl --hardware`, argue in half a page whether that bug can still occur today: point to the exact function and lines that would have to misbehave, and design (do not necessarily run) an experiment with `taskset`, `perf sched` and `mpstat -P ALL 1` that would show it.

Solutions: [`solution/review-osdi10.md`](solution/review-osdi10.md), [`solution/review-wasted-cores.md`](solution/review-wasted-cores.md).
