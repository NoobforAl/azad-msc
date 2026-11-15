# Module 06 notes — index

> Module 06 · Distributed OS & Virtualization · pins: Linux **v6.18.63**, OpenBSD **`8cada8c`** · Farsi: [`INDEX.fa.md`](INDEX.fa.md) · Lesson: [`../lesson.en.md`](../lesson.en.md)

Read in order. Notes 01–05 are the distributed half (theory + Go labs); notes 06–08 are the virtualization half (kernel code + C labs). Each note has the same 7 sections: summary, explanation, diagram, worked example, pitfalls, exam points, links.

| # | Note | One line | Lesson | Lab | Time |
|---|---|---|---|---|---|
| 01 | [RPC semantics](01-rpc-semantics.en.md) | What a remote call can promise when messages are lost: at-most-once, at-least-once, and duplicate filtering for an exactly-once *effect* | §4.1 | [02-rpc-idempotency](../labs/02-rpc-idempotency/) | 40 min |
| 02 | [Lamport & vector clocks](02-lamport-vector-clocks.en.md) | Ordering events without a shared clock: happened-before, Lamport timestamps, vector clocks that detect concurrency | §4.2 | [01-lamport-vector-clocks](../labs/01-lamport-vector-clocks/) | 50 min |
| 03 | [Clock sync: NTP, PTP, chrony](03-clock-sync-ntp-ptp.en.md) | How real clocks are kept close: offset/delay estimation, slewing via `adjtimex`, hardware timestamps | §4.3 | — | 35 min |
| 04 | [Distributed deadlock & snapshots](04-distributed-deadlock-snapshots.en.md) | Wait-for graphs across machines, edge chasing, phantom deadlocks, the Chandy–Lamport consistent snapshot | §4.4 | — | 40 min |
| 05 | [Fault tolerance & replication](05-fault-tolerance-replication.en.md) | Failure models, f+1 / 2f+1 / 3f+1, primary-backup vs state-machine replication, quorums, a Raft preview | §4.5 | — | 45 min |
| 06 | [Hypervisors: trap-and-emulate, VT-x, EPT](06-hypervisors-vtx-ept.en.md) | Popek–Goldberg, why x86 needed VT-x, root/non-root mode, VMCS, VM exits, the 24-reference EPT walk | §4.6 | [05-vmexit-cost](../labs/05-vmexit-cost/) | 45 min |
| 07 | [KVM architecture](07-kvm-architecture.en.md) | `/dev/kvm` → VM fd → vCPU fd, `KVM_RUN` loop, in-kernel vs user-space exits; OpenBSD vmm/vmd contrast | §4.7 | [04-kvm-client](../labs/04-kvm-client/) | 50 min |
| 08 | [Containers = namespaces + cgroups v2](08-containers-namespaces-cgroups.en.md) | `nsproxy`, the 8 namespaces, the PID-namespace fork rule, cgroup v2 limits; OpenBSD pledge/unveil contrast | §4.8 | [03-mini-container](../labs/03-mini-container/) | 50 min |

**Total:** about 6 h of reading, before the labs.

Suggested path:

1. 02 → 01 → 04 → 05 → 03 if you like theory first (clocks are needed to define consistent cuts in 04).
2. 06 → 07 → 08 if you start from the kernel side; 06 is a prerequisite for 07.
3. Do each lab right after its note; the quiz ([`../quiz.en.md`](../quiz.en.md)) cites the notes per question.

Kernel code for 06–08 is collected in [`../kernel-walkthrough.en.md`](../kernel-walkthrough.en.md).
