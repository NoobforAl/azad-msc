# Lab-deck content for 02-processes-threads. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced OS · 02 Processes & Threads", "fa": "سیستم‌عامل پیشرفته · ۰۲ process‌ها و thread‌ها"}
CAP = {
    "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15",
    "fa": "aos-lab (VirtualBox، Ubuntu 24.04، Linux 6.18.63)، 2026-11-15",
}
VM = {"en": "Lab VM (aos-lab)", "fa": "VM آزمایشگاه (aos-lab)"}

LABS = [
    dict(
        slug="01-fork-exec-pipe",
        num="02.1",
        title={"en": "fork, exec, pipe and /proc", "fa": "fork، exec، pipe و /proc"},
        goal={
            "en": "Build fork → dup2 → exec → pipe → waitpid in C and watch the fd table and a zombie through /proc.",
            "fa": "الگوی fork ← dup2 ← exec ← pipe ← waitpid را در C بسازید و جدول fd و یک zombie را از طریق /proc ببینید.",
        },
        where=VM,
        setup_cards=[
            (
                "r-user",
                {"en": "Program", "fa": "برنامه"},
                {"en": "fep.c: parent + one child", "fa": "fep.c: والد و یک فرزند"},
            ),
            (
                "r-kernel",
                {"en": "Kernel path", "fa": "مسیر کرنل"},
                {"en": "kernel_clone · bprm_execve · exit_notify", "fa": "kernel_clone · bprm_execve · exit_notify"},
            ),
            (
                "r-data",
                {"en": "Channel", "fa": "کانال"},
                {"en": "pipe2(O_CLOEXEC) + dup2 to fd 1", "fa": "pipe2(O_CLOEXEC) و dup2 روی fd 1"},
            ),
            (
                "r-hardware",
                {"en": "Observe", "fa": "مشاهده"},
                {"en": "/proc/<pid>/status, fd, maps", "fa": "/proc/<pid>/status، fd، maps"},
            ),
        ],
        steps=[
            "$ cd ~/work/02-processes-threads/labs/01-fork-exec-pipe",
            "$ gcc -Wall -Wextra -O2 -o fep fep.c",
            "$ ./fep",
            "$ strace -f -e trace=pipe2,clone,dup2,execve,wait4 \\",
            "    ./fep >/dev/null",
            "$ sleep 300 & P=$!",
            "$ grep -E 'State|Tgid|ctxt' /proc/$P/status",
            "$ ls -l /proc/$P/fd",
        ],
        expected=[
            "parent pid=4266 forked child pid=4267",
            "--- child's fd table after exec (read through the pipe) ---",
            "!l-wx------ 1 fred fred 64 Nov 15 16:15 1 -> pipe:[13197]",
            "lr-x------ 1 fred fred 64 Nov 15 16:15 3 -> /proc/4267/fd",
            "--- EOF after 237 bytes: every write end is closed ---",
            "before waitpid, /proc/4267/status:",
            "  Name:\tls",
            "!  State:\tZ (zombie)",
            "waitpid: child 4267 exited with status 0",
            "  /proc/4267/status: No such file or directory",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "fds 3 and 4 vanished at exec", "fa": "fdهای ۳ و ۴ در exec ناپدید شدند"},
                {"en": "O_CLOEXEC → do_close_on_exec()", "fa": "O_CLOEXEC ← do_close_on_exec()"},
            ),
            (
                {"en": "glibc fork() is clone()", "fa": "fork() در glibc همان clone() است"},
                {
                    "en": "flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD",
                    "fa": "flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD",
                },
            ),
            (
                {"en": "Zombie until waitpid()", "fa": "zombie تا waitpid()"},
                {
                    "en": "exit_notify() → EXIT_ZOMBIE → release_task()",
                    "fa": "exit_notify() ← EXIT_ZOMBIE ← release_task()",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "hangs after the listing", "fa": "بعد از فهرست گیر می‌کند"},
                {"en": "parent kept fds[1]: close it after fork", "fa": "والد fds[1] را نگه داشته؛ بعد از fork ببندید"},
            ),
            (
                {"en": "child sees fds 3 and 4", "fa": "فرزند fdهای ۳ و ۴ را می‌بیند"},
                {"en": "use pipe2(fds, O_CLOEXEC)", "fa": "از pipe2(fds, O_CLOEXEC) استفاده کنید"},
            ),
            (
                {"en": "output printed twice", "fa": "خروجی دو بار چاپ می‌شود"},
                {"en": "fflush(stdout) before fork()", "fa": "قبل از fork() دستور fflush(stdout)"},
            ),
        ],
        ext={
            "en": "pipeline.c: run ls -l /proc/self/fd | wc -l with two children and no shell; prove with /proc that each holds only its own pipe end.",
            "fa": "pipeline.c: دستور ls -l /proc/self/fd | wc -l را با دو فرزند و بدون shell اجرا کنید و با /proc ثابت کنید هر کدام فقط سر خودش از pipe را دارد.",
        },
    ),
    dict(
        slug="02-clone-flags",
        num="02.2",
        title={"en": "clone() flags: what is shared", "fa": "پرچم‌های clone(): چه چیزی مشترک است"},
        goal={
            "en": "Prove flag by flag which resource (mm, fd table, cwd, thread group) each CLONE_* flag shares.",
            "fa": "پرچم به پرچم ثابت کنید هر پرچم CLONE_* کدام منبع (mm، جدول fd، cwd، گروه thread) را مشترک می‌کند.",
        },
        where=VM,
        setup_cards=[
            (
                "r-user",
                {"en": "Child does", "fa": "کار فرزند"},
                {"en": "write global · open() · chdir(/tmp)", "fa": "نوشتن متغیر سراسری · open() · chdir(/tmp)"},
            ),
            (
                "r-kernel",
                {"en": "Kernel", "fa": "کرنل"},
                {"en": "copy_process: copy_mm/files/fs", "fa": "copy_process: copy_mm/files/fs"},
            ),
            (
                "r-data",
                {"en": "Shared objects", "fa": "شیءهای مشترک"},
                {"en": "mm_struct · files_struct · fs_struct", "fa": "mm_struct · files_struct · fs_struct"},
            ),
            (
                "r-hardware",
                {"en": "Thread exit", "fa": "خروج thread"},
                {"en": "futex on CLONE_CHILD_CLEARTID word", "fa": "futex روی کلمهٔ CLONE_CHILD_CLEARTID"},
            ),
        ],
        steps=[
            "$ cd ~/work/02-processes-threads/labs/02-clone-flags",
            "$ gcc -Wall -Wextra -O2 -o cloneflags cloneflags.c",
            "$ ./cloneflags",
            "",
            "# what does glibc pass for a thread?",
            "$ gcc -Wall -Wextra -O2 -pthread -o t t.c",
            "$ strace -f -e trace=clone,clone3 ./t",
        ],
        expected=[
            "0 (like fork)          mem=no  fds=no  cwd=no  child_tgid=n/a",
            "CLONE_VM               mem=yes fds=no  cwd=no  child_tgid=other",
            "CLONE_FILES            mem=no  fds=yes cwd=no  child_tgid=n/a",
            "CLONE_FS               mem=no  fds=no  cwd=yes child_tgid=n/a",
            "CLONE_VM|FILES|FS      mem=yes fds=yes cwd=yes child_tgid=other",
            "!pthread set            mem=yes fds=yes cwd=yes child_tgid=same",
            "",
            "$ strace -f -e trace=clone3 ./t",
            "!clone3({flags=CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|",
            "  CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|...}) = 5107",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "One flag, one resource", "fa": "یک پرچم، یک منبع"},
                {"en": "copy_mm / copy_files / copy_fs", "fa": "copy_mm / copy_files / copy_fs"},
            ),
            (
                {"en": "CLONE_VM alone ≠ thread", "fa": "CLONE_VM به‌تنهایی thread نیست"},
                {
                    "en": "other TGID: what vfork / posix_spawn use",
                    "fa": "TGID دیگر؛ همان که vfork و posix_spawn به کار می‌برند",
                },
            ),
            (
                {"en": "Thread = same TGID", "fa": "thread = TGID یکسان"},
                {"en": "fork.c L2261: p->tgid = current->tgid", "fa": "fork.c L2261: p->tgid = current->tgid"},
            ),
        ],
        pitfalls=[
            (
                {"en": "clone: Invalid argument", "fa": "clone: Invalid argument"},
                {"en": "THREAD needs SIGHAND needs VM", "fa": "THREAD به SIGHAND و آن به VM نیاز دارد"},
            ),
            (
                {"en": "segfault in child", "fa": "segfault در فرزند"},
                {"en": "pass stack + STACK_SIZE (top)", "fa": "stack + STACK_SIZE (بالای پشته) را بدهید"},
            ),
            (
                {"en": "waitpid: No child processes", "fa": "waitpid: No child processes"},
                {"en": "threads: wait on the CLEARTID futex", "fa": "برای thread روی futex مربوط به CLEARTID صبر کنید"},
            ),
        ],
        ext={
            "en": "Add CLONE_VFORK|CLONE_VM and show by timing that clone() returns in the parent only after the child's _exit() (child sleeps 1 s).",
            "fa": "پرچم CLONE_VFORK|CLONE_VM را اضافه کنید و با زمان‌سنجی نشان دهید clone() در والد فقط بعد از _exit() فرزند برمی‌گردد (فرزند ۱ ثانیه می‌خوابد).",
        },
    ),
    dict(
        slug="03-ctxsw-pingpong",
        num="02.3",
        title={"en": "Context-switch cost: pipe ping-pong", "fa": "هزینهٔ context switch: ping-pong با pipe"},
        goal={
            "en": "Measure a blocking round trip with both tasks on one CPU vs two CPUs, and explain why two CPUs are slower here.",
            "fa": "رفت‌وبرگشت blocking را وقتی هر دو task روی یک CPU یا روی دو CPU هستند اندازه بگیرید و توضیح دهید چرا اینجا دو CPU کندتر است.",
        },
        where=VM,
        setup_cards=[
            (
                "r-user",
                {"en": "Two processes", "fa": "دو process"},
                {"en": "1 byte back and forth, 200 000 times", "fa": "یک بایت رفت و برگشت، ۲۰۰ هزار بار"},
            ),
            (
                "r-kernel",
                {"en": "Kernel path", "fa": "مسیر کرنل"},
                {"en": "pipe wait → __schedule → wake_up", "fa": "انتظار pipe ← __schedule ← wake_up"},
            ),
            (
                "r-hardware",
                {"en": "Placement", "fa": "جای‌گذاری"},
                {"en": "same: CPU 0 · split: CPU 0 + 1", "fa": "same: CPU 0 · split: CPU 0 و 1"},
            ),
            (
                "r-data",
                {"en": "Statistics", "fa": "آمار"},
                {"en": "5 runs, median (shared VM)", "fa": "۵ اجرا، میانه (VM مشترک)"},
            ),
        ],
        steps=[
            "$ cd ~/work/02-processes-threads/labs/03-ctxsw-pingpong",
            "$ gcc -Wall -Wextra -O2 -o pingpong pingpong.c",
            "$ ./pingpong same 200000",
            "$ bash run.sh",
            "",
            "$ perf stat -e context-switches,cpu-migrations \\",
            "    ./pingpong same 200000",
        ],
        expected=[
            "$ bash run.sh",
            "mode=same  round_trip=2717 ns  vcsw=115381 ivcsw=84623",
            "!== same: median round_trip 2717 ns over 5 runs",
            "mode=split round_trip=195549 ns  vcsw=19989 ivcsw=1",
            "!== split: median round_trip 195549 ns over 5 runs",
            "== free: median round_trip 20619 ns over 5 runs",
            "",
            "$ perf stat -e context-switches ./pingpong same 200000",
            "            400003      context-switches",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "same: 43% involuntary", "fa": "same: ۴۳٪ involuntary"},
                {
                    "en": "wakee preempts the writer before read()",
                    "fa": "task بیدارشده نویسنده را پیش از read() preempt می‌کند",
                },
            ),
            (
                {"en": "split is ~70x slower", "fa": "split حدود ۷۰ برابر کندتر است"},
                {"en": "cross-vCPU wakeup via IPI + hypervisor", "fa": "بیدار کردن vCPU دیگر با IPI و hypervisor"},
            ),
            (
                {"en": "free ≈ same", "fa": "free ≈ same"},
                {"en": "wake-affine, WF_SYNC from the pipe", "fa": "wake-affine و WF_SYNC از سمت pipe"},
            ),
        ],
        pitfalls=[
            (
                {"en": "numbers jump 2× between runs", "fa": "عددها بین اجراها دو برابر می‌شوند"},
                {"en": "shared VM: use run.sh medians", "fa": "VM مشترک: از میانهٔ run.sh استفاده کنید"},
            ),
            (
                {"en": "cycles <not supported>", "fa": "cycles <not supported>"},
                {"en": "no PMU in this VM: software events", "fa": "این VM PMU ندارد؛ رویدادهای نرم‌افزاری"},
            ),
            (
                {"en": "affinity: Invalid argument", "fa": "affinity: Invalid argument"},
                {"en": "1-vCPU VM: only free mode", "fa": "VM تک‌هسته‌ای: فقط حالت free"},
            ),
        ],
        ext={
            "en": "Compare pipe, AF_UNIX socketpair and shared page + futex round trips, same and split, 5 runs each; explain why the gap closes in split mode.",
            "fa": "رفت‌وبرگشت pipe، socketpair با AF_UNIX و صفحهٔ مشترک + futex را در حالت same و split، هر کدام ۵ اجرا، مقایسه کنید و توضیح دهید چرا در split فاصله‌ها کم می‌شود.",
        },
    ),
    dict(
        slug="04-perf-sched-bpftrace",
        num="02.4",
        title={"en": "perf sched and bpftrace on sched_switch", "fa": "perf sched و bpftrace روی sched_switch"},
        goal={
            "en": "Read scheduling latency with perf sched and split every context switch into voluntary vs involuntary with bpftrace.",
            "fa": "تأخیر زمان‌بندی را با perf sched بخوانید و هر context switch را با bpftrace به voluntary و involuntary تقسیم کنید.",
        },
        where={"en": "Lab VM (root, tracing only)", "fa": "VM آزمایشگاه (root، فقط ردیابی)"},
        setup_cards=[
            (
                "r-user",
                {"en": "Load on CPU 2", "fa": "بار روی CPU 2"},
                {"en": "2 shell busy loops + pingpong", "fa": "دو حلقهٔ پرکار shell و pingpong"},
            ),
            (
                "r-kernel",
                {"en": "Tracepoint", "fa": "tracepoint"},
                {"en": "sched:sched_switch (prev_state)", "fa": "sched:sched_switch (prev_state)"},
            ),
            (
                "r-data",
                {"en": "Recording", "fa": "ضبط"},
                {"en": "perf sched record -C 2 -- sleep 3", "fa": "perf sched record -C 2 -- sleep 3"},
            ),
            (
                "r-hardware",
                {"en": "Scope", "fa": "دامنه"},
                {"en": "one CPU, 8 s of load (shared VM)", "fa": "یک CPU، ۸ ثانیه بار (VM مشترک)"},
            ),
        ],
        steps=[
            "$ for i in 1 2; do timeout 8 taskset -c 2 \\",
            "    sh -c 'while :; do :; done' & done",
            "$ timeout 8 taskset -c 2 ./pingpong free 3000000 &",
            "$ sudo perf sched record -C 2 -- sleep 3",
            "$ sudo perf sched latency --sort max | head",
            "$ sudo perf sched timehist | head -20",
            "",
            "$ sudo bpftrace switch_kinds.bt",
        ],
        expected=[
            "$ sudo perf sched latency --sort max | head",
            "  Task          | Switches | Avg delay ms    | Max delay ms",
            "!  sh:(2)        |      179 | avg:  18.576 ms | max: 101.378 ms",
            "!  pingpong:(2)  |   187804 | avg:   0.014 ms | max:  92.529 ms",
            "",
            "$ sudo bpftrace switch_kinds.bt",
            "@involuntary[sh]: 402",
            "@involuntary[pingpong]: 3260",
            "!@voluntary[pingpong]: 703563",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "pingpong waits 0.014 ms", "fa": "pingpong فقط ۰٫۰۱۴ ms منتظر می‌ماند"},
                {
                    "en": "wakes with lag ≥ 0, preempts the hogs",
                    "fa": "با lag ≥ 0 بیدار می‌شود و hogها را preempt می‌کند",
                },
            ),
            (
                {"en": "sh hogs: involuntary only", "fa": "hogهای sh: فقط involuntary"},
                {"en": "prev_state == 0 → preempted", "fa": "prev_state == 0 ← preempt شده"},
            ),
            (
                {"en": "pingpong: voluntary", "fa": "pingpong: voluntary"},
                {"en": "blocks in read() every round trip", "fa": "در هر رفت‌وبرگشت در read() مسدود می‌شود"},
            ),
        ],
        pitfalls=[
            (
                {"en": "perf: No permission", "fa": "perf: No permission"},
                {"en": "perf_event_paranoid: use sudo", "fa": "perf_event_paranoid؛ با sudo اجرا کنید"},
            ),
            (
                {"en": "stress-ng: caught SIGILL", "fa": "stress-ng: caught SIGILL"},
                {
                    "en": "VM vCPU lacks an instruction: --cpu-method int64",
                    "fa": "vCPU این VM دستوری را ندارد: --cpu-method int64",
                },
            ),
            (
                {"en": "bpftrace BTF error", "fa": "خطای BTF در bpftrace"},
                {"en": "needs /sys/kernel/btf/vmlinux", "fa": "به /sys/kernel/btf/vmlinux نیاز دارد"},
            ),
        ],
        ext={
            "en": "bpftrace run-queue latency histogram (wakeup → on CPU) for pingpong vs the rest; re-queue preempted tasks at sched_switch with prev_state == 0.",
            "fa": "هیستوگرام تأخیر run queue (بیدار شدن ← روی CPU) با bpftrace برای pingpong در برابر بقیه؛ taskهای preempt‌شده را در sched_switch با prev_state == 0 دوباره در صف حساب کنید.",
        },
    ),
    dict(
        slug="05-sched-policies",
        num="02.5",
        title={"en": "nice, SCHED_FIFO and EEVDF slices", "fa": "nice، SCHED_FIFO و sliceهای EEVDF"},
        goal={
            "en": "Measure that CPU share follows the nice weight table, that the fair server leaves ~5% under SCHED_FIFO, and that sched_setattr sets a clamped slice.",
            "fa": "اندازه بگیرید که سهم CPU از جدول وزن nice پیروی می‌کند، fair server زیر SCHED_FIFO حدود ۵٪ باقی می‌گذارد و sched_setattr یک slice محدودشده تنظیم می‌کند.",
        },
        where={"en": "VM only (RT busy loop, pinned to CPU 3)", "fa": "فقط VM (حلقهٔ پرکار RT، سنجاق به CPU 3)"},
        setup_cards=[
            (
                "r-user",
                {"en": "share.c", "fa": "share.c"},
                {"en": "N spinners pinned to one CPU", "fa": "N حلقهٔ پرکار روی یک CPU"},
            ),
            (
                "r-kernel",
                {"en": "Classes", "fa": "کلاس‌ها"},
                {
                    "en": "fair (nice) vs rt (FIFO 10) vs dl server",
                    "fa": "fair (nice) در برابر rt (FIFO 10) در برابر dl server",
                },
            ),
            (
                "r-data",
                {"en": "Prediction", "fa": "پیش‌بینی"},
                {"en": "sched_prio_to_weight[]: 1024, 335, 110", "fa": "sched_prio_to_weight[]: 1024، 335، 110"},
            ),
            (
                "r-hardware",
                {"en": "Safety", "fa": "ایمنی"},
                {"en": "CPU 3 only, 3 s per run", "fa": "فقط CPU 3، هر اجرا ۳ ثانیه"},
            ),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o share share.c",
            "$ ./share 0 5",
            "$ ./share 0 0 10",
            "$ sudo ./share fifo 0",
            "$ sudo cat /sys/kernel/debug/sched/fair_server/cpu3/runtime",
            "$ gcc -Wall -Wextra -O2 -o slice slice.c",
            "$ ./slice 50000 3000000 0",
        ],
        expected=[
            "$ ./share 0 5",
            "task   policy      cpu_s    share  fair_pred",
            "!0      nice:0      2.258    75.2%      75.3%",
            "1      nice:5      0.743    24.8%      24.7%",
            "$ sudo ./share fifo 0",
            "0      FIFO:10     2.825    94.2%          -",
            "!1      nice:0      0.174     5.8%     100.0%",
            "$ ./slice 50000 3000000 0",
            "!request 50000 ns  ... /proc se.slice=100000 ns",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "nice 0 vs 5 ≈ 75 / 25", "fa": "nice 0 در برابر 5 ≈ ۷۵ / ۲۵"},
                {"en": "1024 / (1024 + 335) = 75.4%", "fa": "1024 / (1024 + 335) = 75.4%"},
            ),
            (
                {"en": "FIFO ≈ 95%, fair ≈ 5%", "fa": "FIFO ≈ ۹۵٪، fair ≈ ۵٪"},
                {"en": "fair_server: 50 ms per 1000 ms", "fa": "fair_server: ۵۰ ms در هر ۱۰۰۰ ms"},
            ),
            (
                {"en": "50 µs → 100 µs", "fa": "۵۰ میکروثانیه ← ۱۰۰"},
                {"en": "__setparam_fair() clamps 0.1–100 ms", "fa": "__setparam_fair() به ۰٫۱ تا ۱۰۰ ms محدود می‌کند"},
            ),
        ],
        pitfalls=[
            (
                {"en": "SCHED_FIFO: Operation not permitted", "fa": "SCHED_FIFO: Operation not permitted"},
                {"en": "needs CAP_SYS_NICE: sudo", "fa": "CAP_SYS_NICE لازم است؛ sudo"},
            ),
            (
                {"en": "shares far from prediction", "fa": "سهم‌ها از پیش‌بینی دورند"},
                {"en": "busy CPU: pick another with -c", "fa": "CPU مشغول است؛ با -c یکی دیگر انتخاب کنید"},
            ),
            (
                {"en": "/sys/kernel/debug empty", "fa": "/sys/kernel/debug خالی است"},
                {"en": "mount -t debugfs none /sys/kernel/debug", "fa": "mount -t debugfs none /sys/kernel/debug"},
            ),
        ],
        ext={
            "en": "Measure wakeup lateness of a 1 ms sleeper against two nice-0 spinners with the default slice vs a 0.1 ms slice (p50/p99 of 2,000 wakeups). Explain with vd = v + slice/w.",
            "fa": "latency بیدار شدن یک task که ۱ میلی‌ثانیه می‌خوابد را در رقابت با دو حلقهٔ nice 0، با slice پیش‌فرض و slice صدمیکروثانیه‌ای اندازه بگیرید (p50 و p99 از ۲۰۰۰ بیدار شدن) و با vd = v + slice/w توضیح دهید.",
        },
    ),
    dict(
        slug="06-goroutines-vs-threads",
        num="02.6",
        title={"en": "Goroutines vs OS threads", "fa": "goroutine در برابر thread سیستم‌عامل"},
        goal={
            "en": "Show that the kernel sees only OS threads and that Go multiplexes goroutines onto few of them, except during blocking syscalls.",
            "fa": "نشان دهید کرنل فقط thread‌های سیستم‌عامل را می‌بیند و Go goroutineها را روی تعداد کمی از آن‌ها سوار می‌کند، مگر هنگام syscallهای blocking.",
        },
        where=VM,
        setup_cards=[
            (
                "r-user",
                {"en": "gvt.go", "fa": "gvt.go"},
                {"en": "modes: sleep · cpu · syscall", "fa": "حالت‌ها: sleep · cpu · syscall"},
            ),
            (
                "r-kernel",
                {"en": "Kernel view", "fa": "دید کرنل"},
                {"en": "/proc/self/task = one task_struct each", "fa": "/proc/self/task = هر کدام یک task_struct"},
            ),
            (
                "r-hardware",
                {"en": "Ps", "fa": "Pها"},
                {"en": "GOMAXPROCS (default NumCPU = 8)", "fa": "GOMAXPROCS (پیش‌فرض NumCPU = 8)"},
            ),
            (
                "r-data",
                {"en": "Compare", "fa": "مقایسه"},
                {"en": "threads.c: N pthreads", "fa": "threads.c: N عدد pthread"},
            ),
        ],
        steps=[
            "$ go build -o gvt gvt.go",
            "$ ./gvt sleep 10000",
            "$ GOMAXPROCS=2 ./gvt cpu 100",
            "$ ./gvt syscall 200",
            "$ gcc -Wall -Wextra -O2 -pthread -o threads threads.c",
            "$ ./threads 10000",
        ],
        expected=[
            "$ ./gvt sleep 10000",
            "!after 1s: goroutines=10001  os_threads=10   VmRSS=28760 kB",
            "$ GOMAXPROCS=2 ./gvt cpu 100",
            "after 1s: goroutines=101    os_threads=5    VmRSS=2264 kB",
            "$ ./gvt syscall 200",
            "!after 1s: goroutines=201    os_threads=204  VmRSS=5776 kB",
            "$ ./threads 10000",
            "created: os_threads=10001  VmRSS=84680 kB  in 3188.5 ms",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "10 000 sleeping goroutines", "fa": "۱۰٬۰۰۰ goroutine در خواب"},
                {"en": "a handful of OS threads", "fa": "فقط چند thread سیستم‌عامل"},
            ),
            (
                {"en": "Blocking syscalls cost threads", "fa": "syscall blocking thread مصرف می‌کند"},
                {"en": "the P is handed to a new M", "fa": "P به یک M جدید داده می‌شود"},
            ),
            (
                {"en": "pthreads are tasks", "fa": "pthreadها task هستند"},
                {
                    "en": "10 001 tasks, ~320 µs each on this VM",
                    "fa": "۱۰٬۰۰۱ task، هر کدام حدود ۳۲۰ میکروثانیه روی این VM",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "syscall mode: few threads", "fa": "حالت syscall: thread کم"},
                {"en": "os.File.Read uses the netpoller", "fa": "os.File.Read از netpoller استفاده می‌کند"},
            ),
            (
                {"en": "pthread_create: EAGAIN", "fa": "pthread_create: EAGAIN"},
                {"en": "ulimit -u or cgroup pids.max", "fa": "ulimit -u یا pids.max در cgroup"},
            ),
            (
                {"en": "go: command not found", "fa": "go: command not found"},
                {"en": "sudo apt install golang-go", "fa": "sudo apt install golang-go"},
            ),
        ],
        ext={
            "en": "Make syscall mode create no threads by reading the pipe non-blocking through os.NewFile (netpoller); find the epoll fd in /proc/<pid>/fd.",
            "fa": "کاری کنید syscall هیچ thread جدیدی نسازد: pipe را non-blocking و از طریق os.NewFile (netpoller) بخوانید و fd مربوط به epoll را در /proc/<pid>/fd پیدا کنید.",
        },
    ),
]
