# Paper review — The Linux Scheduler: a Decade of Wasted Cores

**Venue / year:** EuroSys '16, London · **Authors:** J.-P. Lozi, B. Lepers, J. Funston, F. Gaud, V. Quéma, A. Fedorova · **Link:** <https://people.ece.ubc.ca/~sasha/papers/eurosys16-final29.pdf> · code <https://github.com/jplozi/wastedcores>
**Reviewer:** model solution, 2026-11-15 · all quotes checked against the PDF text

## Pass 1 — the five Cs
- **Category:** bug study + tooling for an existing system (Linux CFS load balancer).
- **Context:** CFS on multi-core NUMA; hierarchical load balancing over scheduling domains/groups; the 2000s view that "scheduling is a solved problem".
- **Correctness:** the invariant "ready threads are scheduled on available cores" is a fair definition of work conservation for throughput workloads (it is deliberately not one for energy or cache affinity).
- **Contributions:** four bugs with root cause and fix; an online *sanity checker* for the invariant; a *visualization* tool; measured impact.
- **Clarity:** good — per-core heat-map figures make each bug visible.

## 1. Problem
Linux sometimes leaves cores idle "for seconds while ready threads are waiting in runqueues"; the paper reports degradations "in the range 13-24% for typical Linux workloads, and reach 138× in some corner cases" (TPC-H on a commercial DB: 14–23 % lower throughput; kernel make: 13 % higher latency).

## 2. Key insight
Load balancing is a hierarchy of heuristics (averages, per-node shortcuts, cached topology) and each heuristic can silently break work conservation; conventional testing doesn't notice because nothing crashes — you need a checker for the **invariant**, not for outputs.

## 3. Mechanism
Four bugs, all in CFS load balancing / wake-up placement (Linux 3.17–4.3):

| Bug | Root cause | Fix |
|---|---|---|
| Group Imbalance | balancer compares **average** group load; one high-load thread (e.g. a single-threaded R process in another autogroup) skews a node's average so idle cores there don't steal | compare the **minimum** load of groups |
| Scheduling Group Construction | groups built from Node 0's perspective; with `taskset` on nodes two hops apart, balancing never migrates between them | build groups from each core's own perspective |
| Overload-on-Wakeup | wake-up optimization in `select_task_rq_fair` only considers cores of the waker's node; if they're busy, the thread wakes on a busy core while other nodes idle | wake on the previous core if idle, else the longest-idle core in the system |
| Missing Scheduling Domains | after disabling and re-enabling a core via `/proc`, a global count of domains is wrong, so balancing between NUMA nodes stops | correct the domain regeneration |

Tools: the sanity checker periodically checks the invariant and records traces; the visualizer plots runqueue sizes and loads per core over time.

## 4. Evaluation
| Hardware | Kernel | Workloads | Baseline | Metric | Variance |
|---|---|---|---|---|---|
| 64-core, eight-node NUMA server | 3.17 – 4.3 | kernel make + R, NAS benchmarks, TPC-H on a commercial DB | same kernel without the fix | completion time, throughput | per-benchmark tables; repeated runs not prominent |

The evaluation tests the claim directly: same machine, same kernel, fix on/off.

## 5. Limits / threats to validity
- One machine topology (8 nodes × 8 cores); impact on 2-socket or chiplet machines is not quantified.
- The invariant ignores energy and cache affinity, which the "optimizations" were trying to protect; some fixes might cost there.
- 138× is a corner case (NAS `lu`, a synchronization-heavy scientific benchmark, under the Missing Scheduling Domains bug), not representative.

## 6. Today (Linux v6.18.63)
- Load balancer entry: `sched_balance_rq()` (`kernel/sched/fair.c` L12052), busiest-group choice `update_sd_pick_busiest()` (L10740) inside `sched_balance_find_src_group()` (L11596).
- Wake-up placement: `select_task_rq_fair()` (L8744), `wake_affine()` (L7574), `select_idle_sibling()` (L7991).
- Task selection is EEVDF now (Module 02), but balancing across `sched_domain`/`sched_group` hierarchies (`kernel/sched/topology.c`) is the same design, so this *class* of bug is still possible. Whether each specific fix was merged: `UNVERIFIED` here (needs a history clone; `git log -S` on a `--filter=blob:none` clone).

## 7. Verdict + question
**Accept.** Concrete, reproducible bugs in the most-used scheduler, plus tools that generalize.
Question: could the sanity checker run permanently in production (as a BPF program on `sched_switch` + idle tracepoints) with negligible overhead, and would it have flagged regressions introduced after 4.3?
