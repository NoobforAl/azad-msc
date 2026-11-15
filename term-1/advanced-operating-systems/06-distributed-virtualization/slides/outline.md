# 06 · Distributed OS & Virtualization — slide outlines

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced OS (user = teal, kernel = amber, hardware = violet, data = green).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 18 |
| Lab 06.1 Lamport & vector clocks | [`labs/01-lamport-vector-clocks.en.html`](labs/01-lamport-vector-clocks.en.html) | [`labs/01-lamport-vector-clocks.fa.html`](labs/01-lamport-vector-clocks.fa.html) | 7 |
| Lab 06.2 RPC retries & idempotency | [`labs/02-rpc-idempotency.en.html`](labs/02-rpc-idempotency.en.html) | [`labs/02-rpc-idempotency.fa.html`](labs/02-rpc-idempotency.fa.html) | 7 |
| Lab 06.3 Mini container | [`labs/03-mini-container.en.html`](labs/03-mini-container.en.html) | [`labs/03-mini-container.fa.html`](labs/03-mini-container.fa.html) | 7 |
| Lab 06.4 KVM client | [`labs/04-kvm-client.en.html`](labs/04-kvm-client.en.html) | [`labs/04-kvm-client.fa.html`](labs/04-kvm-client.fa.html) | 7 |
| Lab 06.5 VM-exit cost | [`labs/05-vmexit-cost.en.html`](labs/05-vmexit-cost.en.html) | [`labs/05-vmexit-cost.fa.html`](labs/05-vmexit-cost.fa.html) | 7 |

Lab decks are generated: `python _shared/tools/labdeck.py term-1/advanced-operating-systems/06-distributed-virtualization/slides/labs.content.py`. Open decks through `python -m http.server` at the repo root. `S` = speaker notes, `?print-pdf` = PDF export.

SVGs in `assets/` are shared by EN and FA and use English/identifier labels only: `rpc-retry.svg`, `clocks.svg`, `vm-vs-container.svg`.

---

## Lesson deck

## Slide 1 — TITLE
Title: Many machines, one machine many times · Fields: placeholders from §3.4

## Slide 2 — SECTION
Eyebrow: Module 06 · Title: Distributed OS & Virtualization · Why: networks lose replies and clocks drift; hypervisors and containers decide what a process can see and use · Pills: RPC · clocks / KVM · VT-x / namespaces · cgroups · Notes: dependencies M01, M02, M04

## Slide 3 — AGENDA
Five questions → five labs (current = 1)

## Slide 4 — SEQUENCE
Title: A timeout cannot tell a lost request from a lost reply
Diagram: `assets/rpc-retry.svg`: Client (role-1) / Server (role-4) lifelines, ① request ② lost reply ③ timeout (role-2) ④ retry with same id, BUG (no dedup) / FIX (reply cache) labels, ⑤ reply
Takeaway: Lab 06.2 real numbers (no dedup vs reply cache)
Source: fs/nfsd/nfscache.c · nfsd_cache_lookup() (notes)

## Slide 5 — CONCEPT_DIAGRAM
Title: Lamport order is consistent with causality, not equal to it
Diagram: `assets/clocks.svg`, 3 process lines, events with L and V, highlighted pair a ∥ g with L(a) < L(g)
Takeaway: a → b ⇔ V(a) ≤ V(b), V(a) ≠ V(b)

## Slide 6 — BENTO
f+1 (role-4) / 2f+1 (role-2) / 3f+1 (role-3) · Takeaway: Raft 5 nodes, FLP

## Slide 7 — LAYER_STACK
guest apps ring 3 (role-1) → guest kernel ring 0 (role-2) → boundary "VMX non-root ↕ VM entry / VM exit" → host kernel + KVM (role-2) → CPU VT-x/EPT (role-3)

## Slide 8 — TERMINAL_DEMO
Title: A CPUID exit costs four guest syscalls · real `vmexit-cost` output from the WSL2 VM (Hyper-V), highlighted cpuid line · caption names the environment

## Slide 9 — FLOW_TIMELINE
open /dev/kvm → KVM_CREATE_VM → SET_USER_MEMORY_REGION → KVM_CREATE_VCPU → mmap kvm_run → KVM_RUN loop (fragments move the highlight)

## Slide 10 — CODE_WALKTHROUGH
`linux/arch/x86/kvm/vmx/vmx.c · v6.18.63`: three rows of `kvm_vmx_exit_handlers[]` (L6092) + `handle_io()` (L5366) · 4 highlight fragments ↔ 4 callouts

## Slide 11 — CODE_WALKTHROUGH
`linux/arch/x86/kvm/x86.c · emulator_pio_in_out()`: in-kernel bus first, `userspace_io:` fills `kvm_run`, `return 0` · 4 callouts

## Slide 12 — CONCEPT_DIAGRAM
Title: A container moves the isolation boundary up to the syscalls · `assets/vm-vs-container.svg`

## Slide 13 — CODE_WALKTHROUGH
`linux/kernel/pid_namespace.c · copy_pid_ns()` L175 · 3 callouts (share / EINVAL / child of old ns → pid_ns_for_children)

## Slide 14 — TERMINAL_DEMO
Real `minictr.sh` + `demo.sh` output from aos-lab: PID 1, hostname, `0::/`, lo only, fork failures, OOM kill, host `memory.events`

## Slide 15 — TWO_COLUMN_COMPARE
Linux (KVM in-kernel bus, namespaces, cgroup v2, seccomp) vs OpenBSD (vmm → vmd for every I/O exit, chroot, setrlimit, pledge/unveil)

## Slide 16 — QUIZ
V(a) = [3,1,0], V(b) = [2,2,0]: relation? (A a→b, B b→a, C a∥b, D depends on Lamport time)

## Slide 17 — DEFINITION (answer)
Answer C: neither vector ≤ the other

## Slide 18 — SUMMARY
① request IDs / vectors / 2f+1 ② KVM = VT-x behind three fds, exits are the cost ③ container = namespaces + cgroups on one kernel · Next: Module 07

---

## Lab decks (generated, 7 slides each)

Every lab deck: SECTION (goal, where it runs) → Setup (4 cards) → Steps (TERMINAL_DEMO, the README commands) → Expected output (real run; caption names the machine, or the EXPECTED marker) → What to observe (3) → Common pitfalls (3, symptom → fix) → Extension (no solution).

| Lab | Runs on | Expected-output source |
|---|---|---|
| 06.1 Lamport & vector clocks | aos-lab, Go | real run, `captured` set |
| 06.2 RPC retries & idempotency | aos-lab, Go | real run, `captured` set |
| 06.3 Mini container | aos-lab, VM only | real run, `captured` set |
| 06.4 KVM client | KVM host / nested VM | only the no-`/dev/kvm` path is real; KVM run is EXPECTED (UNVERIFIED) |
| 06.5 VM-exit cost | any x86-64 guest | real run on aos-lab, `captured` set; `perf kvm stat` part UNVERIFIED |
