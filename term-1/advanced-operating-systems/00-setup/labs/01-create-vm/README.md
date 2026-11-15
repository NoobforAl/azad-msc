# Lab 00.1 — Create the lab VM

> **Safety:** this lab changes the host (installs libvirt, creates a VM). It does **not** touch the host kernel. Every kernel-level lab later in the course runs **inside this VM**, never on the server itself.

**Goal:** have a disposable Ubuntu 24.04 VM (`aos-lab`) with a serial console and a `fresh` snapshot you can roll back to in 10 seconds.

## Steps

```bash
# on the server
cd term-1/advanced-operating-systems/00-setup/labs/01-create-vm
bash create-vm.sh                       # defaults: 4 vCPU, 8 GB RAM, 60 GB disk
# bigger build machine:  VCPUS=8 RAM_MB=16384 bash create-vm.sh

ssh "$USER@<vm-ip>"                     # IP is printed at the end
sudo virsh list --all                   # aos-lab   running
sudo virsh snapshot-list aos-lab        # fresh
```

What the script does, in order:

1. **Host checks.** x86-64, a `vmx`/`svm` CPU flag, `/dev/kvm`, an SSH key. It warns if **nested virtualization** is off (only Module 6 lab 4 needs it).
2. Installs `qemu-kvm libvirt-daemon-system virtinst cloud-image-utils` if they're missing.
3. Creates a **qcow2 overlay** on top of the Ubuntu cloud image, so the base image stays untouched.
4. Writes a **cloud-init** `user-data`: your user, your SSH key, passwordless sudo, and `console=ttyS0` on the kernel command line.
5. Runs `virt-install --import --cpu host-passthrough --cloud-init ...`.
6. Waits for the IP and for cloud-init to finish, shuts down, takes the snapshot `fresh`, and starts the VM again.

## Variant: Windows host with VirtualBox

If your PC runs Windows and VirtualBox, run `make vm-create` from the repository root. It calls [`create-vm-virtualbox.ps1`](create-vm-virtualbox.ps1), the exact recipe used to build the course's own test VM. The script:
- puts the VM in `<repo>/.cache/vm/aos-lab`;
- caches every download in `<repo>/.cache/downloads`: the Ubuntu image, the setup ISO and the 6.18.63 kernel `.deb`s, so a rebuild downloads nothing;
- installs the course kernel 6.18.63 (with [`install-mainline-kernel.sh`](install-mainline-kernel.sh)) and takes a snapshot named `fresh`.

```bash
make vm-create                                # 8 vCPU, 12 GB RAM, 60 GB disk, ~10 min the first time
make vm-ssh                                   # = ssh -p 2222 fred@127.0.0.1 (NAT port-forward)
make vm-stop && make vm-restore SNAP=fresh    # rollback
```

Captured on the course test VM (2026-11-15, VirtualBox 7.2.22 on Windows 11 with Hyper-V active):

```
$ ssh -p 2222 fred@127.0.0.1 'cloud-init status; uname -r; nproc'
status: done
6.8.0-147-generic
8
```

Limits of this variant (all observed on that VM):

| Feature | VirtualBox on Hyper-V | Why it matters |
|---|---|---|
| Hardware PMU (`perf stat -e cycles`) | `<not supported>` | Use software events (`task-clock`, `page-faults`, `context-switches`) or timing in C |
| `/dev/kvm` inside the VM | missing (no nested VT-x) | Module 06 lab 4 needs another machine, or a libvirt host |
| ftrace, BTF, bpftrace, kprobes | work | Most kernel-tracing labs run unchanged |

To run exactly the pinned kernel without the 1-hour build in lab 03, the VM uses Ubuntu's mainline build of v6.18.63 (`kernel.ubuntu.com/mainline/v6.18.63/amd64/`). Its `linux-image-unsigned` post-install hook fails on 24.04 with `run-parts: missing operand`; `install-mainline-kernel.sh` works around it (initramfs by hand, postinst neutralised, `dpkg --configure -a`, `update-grub`). Check the result with `uname -rv` → `6.18.63-061863-generic #202611101835 SMP PREEMPT_DYNAMIC`.

## Expected output

> `EXPECTED (not yet captured on your server)`: replace this block with your real run.

```
ok: nested virtualization enabled on host
...
VM IP: 192.168.122.57
waiting for cloud-init to finish...
Domain 'aos-lab' is being shutdown
Domain snapshot fresh created
Domain 'aos-lab' started

Done.
  ssh fred@192.168.122.57
```

## What to observe

- `ps -o pid,nlwp,cmd -C qemu-system-x86_64` on the host. The VM is **one host process**, and each vCPU is a **thread** in it (`nlwp` ≥ vCPUs). You will meet this again in Module 6 (KVM vCPU threads).
- `ls -l /var/lib/libvirt/images/`: the VM disk is small at first, because qcow2 is copy-on-write over the base image. This is the same idea as COW pages in Module 4.
- `sudo virsh console aos-lab` shows kernel boot messages. This is where you'll read a kernel panic when a module lab goes wrong.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `CPU has no VT-x/AMD-V flag` | virtualization disabled in BIOS, or the server is a VPS | enable VT-x in BIOS. On a VPS, run the VM on your own PC instead (see the guide, section 2) |
| `permission denied` on `virsh` without sudo | not in group `libvirt` yet | log out and in again |
| no IP after 5 min | the `default` network is inactive | `sudo virsh net-start default && sudo virsh net-autostart default` |
| snapshot fails with UEFI | internal snapshots aren't supported with pflash NVRAM | the script uses BIOS boot, so don't add `--boot uefi` |

## Extension task

Make a **second, throw-away VM** from the same base in under a minute, *without* running cloud-init again. Then prove it's independent: delete `/etc/hostname` in the clone and show that `aos-lab` is unaffected.

Solution: [`solution/clone-vm.md`](solution/clone-vm.md).
