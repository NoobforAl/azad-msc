# 01 — Quiz: Architecture & Kernel Structure

> 15 questions: 6 conceptual (40%), 5 read-the-code/output (≈30%), 4 debug/design (≈30%), plus 3 oral-exam questions. Answers are at the end. Persian: [`quiz.fa.md`](quiz.fa.md).

## A. Conceptual

**1.** In one sentence each, define a monolithic kernel and a microkernel by **what runs in ring 0** and **how components communicate**. Where do Linux, OpenBSD, seL4 and XNU fit?

**2.** "Linux has loadable modules, so it is a microkernel." Give two technical reasons this is wrong.

**3.** On x86-64 Linux, where is the CPU's current privilege level stored? What value does `CS` have in a normal user process, and what is that value made of?

**4.** List three different things the CPU checks against the privilege level, and the exception each violation raises.

**5.** Classify each as fault, trap, abort or interrupt, and say where the saved `RIP` points: (a) page fault on a stack access, (b) `int3`, (c) a network packet arrives, (d) double fault.

**6.** Why do NMI, `#DF` and `#MC` use IST stacks, when a page fault doesn't?

## B. Read the code / output

**7.** From `arch/x86/entry/entry_64.S`:

```asm
	swapgs
	/* tss.sp2 is scratch space. */
	movq	%rsp, PER_CPU_VAR(cpu_tss_rw + TSS_sp2)
	SWITCH_TO_KERNEL_CR3 scratch_reg=%rsp
	movq	PER_CPU_VAR(cpu_current_top_of_stack), %rsp
```

Explain each line. Why can't the kernel just `push` the user registers onto the current stack as its first instruction?

**8.** From `arch/x86/entry/syscall_64.c`:

```c
	unsigned int unr = nr;

	if (likely(unr < NR_syscalls)) {
		unr = array_index_nospec(unr, NR_syscalls);
		regs->ax = x64_sys_call(regs, unr);
		return true;
	}
	return false;
```

(a) Why convert to `unsigned`? (b) What does `array_index_nospec` defend against, given that the bounds check is already there? (c) What will user space see in `rax` for `nr = 1000`?

**9.** A line from `strace -f cat /etc/hostname` on the course VM:

```text
openat(AT_FDCWD, "/etc/hostname", O_RDONLY) = 3
read(3, "aos-lab\n", 131072)            = 8
read(3, "", 131072)                     = 0
```

For the first `read`, give the value of `rax`, `rdi` and `rdx` at the moment `syscall` executes. Name the kernel functions on the path from `entry_SYSCALL_64` to the file system, in order.

**10.** From `arch/x86/kernel/process_64.c` `__switch_to()`:

```c
	raw_cpu_write(current_task, next_p);
	raw_cpu_write(cpu_current_top_of_stack, task_top_of_stack(next_p));
```

Which instruction in `entry_SYSCALL_64` reads the value written on the second line? What would go wrong if this line were missing?

**11.** On the course VM (8 vCPUs, `CONFIG_HZ=1000`, `CONFIG_NO_HZ_FULL=y`), two snapshots of `/proc/interrupts` five seconds apart show the `LOC` row growing by 8,746. Is that consistent with a 1000 Hz tick? Explain.

## C. Debug / design

**12.** A student writes a raw `mmap` with inline asm, putting the 4th argument (`flags`) in `rcx`. The call returns `-22` (`EINVAL`), or maps memory with strange flags. Explain the bug. What else must the inline asm declare as clobbered?

**13.** A program runs 40× slower under `strace -f` than without it, but `perf stat` shows almost the same number of syscalls. Using `syscall_trace_enter()`, explain where the time goes. How would you count syscalls with much lower overhead?

**14.** You measure: empty loop 0.3 ns/iter, `clock_gettime()` 20 ns, `syscall(SYS_getpid)` 250 ns. Then on another VM, `clock_gettime()` costs 300 ns. Give two possible causes and the files or commands you'd check.

**15.** You must find where Linux v6.18.63 turns `SYSCALL_DEFINE3(read, …)` into the symbol `__x64_sys_read`. Describe the search steps and name the file and macro you'd end at.

## Oral-exam questions

**O1.** Argue for and against moving the Linux page cache and ext4 into a user-space server, as a microkernel would. Which costs would grow, which risks would shrink, and what does FUSE tell us in practice?

**O2.** Walk the board through everything that happens between `read()` returning in task A, which blocks, and task B's next instruction in user space. Mention every saved/restored register set and every stack involved.

**O3.** OpenBSD checks, on every syscall, that the call comes from the registered libc address for that number (pinsyscalls), and still takes a big kernel lock for many calls. Linux does neither. Defend each design for its target users.

---

## Answers

**1.** Monolithic: all core services (scheduler, memory, VFS, file systems, network, drivers) run in ring 0 in one address space and talk by **function calls**. Microkernel: only IPC, scheduling and address-space management run in ring 0; services are user processes that talk by **messages**. Linux and OpenBSD are monolithic, seL4 is a microkernel, XNU is hybrid (Mach + BSD in kernel space).

**2.** (i) A `.ko` module is linked into the kernel's own address space and runs in ring 0 with full privilege, so there is no isolation. (ii) It communicates through direct function calls and shared data structures (`f_op->read_iter`), not IPC. A module bug crashes or compromises the whole kernel.

**3.** In the low 2 bits (RPL = CPL) of the `CS` selector. User `CS` = `0x33` = GDT index 6 × 8 + RPL 3 (`__USER_CS` in `segment.h`). Kernel `CS` = `0x10` (index 2, RPL 0).

**4.** Any three of: a privileged instruction (`cli`, `mov %cr3`, `wrmsr`, `hlt`) needs CPL 0, else `#GP`. A page with `U/S=0` touched at CPL 3 raises `#PF`. `int N` with gate DPL < CPL raises `#GP`. I/O port access without IOPL or bitmap permission raises `#GP`. SMAP/SMEP violations by the kernel raise `#PF`.

**5.** (a) Fault: `RIP` = the faulting instruction, which is retried after the page is mapped. (b) Trap: `RIP` = the next instruction. (c) Interrupt: asynchronous, `RIP` = the next instruction not yet executed. (d) Abort: no reliable `RIP`, no return.

**6.** They can arrive when the current kernel stack is unusable: a stack overflow (`#DF`), the middle of the entry code before `rsp` is switched (NMI, `#DB`), or hardware failure (`#MC`). IST makes the CPU switch to a known-good per-CPU stack regardless. A page fault arrives in states where the normal stack is valid, and it may sleep, which an IST stack can't support.

**7.** `swapgs`: load the kernel `GS.base`, so `%gs:` reaches this CPU's per-CPU area. `movq %rsp, …TSS_sp2`: park the user `rsp` in a per-CPU scratch slot. `SWITCH_TO_KERNEL_CR3`: with PTI, switch to the kernel page tables; the user tables don't map most kernel memory. `movq cpu_current_top_of_stack, %rsp`: switch to this task's kernel stack. The kernel can't push first because `syscall` does not change `rsp`. The current stack is the **user's**: it may be invalid, unmapped, or crafted by an attacker, and other user threads could read or modify it.

**8.** (a) A negative `int` becomes a huge unsigned number, so one `<` comparison rejects both negative and too-large numbers. (b) Spectre v1: the CPU can speculatively run past the bounds check with an out-of-range index and leak data through the cache. `array_index_nospec` clamps the index with a branch-free mask, so even speculative execution uses a valid index. (c) `do_syscall_x64` returns `false` (1000 ≥ `NR_syscalls`), `do_syscall_x32` also fails, and `nr != -1`, so `regs->ax = __x64_sys_ni_syscall(regs)` = `-ENOSYS`. User space sees `rax = -38`, and `syscall(3)` returns `-1` with `errno = 38`.

**9.** `rax = 0` (`__NR_read`), `rdi = 3` (fd), `rdx = 131072` (count); `rsi` = buffer address. Path: `entry_SYSCALL_64` → `do_syscall_64()` → `syscall_enter_from_user_mode()` → `do_syscall_x64()` → `x64_sys_call()` → `__x64_sys_read()` → (`__se_sys_read` → `__do_sys_read`, inlined) → `ksys_read()` → `vfs_read()` → `file->f_op->read_iter` = `ext4_file_read_iter()` (via `new_sync_read`) → `filemap_read()` … Return goes through `syscall_exit_to_user_mode()` → `sysretq`.

**10.** `movq PER_CPU_VAR(cpu_current_top_of_stack), %rsp` (entry_64.S L95). Without that write, the next syscall from `next` would land on the previous task's kernel stack and overwrite its frames: memory corruption and a crash.

**11.** Yes. Without tick suppression it would be 8 CPUs × 1000 Hz × 5 s = 40,000. With `NO_HZ` (`CONFIG_NO_HZ_FULL=y` includes idle-tick suppression) an idle CPU stops its periodic tick and programs the timer only for the next real event. 8,746 / 5 s / 8 CPUs ≈ 220 ticks per second per CPU, so most CPUs were idle most of the time. A busy CPU ticks at the full `HZ` (a `perf stat` window on the same VM counted 22,222 `local_timer_entry` events while other users were busier).

**12.** `syscall` overwrites `rcx` with the return `RIP`, so the kernel ABI takes argument 4 from `r10` (`SC_X86_64_REGS_TO_ARGS`: `regs->di, si, dx, r10, r8, r9`). The `flags` value is lost and `regs->r10` holds whatever was there. The asm must also list `"rcx"` and `"r11"` (overwritten by `syscall`) and `"memory"` (the kernel may read or write user memory) as clobbers.

**13.** strace uses ptrace, which sets `SYSCALL_WORK_SYSCALL_TRACE`. Every syscall then calls `ptrace_report_syscall_entry()` and the matching exit report. The tracee stops, the tracer is woken, it reads registers with more syscalls, and it resumes the tracee. That is several context switches and syscalls per traced syscall. Lower-overhead counting: `perf stat -e 'raw_syscalls:sys_enter'`, `perf trace -s`, or `bpftrace -e 'tracepoint:raw_syscalls:sys_enter /comm=="cat"/ { @[args->id] = count(); }'`. These use tracepoints in the kernel, with no stop and no tracer context switch.

**14.** (i) The clocksource isn't vDSO-capable: `current_clocksource` is `hpet` or `acpi_pm` instead of `tsc` or `kvm-clock`, so the vDSO falls back to a real syscall. Check `/sys/devices/system/clocksource/clocksource0/current_clocksource` and run `strace -e clock_gettime` (the call appears only if it really enters the kernel). (ii) It's a real syscall anyway and is expensive because of mitigations (PTI on a Meltdown-affected CPU, or `IBRS`/retbleed mitigations): `grep . /sys/devices/system/cpu/vulnerabilities/*`. (Another cause: the program is statically linked or calls `syscall(SYS_clock_gettime)` directly.)

**15.** `git grep -n "SYSCALL_DEFINE3(read,"` finds `fs/read_write.c` L722. Open `include/linux/syscalls.h`: `SYSCALL_DEFINE3` → `SYSCALL_DEFINEx` → `__SYSCALL_DEFINEx`. On x86 the last one is overridden in `arch/x86/include/asm/syscall_wrapper.h` (L223), which calls `__X64_SYS_STUBx` → `__SYS_STUBx(x64, sys##name, …)` (L91). That macro defines `long __x64_sys_read(const struct pt_regs *regs)` returning `__se_sys_read(regs->di, regs->si, regs->dx)`. Confirm on the VM with `grep -w __x64_sys_read /proc/kallsyms`.

**O1 (points to cover).** Costs that grow: every `read` becomes at least 2 IPC round trips (app → FS server → block driver). The page cache, which is shared and zero-copy today, needs shared-memory protocols or copies. Locking and consistency across servers get harder, and so does `mmap` of file pages (the pager must talk to the FS server). Risks that shrink: an ext4 bug crashes or restarts one server instead of the kernel, and the kernel's trusted code base gets smaller. FUSE is the real-world data point. It works and is used (sshfs, rclone), but throughput and latency are clearly worse than in-kernel file systems for metadata-heavy work, and Linux keeps adding special paths (FUSE passthrough, io_uring for FUSE) to win the speed back.

**O2 (points to cover).** A's user registers are saved in A's `pt_regs` at `entry_SYSCALL_64`, on A's kernel stack. `vfs_read` → the file system finds no data → the task state becomes `TASK_INTERRUPTIBLE` → `schedule()` → `__schedule()` picks B → `context_switch()` → `switch_mm_irqs_off()`: `CR3` is written if B has a different `mm` → `__switch_to_asm` pushes A's 6 callee-saved registers on A's kernel stack, saves `rsp` into `A->thread.sp`, loads `B->thread.sp`, and pops B's 6 → `__switch_to()`: FPU (save A, defer B's restore), `FS`/`GS` base, `current_task = B`, `cpu_current_top_of_stack = B` → it returns into B's earlier `context_switch()` → `finish_task_switch()` → B unwinds to its own exit path → `syscall_exit_to_user_mode()` (or `irqentry_exit`) → B's FPU is restored (`TIF_NEED_FPU_LOAD`) → B's `pt_regs` are popped → `sysretq`/`iretq` → B's user instruction. Stacks involved: A's user and kernel stacks, B's kernel and user stacks, and the entry trampoline stack at exit.

**O3 (points to cover).** OpenBSD's users are security-first deployments that accept small performance and compatibility costs. pinsyscalls blocks ROP and shellcode that issue syscalls from arbitrary code, and recompiling all of base each release makes breaking the ABI acceptable. The big kernel lock keeps the code simpler and easier to audit, and OpenBSD removes it per syscall (`NOLOCK`) as each subsystem is made MP-safe. Linux's users run anything from huge servers to JITs, Go runtimes and static binaries, which all issue `syscall` directly. Linux never breaks user space, and it must scale to hundreds of CPUs, so a global lock is unacceptable. Its policy is opt-in and per process (seccomp-BPF), and is paid only when used (the slow path through `syscall_trace_enter`).
