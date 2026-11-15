# Lab-deck content for 01-architecture. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced OS · 01 Architecture", "fa": "سیستم‌عامل پیشرفته · ۰۱ معماری"}
CAP = {
    "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15",
    "fa": "aos-lab (VirtualBox، Ubuntu 24.04، Linux 6.18.63)، ۱۴۰۵/۰۸/۲۴",
}

LABS = [
    dict(
        slug="01-strace-map",
        num="01.1",
        title={"en": "Map every syscall of cat to its kernel entry", "fa": "نگاشت هر syscall برنامهٔ cat به ورودی کرنل"},
        goal={
            "en": "Turn an strace log into name → number → table entry → the __x64_sys_* symbol in the running kernel.",
            "fa": "یک لاگ strace را به نام ← شماره ← ورودی جدول ← نماد __x64_sys_* در کرنل در حال اجرا تبدیل کنید.",
        },
        where={"en": "aos-lab VM", "fa": "VM با نام aos-lab"},
        setup_cards=[
            ("r-user", {"en": "Tracer", "fa": "ردیاب"}, {"en": "strace -f (ptrace)", "fa": "strace -f (ptrace)"}),
            (
                "r-data",
                {"en": "Table", "fa": "جدول"},
                {"en": "syscall_64.tbl from v6.18.63", "fa": "syscall_64.tbl از v6.18.63"},
            ),
            ("r-kernel", {"en": "Symbols", "fa": "نمادها"}, {"en": "/proc/kallsyms", "fa": "/proc/kallsyms"}),
            (
                "r-hardware",
                {"en": "ABI", "fa": "ABI"},
                {"en": "x86-64: rax = number", "fa": "در x86-64 شماره در rax است"},
            ),
        ],
        steps=[
            "$ cd ~/work/01-architecture/lab01",
            "$ strace -f -o cat.trace cat /etc/hostname",
            "$ strace -c -f cat /etc/hostname > /dev/null",
            "$ bash map-syscalls.sh cat.trace",
            "$ grep -w -e do_syscall_64 -e x64_sys_call \\",
            "    -e __x64_sys_read /proc/kallsyms",
        ],
        expected=[
            "count  syscall              nr  tbl entry            kernel symbol              in kallsyms",
            "   31  openat              257  sys_openat           __x64_sys_openat           yes",
            "   23  mmap                  9  sys_mmap             __x64_sys_mmap             yes",
            "!   20  fstat                 5  sys_newfstat         __x64_sys_newfstat         yes",
            "!    5  read                  0  sys_read             __x64_sys_read             yes",
            "    ...",
            "    1  exit_group          231  sys_exit_group       __x64_sys_exit_group       yes",
            "$ grep -w -e do_syscall_64 -e x64_sys_call /proc/kallsyms",
            "ffffffffb5929b60 T x64_sys_call",
            "ffffffffb6c8a1d0 T do_syscall_64",
        ],
        observe=[
            (
                {"en": "cat itself makes ~5 calls", "fa": "خود cat حدود ۵ فراخوانی دارد"},
                {
                    "en": "most of 121 come from ld.so and locale setup",
                    "fa": "بیشتر ۱۲۱ فراخوانی از ld.so و تنظیم locale است",
                },
            ),
            (
                {"en": "Name ≠ entry point", "fa": "نام ≠ نقطهٔ ورود"},
                {"en": "fstat → sys_newfstat", "fa": "fstat → sys_newfstat"},
            ),
            (
                {"en": "Every stub is real", "fa": "همهٔ stubها واقعی‌اند"},
                {
                    "en": "__x64_sys_* in kallsyms (SYSCALL_DEFINEn)",
                    "fa": "مثلاً __x64_sys_read در kallsyms (ساختهٔ SYSCALL_DEFINEn)",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "every row says 'no'", "fa": "همهٔ ردیف‌ها no هستند"},
                {
                    "en": "CRLF table from Windows: script strips \\r",
                    "fa": "جدول CRLF از ویندوز؛ اسکریپت \\r را حذف می‌کند",
                },
            ),
            (
                {"en": "addresses all zero", "fa": "همهٔ آدرس‌ها صفرند"},
                {"en": "kptr_restrict: use sudo", "fa": "kptr_restrict؛ از sudo استفاده کنید"},
            ),
            (
                {"en": "<... resumed> counted twice", "fa": "<... resumed> دو بار شمرده شده"},
                {"en": "skip resumed halves", "fa": "نیمه‌های resumed را رد کنید"},
            ),
        ],
        ext={
            "en": "Count raw_syscalls:sys_enter by number for the cat PID with bpftrace (no ptrace stop) and compare with strace -c. Explain any difference.",
            "fa": "با bpftrace رویداد raw_syscalls:sys_enter را بر اساس شماره برای PID برنامهٔ cat بشمارید (بدون توقف ptrace) و با strace -c مقایسه کنید. هر تفاوتی را توضیح دهید.",
        },
        captured=CAP,
    ),
    dict(
        slug="02-raw-syscall",
        num="01.2",
        title={
            "en": "Raw syscall: libc vs syscall(3) vs inline asm",
            "fa": "syscall خام: libc در برابر syscall(3) و inline asm",
        },
        goal={
            "en": "See the x86-64 register ABI and the -errno convention, prove CPL = 3, and time each path.",
            "fa": "ABI رجیستری x86-64 و قرارداد -errno را ببینید، ثابت کنید CPL برابر ۳ است و هر مسیر را زمان‌سنجی کنید.",
        },
        where={"en": "aos-lab VM", "fa": "VM با نام aos-lab"},
        setup_cards=[
            (
                "r-user",
                {"en": "Three paths", "fa": "سه مسیر"},
                {"en": "write() · syscall() · asm", "fa": "write() · syscall() · asm"},
            ),
            (
                "r-hardware",
                {"en": "Clobbers", "fa": "رجیسترهای ازبین‌رفته"},
                {"en": "rcx = RIP, r11 = RFLAGS", "fa": "rcx = RIP، r11 = RFLAGS"},
            ),
            (
                "r-kernel",
                {"en": "Errors", "fa": "خطاها"},
                {"en": "kernel -9 vs libc -1/errno", "fa": "کرنل -9 در برابر libc -1/errno"},
            ),
            ("r-data", {"en": "Build", "fa": "ساخت"}, {"en": "gcc -Wall -Wextra -O2", "fa": "gcc -Wall -Wextra -O2"}),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o raw_syscall raw_syscall.c",
            "$ gcc -Wall -Wextra -O2 -o cpl cpl.c",
            "$ taskset -c 3 ./raw_syscall",
            "$ strace -e trace=write,getpid \\",
            "    ./raw_syscall 3 > /dev/null",
            "$ ./cpl",
            "$ gdb -batch -ex 'disassemble read' \\",
            "    /lib/x86_64-linux-gnu/libc.so.6",
        ],
        expected=[
            "returns: 15 19 19",
            "libc write(999): ret=-1 errno=9 (Bad file descriptor)",
            "!raw  write(999): ret=-9  (kernel returns -errno)",
            "libc getpid()          103.3 ns/call",
            "syscall(SYS_getpid)    110.8 ns/call",
            "inline asm syscall     106.8 ns/call",
            "empty loop               0.7 ns/iter",
            "",
            "$ ./cpl",
            "!CS = 0x0033  -> index 6, RPL/CPL = 3",
            "cli            -> killed by signal 11 (Segmentation fault)",
        ],
        observe=[
            (
                {"en": "strace sees three identical writes", "fa": "strace سه write یکسان می‌بیند"},
                {"en": "all end in syscall with rax = 1", "fa": "همه با rax = 1 به syscall ختم می‌شوند"},
            ),
            (
                {"en": "read() wrapper", "fa": "wrapper تابع read()"},
                {"en": "xor %eax,%eax; syscall; cmp $-4096,%rax", "fa": "xor %eax,%eax; syscall; cmp $-4096,%rax"},
            ),
            (
                {"en": "CS = 0x33", "fa": "CS = 0x33"},
                {"en": "__USER_CS: index 6, RPL 3", "fa": "__USER_CS: اندیس ۶، RPL برابر ۳"},
            ),
        ],
        pitfalls=[
            (
                {"en": "breaks only at -O2", "fa": "فقط در -O2 خراب می‌شود"},
                {"en": 'add "rcx", "r11", "memory" clobbers', "fa": 'clobberهای "rcx"، "r11" و "memory" را اضافه کنید'},
            ),
            (
                {"en": "-1 vs -22 confusion", "fa": "سردرگمی -1 و -22"},
                {"en": "compare -raw with errno", "fa": "-raw را با errno مقایسه کنید"},
            ),
            (
                {"en": "timings jump 2×", "fa": "زمان‌ها دو برابر می‌پرند"},
                {"en": "shared VM: compare within one run", "fa": "VM مشترک است؛ فقط در یک اجرا مقایسه کنید"},
            ),
        ],
        ext={
            "en": "Call mmap with your own 6-argument inline-asm wrapper, once with arg 4 in rcx and once correctly. Explain the wrong result from SC_X86_64_REGS_TO_ARGS.",
            "fa": "mmap را با wrapper شش‌آرگومانی inline asm خودتان صدا بزنید؛ یک بار با آرگومان ۴ در rcx و یک بار درست. نتیجهٔ غلط را با SC_X86_64_REGS_TO_ARGS توضیح دهید.",
        },
        captured=CAP,
    ),
    dict(
        slug="03-interrupts",
        num="01.3",
        title={"en": "Count interrupts and tracepoints", "fa": "شمارش interruptها و tracepointها"},
        goal={
            "en": "Measure which interrupt sources fire, cross-check with irq:* tracepoints, and see that page faults are counted elsewhere.",
            "fa": "اندازه بگیرید کدام منبع‌های interrupt فعال می‌شوند، با tracepointهای irq:* مقایسه کنید و ببینید page faultها جای دیگری شمرده می‌شوند.",
        },
        where={"en": "aos-lab VM (root for perf -a)", "fa": "VM با نام aos-lab (برای perf -a به root نیاز است)"},
        setup_cards=[
            (
                "r-hardware",
                {"en": "Sources", "fa": "منبع‌ها"},
                {"en": "APIC timer · IPIs · virtio", "fa": "تایمر APIC · IPIها · virtio"},
            ),
            (
                "r-data",
                {"en": "Counters", "fa": "شمارنده‌ها"},
                {"en": "/proc/interrupts (since boot)", "fa": "/proc/interrupts (از زمان بوت)"},
            ),
            (
                "r-kernel",
                {"en": "Tracepoints", "fa": "tracepointها"},
                {"en": "irq:* · irq_vectors:* · exceptions:*", "fa": "irq:* · irq_vectors:* · exceptions:*"},
            ),
            ("r-user", {"en": "Load", "fa": "بار"}, {"en": "dd ... oflag=direct", "fa": "dd ... oflag=direct"}),
        ],
        steps=[
            "$ bash irq-delta.sh 5 8",
            "$ bash irq-delta.sh 5 8 -- \\",
            "    dd if=/dev/zero of=big.bin bs=1M count=512 oflag=direct",
            "$ sudo perf stat -a -e 'irq:irq_handler_entry,\\",
            "    irq_vectors:local_timer_entry,\\",
            "    irq_vectors:reschedule_entry,exceptions:page_fault_user' sleep 5",
        ],
        expected=[
            "$ bash irq-delta.sh 5 8",
            "   delta  irq    source",
            "!   46186  CAL    Function call interrupts",
            "    9223  21     IO-APIC 21-fasteoi ahci[0000:00:0d.0]",
            "!    8746  LOC    Local timer interrupts",
            "     193  RES    Rescheduling interrupts",
            "",
            "$ sudo perf stat -a -e ... sleep 5",
            "              3650      irq:irq_handler_entry",
            "             22222      irq_vectors:local_timer_entry",
            "!            134260      exceptions:page_fault_user",
        ],
        observe=[
            (
                {"en": "Named vectors ≠ device IRQs", "fa": "بردارهای نام‌دار ≠ IRQ دستگاه"},
                {
                    "en": "LOC/CAL/RES bypass irq_handler_entry (3,650)",
                    "fa": "LOC و CAL و RES از irq_handler_entry (۳٬۶۵۰) نمی‌گذرند",
                },
            ),
            (
                {"en": "LOC ≈ 220/s per CPU, HZ=1000", "fa": "LOC حدود ۲۲۰ در ثانیه برای هر CPU، با HZ=1000"},
                {"en": "NO_HZ: idle CPUs skip ticks", "fa": "NO_HZ: CPUهای بیکار tick را رد می‌کنند"},
            ),
            (
                {"en": "134,260 page faults, none here", "fa": "۱۳۴٬۲۶۰ page fault، هیچ‌کدام اینجا نیست"},
                {"en": "exceptions are not interrupts", "fa": "exception همان interrupt نیست"},
            ),
        ],
        pitfalls=[
            (
                {"en": "irq_vectors:* not found", "fa": "رویدادهای irq_vectors پیدا نمی‌شوند"},
                {
                    "en": "ls /sys/kernel/tracing/events/irq_vectors/",
                    "fa": "ls /sys/kernel/tracing/events/irq_vectors/",
                },
            ),
            (
                {"en": "perf -a: permission denied", "fa": "perf -a: اجازه ندارید"},
                {"en": "sudo", "fa": "از sudo استفاده کنید"},
            ),
            (
                {"en": "huge LOC numbers", "fa": "عددهای خیلی بزرگ LOC"},
                {"en": "diff two snapshots", "fa": "دو نمونه را با هم مقایسه کنید"},
            ),
        ],
        ext={
            "en": "bpftrace: a histogram of top-half run time per handler name from irq_handler_entry/exit, during the dd load. Why is per-CPU pairing safe?",
            "fa": "با bpftrace برای هر نام handler یک هیستوگرام از زمان اجرای نیمهٔ بالایی، از روی irq_handler_entry/exit و هنگام بار dd، بسازید. چرا جفت کردن بر اساس CPU امن است؟",
        },
        captured=CAP,
    ),
    dict(
        slug="04-syscall-cost",
        num="01.4",
        title={"en": "What does a syscall cost?", "fa": "هزینهٔ یک syscall چقدر است؟"},
        goal={
            "en": "Measure ns per call for an empty loop, vDSO clock_gettime, the same call via syscall, and getpid; then add strace.",
            "fa": "زمان هر فراخوانی را برای حلقهٔ خالی، clock_gettime از vDSO، همان فراخوانی با syscall و getpid اندازه بگیرید؛ بعد strace را اضافه کنید.",
        },
        where={
            "en": "aos-lab VM (no PMU: clock_gettime timing)",
            "fa": "VM با نام aos-lab (بدون PMU؛ زمان‌سنجی با clock_gettime)",
        },
        setup_cards=[
            (
                "r-user",
                {"en": "Timer", "fa": "زمان‌سنج"},
                {"en": "CLOCK_MONOTONIC, 7 rounds", "fa": "CLOCK_MONOTONIC، ۷ دور"},
            ),
            (
                "r-data",
                {"en": "vDSO", "fa": "vDSO"},
                {"en": "[vdso] + [vvar] in /proc/self/maps", "fa": "[vdso] و [vvar] در /proc/self/maps"},
            ),
            (
                "r-hardware",
                {"en": "Clocksource", "fa": "منبع ساعت"},
                {"en": "tsc → vDSO works in ring 3", "fa": "tsc ← vDSO در ring 3 کار می‌کند"},
            ),
            (
                "r-kernel",
                {"en": "Mitigations", "fa": "وصله‌ها"},
                {"en": "meltdown: Not affected → no PTI", "fa": "meltdown: Not affected ← بدون PTI"},
            ),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o syscost syscost.c",
            "$ taskset -c 2 ./syscost",
            "$ grep -E 'vdso|vvar' /proc/self/maps",
            "$ strace -f -c -e trace=getpid,clock_gettime \\",
            "    ./syscost 200000 > /dev/null",
            "$ time ./syscost 200000 > /dev/null",
            "$ time strace -o /dev/null ./syscost 200000 > /dev/null",
        ],
        expected=[
            "clocksource            tsc",
            "meltdown (PTI)         Not affected",
            "empty loop                         min     2.2  median     3.2",
            "!clock_gettime() via vDSO           min    14.5  median    14.8",
            "!syscall(SYS_clock_gettime)         min   110.3  median   123.9",
            "syscall(SYS_getpid)                min    91.4  median    96.8",
            "",
            "$ strace -f -c -e trace=getpid,clock_gettime ./syscost 200000",
            " 68.71   21.308826     15   1420000   clock_gettime",
            "",
            "$ time strace -o /dev/null ./syscost 200000   # vs 1.351s",
            "!real	1m10.384s",
        ],
        observe=[
            (
                {"en": "vDSO ≈ 8× cheaper", "fa": "vDSO حدود ۸ برابر ارزان‌تر"},
                {
                    "en": "14.8 vs 123.9 ns: no boundary crossing",
                    "fa": "۱۴٫۸ در برابر ۱۲۳٫۹ نانوثانیه: بدون عبور از مرز",
                },
            ),
            (
                {"en": "strace saw only the forced calls", "fa": "strace فقط فراخوانی‌های اجباری را دید"},
                {
                    "en": "1,420,000 = syscall(SYS_clock_gettime) only",
                    "fa": "۱٬۴۲۰٬۰۰۰ = فقط syscall(SYS_clock_gettime)",
                },
            ),
            (
                {"en": "strace: 1.35 s → 70.4 s", "fa": "strace: ۱٫۳۵ ثانیه ← ۷۰٫۴ ثانیه"},
                {"en": "ptrace stop on every entry and exit", "fa": "توقف ptrace در هر ورود و خروج"},
            ),
        ],
        pitfalls=[
            (
                {"en": "vDSO as slow as syscall", "fa": "vDSO به کندی syscall"},
                {"en": "clocksource hpet/acpi_pm → fallback", "fa": "منبع ساعت hpet/acpi_pm ← برگشت به syscall"},
            ),
            (
                {"en": "empty loop = 0 ns", "fa": "حلقهٔ خالی = ۰ نانوثانیه"},
                {"en": "keep the volatile sink", "fa": "sink از نوع volatile را نگه دارید"},
            ),
            (
                {"en": "perf cycles <not supported>", "fa": "perf cycles <not supported>"},
                {"en": "no PMU in this guest", "fa": "این مهمان PMU ندارد"},
            ),
        ],
        ext={
            "en": "Time syscall(1000) (-ENOSYS) against getpid. Trace which code in syscall_64.c runs for it and explain why it is barely cheaper.",
            "fa": "زمان syscall(1000) (یعنی -ENOSYS) را با getpid مقایسه کنید. ببینید کدام کد در syscall_64.c برایش اجرا می‌شود و توضیح دهید چرا فقط کمی ارزان‌تر است.",
        },
        captured=CAP,
    ),
    dict(
        slug="05-ftrace-vfs-read",
        num="01.5",
        title={"en": "ftrace function_graph of vfs_read()", "fa": "function_graph از ftrace برای vfs_read()"},
        goal={
            "en": "See the real call tree under one read(), from vfs_read() into the file system, and confirm noinstr entry code is invisible.",
            "fa": "درخت واقعی فراخوانی زیر یک read() را از vfs_read() تا فایل‌سیستم ببینید و تأیید کنید کد ورود noinstr دیده نمی‌شود.",
        },
        where={"en": "VM only (root, ftrace)", "fa": "فقط VM (root، ftrace)"},
        setup_cards=[
            (
                "r-kernel",
                {"en": "Tracer", "fa": "ردیاب"},
                {"en": "function_graph + funcgraph-tail", "fa": "function_graph + funcgraph-tail"},
            ),
            (
                "r-data",
                {"en": "Filters", "fa": "فیلترها"},
                {"en": "-g vfs_read · -l <read path> · -F cat", "fa": "-g vfs_read · -l <read path> · -F cat"},
            ),
            (
                "r-user",
                {"en": "Bounds", "fa": "محدودیت‌ها"},
                {"en": "--max-graph-depth 6 · timeout 10", "fa": "--max-graph-depth 6 · timeout 10"},
            ),
            (
                "r-hardware",
                {"en": "Cleanup", "fa": "پاک‌سازی"},
                {"en": "trap: trace-cmd reset", "fa": "trap: trace-cmd reset"},
            ),
        ],
        steps=[
            "$ cd ~/work/01-architecture/lab05",
            "$ sudo bash ftrace-vfs-read.sh /etc/hostname cat.graph",
            "$ sudo N=6 bash ftrace-vfs-read.sh /etc/hostname cat.graph",
            "$ sudo bash ftrace-vfs-read.sh /proc/version proc.graph",
            "# inside: timeout 10 trace-cmd record -p function_graph \\",
            "#   -g vfs_read --max-graph-depth 6 -l <read path> -F cat ...",
            "$ sudo grep -c -w do_syscall_64 \\",
            "    /sys/kernel/tracing/available_filter_functions",
        ],
        expected=[
            "  #1   15 lines    6.204 us  ext4_file_read_iter()",
            "!  #6   21 lines  ! 949.028 us  ext4_file_read_iter()",
            "                  |  vfs_read() {",
            "                  |    ext4_file_read_iter() {",
            "                  |      generic_file_read_iter() {",
            "                  |        filemap_read() {",
            "     ! 152.831 us |            filemap_add_folio();",
            "!     ! 548.053 us |            filemap_update_page();",
            "",
            "# /proc/version:  #6  ...  proc_reg_read_iter()",
            "$ ... grep -c -w do_syscall_64 ...",
            "0",
        ],
        observe=[
            (
                {"en": "7 vfs_read() for 5 read()s", "fa": "۷ بار vfs_read() برای ۵ بار read()"},
                {"en": "pread64 also calls vfs_read()", "fa": "pread64 هم vfs_read() را صدا می‌زند"},
            ),
            (
                {"en": "Cache miss: 949 µs vs 6 µs", "fa": "نبودن در cache: ۹۴۹ در برابر ۶ میکروثانیه"},
                {"en": "filemap_add_folio + filemap_update_page", "fa": "filemap_add_folio + filemap_update_page"},
            ),
            (
                {"en": "Entry code is not traceable", "fa": "کد ورود قابل ردیابی نیست"},
                {"en": "do_syscall_64: noinstr → count 0", "fa": "do_syscall_64: noinstr ← شمارش 0"},
            ),
        ],
        pitfalls=[
            (
                {"en": "record failed: bad -l pattern", "fa": "خطای record: الگوی -l نامعتبر"},
                {"en": "inlined fn (new_sync_read): drop it", "fa": "تابع inline شده (new_sync_read) را حذف کنید"},
            ),
            (
                {"en": "dropping the filters", "fa": "برداشتن فیلترها"},
                {
                    "en": "never: unfiltered tracing can soft-lock",
                    "fa": "هرگز؛ ردیابی بی‌فیلتر می‌تواند soft lockup بدهد",
                },
            ),
            (
                {"en": "N=6 ignored", "fa": "N=6 نادیده گرفته می‌شود"},
                {"en": "sudo N=6 bash ...", "fa": "sudo N=6 bash ..."},
            ),
        ],
        ext={
            "en": "Trace /etc/hostname, /proc/version and a pipe. Name the ->read_iter each reaches and explain via vfs_read() L569-574. Why is __switch_to never in the graph?",
            "fa": "‏/etc/hostname و /proc/version و یک pipe را trace کنید. ‎->read_iter هر کدام را نام ببرید و با vfs_read() خط‌های ۵۶۹ تا ۵۷۴ توضیح دهید. چرا __switch_to هرگز در گراف نیست؟",
        },
        captured=CAP,
    ),
]
