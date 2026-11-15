<div dir="rtl">

# ۰۷ — فهرست یادداشت‌ها (Real-Time و موضوعات پژوهشی)

به ترتیب بخوانید؛ هر یادداشت هفت بخش دارد (خلاصه، توضیح، نمودار، مثال کاربردی، دام‌ها، نکته‌های کلیدی، پیوندها). نسخهٔ انگلیسی: [`INDEX.en.md`](INDEX.en.md).

| # | یادداشت | فایل‌های اصلی کرنل | آزمایش | آزمون |
|---|---|---|---|---|
| ۰۱ | [real-time سخت، نیمه‌سخت و نرم؛ WCET و latency](01-hard-soft-realtime-wcet.fa.md) | `kernel/sched/core.c` (`try_to_wake_up` و `__schedule`) | ۰۱ | ۱، ۲، ۷ |
| ۰۲ | [زمان‌بندی RT: ‏RMS، ‏EDF و `SCHED_DEADLINE`](02-rt-scheduling-rms-edf-deadline.fa.md) | `kernel/sched/deadline.c` و `Documentation/scheduler/sched-deadline.rst` | ۰۱ (تکمیلی) | ۳، ۸، ۱۲ |
| ۰۳ | [Priority inversion و inheritance (‏Mars Pathfinder)](03-priority-inversion-inheritance.fa.md) | `kernel/locking/rtmutex.c`، ‏`kernel/futex/pi.c`، ‏`kernel/sched/core.c` | ۰۲ | ۴، ۹، ۱۳ |
| ۰۴ | [‏`PREEMPT_RT`](04-preempt-rt.fa.md) | `kernel/Kconfig.preempt`، ‏`kernel/locking/spinlock_rt.c`، ‏`init/Makefile` | ۰۱ | ۵، ۱۰، O1 |
| ۰۵ | [‏seccomp-BPF، ‏LSM و Landlock](05-seccomp-lsm-landlock.fa.md) | `kernel/seccomp.c`، ‏`kernel/entry/syscall-common.c`، ‏`security/landlock/` | ۰۳، ۰۴ | ۶، ۱۱، ۱۴، O3 |
| ۰۶ | [چطور مقالهٔ پژوهشی سیستم‌عامل بخوانیم](06-reading-os-papers.fa.md) | `kernel/sched/fair.c` و `include/linux/dcache.h` (نگاشت مقاله) | ۰۵ | ۱۵، O2 |

زمان کل خواندن حدود ۲٫۵ ساعت. پیش‌نیاز: یادداشت‌های ماژول ۰۲ دربارهٔ کلاس‌های زمان‌بندی و یادداشت‌های ماژول ۰۳ دربارهٔ futex و mutex.

</div>
