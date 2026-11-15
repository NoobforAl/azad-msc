<div dir="rtl">

# یادداشت‌های ماژول ۰۲ — فهرست

> نسخهٔ انگلیسی: [`INDEX.en.md`](INDEX.en.md) · درس: [`../lesson.fa.md`](../lesson.fa.md)

یادداشت‌ها را به ترتیب بخوانید. هر یادداشت همان ۷ بخش را دارد: خلاصه، توضیح، نمودار، مثال عملی (کد واقعی یا خروجی واقعی VM)، دام‌ها، نکته‌های کلیدی امتحانی و پیوندها.

| # | یادداشت | کد اصلی کرنل | آزمایش‌ها | آزمون |
|---|---|---|---|---|
| ۰۱ | [ساختار `task_struct`](01-task-struct-anatomy.fa.md) | `include/linux/sched.h` خط 815، `fs/proc/array.c` | ۰۲.۱، ۰۲.۶ | Q1، Q7 |
| ۰۲ | [fork، vfork و پرچم‌های clone](02-fork-vfork-clone-flags.fa.md) | `kernel/fork.c`: `kernel_clone()`، `copy_process()`، `copy_mm()` | ۰۲.۱، ۰۲.۲ | Q2، Q8 |
| ۰۳ | [execve و بارگذاری ELF](03-execve-and-elf-loading.fa.md) | `fs/exec.c`: `bprm_execve()`، `begin_new_exec()`؛ `fs/binfmt_elf.c` | ۰۲.۱ | Q3، Q9 |
| ۰۴ | [وضعیت‌ها، exit و wait](04-process-states-and-wait.fa.md) | `kernel/exit.c`: `exit_notify()`؛ `kernel/signal.c`: `do_notify_parent()` | ۰۲.۱ | Q4، Q14 |
| ۰۵ | [نخ‌ها یک mm مشترک دارند](05-threads-share-an-mm.fa.md) | تعیین `tgid` در `kernel/fork.c`؛ G/M/P در runtime زبان Go | ۰۲.۲، ۰۲.۶ | Q1، Q12 |
| ۰۶ | [کلاس‌های زمان‌بندی](06-scheduling-classes.fa.md) | `DEFINE_SCHED_CLASS` در `kernel/sched/sched.h`، `SCHED_DATA` در `vmlinux.lds.h` | ۰۲.۵ | Q5، Q13 |
| ۰۷ | [EEVDF](07-eevdf.fa.md) | `kernel/sched/fair.c`: `pick_eevdf()`، `update_deadline()` | ۰۲.۵ | Q6، Q13 |
| ۰۸ | [IPC: pipe، shm و سوکت](08-ipc-pipes-shm-sockets.fa.md) | `fs/pipe.c`: `anon_pipe_read()`؛ `ipc/shm.c`: `newseg()` | ۰۲.۱، ۰۲.۳ | Q10، Q11 |

خود context switch (`context_switch()` و `switch_to()`) در بخش ۲.۸ درس، بخش ۶ مرور کد و آزمایش ۰۲.۳ آمده است؛ جزئیات سطح رجیستر در یادداشت ۰۵ ماژول ۰۱ است.

</div>
