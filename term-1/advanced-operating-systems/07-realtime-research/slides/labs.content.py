# Lab-deck content for 07-realtime-research. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced OS · 07 Real-Time & Research", "fa": "سیستم‌عامل پیشرفته · ۰۷ Real-Time و پژوهش"}
CAP = {
    "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15",
    "fa": "aos-lab (VirtualBox، Ubuntu 24.04، Linux 6.18.63)، ۲۰۲۶-۱۱-۱۵",
}


def c(s):
    """Code / command text: identical in both languages."""
    return {"en": s, "fa": s}


LAB1_EXPECTED = [
    "$ sudo ./latency 80 1000 10000",
    "latency us: min=35 avg=1012 max=159033",
    "$ sudo bash run-cyclictest.sh 60 2,3",
    "[idle] # Max Latencies: 395586 395126",
    "[load] # Min Latencies: 00032 00031",
    "[load] # Avg Latencies: 09389 09364",
    "![load] # Max Latencies: 26624226 26624344",
    "$ sudo bash compare-preempt.sh 30 2,3 ...",
    "(none) voluntary ...  max_us=[433118 1363610]",
    "none voluntary (full) ...  max_us=[1484984 1484192]",
]

LABS = [
    dict(
        slug="01-cyclictest",
        num="07.1",
        title={"en": "Measure wake-up latency with cyclictest", "fa": "اندازه‌گیری latency بیدار شدن با cyclictest"},
        goal={
            "en": "See latency as a histogram, see what load does to the maximum, and compare preemption models.",
            "fa": "latency را به شکل هیستوگرام ببینید، اثر بار روی بیشینه را ببینید و مدل‌های preemption را مقایسه کنید.",
        },
        where={"en": "VM only — global preempt switch", "fa": "فقط VM — کلید سراسری preempt"},
        setup_cards=[
            ("r-kernel", {"en": "Kernel", "fa": "کرنل"}, c("uname -v → PREEMPT_DYNAMIC (not RT)")),
            ("r-user", {"en": "Measurer", "fa": "اندازه‌گیر"}, c("cyclictest -m -p 80 -i 1000 -a 2,3 -t 2")),
            ("r-hardware", {"en": "Load", "fa": "بار"}, c("stress-ng --cpu 2 --iomix 1 --taskset 2,3")),
            (
                "r-data",
                {"en": "Output", "fa": "خروجی"},
                {"en": "histogram: min / avg / max (µs)", "fa": "هیستوگرام: کمینه / میانگین / بیشینه (µs)"},
            ),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o latency latency.c",
            "$ sudo ./latency 80 1000 10000",
            "$ sudo bash run-cyclictest.sh 60 2,3",
            "# VM only: flips /sys/kernel/debug/sched/preempt",
            '$ sudo bash compare-preempt.sh 30 2,3 "none voluntary full"',
            "# RT side: 00-setup lab 03 --rt (UNVERIFIED here)",
        ],
        expected=LAB1_EXPECTED,
        captured=CAP,
        observe=[
            (
                {"en": "Load moves the max, not the min", "fa": "بار بیشینه را جابه‌جا می‌کند، نه کمینه را"},
                {
                    "en": "min = fixed path; max = time the CPU couldn't switch",
                    "fa": "کمینه = مسیر ثابت؛ بیشینه = زمانی که CPU نمی‌توانست جابه‌جا شود",
                },
            ),
            (
                {"en": "On a VM the host dominates", "fa": "در VM میزبان غالب است"},
                {"en": "ms spikes = vCPU descheduled; shape only", "fa": "جهش میلی‌ثانیه‌ای = کنار گذاشتن vCPU؛ فقط شکل"},
            ),
            (
                {"en": "No /sys/kernel/realtime", "fa": "‏/sys/kernel/realtime وجود ندارد"},
                c("uname -v | grep -o PREEMPT_RT  (init/Makefile L30)"),
            ),
        ],
        pitfalls=[
            (
                {
                    "en": "sched_setscheduler: Operation not permitted",
                    "fa": "sched_setscheduler: Operation not permitted",
                },
                {"en": "sudo, or RLIMIT_RTPRIO in limits.conf", "fa": "sudo، یا RLIMIT_RTPRIO در limits.conf"},
            ),
            (
                {"en": "sched/preempt: No such file", "fa": "sched/preempt: No such file"},
                {"en": "mount debugfs; needs PREEMPT_DYNAMIC", "fa": "debugfs را mount کنید؛ PREEMPT_DYNAMIC لازم است"},
            ),
            (
                {"en": "tiny max on an idle box", "fa": "بیشینهٔ کوچک روی ماشین بیکار"},
                {"en": "always report the loaded run", "fa": "همیشه اجرای زیر بار را گزارش کنید"},
            ),
        ],
        ext={
            "en": "Port latency.c to SCHED_DEADLINE (runtime 200 µs, period 1 ms, sched_yield per job). Then provoke EINVAL and EBUSY with chrt -d and name the kernel function behind each.",
            "fa": "latency.c را به SCHED_DEADLINE ببرید (runtime ‏۲۰۰ میکروثانیه، period ‏۱ میلی‌ثانیه، sched_yield در پایان هر job). بعد با chrt -d خطاهای EINVAL و EBUSY را ایجاد کنید و تابع کرنلِ پشت هر کدام را نام ببرید.",
        },
    ),
    dict(
        slug="02-priority-inversion",
        num="07.2",
        title={"en": "Priority inversion and PTHREAD_PRIO_INHERIT", "fa": "وارونگی اولویت و PTHREAD_PRIO_INHERIT"},
        goal={
            "en": "Make unbounded priority inversion happen on demand, then remove it with one mutex attribute.",
            "fa": "وارونگی نامحدود اولویت را هر وقت خواستید ایجاد کنید، بعد با یک ویژگی mutex حذفش کنید.",
        },
        where={"en": "VM only — 1 s of RT busy-loop", "fa": "فقط VM — ۱ ثانیه حلقهٔ پرکار RT"},
        setup_cards=[
            (
                "r-user",
                {"en": "L · FIFO 10", "fa": "L · FIFO 10"},
                {"en": "holds the mutex, needs 200 ms CPU", "fa": "mutex را دارد، ۲۰۰ میلی‌ثانیه CPU لازم دارد"},
            ),
            (
                "r-user",
                {"en": "H · FIFO 30", "fa": "H · FIFO 30"},
                {"en": "wants the mutex 20 ms later", "fa": "۲۰ میلی‌ثانیه بعد mutex را می‌خواهد"},
            ),
            (
                "r-user",
                {"en": "M · FIFO 20", "fa": "M · FIFO 20"},
                {"en": "burns 800 ms, never locks", "fa": "۸۰۰ میلی‌ثانیه می‌سوزاند، هرگز قفل نمی‌گیرد"},
            ),
            ("r-hardware", {"en": "One CPU", "fa": "یک CPU"}, c("taskset -c 7 (else L runs elsewhere)")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -pthread -o inversion inversion.c",
            "$ sudo taskset -c 7 ./inversion none",
            "$ sudo taskset -c 7 ./inversion inherit",
            "$ sudo strace -f -e trace=futex taskset -c 7 \\",
            "    ./inversion inherit 2>&1 | grep LOCK_PI",
            "$ sudo bpftrace -e 'tracepoint:sched:sched_pi_setprio",
            '    { printf("%s %d -> %d\\n", str(args.comm),',
            "      args.oldprio, args.newprio); }' &",
        ],
        expected=[
            "$ sudo taskset -c 7 ./inversion none",
            "    25.1 ms  M  start, burning 800 ms (no lock)",
            "   825.2 ms  M  done",
            "!  1000.7 ms  H  got the lock after 977.6 ms",
            "$ sudo taskset -c 7 ./inversion inherit",
            "!   202.2 ms  H  got the lock after 181.6 ms",
            "  1002.3 ms  M  done",
            "# bpftrace, inherit run:",
            "!inversion pid=9760 prio 89 -> 69",
            "inversion pid=9760 prio 69 -> 89",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "H waits 977.6 ms → 181.6 ms", "fa": "انتظار H از ۹۷۷٫۶ به ۱۸۱٫۶ میلی‌ثانیه"},
                {"en": "the difference is M's 800 ms", "fa": "تفاوت همان ۸۰۰ میلی‌ثانیهٔ M است"},
            ),
            (
                {"en": "Kernel boost 89 → 69", "fa": "boost کرنل از ۸۹ به ۶۹"},
                c("prio = 99 - rt_priority · rt_mutex_setprio()"),
            ),
            (
                {"en": "Only PI uses FUTEX_LOCK_PI", "fa": "فقط PI از FUTEX_LOCK_PI استفاده می‌کند"},
                {"en": "the futex word holds the owner TID", "fa": "کلمهٔ futex شناسهٔ thread صاحب را دارد"},
            ),
        ],
        pitfalls=[
            (
                {"en": "no inversion visible", "fa": "وارونگی دیده نمی‌شود"},
                {"en": "pin all threads: taskset -c N", "fa": "همهٔ threadها را ببندید: taskset -c N"},
            ),
            (
                {"en": "bpftrace: %s expects a string", "fa": "bpftrace: %s expects a string"},
                c("str(args.comm) — __data_loc field"),
            ),
            (
                {"en": "inherit still slow", "fa": "inherit هنوز کند است"},
                {
                    "en": "set the protocol before pthread_mutex_init",
                    "fa": "پروتکل را پیش از pthread_mutex_init بگذارید",
                },
            ),
        ],
        ext={
            "en": "Add a 'protect' mode (PTHREAD_PRIO_PROTECT, ceiling 30). When does L's priority change, how long does H wait, and which syscall does glibc use?",
            "fa": "حالت سومی به نام protect اضافه کنید (PTHREAD_PRIO_PROTECT با سقف ۳۰). اولویت L کی عوض می‌شود، H چقدر منتظر می‌ماند و glibc از کدام syscall استفاده می‌کند؟",
        },
    ),
    dict(
        slug="03-seccomp-bpf",
        num="07.3",
        title={"en": "A seccomp-BPF sandbox", "fa": "یک sandbox با seccomp-BPF"},
        goal={
            "en": "Confine a program with a seccomp filter and see errno, kill and allow from user space.",
            "fa": "یک برنامه را با فیلتر seccomp محدود کنید و errno و kill و allow را از فضای کاربر ببینید.",
        },
        where={"en": "VM or any Linux (unprivileged)", "fa": "VM یا هر لینوکسی (بدون امتیاز)"},
        setup_cards=[
            ("r-user", {"en": "Library", "fa": "کتابخانه"}, c("libseccomp-dev · -lseccomp")),
            ("r-kernel", {"en": "Precondition", "fa": "پیش‌شرط"}, c("prctl(PR_SET_NO_NEW_PRIVS, 1)")),
            ("r-kernel", {"en": "Rules", "fa": "قانون‌ها"}, c("socket→EACCES · mkdir→KILL · ptrace→EPERM")),
            (
                "r-data",
                {"en": "By hand", "fa": "دستی"},
                {"en": "raw-bpf.c: 7 BPF instructions", "fa": "raw-bpf.c: ‏۷ دستور BPF"},
            ),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o sandbox sandbox.c -lseccomp",
            "$ ./sandbox grep -E '^(NoNewPrivs|Seccomp)' /proc/self/status",
            "$ ./sandbox python3 -c 'import socket; socket.socket()'",
            '$ ./sandbox mkdir /tmp/seccomp-test; echo "exit=$?"',
            "$ SANDBOX_DUMP=1 ./sandbox true 2>&1 | head -30",
            "$ ./raw-bpf",
        ],
        expected=[
            "NoNewPrivs:\t1",
            "Seccomp:\t2",
            "!PermissionError: [Errno 13] Permission denied",
            "!... 2244 Bad system call   (core dumped) ./sandbox mkdir ...",
            "exit=159",
            "if ($arch == 3221225534)",
            "  if ($syscall == 41)",
            "    action ERRNO(13);",
            "getpid() = 5367",
            "!uname: Operation not permitted",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "Filter survives execve()", "fa": "فیلتر از execve() عبور می‌کند"},
                c("Seccomp: 2 · NoNewPrivs: 1 in the exec'd grep"),
            ),
            (
                {"en": "exit 159 = 128 + SIGSYS", "fa": "exit 159 = 128 + SIGSYS"},
                c("SECCOMP_RET_KILL_PROCESS → force_sig_seccomp()"),
            ),
            (
                {"en": "Arch check comes first", "fa": "بررسی arch اول می‌آید"},
                {"en": "libseccomp guards the i386 ABI bypass", "fa": "libseccomp جلوی دور زدن با ABIِ i386 را می‌گیرد"},
            ),
        ],
        pitfalls=[
            ({"en": "seccomp_load: EACCES", "fa": "seccomp_load: EACCES"}, c("prctl(PR_SET_NO_NEW_PRIVS) first")),
            (
                {"en": "open rule never fires", "fa": "قانون open اجرا نمی‌شود"},
                {"en": "libc calls openat — strace first", "fa": "libc از openat استفاده می‌کند — اول strace"},
            ),
            (
                {"en": "allow-list → segfault", "fa": "segfault در allow-list"},
                {
                    "en": "forgot futex: glibc can't handle ENOSYS there",
                    "fa": "futex جا افتاده است؛ glibc در آنجا ENOSYS را تحمل نمی‌کند",
                },
            ),
        ],
        ext={
            "en": "Write allowlist.c: default ERRNO(ENOSYS), allow only what `cat` needs (strace -f -c). Show cat works and ls fails. Why ENOSYS rather than KILL?",
            "fa": "allowlist.c را بنویسید: پیش‌فرض ERRNO(ENOSYS)، فقط چیزهایی که cat لازم دارد مجاز (strace -f -c). نشان دهید cat کار می‌کند و ls نه. چرا ENOSYS و نه KILL؟",
        },
    ),
    dict(
        slug="04-landlock",
        num="07.4",
        title={"en": "An unprivileged Landlock sandbox", "fa": "یک sandboxِ بدون امتیاز با Landlock"},
        goal={
            "en": "Read and execute everywhere, write only in one directory — no root, and see where the kernel says no.",
            "fa": "خواندن و اجرا همه‌جا، نوشتن فقط در یک پوشه؛ بدون root، و ببینید کرنل کجا نه می‌گوید.",
        },
        where={"en": "VM or any Linux with landlock LSM", "fa": "VM یا هر لینوکس با LSMِ landlock"},
        setup_cards=[
            ("r-kernel", {"en": "LSM active", "fa": "LSM فعال"}, c("cat /sys/kernel/security/lsm | grep landlock")),
            ("r-kernel", {"en": "ABI", "fa": "ABI"}, c("landlock_abi_version = 7 (v6.18.63)")),
            ("r-data", {"en": "Rules", "fa": "قانون‌ها"}, c("/ → READ+EXEC · /tmp/ll-rw → +WRITE")),
            ("r-user", {"en": "No wrappers", "fa": "بدون wrapper"}, c("syscall(SYS_landlock_*) · glibc 2.39")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o landlock-sandbox landlock-sandbox.c",
            "$ mkdir -p /tmp/ll-rw",
            "$ ./landlock-sandbox /tmp/ll-rw sh -c '",
            "    echo ok > /tmp/ll-rw/a; echo no > /tmp/ll-b;",
            "    cat /etc/hostname; mkdir /tmp/ll-dir'",
            "$ ./landlock-sandbox /tmp/ll-rw sh -c 'echo hi 2>/dev/null'",
            "$ strace -f -e trace=landlock_restrict_self,openat \\",
            "    ./landlock-sandbox /tmp/ll-rw sh -c 'echo no > /tmp/ll-b'",
        ],
        expected=[
            "landlock ABI version: 7",
            "write inside: ok",
            "!sh: 3: cannot create /tmp/ll-b: Permission denied",
            "aos-lab",
            "read outside: ok",
            "mkdir: cannot create directory ‘/tmp/ll-dir’: Permission denied",
            "!sh: 1: cannot create /dev/null: Permission denied",
            "landlock_restrict_self(3, 0)            = 0",
            '!openat(AT_FDCWD, "/tmp/ll-b", O_WRONLY|O_CREAT|O_TRUNC, 0666)',
            "    = -1 EACCES (Permission denied)",
        ],
        captured=CAP,
        observe=[
            (
                {"en": "Denied after path lookup", "fa": "رد پس از جستجوی مسیر"},
                c("openat ... = -1 EACCES  (LSM hook, not seccomp)"),
            ),
            (
                {"en": "/dev/null is a file too", "fa": "‏/dev/null هم فایل است"},
                {
                    "en": "WRITE_FILE is handled → granted nowhere but /tmp/ll-rw",
                    "fa": "WRITE_FILE مدیریت می‌شود ← جز /tmp/ll-rw هیچ‌جا داده نشده",
                },
            ),
            ({"en": "No root needed", "fa": "root لازم نیست"}, c("only NO_NEW_PRIVS · landlock_restrict_self()")),
        ],
        pitfalls=[
            (
                {"en": "restrict_self: Operation not permitted", "fa": "restrict_self: Operation not permitted"},
                c("prctl(PR_SET_NO_NEW_PRIVS) first"),
            ),
            (
                {"en": "create_ruleset: Invalid argument", "fa": "create_ruleset: Invalid argument"},
                {"en": "drop rights the running ABI doesn't know", "fa": "حق‌هایی را که ABIِ فعلی نمی‌شناسد حذف کنید"},
            ),
            (
                {"en": "writes still work somewhere", "fa": "نوشتن جایی هنوز کار می‌کند"},
                {"en": "unhandled rights stay allowed", "fa": "حق‌های مدیریت‌نشده مجاز می‌مانند"},
            ),
        ],
        ext={
            "en": "Restrict TCP: handle LANDLOCK_ACCESS_NET_CONNECT_TCP, allow only port 443. Show which errno means 'Landlock said no' and which means 'nobody listens'.",
            "fa": "TCP را محدود کنید: LANDLOCK_ACCESS_NET_CONNECT_TCP را مدیریت و فقط پورت ۴۴۳ را مجاز کنید. نشان دهید کدام errno یعنی «Landlock رد کرد» و کدام یعنی «کسی گوش نمی‌دهد».",
        },
    ),
    dict(
        slug="05-paper-review",
        num="07.5",
        title={"en": "Read two OS papers, write two reviews", "fa": "خواندن دو مقالهٔ سیستم‌عامل و نوشتن دو داوری"},
        goal={
            "en": "Three-pass reading and a one-page review that maps each paper onto Linux v6.18.63.",
            "fa": "خواندن سه‌گذره و یک داوری یک‌صفحه‌ای که هر مقاله را روی Linux v6.18.63 نگاشت کند.",
        },
        where={"en": "Laptop + repo source checkout", "fa": "لپ‌تاپ + checkoutِ سورس مخزن"},
        setup_cards=[
            (
                "r-data",
                {"en": "Paper A", "fa": "مقالهٔ A"},
                {
                    "en": "Linux Scalability to Many Cores · OSDI '10",
                    "fa": "Linux Scalability to Many Cores · OSDI '10",
                },
            ),
            (
                "r-data",
                {"en": "Paper B", "fa": "مقالهٔ B"},
                {"en": "A Decade of Wasted Cores · EuroSys '16", "fa": "A Decade of Wasted Cores · EuroSys '16"},
            ),
            (
                "r-user",
                {"en": "Template", "fa": "قالب"},
                {"en": "review-template.md: five Cs + 7 sections", "fa": "review-template.md: پنج C و ۷ بخش"},
            ),
            ("r-kernel", {"en": "Source", "fa": "سورس"}, c("_shared/sources/linux @ v6.18.63")),
        ],
        steps=[
            "# pass 1: 10 min each -> five Cs",
            "$ cp review-template.md review-A.md",
            "# pass 2: 1 h each -> figures, axes, baselines",
            "# map onto today's kernel:",
            '$ git grep -n "^static int sched_balance_rq" kernel/sched/fair.c',
            '$ git grep -n "^static bool update_sd_pick_busiest" kernel/sched/fair.c',
            '$ git grep -n "struct lockref d_lockref" include/linux/dcache.h',
        ],
        expected=[
            '$ git grep -n "^static int sched_balance_rq" kernel/sched/fair.c',
            "!kernel/sched/fair.c:12052:static int sched_balance_rq(int this_cpu, ...",
            '$ git grep -n "^static bool update_sd_pick_busiest" kernel/sched/fair.c',
            "!kernel/sched/fair.c:10740:static bool update_sd_pick_busiest(...",
            '$ git grep -n "struct lockref d_lockref" include/linux/dcache.h',
            "!include/linux/dcache.h:113:\tstruct lockref d_lockref;",
        ],
        captured={
            "en": "the repo checkout (Linux v6.18.63), 2026-11-15",
            "fa": "checkoutِ مخزن (Linux v6.18.63)، ۲۰۲۶-۱۱-۱۵",
        },
        observe=[
            (
                {"en": "Paper B's balancer still exists", "fa": "load balancerِ مقالهٔ B هنوز هست"},
                {
                    "en": "renamed; EEVDF replaced CFS's pick, not balancing",
                    "fa": "نامش عوض شده؛ EEVDF انتخاب CFS را عوض کرد، نه توازن را",
                },
            ),
            (
                {"en": "Paper A's dentry counter changed", "fa": "شمارندهٔ dentry مقالهٔ A عوض شده"},
                {"en": "lockref instead of sloppy counters", "fa": "lockref به‌جای sloppy counter"},
            ),
            (
                {"en": "Both used big NUMA boxes", "fa": "هر دو ماشین بزرگ NUMA داشتند"},
                {"en": "48 / 64 cores — not an 8-vCPU VM", "fa": "۴۸ / ۶۴ هسته — نه یک VM با ۸ vCPU"},
            ),
        ],
        pitfalls=[
            (
                {"en": "section-by-section summary", "fa": "خلاصهٔ بخش‌به‌بخش"},
                {"en": "one sentence each: problem, insight, mechanism", "fa": "هر کدام یک جمله: مسئله، بینش، سازوکار"},
            ),
            (
                {"en": '"Linux is 138× slower"', "fa": "«لینوکس ۱۳۸ برابر کندتر است»"},
                {"en": "a corner case; typical 13–24 %", "fa": "حالت گوشه‌ای؛ معمولاً ۱۳ تا ۲۴٪"},
            ),
            ({"en": "load_balance() not found", "fa": "load_balance() پیدا نمی‌شود"}, c("search sched_balance_*")),
        ],
        ext={
            "en": "Pick one Wasted Cores bug. Using only v6.18.63 source and numactl/perf sched/mpstat, argue in half a page whether it can still happen and design the experiment that would show it.",
            "fa": "یکی از باگ‌های Wasted Cores را انتخاب کنید. فقط با سورس v6.18.63 و ابزارهای numactl و perf sched و mpstat در نیم صفحه استدلال کنید که آیا هنوز ممکن است رخ دهد، و آزمایشی طراحی کنید که آن را نشان دهد.",
        },
    ),
]
