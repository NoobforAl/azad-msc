<div dir="rtl">

# برنامهٔ مطالعه — سیستم‌عامل پیشرفته

دو برنامه برای یک محتوا: **۱۰ هفته‌ای (آرام)** که همه‌چیز را پوشش می‌دهد، و **۴ هفته‌ای (فشرده)** که فقط مسیر اصلی را می‌رود. هر دو روزی **۶۰ تا ۹۰ دقیقه** فرض شده‌اند. هر روز یک خروجی مشخص دارد؛ چیزی که می‌سازید یا اجرا می‌کنید، نه فقط چیزی که می‌خوانید.

ستون «روز» یعنی *روز مطالعه*. اگر روزی جا ماند، از همان‌جا ادامه دهید و جلو نپرید.

## بودجهٔ زمانی

</div>

| ماژول | پوشه | Noteها | Labها | ساعت کامل (PLAN) | ۱۰ هفته‌ای | ۴ هفته‌ای |
|---|---|---|---|---|---|---|
| 00 Setup | `00-setup/` | guide | 3 | 4 | W1 | D1–2 |
| 01 Architecture | `01-architecture/` | 6 | 5 | 13 | W1–W2 | D3–6 |
| 02 Processes & Threads | `02-processes-threads/` | 8 | 6 | 16 | W2–W3 | D7–10 |
| 03 Concurrency | `03-concurrency/` | 10 | 6 | 18 | W4–W5 | D11–14 |
| 04 Memory | `04-memory/` | 10 | 6 | 18 | W5–W6 | D15–18 |
| 05 File Systems & I/O | `05-filesystems-io/` | 9 | 6 | 16 | W7–W8 | D19–22 |
| 06 Distributed & Virtualization | `06-distributed-virtualization/` | 8 | 5 | 14 | W8–W9 | D23–25 |
| 07 Real-Time & Research | `07-realtime-research/` | 6 | 5 | 11 | W10 | D26–27 |
| مرور | `CHEATSHEET.*`، همهٔ `quiz.*` | — | — | — | W10 | D28 |

<div dir="rtl">

- **۱۰ هفته‌ای:** ۷۰ روز × ۶۰ تا ۹۰ دقیقه، یعنی حدود ۷۰ تا ۱۰۵ ساعت. برای جا شدن در حدود ۱۱۰ ساعتِ PLAN، ویدیوها را با سرعت ۱.۲۵ ببینید و بعضی تمرین‌های تکمیلی *(ext)* را بگذارید برای وقتی که جلو هستید.
- **۴ هفته‌ای:** ۲۸ روز × ۹۰ دقیقه، یعنی حدود ۴۲ ساعت. فقط lesson هر ماژول، noteهای ستاره‌دار (★) و ۲ تا ۳ lab. بقیه در فهرست «دور دوم» آخر این فایل است.

**روال روزانه (هر دو برنامه):**
۱. **۱۰ دقیقه:** نکته‌های امتحانیِ دیروز را دوباره بخوانید.
۲. **۵۰ تا ۷۰ دقیقه:** کار همان روز.
۳. **۵ تا ۱۰ دقیقه:** سه خط در دفترتان بنویسید: چه اجرا کردید، چه چیزی غافلگیرتان کرد، و یک سؤال باز.

**محل اجرای Labها:** Labهایی که root، kernel سفارشی، cgroup با احتمال OOM یا تست crash لازم دارند **فقط داخل VM** (`00-setup`) اجرا می‌شوند و README آن‌ها بنر «VM only» دارد. پیش از هر جلسه روی VM، خروجی `uname -r` را ببینید و اگر چیزی غیرعادی بود به snapshot برگردید.

---

## برنامهٔ ۱۰ هفته‌ای (همه‌چیز)

### هفتهٔ ۱ — راه‌اندازی + معماری (بخش ۱)

</div>

| روز | کار | خروجی |
|---|---|---|
| 1 | `00-setup/guide.fa.md` بخش ۱ تا ۳؛ lab 00.1 (ساخت VM؛ روی ویندوز `create-vm-virtualbox.ps1`) | VM به `ssh` جواب می‌دهد و snapshot `fresh` دارد |
| 2 | Lab 00.2 نصب ابزارها + `verify-tools.sh` | exit code صفر (فقط WARN مربوط به RT و `/dev/kvm`) |
| 3 | Lab 00.3 ساخت v6.18.63 (یا مسیر .deb در README آزمایش 00.1) | `uname -r` نسخهٔ 6.18.63 را نشان می‌دهد |
| 4 | بخش ۴ guide (ctags/cscope/`cite.sh`) + `lesson.fa.md` ماژول ۰۱ | `cite.sh linux arch/x86/entry/syscall_64.c do_syscall_64` کار می‌کند |
| 5 | Noteهای ۰۱ (انواع kernel) و ۰۲ (ringها و CPL) | جدول یک‌صفحه‌ای monolithic / micro / hybrid |
| 6 | Lab 01 ماژول ۰۱: `strace-map` | جدول syscall ← تابع kernel برای `cat` |
| 7 | مرور: سؤال ۱ تا ۵ کوییز ۰۱ + یک ویدیو از `01-architecture/videos.md` | پاسخ‌ها بررسی شده |

<div dir="rtl">

### هفتهٔ ۲ — معماری (بخش ۲) + پردازه‌ها (بخش ۱)

</div>

| روز | کار | خروجی |
|---|---|---|
| 8 | Note 03 (interrupt / exception / IDT) + lab 03 | جدول تغییر IRQها از `/proc/interrupts` |
| 9 | Note 04 (مسیر syscall) + بخش syscall entry در walkthrough | رسم `entry_SYSCALL_64 → do_syscall_64 → x64_sys_call` از حفظ |
| 10 | Lab 02 (raw syscall) + lab 04 (هزینهٔ syscall) | ns/call برای vDSO در برابر syscall واقعی |
| 11 | Noteهای ۰۵ (context switch) و ۰۶ (نقشهٔ سورس) + lab 05 ftrace روی `vfs_read` *(حتماً با filter؛ README را ببینید)* | trace از نوع function_graph برای یک `read()` |
| 12 | کل کوییز ۰۱ + سؤال‌های شفاهی با صدای بلند | ۳ نقطهٔ ضعف فهرست‌شده |
| 13 | Lesson ماژول ۰۲ + note 01 (`task_struct`) | ۱۰ فیلدی که می‌توانید توضیح دهید |
| 14 | Note 02 (fork/vfork/clone) + lab 01 (fork-exec-pipe) | خروجی `/proc/<pid>/{status,maps,fd}` در دفترتان |

<div dir="rtl">

### هفتهٔ ۳ — پردازه‌ها و Threadها (بخش ۲)

</div>

| روز | کار | خروجی |
|---|---|---|
| 15 | Note 03 (execve و ELF) + lab 02 (پرچم‌های clone) | جدول پرچم ← چه چیزی مشترک است |
| 16 | Noteهای ۰۴ (حالت‌ها و wait) و ۰۵ (threadها `mm` مشترک دارند) | نمودار حالت‌ها از حفظ |
| 17 | Note 06 (scheduling classها) + `__schedule` / `context_switch` در walkthrough | زنجیرهٔ فراخوانی در یک صفحه |
| 18 | Note 07 **EEVDF** (lag، eligibility، virtual deadline) | حل دستی مثال note |
| 19 | Lab 03 (ping-pong) + lab 04 (`perf sched` / bpftrace) | میانه در حالت pin‌شده و آزاد |
| 20 | Lab 05 (sched policies، در VM) + lab 06 (goroutine در برابر thread)؛ note 08 IPC | جدول `GOMAXPROCS` ← تعداد thread |
| 21 | کوییز ۰۲ + شفاهی؛ مقایسه با `sched_bsd.c` در OpenBSD | جدول trade-off با کلمات خودتان |

<div dir="rtl">

### هفتهٔ ۴ — همروندی (بخش ۱)

</div>

| روز | کار | خروجی |
|---|---|---|
| 22 | Lesson ماژول ۰۳ + note 01 (race و critical section) | — |
| 23 | Lab 01: data race ← TSan ← mutex ← atomics | هزینهٔ هر راه‌حل با `perf stat` |
| 24 | Note 02 (atomics و مدل حافظهٔ C11) | — |
| 25 | Note 03 (x86-TSO و barrierها) + lab 05 (litmus از نوع store-buffering) | تعداد نتیجه‌های reorder‌شده |
| 26 | Note 04 (spinlock و qspinlock) + `queued_spin_lock` در walkthrough | — |
| 27 | Note 05 (optimistic spinning در mutex) + `mutex_lock` ← `__mutex_lock_common` | fast path و slow path در یک صفحه |
| 28 | مرور: سؤال ۱ تا ۷ کوییز ۰۳ | — |

<div dir="rtl">

### هفتهٔ ۵ — همروندی (بخش ۲) + حافظه (بخش ۱)

</div>

| روز | کار | خروجی |
|---|---|---|
| 29 | Note 06 (semaphore و condvar) + lab 02 (producer-consumer) | هر سه نسخه جمع یکسان می‌دهند |
| 30 | Note 07 (futex) + lab 04 (mutex خام با futex) | `strace -f` فقط هنگام رقابت `FUTEX_WAIT`/`FUTEX_WAKE` نشان می‌دهد |
| 31 | Note 08 (RCU و SMR در OpenBSD) + lab 03 (readers-writers) | عددهای گرسنگیِ writer |
| 32 | Noteهای ۰۹ (deadlock و lockdep) و ۱۰ (مسائل کلاسیک) + lab 06 | dump threadها در gdb که چرخه را نشان می‌دهد |
| 33 | کل کوییز ۰۳ + شفاهی | — |
| 34 | Lesson ماژول ۰۴ + note 01 (فضای آدرس مجازی) | `/proc/self/maps` حاشیه‌نویسی‌شده |
| 35 | Note 02 (page table) + note 03 (TLB و PCID) | walk چهارسطحی یک آدرس روی کاغذ |

<div dir="rtl">

### هفتهٔ ۶ — حافظه (بخش ۲)

</div>

| روز | کار | خروجی |
|---|---|---|
| 36 | Note 04 (مسیر page fault) + `exc_page_fault → handle_mm_fault` در walkthrough | زنجیره از حفظ |
| 37 | Lab 01 (page fault) | تعداد minor/major در هر حالت |
| 38 | Note 05 (demand paging و COW) + lab 02 (COW با pagemap) | PFN یکسان پیش از نوشتن و PFN تازه پس از آن |
| 39 | Note 09 (mmap) + lab 03 | — |
| 40 | Noteهای ۰۶ (buddy) و ۰۷ (SLUB) + lab 05 (slab) | `slabtop` پیش و پس |
| 41 | Note 08 (reclaim و MGLRU) + note 10 (huge page، NUMA، OOM)؛ lab 04 (TLB) | منحنی ns/access برای 4k و THP |
| 42 | Lab 06 (OOM و thrashing در cgroup، در VM) + کوییز | `oom_kill 1` در `memory.events` |

<div dir="rtl">

### هفتهٔ ۷ — فایل‌سیستم و I/O (بخش ۱)

</div>

| روز | کار | خروجی |
|---|---|---|
| 43 | Lesson ماژول ۰۵ + note 01 (اشیای VFS) | نمودار superblock/inode/dentry/file |
| 44 | Noteهای ۰۲ (path lookup) و ۰۳ (جدول fd) | — |
| 45 | Lab 01 (زنجیرهٔ `read()` با ftrace فیلترشده + bpftrace) | trace مسیر `vfs_read → filemap_read` |
| 46 | Note 04 (page cache و writeback) + lab 02 | MiB/s سرد و گرم |
| 47 | Lab 03 (fsync و writeback) | جدول تأخیر fsync |
| 48 | Noteهای ۰۵ (block layer و blk-mq) و ۰۶ (I/O schedulerها) | — |
| 49 | مرور: دوباره کوییز ۰۴ (تکرار با فاصله) + سؤال ۱ تا ۵ کوییز ۰۵ | — |

<div dir="rtl">

### هفتهٔ ۸ — فایل‌سیستم (بخش ۲) + توزیع‌شده (بخش ۱)

</div>

| روز | کار | خروجی |
|---|---|---|
| 50 | Lab 04 (I/O schedulerها با fio) | IOPS و تأخیر برای هر scheduler |
| 51 | Note 08 (io_uring) + lab 05 | تعداد syscall در `read()` و io_uring |
| 52 | Note 07 (journaling) + lab 06 (crash در ext4 با dm-flakey، در VM) | فایل fsync‌شده می‌ماند و فایل دیگر نه |
| 53 | Note 09 (driverها و char device) + کل کوییز | — |
| 54 | Lesson ماژول ۰۶ + noteهای ۰۱ (معنای RPC) و ۰۲ (ساعت Lamport و برداری) | — |
| 55 | Lab 01 (Lamport و vector clock) | شرط ساعت برقرار است |
| 56 | Note 03 (همگام‌سازی ساعت) + lab 02 (RPC و idempotency) | موجودی با retry درست می‌ماند |

<div dir="rtl">

### هفتهٔ ۹ — توزیع‌شده و مجازی‌سازی (بخش ۲)

</div>

| روز | کار | خروجی |
|---|---|---|
| 57 | Noteهای ۰۴ (deadlock توزیع‌شده و snapshot) و ۰۵ (تحمل خطا) | — |
| 58 | Note 06 (hypervisor، VT-x، EPT) + note 07 (KVM) | — |
| 59 | Note 08 (namespace و cgroup v2) + `nsproxy.c` و `cgroup.c` در walkthrough | — |
| 60 | Lab 03 (container کوچک، در VM) | PID 1 داخل container و اعمال `pids.max` |
| 61 | Lab 04 (کلاینت KVM؛ `/dev/kvm` واقعی لازم است) + lab 05 (هزینهٔ VM exit) | هزینهٔ exit با `cpuid` در برابر syscall |
| 62 | کوییز ۰۶ + شفاهی | — |
| 63 | مرور با فاصله: کوییزهای ۰۱ تا ۰۳، فقط پاسخ‌های غلط | — |

<div dir="rtl">

### هفتهٔ ۱۰ — بی‌درنگ و پژوهش + مرور نهایی

</div>

| روز | کار | خروجی |
|---|---|---|
| 64 | Lesson ماژول ۰۷ + noteهای ۰۱ (RT سخت و نرم) و ۰۲ (RMS / EDF / `SCHED_DEADLINE`) | — |
| 65 | Note 03 (priority inversion) + lab 02 | زمان انتظار H در حالت `none` و `inherit` |
| 66 | Note 04 (`PREEMPT_RT`) + lab 01 cyclictest (kernel RT: lab 00.3 با `--rt`) | هیستوگرام تأخیر |
| 67 | Note 05 (seccomp، LSM، Landlock) + labهای ۰۳ و ۰۴ | kill یا EACCES همان‌طور که انتظار می‌رود |
| 68 | Note 06 (خواندن مقاله) + lab 05 (نقد یک مقاله) | نقد یک‌صفحه‌ای |
| 69 | کل `CHEATSHEET.fa.md`؛ همهٔ سؤال‌های شفاهی با صدای بلند | — |
| 70 | امتحان آزمایشی: ۲ کوییز تصادفی، ۶۰ دقیقه، بدون جزوه | نمره + فهرست ضعف‌ها |

<div dir="rtl">

---

## برنامهٔ ۴ هفته‌ای (مسیر اصلی)

★ یعنی note اصلی. برنامهٔ ۴ هفته‌ای فقط همین noteها را می‌خواند و بقیه به فهرست دور دوم می‌روند.

</div>

| روز | کار |
|---|---|
| 1 | Labهای 00.1 و 00.2 (VirtualBox: `create-vm-virtualbox.ps1`) |
| 2 | Lab 00.3 (ساخت kernel یا .deb از mainline)؛ روال `cite.sh` و ctags |
| 3 | Lesson ماژول ۰۱ + ★ noteهای ۰۲ (ringها و CPL) و ۰۴ (مسیر syscall) |
| 4 | Lab 01 (strace map) + walkthrough (ورود syscall) |
| 5 | ★ Note 05 (context switch) + lab 04 (هزینهٔ syscall) |
| 6 | کوییز ۰۱ + شفاهی |
| 7 | Lesson ماژول ۰۲ + ★ noteهای ۰۱ (`task_struct`) و ۰۲ (fork/clone) |
| 8 | Lab 01 (fork-exec-pipe) + lab 02 (پرچم‌های clone) |
| 9 | ★ Noteهای ۰۶ (sched classها) و ۰۷ (EEVDF) + `__schedule` در walkthrough |
| 10 | Lab 03 (ping-pong) + کوییز |
| 11 | Lesson ماژول ۰۳ + ★ noteهای ۰۱ (race) و ۰۲ (atomics/C11) + lab 01 (data race) |
| 12 | ★ Noteهای ۰۳ (TSO و barrier) و ۰۷ (futex) + lab 04 (futex خام) |
| 13 | ★ Noteهای ۰۸ (RCU) و ۰۹ (deadlock) + lab 02 (producer-consumer) |
| 14 | کوییز ۰۳ + شفاهی |
| 15 | Lesson ماژول ۰۴ + ★ noteهای ۰۲ (page table) و ۰۳ (TLB) |
| 16 | ★ Note 04 (مسیر page fault) + lab 01 |
| 17 | ★ Noteهای ۰۵ (COW) و ۰۹ (mmap) + lab 02 (COW) |
| 18 | ★ Note 10 (huge page و OOM) + lab 06 (OOM، در VM) + کوییز |
| 19 | Lesson ماژول ۰۵ + ★ noteهای ۰۱ (اشیای VFS) و ۰۴ (page cache) |
| 20 | Lab 01 (زنجیرهٔ read) + lab 02 (page cache) |
| 21 | ★ Noteهای ۰۷ (journaling) و ۰۸ (io_uring) + lab 05 (io_uring) |
| 22 | کوییز ۰۵ |
| 23 | Lesson ماژول ۰۶ + ★ noteهای ۰۲ (ساعت‌ها) و ۰۸ (namespace و cgroup) |
| 24 | Lab 03 (container کوچک، در VM) + ★ note 07 (KVM) |
| 25 | کوییز ۰۶ |
| 26 | Lesson ماژول ۰۷ + ★ noteهای ۰۳ (priority inversion) و ۰۵ (seccomp و Landlock) + lab 02 |
| 27 | Lab 03 (seccomp) + کوییز |
| 28 | امتحان آزمایشی (۲ کوییز، ۶۰ دقیقه) + `CHEATSHEET` |

<div dir="rtl">

**دور دوم پس از ۴ هفته:**
- **M01:** noteهای ۰۱، ۰۳ و ۰۶؛ labهای ۰۲، ۰۳ و ۰۵.
- **M02:** noteهای ۰۳، ۰۴، ۰۵ و ۰۸؛ labهای ۰۴ تا ۰۶.
- **M03:** noteهای ۰۴ تا ۰۶ و ۱۰؛ labهای ۰۳، ۰۵ و ۰۶.
- **M04:** noteهای ۰۱ و ۰۶ تا ۰۸؛ labهای ۰۳ تا ۰۵.
- **M05:** noteهای ۰۲، ۰۳، ۰۵، ۰۶ و ۰۹؛ labهای ۰۳، ۰۴ و ۰۶.
- **M06:** noteهای ۰۱ و ۰۳ تا ۰۶؛ labهای ۰۱، ۰۲، ۰۴ و ۰۵.
- **M07:** noteهای ۰۱، ۰۲، ۰۴ و ۰۶؛ labهای ۰۱، ۰۴ و ۰۵.

## قاعده‌هایی که هر دو برنامه را جواب‌دار می‌کنند

- **پیش از دیدن solution، خودتان اجرا کنید.** پوشهٔ `solution/` هر lab برای بعد از تلاش خودتان است.
- **هر کوییز را دو بار بزنید:** یک بار آخر ماژول و یک بار دو هفته بعد (تکرار با فاصله). فقط سؤال‌های غلط را دوباره بخوانید.
- **سؤال‌های شفاهی را بلند جواب دهید.** امتحان شفاهی آزاد به پاسخ روشن دودقیقه‌ای همراه با یک نمودار نمره می‌دهد.
- **اگر عددی روی ماشین شما با README فرق دارد:** عددهای README روی یک VM مشترک VirtualBox گرفته شده‌اند. *شکل* نتیجه را مقایسه کنید (نسبت‌ها و این‌که کدام بزرگ‌تر است)، نه مقدار مطلق را.

</div>
