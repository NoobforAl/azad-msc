# Lab 06.5 — What a VM exit costs, seen from inside a guest

**Goal:** measure the price of a VM exit from inside a virtual machine by timing an instruction that always exits (`CPUID`) against one that never leaves the CPU (`add`) and one that stays inside the guest kernel (a syscall).

ARCH-SPECIFIC (x86-64). Runs in any x86-64 **guest** (that is the point): aos-lab, a cloud VM, WSL2. No root.

> **Changed from PLAN.md.** PLAN listed "`perf kvm stat` on a running guest". That needs a KVM *host* with a running guest, and neither the course VM (no `/dev/kvm`, no nesting) nor Docker Desktop's WSL2 VM has KVM, so it could not be run here. The lab now measures exit cost from the guest side (real, reproducible), and `perf kvm stat` moved to the extension, marked **UNVERIFIED**.

## Steps

```bash
cd ~/work/06-distributed-virtualization/05-vmexit-cost
systemd-detect-virt                         # which hypervisor are we under?
grep -m1 -o hypervisor /proc/cpuinfo        # the CPUID "hypervisor present" bit, as a flag
sudo dmesg | grep -i 'hypervisor detected'

gcc -Wall -Wextra -O2 -o vmexit-cost vmexit-cost.c
./vmexit-cost                               # default 200000 iterations
for i in 1 2 3; do ./vmexit-cost 100000 | grep 'cpuid leaf 0'; done   # noise check

# software counters only (no PMU in this guest): the exits are invisible to the guest
perf stat -e task-clock,context-switches ./vmexit-cost 100000
```

## Code

[`vmexit-cost.c`](vmexit-cost.c). Three timed loops with `clock_gettime(CLOCK_MONOTONIC)`:

| Loop | Instruction | Leaves the guest? |
|---|---|---|
| `do_alu()` | `add $1, %reg` | no, not even the CPU pipeline |
| `do_syscall()` | `syscall(SYS_getppid)` | no: guest ring 3 → guest ring 0 inside VMX non-root |
| `do_cpuid(leaf)` | `cpuid` | **yes**: unconditional VM exit on VT-x; the hypervisor emulates it |

Before measuring, it prints CPUID leaf 1 ECX bit 31 (set by every mainstream hypervisor) and the signature at leaf `0x40000000` (`KVMKVMKVM`, `Microsoft Hv`, `VBoxVBoxVBox`, `VMwareVMware`).

On a KVM host the exit lands in `kvm_vmx_exit_handlers[EXIT_REASON_CPUID] = kvm_emulate_cpuid` (`linux/arch/x86/kvm/vmx/vmx.c` L6100 · v6.18.63, [walkthrough §2.1](../../kernel-walkthrough.en.md)). Here the outer hypervisor is Hyper-V, so the handler is Microsoft's.

## Expected output

> Real output, aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15, captured right after a VM reboot with load average ~7–9 from six other agents. The `cpuid` numbers are **extremely** noisy here (a repeat 3 minutes later gave 94–540 µs); the order of magnitude is the finding.

```
$ systemd-detect-virt; grep -m1 -o hypervisor /proc/cpuinfo; sudo dmesg | grep -i 'hypervisor detected'
oracle
hypervisor
[    0.000000] Hypervisor detected: KVM
$ ./vmexit-cost
CPUID.1:ECX bit 31 (hypervisor present) = 1
CPUID.0x40000000 hypervisor signature = "KVMKVMKVM"
add (stays on the CPU)            0.3 ns/op   (20000000 ops)
getppid syscall (guest)         131.1 ns/op   (200000 ops)
cpuid leaf 0 (VM exit)        57792.9 ns/op   (200000 ops)
cpuid leaf 1 (VM exit)        26008.4 ns/op   (200000 ops)
$ for i in 1 2 3; do ./vmexit-cost 100000 | grep 'cpuid leaf 0'; done
cpuid leaf 0 (VM exit)       316054.5 ns/op   (100000 ops)
cpuid leaf 0 (VM exit)        34592.4 ns/op   (100000 ops)
cpuid leaf 0 (VM exit)        45560.8 ns/op   (100000 ops)
$ perf stat -e task-clock,context-switches ./vmexit-cost 100000
 Performance counter stats for './vmexit-cost 100000':

          12394.99 msec task-clock                       #    0.852 CPUs utilized             
               679      context-switches                 #   54.780 /sec                      

      14.549408484 seconds time elapsed

      10.822779000 seconds user
       1.675295000 seconds sys
```

For comparison, the same binary in Docker Desktop's WSL2 VM on the same Windows host (Hyper-V directly, kernel 6.18.58.1-microsoft-standard-WSL2), real run 2026-11-15:

```
CPUID.1:ECX bit 31 (hypervisor present) = 1
CPUID.0x40000000 hypervisor signature = "Microsoft Hv"
add (stays on the CPU)            0.2 ns/op   (20000000 ops)
getppid syscall (guest)          96.4 ns/op   (200000 ops)
cpuid leaf 0 (VM exit)          383.5 ns/op   (200000 ops)
cpuid leaf 1 (VM exit)          385.7 ns/op   (200000 ops)
```

**Reading it.** aos-lab reports `KVMKVMKVM` because VirtualBox exposes a KVM-compatible paravirtual interface to Linux guests (`systemd-detect-virt` still says `oracle`). The real exit handler is VirtualBox running on top of Hyper-V's API, so each `cpuid` exit takes tens of microseconds instead of ~0.4 µs. *Why* it is that slow (VirtualBox's Hyper-V/NEM backend handling exits in its host process) is an interpretation, not measured here: UNVERIFIED. On aos-lab, `sudo perf kvm stat record -a sleep 1` only prints its usage text, `/sys/kernel/tracing/events/kvm` does not exist, and `kvm` is not loaded: host-side exit counting is impossible here.

## What to observe

- **Ratio, not absolute numbers.** The `add` is ~0.2 ns (the loop overhead dominates). The syscall is the guest kernel's own cost. `cpuid` adds the full round trip: save guest state to the VMCS, load host state, run the handler, VM entry.
- **The guest cannot count its own exits.** `perf stat` inside the guest shows `task-clock` but no "exit" counter: exits are invisible from non-root mode. Only the host sees them (`kvm:kvm_exit` tracepoint, `perf kvm stat`).
- **Two hypervisors, two numbers.** Compare the aos-lab result (VirtualBox using Hyper-V's API) with the WSL2 result (Hyper-V directly). The extra layer shows up in the exit cost.
- **Why it matters.** A device emulated with port I/O exits on every register access; virtio rings batch many requests per exit; a CPU-bound process never exits at all.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `hypervisor present = 0` | you are on bare metal | then `cpuid` does not exit: its cost is the plain instruction (tens of ns) |
| very noisy `cpuid` numbers | shared host, vCPU preempted mid-loop | run 3×, take the minimum; pin with `taskset -c 2` |
| `perf stat -e cycles` → `<not supported>` | no virtual PMU in this guest | use `task-clock` and `clock_gettime`, as the lab does |

## Extension (UNVERIFIED here: needs a KVM host)

On a Linux machine **with** `/dev/kvm`, run a guest (Lab 06.4's `kvm-hello` in a loop, or any QEMU/KVM VM) and count its exits by reason from the host:

```bash
sudo perf kvm stat record -a sleep 10        # while the guest runs
sudo perf kvm stat report --event=vmexit
sudo bpftrace solution/kvm-exits.bt          # same data from the kvm:kvm_exit tracepoint
```

Questions: which exit reasons dominate for an idle Linux guest? For a guest running `vmexit-cost`? What fraction of exits ever reach user space (`kvm:kvm_userspace_exit`)?

Solution: [`solution/kvm-exits.bt`](solution/kvm-exits.bt) (the tracepoint and its `exit_reason` field are defined in `linux/arch/x86/kvm/trace.h` L391–434 · v6.18.63). Expected shape, not measured here: an idle guest is dominated by `HLT`, `EXTERNAL_INTERRUPT`, `MSR_WRITE` (timer programming) and `EPT_VIOLATION` right after boot.

Related: [note 06](../../notes/06-hypervisors-vtx-ept.en.md) · [lesson §4.6](../../lesson.en.md) · quiz Q6, Q10.
