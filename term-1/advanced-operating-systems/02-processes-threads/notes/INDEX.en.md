# Module 02 notes — index

> Persian: [`INDEX.fa.md`](INDEX.fa.md) · Lesson: [`../lesson.en.md`](../lesson.en.md)

Read in order. Each note has the same 7 sections: summary, explanation, diagram, worked example (real code or real VM output), pitfalls, exam key points, links.

| # | Note | Main kernel code | Labs | Quiz |
|---|---|---|---|---|
| 01 | [`task_struct` anatomy](01-task-struct-anatomy.en.md) | `include/linux/sched.h` L815, `fs/proc/array.c` | 02.1, 02.6 | Q1, Q7 |
| 02 | [fork, vfork, clone flags](02-fork-vfork-clone-flags.en.md) | `kernel/fork.c` `kernel_clone()`, `copy_process()`, `copy_mm()` | 02.1, 02.2 | Q2, Q8 |
| 03 | [execve and ELF loading](03-execve-and-elf-loading.en.md) | `fs/exec.c` `bprm_execve()`, `begin_new_exec()`; `fs/binfmt_elf.c` | 02.1 | Q3, Q9 |
| 04 | [process states, exit and wait](04-process-states-and-wait.en.md) | `kernel/exit.c` `exit_notify()`, `kernel/signal.c` `do_notify_parent()` | 02.1 | Q4, Q14 |
| 05 | [threads share an mm](05-threads-share-an-mm.en.md) | `kernel/fork.c` `tgid` assignment; Go runtime G/M/P | 02.2, 02.6 | Q1, Q12 |
| 06 | [scheduling classes](06-scheduling-classes.en.md) | `kernel/sched/sched.h` `DEFINE_SCHED_CLASS`, `vmlinux.lds.h` `SCHED_DATA` | 02.5 | Q5, Q13 |
| 07 | [EEVDF](07-eevdf.en.md) | `kernel/sched/fair.c` `pick_eevdf()`, `update_deadline()` | 02.5 | Q6, Q13 |
| 08 | [IPC: pipes, shm, sockets](08-ipc-pipes-shm-sockets.en.md) | `fs/pipe.c` `anon_pipe_read()`, `ipc/shm.c` `newseg()` | 02.1, 02.3 | Q10, Q11 |

The context switch itself (`context_switch()`, `switch_to()`) is covered in the lesson §2.8, the walkthrough §6 and lab 02.3; Module 01 note 05 covers the register-level details.
