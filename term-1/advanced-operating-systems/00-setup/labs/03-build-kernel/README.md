# Lab 00.3 — Build and boot the course kernel (v6.18.63) in the VM

> **Safety: run inside the VM only.** The script refuses to run on bare metal (`systemd-detect-virt`). Take a snapshot first: `sudo virsh snapshot-create-as aos-lab pre-kernel` (on the host).

**Goal:** the VM boots **exactly the kernel whose source you read**, v6.18.63, with BTF, ftrace, kallsyms, and debugfs on. Later you also build the `--rt` (Module 7) and `--lockdep` (Module 3) flavors.

## Steps

```bash
# inside the VM
git clone https://github.com/NoobforAl/azad-msc.git && cd azad-msc/term-1/advanced-operating-systems/00-setup/labs/03-build-kernel
bash build-kernel.sh            # ~20-40 min on 4 vCPU
sudo reboot
uname -r                        # 6.18.63-aos-lab
zgrep -E 'CONFIG_(DEBUG_INFO_BTF|FUNCTION_GRAPH_TRACER|PREEMPT)=' /proc/config.gz
bash ../02-install-tools/verify-tools.sh
```

What the script does:

| Step | Command | Why |
|---|---|---|
| 1 | `apt install bc bison flex libelf-dev libssl-dev dwarves ...` | the kernel build needs these. `dwarves` provides `pahole`, which generates BTF |
| 2 | `git clone --depth 1 --branch v6.18.63` | a **full** tree of the pin. The repo's sparse checkout has no `scripts/` or `drivers/`, so it can't be built |
| 3 | `cp /boot/config-$(uname -r) .config && make olddefconfig` | start from Ubuntu's working config, and set defaults for options added since Ubuntu's kernel |
| 3 | `make localmodconfig` | build only the modules currently loaded. Cuts the build from hours to minutes. The script `modprobe`s KVM, loop, overlay, veth, nf_tables, and dm-flakey first, so later labs keep them |
| 3 | `SYSTEM_TRUSTED_KEYS=""` | Ubuntu's config references Canonical cert files that a vanilla tree doesn't have, so the build fails without this |
| 3 | `scripts/config --enable ...` | BTF, ftrace, kprobes, KVM, `IKCONFIG_PROC` (`/proc/config.gz`) |
| 3 | config check | fails early if a dependency silently turned an option off |
| 4 | `make bindeb-pkg` | builds `.deb` packages, so `apt`/`dpkg` can remove the kernel cleanly later |
| 5 | `dpkg -i` + `update-grub` | 6.18 sorts above Ubuntu's kernel, so GRUB boots it by default |
| 6 | `make -C tools/perf` | Ubuntu ships no `perf` for a custom kernel. Build it from the same tree |

Flavors:

```bash
bash build-kernel.sh --rt        # 6.18.63-aos-rt       PREEMPT_RT (needs EXPERT; verified in kernel/Kconfig.preempt)
bash build-kernel.sh --lockdep   # 6.18.63-aos-lockdep  PROVE_LOCKING (noticeably slower kernel)
```

The source of the `PREEMPT_RT` dependency, quoted from the pinned tree:

```text
linux/kernel/Kconfig.preempt · config PREEMPT_RT · v6.18.63
config PREEMPT_RT
	bool "Fully Preemptible Kernel (Real-Time)"
	depends on EXPERT && ARCH_SUPPORTS_RT && !COMPILE_TEST
	select PREEMPTION
```

- `depends on EXPERT`: the option is **hidden** unless `EXPERT=y`. That's why the script enables `EXPERT` first. Without it, `olddefconfig` silently drops `PREEMPT_RT`, and the config check catches that.
- `ARCH_SUPPORTS_RT`: x86-64 selects this. Not every architecture does.
- `select PREEMPTION`: RT forces the general preemption machinery on (Module 7).

## Expected output

> `EXPECTED (not yet captured)`: replace with your real run.

```
real    27m41s
installed 6.18.63-aos-lab. Reboot, then check:  uname -r   # expect 6.18.63-aos-lab
$ uname -r
6.18.63-aos-lab
CONFIG_DEBUG_INFO_BTF=y
CONFIG_FUNCTION_GRAPH_TRACER=y
CONFIG_PREEMPT_VOLUNTARY=y      # or PREEMPT_DYNAMIC, depending on Ubuntu's base config
```

## What to observe

- `ls -la ../*.deb`: `linux-image`, `linux-headers`, `linux-libc-dev`, and `-dbg` packages. The `-dbg` one holds `vmlinux` with full DWARF symbols, which gdb uses on a crash dump.
- `du -sh .` after the build: about 20+ GB, most of it object files with debug info.
- `cat /sys/kernel/debug/sched/features` (as root) works now. Module 2 uses it.
- `uname -v` on the RT flavor contains `PREEMPT_RT` (set by `preempt-flag-$(CONFIG_PREEMPT_RT)` in `linux/init/Makefile` · L30 · v6.18.63).

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `No rule to make target 'debian/canonical-certs.pem'` | trusted-keys option not cleared | the script clears it. If you edit `.config` by hand, re-run `scripts/config --set-str SYSTEM_TRUSTED_KEYS ""` |
| `BTF: .tmp_vmlinux.btf: pahole (pahole) is not available` | `dwarves` missing | `sudo apt install dwarves` |
| build killed (`Killed signal terminated program cc1`) | VM out of RAM | `-j` lower, or `RAM_MB=16384` in lab 01 |
| VM doesn't boot the new kernel | panic early in boot | `sudo virsh console aos-lab`, pick the Ubuntu kernel in GRUB, or `virsh snapshot-revert aos-lab pre-kernel` |
| `config check failed: CONFIG_PREEMPT_RT` | `EXPERT` not set | use `--rt`, which sets both |

## Extension task

Prove that the running kernel really is the source you read. Pick a function from Module 1's walkthrough (`do_syscall_64`) and show, **using only the running VM**, that:

1. the symbol exists in the running kernel, with its address,
2. ftrace can trace it,
3. the line in the local source (`_shared/sources/linux/arch/x86/entry/syscall_64.c`) matches what `gdb` shows from the `-dbg` package's `vmlinux`.

Solution: [`solution/prove-kernel-matches-source.md`](solution/prove-kernel-matches-source.md).
