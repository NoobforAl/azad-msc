# منابع بیشتر برای مطالعه

منتخب از فهرست‌های «awesome-os» در GitHub. همهٔ لینک‌ها در 2026-11-15 باز و بررسی شده‌اند (`python _shared/tools/add_references.py --check` دوباره بررسی می‌کند). همین موارد در آخرین اسلاید هر درس هم آمده‌اند.

## 00-setup

- **[The Linux Kernel documentation](https://www.kernel.org/doc/html/latest/)** (مستندات): مستندات رسمی کرنل: راهنمای مدیریت، APIهای هسته و یادداشت‌های هر subsystem.
- **[virtme-ng](https://github.com/arighi/virtme-ng)** (ابزار): ساخت و اجرای کرنل درون یک snapshot مجازی از سیستم فعلی (نیاز به میزبان Linux).
- **[A Beginner's Guide to Linux Kernel Development (LFD103)](https://training.linuxfoundation.org/training/a-beginners-guide-to-linux-kernel-development-lfd103/)** (دوره): دورهٔ Linux Foundation برای شروع توسعهٔ کرنل.
- **[Bug hunting (kernel docs)](https://www.kernel.org/doc/html/latest/admin-guide/bug-hunting.html)** (مستندات): راهنمای مدیریت کرنل دربارهٔ پیدا کردن باگ.
- **[Bisecting a regression (kernel docs)](https://www.kernel.org/doc/html/latest/admin-guide/bug-bisect.html)** (مستندات): پیدا کردن دقیق commitی که چیزی را خراب کرده.
- **[kworkflow (kw)](https://github.com/kworkflow/kworkflow)** (ابزار): ابزاری که هزینهٔ راه‌اندازی محیط توسعهٔ کرنل را کم می‌کند.

## 01-architecture

- **[linux-insides](https://0xax.gitbooks.io/linux-insides/content/)** (کتاب): مرور کتاب‌گونهٔ درون Linux: boot، interrupt، system call و حافظه.
- **[Interactive map of Linux kernel](https://makelinux.github.io/kernel/map/)** (مستندات): یک نمودار کلیک‌پذیر از subsystemهای کرنل و ارتباط آن‌ها.
- **[Linux system calls table](https://gpages.juszkiewicz.com.pl/syscalls-table/syscalls.html)** (مستندات): شمارهٔ system callها برای همهٔ معماری‌ها، کنار هم.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (کتاب): فصل‌های «Operating system organization» و «Traps and device drivers».
- **[Exokernel: An Operating System Architecture for Application-Level Resource Management](https://pdos.csail.mit.edu/6.828/2008/readings/engler95exokernel.pdf)** (مقاله): ۱۹۹۵: سخت‌افزار را در اختیار بگذار و بگذار کتابخانه‌ها خودِ OS باشند؛ نقطهٔ مقابل کرنل بزرگ.
- **[seL4: Formal Verification of an OS Kernel](https://www.sigops.org/s/conferences/sosp/2009/papers/klein-sosp09.pdf)** (مقاله): SOSP ‏'09: کرنلی کوچک که درستی‌اش اثبات شده؛ microkernel در اوج.

## 02-processes-threads

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (کتاب): بخش اول، virtualization: process، scheduling و address space.
- **[Think OS (Allen B. Downey)](https://greenteapress.com/wp/think-os/)** (کتاب): مقدمه‌ای کوتاه بر سیستم‌عامل که برای برنامه‌نویس‌ها نوشته شده است.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (کتاب): فصل «Scheduling».
- **[Linux Kernel Teaching](https://linux-kernel-labs.github.io/refs/heads/master/)** (دوره): درس‌نامه و آزمایشگاه دانشگاهی دربارهٔ کرنل Linux.
- **[linux-insides](https://0xax.gitbooks.io/linux-insides/content/)** (کتاب): مرور کتاب‌گونهٔ درون Linux: boot، interrupt، system call و حافظه.
- **[Tracing Linux kernel with retsnoop](https://nakryiko.com/posts/retsnoop-intro/)** (نوشته): نوشته‌ای دربارهٔ ردیابی فراخوانی و بازگشت توابع کرنل با یک ابزار BPF.

## 03-concurrency

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (کتاب): بخش دوم، concurrency: lock، condition variable، semaphore و باگ‌ها.
- **[Think OS (Allen B. Downey)](https://greenteapress.com/wp/think-os/)** (کتاب): مقدمه‌ای کوتاه بر سیستم‌عامل که برای برنامه‌نویس‌ها نوشته شده است.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (کتاب): فصل‌های «Locking» و «Concurrency revisited».
- **[Corey: An Operating System for Many Cores](https://www.usenix.org/legacy/events/osdi08/tech/full_papers/boyd-wickizer/boyd_wickizer.pdf)** (مقاله): OSDI ‏'08: طراحی OS برای چندهسته‌های زیاد، با کنترل اشتراک‌گذاری توسط برنامه‌ها.
- **[The Multikernel: A new OS architecture for scalable multicore systems](https://www.sigops.org/s/conferences/sosp/2009/papers/baumann-sosp09.pdf)** (مقاله): SOSP ‏'09: یک ماشین چندهسته‌ای را شبکه‌ای از هسته‌ها بدان که پیام رد و بدل می‌کنند.
- **[Linux Kernel Teaching](https://linux-kernel-labs.github.io/refs/heads/master/)** (دوره): درس‌نامه و آزمایشگاه دانشگاهی دربارهٔ کرنل Linux.

## 04-memory

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (کتاب): بخش اول، virtualization: address space، paging، TLB و swapping.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (کتاب): فصل «Page tables».
- **[linux-insides](https://0xax.gitbooks.io/linux-insides/content/)** (کتاب): مرور کتاب‌گونهٔ درون Linux: boot، interrupt، system call و حافظه.
- **[Linux Kernel Teaching](https://linux-kernel-labs.github.io/refs/heads/master/)** (دوره): درس‌نامه و آزمایشگاه دانشگاهی دربارهٔ کرنل Linux.
- **[Dune: Safe User-level Access to Privileged CPU Features](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-117.pdf)** (مقاله): OSDI ‏'12: دسترسی امن یک process به قابلیت‌های privileged پردازنده با کمک سخت‌افزار مجازی‌سازی.
- **[The Linux Kernel documentation](https://www.kernel.org/doc/html/latest/)** (مستندات): مستندات رسمی کرنل: راهنمای مدیریت، APIهای هسته و یادداشت‌های هر subsystem.

## 05-filesystems-io

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (کتاب): بخش سوم، persistence: دستگاه‌های I/O، file system و journaling.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (کتاب): فصل‌های «File system» و «Traps and device drivers».
- **[The Linux Kernel Module Programming Guide](https://sysprog21.github.io/lkmpg/)** (کتاب): راهنمای عملی نوشتن kernel module؛ نقطهٔ شروع driverها.
- **[The Linux Kernel documentation](https://www.kernel.org/doc/html/latest/)** (مستندات): مستندات رسمی کرنل: راهنمای مدیریت، APIهای هسته و یادداشت‌های هر subsystem.
- **[Arrakis: The Operating System is the Control Plane](https://www.usenix.org/conference/osdi14/technical-sessions/presentation/peter)** (مقاله): OSDI ‏'14: کرنل از مسیر داده‌ی I/O کنار می‌رود و فقط آن را کنترل می‌کند.
- **[The Demikernel Datapath OS Architecture for Microsecond-scale Datacenter Systems](https://irenezhang.net/papers/demikernel-sosp21.pdf)** (مقاله): SOSP ‏'21: معماری OS برای I/O در مقیاس میکروثانیه در دیتاسنترها.

## 06-distributed-virtualization

- **[Unikernels: Library Operating Systems for the Cloud](https://anil.recoil.org/papers/2013-asplos-mirage.pdf)** (مقاله): ASPLOS ‏'13: یک برنامه به‌همراه library OS که به‌صورت یک image ابری ساخته می‌شود.
- **[Unikraft](https://github.com/unikraft/unikraft)** (ابزار): پروژه‌ای برای ساخت unikernelهای تخصصی و سریع.
- **[LegoOS: A Disseminated, Distributed OS for Hardware Resource Disaggregation](https://www.usenix.org/system/files/osdi18-shan.pdf)** (مقاله): OSDI ‏'18: یک OS که بر اساس نوع منبع سخت‌افزاری بین چند ماشین تقسیم شده است.
- **[Dune: Safe User-level Access to Privileged CPU Features](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-117.pdf)** (مقاله): OSDI ‏'12: دسترسی امن یک process به قابلیت‌های privileged پردازنده با کمک سخت‌افزار مجازی‌سازی.
- **[The Multikernel: A new OS architecture for scalable multicore systems](https://www.sigops.org/s/conferences/sosp/2009/papers/baumann-sosp09.pdf)** (مقاله): SOSP ‏'09: یک ماشین چندهسته‌ای را شبکه‌ای از هسته‌ها بدان که پیام رد و بدل می‌کنند.

## 07-realtime-research

- **[SOSP: Symposium on Operating Systems Principles](https://sosp.org/)** (کنفرانس): کنفرانس شاخص پژوهش در سیستم‌عامل.
- **[USENIX conferences (OSDI, ATC)](https://www.usenix.org/conferences)** (کنفرانس): خانهٔ OSDI و ATC؛ دو رویداد اصلی دیگر پژوهش OS.
- **[ASPLOS](https://www.asplos-conference.org/)** (کنفرانس): جایی که پژوهش OS با معماری و زبان‌های برنامه‌نویسی تلاقی می‌کند.
- **[HotOS: Workshop on Hot Topics in Operating Systems](https://sigops.org/s/conferences/hotos/)** (کنفرانس): مقاله‌های کوتاه و آینده‌نگر دربارهٔ مسیر پژوهش در OS.
- **[The benefits and costs of writing a POSIX kernel in a high-level language](https://www.usenix.org/conference/osdi18/presentation/cutler)** (مقاله): OSDI ‏'18: کرنلی که با C نوشته نشده چه چیزی به‌دست می‌آورد و چه چیزی از دست می‌دهد.
- **[Multiprogramming a 64 kB Computer Safely and Efficiently](https://www.tockos.org/assets/papers/tock-sosp2017.pdf)** (مقاله): SOSP ‏'17 (Tock): اجرای امن چند برنامه روی یک میکروکنترلر بسیار کوچک.
- **[Linux Plumbers Conference](https://lpc.events/)** (کنفرانس): جایی که توسعه‌دهنده‌های کرنل کارشان را ارائه و بحث می‌کنند.

## فهرست‌هایی که بررسی شد

| فهرست | استفاده | دلیل |
|---|---|---|
| [jubalh/awesome-os](https://github.com/jubalh/awesome-os) | بله | بیشترین استفاده: کتاب‌ها، راهنمای مخصوص Linux، دیباگ کرنل، ابزارها و کنفرانس‌ها. |
| [penberg/awesome-os](https://github.com/penberg/awesome-os) | بله | برای بخش پژوهشی: مقاله‌های کلاسیک OS و کنفرانس‌های اصلی پژوهش OS. |
| [Francesco601/AWESOME-Operating-System-Resources](https://github.com/Francesco601/AWESOME-Operating-System-Resources) | خیر | استفاده نشد: بیشتر فهرستی از OSهای سرگرمی و آموزش‌های «ساخت از صفر» است. این درس به‌جای آن، کرنل‌های واقعی (Linux و OpenBSD) را می‌خواند. |
| [leap0x7b/awesome-osdev](https://github.com/leap0x7b/awesome-osdev) | خیر | استفاده نشد: دربارهٔ نوشتن یک OS سرگرمی جدید (bootloader و کرنل اسباب‌بازی) است و خارج از این درس قرار دارد. |
| [ishandutta2007/Awesome-Operating-Systems](https://github.com/ishandutta2007/Awesome-Operating-Systems) | خیر | استفاده نشد: فهرستی از سیستم‌عامل‌ها با بخش‌های معرفیِ بازاری و منابع آموزشی اندک. |

یادداشت: لینک مقالهٔ «The UNIX Time-Sharing System» در penberg/awesome-os (dsf.berkeley.edu) دیگر کار نمی‌کند، پس نیامده است.
