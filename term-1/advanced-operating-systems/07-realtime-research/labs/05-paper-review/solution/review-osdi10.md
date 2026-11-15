# Paper review — An Analysis of Linux Scalability to Many Cores

**Venue / year:** OSDI '10, Vancouver · **Authors:** S. Boyd-Wickizer, A. T. Clements, Y. Mao, A. Pesterev, M. F. Kaashoek, R. Morris, N. Zeldovich (MIT CSAIL) · **Link:** <https://www.usenix.org/conference/osdi10/analysis-linux-scalability-many-cores>
**Reviewer:** model solution, 2026-11-15 · all quotes checked against the PDF text

## Pass 1 — the five Cs
- **Category:** measurement + analysis of an existing system, with targeted fixes.
- **Context:** the 2008–2010 argument that traditional kernels won't scale and need new designs (Barrelfish, Corey, fos — all cited in the intro).
- **Correctness:** reasonable but scoped: in-memory tmpfs "to avoid disk bottlenecks", synthetic drivers "with realism a secondary consideration" (their words).
- **Contributions:** 16 scalability fixes to Linux 2.6.35-rc5 ("PK"), the *sloppy counter* technique, application changes, MOSBENCH as a public benchmark.
- **Clarity:** very good; one table maps each bottleneck to its fix.

## 1. Problem
Do traditional monolithic kernels limit application scaling on many cores? On a 48-core machine, "except for gmake, all applications trigger scalability bottlenecks inside a recent Linux kernel" (e.g. Psearchy's kernel time grows from 1.9 % at one core to 23 % at 48).

## 2. Key insight
Most kernel bottlenecks are **shared cache lines**, not the kernel's architecture: shared counters and locks touched on every operation. They can be removed with standard techniques (per-core data, finer locks, lock-free) plus one new idea, sloppy counters.

## 3. Mechanism
- **Sloppy counters**: one logical counter = a shared central counter + per-core counts of spare references; a core usually updates only its local count, keeping the invariant "sum of per-core counters + references in use = central counter". Used for dentry, vfsmount, `dst_entry` and protocol counters.
- Per-core mount-table caches, per-core open-file lists per superblock, finer dentry locking, avoiding the per-inode mutex in `lseek`, per-core accept backlog queues for listening sockets (with NIC flow steering), super-page fault locking.
- Total: 3002 lines of kernel changes.

## 4. Evaluation
| Hardware | Kernel | Workloads | Baseline | Metric | Variance |
|---|---|---|---|---|---|
| 48 cores: eight 6-core AMD Opteron 8431, 2.4 GHz, 8 GB DRAM per chip | 2.6.35-rc5 stock vs PK | Exim, memcached, Apache, PostgreSQL, gmake, Psearchy, Metis MapReduce (MOSBENCH), tmpfs | stock kernel | throughput per core vs number of cores | per-core curves; few explicit error bars |

It tests the claim at its stated scope (48 cores, in-memory). It cannot test "many" beyond 48.

## 5. Limits / threats to validity
- tmpfs and synthetic loads remove I/O; real deployments may bottleneck elsewhere (the paper admits this in §7).
- 48 cores in 2010; "different applications or more cores are certain to reveal more bottlenecks" (§6, their words).
- The fixes are point fixes; the paper doesn't show the kernel *stays* scalable as it evolves.

## 6. Today (Linux v6.18.63)
- `struct dentry` now has `struct lockref d_lockref` (`include/linux/dcache.h` L113; `lib/lockref.c`): lock + refcount updated together with one `cmpxchg`. A different fix than sloppy counters for the same dentry-refcount bottleneck.
- Per-CPU counting is generic: `lib/percpu_counter.c`. Path lookup uses RCU-walk (Module 05).
- Whether PK's exact patches were merged: `UNVERIFIED` here (needs history).

## 7. Verdict + question
**Accept.** It turned a design debate into measurements and gave a reusable method (find the shared line, make it per-core).
Question: how many of the 16 fixes would be needed again for 2026 chiplet CPUs with 128+ cores, where cross-die cache-line transfer is much costlier than in a 2010 Opteron box?
