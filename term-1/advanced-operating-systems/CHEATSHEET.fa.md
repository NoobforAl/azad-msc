<div dir="rtl">

# برگهٔ خلاصه — سیستم‌عامل پیشرفته

برای هر ماژول یک صفحه: اصطلاح‌های کلیدی، تابع‌های کلیدی kernel و دستورهای کلیدی. نسخه‌ها: Linux **v6.18.63**، OpenBSD **8cada8c**، معماری x86-64. محل تابع‌ها از walkthrough هر ماژول آمده و همه با `_shared/sources/cite.sh` از سورس محلی کپی شده‌اند. برای دیدن هر کدام: <bdi dir="ltr">bash _shared/sources/cite.sh linux &lt;path&gt; &lt;function&gt;</bdi>. دستورهایی که با `#` علامت خورده‌اند root لازم دارند و کارهای سطح kernel را داخل VM اجرا کنید.

---

## ۰۱ · معماری و ساختار Kernel

**اصطلاح‌ها**
- **monolithic / microkernel / hybrid / exokernel:** تفاوت در این است که driverها و فایل‌سیستم کجا اجرا می‌شوند: داخل kernel یا در سرویس‌های فضای کاربر.
- **CPL:** سطح دسترسی فعلی، یعنی دو بیت پایین `CS`. ring 0 یعنی kernel و ring 3 یعنی کاربر.
- **trap / fault / abort:** استثناهای همگام. trap پس از دستور ادامه می‌دهد، fault همان دستور را دوباره اجرا می‌کند و abort برنمی‌گردد.
- **interrupt:** ناهمگام، از دستگاه یا تایمر APIC؛ vectorها از **IDT** می‌گذرند.
- **`syscall` / `sysret`:** گذر سریع بین ringها از طریق MSRها (`LSTAR` نشانی ورودی را نگه می‌دارد). `rcx` نشانی برگشت کاربر و `r11` مقدار RFLAGS را نگه می‌دارد.
- **vDSO:** کدی که kernel در فضای کاربر map می‌کند تا `clock_gettime` بدون عوض کردن ring اجرا شود.
- **context switch:** ذخیره و بازیابی registerها، عوض کردن پشتهٔ kernel و عوض کردن `CR3` (یعنی mm)، مگر برای kernel thread یا وقتی mm یکسان باشد.

**تابع‌های kernel**

</div>

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

<div dir="rtl">

در OpenBSD: تابع `syscall()` در <bdi dir="ltr">sys/arch/amd64/amd64/trap.c</bdi>، تابع `mi_syscall()` در <bdi dir="ltr">sys/sys/syscall_mi.h</bdi>، `cpu_switchto` در `locore.S` و جدول syscallها در <bdi dir="ltr">sys/kern/syscalls.master</bdi>.

**دستورها**

</div>

```bash
strace -f -tt -e trace=%file,%desc cat /etc/hostname   # syscalls of one program
strace -c ls >/dev/null                                 # syscall count/time summary
grep -E ' (__x64_sys_read|do_syscall_64)$' /proc/kallsyms
cat /proc/interrupts; watch -d -n1 cat /proc/interrupts
sudo perf stat -e 'irq:*' -a sleep 1                    # irq tracepoints (tracefs needs root)
# trace-cmd record -p function_graph -g vfs_read --max-graph-depth 6 -F cat f   # ALWAYS filtered
```

<div dir="rtl">

---

## ۰۲ · پردازه‌ها و Threadها

**اصطلاح‌ها**
- **`task_struct`:** برای هر thread یکی. پردازه یعنی گروهی از threadها که `mm`، `files` و `signal` را با هم شریک‌اند.
- **پرچم‌های `clone`:** `CLONE_VM`، `CLONE_FILES`، `CLONE_FS`، `CLONE_SIGHAND` و `CLONE_THREAD` تعیین می‌کنند چه چیزی مشترک باشد. fork یعنی هیچ‌کدام و pthread یعنی همه.
- **`execve`:** mm را جایگزین می‌کند و ELF را از طریق handlerهای `binfmt` بار می‌کند. PID و fdها می‌مانند، به‌جز fdهایی که `O_CLOEXEC` دارند.
- **حالت‌ها:** `R`، `S`، `D` (وقفه‌ناپذیر)، `T`، و `Z` (zombie، تا وقتی والد `wait` کند).
- **scheduling classها به ترتیب اولویت:** stop ← deadline ← rt ← fair ← ext ← idle.
- **EEVDF (از 6.6 در کلاس fair):** **lag** یعنی سهمی که task طلبکار است. task با lag ≥ 0 **eligible** است. از میان eligibleها، آن‌که **virtual deadline** (برابر vruntime + slice/weight) زودتری دارد انتخاب می‌شود.
- **nice و weight:** هر پلهٔ nice وزن را حدود ۱.۲۵ برابر عوض می‌کند، پس نسبت سهم CPU حدود ۱.۲۵ به توان n است.
- **fair server** (VERSION-DEPENDENT): برای taskهای fair مقداری CPU کنار می‌گذارد تا RT کاملاً گرسنه‌شان نکند. اندازه‌گیری شده: spinner از نوع FIFO ۹۴٪ و task از نوع fair ۶٪.

**تابع‌های kernel**

</div>

| Function | File |
|---|---|
| `kernel_clone()` (L2578), `copy_process()`, `copy_mm()` | `kernel/fork.c` |
| `bprm_execve()` (L1756), `search_binary_handler()` | `fs/exec.c` |
| `__schedule()` (L6801), `__pick_next_task()`, `context_switch()` (L5293) | `kernel/sched/core.c` |
| `pick_eevdf()`, `vruntime_eligible()`, `update_deadline()` | `kernel/sched/fair.c` |
| `DEFINE_SCHED_CLASS` | `kernel/sched/sched.h` |
| `anon_pipe_read()` | `fs/pipe.c` |
| `newseg()` | `ipc/shm.c` |

<div dir="rtl">

در OpenBSD: `fork1()` در <bdi dir="ltr">sys/kern/kern_fork.c</bdi> (L350)، `sys_execve()` در `kern_exec.c`، `sched_chooseproc()` در `kern_sched.c` و `setpriority()` در `sched_bsd.c`. زمان‌بندی OpenBSD بر پایهٔ اولویت است و EEVDF ندارد.

**دستورها**

</div>

```bash
cat /proc/$PID/status | grep -E 'State|Threads|voluntary'; ls -l /proc/$PID/fd; cat /proc/$PID/maps
ls /proc/$PID/task                                       # threads = tasks
taskset -c 0 ./pingpong; chrt -f 10 ./spin; nice -n 5 ./spin
perf sched record -- sleep 5 && perf sched latency
bpftrace -e 'tracepoint:sched:sched_switch { @[args->prev_comm] = count(); }'
cat /sys/kernel/debug/sched/base_slice_ns                # EEVDF base slice (#)
```

<div dir="rtl">

---

## ۰۳ · همروندی و همگام‌سازی

**اصطلاح‌ها**
- **race، critical section و atomicity.**
- **ترتیب‌های C11:** `relaxed`، `acquire`، `release`، `acq_rel` و `seq_cst`.
- **x86-TSO:** storeها ممکن است در store buffer بمانند، پس تنها جابه‌جایی مجاز **store پیش از load** است. `mfence` یا دستوری با پیشوند `lock` جلویش را می‌گیرد (آزمون store-buffering).
- **spinlock:** busy-wait است و هرگز نمی‌خوابد. لینوکس **qspinlock** (صف MCS) دارد.
- **mutex:** می‌خوابد. پیش از خوابیدن، fast path (cmpxchg روی owner) و سپس **optimistic spinning** را امتحان می‌کند، تا وقتی owner در حال اجراست.
- **futex:** مسیر بدون رقابت در فضای کاربر می‌ماند و فقط برای انتظار یا بیدار کردن (`FUTEX_WAIT` / `FUTEX_WAKE`) وارد kernel می‌شود، روی یک hash bucket که کلیدش نشانی است.
- **RCU:** خواننده‌ها قفل نمی‌گیرند. نویسنده با `rcu_assign_pointer` منتشر می‌کند و پیش از آزاد کردن یک **grace period** صبر می‌کند، یعنی تا همهٔ CPUها از یک quiescent state بگذرند.
- **deadlock، شرط‌های Coffman:** انحصار متقابل، نگه‌داشتن و انتظار، نبود preemption و انتظار چرخه‌ای. **lockdep** چرخه‌های ترتیب قفل را در زمان اجرا پیدا می‌کند.
- **starvation:** مثلاً writer در `pthread_rwlock` وقتی اولویت با خواننده‌هاست.

**تابع‌های kernel**

</div>

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

<div dir="rtl">

در OpenBSD: `mtx_enter()` در `kern_lock.c`، `rw_do_enter_write()` در `kern_rwlock.c` و `futex_wait()` در `sys_futex.c`. همتای RCU در OpenBSD سازوکار **SMR** است (`smr_grace_wait()` در `kern_smr.c`).

**دستورها**

</div>

```bash
gcc -O2 -g -fsanitize=thread race.c -o race && ./race        # TSan report
strace -f -e trace=futex ./futex_mutex                        # syscalls only under contention
perf stat -e task-clock,context-switches ./race_mutex
valgrind --tool=helgrind ./deadlock
gdb -p $PID -batch -ex 'thread apply all bt'                  # see the wait cycle
grep PROVE_LOCKING /boot/config-$(uname -r)                   # lockdep needs the --lockdep kernel
```

<div dir="rtl">

---

## ۰۴ · مدیریت حافظه

**اصطلاح‌ها**
- **VMA:** یک ناحیه از فضای آدرس (`/proc/PID/maps`).
- **page table:** ۴ سطح (PGD←PUD←PMD←PTE) یا ۵ سطح (P4D). در 6.18 انتخاب هنگام بوت انجام می‌شود و `CONFIG_X86_5LEVEL` دیگر وجود ندارد.
- **TLB:** کش ترجمهٔ نشانی‌ها. با **PCID/ASID** هر context switch همه‌چیز را flush نمی‌کند. **shootdown** یعنی فرستادن IPI به CPUهای دیگر برای flush.
- **page fault:** **minor** (صفحه در حافظه هست)، **major** (I/O لازم است)، **invalid** (نتیجه SIGSEGV است).
- **demand paging؛ COW** (copy-on-write): پس از `fork` صفحه‌ها فقط‌خواندنی مشترک می‌شوند و با اولین نوشتن کپی می‌شوند.
- **buddy allocator:** بلوک‌هایی با اندازهٔ توانی از ۲ (order) در هر zone که هنگام آزاد شدن با buddy خود ادغام می‌شوند.
- **SLUB:** کش اشیا روی صفحه‌ها (`kmalloc-*`، `dentry`، `inode_cache`).
- **reclaim:** نسل‌های LRU یا **MGLRU**؛ `kswapd` در پس‌زمینه یا مستقیم هنگام فشار حافظه.
- **THP و hugetlb:** صفحه‌های ۲ مگابایتی و miss کمتر در TLB.
- **NUMA:** حافظهٔ محلی یا دور نسبت به یک node.
- **OOM killer:** قربانی را با `oom_badness` انتخاب می‌کند. در cgroupی که به `memory.max` رسیده، فقط taskهای همان cgroup.
- **thrashing:** working set از حافظه بزرگ‌تر است و major faultها منفجر می‌شوند.

**تابع‌های kernel**

</div>

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

<div dir="rtl">

در OpenBSD (UVM): ابتدا `upageflttrap()` در `trap.c`، سپس `uvm_fault()` و `uvm_fault_upper()` در <bdi dir="ltr">sys/uvm/uvm_fault.c</bdi>، که برای COW از لایه‌های amap و anon استفاده می‌کند.

**دستورها**

</div>

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

<div dir="rtl">

---

## ۰۵ · فایل‌سیستم و I/O

**اصطلاح‌ها**
- **اشیای VFS:** `super_block` (یک فایل‌سیستم mount‌شده)، `inode` (خود فایل)، `dentry` (کش نام به inode) و `file` (یک نمونهٔ باز با offset و flagها).
- **path lookup:** `namei` هر بار یک جزء از مسیر را می‌پیماید. اول **RCU-walk** بدون قفل، و اگر نشد **ref-walk**.
- **جدول fd:** برای هر پردازه، `files_struct` ← fdtable ← `struct file *`. با `dup` و `fork` شیء `file`، و در نتیجه offset، مشترک می‌شود.
- **page cache:** صفحه‌های فایل در folioها، از جمله **large folio** (در ext4 نسخهٔ 6.18). **writeback:** threadهای flusher صفحه‌های dirty را می‌نویسند؛ پارامترها `dirty_ratio` و `dirty_background_ratio`.
- **block layer:** `bio` ← صف‌های نرم‌افزاری و سخت‌افزاری **blk-mq** ← driver.
- **I/O schedulerها:** `none`، `mq-deadline`، `bfq` و `kyber`. پیش‌فرض loop device و NVMe، `none` است.
- **journaling (ext4 با `data=ordered`):** metadata در journal می‌رود و داده پیش از commit نوشته می‌شود. `fsync` یعنی ماندگاری.
- **io_uring:** حلقه‌های submission و completion مشترک با kernel؛ تعداد زیادی I/O با تعداد کمی syscall. بعضی عملیات به threadهای `io-wq` سپرده می‌شوند.
- **char device:** `major:minor` ← `file_operations`، از طریق `init_special_inode`.

**تابع‌های kernel**

</div>

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

<div dir="rtl">

در OpenBSD: `vfs_syscalls.c` و `vfs_lookup.c`، **buffer cache** در `vfs_bio.c` (به‌جای page cache یکپارچه)، و `bufq_nscan_dequeue()` در `kern_bufq.c`.

**دستورها**

</div>

```bash
strace -e trace=openat,read,close cat f
bpftrace -e 'kprobe:vfs_read /comm == "cat"/ { @[kstack(6)] = count(); }'
cat /sys/block/loop0/queue/scheduler; echo mq-deadline > /sys/block/loop0/queue/scheduler  # (#)
fio --name=r --filename=/dev/loop0 --rw=randread --bs=4k --direct=1 --runtime=20 --iodepth=16
grep -E 'Dirty|Writeback' /proc/meminfo
# crash test (VM): dmsetup create flaky --table "0 $SZ flakey /dev/loop0 0 5 5"; dmsetup suspend --nolockfs
```

<div dir="rtl">

---

## ۰۶ · سیستم‌عامل توزیع‌شده و مجازی‌سازی

**اصطلاح‌ها**
- **معنای RPC:** at-most-once، at-least-once و «exactly-once» (که یعنی at-least-once به‌علاوهٔ idempotency یا جدول حذف تکراری).
- **ساعت Lamport:** از a→b نتیجه می‌شود L(a) < L(b)، اما عکسش نه. **ساعت برداری:** a→b اگر و فقط اگر V(a) < V(b)، پس همروندی را تشخیص می‌دهد.
- **همگام‌سازی ساعت:** NTP (میلی‌ثانیه)، PTP (میکرو یا نانوثانیه) و `chrony`.
- **snapshot توزیع‌شده:** markerهای Chandy–Lamport.
- **deadlock توزیع‌شده:** گراف انتظار میان چند سایت.
- **replication و quorum:** پیش‌درآمدی بر consensus (Raft/Paxos).
- **hypervisor نوع ۱ و ۲؛ trap-and-emulate:** حالت root و non-root در VT-x، **VM exit** و VMCS. **EPT** یعنی ترجمهٔ نشانی سطح دوم.
- **KVM:** `/dev/kvm` ← fd ماشین ← fd هر vCPU. `KVM_RUN` thread مربوط به vCPU را اجرا می‌کند تا exitی رخ دهد که فضای کاربر (QEMU) رسیدگی‌اش کند.
- **container:** namespaceها (pid، mnt، net، uts، ipc، user، cgroup، time)، به‌علاوهٔ محدودیت‌های **cgroup v2** (`memory.max`، `pids.max`، `cpu.max`) و `pivot_root`.

**تابع‌های kernel**

</div>

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

<div dir="rtl">

OpenBSD نه namespace دارد نه cgroup. hypervisor آن **vmm(4)** است: `vmmioctl()` در <bdi dir="ltr">sys/dev/vmm/vmm.c</bdi> و `vmx_handle_exit()` در `vmm_machdep.c`. پاسخ OpenBSD به جداسازی، **pledge/unveil** است.

**دستورها**

</div>

```bash
unshare --user --map-root-user --pid --fork --mount-proc bash -c 'echo $$; ps'
lsns; ls -l /proc/$$/ns
mkdir /sys/fs/cgroup/c && echo 20 > /sys/fs/cgroup/c/pids.max && echo $$ > /sys/fs/cgroup/c/cgroup.procs  # (#)
ls -l /dev/kvm; grep -cE 'vmx|svm' /proc/cpuinfo; systemd-detect-virt
perf kvm stat record -a sleep 10 && perf kvm stat report     # on a KVM host
```

<div dir="rtl">

---

## ۰۷ · بی‌درنگ و موضوع‌های پژوهشی

**اصطلاح‌ها**
- **real-time سخت، firm و نرم:** از دست دادن deadline به ترتیب یعنی شکست، نتیجهٔ بی‌ارزش، یا افت کیفیت.
- **WCET:** بدترین زمان اجرا. **jitter** و **latency**.
- **RMS:** اولویت ایستا بر اساس دوره. کران Liu–Layland برابر U ≤ n(2^{1/n}−1) است که به ln 2 یعنی حدود ۰.۶۹ میل می‌کند.
- **EDF:** پویا، بر اساس زودترین deadline، و بهینه تا U ≤ 1.
- **`SCHED_DEADLINE`:** سه پارامتر runtime، deadline و period با throttle از نوع **CBS**. اگر پهنای باند بیش از حد شود، admission control با `EBUSY` رد می‌کند.
- **priority inversion:** task با اولویت متوسط، دارندهٔ قفلِ کم‌اولویت را کنار می‌زند و task پراولویت منتظر می‌ماند (Mars Pathfinder، ۱۹۹۷). دو راه‌حل: **inheritance** (`PTHREAD_PRIO_INHERIT`، با `FUTEX_LOCK_PI` و rt_mutex) و **ceiling** (`PTHREAD_PRIO_PROTECT`).
- **`PREEMPT_RT`:** از 6.12 در mainline است، با شرط <bdi dir="ltr">depends on EXPERT &amp;&amp; ARCH_SUPPORTS_RT</bdi>. spinlockها به rt_mutex خوابنده تبدیل می‌شوند و IRQها thread‌دار می‌شوند. `uname -v` عبارت `PREEMPT_RT` را نشان می‌دهد.
- **PREEMPT_DYNAMIC:** حالت‌های `none`، `voluntary`، `full` و `lazy` که هنگام بوت یا از debugfs انتخاب می‌شوند.
- **seccomp-BPF:** فیلتر cBPF روی `seccomp_data` (nr، arch، args) که یکی از ALLOW، ERRNO، KILL یا TRAP را برمی‌گرداند.
- **LSM:** hookهای داخل kernel. **Landlock:** sandbox بدون نیاز به دسترسی ویژه و قابل روی‌هم‌گذاری، برای دسترسی فایل‌سیستم و پورت TCP، با نسخه‌بندی ABI.
- **خواندن مقاله در ۳ مرحله:** مرور سریع (۵ دقیقه)، فهمیدن (۱ ساعت)، بازپیاده‌سازی یا نقد.

**تابع‌های kernel**

</div>

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

<div dir="rtl">

در OpenBSD: `pledge_syscall()` در <bdi dir="ltr">sys/kern/kern_pledge.c</bdi> (L537) و `unveil_check_final()` در `kern_unveil.c`. ساده است (رشته‌های promise)، در حالی که seccomp و Landlock انعطاف بیشتری دارند و پیچیده‌ترند.

**دستورها**

</div>

```bash
cyclictest -m -S -p 80 -i 200 -D 60 -q -h 400 > hist.txt       # (#) latency histogram
cat /sys/kernel/debug/sched/preempt; uname -v                    # preempt mode / PREEMPT_RT
taskset -c 0 ./inversion none; taskset -c 0 ./inversion inherit
strace -f -e trace=futex ./inversion inherit                     # FUTEX_LOCK_PI
chrt -d --sched-runtime 5000000 --sched-deadline 10000000 --sched-period 10000000 0 ./task
cat /sys/kernel/security/lsm; grep Seccomp /proc/$PID/status
```
