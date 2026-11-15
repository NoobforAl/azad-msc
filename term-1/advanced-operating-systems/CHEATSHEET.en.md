# Cheatsheet — Advanced Operating Systems

- **One page per module:** key terms, key kernel functions, key commands.
- **Pins:** Linux **v6.18.63**, OpenBSD **8cada8c**, x86-64.
- **Function locations:** taken from the module walkthroughs; each was copied with `_shared/sources/cite.sh` from the local checkout. Look any of them up with `bash _shared/sources/cite.sh linux <path> <function>`.
- **Root:** commands marked `#` need root; run kernel-level ones in the VM.

---

## 01 · Architecture & Kernel Structure

**Terms**
- **monolithic / microkernel / hybrid / exokernel:** where drivers and file systems run (kernel space vs user-space servers).
- **CPL:** current privilege level, the low 2 bits of `CS`. Ring 0 is the kernel, ring 3 is user.
- **trap / fault / abort:** synchronous exceptions. A trap resumes *after* the instruction, a fault *re-executes* it, an abort doesn't return.
- **interrupt:** asynchronous, from a device or the APIC timer. Vectors go through the **IDT**.
- **`syscall` / `sysret`:** fast ring transition via MSRs (`LSTAR` holds the entry address). `rcx` gets the user RIP and `r11` gets RFLAGS.
- **vDSO:** kernel-mapped user code, so `clock_gettime` runs with no ring switch.
- **context switch:** save and restore registers, switch the kernel stack, switch `CR3` (the mm) unless it's a kernel thread or the same mm.

**Kernel functions**

| Function | File |
|---|---|
| `entry_SYSCALL_64` | `arch/x86/entry/entry_64.S` (L87) |
| `do_syscall_64()` (`noinstr`) | `arch/x86/entry/syscall_64.c` (L87) |
| `x64_sys_call()` (switch over the table) | `arch/x86/entry/syscall_64.c` (L35) |
| syscall table | `arch/x86/entry/syscalls/syscall_64.tbl` |
| `SC_X86_64_REGS_TO_ARGS` | `arch/x86/include/asm/syscall_wrapper.h` |
| `idt_syscall_init()` | `arch/x86/kernel/cpu/common.c` |
| `common_interrupt` | `arch/x86/kernel/irq.c` |
| `__handle_irq_event_percpu()` | `kernel/irq/handle.c` |
| `context_switch()` | `kernel/sched/core.c` |
| `__switch_to_asm` | `arch/x86/entry/entry_64.S` |
| `__switch_to()` | `arch/x86/kernel/process_64.c` |

OpenBSD: `syscall()` in `sys/arch/amd64/amd64/trap.c`, `mi_syscall()` in `sys/sys/syscall_mi.h`, `cpu_switchto` in `locore.S`, and the table in `sys/kern/syscalls.master`.

**Commands**
```bash
strace -f -tt -e trace=%file,%desc cat /etc/hostname   # syscalls of one program
strace -c ls >/dev/null                                 # syscall count/time summary
grep -E ' (__x64_sys_read|do_syscall_64)$' /proc/kallsyms
cat /proc/interrupts; watch -d -n1 cat /proc/interrupts
sudo perf stat -e 'irq:*' -a sleep 1                    # irq tracepoints (tracefs needs root)
# trace-cmd record -p function_graph -g vfs_read --max-graph-depth 6 -F cat f   # ALWAYS filtered
```

---

## 02 · Processes & Threads

**Terms**
- **`task_struct`:** one per thread. A process is a thread group sharing `mm`, `files`, `signal`.
- **`clone` flags:** `CLONE_VM`, `CLONE_FILES`, `CLONE_FS`, `CLONE_SIGHAND`, `CLONE_THREAD` decide what is shared. fork means none of them; a pthread means all of them.
- **`execve`:** replaces the mm and loads the ELF via `binfmt` handlers. PID and fds survive, except fds marked `O_CLOEXEC`.
- **states:** `R`, `S`, `D` (uninterruptible), `T`, `Z` (zombie until parent `wait`s).
- **sched classes (high to low priority):** stop → deadline → rt → fair → ext → idle.
- **EEVDF (fair class since 6.6):**
  - **lag** = what a task is owed. A task is **eligible** if its lag is ≥ 0.
  - The scheduler picks the eligible task with the earliest **virtual deadline** (vruntime + slice/weight).
- **nice → weight:** each nice step is about a 1.25× weight change, so the CPU share ratio is about 1.25ⁿ.
- **fair server (VERSION-DEPENDENT):** reserves CPU for fair tasks so RT tasks can't starve them completely (measured: FIFO spinner 94% vs fair task 6%).

**Kernel functions**

| Function | File |
|---|---|
| `kernel_clone()` (L2578), `copy_process()`, `copy_mm()` | `kernel/fork.c` |
| `bprm_execve()` (L1756), `search_binary_handler()` | `fs/exec.c` |
| `__schedule()` (L6801), `__pick_next_task()`, `context_switch()` (L5293) | `kernel/sched/core.c` |
| `pick_eevdf()`, `vruntime_eligible()`, `update_deadline()` | `kernel/sched/fair.c` |
| `DEFINE_SCHED_CLASS` | `kernel/sched/sched.h` |
| `anon_pipe_read()` | `fs/pipe.c` |
| `newseg()` | `ipc/shm.c` |

OpenBSD: `fork1()` in `sys/kern/kern_fork.c` (L350), `sys_execve()` in `kern_exec.c`, `sched_chooseproc()` in `kern_sched.c`, `setpriority()` in `sched_bsd.c`. OpenBSD schedules by priority; there is no EEVDF.

**Commands**
```bash
cat /proc/$PID/status | grep -E 'State|Threads|voluntary'; ls -l /proc/$PID/fd; cat /proc/$PID/maps
ls /proc/$PID/task                                       # threads = tasks
taskset -c 0 ./pingpong; chrt -f 10 ./spin; nice -n 5 ./spin
perf sched record -- sleep 5 && perf sched latency
bpftrace -e 'tracepoint:sched:sched_switch { @[args->prev_comm] = count(); }'
cat /sys/kernel/debug/sched/base_slice_ns                # EEVDF base slice (#)
```

---

## 03 · Concurrency & Synchronization

**Terms**
- **race / critical section / atomicity.**
- **C11 orders:** `relaxed`, `acquire`, `release`, `acq_rel`, `seq_cst`.
- **x86-TSO:** stores may be delayed in the store buffer, so **store→load reordering** is the only reordering allowed. `mfence` or a `lock`-prefixed instruction prevents it (store-buffering litmus).
- **spinlock:** busy-waits, never sleeps. Linux uses the **qspinlock** (MCS queue).
- **mutex:** sleeps. Before sleeping it tries a fast path (cmpxchg on the owner) and then **optimistic spinning** while the owner is running.
- **futex:** the uncontended path stays in user space; the kernel is entered only to wait or wake (`FUTEX_WAIT` / `FUTEX_WAKE`), on a hash bucket keyed by address.
- **RCU:**
  - Readers take no locks.
  - Writers publish with `rcu_assign_pointer`, then wait a **grace period** (every CPU passes a quiescent state) before freeing.
- **deadlock (Coffman conditions):** mutual exclusion, hold and wait, no preemption, circular wait. **lockdep** detects lock-order cycles at runtime.
- **starvation:** for example, a writer under `pthread_rwlock` when readers have priority.

**Kernel functions**

| Function | File |
|---|---|
| `spin_lock()` | `include/linux/spinlock.h` (L349) |
| `queued_spin_lock()` | `include/asm-generic/qspinlock.h` (L107) |
| `queued_spin_lock_slowpath()` | `kernel/locking/qspinlock.c` (L277) |
| `mutex_lock()` (L269), `__mutex_trylock_fast()` (L150), `mutex_spin_on_owner()` (L340), `__mutex_lock_common()` (L597) | `kernel/locking/mutex.c` |
| `do_futex()` | `kernel/futex/syscalls.c` (L112) |
| `futex_wait_setup()` (L620), `futex_wake()` (L172) | `kernel/futex/waitwake.c` |
| `rcu_read_lock()` (L863), `rcu_assign_pointer()` (L588) | `include/linux/rcupdate.h` |
| `synchronize_rcu()` | `kernel/rcu/tree.c` (L3341) |
| `check_noncircular()` | `kernel/locking/lockdep.c` (L2169) |
| `__rt_mutex_lock()` | `kernel/locking/rtmutex.c` (L1813) |

OpenBSD: `mtx_enter()` in `kern_lock.c`, `rw_do_enter_write()` in `kern_rwlock.c`, `futex_wait()` in `sys_futex.c`. **SMR** (`smr_grace_wait()` in `kern_smr.c`) is OpenBSD's counterpart to RCU.

**Commands**
```bash
gcc -O2 -g -fsanitize=thread race.c -o race && ./race        # TSan report
strace -f -e trace=futex ./futex_mutex                        # syscalls only under contention
perf stat -e task-clock,context-switches ./race_mutex
valgrind --tool=helgrind ./deadlock
gdb -p $PID -batch -ex 'thread apply all bt'                  # see the wait cycle
grep PROVE_LOCKING /boot/config-$(uname -r)                   # lockdep needs the --lockdep kernel
```

---

## 04 · Memory Management

**Terms**
- **VMA:** a region of the address space (`/proc/PID/maps`).
- **page table:** 4 levels (PGD→PUD→PMD→PTE) or 5 levels (P4D). In 6.18 the choice is made at boot (`CONFIG_X86_5LEVEL` is gone).
- **TLB:** caches translations. **PCID/ASID** tags entries so a context switch doesn't flush everything. **Shootdown** = an IPI to other CPUs to flush.
- **page fault:**
  - **minor:** the page is already in memory.
  - **major:** the page needs I/O.
  - **invalid:** the access is bad, so the kernel sends SIGSEGV.
- **demand paging; COW** (copy-on-write): after `fork`, pages are shared read-only and copied on the first write.
- **buddy allocator:** power-of-2 blocks (orders) per zone, merged with their buddy on free.
- **SLUB:** object caches on top of pages (`kmalloc-*`, `dentry`, `inode_cache`).
- **reclaim:** LRU or **MGLRU** generations, run by `kswapd` in the background or directly under pressure.
- **THP / hugetlb:** 2 MiB pages, fewer TLB misses.
- **NUMA:** memory is local or remote to a node.
- **OOM killer:** picks the victim by `oom_badness`; inside a cgroup at `memory.max`, only that cgroup's tasks are candidates.
- **thrashing:** the working set is larger than memory, so major faults explode.

**Kernel functions**

| Function | File |
|---|---|
| `exc_page_fault()` (L1483), `do_user_addr_fault()` (L1322) | `arch/x86/mm/fault.c` |
| `handle_mm_fault()` (L6490), `__handle_mm_fault()` (L6260), `handle_pte_fault()` (L6209), `do_anonymous_page()` (L5158), `do_wp_page()` (L4126) | `mm/memory.c` |
| `do_mmap()` | `mm/mmap.c` (L550) |
| `__rmqueue_smallest()` (L1932), `__free_one_page()` (L999) | `mm/page_alloc.c` |
| `__slab_alloc_node()` | `mm/slub.c` (L4887) |
| `kswapd()` (L7380), `shrink_lruvec()` (L5799) | `mm/vmscan.c` |
| `oom_badness()` | `mm/oom_kill.c` (L219) |
| `choose_new_asid()` (L252), `flush_tlb_mm_range()` (L1456) | `arch/x86/mm/tlb.c` |

OpenBSD (UVM): `upageflttrap()` in `trap.c`, then `uvm_fault()` / `uvm_fault_upper()` in `sys/uvm/uvm_fault.c`, which uses amap/anon layering for COW.

**Commands**
```bash
perf stat -e page-faults,minor-faults,major-faults ./touch anon
grep -E 'Rss|Pss|Shared|Private|AnonHugePages' /proc/$PID/smaps_rollup
# pagemap: read /proc/PID/pagemap (8 bytes per page, PFN needs root)
cat /sys/kernel/mm/transparent_hugepage/enabled
slabtop -o | head -15; grep -E '^(dentry|inode_cache)' /proc/slabinfo   # (#)
cat /proc/buddyinfo; cat /proc/pagetypeinfo | head
# cgroup v2 OOM test (VM):
mkdir /sys/fs/cgroup/t && echo 64M > /sys/fs/cgroup/t/memory.max && echo 0 > /sys/fs/cgroup/t/memory.swap.max
echo $$ > /sys/fs/cgroup/t/cgroup.procs; ./hog 256; cat /sys/fs/cgroup/t/memory.events
```

---

## 05 · File Systems & I/O

**Terms**
- **VFS objects:** `super_block` (a mounted fs), `inode` (the file itself), `dentry` (a name→inode cache entry), `file` (an open instance: offset, flags).
- **path lookup:** `namei` walks one component at a time. **RCU-walk** runs lockless first and falls back to **ref-walk**.
- **fd table:** per process, `files_struct` → fdtable → `struct file *`. `dup` and `fork` share the `file`, so they share the offset.
- **page cache:** file pages in folios, which can be **large folios** (ext4 in 6.18). **writeback:** dirty pages are flushed by flusher threads; `dirty_ratio` / `dirty_background_ratio`.
- **block layer:** `bio` → **blk-mq** software and hardware queues → driver.
- **I/O schedulers:** `none`, `mq-deadline`, `bfq`, `kyber`. Loop devices and NVMe default to `none`.
- **journaling (ext4 `data=ordered`):** metadata is journaled and data is written before the commit. `fsync` = durable.
- **io_uring:** submission and completion rings shared with the kernel, so many I/Os cost few syscalls. Some operations get punted to `io-wq` worker threads.
- **char device:** `major:minor` → `file_operations`, via `init_special_inode`.

**Kernel functions**

| Function | File |
|---|---|
| `SYSCALL_DEFINE3(read)` (L722), `ksys_read()` (L704), `vfs_read()` (L552) | `fs/read_write.c` |
| `ext4_file_read_iter()` (L130) | `fs/ext4/file.c` |
| `ext4_sync_file()` (L164) | `fs/ext4/fsync.c` |
| `filemap_read()` (L2747) | `mm/filemap.c` |
| `do_filp_open()` (L4163), `walk_component()` (L2146) | `fs/namei.c` |
| `init_special_inode()` | `fs/inode.c` (L2548) |
| `submit_bio()` | `block/blk-core.c` (L908) |
| `io_submit_sqes()` | `io_uring/io_uring.c` (L2575) |

OpenBSD: `vfs_syscalls.c`, `vfs_lookup.c`, the **buffer cache** in `vfs_bio.c` (not a unified page cache), and `bufq_nscan_dequeue()` in `kern_bufq.c`.

**Commands**
```bash
strace -e trace=openat,read,close cat f
bpftrace -e 'kprobe:vfs_read /comm == "cat"/ { @[kstack(6)] = count(); }'
cat /sys/block/loop0/queue/scheduler; echo mq-deadline > /sys/block/loop0/queue/scheduler  # (#)
fio --name=r --filename=/dev/loop0 --rw=randread --bs=4k --direct=1 --runtime=20 --iodepth=16
grep -E 'Dirty|Writeback' /proc/meminfo
# crash test (VM): dmsetup create flaky --table "0 $SZ flakey /dev/loop0 0 5 5"; dmsetup suspend --nolockfs
```

---

## 06 · Distributed OS & Virtualization

**Terms**
- **RPC semantics:** at-most-once, at-least-once, "exactly-once" (= at-least-once + idempotency or a dedup table).
- **Lamport clock:** a→b ⇒ L(a) < L(b), but not the converse. **Vector clock:** a→b ⇔ V(a) < V(b), so it detects concurrency.
- **clock sync:** NTP (ms), PTP (µs/ns), `chrony`.
- **distributed snapshot:** Chandy–Lamport markers.
- **distributed deadlock:** wait-for-graph across sites.
- **replication, quorum:** consensus preview (Raft/Paxos).
- **hypervisor type 1/2; trap-and-emulate:** VT-x root/non-root mode, **VM exit**, VMCS. **EPT** = second-level address translation.
- **KVM:** `/dev/kvm` → VM fd → vCPU fd. `KVM_RUN` runs a vCPU thread until an exit that user space (QEMU) handles.
- **container:** namespaces (pid, mnt, net, uts, ipc, user, cgroup, time) plus **cgroups v2** limits (`memory.max`, `pids.max`, `cpu.max`) plus `pivot_root`.

**Kernel functions**

| Function | File |
|---|---|
| `kvm_dev_ioctl()`, `kvm_vcpu_ioctl()` (L4468) | `virt/kvm/kvm_main.c` |
| `vcpu_run()` (L11272), `emulator_pio_in_out()` (L8047) | `arch/x86/kvm/x86.c` |
| `handle_io()` | `arch/x86/kvm/vmx/vmx.c` (L5366) |
| `create_new_namespaces()` (L67), `unshare_nsproxy_namespaces()` (L203) | `kernel/nsproxy.c` |
| `copy_pid_ns()` | `kernel/pid_namespace.c` (L175) |
| `__cgroup_procs_write()` | `kernel/cgroup/cgroup.c` (L5390) |
| `pids_try_charge()` | `kernel/cgroup/pids.c` (L166) |
| `memory_max_write()` | `mm/memcontrol.c` (L4437) |

OpenBSD: no namespaces or cgroups. Its **vmm(4)** hypervisor has `vmmioctl()` in `sys/dev/vmm/vmm.c` and `vmx_handle_exit()` in `vmm_machdep.c`. For isolation it uses **pledge/unveil** instead.

**Commands**
```bash
unshare --user --map-root-user --pid --fork --mount-proc bash -c 'echo $$; ps'
lsns; ls -l /proc/$$/ns
mkdir /sys/fs/cgroup/c && echo 20 > /sys/fs/cgroup/c/pids.max && echo $$ > /sys/fs/cgroup/c/cgroup.procs  # (#)
ls -l /dev/kvm; grep -cE 'vmx|svm' /proc/cpuinfo; systemd-detect-virt
perf kvm stat record -a sleep 10 && perf kvm stat report     # on a KVM host
```

---

## 07 · Real-Time & Research

**Terms**
- **hard / firm / soft real-time:** a missed deadline is a failure, makes the result worthless, or degrades quality.
- **WCET:** worst-case execution time. **jitter**, **latency**.
- **RMS:**
  - Static priorities by period.
  - Liu–Layland bound: U ≤ n(2^{1/n}−1), which tends to ln 2 ≈ 0.69.
- **EDF:** dynamic scheduling by earliest deadline, optimal up to U ≤ 1.
- **`SCHED_DEADLINE`:** runtime/deadline/period with **CBS** throttling. Admission control rejects with `EBUSY` when bandwidth is exceeded.
- **priority inversion:** a medium-priority task preempts the low-priority lock holder while the high-priority task waits (Mars Pathfinder 1997). Fixes:
  - **inheritance:** `PTHREAD_PRIO_INHERIT`, which uses `FUTEX_LOCK_PI` and rt_mutex.
  - **ceiling:** `PTHREAD_PRIO_PROTECT`.
- **`PREEMPT_RT`:**
  - Mainline since 6.12; `depends on EXPERT && ARCH_SUPPORTS_RT`.
  - Spinlocks become sleeping rt_mutexes and IRQs run in threads.
  - `uname -v` shows `PREEMPT_RT`.
- **PREEMPT_DYNAMIC:** `none` / `voluntary` / `full` / `lazy`, selectable at boot or through debugfs.
- **seccomp-BPF:** a cBPF filter on `seccomp_data` (nr, arch, args) returns ALLOW, ERRNO, KILL or TRAP.
- **LSM:** hooks in the kernel. **Landlock:** an unprivileged, stackable sandbox for filesystem and TCP-port rights, versioned by ABI.
- **3-pass paper reading:** skim (5 min), understand (1 h), re-implement or critique.

**Kernel functions**

| Function | File |
|---|---|
| `config PREEMPT_RT` | `kernel/Kconfig.preempt` |
| `rt_mutex_adjust_prio()` (L527), `task_blocks_on_rt_mutex()` (L1265) | `kernel/locking/rtmutex.c` |
| `rt_mutex_setprio()` | `kernel/sched/core.c` (L7352) |
| `futex_lock_pi()` | `kernel/futex/pi.c` (L975) |
| `rt_spin_lock()` | `kernel/locking/spinlock_rt.c` (L38) |
| `__dl_overflow()` (L212), `update_curr_dl_se()` (L1480), `__checkparam_dl()` (L3580) | `kernel/sched/deadline.c` |
| `syscall_trace_enter()` | `kernel/entry/syscall-common.c` (L45) |
| `seccomp_run_filters()` (L404), `__seccomp_filter()` (L1274) | `kernel/seccomp.c` |
| `landlock_restrict_self()` | `security/landlock/syscalls.c` (L491) |
| `hook_file_open()` | `security/landlock/fs.c` (L1626) |

OpenBSD: `pledge_syscall()` in `sys/kern/kern_pledge.c` (L537) and `unveil_check_final()` in `kern_unveil.c`. It is simple (promise strings) where seccomp/Landlock are flexible but complex.

**Commands**
```bash
cyclictest -m -S -p 80 -i 200 -D 60 -q -h 400 > hist.txt       # (#) latency histogram
cat /sys/kernel/debug/sched/preempt; uname -v                    # preempt mode / PREEMPT_RT
taskset -c 0 ./inversion none; taskset -c 0 ./inversion inherit
strace -f -e trace=futex ./inversion inherit                     # FUTEX_LOCK_PI
chrt -d --sched-runtime 5000000 --sched-deadline 10000000 --sched-period 10000000 0 ./task
cat /sys/kernel/security/lsm; grep Seccomp /proc/$PID/status
```
