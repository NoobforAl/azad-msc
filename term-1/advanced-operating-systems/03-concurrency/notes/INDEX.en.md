# Module 03 notes — index

> Read in order. Each note has the same 7 sections: Summary · Explanation · Diagram · Worked example · Edge cases · Exam key points · Links. Farsi: [INDEX.fa.md](INDEX.fa.md).

| # | Note | Lesson § | Main kernel source (v6.18.63) | Labs | Quiz |
|---|---|---|---|---|---|
| 01 | [Race conditions & critical sections](01-race-conditions-critical-sections.en.md) | 4.1 | `READ_ONCE`/`WRITE_ONCE`, preemption & IRQs as concurrency sources | 01 | Q1, Q11 |
| 02 | [Atomics and the C11 memory model](02-atomics-c11-memory-model.en.md) | 4.2 | `atomic_long_try_cmpxchg_acquire()`, `smp_store_release()` | 01, 05 | Q2 |
| 03 | [x86-TSO vs weaker models; barriers](03-x86-tso-and-barriers.en.md) | 4.2 | `arch/x86/include/asm/barrier.h`, futex `smp_mb()` pairing | 05 | Q3, Q15 |
| 04 | [Spinlocks: ticket → MCS → qspinlock](04-spinlocks-qspinlock.en.md) | 4.3 | `include/linux/spinlock.h`, `kernel/locking/qspinlock.c` | 04 | Q4, Q8 |
| 05 | [Mutex and optimistic spinning](05-mutex-optimistic-spinning.en.md) | 4.3 | `kernel/locking/mutex.c` (`mutex_lock()` L269) | 04 | Q4, Q7 |
| 06 | [Semaphores & condition variables](06-semaphores-condition-variables.en.md) | 4.5 | `kernel/locking/semaphore.c`, `include/linux/wait.h` | 02, 03 | Q13, Q14 |
| 07 | [Futex: the user/kernel split](07-futex-user-kernel-split.en.md) | 4.4 | `kernel/futex/syscalls.c`, `waitwake.c`, `core.c` | 04 | Q9, Q10 |
| 08 | [RCU (and OpenBSD SMR)](08-rcu.en.md) | 4.6 | `include/linux/rcupdate.h`, `kernel/rcu/tree.c`, `tree_plugin.h` | — | Q5 |
| 09 | [Deadlock: Coffman, detection, lockdep](09-deadlock-coffman-lockdep.en.md) | 4.7 | `kernel/locking/lockdep.c` (`check_noncircular()`) | 06 | Q6, Q12 |
| 10 | [Classic problems](10-classic-problems.en.md) | 4.5 | `kernel/locking/rwsem.c`, `percpu-rwsem.c` | 02, 03 | Q13, Q14 |

Suggested path: 01 → 02 → 03 (memory model), then 04 → 05 → 07 (lock implementations, bottom up), then 06 → 10 (waiting on conditions), then 08 (lock-free reading) and 09 (when it all goes wrong).
