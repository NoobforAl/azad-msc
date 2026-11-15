# Lab-deck content for 04-memory. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced OS · 04 Memory", "fa": "سیستم‌عامل پیشرفته · ۰۴ حافظه"}

CAP = {
    "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15",
    "fa": "aos-lab (VirtualBox، اوبونتو 24.04، لینوکس 6.18.63)، 2026-11-15",
}


def same(s):
    return {"en": s, "fa": s}


LABS = [
    dict(
        slug="01-page-faults",
        num="04.1",
        title={"en": "Count page faults", "fa": "شمردن page faultها"},
        goal={
            "en": "Count the faults it costs to touch every page of a mapping, and explain each count: demand paging, zero page, readahead, THP.",
            "fa": "تعداد faultهایی را که touch هر صفحهٔ یک mapping هزینه دارد بشمارید و هر عدد را با demand paging، zero page، readahead و THP توضیح دهید.",
        },
        where={"en": "aos-lab VM · user space", "fa": "VM آزمایشگاه · فضای کاربر"},
        setup_cards=[
            ("r-user", {"en": "Program", "fa": "برنامه"}, same("touch.c: 1 byte per 4 KiB page")),
            ("r-kernel", {"en": "Kernel path", "fa": "مسیر کرنل"}, same("do_anonymous_page · filemap_fault")),
            ("r-hardware", {"en": "Counters", "fa": "شمارنده‌ها"}, same("getrusage · perf software events")),
            ("r-data", {"en": "Modes", "fa": "حالت‌ها"}, same("anon · anon-read · thp · file · file-rand")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o touch touch.c",
            "$ ./touch anon      256",
            "$ ./touch anon-read 256",
            "$ ./touch thp       256",
            "$ dd if=/dev/urandom of=data.bin bs=1M count=256",
            "$ ./touch file      256 data.bin",
            "$ ./touch file-rand 256 data.bin",
            "$ perf stat -e page-faults,minor-faults,major-faults \\",
            "    ./touch anon 256",
        ],
        expected="@LAB1@",
        observe=[
            (
                {"en": "Same faults, different RSS", "fa": "fault یکسان، RSS متفاوت"},
                {"en": "anon-read maps the zero page", "fa": "anon-read فقط zero page را map می‌کند"},
            ),
            (
                {"en": "THP: ~pages/512 faults", "fa": "THP: حدود صفحه‌ها تقسیم بر ۵۱۲"},
                {"en": "one PMD maps 2 MiB", "fa": "یک PMD دو مگابایت را map می‌کند"},
            ),
            (
                {"en": "file vs file-rand", "fa": "file در برابر file-rand"},
                {
                    "en": "readahead + fault-around vs 1 major fault per page",
                    "fa": "readahead و fault-around در برابر یک fault بزرگ برای هر صفحه",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "thp = anon fault count", "fa": "تعداد fault در thp مثل anon"},
                {"en": "THP set to never; check enabled", "fa": "THP روی never است؛ enabled را ببینید"},
            ),
            (
                {"en": "file: 0 major faults", "fa": "file: صفر fault بزرگ"},
                {
                    "en": "pages still cached; DONTNEED after fdatasync",
                    "fa": "صفحه‌ها هنوز در cache؛ DONTNEED بعد از fdatasync",
                },
            ),
            (
                {"en": "perf: <not supported>", "fa": "perf: <not supported>"},
                {"en": "no PMU here: software events only", "fa": "اینجا PMU نیست؛ فقط رویدادهای نرم‌افزاری"},
            ),
        ],
        ext={
            "en": "Make anon mode fault once per 64 KiB without THP (mTHP hugepages-64kB, or MAP_POPULATE). Which removes faults and which only moves them?",
            "fa": "کاری کنید حالت anon بدون THP برای هر ۶۴ کیلوبایت یک fault بدهد (mTHP با hugepages-64kB یا MAP_POPULATE). کدام fault را حذف می‌کند و کدام فقط جابه‌جا؟",
        },
        captured=CAP,
    ),
    dict(
        slug="02-cow-pagemap",
        num="04.2",
        title={"en": "Copy-on-write through pagemap", "fa": "copy-on-write از راه pagemap"},
        goal={
            "en": "Prove that after fork() parent and child share frames until a write, and that each first write costs one fault and one new frame.",
            "fa": "ثابت کنید بعد از fork() والد و فرزند تا اولین نوشتن قاب‌ها را شریک‌اند و هر اولین نوشتن یک fault و یک قاب تازه هزینه دارد.",
        },
        where={"en": "aos-lab VM · sudo (PFNs)", "fa": "VM آزمایشگاه · با sudo (برای PFN)"},
        setup_cards=[
            ("r-user", {"en": "Program", "fa": "برنامه"}, same("cow.c: 64 MiB, fork, child writes half")),
            ("r-data", {"en": "pagemap", "fa": "pagemap"}, same("bit 63 present · bit 56 excl · PFN")),
            ("r-kernel", {"en": "Kernel path", "fa": "مسیر کرنل"}, same("do_wp_page → wp_page_copy")),
            ("r-hardware", {"en": "smaps", "fa": "smaps"}, same("Shared_Dirty / Private_Dirty")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o cow cow.c",
            "$ sudo ./cow 64",
            "",
            "# without root PFNs read as 0",
            "$ ./cow 16 | head -3",
        ],
        expected="@LAB2@",
        observe=[
            (
                {"en": "Same PFN after fork", "fa": "PFN یکسان بعد از fork"},
                {"en": "PTE copied, page not", "fa": "PTE کپی شده، صفحه نه"},
            ),
            (
                {"en": "minor faults = pages written", "fa": "تعداد minor fault برابر صفحه‌های نوشته‌شده"},
                {"en": "one COW per page", "fa": "یک COW برای هر صفحه"},
            ),
            (
                {"en": "Parent PFN unchanged", "fa": "PFN والد تغییر نمی‌کند"},
                {"en": "the writer gets the copy", "fa": "نویسنده کپی را می‌گیرد"},
            ),
        ],
        pitfalls=[
            (
                {"en": "pfn=0x0", "fa": "pfn=0x0"},
                {"en": "not root (hidden since 4.2)", "fa": "بدون root (از ۴٫۲ پنهان است)"},
            ),
            (
                {"en": "Shared_Dirty = 0 after fork", "fa": "Shared_Dirty صفر بعد از fork"},
                {"en": "THP pages; keep MADV_NOHUGEPAGE", "fa": "صفحهٔ THP؛ MADV_NOHUGEPAGE را نگه دارید"},
            ),
            (
                {"en": "faults ≠ 8192", "fa": "تعداد fault برابر ۸۱۹۲ نیست"},
                {
                    "en": "a few stack/printf pages; small diff is fine",
                    "fa": "چند صفحهٔ stack و printf؛ اختلاف کم عادی است",
                },
            ),
        ],
        ext={
            "en": "Repeat with MADV_HUGEPAGE. How many COW faults now, and does the child copy 2 MiB or split? Use AnonHugePages and thp_split_pmd.",
            "fa": "با MADV_HUGEPAGE تکرار کنید. حالا چند COW fault هست و فرزند ۲ مگابایت کپی می‌کند یا صفحه شکسته می‌شود؟ از AnonHugePages و thp_split_pmd استفاده کنید.",
        },
        captured=CAP,
    ),
    dict(
        slug="03-mmap-shared",
        num="04.3",
        title={"en": "mmap: shared vs private", "fa": "mmap: اشتراکی یا خصوصی"},
        goal={
            "en": "Run 4 × 1 000 000 atomic increments through four kinds of mapping; show who sees the result and what reaches the file.",
            "fa": "۴ × ۱٬۰۰۰٬۰۰۰ افزایش اتمی را در چهار نوع mapping اجرا کنید و نشان دهید چه کسی نتیجه را می‌بیند و چه چیزی به فایل می‌رسد.",
        },
        where={"en": "aos-lab VM · user space", "fa": "VM آزمایشگاه · فضای کاربر"},
        setup_cards=[
            ("r-user", {"en": "Program", "fa": "برنامه"}, same("mapcount.c: fork 4, __atomic_fetch_add")),
            ("r-data", {"en": "File", "fa": "فایل"}, same("counter.bin (4 KiB, ftruncate)")),
            ("r-kernel", {"en": "Kernel path", "fa": "مسیر کرنل"}, same("do_shared_fault · do_cow_fault")),
            ("r-hardware", {"en": "Check", "fa": "بررسی"}, same("msync + pread · od -t u8")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o mapcount mapcount.c",
            "$ ./mapcount file-shared  counter.bin",
            "$ od -A d -t u8 -N 8 counter.bin",
            "$ ./mapcount file-private counter.bin",
            "$ ./mapcount anon-shared",
            "$ ./mapcount anon-private",
        ],
        expected="@LAB3@",
        observe=[
            (
                {"en": "Only shared modes total 4 000 000", "fa": "فقط حالت‌های اشتراکی ۴٬۰۰۰٬۰۰۰ می‌شوند"},
                {"en": "one page, many PTEs", "fa": "یک صفحه، چند PTE"},
            ),
            (
                {"en": "Only file-shared changes the file", "fa": "فقط file-shared فایل را عوض می‌کند"},
                {"en": "page cache + msync", "fa": "page cache و msync"},
            ),
            (
                {"en": "Private writes vanish", "fa": "نوشتن خصوصی از بین می‌رود"},
                {"en": "COW copy freed at _exit", "fa": "کپی COW هنگام _exit آزاد می‌شود"},
            ),
        ],
        pitfalls=[
            (
                {"en": "total < expected", "fa": "مجموع کمتر از انتظار"},
                {"en": "++ instead of an atomic", "fa": "++ به‌جای atomic"},
            ),
            (
                {"en": "Bus error", "fa": "Bus error"},
                {"en": "file shorter than mapping", "fa": "فایل کوتاه‌تر از mapping"},
            ),
            (
                {"en": "od shows old value", "fa": "od مقدار قدیمی را نشان می‌دهد"},
                {
                    "en": "network FS; local FS shares the page cache",
                    "fa": "فایل‌سیستم شبکه‌ای؛ فایل‌سیستم محلی page cache را شریک است",
                },
            ),
        ],
        ext={
            "en": "Use (*ctr)++ with 4 × 10 000 000 on anon-shared and explain the loss; then share a counter between two unrelated processes with memfd_create or shm_open.",
            "fa": "در anon-shared با ۴ × ۱۰٬۰۰۰٬۰۰۰ از (*ctr)++ استفاده کنید و کم شدن عدد را توضیح دهید؛ بعد بین دو process بی‌ربط با memfd_create یا shm_open یک شمارنده شریک کنید.",
        },
        captured=CAP,
    ),
    dict(
        slug="04-tlb-hugepages",
        num="04.4",
        title={"en": "TLB reach and huge pages", "fa": "برد TLB و صفحه‌های بزرگ"},
        goal={
            "en": "Measure the cost of TLB misses as ns per access over a growing number of pages, 4 KiB vs 2 MiB THP, without PMU counters.",
            "fa": "هزینهٔ TLB miss را به‌صورت نانوثانیه برای هر دسترسی روی تعداد رو به افزایش صفحه، با ۴ کیلوبایت و THP دو مگابایتی و بدون شمارندهٔ PMU، اندازه بگیرید.",
        },
        where={"en": "aos-lab VM · 512 MiB", "fa": "VM آزمایشگاه · ۵۱۲ مگابایت"},
        setup_cards=[
            ("r-user", {"en": "Program", "fa": "برنامه"}, same("tlbchase.c: random chase, 1 line/page")),
            ("r-hardware", {"en": "No PMU", "fa": "بدون PMU"}, same("dTLB-load-misses: UNVERIFIED")),
            ("r-kernel", {"en": "THP", "fa": "THP"}, same("MADV_HUGEPAGE → create_huge_pmd")),
            ("r-data", {"en": "Proof", "fa": "اثبات"}, same("AnonHugePages in smaps")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o tlbchase tlbchase.c",
            "$ cat /sys/kernel/mm/transparent_hugepage/enabled",
            "$ perf stat -e cycles true 2>&1 | grep cycles",
            "$ taskset -c 2 ./tlbchase 4k  512 | tee 4k.txt",
            "$ taskset -c 2 ./tlbchase thp 512 | tee thp.txt",
        ],
        expected="@LAB4@",
        observe=[
            (
                {"en": "Same cost up to 16 MiB", "fa": "تا ۱۶ مگابایت هزینه یکسان است"},
                {"en": "data-cache latency, shared by both", "fa": "تأخیر cache داده که در هر دو یکسان است"},
            ),
            (
                {"en": "Split from 32 MiB", "fa": "جدا شدن از ۳۲ مگابایت"},
                {"en": "4k 180-950 ns vs thp 75-170 ns", "fa": "۴k بین ۱۸۰ و ۹۵۰ نانوثانیه، thp بین ۷۵ و ۱۷۰"},
            ),
            (
                {"en": "Gap at same N", "fa": "فاصله در N یکسان"},
                {"en": "page-walk cost (2-D under EPT)", "fa": "هزینهٔ پیمایش جدول (دوبعدی زیر EPT)"},
            ),
        ],
        pitfalls=[
            (
                {"en": "AnonHugePages = 0 in thp", "fa": "AnonHugePages صفر در thp"},
                {"en": "THP never/fallback: thp_fault_fallback", "fa": "THP خاموش یا برگشت: thp_fault_fallback"},
            ),
            (
                {"en": "noisy numbers", "fa": "عددهای پرنوسان"},
                {"en": "shared host: taskset, 3 runs, median", "fa": "میزبان مشترک: taskset، سه اجرا، میانه"},
            ),
            (
                {"en": "flat in both modes", "fa": "صاف در هر دو حالت"},
                {"en": "loop optimized away; keep p live", "fa": "حلقه حذف شده؛ p را زنده نگه دارید"},
            ),
        ],
        ext={
            "en": "Add hugetlbfs (MAP_HUGETLB, nr_hugepages=256 then restore 0) and 1 GiB pages if pdpe1gb exists; plot all curves and explain each knee.",
            "fa": "حالت hugetlbfs (MAP_HUGETLB با nr_hugepages=256 و بعد برگرداندن به ۰) و اگر pdpe1gb هست صفحهٔ ۱ گیگابایتی را اضافه کنید؛ همهٔ منحنی‌ها را رسم و هر knee را توضیح دهید.",
        },
        captured=CAP,
    ),
    dict(
        slug="05-slab-files",
        num="04.5",
        title={"en": "Slab caches and 200 000 files", "fa": "cacheهای slab و ۲۰۰ هزار فایل"},
        goal={
            "en": "Create and delete N empty files and watch the dentry and inode slab caches grow and shrink.",
            "fa": "N فایل خالی بسازید و پاک کنید و رشد و کوچک شدن cacheهای slab مربوط به dentry و inode را ببینید.",
        },
        where={"en": "aos-lab VM · ~10 MB disk", "fa": "VM آزمایشگاه · حدود ۱۰ مگابایت دیسک"},
        setup_cards=[
            ("r-user", {"en": "Program", "fa": "برنامه"}, same("mkfiles.c create|delete DIR N")),
            ("r-kernel", {"en": "Caches", "fa": "cacheها"}, same("dentry · ext4_inode_cache")),
            ("r-data", {"en": "Views", "fa": "نماها"}, same("/proc/slabinfo · slabtop -o -s c")),
            ("r-hardware", {"en": "Accounting", "fa": "accounting"}, same("SReclaimable vs SUnreclaim")),
        ],
        steps=[
            "$ gcc -Wall -Wextra -O2 -o mkfiles mkfiles.c",
            "$ bash slab-watch.sh 200000",
            "$ grep -E '^(Slab|SReclaimable|SUnreclaim):' /proc/meminfo",
        ],
        expected="@LAB5@",
        observe=[
            (
                {"en": "+N dentries, +N inodes", "fa": "N تا dentry و N تا inode بیشتر"},
                {"en": "~1.2 KiB kernel memory per empty file", "fa": "حدود ۱٫۲ کیلوبایت حافظهٔ کرنل برای هر فایل خالی"},
            ),
            (
                {"en": "Not in any RSS", "fa": "در هیچ RSSی نیست"},
                {"en": "slab is kernel memory (SReclaimable)", "fa": "slab حافظهٔ کرنل است (SReclaimable)"},
            ),
            (
                {"en": "Back to baseline after delete", "fa": "بعد از حذف به حالت اول برمی‌گردد"},
                {
                    "en": "bulk free empties slabs → back to buddy",
                    "fa": "آزادسازی دسته‌ای slabها را خالی و به buddy برمی‌گرداند",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "slabinfo: Permission denied", "fa": "slabinfo: Permission denied"},
                {"en": "0400 root: use sudo", "fa": "مجوز ۰۴۰۰ برای root: از sudo استفاده کنید"},
            ),
            (
                {"en": "no ext4_inode_cache", "fa": "ext4_inode_cache نیست"},
                {"en": "other FS: stat -f -c %T ~", "fa": "فایل‌سیستم دیگر: stat -f -c %T ~"},
            ),
            (
                {"en": "numbers barely move", "fa": "عددها تقریباً تکان نمی‌خورند"},
                {"en": "merged caches or small N", "fa": "cacheهای ادغام‌شده یا N کوچک"},
            ),
        ],
        ext={
            "en": "bpftrace tracepoint:kmem:kmem_cache_alloc during mkfiles create: which other caches does creating a file touch?",
            "fa": "در طول mkfiles create با bpftrace روی tracepoint:kmem:kmem_cache_alloc ببینید ساختن یک فایل به چه cacheهای دیگری دست می‌زند.",
        },
        captured=CAP,
    ),
    dict(
        slug="06-oom-thrashing",
        num="04.6",
        title={"en": "Thrashing and OOM in a cgroup", "fa": "thrashing و OOM در cgroup"},
        goal={
            "en": "Watch the OOM killer inside a 128 MiB cgroup, and thrashing in a 64 MiB cgroup reading a 128 MiB file with no swap.",
            "fa": "OOM killer را داخل cgroupی ۱۲۸ مگابایتی ببینید، و thrashing را در cgroupی ۶۴ مگابایتی که بدون swap فایلی ۱۲۸ مگابایتی می‌خواند.",
        },
        where={"en": "VM only · cgroup v2 memory.max", "fa": "فقط VM · cgroup v2 با memory.max"},
        setup_cards=[
            ("r-kernel", {"en": "cgroup", "fa": "cgroup"}, same("memory.max · memory.swap.max=0")),
            ("r-user", {"en": "Programs", "fa": "برنامه‌ها"}, same("hog.c · thrash.c (MADV_RANDOM)")),
            ("r-data", {"en": "Signals", "fa": "نشانه‌ها"}, same("memory.events · memory.stat · PSI")),
            ("r-hardware", {"en": "Safety", "fa": "ایمنی"}, same("only the cgroup is limited")),
        ],
        steps=[
            "$ bash mem-cgroup.sh 128M ./hog 512",
            "$ sudo dmesg | grep -E 'oom-kill:' | tail -1",
            "",
            "$ dd if=/dev/urandom of=big.bin bs=1M count=128",
            "$ bash mem-cgroup.sh 64M  ./thrash big.bin 3",
            "$ bash mem-cgroup.sh 256M ./thrash big.bin 3",
        ],
        expected="@LAB6@",
        observe=[
            (
                {"en": "exit 137, oom_kill 1", "fa": "کد خروج ۱۳۷ و oom_kill 1"},
                {"en": "memcg OOM, rest of VM untouched", "fa": "OOM در memcg؛ بقیهٔ VM دست‌نخورده"},
            ),
            (
                {"en": "64M: same majflt every pass", "fa": "۶۴M: majflt یکسان در هر دور"},
                {"en": "working set > limit = thrashing", "fa": "مجموعهٔ کاری بزرگ‌تر از حد یعنی thrashing"},
            ),
            (
                {"en": "256M: passes 2-3 ~0 faults", "fa": "۲۵۶M: دورهای ۲ و ۳ تقریباً بدون fault"},
                {"en": "working set fits", "fa": "مجموعهٔ کاری جا می‌شود"},
            ),
        ],
        pitfalls=[
            (
                {"en": "mkdir: Permission denied", "fa": "mkdir: Permission denied"},
                {"en": "needs sudo (script does it)", "fa": "sudo لازم است (اسکریپت انجام می‌دهد)"},
            ),
            (
                {"en": "pass 1: 0 major faults", "fa": "دور ۱: صفر fault بزرگ"},
                {
                    "en": "pages charged elsewhere: fadvise DONTNEED",
                    "fa": "صفحه‌ها به cgroup دیگری نوشته شده‌اند: fadvise DONTNEED",
                },
            ),
            (
                {"en": "hog reaches 512 MiB", "fa": "hog به ۵۱۲ مگابایت می‌رسد"},
                {"en": "shell not in the cgroup", "fa": "shell داخل cgroup نیست"},
            ),
        ],
        ext={
            "en": "Use memory.high=64M instead of memory.max for part B: kill, throttle, or both? Then memory.oom.group=1 with two hogs: how many die?",
            "fa": "در بخش B به‌جای memory.max از memory.high=64M استفاده کنید: kill، کندسازی یا هر دو؟ بعد با memory.oom.group=1 دو hog اجرا کنید: چند تا می‌میرند؟",
        },
        captured=CAP,
    ),
]

# Expected-output blocks are pasted from the real runs (lines starting with '!' are highlighted).
EXPECTED = {
    "@LAB1@": [
        "!mode=anon      pages=65536  minflt=65539  majflt=0  rss: 1540 -> 263816 KiB  131.5 ms",
        "!mode=anon-read pages=65536  minflt=65539  majflt=0  rss: 1540 -> 1672 KiB  62.9 ms",
        "!mode=thp       pages=65536  minflt=131  majflt=0  rss: 1536 -> 263812 KiB  67.1 ms",
        "mode=file      pages=65536  minflt=537  majflt=1  rss: 1540 -> 263816 KiB  321.9 ms",
        "!mode=file-rand pages=65536  minflt=3  majflt=65536  rss: 1540 -> 263816 KiB  149234.3 ms",
        "",
        "$ perf stat -e page-faults,... ./touch anon 256",
        "             65600      page-faults",
        "                 0      major-faults",
    ],
    "@LAB2@": [
        "parent before fork  va=0x7de3eda00000 present=1 excl=1 pfn=0x11e516",
        "parent before fork  Rss=65536 kB  Shared_Dirty=0 kB  Private_Dirty=65536 kB",
        "!child  after fork   va=0x7de3eda00000 present=1 excl=0 pfn=0x11e516",
        "child  after fork   Rss=65536 kB  Shared_Dirty=65536 kB  Private_Dirty=0 kB",
        "!child  after write  va=0x7de3eda00000 present=1 excl=1 pfn=0x11d498",
        "child  after write  Rss=65536 kB  Shared_Dirty=32768 kB  Private_Dirty=32768 kB",
        "!child  wrote 8192 pages -> 8193 minor faults (COW)",
        "parent child wrote  va=0x7de3eda00000 present=1 excl=1 pfn=0x11e516",
        "parent byte[0]=0xaa (child wrote 0x55 into its own copy)",
    ],
    "@LAB3@": [
        "!file-shared  children=4 iters=1000000  expected=4000000  parent sees=4000000  file has=4000000",
        "file-private children=4 iters=1000000  expected=4000000  parent sees=0  file has=0",
        "!anon-shared  children=4 iters=1000000  expected=4000000  parent sees=4000000",
        "anon-private children=4 iters=1000000  expected=4000000  parent sees=0",
        "",
        "$ od -A d -t u8 -N 8 counter.bin   # after file-shared",
        "0000000              4000000",
    ],
    "@LAB4@": [
        "      16 pages      0.1 MiB   4k    5.58 ns   thp    3.58 ns",
        "    1024 pages      4.0 MiB   4k   21.76 ns   thp   20.81 ns",
        "    4096 pages     16.0 MiB   4k   97.22 ns   thp   99.03 ns",
        "!    8192 pages     32.0 MiB   4k  181.54 ns   thp   75.12 ns",
        "!   16384 pages     64.0 MiB   4k  603.09 ns   thp  157.67 ns",
        "   32768 pages    128.0 MiB   4k  948.90 ns   thp  149.66 ns",
        "!  131072 pages    512.0 MiB   4k  815.02 ns   thp  172.45 ns",
        "# 4k:  region=512 MiB AnonHugePages=0 kB",
        "# thp: region=512 MiB AnonHugePages=524288 kB",
    ],
    "@LAB5@": [
        "== filesystem of $HOME: ext2/ext3 ; N=200000",
        "== before",
        "  ext4_inode_cache   active=    8068 total=    8207 objsize=1128  ~    8.8 MiB",
        "  dentry             active=   33939 total=   34125 objsize= 192  ~    6.2 MiB",
        "== after create",
        "!  ext4_inode_cache   active=  208075 total=  208075 objsize=1128  ~  223.8 MiB",
        "!  dentry             active=  233919 total=  233919 objsize= 192  ~   42.8 MiB",
        "== after delete",
        "  ext4_inode_cache   active=    8433 total=    8671 objsize=1128  ~    9.3 MiB",
    ],
    "@LAB6@": [
        "hog pid=11690 touched 112 MiB",
        "!== exit status: 137",
        "!  oom_kill 1",
        "# 64M: thrashing, no swap",
        "!pass 1: pages=32768 majflt=32768 minflt=3  223870 ms",
        "!pass 2: pages=32768 majflt=32768 minflt=0  52152 ms",
        "!pass 3: pages=32768 majflt=32768 minflt=0  63778 ms",
        "# 256M: fits",
        "pass 1: pages=32768 majflt=32768 minflt=3  26193 ms",
        "pass 2: pages=32768 majflt=0 minflt=0  2 ms",
        "pass 3: pages=32768 majflt=0 minflt=0  4 ms",
    ],
}
for _lab in LABS:
    _lab["expected"] = EXPECTED.get(_lab["expected"], [_lab["expected"]])
