# Lab-deck content for 03-concurrency. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced OS · 03 Concurrency", "fa": "سیستم‌عامل پیشرفته · ۰۳ هم‌روندی"}
CAP = {
    "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15; shared 8-vCPU guest, timings are noisy",
    "fa": "aos-lab (VirtualBox، Ubuntu 24.04، Linux 6.18.63)، 2026-11-15؛ مهمان مشترک ۸ vCPU، زمان‌ها نویز دارند",
}


def same(s):
    return {"en": s, "fa": s}


LABS = [
    dict(
        slug="01-data-race",
        num="03.1",
        title={"en": "Data race → TSan → mutex → atomic", "fa": "Data race ← TSan ← mutex ← atomic"},
        goal={
            "en": "Watch count++ lose updates on four threads, let ThreadSanitizer name the race, fix it twice and measure each fix.",
            "fa": "ببینید count++ روی چهار نخ به‌روزرسانی گم می‌کند، بگذارید ThreadSanitizer race را نام ببرد، دو بار درستش کنید و هزینهٔ هر راه را بسنجید.",
        },
        where={"en": "aos-lab VM (user space)", "fa": "VM با نام aos-lab (فضای کاربر)"},
        setup_cards=[
            ("r-user", {"en": "Program", "fa": "برنامه"}, same("race.c: race | mutex | atomic")),
            ("r-hardware", {"en": "Atomic RMW", "fa": "RMW اتمی"}, same("atomic_fetch_add → lock xadd")),
            ("r-kernel", {"en": "Detector", "fa": "آشکارساز"}, same("gcc -fsanitize=thread")),
            ("r-data", {"en": "Cost", "fa": "هزینه"}, same("perf stat -e task-clock,context-switches")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -pthread race.c -o race",
            "$ gcc -Wall -Wextra -O1 -g -fsanitize=thread \\",
            "    -pthread race.c -o race-tsan",
            "$ for m in race mutex atomic; do ./race $m 4 1000000; done",
            "$ ./race-tsan race 2 1000",
            "$ sudo perf stat -e task-clock,context-switches \\",
            "    ./race mutex 4 1000000",
        ],
        expected=[
            "$ for m in race mutex atomic; do ./race $m 4 1000000; done",
            "!mode=race   threads=4 expected=4000000 got=2498418 lost=1501582",
            "mode=mutex  threads=4 ... lost=0 time=0.358s ns/inc=89.6",
            "mode=atomic threads=4 ... lost=0 time=0.098s ns/inc=24.4",
            "$ ./race-tsan race 2 1000",
            "!WARNING: ThreadSanitizer: data race (pid=4446)",
            "  Read of size 8 at 0x55912d33b070 by thread T2:",
            "  Previous write of size 8 at 0x55912d33b070 by thread T1:",
            "  Location is global 'g_plain' of size 8",
            "$ sudo perf stat ... ./race mutex 4 1000000",
            "           1002.69 msec task-clock  # 1.327 CPUs utilized",
            "!              349      context-switches",
        ],
        observe=[
            (
                {"en": "Lost updates", "fa": "به‌روزرسانی‌های گم‌شده"},
                {
                    "en": "load-add-store interleave; volatile does not help",
                    "fa": "load و add و store درهم می‌شوند؛ volatile کمکی نمی‌کند",
                },
            ),
            (
                {"en": "TSan names both accesses", "fa": "TSan هر دو دسترسی را نام می‌برد"},
                same("race.c:33 write vs race.c:33 read"),
            ),
            (
                {"en": "Mutex costs context switches", "fa": "mutex هزینهٔ context switch دارد"},
                {"en": "contended pthread_mutex sleeps in futex", "fa": "pthread_mutex با رقابت در futex می‌خوابد"},
            ),
        ],
        pitfalls=[
            (
                {"en": "race mode looks correct", "fa": "حالت race درست به نظر می‌آید"},
                {"en": "use ≥1M iterations and 4 threads", "fa": "دست‌کم ۱ میلیون تکرار و ۴ نخ"},
            ),
            (
                {"en": "TSan: unexpected memory mapping", "fa": "TSan: unexpected memory mapping"},
                same("setarch x86_64 -R ./race-tsan ..."),
            ),
            (
                {"en": "cycles <not supported>", "fa": "cycles <not supported>"},
                {"en": "no PMU in the guest: software events", "fa": "PMU در مهمان نیست: رویدادهای نرم‌افزاری"},
            ),
        ],
        ext={
            "en": "Remove sharing: per-thread counters, packed in one array vs. padded to 64 bytes each. Measure both and explain the gap with cache coherence.",
            "fa": "اشتراک را حذف کنید: شمارندهٔ جدا برای هر نخ، یک بار فشرده در یک آرایه و یک بار هر کدام در ۶۴ بایت جدا. هر دو را بسنجید و فاصله را با cache coherence توضیح دهید.",
        },
        captured=CAP,
    ),
    dict(
        slug="02-producer-consumer",
        num="03.2",
        title={"en": "Producer-Consumer three ways", "fa": "Producer-Consumer به سه روش"},
        goal={
            "en": "One bounded buffer built with semaphores, with condition variables and with a Go channel; same checksum, different waiting.",
            "fa": "یک بافر محدود با semaphore، با condition variable و با کانال Go؛ checksum یکسان، شیوهٔ انتظار متفاوت.",
        },
        where={"en": "aos-lab VM (user space)", "fa": "VM با نام aos-lab (فضای کاربر)"},
        setup_cards=[
            ("r-user", {"en": "Semaphores", "fa": "Semaphore"}, same("sem_t empty, full + mutex")),
            ("r-user", {"en": "Condvars", "fa": "Condition variable"}, same("while (count == 0) cond_wait")),
            ("r-data", {"en": "Go channel", "fa": "کانال Go"}, same("make(chan int64, cap); close(ch)")),
            ("r-kernel", {"en": "Kernel view", "fa": "نگاه کرنل"}, same("strace -f -c -e trace=futex")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -pthread pc_sem.c -o pc_sem",
            "$ gcc -Wall -Wextra -O2 -pthread pc_cond.c -o pc_cond",
            "$ go build -o pc_chan pc_chan.go",
            "$ for cap in 1 16 1024; do",
            "    ./pc_sem 1000000 $cap; ./pc_cond 1000000 $cap",
            "    ./pc_chan 1000000 $cap; done",
            "$ strace -f -c -e trace=futex ./pc_cond 200000 16",
        ],
        expected=[
            "sem   items=1000000 cap=1 sum=500000500000 OK ns/item=3257",
            "!cond  items=1000000 cap=1 ... ns/item=76909 waits(full)=722595",
            "chan  items=1000000 cap=1 sum=500000500000 OK ns/item=181",
            "sem   items=1000000 cap=16 ... OK ns/item=11667",
            "cond  items=1000000 cap=16 ... OK ns/item=8917",
            "chan  items=1000000 cap=16 ... OK ns/item=50",
            "cond  items=1000000 cap=1024 ... OK ns/item=186 waits(full)=975",
            "chan  items=1000000 cap=1024 ... OK ns/item=39",
            "$ strace -f -c -e trace=futex ./pc_cond 200000 16",
            "% time     seconds  usecs/call     calls    errors syscall",
            "!100.00   56.667936         321    175989     24310 futex",
        ],
        observe=[
            ({"en": "Same checksum, all three", "fa": "checksum یکسان در هر سه"}, same("sum=500000500000 OK")),
            (
                {"en": "Capacity 1 = ping-pong", "fa": "ظرفیت ۱ یعنی پینگ‌پنگ"},
                {"en": "every item forces a sleep/wake pair", "fa": "هر آیتم یک جفت خواب و بیدار لازم دارد"},
            ),
            (
                {"en": "Go parks goroutines, not threads", "fa": "Go گوروتین را park می‌کند، نه نخ را"},
                {
                    "en": "the runtime scheduler does the waiting (M02)",
                    "fa": "scheduler خود runtime انتظار را انجام می‌دهد (ماژول ۰۲)",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "if instead of while", "fa": "if به‌جای while"},
                {
                    "en": "breaks with 2 consumers or spurious wake-ups",
                    "fa": "با ۲ مصرف‌کننده یا بیدارشدن بی‌دلیل خراب می‌شود",
                },
            ),
            (
                {"en": "hang at shutdown", "fa": "گیرکردن در پایان"},
                {
                    "en": "poison pill per consumer, or closed flag + broadcast",
                    "fa": "یک poison pill برای هر مصرف‌کننده یا پرچم closed و broadcast",
                },
            ),
            (
                {"en": "Go: all goroutines are asleep", "fa": "Go: all goroutines are asleep"},
                same("producer must close(ch)"),
            ),
        ],
        ext={
            "en": "Generalise the condvar version to P producers and C consumers with a clean shutdown; the sum must stay exact.",
            "fa": "نسخهٔ condvar را برای P تولیدکننده و C مصرف‌کننده با پایان تمیز تعمیم دهید؛ جمع باید دقیق بماند.",
        },
        captured=CAP,
    ),
    dict(
        slug="03-readers-writers",
        num="03.3",
        title={"en": "Readers-Writers and writer starvation", "fa": "Readers-Writers و گرسنگی نویسنده"},
        goal={
            "en": "Show that glibc's default rwlock lets overlapping readers starve a writer, and that the writer-preferring kind fixes it.",
            "fa": "نشان دهید rwlock پیش‌فرض glibc اجازه می‌دهد خواننده‌های هم‌پوشان نویسنده را گرسنه نگه دارند و گونهٔ ترجیح‌دهندهٔ نویسنده درستش می‌کند.",
        },
        where={"en": "aos-lab VM (user space)", "fa": "VM با نام aos-lab (فضای کاربر)"},
        setup_cards=[
            ("r-user", {"en": "Readers", "fa": "خواننده‌ها"}, same("4 threads x 100 us read sections")),
            ("r-user", {"en": "Writer", "fa": "نویسنده"}, same("wrlock every 1 ms, wait timed")),
            ("r-kernel", {"en": "Default kind", "fa": "گونهٔ پیش‌فرض"}, same("PTHREAD_RWLOCK_PREFER_READER_NP")),
            ("r-data", {"en": "Fix", "fa": "درمان"}, same("..._PREFER_WRITER_NONRECURSIVE_NP")),
        ],
        steps=["$ gcc -Wall -Wextra -O2 -pthread rw.c -o rw", "$ ./rw reader 4 3", "$ ./rw writer 4 3"],
        expected=[
            "$ ./rw reader 4 3",
            "!pref=reader readers=4 secs=3 reads=161806 writes=0 (+1 after stop)",
            "              writer_wait max=4.281s avg=4.281458s",
            "$ ./rw writer 4 3",
            "!pref=writer readers=4 secs=3 reads=270250 writes=188 (+1 after stop)",
            "              writer_wait max=0.036s avg=0.003488s",
            "# more runs: reader writes=0, 0; writer max wait 2-36 ms",
        ],
        observe=[
            (
                {
                    "en": "Reader preference: writer waits the whole run",
                    "fa": "ترجیح خواننده: نویسنده کل اجرا منتظر می‌ماند",
                },
                {
                    "en": "a new reader is admitted while a writer waits",
                    "fa": "خوانندهٔ تازه پذیرفته می‌شود در حالی که نویسنده منتظر است",
                },
            ),
            (
                {"en": "Writer preference: thousands of writes", "fa": "ترجیح نویسنده: هزاران نوشتن"},
                {"en": "readers queue behind a waiting writer", "fa": "خواننده‌ها پشت نویسندهٔ منتظر صف می‌کشند"},
            ),
            (
                {"en": "Starvation is not deadlock", "fa": "گرسنگی deadlock نیست"},
                {"en": "readers progress; only the writer does not", "fa": "خواننده‌ها پیش می‌روند؛ فقط نویسنده نه"},
            ),
        ],
        pitfalls=[
            (
                {"en": "PREFER_WRITER_NP changes nothing", "fa": "PREFER_WRITER_NP اثری ندارد"},
                same("use PREFER_WRITER_NONRECURSIVE_NP"),
            ),
            (
                {"en": "no starvation visible", "fa": "گرسنگی دیده نمی‌شود"},
                {
                    "en": "readers must overlap: ≥2 readers, no gaps",
                    "fa": "خواننده‌ها باید هم‌پوشان باشند: دست‌کم ۲ و بدون فاصله",
                },
            ),
            (
                {"en": "writer-pref deadlock", "fa": "deadlock با ترجیح نویسنده"},
                {"en": "recursive read lock while a writer waits", "fa": "قفل خواندن بازگشتی وقتی نویسنده منتظر است"},
            ),
        ],
        ext={
            "en": "Build a starvation-free rwlock from three semaphores (a turnstile held by a waiting writer) and compare it with both glibc kinds.",
            "fa": "یک rwlock بدون گرسنگی با سه semaphore بسازید (turnstileی که نویسندهٔ منتظر نگه می‌دارد) و با هر دو گونهٔ glibc مقایسه کنید.",
        },
        captured=CAP,
    ),
    dict(
        slug="04-futex-mutex",
        num="03.4",
        title={"en": "A mutex on raw futex()", "fa": "یک mutex روی futex() خام"},
        goal={
            "en": "Build Drepper's three-state futex mutex and prove with strace and bpftrace that only contention enters the kernel.",
            "fa": "mutex سه‌حالته‌ی Drepper را روی futex بسازید و با strace و bpftrace ثابت کنید فقط رقابت وارد کرنل می‌شود.",
        },
        where={"en": "aos-lab VM (bpftrace needs root)", "fa": "VM با نام aos-lab (bpftrace به root نیاز دارد)"},
        setup_cards=[
            ("r-data", {"en": "State word", "fa": "کلمهٔ حالت"}, same("0 free · 1 held · 2 held+waiters")),
            ("r-user", {"en": "Fast path", "fa": "مسیر سریع"}, same("cmpxchg 0→1 / fetch_sub 1→0")),
            ("r-kernel", {"en": "Slow path", "fa": "مسیر کند"}, same("FUTEX_WAIT_PRIVATE / FUTEX_WAKE_PRIVATE")),
            ("r-kernel", {"en": "Tracing", "fa": "ردیابی"}, same("strace -c · bpftrace sys_enter_futex")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -pthread futex_mutex.c -o futex_mutex",
            "$ ./futex_mutex 1 1000000",
            "$ ./futex_mutex 4 1000000",
            "$ strace -f -c -e trace=futex ./futex_mutex 1 1000000",
            "$ strace -f -c -e trace=futex ./futex_mutex 4 200000",
            "$ sudo bpftrace futex-ops.bt -c './futex_mutex 4 200000'",
        ],
        expected=[
            "$ ./futex_mutex 1 1000000",
            "!threads=1 ... OK futex_wait=0 futex_wake=0",
            "$ ./futex_mutex 4 1000000",
            "threads=4 ... OK futex_wait=37928 futex_wake=48919",
            "$ sudo bpftrace futex-ops.bt -c './futex_mutex 4 200000'",
            "@calls[9]: 3",
            "!@calls[0]: 6680",
            "@calls[1]: 8949",
            "@usecs[0]:",
            "![0]                 6559 |@@@@@@@@@@@@@@@@@@@@...",
            "[64, 128)             32 |",
        ],
        observe=[
            (
                {"en": "1 thread: zero futex calls", "fa": "۱ نخ: صفر فراخوانی futex"},
                {"en": "every lock/unlock stayed in user space", "fa": "همهٔ گرفتن و آزادکردن‌ها در فضای کاربر ماند"},
            ),
            (
                {"en": "WAIT errors = EAGAIN", "fa": "خطاهای WAIT همان EAGAIN است"},
                {"en": "value changed before the kernel checked it", "fa": "مقدار پیش از بررسی کرنل عوض شده بود"},
            ),
            (
                {"en": "op 0 = WAIT, op 1 = WAKE", "fa": "op 0 یعنی WAIT و op 1 یعنی WAKE"},
                same("op & 127 strips FUTEX_PRIVATE_FLAG"),
            ),
        ],
        pitfalls=[
            (
                {"en": "hangs under contention", "fa": "با رقابت گیر می‌کند"},
                {"en": "unlock must wake when old value was 2", "fa": "آزادکردن باید وقتی مقدار قبلی ۲ بود بیدار کند"},
            ),
            (
                {"en": "strace changes the result", "fa": "strace نتیجه را تغییر می‌دهد"},
                {
                    "en": "tracing slows threads; compare with the program's own counters",
                    "fa": "ردیابی نخ‌ها را کند می‌کند؛ با شمارنده‌های خود برنامه مقایسه کنید",
                },
            ),
            (
                {"en": "more WAKE than WAIT", "fa": "WAKE بیشتر از WAIT"},
                {"en": "state 2 is sticky: expected", "fa": "حالت ۲ چسبنده است: طبیعی است"},
            ),
        ],
        ext={
            "en": "Spin a bounded number of times before FUTEX_WAIT (user-space optimistic spinning). Measure futex calls and time for spin = 0, 100, 1000.",
            "fa": "پیش از FUTEX_WAIT تعداد محدودی بچرخید (optimistic spinning در فضای کاربر). تعداد فراخوانی futex و زمان را برای spin برابر ۰، ۱۰۰ و ۱۰۰۰ بسنجید.",
        },
        captured=CAP,
    ),
    dict(
        slug="05-litmus-sb",
        num="03.5",
        title={
            "en": "Store-buffering litmus test, C11 and Rust",
            "fa": "آزمون litmus از نوع store-buffering در C11 و Rust",
        },
        goal={
            "en": "Count how often x86 shows r0 = r1 = 0 in a million runs, then make it vanish with a full fence.",
            "fa": "بشمارید x86 در یک میلیون اجرا چند بار r0 = r1 = 0 نشان می‌دهد، بعد با یک fence کامل حذفش کنید.",
        },
        where={
            "en": "aos-lab VM, 2 pinned CPUs · ARCH-SPECIFIC x86-64",
            "fa": "VM با نام aos-lab، ۲ CPU ثابت · ARCH-SPECIFIC x86-64",
        },
        setup_cards=[
            ("r-user", {"en": "Test", "fa": "آزمون"}, same("x=1; r0=y  ||  y=1; r1=x")),
            (
                "r-hardware",
                {"en": "Cause", "fa": "علت"},
                {"en": "per-core store buffer (x86-TSO)", "fa": "store buffer هر هسته (x86-TSO)"},
            ),
            ("r-kernel", {"en": "Modes", "fa": "حالت‌ها"}, same("relaxed · fence · seqcst")),
            ("r-data", {"en": "Two languages", "fa": "دو زبان"}, same("sb.c (C11) · sb.rs (Rust std)")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -pthread sb.c -o sb",
            "$ rustc -O sb.rs -o sb_rs",
            "$ ./sb relaxed 1000000 0 1",
            "$ ./sb fence 1000000 0 1",
            "$ ./sb_rs relaxed 1000000",
            "$ objdump -d sb | grep -E 'mfence|lock|xchg'",
        ],
        expected=[
            "$ ./sb relaxed 1000000 0 1",
            "!  r0=0 r1=0 :     35320  (3.5320%)  <- forbidden under SC",
            "$ ./sb fence 1000000 0 1",
            "!  r0=0 r1=0 :         0  (0.0000%)  <- forbidden under SC",
            "$ ./sb_rs relaxed 1000000",
            "  r0=0 r1=0 :     17318  (1.7318%)  <- forbidden under SC",
            "$ ./sb_rs fence 1000000",
            "  r0=0 r1=0 :         0  (0.0000%)  <- forbidden under SC",
            "$ objdump -d sb | grep -E 'mfence|lock|xchg'",
            "    1733:  xchg   %eax,(%rsi)",
            "!    1746:  lock orq $0x0,(%rsp)",
        ],
        observe=[
            (
                {"en": "0/0 appears only in relaxed", "fa": "0/0 فقط در relaxed دیده می‌شود"},
                {
                    "en": "the store waited in the buffer while the load ran",
                    "fa": "store در بافر ماند در حالی که load اجرا شد",
                },
            ),
            (
                {"en": "The fence is a locked no-op", "fa": "fence یک دستور بی‌اثرِ lockدار است"},
                same("lock orq $0x0,(%rsp)"),
            ),
            (
                {"en": "Rust shows the same", "fa": "Rust هم همین را نشان می‌دهد"},
                {"en": "same hardware, same memory model (C++20)", "fa": "همان سخت‌افزار، همان مدل حافظه (C++20)"},
            ),
        ],
        pitfalls=[
            (
                {"en": "relaxed shows 0", "fa": "relaxed صفر نشان می‌دهد"},
                {
                    "en": "both threads on one CPU: check nproc / pinning",
                    "fa": "هر دو نخ روی یک CPU: nproc و pinning را بررسی کنید",
                },
            ),
            (
                {"en": "looking for mfence", "fa": "دنبال mfence گشتن"},
                {
                    "en": "gcc emits lock or: also a full barrier",
                    "fa": "gcc دستور lock or می‌دهد: آن هم barrier کامل است",
                },
            ),
            (
                {"en": "counts vary", "fa": "تعدادها تغییر می‌کنند"},
                {
                    "en": "timing-dependent: compare orders of magnitude",
                    "fa": "وابسته به زمان‌بندی: مرتبهٔ بزرگی را مقایسه کنید",
                },
            ),
        ],
        ext={
            "en": "Write the message-passing test (data=1; flag=1 || r0=flag; r1=data) with relaxed atomics. Does x86 ever show flag=1, data=0? Why, and what about Arm64?",
            "fa": "آزمون message-passing را بنویسید (data=1; flag=1 || r0=flag; r1=data) با atomicهای relaxed. آیا x86 هرگز flag=1 و data=0 نشان می‌دهد؟ چرا، و روی Arm64 چه؟",
        },
        captured=CAP,
    ),
    dict(
        slug="06-deadlock",
        num="03.6",
        title={"en": "Deadlock: create, read, detect", "fa": "Deadlock: ساختن، خواندن، تشخیص"},
        goal={
            "en": "Create an AB-BA deadlock, read it from gdb and /proc, detect the inverted order with TSan and helgrind, fix it with address ordering.",
            "fa": "یک deadlock از نوع AB-BA بسازید، آن را از gdb و /proc بخوانید، ترتیب وارونه را با TSan و helgrind تشخیص دهید و با ترتیب آدرس درستش کنید.",
        },
        where={
            "en": "aos-lab VM; lockdep part: VM with --lockdep kernel only",
            "fa": "VM با نام aos-lab؛ بخش lockdep فقط روی VM با کرنل --lockdep",
        },
        setup_cards=[
            ("r-user", {"en": "Program", "fa": "برنامه"}, same("deadlock.c: hang | quick | ordered")),
            ("r-kernel", {"en": "Thread dump", "fa": "thread dump"}, same("gdb -p · /proc/PID/task/*/stack")),
            ("r-data", {"en": "Order checkers", "fa": "بررسی‌کنندهٔ ترتیب"}, same("TSan · helgrind · lockdep")),
            (
                "r-hardware",
                {"en": "Kernel module", "fa": "ماژول کرنل"},
                {"en": "lockdep_abba.ko: VM + PROVE_LOCKING only", "fa": "lockdep_abba.ko: فقط VM با PROVE_LOCKING"},
            ),
        ],
        steps=[
            "$ ./deadlock hang &  P=$!; sleep 1",
            "$ ps -L -o pid,lwp,stat,wchan:20,comm -p $P",
            "$ sudo cat /proc/$P/task/*/stack",
            "$ sudo gdb -p $P -batch -ex 'thread apply all bt'",
            "$ kill -9 $P",
            "$ ./deadlock-tsan quick",
            "$ valgrind --tool=helgrind ./deadlock quick",
            "$ ./deadlock ordered",
        ],
        expected=[
            "$ ps -L -o pid,lwp,stat,wchan:20,comm -p $P",
            "!  27823   27826 Sl   futex_do_wait        deadlock",
            "  27823   27827 Sl   futex_do_wait        deadlock",
            "#0 futex_wait (... futex_word=0x...020 <g_acc_b>)",
            "#4 ... in transfer (from=...<g_acc_a>, to=...<g_acc_b>, ...) at deadlock.c:39",
            "#0 futex_wait (... futex_word=0x...060 <g_acc_a>)",
            "#4 ... in transfer (from=...<g_acc_b>, to=...<g_acc_a>, ...) at deadlock.c:39",
            "$ setarch x86_64 -R ./deadlock-tsan quick",
            "!WARNING: ThreadSanitizer: lock-order-inversion (potential deadlock)",
            "  Cycle in lock order graph: M0 => M1 => M0",
            "$ valgrind --tool=helgrind ./deadlock quick",
            '!Thread #3: lock order "0x10C060 before 0x10C020" violated',
        ],
        observe=[
            (
                {"en": "Both threads sleep in futex_wait", "fa": "هر دو نخ در futex_wait خوابیده‌اند"},
                {"en": "state S, 0% CPU: a deadlock does not spin", "fa": "وضعیت S و ۰٪ CPU: deadlock نمی‌چرخد"},
            ),
            (
                {"en": "TSan reports without a hang", "fa": "TSan بدون گیرکردن گزارش می‌دهد"},
                same("lock-order-inversion (potential deadlock)"),
            ),
            (
                {"en": "Lockdep: same idea in the kernel", "fa": "lockdep: همین ایده در کرنل"},
                {
                    "en": "report UNVERIFIED: VM kernel lacks PROVE_LOCKING",
                    "fa": "گزارش UNVERIFIED: کرنل VM فاقد PROVE_LOCKING است",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "gdb: ptrace not permitted", "fa": "gdb: ptrace not permitted"},
                same("sudo gdb -p (Yama ptrace_scope=1)"),
            ),
            (
                {"en": "quick mode works", "fa": "حالت quick کار می‌کند"},
                {"en": "order still inverted; timing hid it", "fa": "ترتیب هنوز وارونه است؛ زمان‌بندی پنهانش کرد"},
            ),
            ({"en": "lockdep silent", "fa": "lockdep ساکت است"}, same("grep PROVE_LOCKING /boot/config-$(uname -r)")),
        ],
        ext={
            "en": "Dining Philosophers: make 5 philosophers deadlock, then fix it two ways (fork ordering; at most 4 seated via a semaphore) and run each 10 s TSan-clean.",
            "fa": "فیلسوف‌های غذاخور: ۵ فیلسوف را به deadlock برسانید، بعد به دو روش درستش کنید (ترتیب چنگال‌ها؛ حداکثر ۴ نفر نشسته با semaphore) و هر کدام را ۱۰ ثانیه بدون هشدار TSan اجرا کنید.",
        },
        captured=CAP,
    ),
]
