# Lab 06.4 — A 100-line KVM client

> **VM only / bare metal only.** Needs `/dev/kvm`: a Linux host with VT-x/AMD-V, or a VM with **nested virtualization**. ARCH-SPECIFIC (x86-64).
> **UNVERIFIED run output.** Neither the course VM `aos-lab` (VirtualBox on Hyper-V, no nesting) nor the Docker Desktop WSL2 VM on the same host has `/dev/kvm` (both checked 2026-11-15). The code compiles with zero warnings and its guest bytes were checked with `as`/`objdump`; the output below marked EXPECTED is what the code must print, derived from the code path in the [walkthrough §2](../../kernel-walkthrough.en.md#2-one-vm-exit-end-to-end-out-al-dx-on-port-0x3f8).

**Goal:** write the whole user-space side of a hypervisor (one VM, one vCPU, 4 KiB of RAM) and watch every VM exit that reaches user space.

## Steps

```bash
cd ~/work/06-distributed-virtualization/04-kvm-client
ls -l /dev/kvm || echo "no KVM here: see 'Where to run' below"
grep -cE 'vmx|svm' /proc/cpuinfo          # >0 means the CPU (or virtual CPU) exposes VT-x/AMD-V

# 1. check the guest bytes embedded in kvm-hello.c
as --32 -o guest.o guest.S && objdump -d -mi8086 guest.o | tail -8

# 2. build (zero warnings) and run
gcc -Wall -Wextra -O2 -o kvm-hello kvm-hello.c
./kvm-hello
```

### Where to run

| Machine | `/dev/kvm` | How |
|---|---|---|
| Linux PC/laptop, bare metal | yes, if VT-x on in BIOS | `sudo usermod -aG kvm $USER`, re-login |
| libvirt/QEMU VM on a KVM host | with nesting | host: `cat /sys/module/kvm_intel/parameters/nested` = `Y`; VM: `<cpu mode='host-passthrough'/>` |
| VirtualBox on Hyper-V (`aos-lab`) | **no** | VirtualBox runs through Hyper-V's API here and does not expose VMX to the guest |
| WSL2 / Docker Desktop | only with `nestedVirtualization=true` in `.wslconfig` and a supporting build | not available on this host (checked) |

## Code

[`kvm-hello.c`](kvm-hello.c) (116 lines incl. comments), guest program [`guest.S`](guest.S). The fd chain is the one from the lesson §4.7:

| Step | ioctl | Kernel side (v6.18.63) |
|---|---|---|
| system fd | `open("/dev/kvm")`, `KVM_GET_API_VERSION` | `virt/kvm/kvm_main.c` `kvm_dev_ioctl()` L5546 |
| VM fd | `KVM_CREATE_VM` | `kvm_dev_ioctl_create_vm()` L5503 |
| guest RAM | `KVM_SET_USER_MEMORY_REGION` (slot 0 at GPA 0x1000 → our `mmap`) | `kvm_vm_ioctl()` L5194 |
| vCPU fd | `KVM_CREATE_VCPU`, `mmap(vcpufd)` = `struct kvm_run` + PIO page | `kvm_vm_ioctl_create_vcpu()` L4182, `KVM_GET_VCPU_MMAP_SIZE` L5563 |
| registers | `KVM_GET_SREGS`/`KVM_SET_SREGS` (CS base 0), `KVM_SET_REGS` (RIP 0x1000, RAX=RBX=2, RFLAGS 0x2) | — |
| run | `KVM_RUN` in a loop, `switch (run->exit_reason)` | `kvm_vcpu_ioctl()` L4471 → `vcpu_run()` → `handle_io()` → `KVM_EXIT_IO` |

The guest, verified with `objdump` (real output, `gcc:13` container on the host, 2026-11-15):

```
   0:	ba f8 03             	mov    $0x3f8,%dx
   3:	00 d8                	add    %bl,%al
   5:	04 30                	add    $0x30,%al
   7:	ee                   	out    %al,(%dx)
   8:	b0 0a                	mov    $0xa,%al
   a:	ee                   	out    %al,(%dx)
   b:	f4                   	hlt
```

## Expected output

Real output on aos-lab (2026-11-15), where KVM is missing (`grep -cE 'vmx|svm' /proc/cpuinfo` prints `0`). This is the first `err()` path:

```
$ ./kvm-hello
kvm-hello: open /dev/kvm: No such file or directory
$ echo $?
1
```

`EXPECTED (UNVERIFIED: no /dev/kvm available)` on a KVM host. Three exits reach user space: two `OUT`s and the `HLT`. Timings are not predicted; you will see your own:

```
$ ./kvm-hello
exit 1: KVM_EXIT_IO port=0x3f8 byte=0x34 (<t> us)
4exit 2: KVM_EXIT_IO port=0x3f8 byte=0x0a (<t> us)

exit 3: KVM_EXIT_HLT (<t> us)
```

(`stderr` and `stdout` interleave: the `4` and the newline are the guest's own output on stdout.)

## What to observe

- **Expect exit 1 to be slower than exit 2** (UNVERIFIED here). The first `KVM_RUN` also does the first VM entry: loading the VMCS, faulting in the guest page through EPT (an EPT-violation exit that KVM handles *in the kernel*, so you never see it).
- **Only 3 exits reach you.** On the host, `sudo perf stat -e 'kvm:*' ./kvm-hello` or [Lab 06.5's `kvm-exits.bt`](../05-vmexit-cost/solution/kvm-exits.bt) shows more `kvm:kvm_exit` events than user-space exits: the difference is what KVM handles in-kernel.
- **`HLT` comes to user space** only because we created no in-kernel irqchip (`KVM_CREATE_IRQCHIP`). With one, KVM puts the vCPU thread to sleep in `vcpu_block()` instead.
- **vCPU = thread.** Run `./kvm-hello` under `strace -f -e trace=ioctl`: every `KVM_RUN` is one `ioctl` from the main thread.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `open /dev/kvm: No such file or directory` | no VT-x/AMD-V exposed, or `kvm_intel`/`kvm_amd` not loaded | bare metal or nested VM (table above); `sudo modprobe kvm_intel` |
| `open /dev/kvm: Permission denied` | not in group `kvm` | `sudo usermod -aG kvm $USER` |
| `KVM_EXIT_FAIL_ENTRY ... 0x80000021` | invalid guest state: e.g. you zeroed `sregs` instead of `KVM_GET_SREGS` first | read sregs, change only CS base/selector (quiz Q14) |
| `KVM_EXIT_SHUTDOWN` | triple fault: RIP outside the memory slot | `rip` must be inside `[guest_phys_addr, +memory_size)` |
| garbage character | read the byte at `run + 0` instead of `run + run->io.data_offset` | data is in the PIO page (walkthrough §2.3) |

## Extension

Change the guest to print `Hello\n` with a `lodsb`/`out` loop (needs DS base 0), then make it write one byte to guest-physical **0x8000**, where there is no memory slot. Handle `KVM_EXIT_MMIO` (print address, length, data) and print an exit histogram at the end. Predict the histogram before running.

Solution: [`solution/kvm-mmio.c`](solution/kvm-mmio.c) with [`solution/guest-mmio.S`](solution/guest-mmio.S) (assembled to a flat binary at 0x1000; bytes checked with `ld --oformat binary` + `objdump -b binary`).
