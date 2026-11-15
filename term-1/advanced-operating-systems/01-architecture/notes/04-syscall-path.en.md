# Note 04 — The `syscall` instruction path

> Module 01 · Architecture · Persian: [`04-syscall-path.fa.md`](04-syscall-path.fa.md) · Index: [`INDEX.en.md`](INDEX.en.md) · **ARCH-SPECIFIC (x86-64)**

## 1. Summary

- A system call is a numbered request: number in `rax`, up to six arguments in `rdi, rsi, rdx, r10, r8, r9`, result (or `-errno`) back in `rax`. The `syscall` instruction jumps to the address in `MSR_LSTAR`.
- Linux's path is `entry_SYSCALL_64` (asm: `swapgs`, kernel stack, `pt_regs`) → `do_syscall_64()` (entry work, dispatch, exit work) → `x64_sys_call()` (a `switch` on the number) → `__x64_sys_<name>()`.
- The fast exit is `sysretq`; the kernel falls back to `iretq` when the saved state isn't safe for `sysret`. Tracing (strace), seccomp and signals hook into the entry/exit work, not into each syscall.

## 2. Explanation

### Intuition

A syscall is a function call across a privilege boundary. The caller can't jump to an arbitrary kernel address, so it uses one fixed door and passes "which function" as a number. The kernel on the other side must not trust anything: not the stack pointer, not the registers, not the pointers in the arguments.

### Step by step

**0. The libc wrapper.** `read(fd, buf, n)` in glibc puts 0 in `eax` (`__NR_read`), moves arguments into place and executes `syscall`. On return it checks `rax`: a value in `[-4095, -1]` means error, so it stores `-rax` in `errno` and returns `-1`.

**1. What the instruction does in hardware** (from the comment above `entry_SYSCALL_64`):

`linux/arch/x86/entry/entry_64.S · entry_SYSCALL_64 (comment) · v6.18.63` (L62–78)

```text
 * 64-bit SYSCALL saves rip to rcx, clears rflags.RF, then saves rflags to r11,
 * then loads new ss, cs, and rip from previously programmed MSRs.
 * rflags gets masked by a value from another MSR (so CLD and CLAC
 * are not needed). SYSCALL does not save anything on the stack
 * and does not change rsp.
 *
 * Registers on entry:
 * rax  system call number
 * rcx  return address
 * r11  saved rflags (note: r11 is callee-clobbered register in C ABI)
 * rdi  arg0
 * rsi  arg1
 * rdx  arg2
 * r10  arg3 (needs to be moved to rcx to conform to C ABI)
 * r8   arg4
 * r9   arg5
 * (note: r12-r15, rbp, rbx are callee-preserved in C ABI)
```

The key sentence: **"SYSCALL does not save anything on the stack and does not change rsp."** The kernel starts on a user-controlled stack and must leave it before it does anything else.

**2. `entry_SYSCALL_64` (asm, `entry_64.S` L87).** `swapgs` (reach per-CPU data), save user `rsp` to a per-CPU slot, `SWITCH_TO_KERNEL_CR3` (only with PTI), load `cpu_current_top_of_stack` into `rsp`, push a hardware-style frame + all GPRs = `struct pt_regs`, clear the GPRs, Spectre mitigations, `call do_syscall_64(regs, nr)` (walkthrough §2).

**3. `do_syscall_64()` (C, `syscall_64.c` L87, `noinstr`).**
- `syscall_enter_from_user_mode()`: enable interrupts; if `syscall_work` flags are set, `syscall_trace_enter()` runs **syscall user dispatch → ptrace (strace) → seccomp → `sys_enter` tracepoint → audit**, in that order (`kernel/entry/syscall-common.c` L20–67).
- `do_syscall_x64()`: bounds check with `unsigned` compare, `array_index_nospec()`, then `x64_sys_call(regs, nr)`; result into `regs->ax`.
- `syscall_exit_to_user_mode()`: `exit_to_user_mode_loop()` → `schedule()` if `need_resched`, signal delivery, `resume_user_mode_work`; then the `sys_exit` tracepoint/ptrace stop.
- Return `true` if `sysret` is safe (checks `rcx == rip`, `r11 == flags`, canonical `rip`, no `RF`/`TF`).

**4. `x64_sys_call()` → `__x64_sys_read(regs)`.** A `switch` generated from `syscall_64.tbl`. The stub, made by `SYSCALL_DEFINE3`, pulls `regs->di, regs->si, regs->dx` and calls the real body (walkthrough §4–§5).

**5. Return.** Back in asm: `POP_REGS`, switch to the trampoline stack, `SWITCH_TO_USER_CR3`, `swapgs`, `sysretq` (L166): `rip ← rcx`, `rflags ← r11`, `CPL ← 3`. Or the `iretq` path via `swapgs_restore_regs_and_return_to_usermode`.

### Fast path vs slow path

There is no separate "fast path" function any more. The cost difference is the `syscall_work` flags: with no tracer, no seccomp filter and no audit, `syscall_enter_from_user_mode` does almost nothing. Attach `strace` and **every** syscall takes `ptrace_report_syscall_entry()`, which stops the task and wakes the tracer process: two context switches per syscall entry and two per exit. That's why programs run many times slower under strace (lab 04 measures it).

### What costs time in a syscall

| Part | Why | Rough share |
|---|---|---|
| `syscall` + `sysret` instructions | pipeline serialization, MSR-based target | fixed, tens of ns |
| PTI `CR3` writes (if Meltdown-vulnerable CPU) | two `CR3` loads per syscall; with PCID no full TLB flush | can double the cost |
| Spectre mitigations (`IBRS_ENTER`, `UNTRAIN_RET`, `CLEAR_BRANCH_HISTORY`, `CLEAR_CPU_BUFFERS`) | CPU-dependent | from 0 to large |
| entry/exit work | RCU/lockdep state, `need_resched` and signal checks | small when idle |
| the syscall body | `getpid` ≈ nothing; `read` = VFS + FS + copy | varies |

Check your CPU: `grep . /sys/devices/system/cpu/vulnerabilities/*`.

### The vDSO: syscalls that aren't

Some calls only *read* kernel-maintained data: time (`clock_gettime`, `gettimeofday`, `time`), `getcpu`, and since v6.11 `getrandom`. The kernel maps a small ELF (`[vdso]` in `/proc/self/maps`) plus data pages (`[vvar]`) into every process, and glibc calls it like a normal library function. No mode switch, as long as the clock source can be read from user mode (TSC, or a paravirt clock); otherwise the vDSO itself falls back to a real `syscall`. Source: `arch/x86/entry/vdso/vclock_gettime.c`, `lib/vdso/gettimeofday.c`.

## 3. Diagram

```mermaid
sequenceDiagram
  participant U as user code
  participant CPU
  participant A as entry_SYSCALL_64 (asm)
  participant D as do_syscall_64 (C)
  participant W as entry/exit work
  participant S as __x64_sys_getpid
  U->>CPU: eax=39; syscall
  CPU->>A: rcx=RIP, r11=RFLAGS, RIP=LSTAR, CPL=0, IF=0
  A->>A: swapgs · save rsp · [CR3] · kernel rsp · pt_regs
  A->>D: call do_syscall_64(regs, 39)
  D->>W: syscall_enter_from_user_mode: IRQs on, [ptrace/seccomp/trace]
  D->>S: x64_sys_call → case 39
  S-->>D: regs->ax = tgid
  D->>W: syscall_exit_to_user_mode: [schedule()] [signals]
  D-->>A: true (sysret OK)
  A->>A: pop regs · [CR3] · swapgs
  A-->>U: sysretq → rax = pid
```

## 4. Worked example: the wrapper and the kernel symbols on the VM

The glibc wrapper really is a few instructions around `syscall`, and the kernel side has the stub that `x64_sys_call` jumps to (real output, aos-lab, 2026-11-15):

```text
$ gdb -batch -ex 'disassemble read' /lib/x86_64-linux-gnu/libc.so.6 | head -9
Dump of assembler code for function __GI___libc_read:
   0x000000000011bce0 <+0>:	endbr64
   0x000000000011bce4 <+4>:	cmpb   $0x0,0xf0355(%rip)        # 0x20c040 <__libc_single_threaded>
   0x000000000011bceb <+11>:	je     0x11bd00 <__GI___libc_read+32>
   0x000000000011bced <+13>:	xor    %eax,%eax
   0x000000000011bcef <+15>:	syscall
   0x000000000011bcf1 <+17>:	cmp    $0xfffffffffffff000,%rax
   0x000000000011bcf7 <+23>:	ja     0x11bd48 <__GI___libc_read+104>
   0x000000000011bcf9 <+25>:	ret

$ grep -w -e do_syscall_64 -e x64_sys_call -e __x64_sys_read /proc/kallsyms
ffffffffb5929b60 T x64_sys_call
ffffffffb5ea3d60 T __x64_sys_read
ffffffffb6c8a1d0 T do_syscall_64
```

- `xor %eax,%eax` then `syscall`: `__NR_read` is 0 (`syscall_64.tbl` L12), and xor is the short way to load 0. `getpid` is `mov $0x27,%eax` (39).
- `cmp $0xfffffffffffff000,%rax` + `ja`: the `-4095..-1` error check.
- `__x64_sys_read`, `x64_sys_call` and `do_syscall_64` are real symbols in `/proc/kallsyms`; `__do_sys_read` is `static inline` and usually inlined into `__x64_sys_read`.

## 5. Edge cases & pitfalls

- **`r10`, not `rcx`.** Calling a 4+ argument syscall from inline asm with the 4th argument in `rcx` silently passes garbage (lab 02 extension).
- **`rcx` and `r11` are clobbered.** Inline asm must list them, plus `"memory"` if the kernel writes user memory.
- **Return value ≠ libc return value.** The kernel returns `-EBADF` (`-9`); `syscall(3)` and wrappers return `-1` with `errno = 9`.
- **Restartable calls.** A `read` interrupted by a signal returns `-ERESTARTSYS` internally; the signal code either restarts it (SA_RESTART: backs up `rip` by 2, the length of `syscall`) or turns it into `-EINTR`.
- **32-bit paths are different entry points**: `int 0x80` → `do_int80_emulation()`, `sysenter`/32-bit `syscall` → `entry_SYSENTER_compat` / `entry_SYSCALL_compat`, with the i386 numbers (`read` = 3).
- **FRED** (Flexible Return and Event Delivery, recent Intel CPUs): one entry mechanism for syscalls and events; `syscall_init()` skips the LSTAR setup when FRED is on (`common.c` L2280–2281). VERSION-DEPENDENT; not active on our VM.
- **`do_syscall_64` is `noinstr`**: you can't ftrace or kprobe it. Probe `x64_sys_call`, `__x64_sys_*`, or the `raw_syscalls:sys_enter` tracepoint instead.

## 6. Exam-style key points

- ABI: `rax` = number, args `rdi rsi rdx r10 r8 r9`, result `rax`, `rcx`/`r11` clobbered, errors `-4095..-1`.
- `syscall`: `rcx ← RIP`, `r11 ← RFLAGS`, `CS/SS ← STAR`, `RIP ← LSTAR`, `RFLAGS &= ~SFMASK`; **no stack switch**.
- Entry asm: `swapgs`, save user `rsp`, PTI `CR3`, kernel stack, build `pt_regs`, clear GPRs.
- `do_syscall_64`: enter work (ptrace/seccomp/tracepoint/audit) → `x64_sys_call` switch → exit work (schedule, signals) → choose `sysret` or `iret`.
- `SYSCALL_DEFINEn(name, ...)` generates `__x64_sys_name(regs)`, `__se_sys_name`, `__do_sys_name`.
- strace makes every syscall stop in `ptrace_report_syscall_entry/exit` → slow.
- vDSO: `clock_gettime` & co. run in user mode from kernel-updated data; fallback is a real syscall.
- Syscall return is a preemption and signal-delivery point.

## 7. Links

- Lesson: [§2.2 What happens when a program calls `read()`](../lesson.en.md#22-what-happens-when-a-program-calls-read), [§2.4 vDSO](../lesson.en.md#24-why-is-clock_gettime-10-cheaper-than-getpid)
- Walkthrough: [§2–§5](../kernel-walkthrough.en.md#2-entry_syscall_64-the-first-kernel-instructions)
- Labs: [01 strace map](../labs/01-strace-map/README.md), [02 raw syscall](../labs/02-raw-syscall/README.md), [04 syscall cost](../labs/04-syscall-cost/README.md)
- Quiz: questions 7, 8, 9, 12 in [`quiz.en.md`](../quiz.en.md)
