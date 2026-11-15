# Note 05 — Context switch: registers, stacks, `CR3`

> Module 01 · Architecture · Persian: [`05-context-switch.fa.md`](05-context-switch.fa.md) · Index: [`INDEX.en.md`](INDEX.en.md) · **ARCH-SPECIFIC (x86-64)** for the register details

## 1. Summary

- A context switch always happens **inside the kernel**, in `__schedule()` → `context_switch()`. The outgoing task's user registers were already saved in its `pt_regs` when it entered the kernel.
- The switch itself does three things: maybe load a new address space (`switch_mm_irqs_off()` → write `CR3`), swap the **kernel stack** (`__switch_to_asm`: push 6 callee-saved registers, swap `rsp`), and fix per-task CPU state (`__switch_to()`: FPU, `FS`/`GS` base, `current`, top-of-stack).
- Switching between two threads of the same process, or to a kernel thread, skips the `CR3` write. Direct cost is on the order of microseconds (Module 02 lab 3 measures it on this VM); the indirect cost (cold caches and TLB) is often larger.

## 2. Explanation

### Intuition

Each task has its own kernel stack. A task that is not running is "frozen" in the middle of a function call: `context_switch()` → `switch_to()`. Its stack holds the return addresses of that call chain. Switching tasks means: save where I am (my stack pointer) and continue on another task's stack, which is frozen at exactly the same point in the code. When `switch_to` "returns", it returns on the *other* task's stack, into the other task's call to `context_switch()`. Every task sleeps and wakes up at the same line.

### Why only 6 registers?

`switch_to()` is a function call from C. The x86-64 System V ABI says the caller has already saved any caller-saved register (`rax, rcx, rdx, rsi, rdi, r8–r11`) it needs. So the callee only has to preserve the **callee-saved** ones: `rbx, rbp, r12–r15`. `__switch_to_asm` pushes exactly those six, in the order of `struct inactive_task_frame`:

`linux/arch/x86/include/asm/switch_to.h · struct inactive_task_frame · v6.18.63` (L23–42)

```c
struct inactive_task_frame {
#ifdef CONFIG_X86_64
	unsigned long r15;
	unsigned long r14;
	unsigned long r13;
	unsigned long r12;
#else
	unsigned long flags;
	unsigned long si;
	unsigned long di;
#endif
	unsigned long bx;

	/*
	 * These two fields must be together.  They form a stack frame header,
	 * needed by get_frame_pointer().
	 */
	unsigned long bp;
	unsigned long ret_addr;
};
```

- Read bottom-up as the stack grows down: the `call __switch_to_asm` pushed `ret_addr`, then `pushq %rbp`, `%rbx`, `%r12`…`%r15`. `thread.sp` points at `r15`.
- A newly forked task gets a hand-made `inactive_task_frame` with `ret_addr = ret_from_fork_asm` (`struct fork_frame`, L44), so its first "return from `switch_to`" lands in the fork return path.

The user-mode registers (`rip`, `rsp`, all GPRs, `rflags`) are not touched here: they are in `pt_regs` at the top of each task's kernel stack, saved at entry and restored at exit.

### What `context_switch()` decides

| Case | `next->mm` | Address space action |
|---|---|---|
| user → user, different process | non-NULL, ≠ prev | `switch_mm_irqs_off()`: write `CR3` (with PCID: tag with ASID, no full TLB flush) |
| thread → thread, same process | non-NULL, = prev | `switch_mm_irqs_off()` sees `prev == next`: normally no `CR3` write |
| any → kernel thread | NULL | **lazy TLB**: keep the old `mm` loaded (`active_mm`), no `CR3` write |
| kernel thread → user | non-NULL | load `next->mm`; drop the borrowed `mm` later in `finish_task_switch()` |

Kernel threads live only in the kernel half of the address space, which is identical in every `mm`, so they can borrow any one.

### What `__switch_to()` does (C, per arch)

From `arch/x86/kernel/process_64.c` L611–700:
1. `switch_fpu(prev_p, cpu)`: **save** `prev`'s FPU/SSE/AVX registers now (`save_fpregs_to_fpstate()`) and set `TIF_NEED_FPU_LOAD` on it (`arch/x86/include/asm/fpu/sched.h` L32–52). Registers are **restored** only on the way back to user mode, and skipped if this CPU still holds that task's state.
2. `save_fsgs()`, `load_TLS()`, `x86_fsgsbase_load()`: the `FS` base is the thread pointer (TLS) for user space; `GS` base too for some programs.
3. `x86_pkru_load()`: memory protection keys.
4. `raw_cpu_write(current_task, next_p)`: now `current` is `next`.
5. `raw_cpu_write(cpu_current_top_of_stack, …)`: the next `syscall` on this CPU will land on `next`'s kernel stack (walkthrough §7).
6. `switch_to_extra()`: rarely used features (I/O bitmap, speculation control).

### When does a switch happen?

- **Voluntary**: the task blocks (`read` on an empty pipe, `futex` wait, `nanosleep`) and calls `schedule()`. Counted in `/proc/<pid>/status` as `voluntary_ctxt_switches`.
- **Involuntary (preemption)**: the timer tick or a wakeup sets `need_resched`; the kernel calls `schedule()` on interrupt exit or syscall exit (or at a preemption point inside the kernel, depending on the `PREEMPT_DYNAMIC` mode). Counted as `nonvoluntary_ctxt_switches`.

### Cost

- **Direct**: entering the kernel, the scheduler's pick, the switch code, `CR3` write. Microseconds.
- **Indirect**: the next task finds caches and TLB filled with the previous task's data. With PCID the TLB entries survive, but L1/L2 caches are still cold. This is why pinning a ping-pong pair to one CPU is faster than two CPUs for some workloads and slower for others (Module 02 lab 3 measures it).

## 3. Diagram

```mermaid
sequenceDiagram
  participant A as task A (kernel stack A)
  participant S as __schedule / context_switch
  participant M as switch_mm_irqs_off
  participant W as __switch_to_asm
  participant C as __switch_to
  participant B as task B (kernel stack B)
  A->>S: blocks or is preempted (user regs already in pt_regs A)
  S->>M: next->mm differs: write CR3 (ASID)
  S->>W: switch_to(A, B)
  W->>W: push rbp rbx r12-r15 on stack A
  W->>W: A->thread.sp = rsp ; rsp = B->thread.sp
  W->>W: pop r15-r12 rbx rbp (B's saved values)
  W->>C: jmp __switch_to(A, B)
  C->>C: FPU, FS/GS, current_task = B, top_of_stack = B
  C-->>B: ret: returns into B's old context_switch()
  B->>B: finish_task_switch(A), back up B's call chain → sysret/iret to B's user code
```

## 4. Worked example

Count switches for a task that blocks a lot (a subshell that waits for 20 short `sleep` children) and one that never blocks (`yes > /dev/null`), on the VM, 2026-11-15:

```text
$ ( for i in $(seq 1 20); do sleep 0.05; done ) & P=$!; sleep 0.5; grep ctxt /proc/$P/status
voluntary_ctxt_switches:	11
nonvoluntary_ctxt_switches:	0
$ yes > /dev/null & Y=$!; sleep 3; grep ctxt /proc/$Y/status; kill $Y
voluntary_ctxt_switches:	2
nonvoluntary_ctxt_switches:	2
$ perf stat -e context-switches,cpu-migrations,task-clock sleep 1
                 1      context-switches                 #  419.104 /sec
                 0      cpu-migrations                   #    0.000 /sec
              2.39 msec task-clock                       #    0.001 CPUs utilized
       1.605512149 seconds time elapsed
```

- The subshell: 11 voluntary switches after 0.5 s and 0 involuntary. Each `wait()` for a `sleep` child blocks, which means `schedule()` is called voluntarily.
- `yes`: only 2 + 2 switches in 3 s of pure CPU work. A CPU-bound task is preempted only when another task wants *its* CPU; with 8 vCPUs there was usually a free one. Involuntary switches grow with contention, not with time.
- `perf stat` on `sleep 1`: 1 context switch (the one sleep) and 2.39 ms of CPU in 1.6 s of wall time.

## 5. Edge cases & pitfalls

- **A syscall is not a context switch** (note 02). `getpid()` never calls `schedule()` unless `need_resched` is already set on exit.
- **"The kernel saves all registers on a context switch."** It saves 6 in `__switch_to_asm`; the rest were saved by the compiler or at kernel entry.
- **FPU state is lazy on restore**, eager on save (since v4.x Linux dropped fully-lazy FPU switching because of the LazyFP vulnerability). VERSION-DEPENDENT detail.
- **`__switch_to` can't be traced with function_graph** (`__notrace_funcgraph`, process_64.c L610): the function returns on a different stack than it was called on.
- **Threads switch faster than processes** only by the `CR3`/TLB part; scheduling cost is the same.
- **`last` in `switch_to(prev, next, last)`**: when B resumes, its local `prev` variable is stale (it held whatever B saw when *it* was switched out). The macro returns the real previous task so `finish_task_switch()` cleans up the right one.
- **Interrupts are off** during the switch (`rq` lock held, `_irqs_off` suffix); `finish_task_switch()` re-enables them.

## 6. Exam-style key points

- Context switch = `__schedule()` → `context_switch()` → `switch_mm_irqs_off()` (+`CR3`) → `switch_to()` → `__switch_to_asm` → `__switch_to()`.
- User registers are in `pt_regs` (saved at entry); the switch saves only `rbx, rbp, r12–r15` + `rsp` (in `thread.sp`).
- The real switch is one instruction: `movq TASK_threadsp(%rsi), %rsp`.
- `CR3` is skipped for same-`mm` threads and for kernel threads (lazy TLB, `active_mm`).
- `__switch_to()` updates `current_task` and `cpu_current_top_of_stack` (used by the next syscall entry).
- New tasks start at `ret_from_fork_asm` via a fake `inactive_task_frame`.
- Voluntary (blocking) vs involuntary (preemption) switches are counted in `/proc/<pid>/status`.
- Indirect cost (cache/TLB) often exceeds direct cost.

## 7. Links

- Lesson: [§2.5 What does a context switch actually switch?](../lesson.en.md#25-what-does-a-context-switch-actually-switch)
- Walkthrough: [§7 Context switch](../kernel-walkthrough.en.md#7-context-switch-context_switch--__switch_to_asm--__switch_to)
- Lab: [05 ftrace vfs_read](../labs/05-ftrace-vfs-read/README.md) extension; Module 02 lab 3 (ping-pong cost)
- Quiz: questions 10, 14 and oral question O2 in [`quiz.en.md`](../quiz.en.md)
