// Guided mini-labs for the browser lab (32-bit Linux 6.8.12 on v86). One source of truth, used by the page
// (lab.js) and by the headless self-test. Every command is one line, runs in busybox sh, and needs no compiler.
// `expect` is a regex that the output must match; it is how we know each step really works.
//
// Kernel links point at the course's pinned source (Linux v6.18.63); the guest runs 6.8.12, so details can differ a little.

export const KERNEL_TAG = "v6.18.63";
export const elixir = (path) => `https://elixir.bootlin.com/linux/${KERNEL_TAG}/source/${path}`;

export const LABS = [
  {
    id: "kernel", module: "01",
    title: { en: "Meet the kernel", fa: "آشنایی با کرنل" },
    intro: {
      en: "You are talking to a real Linux kernel that is booted inside your browser. Ask it who it is, and read its own symbol table.",
      fa: "شما با یک کرنل واقعی Linux حرف می‌زنید که داخل مرورگر شما boot شده است. از آن بپرسید کیست و جدول symbolهای خودش را بخوانید.",
    },
    steps: [
      { cmd: "uname -a", expect: "Linux .* 6\\.8\\.12 .* i686",
        en: "Kernel version and CPU architecture. Note i686: this is a 32-bit kernel.",
        fa: "نسخهٔ کرنل و معماری CPU. به i686 دقت کنید: این یک کرنل ۳۲ بیتی است." },
      { cmd: "cat /proc/cmdline", expect: "tsc=reliable",
        en: "The command line the boot loader gave to the kernel.",
        fa: "command lineای که boot loader به کرنل داده است." },
      { cmd: "head -3 /proc/kallsyms", expect: "startup_32",
        en: "The first kernel symbols with their addresses. startup_32 is where the kernel starts running.",
        fa: "اولین symbolهای کرنل و آدرس‌هایشان. startup_32 جایی است که اجرای کرنل شروع می‌شود." },
      { cmd: "wc -l < /proc/kallsyms", expect: "\\d{4,}",
        en: "How many symbols the kernel knows about.",
        fa: "کرنل چند symbol می‌شناسد." },
      { cmd: "dmesg | head -6", expect: "Linux version",
        en: "The kernel's own boot log (its ring buffer).",
        fa: "لاگ boot خود کرنل (ring buffer آن)." },
    ],
    ask: {
      en: "The first symbol has an address like c1000000. Why does a kernel address start with c?",
      fa: "آدرس اولین symbol چیزی شبیه c1000000 است. چرا آدرس کرنل با c شروع می‌شود؟",
    },
    answer: {
      en: "On 32-bit x86 the default split is 3 GB user / 1 GB kernel: the kernel lives at and above 0xC0000000 (__PAGE_OFFSET). The extra 0x01000000 is the 16 MB physical address the kernel was loaded at. On x86-64 (the course VM) the kernel is in the top half of a 48-bit address space instead.",
      fa: "در x86 ۳۲ بیتی تقسیم پیش‌فرض ۳ گیگابایت user و ۱ گیگابایت kernel است: کرنل از 0xC0000000 (همان __PAGE_OFFSET) به بالا قرار دارد. مقدار اضافهٔ 0x01000000 همان آدرس فیزیکی ۱۶ مگابایتی است که کرنل در آن load شده. در x86-64 (ماشین مجازی درس) کرنل در نیمهٔ بالایی فضای آدرس ۴۸ بیتی است.",
    },
    source: [
      { path: "arch/x86/kernel/head_32.S", en: "startup_32: the first code that runs", fa: "startup_32: اولین کدی که اجرا می‌شود" },
      { path: "arch/x86/include/asm/page_32_types.h", en: "__PAGE_OFFSET", fa: "__PAGE_OFFSET" },
      { path: "kernel/kallsyms.c", en: "how /proc/kallsyms is produced", fa: "نحوهٔ ساخته‌شدن /proc/kallsyms" },
    ],
    real: { en: "Course Module 01 and Lab 01.x (on the real x86-64 VM).", fa: "ماژول ۰۱ و آزمایش 01.x درس (روی ماشین مجازی واقعی x86-64)." },
  },
  {
    id: "interrupts", module: "01",
    title: { en: "Interrupts", fa: "Interruptها" },
    intro: {
      en: "Hardware pokes the kernel with interrupts. /proc/interrupts counts them per line.",
      fa: "سخت‌افزار با interrupt کرنل را صدا می‌زند. /proc/interrupts تعداد آن‌ها را برای هر خط نشان می‌دهد.",
    },
    steps: [
      { cmd: "cat /proc/interrupts", expect: "timer",
        en: "One row per interrupt line. Find timer and ttyS0.",
        fa: "هر ردیف یک خط interrupt است. timer و ttyS0 را پیدا کنید." },
      { cmd: "a=$(awk '/timer/{print $2}' /proc/interrupts); sleep 5; b=$(awk '/timer/{print $2}' /proc/interrupts); echo \"timer interrupts in 5 s: $((b-a))\"",
        expect: "timer interrupts in 5 s: \\d+",
        en: "Count the timer ticks over 5 seconds, so you can estimate the tick rate.",
        fa: "تعداد tickهای timer را در ۵ ثانیه بشمارید تا نرخ tick را تخمین بزنید." },
      { cmd: "cat /proc/softirqs | head -4", expect: "HI|TIMER|NET_TX",
        en: "Softirqs: the deferred half of interrupt work.",
        fa: "Softirqها: نیمهٔ به‌تعویق‌افتادهٔ کار interrupt." },
    ],
    ask: {
      en: "Type a few characters, then run cat /proc/interrupts again. Which counter grew, and why that one?",
      fa: "چند کاراکتر تایپ کنید و دوباره cat /proc/interrupts را اجرا کنید. کدام شمارنده بالا رفت و چرا آن؟",
    },
    answer: {
      en: "ttyS0 grew: your keystrokes reach this machine through its emulated serial port, and each byte raises an interrupt. In a normal PC the keyboard (i8042) would grow instead.",
      fa: "ttyS0 بالا رفت: کلیدهایی که می‌زنید از طریق پورت serial شبیه‌سازی‌شده به این ماشین می‌رسند و هر بایت یک interrupt ایجاد می‌کند. در یک PC معمولی به‌جای آن کیبورد (i8042) بالا می‌رفت.",
    },
    source: [
      { path: "kernel/irq/handle.c", en: "handle_irq_event: running the handlers", fa: "handle_irq_event: اجرای handlerها" },
      { path: "fs/proc/interrupts.c", en: "the code behind /proc/interrupts", fa: "کد پشت /proc/interrupts" },
    ],
    real: { en: "Course Module 01, Lab 01.3 (interrupts and tracepoints).", fa: "ماژول ۰۱، آزمایش 01.3 (interruptها و tracepointها)." },
  },
  {
    id: "processes", module: "02",
    title: { en: "Processes, fork and pipes", fa: "Process، fork و pipe" },
    intro: {
      en: "Every command is a process. The shell creates them with fork and exec, and pipes connect them.",
      fa: "هر دستور یک process است. shell آن‌ها را با fork و exec می‌سازد و pipeها آن‌ها را به هم وصل می‌کنند.",
    },
    steps: [
      { cmd: "echo \"shell pid=$$\"; sh -c 'echo \"child pid=$$ parent=$PPID\"'", expect: "child pid=\\d+ parent=\\d+",
        en: "The child has a new pid, and its parent is your shell.",
        fa: "child یک pid جدید دارد و parent آن shell شماست." },
      { cmd: "sleep 300 & echo \"started pid $!\"", expect: "started pid \\d+",
        en: "Start a background process that just sleeps.",
        fa: "یک process پس‌زمینه بسازید که فقط می‌خوابد." },
      { cmd: "grep -E 'Name|State|PPid|Threads' /proc/$!/status", expect: "State:\\s+S \\(sleeping\\)",
        en: "The kernel's view of that process: sleeping, with your shell as its parent.",
        fa: "دید کرنل از آن process: در حال خواب، و parent آن همان shell شماست." },
      { cmd: "ps | head -8", expect: "PID",
        en: "All processes. Look for the sleep.",
        fa: "همهٔ processها. sleep را پیدا کنید." },
      { cmd: "echo hello | cat | tr a-z A-Z", expect: "HELLO",
        en: "Three processes, two pipes, started at once.",
        fa: "سه process و دو pipe که هم‌زمان ساخته می‌شوند." },
      { cmd: "kill $!; sleep 1; echo cleaned up", expect: "cleaned up",
        en: "Stop the sleeper.",
        fa: "process خواب را متوقف کنید." },
    ],
    ask: {
      en: "In step 1, why does the child print a different pid but the same parent as your shell's pid?",
      fa: "در گام ۱ چرا child یک pid متفاوت چاپ می‌کند ولی parent آن برابر pid خود shell است؟",
    },
    answer: {
      en: "fork duplicates the calling process: the copy gets a new pid and keeps the original as its parent (PPid). exec then replaces the copy's program, which is how sh -c runs a new command.",
      fa: "fork process فراخواننده را کپی می‌کند: کپی یک pid جدید می‌گیرد و process اصلی parent آن (PPid) می‌ماند. سپس exec برنامهٔ کپی را عوض می‌کند و به همین شکل sh -c دستور جدید را اجرا می‌کند.",
    },
    source: [
      { path: "kernel/fork.c", en: "kernel_clone: what fork and clone call", fa: "kernel_clone: چیزی که fork و clone صدا می‌زنند" },
      { path: "fs/exec.c", en: "execve: replace the program", fa: "execve: جایگزینی برنامه" },
      { path: "fs/proc/array.c", en: "the State: line of /proc/PID/status", fa: "خط State: در /proc/PID/status" },
    ],
    real: { en: "Course Module 02, Lab 02.1 (fork, exec, pipe).", fa: "ماژول ۰۲، آزمایش 02.1 (fork، exec و pipe)." },
  },
  {
    id: "scheduling", module: "02",
    title: { en: "Scheduling and nice", fa: "زمان‌بندی (scheduling) و nice" },
    intro: {
      en: "Two programs fight for one CPU. The scheduler decides who runs, and nice changes the odds.",
      fa: "دو برنامه برای یک CPU رقابت می‌کنند. scheduler تصمیم می‌گیرد چه کسی اجرا شود و nice شانس‌ها را تغییر می‌دهد.",
    },
    steps: [
      { cmd: "chrt -p $$", expect: "SCHED_OTHER",
        en: "Your shell uses the normal time-sharing policy (SCHED_OTHER).",
        fa: "shell شما از سیاست معمولی time-sharing (یعنی SCHED_OTHER) استفاده می‌کند." },
      { cmd: "nice -n 19 sh -c 'while :; do :; done' & p1=$!; sh -c 'while :; do :; done' & p2=$!; sleep 10; top -b -n 1 | head -12; kill $p1 $p2",
        expect: "sh -c while", timeout: 60000,
        en: "Two busy loops, one with nice 19 (polite) and one normal. Wait 10 seconds, then read their CPU use from top.",
        fa: "دو busy loop، یکی با nice 19 (مؤدب) و یکی عادی. ۱۰ ثانیه صبر کنید و مصرف CPU آن‌ها را در top بخوانید." },
    ],
    ask: {
      en: "Which loop got more CPU in top, and by how much? What does that say about nice?",
      fa: "در top کدام حلقه CPU بیشتری گرفت و چقدر؟ این دربارهٔ nice چه می‌گوید؟",
    },
    answer: {
      en: "The normal loop gets almost all of the CPU; the nice-19 loop gets a small share. nice does not forbid running, it changes the weight the scheduler uses (Linux 6.6+ uses EEVDF for the normal class).",
      fa: "حلقهٔ عادی تقریباً همهٔ CPU را می‌گیرد و حلقهٔ nice-19 سهم کوچکی دارد. nice اجرا را ممنوع نمی‌کند، فقط وزنی را که scheduler استفاده می‌کند تغییر می‌دهد (Linux از نسخهٔ 6.6 برای کلاس عادی از EEVDF استفاده می‌کند).",
    },
    source: [
      { path: "kernel/sched/fair.c", en: "the fair (normal) scheduling class", fa: "کلاس scheduling عادی (fair)" },
      { path: "kernel/sched/core.c", en: "__schedule: pick the next task", fa: "__schedule: انتخاب task بعدی" },
    ],
    real: { en: "Course Module 02, Lab 02.5 (nice, SCHED_FIFO and EEVDF slices).", fa: "ماژول ۰۲، آزمایش 02.5 (nice، SCHED_FIFO و sliceهای EEVDF)." },
  },
  {
    id: "switches", module: "02",
    title: { en: "Context switches", fa: "Context switch" },
    intro: {
      en: "Every time the CPU moves from one process to another, the kernel does a context switch. Make some happen and count them.",
      fa: "هر بار که CPU از یک process به process دیگر می‌رود، کرنل یک context switch انجام می‌دهد. چند تا بسازید و بشمارید.",
    },
    steps: [
      { cmd: "grep ctxt /proc/self/status", expect: "voluntary_ctxt_switches",
        en: "Per-process counters: voluntary (it waited) and non-voluntary (it was preempted).",
        fa: "شمارنده‌های هر process: voluntary (خودش منتظر ماند) و non-voluntary (قطع شد)." },
      { cmd: "grep '^ctxt' /proc/stat", expect: "ctxt \\d+",
        en: "The whole machine's total since boot.",
        fa: "مجموع کل ماشین از زمان boot." },
      { cmd: "a=$(awk '/^ctxt/{print $2}' /proc/stat); yes | head -n 400000 | wc -l; b=$(awk '/^ctxt/{print $2}' /proc/stat); echo \"context switches caused: $((b-a))\"",
        expect: "context switches caused: \\d{3,}", timeout: 90000,
        en: "Push 400,000 lines (800 KB) through a pipe and count the switches it caused. A smaller amount would fit in the pipe's 64 KB buffer and barely switch at all.",
        fa: "۴۰۰٬۰۰۰ خط (۸۰۰ کیلوبایت) را از یک pipe رد کنید و تعداد switchهایی را که ایجاد شد بشمارید. مقدار کمتر در بافر ۶۴ کیلوبایتی pipe جا می‌شد و تقریباً switchی ایجاد نمی‌کرد." },
    ],
    ask: {
      en: "Why does moving data through a pipe cause context switches?",
      fa: "چرا عبور داده از یک pipe باعث context switch می‌شود؟",
    },
    answer: {
      en: "A pipe has a small buffer. When it is full the writer must sleep until the reader drains it, and when it is empty the reader sleeps until the writer fills it. Each sleep is a voluntary switch.",
      fa: "pipe بافر کوچکی دارد. وقتی پر است writer باید بخوابد تا reader آن را خالی کند و وقتی خالی است reader می‌خوابد تا writer پرش کند. هر خواب یک voluntary switch است.",
    },
    source: [
      { path: "kernel/sched/core.c", en: "context_switch: switch address space and registers", fa: "context_switch: عوض‌کردن address space و registerها" },
      { path: "fs/pipe.c", en: "pipe_read and pipe_write sleep here", fa: "pipe_read و pipe_write اینجا می‌خوابند" },
      { path: "fs/proc/stat.c", en: "the ctxt line", fa: "خط ctxt" },
    ],
    real: { en: "Course Module 02, Lab 02.3 (context-switch cost, pipe ping-pong).", fa: "ماژول ۰۲، آزمایش 02.3 (هزینهٔ context switch، pipe ping-pong)." },
  },
  {
    id: "signals", module: "02",
    title: { en: "Signals", fa: "Signalها" },
    intro: {
      en: "Signals are the kernel's way to interrupt a process. Catch one, then freeze and thaw another.",
      fa: "Signalها راه کرنل برای قطع‌کردن یک process هستند. یکی را بگیرید، سپس process دیگری را متوقف کنید و ادامه دهید.",
    },
    steps: [
      { cmd: "trap 'echo \"caught SIGUSR1 in pid $$\"' USR1; kill -USR1 $$", expect: "caught SIGUSR1 in pid \\d+",
        en: "Install a handler, then send the signal to yourself.",
        fa: "یک handler نصب کنید و سپس signal را به خودتان بفرستید." },
      { cmd: "sleep 100 & p=$!; kill -STOP $p; sleep 1; grep State /proc/$p/status; kill -CONT $p; sleep 1; grep State /proc/$p/status; kill $p",
        expect: "State:\\s+T \\(stopped\\)[\\s\\S]*State:\\s+S \\(sleeping\\)",
        en: "Freeze a process with SIGSTOP (state T), thaw it with SIGCONT (state S), then end it.",
        fa: "یک process را با SIGSTOP متوقف کنید (حالت T)، با SIGCONT ادامه دهید (حالت S) و سپس تمامش کنید." },
    ],
    ask: {
      en: "Can the sleeping process ignore SIGSTOP? Try: sleep 100 & kill -KILL $!",
      fa: "آیا process خوابیده می‌تواند SIGSTOP را نادیده بگیرد؟ امتحان کنید: sleep 100 & kill -KILL $!",
    },
    answer: {
      en: "No. SIGSTOP and SIGKILL cannot be caught, blocked or ignored; the kernel acts on them directly. That is why kill -9 always works (except for processes stuck in uninterruptible sleep).",
      fa: "نه. SIGSTOP و SIGKILL را نمی‌شود گرفت، مسدود یا نادیده کرد؛ کرنل مستقیم روی آن‌ها عمل می‌کند. به همین دلیل kill -9 همیشه کار می‌کند (به‌جز processهایی که در uninterruptible sleep گیر کرده‌اند).",
    },
    source: [{ path: "kernel/signal.c", en: "signal delivery and the rules for SIGKILL and SIGSTOP", fa: "تحویل signal و قانون‌های SIGKILL و SIGSTOP" }],
    real: { en: "Course Module 02 (process states).", fa: "ماژول ۰۲ (حالت‌های process)." },
  },
  {
    id: "memory", module: "04",
    title: { en: "Virtual memory", fa: "حافظهٔ مجازی" },
    intro: {
      en: "Every process sees its own address space. The kernel shows you its layout in /proc/PID/maps.",
      fa: "هر process فضای آدرس مخصوص خودش را می‌بیند. کرنل چیدمان آن را در /proc/PID/maps نشان می‌دهد.",
    },
    steps: [
      { cmd: "free", expect: "Mem:",
        en: "Physical memory: total, used, free. This machine has about 100 MB.",
        fa: "حافظهٔ فیزیکی: کل، استفاده‌شده، آزاد. این ماشین حدود ۱۰۰ مگابایت دارد." },
      { cmd: "grep -E 'MemTotal|MemFree|Slab|Shmem' /proc/meminfo", expect: "MemTotal",
        en: "A few more counters from the kernel's memory accounting.",
        fa: "چند شمارندهٔ دیگر از accounting حافظهٔ کرنل." },
      { cmd: "cat /proc/self/maps", expect: "\\[stack\\]",
        en: "The address space of the cat command itself: program, libraries, heap, stack.",
        fa: "فضای آدرس خودِ دستور cat: برنامه، کتابخانه‌ها، heap و stack." },
      { cmd: "grep -E 'Rss|Pss|Size' /proc/self/smaps_rollup", expect: "Rss",
        en: "How much of that address space is really in RAM (Rss).",
        fa: "چه مقدار از آن فضای آدرس واقعاً در RAM است (Rss)." },
    ],
    ask: {
      en: "Look at the [stack] line. How high in the address space is it, and how does that relate to the 3 GB / 1 GB split from the first lab?",
      fa: "خط [stack] را ببینید. در چه آدرس بالایی قرار دارد و این به تقسیم ۳ گیگابایت / ۱ گیگابایت در آزمایش اول چه ربطی دارد؟",
    },
    answer: {
      en: "The stack sits near the top of the user part, just under 0xC0000000 (the exact spot is randomised by ASLR), and grows downward. Everything above 0xC0000000 belongs to the kernel and is not listed in a process's maps.",
      fa: "stack نزدیک بالای بخش user و درست زیر 0xC0000000 قرار دارد (جای دقیق آن با ASLR تصادفی می‌شود) و به سمت پایین رشد می‌کند. هرچه بالاتر از 0xC0000000 است مال کرنل است و در maps یک process فهرست نمی‌شود.",
    },
    source: [
      { path: "fs/proc/task_mmu.c", en: "the code that prints /proc/PID/maps", fa: "کدی که /proc/PID/maps را چاپ می‌کند" },
      { path: "mm/memory.c", en: "handle_mm_fault: page-fault handling", fa: "handle_mm_fault: رسیدگی به page fault" },
      { path: "fs/proc/meminfo.c", en: "the code behind /proc/meminfo", fa: "کد پشت /proc/meminfo" },
    ],
    real: { en: "Course Module 04, Labs 04.1 and 04.2 (page faults, copy-on-write).", fa: "ماژول ۰۴، آزمایش‌های 04.1 و 04.2 (page fault و copy-on-write)." },
  },
  {
    id: "tmpfs", module: "04",
    title: { en: "Files are pages (tmpfs)", fa: "فایل‌ها همان page هستند (tmpfs)" },
    intro: {
      en: "A tmpfs file lives entirely in RAM pages. Write one and watch free memory shrink and Shmem grow.",
      fa: "فایل در tmpfs کاملاً در pageهای RAM قرار دارد. یکی بنویسید و ببینید حافظهٔ آزاد کم و Shmem زیاد می‌شود.",
    },
    steps: [
      { cmd: "mkdir -p /tmp/t && mount -t tmpfs none /tmp/t && grep -E 'MemFree|Shmem:' /proc/meminfo", expect: "MemFree",
        en: "Mount a fresh tmpfs and note MemFree and Shmem.",
        fa: "یک tmpfs تازه mount کنید و MemFree و Shmem را یادداشت کنید." },
      { cmd: "a=$(awk '/^pgfault/{print $2}' /proc/vmstat); dd if=/dev/zero of=/tmp/t/big bs=1M count=20 2>/dev/null; b=$(awk '/^pgfault/{print $2}' /proc/vmstat); echo \"page faults while writing 20 MB: $((b-a))\"; grep -E 'MemFree|Shmem:' /proc/meminfo",
        expect: "page faults while writing 20 MB: \\d+[\\s\\S]*Shmem", timeout: 60000,
        en: "Write 20 MB into the tmpfs. MemFree drops by about 20 MB and Shmem grows by about the same. Also note how few page faults happened.",
        fa: "۲۰ مگابایت در tmpfs بنویسید. MemFree حدود ۲۰ مگابایت کم و Shmem تقریباً به همان اندازه زیاد می‌شود. به تعداد کم page faultها هم دقت کنید." },
      { cmd: "rm /tmp/t/big; grep -E 'MemFree|Shmem:' /proc/meminfo; umount /tmp/t", expect: "Shmem:\\s+\\d+ kB",
        en: "Delete the file: Shmem drops back to where it started, because the file's pages are freed.",
        fa: "فایل را پاک کنید: Shmem به مقدار اولش برمی‌گردد چون pageهای فایل آزاد می‌شوند." },
    ],
    ask: {
      en: "Why did MemFree fall by about 20 MB, and why were there only a few hundred page faults for roughly 5,000 new 4 KB pages?",
      fa: "چرا MemFree حدود ۲۰ مگابایت کم شد و چرا برای حدود ۵٬۰۰۰ page جدید ۴ کیلوبایتی فقط چند صد page fault رخ داد؟",
    },
    answer: {
      en: "A tmpfs file's data is its page-cache pages and nothing else (no disk copy), so 20 MB of data costs 20 MB of RAM. The pages were not created by page faults: dd calls write(), and the kernel allocates the pages itself while copying. The few hundred faults are dd's own. A fault happens when a process touches a page it has mapped but that is not there yet (for example after mmap).",
      fa: "داده‌ی فایل tmpfs همان pageهای page cache است و هیچ نسخهٔ دیسکی ندارد؛ پس ۲۰ مگابایت داده ۲۰ مگابایت RAM مصرف می‌کند. این pageها با page fault ساخته نشدند: dd تابع write() را صدا می‌زند و خودِ کرنل هنگام کپی، pageها را می‌گیرد. چند صد faultی که دیدید مال خود dd است. fault وقتی رخ می‌دهد که یک process به pageای که map کرده ولی هنوز وجود ندارد دست بزند (مثلاً بعد از mmap).",
    },
    source: [
      { path: "mm/shmem.c", en: "the tmpfs implementation", fa: "پیاده‌سازی tmpfs" },
      { path: "mm/vmstat.c", en: "the counters in /proc/vmstat", fa: "شمارنده‌های /proc/vmstat" },
    ],
    real: { en: "Course Module 04 (page faults) and Module 05 (page cache).", fa: "ماژول ۰۴ (page fault) و ماژول ۰۵ (page cache)." },
  },
  {
    id: "files", module: "05",
    title: { en: "Files, inodes and descriptors", fa: "فایل، inode و descriptor" },
    intro: {
      en: "A name is not the file. See hard links share an inode, and see what a file descriptor really points to.",
      fa: "نام فایل خودِ فایل نیست. ببینید hard linkها یک inode را به اشتراک می‌گذارند و ببینید file descriptor واقعاً به چه چیزی اشاره می‌کند.",
    },
    steps: [
      { cmd: "(cd /tmp && echo data > a && ln a b && ln -s a c && ls -li --color=never a b c)", expect: "-rw-r--r--\\s+2[\\s\\S]*-rw-r--r--\\s+2[\\s\\S]*c -> a",
        en: "In /tmp, a and b show the same inode number: two names, one file (link count 2). c is a symlink with its own inode.",
        fa: "در /tmp، فایل‌های a و b شمارهٔ inode یکسان دارند: دو نام، یک فایل (link count برابر ۲). c یک symlink با inode مخصوص خودش است." },
      { cmd: "cat /proc/filesystems | tr '\\n' ' '", expect: "ext4",
        en: "Filesystem types this kernel knows. nodev ones are virtual (proc, tmpfs).",
        fa: "انواع filesystemای که این کرنل می‌شناسد. موارد nodev مجازی‌اند (مثل proc و tmpfs)." },
      { cmd: "sh -c 'ls -l /proc/$$/fd 2>/dev/null; true' | cat", expect: "1 -> pipe:",
        en: "The file descriptors of a child shell: 0 and 2 are your terminal, and fd 1 is a pipe because its output goes into | cat.",
        fa: "file descriptorهای یک shell فرزند: ‏0 و 2 همان ترمینال شما هستند و fd 1 یک pipe است چون خروجی‌اش به | cat می‌رود." },
      { cmd: "exec 3</proc/version; ls -l /proc/$$/fd; exec 3<&-", expect: "/proc/version",
        en: "Open a file on descriptor 3 in your own shell and see it listed, then close it.",
        fa: "در shell خودتان فایلی را روی descriptor شمارهٔ 3 باز کنید، ببینید لیست می‌شود و سپس ببندید." },
    ],
    ask: {
      en: "Delete the first name with rm /tmp/a. Can you still read the data through the other name? Check with cat /tmp/b.",
      fa: "نام اول را با rm /tmp/a پاک کنید. هنوز می‌توانید داده را از نام دیگر بخوانید؟ با cat /tmp/b بررسی کنید.",
    },
    answer: {
      en: "Yes. rm only removes one name (a directory entry) and lowers the link count; the inode and its data are freed when the last name and the last open descriptor are gone.",
      fa: "بله. rm فقط یک نام (یک directory entry) را حذف و link count را کم می‌کند؛ inode و داده‌اش وقتی آزاد می‌شوند که آخرین نام و آخرین descriptor باز نیز از بین رفته باشند.",
    },
    source: [
      { path: "fs/namei.c", en: "path lookup, link, unlink", fa: "path lookup، link و unlink" },
      { path: "fs/open.c", en: "open and close", fa: "open و close" },
      { path: "fs/read_write.c", en: "read and write", fa: "read و write" },
    ],
    real: { en: "Course Module 05, Lab 05.1 (the full call chain of read()).", fa: "ماژول ۰۵، آزمایش 05.1 (زنجیرهٔ کامل فراخوانی read())." },
  },
  {
    id: "race", module: "03",
    title: { en: "A real race condition", fa: "یک race condition واقعی" },
    intro: {
      en: "Four shell loops add to the same counter file. Without a lock they overwrite each other; with flock they do not.",
      fa: "چهار حلقهٔ shell به یک فایل شمارنده اضافه می‌کنند. بدون lock روی کار هم می‌نویسند و با flock نه.",
    },
    steps: [
      { cmd: "echo 0 > /tmp/n; for p in 1 2 3 4; do (i=0; while [ $i -lt 40 ]; do v=$(cat /tmp/n); usleep 2000; echo $((v+1)) > /tmp/n; i=$((i+1)); done) & done; wait; echo \"expected 160, got $(cat /tmp/n)\"",
        expect: "expected 160, got (?!160\\b)\\d+", timeout: 60000,
        en: "No lock: each loop reads the counter, pauses a moment, then writes back its own value + 1. Wait for the result.",
        fa: "بدون lock: هر حلقه شمارنده را می‌خواند، کمی مکث می‌کند و سپس مقدار خودش + ۱ را برمی‌گرداند. منتظر نتیجه بمانید." },
      { cmd: "echo 0 > /tmp/n; for p in 1 2 3 4; do (i=0; while [ $i -lt 40 ]; do flock /tmp/n.lock sh -c 'v=$(cat /tmp/n); usleep 2000; echo $((v+1)) > /tmp/n'; i=$((i+1)); done) & done; wait; echo \"with flock: $(cat /tmp/n)\"",
        expect: "with flock: 160", timeout: 90000,
        en: "The same work, but the read-modify-write is inside flock. The result must be exactly 160.",
        fa: "همین کار، ولی read-modify-write داخل flock است. نتیجه باید دقیقاً ۱۶۰ باشد." },
    ],
    ask: {
      en: "Why was the first result less than 160? Which updates were lost?",
      fa: "چرا نتیجهٔ اول کمتر از ۱۶۰ بود؟ کدام به‌روزرسانی‌ها از بین رفتند؟",
    },
    answer: {
      en: "Two loops read the same value, both add 1, and both write the same number back: one increment is lost. This is a lost update, the classic race on a read-modify-write. flock lets only one loop run that section at a time.",
      fa: "دو حلقه مقدار یکسانی را می‌خوانند، هر دو ۱ اضافه می‌کنند و هر دو همان عدد را می‌نویسند: یک افزایش گم می‌شود. این lost update است، race کلاسیک روی read-modify-write. flock فقط به یک حلقه اجازه می‌دهد در هر لحظه آن بخش را اجرا کند.",
    },
    source: [{ path: "fs/locks.c", en: "flock is implemented here", fa: "flock اینجا پیاده‌سازی شده است" }],
    real: { en: "Course Module 03, Lab 03.1 (data race, TSan, mutex, atomic) on the real VM.", fa: "ماژول ۰۳، آزمایش 03.1 (data race، TSan، mutex، atomic) روی ماشین مجازی واقعی." },
  },
];
