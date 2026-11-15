# Lab-deck content for 05-filesystems-io. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced OS · 05 File Systems & I/O", "fa": "سیستم‌عامل پیشرفته · ۰۵ فایل‌سیستم و I/O"}
CAP = {
    "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15",
    "fa": "aos-lab (VirtualBox، Ubuntu 24.04، Linux 6.18.63)، ۲۰۲۶-۱۱-۱۵",
}

LABS = [
    dict(
        slug="01-read-call-chain",
        num="05.1",
        title={"en": "The full call chain of read()", "fa": "زنجیرهٔ کامل فراخوانی read()"},
        goal={
            "en": "See every kernel function between read(2) and the page cache, and what changes on a cache miss.",
            "fa": "همهٔ توابع کرنل بین read(2) و page cache را ببینید و اینکه در cache miss چه چیزی عوض می‌شود.",
        },
        where={"en": "Lab VM (sudo, read-only tracing)", "fa": "VM آزمایشگاه (sudo، فقط ردیابی)"},
        setup_cards=[
            (
                "r-user",
                {"en": "Program", "fa": "برنامه"},
                {"en": "readone.c: open + one 4 KiB read()", "fa": "readone.c: یک open و یک read() چهار کیلوبایتی"},
            ),
            (
                "r-kernel",
                {"en": "ftrace", "fa": "ftrace"},
                {"en": "function_graph -g vfs_read -l <10 fns>", "fa": "function_graph -g vfs_read -l <10 fns>"},
            ),
            (
                "r-kernel",
                {"en": "bpftrace", "fa": "bpftrace"},
                {"en": "kstack at filemap_read, block_bio_queue", "fa": "kstack در filemap_read و block_bio_queue"},
            ),
            (
                "r-data",
                {"en": "Cold vs warm", "fa": "سرد و گرم"},
                {
                    "en": "dd iflag=nocache count=0 evicts one file",
                    "fa": "dd iflag=nocache count=0 فقط یک فایل را بیرون می‌کند",
                },
            ),
        ],
        steps=[
            "$ cd ~/work/05-filesystems-io/labs/01-read-call-chain",
            "$ gcc -Wall -Wextra -O2 -o readone readone.c",
            "$ bash trace.sh",
            "# 1 ftrace tree   2 kstack   3 cold read",
            "# 4 stat + fdinfo   5 negative dentry",
        ],
        expected=[
            "$ bash trace.sh",
            "  |  vfs_read() {",
            "  |    ext4_file_read_iter() {",
            "  |      generic_file_read_iter() {",
            "  |        filemap_read() {",
            "  |          filemap_get_pages() {",
            "! ! 339.997 us |            page_cache_sync_ra();",
            "== 3. cold read",
            "!@bios: 1",
            "@bytes: 16384",
            "== 5. negative dentry",
            "!@ext4_lookup: 1",
        ],
        observe=[
            (
                {"en": "ext4 adds one level", "fa": "ext4 فقط یک سطح اضافه می‌کند"},
                {
                    "en": "ext4_file_read_iter -> generic_file_read_iter",
                    "fa": "ext4_file_read_iter -> generic_file_read_iter",
                },
            ),
            (
                {"en": "A cold 4 KiB read moves more data", "fa": "یک read سرد ۴ کیلوبایتی دادهٔ بیشتری جابه‌جا می‌کند"},
                {"en": "synchronous readahead window", "fa": "پنجرهٔ readahead همگام"},
            ),
            (
                {"en": "Missing names are cached too", "fa": "نام‌های ناموجود هم cache می‌شوند"},
                {
                    "en": "negative dentry: 1 of 5 stat()s reaches ext4",
                    "fa": "dentry منفی: فقط ۱ از ۵ stat به ext4 می‌رسد",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "VM freezes: soft lockup [trace-cmd]", "fa": "VM قفل می‌شود: soft lockup [trace-cmd]"},
                {
                    "en": "always -l/-g, depth <= 6, timeout 10, reset",
                    "fa": "همیشه -l/-g، عمق <= 6، timeout 10، سپس reset",
                },
            ),
            (
                {"en": "kprobe not found", "fa": "kprobe پیدا نشد"},
                {"en": "bpftrace -l 'kprobe:filemap_read*'", "fa": "bpftrace -l 'kprobe:filemap_read*'"},
            ),
            (
                {"en": "cold read shows 0 bios", "fa": "read سرد هیچ bio نشان نمی‌دهد"},
                {"en": "sync the file first; dirty pages stay", "fa": "اول sync کنید؛ صفحه‌های dirty حذف نمی‌شوند"},
            ),
        ],
        ext={
            "en": "Trace read() on /dev/null, /proc/uptime and a pipe: which vfs_read() branch runs, and which function makes the bytes?",
            "fa": "read() را روی /dev/null، /proc/uptime و یک pipe ردیابی کنید: کدام شاخهٔ vfs_read() اجرا می‌شود و کدام تابع بایت‌ها را می‌سازد؟",
        },
        captured=CAP,
    ),
    dict(
        slug="02-page-cache",
        num="05.2",
        title={"en": "Page-cache hit vs miss", "fa": "hit و miss در page cache"},
        goal={
            "en": "Measure a cold and a warm read of the same file, evicting only that file.",
            "fa": "خواندن سرد و گرم یک فایل را اندازه بگیرید و فقط همان فایل را از cache بیرون کنید.",
        },
        where={"en": "Lab VM or any Linux box", "fa": "VM آزمایشگاه یا هر لینوکسی"},
        setup_cards=[
            (
                "r-user",
                {"en": "pcache.c", "fa": "pcache.c"},
                {"en": "resident · evict · read", "fa": "resident · evict · read"},
            ),
            (
                "r-data",
                {"en": "Residency", "fa": "حضور در cache"},
                {"en": "mmap + mincore, cross-check with fincore", "fa": "mmap + mincore و مقایسه با fincore"},
            ),
            (
                "r-kernel",
                {"en": "Eviction", "fa": "بیرون‌کردن"},
                {"en": "posix_fadvise(POSIX_FADV_DONTNEED)", "fa": "posix_fadvise(POSIX_FADV_DONTNEED)"},
            ),
            (
                "r-kernel",
                {"en": "Tracepoint", "fa": "tracepoint"},
                {"en": "filemap:mm_filemap_add_to_page_cache", "fa": "filemap:mm_filemap_add_to_page_cache"},
            ),
        ],
        steps=[
            "$ cd ~/work/05-filesystems-io/labs/02-page-cache",
            "$ gcc -Wall -Wextra -O2 -o pcache pcache.c",
            "$ ./pcache evict big.bin; ./pcache resident big.bin",
            "$ ./pcache read big.bin     # cold",
            "$ ./pcache read big.bin     # warm",
            "$ bash run.sh               # all of it + bpftrace",
        ],
        expected=[
            "$ bash run.sh",
            "resident: 0/65536 pages (0.0%), 0 KiB of 262144 KiB",
            "!read: 256 MiB in 0.745 s = 344 MiB/s",
            "@added_folios: 1049",
            "@async_ra: 34",
            "@sync_ra: 1",
            "resident: 65536/65536 pages (100.0%), 262144 KiB of 262144 KiB",
            "!read: 256 MiB in 0.079 s = 3256 MiB/s",
            "@added_folios: 0",
            "read: 256 MiB in 0.098 s = 2605 MiB/s",
            "read: 256 MiB in 0.161 s = 1590 MiB/s",
        ],
        observe=[
            (
                {"en": "Warm is an order of magnitude faster", "fa": "حالت گرم یک مرتبهٔ بزرگی سریع‌تر است"},
                {"en": "memcpy vs disk + readahead", "fa": "memcpy در برابر دیسک + readahead"},
            ),
            (
                {"en": "Folios added only on the cold read", "fa": "folio فقط در read سرد اضافه می‌شود"},
                {"en": "mm_filemap_add_to_page_cache count", "fa": "شمارش mm_filemap_add_to_page_cache"},
            ),
            (
                {"en": "Async readahead dominates", "fa": "readahead ناهمگام غالب است"},
                {"en": "page_cache_async_ra >> sync_ra", "fa": "page_cache_async_ra >> sync_ra"},
            ),
        ],
        pitfalls=[
            (
                {"en": "drop_caches on a shared VM", "fa": "drop_caches روی VM مشترک"},
                {"en": "evict one file with fadvise", "fa": "فقط یک فایل را با fadvise بیرون کنید"},
            ),
            (
                {"en": "evict does nothing", "fa": "evict اثری ندارد"},
                {"en": "dirty or mmapped pages: fdatasync first", "fa": "صفحه‌های dirty یا mmap‌شده: اول fdatasync"},
            ),
            (
                {"en": "cold is suspiciously fast", "fa": "حالت سرد مشکوکانه سریع است"},
                {"en": "host-side disk cache in the hypervisor", "fa": "cache دیسک سمت میزبان در hypervisor"},
            ),
        ],
        ext={
            "en": "Read only the first 4 KiB after eviction, with and without POSIX_FADV_RANDOM. How many pages become resident each time, and why?",
            "fa": "بعد از evict فقط ۴ کیلوبایت اول را بخوانید، یک بار با POSIX_FADV_RANDOM و یک بار بدون آن. هر بار چند صفحه در cache می‌ماند و چرا؟",
        },
        captured=CAP,
    ),
    dict(
        slug="03-fsync-writeback",
        num="05.3",
        title={"en": "fsync cost and writeback", "fa": "هزینهٔ fsync و writeback"},
        goal={
            "en": "Measure what durability costs per write, watch dirty pages drain, and throttle one device without touching global sysctls.",
            "fa": "هزینهٔ ماندگاری هر write را اندازه بگیرید، تخلیهٔ صفحه‌های dirty را ببینید و فقط یک دستگاه را بدون تغییر sysctl سراسری محدود کنید.",
        },
        where={"en": "Lab VM (loop device for part 3)", "fa": "VM آزمایشگاه (loop device برای بخش ۳)"},
        setup_cards=[
            (
                "r-user",
                {"en": "wbench.c", "fa": "wbench.c"},
                {
                    "en": "buffered · fdatasync · fsync · O_DSYNC · O_SYNC",
                    "fa": "buffered · fdatasync · fsync · O_DSYNC · O_SYNC",
                },
            ),
            (
                "r-data",
                {"en": "Dirty pages", "fa": "صفحه‌های dirty"},
                {"en": "Dirty / Writeback in /proc/meminfo", "fa": "Dirty و Writeback در /proc/meminfo"},
            ),
            (
                "r-kernel",
                {"en": "Per-BDI limit", "fa": "محدودیت هر BDI"},
                {
                    "en": "/sys/class/bdi/7:N/max_bytes + strict_limit",
                    "fa": "/sys/class/bdi/7:N/max_bytes + strict_limit",
                },
            ),
            (
                "r-hardware",
                {"en": "Device", "fa": "دستگاه"},
                {"en": "virtual disk; flush = host round trip", "fa": "دیسک مجازی؛ flush یعنی رفت‌وبرگشت تا میزبان"},
            ),
        ],
        steps=[
            "$ cd ~/work/05-filesystems-io/labs/03-fsync-writeback",
            "$ gcc -Wall -Wextra -O2 -o wbench wbench.c",
            "$ ./wbench fsync t.dat 2000 4096",
            "$ bash run.sh   # 1 policies  2 writeback  3 per-BDI",
        ],
        expected=[
            "buffered  2000 x 4096 B: total 6.6 ms | p50 1.9 us",
            "!fsync     2000 x 4096 B: total 67909.6 ms | p50 30950.5 us",
            "fdatasync 2000 x 4096 B: total 74069.5 ms | p50 22035.2 us",
            "== 2b. 384 MiB buffered write",
            "  t=  3s Dirty= 339976 kB",
            "  t= 27s Dirty= 288368 kB",
            "!  t= 30s Dirty=   1652 kB",
            "== 3. per-BDI limit (8 MiB, strict_limit)",
            "  default: 465 MB/s  @throttle_events: 0",
            "!  limited: 268 MB/s  @throttle_events: 50",
        ],
        observe=[
            (
                {"en": "fsync per record costs ~10 000x", "fa": "fsync برای هر رکورد حدود ۱۰٬۰۰۰ برابر هزینه دارد"},
                {"en": "journal commit + cache flush each time", "fa": "commit ژورنال + flush cache در هر بار"},
            ),
            (
                {"en": "Dirty waits 30 s, then drains", "fa": "Dirty سی ثانیه می‌ماند و بعد تخلیه می‌شود"},
                {
                    "en": "below background ratio: dirty_expire_centisecs",
                    "fa": "زیر آستانهٔ background: dirty_expire_centisecs",
                },
            ),
            (
                {"en": "Small BDI budget = many short pauses", "fa": "بودجهٔ کوچک BDI = توقف‌های کوتاه زیاد"},
                {"en": "tracepoint writeback:balance_dirty_pages", "fa": "tracepoint writeback:balance_dirty_pages"},
            ),
        ],
        pitfalls=[
            (
                {"en": "changing vm.dirty_* on a shared VM", "fa": "تغییر vm.dirty_ratio روی VM مشترک"},
                {
                    "en": "use per-BDI knobs on your loop device",
                    "fa": "از تنظیم‌های هر BDI روی loop خودتان استفاده کنید",
                },
            ),
            (
                {"en": "fsync looks free", "fa": "fsync رایگان به نظر می‌رسد"},
                {
                    "en": "tmpfs or nobarrier: check findmnt -T .",
                    "fa": "tmpfs یا nobarrier: با findmnt -T . بررسی کنید",
                },
            ),
            (
                {"en": "loop device left behind", "fa": "loop device باقی می‌ماند"},
                {"en": "losetup -a; losetup -d /dev/loopN", "fa": "losetup -a؛ losetup -d /dev/loopN"},
            ),
        ],
        ext={
            "en": "Run 4 writers that each fsync after every record. Count fsync calls vs jbd2 commits (tracepoints). What is group commit, and how does it change per-writer latency?",
            "fa": "۴ نویسنده اجرا کنید که هر کدام بعد از هر رکورد fsync می‌کنند. تعداد fsync را با تعداد commitهای jbd2 (tracepoint) مقایسه کنید. group commit چیست و تأخیر هر نویسنده را چطور تغییر می‌دهد؟",
        },
        captured=CAP,
    ),
    dict(
        slug="04-io-schedulers",
        num="05.4",
        title={"en": "Compare I/O schedulers with fio", "fa": "مقایسهٔ I/O schedulerها با fio"},
        goal={
            "en": "Measure throughput and reader tail latency under none, mq-deadline, bfq and kyber on the same device.",
            "fa": "توان عملیاتی و تأخیر دنبالهٔ خواننده را با none، mq-deadline، bfq و kyber روی یک دستگاه اندازه بگیرید.",
        },
        where={"en": "Lab VM only (loop device, sudo)", "fa": "فقط VM آزمایشگاه (loop device، sudo)"},
        setup_cards=[
            (
                "r-data",
                {"en": "Device", "fa": "دستگاه"},
                {"en": "512 MiB file, losetup --direct-io=on", "fa": "فایل ۵۱۲ مگابایتی، losetup --direct-io=on"},
            ),
            (
                "r-kernel",
                {"en": "Schedulers", "fa": "زمان‌بندها"},
                {"en": "/sys/block/loopN/queue/scheduler", "fa": "/sys/block/loopN/queue/scheduler"},
            ),
            (
                "r-user",
                {"en": "Job A", "fa": "کار A"},
                {"en": "4 KiB randread, QD32, io_uring", "fa": "randread چهار کیلوبایتی، QD32، io_uring"},
            ),
            (
                "r-user",
                {"en": "Job B", "fa": "کار B"},
                {"en": "QD1 reader + 1 MiB sequential writer", "fa": "خوانندهٔ QD1 + نویسندهٔ ترتیبی ۱ مگابایتی"},
            ),
        ],
        steps=[
            "$ cd ~/work/05-filesystems-io/labs/04-io-schedulers",
            "$ bash sched-bench.sh          # ~1 min per scheduler",
            "$ RUNTIME=5 bash sched-bench.sh  # quicker",
        ],
        expected=[
            "device /dev/loop0: [none] mq-deadline bfq kyber",
            "scheduler    A:IOPS A:p99(us) | B:rd p50  B:rd p99  B:wr MiB/s",
            "none           3988    14877 |   17170    101188      609.7",
            "!mq-deadline    4643    12386 |   43778    219152      208.4",
            "!bfq            4310    15008 |     522      1057       10.6",
            "kyber          4108    14746 |   23724    223347      373.3",
        ],
        observe=[
            (
                {"en": "Loop device defaults to none", "fa": "پیش‌فرض loop device برابر none است"},
                {
                    "en": "BLK_MQ_F_NO_SCHED_BY_DEFAULT (loop.c L2042)",
                    "fa": "BLK_MQ_F_NO_SCHED_BY_DEFAULT (loop.c L2042)",
                },
            ),
            (
                {"en": "mq-deadline: worst reader latency in B", "fa": "mq-deadline: بدترین تأخیر خواننده در B"},
                {
                    "en": "16 x 1 MiB write batches before each read",
                    "fa": "دسته‌های ۱۶تایی write یک مگابایتی پیش از هر read",
                },
            ),
            (
                {"en": "bfq can make the reader fast", "fa": "bfq می‌تواند خواننده را سریع کند"},
                {
                    "en": "idling: p50 0.5 ms, writer 10.6 MiB/s (run 2)",
                    "fa": "idling: p50 برابر 0.5 ms، نویسنده 10.6 MiB/s (اجرای ۲)",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "bfq / kyber not listed", "fa": "bfq یا kyber در فهرست نیست"},
                {"en": "sudo modprobe bfq kyber-iosched", "fa": "sudo modprobe bfq kyber-iosched"},
            ),
            (
                {"en": "numbers jump between runs", "fa": "عددها بین اجراها جابه‌جا می‌شوند"},
                {
                    "en": "shared VM + host cache: repeat, compare shapes",
                    "fa": "VM مشترک + cache میزبان: تکرار کنید و شکل را مقایسه کنید",
                },
            ),
            (
                {"en": "Invalid argument writing scheduler", "fa": "Invalid argument هنگام نوشتن scheduler"},
                {"en": "name not in the bracket list", "fa": "نام در فهرست داخل کروشه نیست"},
            ),
        ],
        ext={
            "en": "Under bfq, put the writer in a cgroup with io.bfq.weight 10 and the reader in one with 1000. Does the reader's p99 improve over plain bfq? What does mq-deadline do with the same cgroups?",
            "fa": "زیر bfq نویسنده را در cgroupی با io.bfq.weight برابر ۱۰ و خواننده را در cgroupی با ۱۰۰۰ بگذارید. آیا p99 خواننده نسبت به bfq ساده بهتر می‌شود؟ mq-deadline با همین cgroupها چه می‌کند؟",
        },
        captured=CAP,
    ),
    dict(
        slug="05-io-uring-copy",
        num="05.5",
        title={"en": "read()/write() loop vs io_uring", "fa": "حلقهٔ read()/write() در برابر io_uring"},
        goal={
            "en": "Copy the same 512 MiB file both ways and compare syscalls, time, and where the kernel did the work.",
            "fa": "یک فایل ۵۱۲ مگابایتی را به هر دو روش کپی کنید و تعداد syscall، زمان و محل انجام کار در کرنل را مقایسه کنید.",
        },
        where={"en": "Lab VM (liburing-dev)", "fa": "VM آزمایشگاه (liburing-dev)"},
        setup_cards=[
            (
                "r-user",
                {"en": "copy_rw.c", "fa": "copy_rw.c"},
                {"en": "2 syscalls per 128 KiB block", "fa": "۲ syscall برای هر بلوک ۱۲۸ کیلوبایتی"},
            ),
            (
                "r-user",
                {"en": "copy_uring.c", "fa": "copy_uring.c"},
                {"en": "8 linked READ->WRITE pairs per enter", "fa": "۸ جفت READ->WRITE پیوندخورده در هر enter"},
            ),
            (
                "r-kernel",
                {"en": "Counters", "fa": "شمارنده‌ها"},
                {"en": "perf stat task-clock, strace -c", "fa": "perf stat task-clock و strace -c"},
            ),
            (
                "r-kernel",
                {"en": "Tracepoints", "fa": "tracepointها"},
                {"en": "io_uring:io_uring_queue_async_work", "fa": "io_uring:io_uring_queue_async_work"},
            ),
        ],
        steps=[
            "$ cd ~/work/05-filesystems-io/labs/05-io-uring-copy",
            "$ gcc -Wall -Wextra -O2 -o copy_uring copy_uring.c -luring",
            "$ ./copy_uring src.bin dst.bin 131072 8",
            "$ bash run.sh   # 1 perf stat  2 strace -c  3 bpftrace",
        ],
        expected=[
            "copy_rw:    8193 read/write syscalls, 0.438 s, 1168 MiB/s",
            "    211.11 msec task-clock   68 context-switches",
            "copy_uring: 512 io_uring_enter calls, 0.487 s, 1052 MiB/s",
            "!    410.58 msec task-clock   2066 context-switches",
            "== 3. io_uring tracepoints",
            "!@punted_to_io_wq[23]: 4096",
            "@submitted[23]: 4096",
            "@submitted[22]: 4096",
        ],
        observe=[
            (
                {"en": "16x fewer syscalls", "fa": "۱۶ برابر syscall کمتر"},
                {"en": "8193 read/write vs 512 io_uring_enter", "fa": "۸۱۹۳ read/write در برابر ۵۱۲ io_uring_enter"},
            ),
            (
                {"en": "Not faster at all", "fa": "اصلاً سریع‌تر نیست"},
                {
                    "en": "memcpy-bound; 2x CPU, 30x context switches",
                    "fa": "محدود به memcpy؛ ۲ برابر CPU و ۳۰ برابر context switch",
                },
            ),
            (
                {"en": "All 4096 writes went to io-wq", "fa": "هر ۴۰۹۶ write به io-wq رفت"},
                {"en": "ext4: FOP_BUFFER_RASYNC yes, WASYNC no", "fa": "ext4: FOP_BUFFER_RASYNC دارد، WASYNC ندارد"},
            ),
        ],
        pitfalls=[
            (
                {"en": "undefined reference to io_uring_*", "fa": "undefined reference to io_uring_*"},
                {"en": "-luring at the END of the gcc line", "fa": "-luring در انتهای خط gcc"},
            ),
            (
                {"en": "write failed: res=-125", "fa": "write failed: res=-125"},
                {"en": "-ECANCELED: linked read was short", "fa": "-ECANCELED: read پیوندخورده کوتاه بود"},
            ),
            (
                {"en": "io_uring_setup: EPERM", "fa": "io_uring_setup: EPERM"},
                {"en": "kernel.io_uring_disabled or seccomp", "fa": "kernel.io_uring_disabled یا seccomp"},
            ),
        ],
        ext={
            "en": "Add IORING_SETUP_SQPOLL and registered buffers (io_uring_register_buffers + read_fixed/write_fixed). How many io_uring_enter calls remain, and what does the iou-sqp thread cost in CPU?",
            "fa": "IORING_SETUP_SQPOLL و بافرهای ثبت‌شده (io_uring_register_buffers + read_fixed/write_fixed) را اضافه کنید. چند io_uring_enter باقی می‌ماند و نخ iou-sqp چقدر CPU مصرف می‌کند؟",
        },
        captured=CAP,
    ),
    dict(
        slug="06-ext4-crash",
        num="05.6",
        title={"en": "ext4 crash consistency with dm-flakey", "fa": "سازگاری ext4 پس از crash با dm-flakey"},
        goal={
            "en": "Cut the power under ext4 and see which writes survive: fsync'd, unsynced, and replace-by-rename.",
            "fa": "زیر ext4 برق را قطع کنید و ببینید کدام نوشتن‌ها می‌مانند: fsync‌شده، بدون sync و جایگزینی با rename.",
        },
        where={"en": "VM ONLY (device-mapper, sudo)", "fa": "فقط VM (device-mapper، sudo)"},
        setup_cards=[
            (
                "r-data",
                {"en": "Disk", "fa": "دیسک"},
                {"en": "256 MiB loop file, mkfs.ext4", "fa": "فایل loop با حجم ۲۵۶ مگابایت، mkfs.ext4"},
            ),
            (
                "r-kernel",
                {"en": "dm-flakey", "fa": "dm-flakey"},
                {"en": "table UP -> table DROP (drop_writes)", "fa": "جدول UP -> جدول DROP (drop_writes)"},
            ),
            (
                "r-user",
                {"en": "Writes", "fa": "نوشتن‌ها"},
                {"en": "A: fsync · B: none · config: tmp + mv", "fa": "A: fsync · B: هیچ · config: tmp + mv"},
            ),
            (
                "r-kernel",
                {"en": "Recovery", "fa": "بازیابی"},
                {"en": "e2fsck -n, then mount = journal replay", "fa": "e2fsck -n و سپس mount = replay ژورنال"},
            ),
        ],
        steps=[
            "$ cd ~/work/05-filesystems-io/labs/06-ext4-crash",
            "$ sudo dmsetup targets | grep flakey",
            "$ bash crash-demo.sh                  # data=ordered",
            "$ MODE=writeback bash crash-demo.sh",
        ],
        expected=[
            "== mounted: rw,relatime,data=ordered",
            "== before the crash:",
            "  A 19 bytes   B 21 bytes   config: new contents",
            "== kernel log at remount (journal replay):",
            "!  EXT4-fs (dm-0): recovery complete",
            "== after the crash:",
            "!  A        19 bytes: A: written + fsync",
            "!  B       MISSING",
            "  config   13 bytes: old contents",
        ],
        observe=[
            (
                {"en": "fsync'd file survives", "fa": "فایل fsync‌شده می‌ماند"},
                {"en": "its transaction was committed", "fa": "تراکنش آن commit شده بود"},
            ),
            (
                {"en": "Unsynced file is gone", "fa": "فایل بدون sync از بین رفته"},
                {"en": "B: not even an empty file", "fa": "B: حتی یک فایل خالی هم نمانده"},
            ),
            (
                {"en": "Filesystem is consistent", "fa": "فایل‌سیستم سازگار است"},
                {"en": "replay on mount, no fsck needed", "fa": "replay هنگام mount، بدون نیاز به fsck"},
            ),
        ],
        pitfalls=[
            (
                {"en": "Invalid argument from dmsetup", "fa": "Invalid argument از dmsetup"},
                {"en": "sudo modprobe dm-flakey", "fa": "sudo modprobe dm-flakey"},
            ),
            (
                {"en": "device busy on remove", "fa": "device busy هنگام remove"},
                {"en": "umount first; dmsetup remove; losetup -d", "fa": "اول umount، بعد dmsetup remove و losetup -d"},
            ),
            (
                {"en": "everything survived", "fa": "همه چیز ماند"},
                {
                    "en": "dmsetup suspend without --nolockfs = fs freeze = sync",
                    "fa": "dmsetup suspend بدون --nolockfs یعنی freeze و sync",
                },
            ),
        ],
        ext={
            "en": "Fix the app: make 'config' survive with the new contents (tmp + fsync + rename + fsync dir). Then repeat with data=journal and explain any difference.",
            "fa": "برنامه را درست کنید تا config با محتوای جدید بماند (tmp + fsync + rename + fsync پوشه). سپس با data=journal تکرار کنید و تفاوت را توضیح دهید.",
        },
        captured=CAP,
    ),
]
