# Lab 03.6 — Deadlock: create it, read it from a thread dump, detect it before it happens

> **Part D (lockdep) is VM ONLY** and needs the `--lockdep` kernel flavor from lab 00.3 (`6.18.63-aos-lockdep`, `CONFIG_PROVE_LOCKING=y`). It loads a kernel module. Take a snapshot first. Parts A–C are ordinary user-space programs.

**Goal:** produce an AB-BA deadlock, diagnose it from `gdb` and `/proc`, get the same diagnosis from ThreadSanitizer and helgrind on a run that does *not* hang, and fix it with a global lock order.

Notes: [09](../../notes/09-deadlock-coffman-lockdep.en.md). Lesson §4.7. Walkthrough §5 (`check_noncircular()`).

## Steps

```bash
cd ~/work/03-concurrency/06-deadlock
gcc -Wall -Wextra -O2 -g -pthread deadlock.c -o deadlock
gcc -Wall -Wextra -O1 -g -fsanitize=thread -pthread deadlock.c -o deadlock-tsan

# A. make it hang, then look at it from outside
./deadlock hang &                    # prints its pid, then never finishes
P=$!; sleep 1
ps -L -o pid,lwp,stat,wchan:20,comm -p $P
sudo cat /proc/$P/task/*/stack
sudo gdb -p $P -batch -ex "thread apply all bt"
kill -9 $P

# B. detect the order without hanging
./deadlock quick                     # runs the two transfers one after the other: no hang
./deadlock-tsan quick                # TSan: lock-order-inversion
valgrind --tool=helgrind ./deadlock quick

# C. the fix
./deadlock ordered
./deadlock-tsan ordered              # no report

# D. VM ONLY, on the lockdep kernel
cd lockdep && make && sudo insmod lockdep_abba.ko && sudo dmesg | tail -40; sudo rmmod lockdep_abba
```

If TSan aborts with `unexpected memory mapping`, prefix it with `setarch x86_64 -R`.

## Code

```c
static void transfer(struct account *from, struct account *to, long amount)
{
    struct account *first = from, *second = to;
    if (g_ordered && (uintptr_t)to < (uintptr_t)from) {   // global order: by address
        first = to;
        second = from;
    }
    pthread_mutex_lock(&first->lock);
    if (g_sleep)
        usleep(100000);            // widen the window: the other thread takes its first lock
    pthread_mutex_lock(&second->lock);
    /* ... move the money ... */
}
```

`a_to_b` calls `transfer(&A, &B)`, `b_to_a` calls `transfer(&B, &A)`. Modes: `hang` (both threads at once, with a sleep between the two locks), `quick` (one after the other: same inverted order, no hang), `ordered` (lower address first).

`lockdep/lockdep_abba.c` does the same in the kernel with two `DEFINE_MUTEX`es, A→B then B→A in one thread, so it never actually blocks.

## Expected output

> Parts A–C captured on `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, gcc 13.3.0, gdb 15.1, valgrind 3.22.0), 2026-11-15. Part D is **UNVERIFIED** (see below).

**A. The hang, seen from outside**

```
$ ./deadlock hang &
pid=27823 mode=hang
$ ps -L -o pid,lwp,stat,wchan:20,comm -p 27823
    PID     LWP STAT WCHAN                COMMAND
  27823   27823 Sl   futex_do_wait        deadlock
  27823   27826 Sl   futex_do_wait        deadlock
  27823   27827 Sl   futex_do_wait        deadlock
$ sudo cat /proc/27823/task/27826/stack
[<0>] futex_do_wait+0x48/0x90
[<0>] __futex_wait+0x9c/0x120
[<0>] futex_wait+0x7b/0x140
[<0>] do_futex+0x102/0x260
[<0>] __x64_sys_futex+0x120/0x210
[<0>] x64_sys_call+0x9c8/0x2350
[<0>] do_syscall_64+0x82/0xe30
[<0>] entry_SYSCALL_64_after_hwframe+0x76/0x7e
```

```
$ sudo gdb -p 27823 -batch -ex "thread apply all bt"
...
Thread 3 (Thread 0x7c4ab39ff6c0 (LWP 27826) "deadlock"):
#0  futex_wait (private=0, expected=2, futex_word=0x646ef2c58020 <g_acc_b>) at ../sysdeps/nptl/futex-internal.h:146
#1  __GI___lll_lock_wait (futex=futex@entry=0x646ef2c58020 <g_acc_b>, private=0) at ./nptl/lowlevellock.c:49
#2  0x00007c4ab3aa01c1 in lll_mutex_lock_optimized (mutex=0x646ef2c58020 <g_acc_b>) at ./nptl/pthread_mutex_lock.c:48
#3  ___pthread_mutex_lock (mutex=mutex@entry=0x646ef2c58020 <g_acc_b>) at ./nptl/pthread_mutex_lock.c:93
#4  0x0000646ef2c553e0 in transfer (from=from@entry=0x646ef2c58060 <g_acc_a>, to=to@entry=0x646ef2c58020 <g_acc_b>, amount=amount@entry=10) at deadlock.c:39
#5  0x0000646ef2c55470 in a_to_b (arg=<optimized out>) at deadlock.c:49
...
Thread 2 (Thread 0x7c4ab31fe6c0 (LWP 27827) "deadlock"):
#0  futex_wait (private=0, expected=2, futex_word=0x646ef2c58060 <g_acc_a>) at ../sysdeps/nptl/futex-internal.h:146
#1  __GI___lll_lock_wait (futex=futex@entry=0x646ef2c58060 <g_acc_a>, private=0) at ./nptl/lowlevellock.c:49
...
#4  0x0000646ef2c553e0 in transfer (from=from@entry=0x646ef2c58020 <g_acc_b>, to=to@entry=0x646ef2c58060 <g_acc_a>, amount=amount@entry=20) at deadlock.c:39
#5  0x0000646ef2c55440 in b_to_a (arg=<optimized out>) at deadlock.c:56
...
Thread 1 (Thread 0x7c4ab3cd3740 (LWP 27823) "deadlock"):
...
#3  0x00007c4ab3a9e863 in __pthread_clockjoin_ex (...) at ./nptl/pthread_join_common.c:102
#5  0x0000646ef2c552a6 in main (argc=<optimized out>, argv=<optimized out>) at deadlock.c:74
```

**B. Detection without a hang**

```
$ ./deadlock quick
pid=27930 mode=quick
done: A=1010 B=990
$ setarch x86_64 -R ./deadlock-tsan quick       # plain ./deadlock-tsan aborted: "unexpected memory mapping"
pid=30731 mode=quick
==================
WARNING: ThreadSanitizer: lock-order-inversion (potential deadlock) (pid=30731)
  Cycle in lock order graph: M0 (0x555555558060) => M1 (0x555555558020) => M0

  Mutex M1 acquired here while holding mutex M0 in thread T1:
    #0 pthread_mutex_lock ... (libtsan.so.2+0x59a13)
    #1 transfer .../06-deadlock/deadlock.c:39 (deadlock-tsan+0x13bc)
    #2 a_to_b .../06-deadlock/deadlock.c:49 (deadlock-tsan+0x1497)

  Mutex M0 acquired here while holding mutex M1 in thread T2:
    #0 pthread_mutex_lock ... (libtsan.so.2+0x59a13)
    #1 transfer .../06-deadlock/deadlock.c:39 (deadlock-tsan+0x13bc)
    #2 b_to_a .../06-deadlock/deadlock.c:56 (deadlock-tsan+0x145e)
...
SUMMARY: ThreadSanitizer: lock-order-inversion (potential deadlock) .../06-deadlock/deadlock.c:39 in transfer
==================
ThreadSanitizer: reported 1 warnings
done: A=1010 B=990
$ valgrind --tool=helgrind ./deadlock quick
...
==28122== Thread #3: lock order "0x10C060 before 0x10C020" violated
==28122==
==28122== Observed (incorrect) order is: acquisition of lock at 0x10C020
==28122==    by 0x1093CD: transfer (deadlock.c:36)
==28122==    by 0x10943F: b_to_a (deadlock.c:56)
==28122==
==28122==  followed by a later acquisition of lock at 0x10C060
==28122==    by 0x1093DF: transfer (deadlock.c:39)
==28122==    by 0x10943F: b_to_a (deadlock.c:56)
==28122==
==28122== Required order was established by acquisition of lock at 0x10C060
==28122==    by 0x1093CD: transfer (deadlock.c:36)
==28122==    by 0x10946F: a_to_b (deadlock.c:49)
...
==28122==  Address 0x10c060 is 0 bytes inside data symbol "g_acc_a"
==28122==  Address 0x10c020 is 0 bytes inside data symbol "g_acc_b"
done: A=1010 B=990
==28122== ERROR SUMMARY: 1 errors from 1 contexts (suppressed: 0 from 0)
```

**C. The fix**

```
$ ./deadlock ordered
pid=27933 mode=ordered
done: A=1010 B=990
$ setarch x86_64 -R ./deadlock-tsan ordered
pid=31096 mode=ordered
done: A=1010 B=990
```

**D. lockdep — UNVERIFIED.** The running kernel has `# CONFIG_PROVE_LOCKING is not set` (from `/boot/config-6.18.63-061863-generic`), and the module could not even be built against it: that mainline kernel was compiled with gcc-15, which is not installed in the VM, and gcc 13 rejects the kernel's `-fmin-function-alignment=16`:

```
$ make CC=gcc
warning: the compiler differs from the one used to build the kernel
gcc: error: unrecognized command-line option '-fmin-function-alignment=16'; did you mean '-flimit-function-alignment'?
```

On the self-built `--lockdep` kernel from lab 00.3 (compiled with the VM's own gcc 13) the module builds normally. Expected report header, from the source (`kernel/locking/lockdep.c` L1990): `WARNING: possible circular locking dependency detected`, followed by the two lock names (`lock_b`, `lock_a`), the dependency chain with stack traces, and a "Possible unsafe locking scenario" table showing `lock(lock_a); lock(lock_b); lock(lock_a); lock(lock_b);` per CPU. Replace this paragraph with your real `dmesg` once you run it.

## What to observe

1. **A deadlock does not spin.** All three threads are in state `Sl` (sleeping) in `futex_do_wait`; the process uses 0% CPU. Each kernel stack is the futex wait path from the walkthrough: `entry_SYSCALL_64` → `do_syscall_64` → `__x64_sys_futex` → `do_futex` → `futex_wait` → `__futex_wait` → `futex_do_wait`.
2. **gdb shows the cycle directly.** Thread LWP 27826 (`a_to_b`) waits for `g_acc_b`; LWP 27827 (`b_to_a`) waits for `g_acc_a`; both at `deadlock.c:39`, the *second* lock. `expected=2` is glibc's "locked, with waiters" state — the same 0/1/2 protocol you build in lab 04. The main thread is only waiting in `pthread_join`.
3. **TSan and helgrind find it on a run that did not hang** (`done: A=1010 B=990`): they record lock *order* (edges M0→M1 and M1→M0) rather than waiting for a hang. That is the lockdep idea in user space.
4. **The fix removes the report.** With address ordering both threads take `g_acc_b` (lower address) first, so there is no cycle and TSan prints nothing.
5. **Lockdep cannot be shown on a stock kernel.** Distro and mainline builds leave `CONFIG_PROVE_LOCKING` off because it slows every lock operation and compiles out the mutex fast path (`__mutex_trylock_fast()` exists only `#ifndef CONFIG_DEBUG_LOCK_ALLOC`, `mutex.c` L169).

## Common pitfalls

| Symptom | Fix |
|---|---|
| `gdb -p`: `ptrace: Operation not permitted` | Ubuntu's Yama: use `sudo gdb -p`, or `echo 0 \| sudo tee /proc/sys/kernel/yama/ptrace_scope` (restore to 1) |
| `/proc/<pid>/task/*/stack` is empty or permission denied | needs root (`sudo cat`) |
| `quick` mode "works", so the bug is gone | the order is still inverted; only the timing hid it. TSan/helgrind report it |
| lockdep prints nothing | the running kernel lacks `CONFIG_PROVE_LOCKING`: `grep PROVE_LOCKING /boot/config-$(uname -r)`; or lockdep already turned itself off after an earlier report (`cat /proc/sys/kernel/prove_locking` / `dmesg`) |

## Extension

Five philosophers, five forks (mutexes), each philosopher locks left then right: write it, make it deadlock, then fix it **two different ways** (resource ordering; at most four philosophers at the table via a counting semaphore) and show both run 10 s without hanging and with TSan clean. Solution notes: [`solution/README.md`](solution/README.md).
