# 06 — Quiz: Distributed OS & Virtualization

> 15 questions: 6 conceptual (Q1–Q6), 4 read-the-code-or-output (Q7–Q10), 5 debug/design (Q11–Q15), plus 3 oral-exam questions. Answers are at the end. Farsi: [`quiz.fa.md`](quiz.fa.md)

## Questions

### Conceptual

**Q1.** A payment service exposes `Charge(card, amount)`. Clients retry after a 2 s timeout. (a) Which RPC semantics do they get by default? (b) Name the two ingredients needed for an exactly-once *effect*. (c) Why can't the client alone provide it?

**Q2.** Lamport clocks guarantee a → b ⇒ L(a) < L(b). Give a concrete two-process example where L(a) < L(b) but a and b are concurrent.

**Q3.** Three processes. V(a) = [3, 1, 0], V(b) = [2, 2, 0], V(c) = [3, 2, 1]. For each pair (a,b), (a,c), (b,c), say whether it is →, ←, or ∥.

**Q4.** NTP client: t1 = 10.000 s, t2 = 10.030 s, t3 = 10.031 s, t4 = 10.021 s. (a) Compute the offset θ and delay δ. (b) What is the worst-case error of θ, and which assumption causes it? (c) Should a program measure a timeout with `CLOCK_REALTIME` or `CLOCK_MONOTONIC`? Why?

**Q5.** In the Chandy–Lamport snapshot, process P receives a marker on channel c for the first time. List exactly what P does. Why does the algorithm require FIFO channels?

**Q6.** Popek & Goldberg define when trap-and-emulate works. (a) State the condition. (b) Why did classic x86 fail it (one example)? (c) Which two hardware features of VT-x make trap-and-emulate and fast memory virtualization possible?

### Read the code / output

**Q7.** From `virt/kvm/kvm_main.c · kvm_vcpu_ioctl()` (v6.18.63):

```c
	if (mutex_lock_killable(&vcpu->mutex))
		return -EINTR;
	switch (ioctl) {
	case KVM_RUN: {
		/* ... */
		oldpid = vcpu->pid;
		if (unlikely(oldpid != task_pid(current))) {
			/* The thread running this VCPU changed. */
```

(a) What happens if two threads of a VMM call `KVM_RUN` on the same vCPU fd at once? (b) Why does KVM care which host thread runs a vCPU?

**Q8.** From `kernel/pid_namespace.c · copy_pid_ns()`:

```c
	if (!(flags & CLONE_NEWPID))
		return get_pid_ns(old_ns);
	if (task_active_pid_ns(current) != old_ns)
		return ERR_PTR(-EINVAL);
	return create_pid_namespace(user_ns, old_ns);
```

and `kernel/nsproxy.c` stores the result in `new_nsp->pid_ns_for_children`. Explain why `sudo unshare --pid sh -c 'echo $$'` does **not** print `1`, and what `--fork` changes.

**Q9.** Lab 06.2 printed, for the same 20 deposits of 10 against a server that delays 30% of replies past the client's timeout:

```
== A: retries=0 dedup=false (at-most-once)
logical deposits=20  rpcs sent=20  retries=0  gave up=8
expected balance=200  server balance=200  executions=20
== B: retries=5 dedup=false (at-least-once)
logical deposits=20  rpcs sent=29  retries=9  gave up=0
expected balance=200  server balance=290  executions=29
```

(a) In A, the client "gave up" on 8 deposits, yet the balance is correct. Explain. (b) In B, explain 290. (c) What would `executions` be in run C (dedup on)?

**Q10.** Lab 06.5 inside a Hyper-V guest printed:

```
add (stays on the CPU)            0.2 ns/op
getppid syscall (guest)          96.4 ns/op
cpuid leaf 0 (VM exit)          383.5 ns/op
```

(a) Why is the syscall not a VM exit? (b) What does the CPU and hypervisor do during the 383 ns? (c) Name one guest workload for which this number matters a lot and one for which it does not.

### Debug / design

**Q11.** Your mini container uses `pivot_root . .oldroot` and fails with `pivot_root: Invalid argument`. Give two causes the kernel checks for and the fix for each.

**Q12.** You set `memory.max=64M` on a group. A process inside calls `malloc(1 GiB)` and succeeds, and then runs fine for minutes. Later another process in the same group is OOM-killed while touching only 10 MiB. Explain both observations. Which file tells you what happened?

**Q13.** Design: a 5-node Raft cluster stores a key-value map. (a) How many node crashes can it survive while still accepting writes? (b) Nodes {1,2} are partitioned from {3,4,5}; node 1 was leader. What happens on each side? (c) Why not use 4 nodes instead of 5?

**Q14.** Your KVM client prints nothing and exits with `KVM_EXIT_FAIL_ENTRY: hardware_entry_failure_reason = 0x80000021`. List what you would check in your `kvm_sregs`/`kvm_regs` setup and why the failure happens at *entry*, not in the guest code.

**Q15.** Three database sites. At site A, T1 waits for T2; at site B, T2 waits for T3; at site C, T3 waits for T1. (a) Why can no site detect this deadlock alone? (b) Show the Chandy–Misra–Haas probe messages that detect it, starting from T1. (c) A centralized detector once reported a cycle T1→T2→T1 that never existed. How can that happen, and what is it called?

## Oral-exam questions

**O1.** "Containers are as secure as VMs if you use all namespaces." Argue against this with the notion of an isolation boundary. What do gVisor, Kata Containers, and Firecracker each change?

**O2.** Vector clocks need one entry per process. How do real systems (Dynamo-style stores, CRDTs, Spanner, CockroachDB) avoid or bound that cost? Mention version vectors, dotted version vectors, and hybrid logical clocks.

**O3.** OpenBSD has no namespaces or cgroups. Is that a weakness or a design choice? Compare `pledge`/`unveil` with seccomp + namespaces: who decides the policy, when, and what happens on violation.

---

## Answers

**A1.** (a) At-least-once: a timeout followed by a retry can execute the charge twice, because the first request may have run and only the reply was lost. (b) A unique request ID per logical operation, reused on every retry, and a server-side duplicate filter (reply cache) keyed by that ID that returns the stored reply instead of executing again. This is at-least-once delivery plus deduplication. (c) The client cannot distinguish "request lost" from "reply lost". Only the server knows whether it executed. → note 01, Lab 06.2.

**A2.** P1: event a = local event, L = 1. P2: three local events b1, b2, b3 with L = 1, 2, 3. No messages are exchanged. Then L(a) = 1 < L(b3) = 3, but a ∥ b3. Lab 06.1's analyzer counts exactly such pairs ("pairs with L(a) < L(b) that are concurrent"). → note 02.

**A3.** (a,b): a has 3 > 2 in entry 0, b has 2 > 1 in entry 1, so neither ≤ the other: **a ∥ b**. (a,c): [3,1,0] ≤ [3,2,1] and not equal: **a → c**. (b,c): [2,2,0] ≤ [3,2,1]: **b → c**. → note 02.

**A4.** (a) θ = ((10.030 − 10.000) + (10.031 − 10.021)) / 2 = (0.030 + 0.010) / 2 = **0.020 s** (the client is 20 ms behind). δ = (10.021 − 10.000) − (10.031 − 10.030) = 0.021 − 0.001 = **0.020 s**. (b) |error| ≤ δ/2 = 10 ms; it comes from assuming the outbound and return paths take equal time. (c) `CLOCK_MONOTONIC`: it never jumps when NTP steps the wall clock or an admin sets the time; `CLOCK_REALTIME` can go backwards. → note 03.

**A5.** P records its own local state; records the state of channel c as **empty**; sends a marker on every outgoing channel before sending any other message; from then on, for every other incoming channel, records the messages that arrive until a marker arrives on that channel. FIFO is required so that the marker separates "sent before the snapshot" from "sent after": with reordering, a post-snapshot message could overtake the marker and be recorded as received without its send being in the cut (inconsistent cut). → note 04.

**A6.** (a) Every sensitive instruction (one that reads or changes machine state that the VMM must control) must be privileged (trap when executed in user mode). Then the VMM can run the guest deprivileged and emulate every trap. (b) Example: `popf` in ring 3 silently ignores changes to the interrupt flag instead of trapping; `sgdt`/`sidt`/`smsw` read privileged registers without trapping. Robin & Irvine (2000) list 17 such instructions. (c) VMX root/non-root modes with a VMCS that selects which events cause VM exits (so the guest kernel can run in its own ring 0), and EPT (a second-level page table, so guest page-table updates don't need shadow page tables and exits). → note 06.

**A7.** (a) The second thread blocks in `mutex_lock_killable(&vcpu->mutex)` until the first returns from `KVM_RUN` (or gets `-EINTR` if killed). A vCPU's state can only be loaded on one physical CPU at a time. (b) KVM keeps `vcpu->pid` so it can find the thread that runs a given vCPU: directed yield (`kvm_vcpu_on_spin` boosting the lock holder's vCPU thread), sending signals/IPIs to kick it, and tools like `perf kvm` that map threads to vCPUs. On a thread change the arch hook `kvm_arch_vcpu_run_pid_change()` runs. → note 07, walkthrough §1.2.

**A8.** `unshare()` creates the new PID namespace but stores it in `pid_ns_for_children`. The calling process's PID cannot change (other processes already know it), so `sh` stays in the old namespace and prints its host PID. With `--fork`, `unshare(1)` forks after the syscall; the child is the first process created in the new namespace and gets PID 1. A second `unshare(CLONE_NEWPID)` before forking fails with `EINVAL` (`task_active_pid_ns(current) != old_ns`). → note 08, walkthrough §3.3.

**A9.** (a) "Gave up" means "no reply in time", not "not executed". The server executed all 20 (`executions=20`); 8 replies were just late. The client is left not knowing the outcome; that is at-most-once. (b) 9 retries were sent; without deduplication each retry executed again: 20 + 9 = 29 executions × 10 = 290. (c) 20: retries hit the reply cache and are answered without executing. (The real run C printed `executions=20`, balance 200.) → note 01.

**A10.** (a) In VMX non-root mode the guest kernel is in its own ring 0; `syscall` switches guest ring 3 → guest ring 0 without leaving the guest, so it costs the same as on bare metal (plus mitigations). (b) The CPU saves guest state into the VMCS, loads host state and jumps to the hypervisor (VM exit). The hypervisor reads the exit reason, emulates `cpuid` (fills EAX–EDX, possibly filtering features), advances RIP and does VM entry back. Here the hypervisor is Hyper-V (the signature printed `Microsoft Hv`), not KVM. (c) Matters: workloads that exit often, e.g. emulated port I/O devices, frequent timer programming or MSR access, guests that call `cpuid` in hot loops (some JITs/serialization code). Doesn't matter: CPU-bound compute in user space, which never exits. → note 06, Lab 06.5.

**A11.** Typical `EINVAL` causes from `pivot_root(2)`: (1) `new_root` is not a mount point: fix with `mount --bind rootfs rootfs` first. (2) The current root or `new_root`'s parent mount has **shared** propagation (systemd makes `/` shared): fix with `mount --make-rprivate /` inside the new mount namespace. Others: `put_old` is not underneath `new_root`, or the call isn't in a mount namespace where `/` is a mount point (e.g. running from an initramfs rootfs). → note 08, Lab 06.3.

**A12.** `malloc(1 GiB)` only reserves virtual address space; memcg charges pages when they are faulted in (Module 04: demand paging). The process runs fine as long as it does not touch them. The other process is killed because the **group's** total charged memory (page cache, anonymous pages, kernel memory of all members) reached 64 MiB; the memcg OOM killer picks a victim by its own scoring, not necessarily the process that allocated most recently. Check `memory.events` (`max`, `oom`, `oom_kill`), `memory.current`, `memory.stat`, and `dmesg` (`Memory cgroup out of memory: Killed process ...`). → note 08.

**A13.** (a) A write commits when a majority (3 of 5) stores it, so it survives 2 crashes. (b) Side {3,4,5} has a majority: after an election timeout one of them becomes leader in a higher term and accepts writes. Side {1,2}: node 1 may still think it is leader but cannot commit anything (no majority); its uncommitted entries are overwritten when the partition heals and it sees the higher term. (c) 4 nodes need a majority of 3, so they still tolerate only 1 crash, while costing an extra replica and creating more ways to split 2–2. Odd sizes are standard. → note 05.

**A14.** `0x80000021` = bit 31 (entry failure) + basic reason 33: "VM-entry failure due to invalid guest state". The CPU checks the guest-state area of the VMCS *before* running any guest instruction, so the guest code is never reached. Check: `cs.base`/`cs.selector` consistent for real mode (base = selector × 16), segment limits and access rights left as `KVM_GET_SREGS` returned them, `cr0` without PE for real mode (or a full GDT and PE for protected mode), `rflags` bit 1 set (`0x2`), `rip` inside the memory slot. Get the sregs first and change only what you need, as the client does. → note 07, Lab 06.4.

**A15.** (a) Each site sees one edge of the wait-for graph; the cycle exists only in the union. (b) T1 is blocked waiting for T2, so A sends probe (1, 1, 2) to the site of T2. T2 is blocked on T3: B forwards (1, 2, 3). T3 is blocked on T1: C forwards (1, 3, 1). The probe arrives at T1 with initiator = 1, so T1 declares a deadlock (and e.g. aborts itself). Probes travel only along wait-for edges of blocked processes. (c) Phantom deadlock: the coordinator combined edges reported at different times. E.g. T1 released the resource and T2's wait ended (edge T2→T1 removed), but the removal message arrived after a newer edge T1→T2 was reported. The union of out-of-date local graphs is not a consistent cut. Fix: collect edges in a consistent snapshot (Chandy–Lamport) or use edge chasing. → note 04.

**O1 (hints).** A container's boundary is the host kernel's syscall interface (383 x86-64 syscall entries in `syscall_64.tbl` v6.18.63, plus `/proc`, `/sys`, ioctls); one kernel bug reachable from inside breaks all containers. A VM's boundary is the virtual hardware interface (exits, virtual devices), which is much narrower. gVisor puts a user-space kernel (Sentry) between the container and the host kernel; Kata runs each container in a lightweight VM; Firecracker is a minimal KVM VMM (few virtio devices, in Rust) for microVMs. Trade-off: boundary width vs startup time and density.

**O2 (hints).** Version vectors track replicas (servers), not clients, so N is small; dotted version vectors fix false conflicts when many clients write through one server. CRDTs often use vector-like metadata with pruning. Spanner avoids logical clocks by bounding physical clock error (TrueTime) and waiting it out. Hybrid logical clocks (Kulkarni et al. 2014) combine physical time with a Lamport-style counter: constant size, close to wall clock, and still respect causality (like Lamport, not like vectors). CockroachDB uses HLC.

**O3 (hints).** Design choice: OpenBSD prefers small, auditable mechanisms that a program applies to itself after initialization (pledge: syscall groups; unveil: paths). Policy is written by the program's author, it can only shrink, and violation kills the process (`SIGABRT`). Linux namespaces/cgroups are imposed from outside by a container runtime on unmodified programs, and seccomp-BPF policies are programmable but complex. OpenBSD gives no resource accounting per group and no separate views of PIDs/network; for that it uses separate users, `chroot`, privilege separation, and `vmm(4)` VMs.
