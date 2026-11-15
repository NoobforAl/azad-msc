<div dir="rtl">

# ۰۲ — پردازه‌ها و نخ‌ها: آزمون

> نسخهٔ انگلیسی: [`quiz.en.md`](quiz.en.md) · ۱۴ پرسش (۶ مفهومی، ۴ خواندن کد یا خروجی، ۴ اشکال‌یابی یا طراحی) + ۳ پرسش شفاهی · پاسخ‌ها در پایان.

## بخش الف — مفهومی

**Q1.** در لینوکس چه شیء کرنلی یک نخ را نمایش می‌دهد و چه شیئی یک پردازه را؟ کدام پرچم `clone()` باعث می‌شود task جدید نخی از پردازهٔ فراخواننده باشد نه یک پردازهٔ جدید، و کدام پرچم‌های دیگر باید همراهش بیایند؟

**Q2.** `fork()` پردازه‌ای با RSS چهار گیگابایتی چند میلی‌ثانیه طول می‌کشد، نه چند ثانیه. چرا؟ چه کاری هنوز انجام می‌شود که با اندازهٔ پردازه بزرگ می‌شود؟ `vfork()` چه فرقی دارد؟

**Q3.** بعد از یک `execve()` موفق، برای هر مورد بگویید می‌ماند یا از بین می‌رود: (a) PID، (b) PPID، (c) fd شمارهٔ ۴ که با `O_CLOEXEC` باز شده، (d) fd شمارهٔ ۵ بدون آن، (e) handler سیگنال `SIGINT` که با `sigaction` نصب شده، (f) `SIGINT` که روی `SIG_IGN` گذاشته شده، (g) مقدار nice، (h) هفت نخ دیگر پردازه.

**Q4.** zombie چیست و یتیم (orphan) چیست؟ کدام تابع کرنل task را zombie می‌کند و کدام فراخوانی آن را پاک می‌کند؟ چه وقت فرزند بدون اینکه والد `wait()` کند جمع می‌شود؟

**Q5.** کلاس‌های زمان‌بندی لینوکس را به ترتیب اولویت و policyهای فضای کاربر مربوط به هر کدام را فهرست کنید. چرا یک task پرکار `SCHED_FIFO` روی CPU شمارهٔ ۳ در v6.18 taskهای fair روی همان CPU را کاملاً قفل نمی‌کند؟

**Q6.** در EEVDF مفهوم lag، eligibility و virtual deadline را تعریف کنید. task A با `nice 0` و slice پیش‌فرض، و task B با `nice 0` و slice سه‌دهم میلی‌ثانیه. هر دو روی یک CPU پرمصرف‌اند. در بلندمدت کدام CPU بیشتری می‌گیرد، و کدام بعد از بیدار شدن زودتر CPU را می‌گیرد؟

## بخش ب — خواندن کد و خروجی

**Q7.** از `__schedule()` (`kernel/sched/core.c`، نسخهٔ v6.18.63):

</div>

```c
	switch_count = &prev->nivcsw;
	/* ... */
	prev_state = READ_ONCE(prev->__state);
	if (sched_mode == SM_IDLE) {
		/* ... */
	} else if (!preempt && prev_state) {
		try_to_block_task(rq, prev, &prev_state,
				  !task_is_blocked(prev));
		switch_count = &prev->nvcsw;
	}
```

<div dir="rtl">

یک task روی pipe خالی `read()` صدا می‌زند. task دیگری پرمصرف است و با یک wakeup کنار زده می‌شود. برای هر کدام بگویید کدام شاخه اجرا می‌شود، کدام شمارنده زیاد می‌شود و کدام خط `/proc/<pid>/status` آن را نشان می‌دهد.

**Q8.** از `copy_mm()` (`kernel/fork.c`):

</div>

```c
	oldmm = current->mm;
	if (!oldmm)
		return 0;

	if (clone_flags & CLONE_VM) {
		mmget(oldmm);
		mm = oldmm;
	} else {
		mm = dup_mm(tsk, current->mm);
		if (!mm)
			return -ENOMEM;
	}
```

<div dir="rtl">

(a) چه وقت `current->mm` برابر NULL است و task جدید در آن حالت روی چه چیزی اجرا می‌شود؟ (b) `mmget()` چه چیزی را تغییر می‌دهد و چرا لازم است؟ (c) کدام‌یک از `fork()`، `vfork()` و `pthread_create()` وارد شاخهٔ `CLONE_VM` می‌شوند؟

**Q9.** آزمایش ۰۲.۱ زیر `strace -f` (خروجی واقعی، کوتاه‌شده):

</div>

```text
$ strace -f -e trace=pipe2,clone,clone3,dup2,execve,wait4,exit_group ./fep >/dev/null
execve("./fep", ["./fep"], 0x7ffcde0c5fe8 /* 17 vars */) = 0
pipe2([3, 4], O_CLOEXEC)                = 0
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7ffb68ecea10) = 4284
[pid  4284] dup2(4, 1)                  = 1
[pid  4284] execve("/usr/local/sbin/ls", ["ls", "-l", "/proc/self/fd"], 0x7fff1e5aae98 /* 17 vars */) = -1 ENOENT (No such file or directory)
...
[pid  4284] execve("/usr/bin/ls", ["ls", "-l", "/proc/self/fd"], 0x7fff1e5aae98 /* 17 vars */) = 0
[pid  4284] exit_group(0)               = ?
[pid  4284] +++ exited with 0 +++
--- SIGCHLD {si_signo=SIGCHLD, si_code=CLD_EXITED, si_pid=4284, si_uid=1000, si_status=0, si_utime=0, si_stime=0} ---
wait4(4284, [{WIFEXITED(s) && WEXITSTATUS(s) == 0}], 0, NULL) = 4284
exit_group(0)                           = ?
+++ exited with 0 +++
```

<div dir="rtl">

هر خط را توضیح دهید: چرا `clone` و نه `fork`، چرا `dup2` در فرزند اتفاق می‌افتد، `ls` بعد از exec چه fdهایی دارد، و چرا `read` والد در پایان ۰ برمی‌گرداند.

**Q10.** آزمایش ۰۲.۳ روی VM هشت‌هسته‌ای (میانه‌های واقعی):

</div>

```text
== same: median round_trip 2717 ns over 5 runs     (both tasks on CPU 0, 200 000 round trips)
== split: median round_trip 195549 ns over 5 runs  (CPU 0 and CPU 1, 20 000 round trips)
== free: median round_trip 20619 ns over 5 runs    (no pinning)
```

<div dir="rtl">

چرا `split` (دو CPU) از `same` (یک CPU) کندتر است، با اینکه `same` در هر رفت‌وبرگشت دو context switch کامل لازم دارد؟ روی سخت‌افزار واقعی با `idle=poll` چه انتظاری دارید؟

## بخش ج — اشکال‌یابی و طراحی

**Q11.** این برنامه بعد از چاپ خروجی فرزند برای همیشه گیر می‌کند. اشکال را پیدا و درست کنید.

</div>

```c
int fds[2];
pipe(fds);
if (fork() == 0) {
    dup2(fds[1], 1);
    execlp("ls", "ls", NULL);
    _exit(127);
}
char buf[4096];
ssize_t n;
while ((n = read(fds[0], buf, sizeof buf)) > 0)
    write(1, buf, n);
wait(NULL);
```

<div dir="rtl">

**Q12.** یک سرویس Go روی ماشینی ۱۶ هسته‌ای در `/proc/<pid>/status` مقدار `Threads: 2400` را نشان می‌دهد، در حالی که `runtime.NumGoroutine()` برابر ۳۰۰۰ و `GOMAXPROCS` برابر ۱۶ است. دو علت محتمل بگویید، اینکه هر کدام را با `/proc` یا یک ردیاب چطور تأیید می‌کنید، و یک راه‌حل.

**Q13.** یک handler درخواست حساس به تأخیر را کنار کارهای batch پرمصرف روی یک میزبان ۸ CPUای (کرنل 6.18) اجرا می‌کنید. این گزینه‌ها را مقایسه کنید و بگویید کدام را انتخاب می‌کنید: (a) `nice -n 10` برای کارهای batch، (b) slice نیم‌میلی‌ثانیه‌ای EEVDF برای handler با `sched_setattr()`، (c) `SCHED_FIFO` برای handler، (d) cgroupهای CPU جدا با `cpu.weight`. برای هر کدام یک خطر بگویید.

**Q14.** یک سرور طولانی‌مدت برای هر درخواست یک worker را fork می‌کند. بعد از یک روز `ps` سی هزار ورودی در وضعیت `Z` نشان می‌دهد و فراخوانی‌های جدید `fork()` با `EAGAIN` شکست می‌خورند. شکست را توضیح دهید و دو اصلاح درست و متفاوت در کد سرور بدهید.

## پرسش‌های امتحان شفاهی

**O1.** ساخت پردازه و نخ را در لینوکس (`kernel_clone()` با پرچم‌های `CLONE_*` و یک `task_struct`) و OpenBSD (`fork1()` در برابر `__tfork()`/`thread_fork()`، و `struct process` + `struct proc`) مقایسه کنید. هر طراحی چه چیزی را آسان و چه چیزی را سخت می‌کند؟

**O2.** توضیح دهید چرا لینوکس CFS را با EEVDF جایگزین کرد. CFS چه چیزی را نمی‌توانست بیان کند و EEVDF چه پیچ تنظیم تازه‌ای به کاربر داد؟

**O3.** همهٔ اتفاقاتی را که از فضای کاربر تا اجرای task دیگر رخ می‌دهد قدم به قدم شرح دهید، وقتی task A یک بایت در pipeای می‌نویسد که task B (روی همان CPU) روی آن در `read()` مسدود است.

---

## پاسخ‌ها

**A1.** هر دو `struct task_struct` هستند؛ برای هر نخ یکی. «پردازه» مجموعهٔ taskهایی با `tgid` یکسان است که `mm`، `files`، `signal` و ... را مشترک دارند؛ رهبر گروه `pid == tgid` دارد. `CLONE_THREAD` task جدید را در گروه نخ فراخواننده می‌گذارد (همان `tgid` و `exit_signal = -1`). `copy_process()` همراه آن `CLONE_SIGHAND` را الزامی می‌کند و `CLONE_SIGHAND` هم `CLONE_VM` را (وگرنه `-EINVAL`، `kernel/fork.c` خط‌های 1963 تا 1972). در عمل glibc این‌ها را هم می‌فرستد: `CLONE_FS`، `CLONE_FILES`، `CLONE_SYSVSEM`، `CLONE_SETTLS`، `CLONE_PARENT_SETTID` و `CLONE_CHILD_CLEARTID`.

**A2.** `dup_mm()` درخت VMAها و page tableها را کپی می‌کند اما صفحه‌های داده را نه؛ صفحه‌های خصوصی قابل‌نوشتن هم در والد و هم در فرزند فقط‌خواندنی می‌شوند (copy-on-write) و هر صفحه فقط وقتی یک طرف رویش بنویسد کپی می‌شود. کاری که متناسب با اندازه باقی می‌ماند پیمایش و کپی **page tableها** (و شمارش ارجاع صفحه‌ها) است؛ با ۴ گیگابایت صفحهٔ ۴ کیلوبایتی، حدود ۸ مگابایت PTE. `vfork()` پرچم `CLONE_VM | CLONE_VFORK` را می‌فرستد: هیچ کپی‌ای از `mm` انجام نمی‌شود، فرزند روی حافظهٔ والد اجرا می‌شود و والد تا وقتی فرزند `execve()` یا `_exit()` را صدا بزند می‌خوابد.

**A3.** (a) می‌ماند، (b) می‌ماند، (c) از بین می‌رود (`do_close_on_exec()`)، (d) می‌ماند، (e) از بین می‌رود: handlerهای نصب‌شده به `SIG_DFL` برمی‌گردند (`flush_signal_handlers()`)، (f) می‌ماند: سیگنال‌های نادیده‌گرفته‌شده نادیده می‌مانند، (g) می‌ماند، (h) از بین می‌روند: `de_thread()` آن‌ها را می‌کشد، و اگر نخی غیر از رهبر exec کرده باشد، PID رهبر را می‌گیرد.

**A4.** zombie: taskای که خارج شده (`exit_state = EXIT_ZOMBIE` که در `exit_notify()` گذاشته می‌شود) و والدش وضعیت آن را برنداشته؛ فقط `task_struct` و اطلاعات خروج مانده است. یتیم: taskای زنده که والدش خارج شده؛ `find_new_reaper()` آن را به نخ دیگری از همان پردازه، وگرنه به نزدیک‌ترین نیای دارای `PR_SET_CHILD_SUBREAPER`، وگرنه به init همان namespace می‌سپارد. `wait4()` یا `waitid()` والد ← `wait_task_zombie()` ← `release_task()` آن را پاک می‌کند. اگر عمل `SIGCHLD` والد `SIG_IGN` باشد یا `SA_NOCLDWAIT` داشته باشد، به‌طور خودکار جمع می‌شود (`do_notify_parent()`)، و نخ‌هایی که رهبر نیستند همیشه خودکار جمع می‌شوند.

**A5.** stop ← dl (`SCHED_DEADLINE`) ← rt (`SCHED_FIFO` و `SCHED_RR`) ← fair (`SCHED_OTHER`، `SCHED_BATCH`، `SCHED_IDLE`؛ EEVDF) ← ext (`SCHED_EXT`، sched_ext با BPF) ← idle. task از نوع FIFO از taskهای fair بالاتر است، اما (۱) محدودسازی RT آن را به ۹۵۰ میلی‌ثانیه در هر ۱ ثانیه محدود می‌کند و (۲) از 6.12 fair server هر CPU، که یک موجودیت `SCHED_DEADLINE` با runtime پنجاه میلی‌ثانیه در period هزار میلی‌ثانیه است، وقتی taskهای fair گرسنه‌اند آن‌ها را اجرا می‌کند. آزمایش ۰۲.۵ حدود ۵٪ برای task fair اندازه می‌گیرد.

**A6.** `V` میانگین وزنی vruntime صف است. Lag `= w_i (V − v_i)`: مثبت یعنی طلب سرویس دارد. eligible ⇔ lag ≥ 0 ⇔ `v_i ≤ V`. virtual deadline برابر `vd_i = v_i + r_i / w_i` است (در زمانی که با وزن مقیاس شده). سهم بلندمدت فقط به وزن بستگی دارد: nice برابر ⇐ تقریباً ۵۰/۵۰ برای A و B. B که درخواست کوتاه‌تری دارد deadlineهای زودتری می‌گیرد و بعد از eligible شدن زودتر انتخاب می‌شود، پس تأخیر کمتری دارد، اما نوبت‌هایش کوتاه‌ترند و بیشتر switch می‌کند.

**A7.** خوانندهٔ pipe: `anon_pipe_read()` از طریق `wait_event_interruptible_exclusive()` وضعیت `TASK_INTERRUPTIBLE` را می‌گذارد و `schedule()` را با `SM_NONE` صدا می‌زند، پس `preempt` نادرست و `prev_state` غیرصفر است ← `try_to_block_task()` آن را از صف خارج می‌کند و `nvcsw` زیاد می‌شود ← `voluntary_ctxt_switches`. task پرمصرف preempt می‌شود (`SM_PREEMPT` و `preempt` درست؛ وضعیتش هم `TASK_RUNNING` یعنی ۰ است) ← از این شاخه رد می‌شود، روی run queue می‌ماند و `nivcsw` زیاد می‌شود ← `nonvoluntary_ctxt_switches`.

**A8.** (a) در نخ‌های کرنل (فضای آدرس کاربر ندارند)؛ `copy_mm()` صفر برمی‌گرداند و آن نخ بعداً روی یک `active_mm` قرضی اجرا می‌شود (lazy TLB در `context_switch()`). (b) مقدار `mm->mm_users` را که شمار کاربران فضای آدرس است زیاد می‌کند، تا تا وقتی هر task شریکی هنوز از `mm` استفاده می‌کند خراب نشود. (c) `vfork()` و `pthread_create()` وارد آن می‌شوند؛ `fork()` به `dup_mm()` می‌رود.

**A9.** glibc تابع `fork()` را با syscall به نام `clone` پیاده می‌کند (`flags=CLONE_CHILD_SETTID|CLONE_CHILD_CLEARTID|SIGCHLD`)، پس strace مقدار `clone` را چاپ می‌کند. فرزند `dup2(4, 1)` را صدا می‌زند تا fd شمارهٔ ۱ به سر نوشتن pipe اشاره کند؛ این باید در فرزند، بعد از `fork()` و قبل از `execve()` انجام شود، چون جدول fd همان چیزی است که از exec عبور می‌کند. pipe با `O_CLOEXEC` ساخته شده، پس fdهای اصلی ۳ و ۴ هنگام `execve()` ناپدید می‌شوند؛ `ls` فقط ۰، ۱ (pipe)، ۲ و دایرکتوری‌ای که خودش باز می‌کند را دارد. `read` والد وقتی هیچ سر نوشتنی باز نماند ۰ برمی‌گرداند: fd شمارهٔ ۱ فرزند با خروج `ls` بسته شده و والد هم نسخهٔ خودش از fd شمارهٔ ۴ را درست بعد از `fork()` بسته است.

**A10.** در `same` هر رفت‌وبرگشت این است: نوشتن ← بیدار کردن task دیگر روی همان CPU (`WF_SYNC`) ← نویسنده در `read` مسدود می‌شود ← switch ← و برعکس. همه در cacheهای یک CPU، بدون IPI. در `split` هر بیدارباش به CPU دیگری می‌رود که معمولاً بیکار است: بیدارکننده یک IPI می‌فرستد (یا CPU مقصد از حالت بیکاری halt یا `mwait` خارج می‌شود)، و روی VM ممکن است خود vCPU مقصد هم توسط میزبان از زمان‌بندی خارج شده باشد و hypervisor باید بیدارش کند. همین تأخیر بیدار شدن غالب است. با `idle=poll` روی سخت‌افزار واقعی CPU دیگر به جای halt می‌چرخد و `split` از `same` سریع‌تر می‌شود، چون اصلاً context switchی لازم نیست.

**A11.** والد هیچ‌وقت `fds[1]` را نمی‌بندد. `anon_pipe_read()` فقط وقتی `pipe->writers == 0` باشد EOF برمی‌گرداند؛ خود والد یک نویسنده است، پس بعد از خروج `ls`، والد برای همیشه در `read()` مسدود می‌ماند. اصلاح: درست بعد از `fork()` در والد `close(fds[1]);` (و در فرزند بعد از `dup2` هم `close(fds[0]); close(fds[1]);`، یا ساخت pipe با `pipe2(fds, O_CLOEXEC)`).

**A12.** (۱) goroutineهایی که در **syscallهای مسدودکننده‌ای** گیر کرده‌اند که netpoller نمی‌تواند مدیریتشان کند: I/O فایل روی دیسک کند یا NFS، pipe یا دستگاه‌هایی که با `syscall.Read` خوانده می‌شوند، `flock`، و DNS از طریق resolver مبتنی بر cgo. هر کدام یک M را نگه می‌دارند؛ runtime برای Pها M جدید می‌سازد. تأیید: `cat /proc/<pid>/task/*/stat` (بیشتر نخ‌ها در `S`/`D`)، `/proc/<pid>/task/<tid>/wchan` یا `stack`، یا `bpftrace` روی `sys_enter_*` بر اساس tid؛ و `GODEBUG=schedtrace=1000`. (۲) فراخوانی‌های **cgo** یا `runtime.LockOSThread()`: یک G به یک M قفل می‌شود و هر فراخوانی cgo در حال انجام یک نخ را سنجاق می‌کند. تأیید با dump گوروتین‌ها (`SIGQUIT` یا `goroutine?debug=2` در pprof) که `cgocall` یا `syscall` نشان می‌دهد. اصلاح: محدود کردن همزمانی فراخوانی‌های مسدودکننده با semaphore یا worker pool، استفاده از APIهای ناهمگام (fdهای پشتیبانی‌شده با netpoller، کتابخانه‌های `io_uring`)، resolver خالص Go (`GODEBUG=netdns=go`)، و تنظیم `debug.SetMaxThreads` به‌عنوان سقف ایمنی. `GOMAXPROCS` تعداد نخ‌ها را محدود نمی‌کند.

**A13.** (a) nice ده برای batch: وزن ۱۱۰ در برابر ۱۰۲۴، و handler هنگام رقابت حدود ۹۰٪ می‌گیرد؛ ساده است، اما بیدار شدن هنوز ممکن است تا اندازهٔ یک slice از task batch منتظر بماند. خطر: افت throughput کارهای batch؛ تأخیر را محدود نمی‌کند. (b) slice کوتاه: virtual deadline زودتر، handler بعد از بیدار شدن زودتر preempt می‌کند و سهم تغییر نمی‌کند. خطر: context switch بیشتر، هنوز برای سهم رقابت می‌کند؛ فقط 6.6 به بعد. (c) `SCHED_FIFO`: همیشه اول روی CPU خودش اجرا می‌شود؛ بهترین تأخیر. خطر: یک باگ یا جهش بار همهٔ CPU را گرسنه می‌گذارد (فقط ۵٪ fair server می‌ماند)، و امتیاز لازم دارد. (d) cgroupها با `cpu.weight`: گروه‌ها را جدا می‌کند، با آمدن پردازه‌های batch جدید هم پابرجاست و می‌شود با `cpuset` آن را ترکیب کرد تا handler CPUهای خودش را داشته باشد. خطر: پیکربندی بیشتر؛ وزن‌ها تأخیر را محدود نمی‌کنند مگر CPUها تقسیم شوند. انتخاب معمول: (d) با CPUهای اختصاصی یا وزن بالا، به‌اضافهٔ (b) برای نخ‌های handler؛ از (c) پرهیز کنید مگر handler کوچک، محدود و آزموده باشد.

**A14.** سرور هیچ‌وقت فرزندانش را جمع نمی‌کند. هر worker خارج‌شده به‌صورت zombie یک PID نگه می‌دارد (و در `RLIMIT_NPROC` یا `pids.max` در cgroup شمرده می‌شود)، پس وقتی به یک محدودیت برسیم `fork()` با `EAGAIN` شکست می‌خورد. اصلاح‌ها: (۱) handler برای `SIGCHLD` که حلقهٔ `while (waitpid(-1, &st, WNOHANG) > 0) {}` را اجرا می‌کند (سیگنال‌ها با هم ادغام می‌شوند، پس یک سیگنال ممکن است یعنی چند فرزند)؛ (۲) اگر وضعیت خروج لازم نیست، `signal(SIGCHLD, SIG_IGN)` یا `sigaction` با `SA_NOCLDWAIT` تا کرنل خودکار جمع کند (`do_notify_parent()`)؛ (۳) یک pidfd برای هر فرزند در event loop و `waitid(P_PIDFD, ...)` وقتی خواندنی شد. کشتن zombieها کاری نمی‌کند؛ کشتن والد باعث می‌شود init آن‌ها را جمع کند.

**O1 (رئوس پاسخ).** لینوکس: یک شیء و یک مسیر. `kernel_clone()` ← `copy_process()`؛ پرچم‌ها برای هر منبع انتخاب می‌کنند. آسان: نخ‌ها، `vfork`، `posix_spawn`، containerها (`CLONE_NEW*`) و ترکیب‌های عجیب مثل اشتراک فایل‌ها بدون حافظه. سخت: هر منبع شمارش ارجاع و معنای اشتراک لازم دارد؛ ترکیب‌های نامعتبر زیادی باید رد شوند؛ `exec` در یک گروه نخ و سیگنال‌ها پیچیده‌اند (`de_thread`). OpenBSD: `struct process` (فضای آدرس، fdها، اعتبارنامه‌ها، فهرست نخ‌ها) و `struct proc` (نخ)؛ `fork1()` با چند پرچم `FORK_*` برای پردازه‌ها و `thread_fork()` فقط برای نخ‌ها؛ منابع قبل از بخش «نمی‌تواند شکست بخورد» رزرو می‌شوند. آسان: ناورداهای روشن و بازبینی ساده‌تر (با تمرکز امنیتی OpenBSD سازگار است). سخت: اشتراک جزئی وجود ندارد و ابزارهای جداسازی به سبک namespace هم ندارد.

**O2 (رئوس پاسخ).** CFS کمترین vruntime را انتخاب می‌کرد و برای مصالحهٔ تأخیر و throughput از روش‌های ابتکاری استفاده می‌کرد (`sched_latency`، `min_granularity`، wakeup granularity، اعتبار خواب)؛ هیچ راهی نبود که task بگوید «نوبت‌های کوتاه و پرتکرار لازم دارم» بدون اینکه CPU بیشتری هم بخواهد (`nice`)، و این روش‌ها حالت‌های مرزی داشتند. EEVDF یک معیار انصاف تعریف‌شده (lag و eligibility) و یک پارامتر تأخیر جداگانه (اندازهٔ درخواست یا slice) دارد: virtual deadline = vruntime + slice/weight. پیچ تازه: `sched_setattr()` با `sched_runtime` روی task fair (محدود به ۰٫۱ تا ۱۰۰ میلی‌ثانیه). تنظیمات قدیمی CFS حذف شدند و `base_slice_ns` ماند.

**O3 (رئوس پاسخ).** A: `write()` ← `anon_pipe_write()` ← کپی در یک `pipe_buffer` ← `wake_up_interruptible_sync_poll(&pipe->rd_wait)` ← `try_to_wake_up(B)`: B را `TASK_RUNNING` می‌کند، `enqueue_task_fair()` (که با `place_entity()` lag قبلی B را برمی‌گرداند)، و `wakeup_preempt` یا `check_preempt_wakeup_fair()` ممکن است `need_resched` را روی A بگذارد. A از `write()` برمی‌گردد و روی pipe پاسخ وارد `read()` می‌شود، می‌خوابد (`wait_event_interruptible_exclusive`) ← `schedule()` ← `__schedule()`: A از صف خارج می‌شود (`nvcsw++`)، `pick_next_task()` ← مسیر سریع fair ← `pick_eevdf()` که B را برمی‌گرداند ← `trace_sched_switch` ← `context_switch()`: `mm` متفاوت ← `switch_mm_irqs_off()` (نوشتن در CR3 و PCID)، `switch_to()` پشته‌ها و رجیسترها را جابه‌جا می‌کند ← B داخل `wait_event_*` در `anon_pipe_read()` از سر گرفته می‌شود، دوباره `pipe->mutex` را می‌گیرد، بایت را به فضای کاربر کپی می‌کند و از طریق `syscall_exit_to_user_mode()` برمی‌گردد.

</div>
