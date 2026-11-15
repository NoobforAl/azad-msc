# Lab-deck content for 06-distributed-virtualization.
# Render: python _shared/tools/labdeck.py term-1/advanced-operating-systems/06-distributed-virtualization/slides/labs.content.py
COURSE = {"en": "Advanced OS · 06 Distributed & Virtualization", "fa": "سیستم‌عامل پیشرفته · ۰۶ توزیع‌شده و مجازی‌سازی"}

AOS_LAB = {
    "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15",
    "fa": "aos-lab (VirtualBox، Ubuntu 24.04، Linux 6.18.63)، 2026-11-15",
}

# Expected-output blocks: copied from the real runs pasted in each lab README ("!" = highlighted line).
EXP01 = [
    "$ bash run.sh",
    "events=28 messages=10  clock condition:",
    "!  lamport 10/10, vector 10/10",
    "total order (L, proc):",
    "  L=1   P1 LOCAL      V=[0 1 0]",
    "  L=1   P2 SEND  2-0  V=[0 0 1]",
    "  L=2   P0 RECV  2-0  V=[1 0 1]",
    "  ...",
    "concurrent but L(a)<L(b):",
    "  P1 LOCAL L=1 V=[0 1 0] || P0 RECV L=2 V=[1 0 1]",
    "!pairs with L(a)<L(b) that are concurrent: 85",
]
EXP02 = [
    "$ bash run.sh",
    "== A: retries=0 dedup=false (at-most-once)",
    "rpcs sent=20  retries=0  gave up=8",
    "!expected balance=200  server balance=200  executions=20",
    "== B: retries=5 dedup=false (at-least-once)",
    "rpcs sent=29  retries=9  gave up=0",
    "!expected balance=200  server balance=290  executions=29",
    "== C: retries=5 dedup=true  (exactly-once effect)",
    "rpcs sent=28  retries=8  gave up=0",
    "!expected balance=200  server balance=200  executions=20",
]
EXP03 = [
    "my pid: 1   hostname: aos-ctr",
    "cgroup: 0::/",
    "lo: DOWN",
    "sleepers running: 12",
    "!sh: can't fork: Resource temporarily unavailable",
    "hog: 48 MiB touched",
    "Killed",
    "hog exit status: 137",
    "== host view of /sys/fs/cgroup/aos-m06-ctr after exit",
    "!oom_kill 1",
    "pids.events: max 1   pids.peak: 20",
    "nr_throttled 62",
]
EXP05 = [
    "$ systemd-detect-virt",
    "oracle",
    'CPUID.0x40000000 hypervisor signature = "KVMKVMKVM"',
    "add (stays on the CPU)          0.3 ns/op",
    "getppid syscall (guest)      131.1 ns/op",
    "!cpuid leaf 0 (VM exit)     57792.9 ns/op",
    "cpuid leaf 1 (VM exit)     26008.4 ns/op",
    "# repeats, cpuid leaf 0:",
    "316054.5 / 34592.4 / 45560.8 ns/op",
    "# WSL2 VM on Hyper-V, same host: cpuid 383.5 ns/op",
]
CAP01 = AOS_LAB
CAP02 = AOS_LAB
CAP03 = AOS_LAB
CAP05 = AOS_LAB


def same(s):
    return {"en": s, "fa": s}


LABS = [
    dict(
        slug="01-lamport-vector-clocks",
        num="06.1",
        title={"en": "Lamport and vector clocks", "fa": "ساعت‌های Lamport و برداری"},
        goal={
            "en": "Stamp every event of three real processes with Lamport and vector clocks, and prove that only vectors detect concurrency.",
            "fa": "هر رویداد سه پردازهٔ واقعی را با ساعت Lamport و برداری مهر بزنید و نشان دهید فقط بردارها همروندی را تشخیص می‌دهند.",
        },
        where={"en": "aos-lab · Go · UDP 9600-9602", "fa": "aos-lab · Go · UDP 9600-9602"},
        setup_cards=[
            (
                "r-user",
                {"en": "Three processes", "fa": "سه پردازه"},
                {"en": "P0, P1, P2 on localhost UDP", "fa": "P0 و P1 و P2 روی UDP محلی"},
            ),
            ("r-data", {"en": "Clock rules", "fa": "قواعد ساعت"}, same("tick: L++ · merge: max(L,Lm)+1")),
            (
                "r-kernel",
                {"en": "Log", "fa": "لاگ"},
                {"en": "one JSON line per event, under a mutex", "fa": "یک خط JSON برای هر رویداد، زیر mutex"},
            ),
            (
                "r-hardware",
                {"en": "Analyzer", "fa": "تحلیل‌گر"},
                {"en": "clock condition, total order, concurrent pairs", "fa": "شرط ساعت، ترتیب کامل، جفت‌های همروند"},
            ),
        ],
        steps=[
            "$ cd ~/work/06-distributed-virtualization/01-lamport-vector-clocks",
            "$ go version",
            "$ bash run.sh",
            "# = go build; 3 x ./clocks -id i & ; wait;",
            "#   ./clocks -analyze p0.log p1.log p2.log",
            "$ head -3 p1.log",
            "$ SEED=7 EVENTS=10 bash run.sh",
        ],
        expected=EXP01,
        captured=CAP01,
        observe=[
            (
                {"en": "lamport n/n, vector n/n", "fa": "lamport n/n و vector n/n"},
                {
                    "en": "merge() makes every receive larger than its send",
                    "fa": "merge() هر دریافت را از ارسالش بزرگ‌تر می‌کند",
                },
            ),
            (
                {"en": "Ties in L across processes", "fa": "مقدار L برابر در پردازه‌های مختلف"},
                {"en": "total order breaks ties by process id", "fa": "ترتیب کامل تساوی را با شمارهٔ پردازه می‌شکند"},
            ),
            (
                {"en": "L(a) < L(b) yet a ∥ b", "fa": "L(a) < L(b) ولی a ∥ b"},
                {
                    "en": "sorting logs by Lamport time is not causal order",
                    "fa": "مرتب‌کردن لاگ با زمان Lamport ترتیب علّی نیست",
                },
            ),
        ],
        pitfalls=[
            (same("bind: address already in use"), same("pkill -f './clocks -id'")),
            (
                {"en": "messages=0", "fa": "messages=0"},
                {"en": "keep the 300 ms start delay", "fa": "تأخیر ۳۰۰ میلی‌ثانیه‌ای شروع را نگه دارید"},
            ),
            (
                {"en": "vector k/n with k < n", "fa": "vector k/n با k < n"},
                {
                    "en": "copy the slice; lock update + log",
                    "fa": "slice را کپی کنید؛ به‌روزرسانی و لاگ را با هم قفل کنید",
                },
            ),
        ],
        ext={
            "en": "Make every send a causal broadcast with random 0-300 ms delays per copy, and deliver from a hold-back queue only when Vm[j] = V[j]+1 and Vm[k] ≤ V[k].",
            "fa": "هر ارسال را به broadcast علّی با تأخیر تصادفی ۰ تا ۳۰۰ میلی‌ثانیه برای هر نسخه تبدیل کنید و پیام را از صف انتظار فقط وقتی تحویل دهید که Vm[j] = V[j]+1 و Vm[k] ≤ V[k].",
        },
    ),
    dict(
        slug="02-rpc-idempotency",
        num="06.2",
        title={"en": "RPC retries and idempotency", "fa": "تکرار RPC و idempotency"},
        goal={
            "en": "Watch at-most-once, at-least-once and exactly-once effect happen to the same 20 deposits, and build the duplicate filter.",
            "fa": "ببینید at-most-once و at-least-once و اثر exactly-once روی همان ۲۰ واریز چه می‌کنند و فیلتر تکراری را بسازید.",
        },
        where={"en": "aos-lab · Go net/rpc · TCP 9650-9652", "fa": "aos-lab · Go net/rpc · TCP 9650-9652"},
        setup_cards=[
            (
                "r-data",
                {"en": "Server", "fa": "سرور"},
                {
                    "en": "Deposit runs, then 30% of replies arrive late",
                    "fa": "Deposit اجرا می‌شود و ۳۰٪ پاسخ‌ها دیر می‌رسند",
                },
            ),
            ("r-user", {"en": "Client", "fa": "کلاینت"}, same("timeout 200ms · retries 0 or 5")),
            (
                "r-kernel",
                {"en": "Request ID", "fa": "شناسهٔ درخواست"},
                {"en": "one per logical deposit, reused on retries", "fa": "یکی برای هر واریز منطقی، تکرار در retryها"},
            ),
            ("r-hardware", {"en": "Filter", "fa": "فیلتر"}, same("-dedup: replies[RequestID]")),
        ],
        steps=[
            "$ cd ~/work/06-distributed-virtualization/02-rpc-idempotency",
            "$ bash run.sh",
            "# A: retries=0  B: retries=5  C: retries=5 + dedup",
            "",
            "$ ./rpcbank server -addr 127.0.0.1:9660 -lose 0.5 &",
            "$ ./rpcbank client -addr 127.0.0.1:9660 -n 10 -retries 3",
            "$ kill %1",
        ],
        expected=EXP02,
        captured=CAP02,
        observe=[
            (
                {"en": "A: gave up, yet executions=20", "fa": "A: کلاینت تسلیم شد ولی executions=20"},
                {"en": "a timeout means unknown, not failed", "fa": "timeout یعنی نامعلوم، نه ناموفق"},
            ),
            (
                {"en": "B: executions = 20 + retries", "fa": "B: executions = 20 + retries"},
                {"en": "every retry executed again", "fa": "هر تکرار دوباره اجرا شد"},
            ),
            (
                {"en": "C: same retries, correct balance", "fa": "C: همان تکرارها، موجودی درست"},
                {
                    "en": "at-least-once + dedup = exactly-once effect",
                    "fa": "at-least-once به‌علاوهٔ dedup برابر اثر exactly-once",
                },
            ),
        ],
        pitfalls=[
            (same("bind: address already in use"), same("pkill -f 'rpcbank server'")),
            (
                {"en": "duplicates with dedup on", "fa": "تکرار با dedup روشن"},
                {"en": "create the ID outside the retry loop", "fa": "شناسه را بیرون از حلقهٔ retry بسازید"},
            ),
            (
                {"en": "server memory grows", "fa": "حافظهٔ سرور رشد می‌کند"},
                {"en": "reply cache never evicts: see extension", "fa": "reply cache هرگز پاک نمی‌شود: تمرین تکمیلی"},
            ),
        ],
        ext={
            "en": "Bound the reply cache: client IDs plus increasing sequence numbers, one entry per client. 3 clients x 20 deposits: correct balance, 60 executions, 3 entries.",
            "fa": "reply cache را محدود کنید: شناسهٔ کلاینت و شمارهٔ ترتیبی صعودی، یک مدخل برای هر کلاینت. ۳ کلاینت × ۲۰ واریز: موجودی درست، ۶۰ اجرا، ۳ مدخل.",
        },
    ),
    dict(
        slug="03-mini-container",
        num="06.3",
        title={"en": "A container without Docker", "fa": "container بدون Docker"},
        goal={
            "en": "Build a container from unshare, pivot_root and three cgroup v2 files, then watch each limit fire.",
            "fa": "یک container را از unshare و pivot_root و سه فایل cgroup v2 بسازید و ببینید هر محدودیت چطور عمل می‌کند.",
        },
        where={"en": "VM only (aos-lab, root)", "fa": "فقط VM (aos-lab، root)"},
        setup_cards=[
            (
                "r-data",
                {"en": "Root filesystem", "fa": "فایل‌سیستم ریشه"},
                same("Alpine 3.20.3 minirootfs + static hog"),
            ),
            ("r-kernel", {"en": "cgroup v2", "fa": "cgroup v2"}, same("memory.max=64M pids.max=20 cpu.max=20%")),
            ("r-user", {"en": "Namespaces", "fa": "namespaceها"}, same("mount uts ipc net pid cgroup")),
            (
                "r-hardware",
                {"en": "Safety", "fa": "ایمنی"},
                {
                    "en": "OOM only inside the group; cleanup removes all",
                    "fa": "OOM فقط داخل گروه؛ پاک‌سازی همه را حذف می‌کند",
                },
            ),
        ],
        steps=[
            "$ bash get-rootfs.sh",
            "$ gcc -Wall -Wextra -O2 -static -o hog hog.c",
            "$ sudo install -m 755 hog demo.sh rootfs/usr/local/bin/",
            "$ bash minictr.sh /usr/local/bin/demo.sh",
            "# cleanup",
            "$ sudo rmdir /sys/fs/cgroup/aos-m06-ctr",
            "$ sudo rm -rf rootfs hog alpine-minirootfs-*.tar.gz",
        ],
        expected=EXP03,
        captured=CAP03,
        observe=[
            (
                {"en": "pid 1, cgroup 0::/, only lo", "fa": "pid 1، cgroup 0::/، فقط lo"},
                {"en": "PID, cgroup and net namespaces", "fa": "namespaceهای PID و cgroup و net"},
            ),
            (
                {"en": "can't fork at pids.max", "fa": "can't fork در pids.max"},
                {"en": "EAGAIN from pids_try_charge()", "fa": "EAGAIN از pids_try_charge()"},
            ),
            (
                {"en": "hog killed, oom_kill 1", "fa": "hog کشته شد، oom_kill 1"},
                {"en": "memcg OOM scoped to the group", "fa": "OOM در memcg فقط داخل گروه"},
            ),
        ],
        pitfalls=[
            (same("pivot_root: Invalid argument"), same("mount --bind rootfs rootfs; mount --make-rprivate /")),
            (
                {"en": "ps shows host processes", "fa": "ps پردازه‌های میزبان را نشان می‌دهد"},
                {"en": "mount /proc after pivot_root", "fa": "/proc را بعد از pivot_root سوار کنید"},
            ),
            ({"en": "hog swaps instead of dying", "fa": "hog به‌جای مردن swap می‌کند"}, same("echo 0 > memory.swap.max")),
        ],
        ext={
            "en": "Replace unshare(1) with your own C launcher: clone(CLONE_NEW*), join the cgroup before the child runs, unshare(CLONE_NEWCGROUP), pivot_root(2) via syscall(), mount /proc, execv.",
            "fa": "به‌جای unshare(1) یک launcher به زبان C بنویسید: clone(CLONE_NEW*)، پیوستن به cgroup پیش از اجرای فرزند، unshare(CLONE_NEWCGROUP)، pivot_root(2) با syscall()، سوار کردن /proc و execv.",
        },
    ),
    dict(
        slug="04-kvm-client",
        num="06.4",
        title={"en": "A 100-line KVM client", "fa": "کلاینت KVM در ۱۰۰ خط"},
        goal={
            "en": "Write the whole user-space side of a hypervisor: one VM, one vCPU, 4 KiB of RAM, and a loop over VM exits.",
            "fa": "کل بخش فضای کاربرِ یک hypervisor را بنویسید: یک VM، یک vCPU، ۴ کیلوبایت RAM و حلقه‌ای روی VM exitها.",
        },
        where={"en": "KVM host or nested VM (not aos-lab)", "fa": "میزبان KVM یا VM تودرتو (نه aos-lab)"},
        setup_cards=[
            ("r-hardware", {"en": "Needs", "fa": "نیازمندی"}, same("/dev/kvm · VT-x/AMD-V or nesting")),
            ("r-user", {"en": "Guest", "fa": "مهمان"}, same("mov $0x3f8,%dx; add %bl,%al; out; hlt")),
            ("r-kernel", {"en": "fd chain", "fa": "زنجیرهٔ fd"}, same("/dev/kvm → VM fd → vCPU fd")),
            ("r-data", {"en": "Shared page", "fa": "صفحهٔ مشترک"}, same("mmap(vcpufd) = struct kvm_run")),
        ],
        steps=[
            "$ ls -l /dev/kvm",
            "$ as --32 -o guest.o guest.S",
            "$ objdump -d -mi8086 guest.o | tail -8",
            "$ gcc -Wall -Wextra -O2 -o kvm-hello kvm-hello.c",
            "$ ./kvm-hello",
        ],
        expected=[
            "# real, where KVM is missing (aos-lab, WSL2):",
            "$ ./kvm-hello",
            "!kvm-hello: open /dev/kvm: No such file or directory",
            "",
            "# EXPECTED on a KVM host (UNVERIFIED):",
            "exit 1: KVM_EXIT_IO port=0x3f8 byte=0x34 (<t> us)",
            "4exit 2: KVM_EXIT_IO port=0x3f8 byte=0x0a (<t> us)",
            "",
            "exit 3: KVM_EXIT_HLT (<t> us)",
        ],
        observe=[
            (
                {"en": "Only 3 exits reach user space", "fa": "فقط ۳ exit به فضای کاربر می‌رسد"},
                {"en": "EPT faults etc. are handled inside KVM", "fa": "خطاهای EPT و مانند آن داخل KVM رسیدگی می‌شوند"},
            ),
            (
                {"en": "HLT comes to you", "fa": "HLT به شما می‌رسد"},
                {"en": "no in-kernel irqchip was created", "fa": "irqchip داخل کرنل ساخته نشده"},
            ),
            (
                {"en": "Byte at data_offset", "fa": "بایت در data_offset"},
                {"en": "second page of the vCPU mmap", "fa": "صفحهٔ دوم mmap مربوط به vCPU"},
            ),
        ],
        pitfalls=[
            (
                same("open /dev/kvm: No such file"),
                {
                    "en": "bare metal or nested VM; modprobe kvm_intel",
                    "fa": "سخت‌افزار واقعی یا VM تودرتو؛ modprobe kvm_intel",
                },
            ),
            (
                same("KVM_EXIT_FAIL_ENTRY 0x80000021"),
                {"en": "invalid guest state: KVM_GET_SREGS first", "fa": "وضعیت نامعتبر مهمان: اول KVM_GET_SREGS"},
            ),
            (same("KVM_EXIT_SHUTDOWN"), {"en": "RIP outside the memory slot", "fa": "RIP بیرون از memory slot"}),
        ],
        ext={
            "en": "Print Hello with a lodsb/out loop, then write to guest-physical 0x8000 (no slot there), handle KVM_EXIT_MMIO and print an exit histogram.",
            "fa": "با حلقهٔ lodsb/out رشتهٔ Hello را چاپ کنید، سپس در آدرس فیزیکی مهمان 0x8000 (که slot ندارد) بنویسید، KVM_EXIT_MMIO را رسیدگی کنید و نمودار شمارش exitها را چاپ کنید.",
        },
    ),
    dict(
        slug="05-vmexit-cost",
        num="06.5",
        title={"en": "VM-exit cost from inside a guest", "fa": "هزینهٔ VM exit از داخل مهمان"},
        goal={
            "en": "Time an instruction that always exits (CPUID) against one that never leaves the CPU and one that stays in the guest kernel.",
            "fa": "زمان دستوری که همیشه exit می‌کند (CPUID) را با دستوری که از CPU بیرون نمی‌رود و syscallی که در کرنل مهمان می‌ماند مقایسه کنید.",
        },
        where={"en": "aos-lab (any x86-64 guest)", "fa": "aos-lab (هر مهمان x86-64)"},
        setup_cards=[
            ("r-hardware", {"en": "Exits always", "fa": "همیشه exit"}, same("cpuid → hypervisor emulates")),
            ("r-kernel", {"en": "Stays in guest", "fa": "در مهمان می‌ماند"}, same("syscall(SYS_getppid)")),
            ("r-user", {"en": "Never leaves CPU", "fa": "از CPU بیرون نمی‌رود"}, same("add $1, %reg")),
            ("r-data", {"en": "Timer", "fa": "زمان‌سنج"}, same("clock_gettime(CLOCK_MONOTONIC)")),
        ],
        steps=[
            "$ systemd-detect-virt",
            "$ grep -m1 -o hypervisor /proc/cpuinfo",
            "$ gcc -Wall -Wextra -O2 -o vmexit-cost vmexit-cost.c",
            "$ ./vmexit-cost",
            "$ for i in 1 2 3; do ./vmexit-cost 100000 \\",
            "    | grep 'cpuid leaf 0'; done",
        ],
        expected=EXP05,
        captured=CAP05,
        observe=[
            (
                {"en": "cpuid is many syscalls", "fa": "cpuid برابر چند syscall"},
                {"en": "the price is the exit, not the instruction", "fa": "هزینه مال exit است، نه خود دستور"},
            ),
            (
                {"en": "Guest cannot count exits", "fa": "مهمان exitها را نمی‌شمارد"},
                {"en": "only the host sees kvm:kvm_exit", "fa": "فقط میزبان kvm:kvm_exit را می‌بیند"},
            ),
            (
                {"en": "Two hypervisors, two numbers", "fa": "دو hypervisor، دو عدد"},
                {"en": "compare with WSL2 (Hyper-V): ~384 ns", "fa": "مقایسه با WSL2 (Hyper-V): حدود ۳۸۴ نانوثانیه"},
            ),
        ],
        pitfalls=[
            (
                {"en": "hypervisor present = 0", "fa": "hypervisor present = 0"},
                {"en": "bare metal: cpuid does not exit", "fa": "سخت‌افزار واقعی: cpuid خارج نمی‌شود"},
            ),
            ({"en": "noisy cpuid numbers", "fa": "عددهای پرنوسان cpuid"}, same("run 3x, take the min; taskset -c 2")),
            (
                same("perf stat -e cycles: <not supported>"),
                {"en": "no PMU in this guest: use task-clock", "fa": "این مهمان PMU ندارد: task-clock"},
            ),
        ],
        ext={
            "en": "On a KVM host, record a running guest with perf kvm stat and the kvm:kvm_exit tracepoint, and explain which exit reasons dominate (UNVERIFIED here).",
            "fa": "روی یک میزبان KVM، یک مهمان در حال اجرا را با perf kvm stat و tracepoint با نام kvm:kvm_exit ثبت کنید و توضیح دهید کدام دلیل‌های exit غالب‌اند (اینجا UNVERIFIED).",
        },
    ),
]
