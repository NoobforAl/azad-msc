# Lab-deck content for 00-setup. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced OS · 00 Setup", "fa": "سیستم‌عامل پیشرفته · ۰۰ راه‌اندازی"}

LABS = [
    dict(
        slug="01-create-vm",
        num="00.1",
        title={"en": "Create the lab VM", "fa": "ساخت VM آزمایشگاه"},
        goal={
            "en": "A disposable Ubuntu 24.04 VM with a serial console and a snapshot you can roll back to in 10 seconds.",
            "fa": "یک VM یک‌بارمصرف با Ubuntu 24.04، کنسول سریال و snapshotای که در ۱۰ ثانیه به آن برگردید.",
        },
        where={"en": "Host (Ubuntu server)", "fa": "میزبان (سرور اوبونتو)"},
        setup_cards=[
            (
                "r-hardware",
                {"en": "Host checks", "fa": "بررسی میزبان"},
                {"en": "vmx/svm flag · /dev/kvm · nesting", "fa": "پرچم vmx/svm · /dev/kvm · nesting"},
            ),
            (
                "r-data",
                {"en": "Disk", "fa": "دیسک"},
                {"en": "qcow2 overlay on the cloud image", "fa": "overlay از نوع qcow2 روی image ابری"},
            ),
            (
                "r-user",
                {"en": "First boot", "fa": "اولین بوت"},
                {"en": "cloud-init: user, SSH key, ttyS0", "fa": "cloud-init: کاربر، کلید SSH، ttyS0"},
            ),
            (
                "r-kernel",
                {"en": "Safety net", "fa": "تور ایمنی"},
                {"en": "snapshot 'fresh' after cloud-init", "fa": "snapshot به نام fresh پس از cloud-init"},
            ),
        ],
        steps=[
            "# on the server",
            "$ cd 00-setup/labs/01-create-vm",
            "$ bash create-vm.sh",
            "# bigger VM:",
            "$ VCPUS=8 RAM_MB=16384 bash create-vm.sh",
            "",
            "$ ssh $USER@<vm-ip>",
            "$ sudo virsh snapshot-list aos-lab",
        ],
        expected=[
            "ok: nested virtualization enabled on host",
            "...",
            "!VM IP: 192.168.122.57",
            "waiting for cloud-init to finish...",
            "!Domain snapshot fresh created",
            "Domain 'aos-lab' started",
        ],
        observe=[
            (
                {"en": "One process, many threads", "fa": "یک پردازه، چند نخ"},
                {"en": "ps -o pid,nlwp,cmd -C qemu-system-x86_64", "fa": "ps -o pid,nlwp,cmd -C qemu-system-x86_64"},
            ),
            (
                {"en": "Copy-on-write disk", "fa": "دیسک copy-on-write"},
                {"en": "ls -l /var/lib/libvirt/images/", "fa": "ls -l /var/lib/libvirt/images/"},
            ),
            (
                {"en": "Boot messages", "fa": "پیام‌های بوت"},
                {"en": "sudo virsh console aos-lab", "fa": "sudo virsh console aos-lab"},
            ),
        ],
        pitfalls=[
            (
                {"en": "no VT-x/AMD-V flag", "fa": "پرچم VT-x/AMD-V نیست"},
                {
                    "en": "enable in BIOS, or use your own PC (VPS)",
                    "fa": "در BIOS روشن کنید یا روی کامپیوتر خودتان (VPS)",
                },
            ),
            (
                {"en": "no IP after 5 min", "fa": "بعد از ۵ دقیقه IP نیست"},
                {"en": "virsh net-start default", "fa": "virsh net-start default"},
            ),
            (
                {"en": "snapshot fails with UEFI", "fa": "snapshot با UEFI خطا می‌دهد"},
                {"en": "keep BIOS boot (script default)", "fa": "بوت BIOS (پیش‌فرض اسکریپت) را نگه دارید"},
            ),
        ],
        ext={
            "en": "Make a second throw-away VM from the same base in under a minute, without re-running cloud-init, and prove it is independent of aos-lab.",
            "fa": "در کمتر از یک دقیقه و بدون اجرای دوبارهٔ cloud-init یک VM یک‌بارمصرف دوم از همان پایه بسازید و ثابت کنید از aos-lab مستقل است.",
        },
    ),
    dict(
        slug="02-install-tools",
        num="00.2",
        title={"en": "Install and verify the tool set", "fa": "نصب و آزمودن ابزارها"},
        goal={
            "en": "Every tracing and debugging tool works against the running kernel, on the server and in the VM.",
            "fa": "همهٔ ابزارهای ردیابی و اشکال‌زدایی روی کرنل در حال اجرا کار کنند؛ هم روی سرور و هم در VM.",
        },
        where={"en": "Server and VM", "fa": "سرور و VM"},
        setup_cards=[
            (
                "r-kernel",
                {"en": "Tracing", "fa": "ردیابی"},
                {
                    "en": "strace · perf · bpftrace · bcc · trace-cmd",
                    "fa": "strace · perf · bpftrace · bcc · trace-cmd",
                },
            ),
            (
                "r-user",
                {"en": "Inspection", "fa": "بررسی"},
                {"en": "lsof · sysstat · numactl · hwloc", "fa": "lsof · sysstat · numactl · hwloc"},
            ),
            (
                "r-data",
                {"en": "Libraries", "fa": "کتابخانه‌ها"},
                {"en": "liburing · libseccomp · libbpf", "fa": "liburing · libseccomp · libbpf"},
            ),
            (
                "r-hardware",
                {"en": "Kernel match", "fa": "هماهنگی با کرنل"},
                {"en": "linux-tools-$(uname -r) · BTF", "fa": "linux-tools-$(uname -r) · BTF"},
            ),
        ],
        steps=[
            "$ bash install-tools.sh",
            "$ bash verify-tools.sh; echo $?",
            "",
            "# smoke test on the real kernel",
            "$ strace -c -f ls / >/dev/null",
            "$ perf stat -e task-clock,page-faults ls >/dev/null",
            "$ sudo trace-cmd record -p function_graph \\",
            "    -g vfs_read -F cat /etc/hostname",
        ],
        expected=[
            "$ bash verify-tools.sh",
            "== tools",
            "  OK      gcc            /usr/bin/gcc",
            "  ...",
            "== perf works against the running kernel",
            "!  OK      perf stat      6.18.63-061863-generic",
            "== kernel features",
            "  OK      CONFIG_DEBUG_INFO_BTF bpftrace struct access",
            "  WARN    CONFIG_PREEMPT_RT real-time kernel (not set)",
            "  WARN    /dev/kvm       absent (no nesting)",
            "!all required tools present",
        ],
        captured={
            "en": "aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15",
            "fa": "aos-lab (VirtualBox، Ubuntu 24.04، لینوکس 6.18.63)، ۲۰۲۶-۱۱-۱۵",
        },
        observe=[
            (
                {"en": "Most frequent syscall of ls", "fa": "پرتکرارترین syscall در ls"},
                {"en": "the dynamic loader: mmap, openat (M1)", "fa": "loader پویا: mmap و openat (ماژول ۱)"},
            ),
            (
                {"en": "~100 page faults for ls", "fa": "حدود ۱۰۰ page fault برای ls"},
                {"en": "demand paging of binary + libs (M4)", "fa": "demand paging باینری و کتابخانه‌ها (ماژول ۴)"},
            ),
            (
                {"en": "vfs_read → ->read_iter()", "fa": "vfs_read ← ->read_iter()"},
                {"en": "the call chain of Module 5", "fa": "زنجیرهٔ فراخوانی ماژول ۵"},
            ),
        ],
        pitfalls=[
            (
                {"en": "perf not found for kernel X", "fa": "perf not found for kernel X"},
                {"en": "apt install linux-tools-$(uname -r)", "fa": "apt install linux-tools-$(uname -r)"},
            ),
            (
                {"en": "bpftrace: BTF error", "fa": "خطای BTF در bpftrace"},
                {"en": "kernel without DEBUG_INFO_BTF → lab 03", "fa": "کرنل بدون DEBUG_INFO_BTF ← آزمایش ۰۳"},
            ),
            (
                {"en": "perf_event_open: paranoid", "fa": "perf_event_open: paranoid"},
                {"en": "sysctl kernel.perf_event_paranoid=1", "fa": "sysctl kernel.perf_event_paranoid=1"},
            ),
        ],
        ext={
            "en": "One bpftrace line: every 2 s print the top 5 tasks by context switches out (sched:sched_switch, prev_comm), then clear. Run stress-ng --cpu 4 --cpu-method int64 next to it and explain.",
            "fa": "یک خط bpftrace: هر ۲ ثانیه ۵ task اول را بر اساس تعداد context switch خروجی (sched:sched_switch با کلید prev_comm) چاپ و map را پاک کنید. کنارش stress-ng --cpu 4 --cpu-method int64 اجرا کنید و نتیجه را توضیح دهید.",
        },
    ),
    dict(
        slug="03-build-kernel",
        num="00.3",
        title={"en": "Build and boot v6.18.63 in the VM", "fa": "ساخت و بوت v6.18.63 در VM"},
        goal={
            "en": "The VM boots exactly the kernel whose source you read, with BTF, ftrace, kallsyms and debugfs on.",
            "fa": "VM دقیقاً با کرنلی بوت شود که سورسش را می‌خوانید؛ با BTF، ftrace، kallsyms و debugfs روشن.",
        },
        where={"en": "VM only — snapshot first", "fa": "فقط VM — اول snapshot"},
        setup_cards=[
            (
                "r-data",
                {"en": "Source", "fa": "سورس"},
                {"en": "full shallow clone of tag v6.18.63", "fa": "clone کم‌عمق و کامل از tag v6.18.63"},
            ),
            (
                "r-kernel",
                {"en": "Config", "fa": "پیکربندی"},
                {
                    "en": "Ubuntu config + localmodconfig + BTF/ftrace",
                    "fa": "پیکربندی اوبونتو + localmodconfig + BTF/ftrace",
                },
            ),
            (
                "r-user",
                {"en": "Flavors", "fa": "گونه‌ها"},
                {"en": "lab · --rt (M7) · --lockdep (M3)", "fa": "lab · --rt (ماژول ۷) · --lockdep (ماژول ۳)"},
            ),
            (
                "r-hardware",
                {"en": "Guard", "fa": "محافظ"},
                {"en": "refuses to run on bare metal", "fa": "روی سخت‌افزار واقعی اجرا نمی‌شود"},
            ),
        ],
        steps=[
            "# host: snapshot first",
            "$ sudo virsh snapshot-create-as aos-lab pre-kernel",
            "# inside the VM",
            "$ bash build-kernel.sh",
            "$ sudo reboot",
            "$ uname -r",
            "$ zgrep -E 'BTF|GRAPH_TRACER' /proc/config.gz",
        ],
        expected=[
            "real    27m41s",
            "installed 6.18.63-aos-lab. Reboot, then check ...",
            "",
            "$ uname -r",
            "!6.18.63-aos-lab",
            "CONFIG_DEBUG_INFO_BTF=y",
            "CONFIG_FUNCTION_GRAPH_TRACER=y",
        ],
        observe=[
            (
                {"en": "Four .deb packages", "fa": "چهار بستهٔ .deb"},
                {
                    "en": "image · headers · libc-dev · dbg (vmlinux)",
                    "fa": "image · headers · libc-dev · dbg (vmlinux)",
                },
            ),
            (
                {"en": "Build tree size", "fa": "حجم درخت build"},
                {"en": "du -sh . → 20+ GB, mostly debug info", "fa": "du -sh . ← بیش از ۲۰ گیگ، بیشتر اطلاعات debug"},
            ),
            (
                {"en": "RT marker", "fa": "نشانهٔ RT"},
                {
                    "en": "uname -v contains PREEMPT_RT (init/Makefile L30)",
                    "fa": "uname -v شامل PREEMPT_RT است (init/Makefile L30)",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "canonical-certs.pem missing", "fa": "canonical-certs.pem پیدا نمی‌شود"},
                {"en": 'SYSTEM_TRUSTED_KEYS="" (script does it)', "fa": 'SYSTEM_TRUSTED_KEYS="" (اسکریپت انجام می‌دهد)'},
            ),
            (
                {"en": "pahole is not available", "fa": "pahole موجود نیست"},
                {"en": "sudo apt install dwarves", "fa": "sudo apt install dwarves"},
            ),
            (
                {"en": "cc1 Killed", "fa": "cc1 Killed"},
                {"en": "out of RAM: lower -j or RAM_MB=16384", "fa": "کمبود حافظه؛ عدد -j را کم کنید یا RAM_MB=16384"},
            ),
        ],
        ext={
            "en": "Using only the running VM, prove the kernel is the source you read: do_syscall_64 in kallsyms, its (absent) ftrace entry, and gdb's line number from the -dbg vmlinux.",
            "fa": "فقط با VM در حال اجرا ثابت کنید کرنل همان سورسی است که می‌خوانید: do_syscall_64 در kallsyms، نبودنش در فهرست ftrace، و شمارهٔ خطی که gdb از vmlinux بستهٔ -dbg نشان می‌دهد.",
        },
    ),
]
