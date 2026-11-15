<div dir="rtl">

# یادداشت‌های ماژول ۰۳ — فهرست

> به ترتیب بخوانید. هر یادداشت همان ۷ بخش را دارد: خلاصه · توضیح · نمودار · مثال حل‌شده · حالت‌های مرزی · نکته‌های امتحان · پیوندها. نسخهٔ انگلیسی: [INDEX.en.md](INDEX.en.md).

| # | یادداشت | بخش درس | سورس اصلی کرنل (v6.18.63) | آزمایش | پرسش |
|---|---|---|---|---|---|
| ۰۱ | [Race condition و critical section](01-race-conditions-critical-sections.fa.md) | ۴.۱ | `READ_ONCE` و `WRITE_ONCE`، preemption و وقفه به‌عنوان منبع هم‌روندی | ۰۱ | Q1، Q11 |
| ۰۲ | [عملیات اتمی و مدل حافظهٔ C11](02-atomics-c11-memory-model.fa.md) | ۴.۲ | `atomic_long_try_cmpxchg_acquire()` و `smp_store_release()` | ۰۱، ۰۵ | Q2 |
| ۰۳ | [x86-TSO در برابر مدل‌های ضعیف‌تر؛ barrierها](03-x86-tso-and-barriers.fa.md) | ۴.۲ | `arch/x86/include/asm/barrier.h`، جفت `smp_mb()` در futex | ۰۵ | Q3، Q15 |
| ۰۴ | [Spinlock: از ticket تا MCS و qspinlock](04-spinlocks-qspinlock.fa.md) | ۴.۳ | `include/linux/spinlock.h` و `kernel/locking/qspinlock.c` | ۰۴ | Q4، Q8 |
| ۰۵ | [Mutex و optimistic spinning](05-mutex-optimistic-spinning.fa.md) | ۴.۳ | `kernel/locking/mutex.c` (`mutex_lock()` خط ۲۶۹) | ۰۴ | Q4، Q7 |
| ۰۶ | [Semaphore و condition variable](06-semaphores-condition-variables.fa.md) | ۴.۵ | `kernel/locking/semaphore.c` و `include/linux/wait.h` | ۰۲، ۰۳ | Q13، Q14 |
| ۰۷ | [Futex: تقسیم کار کاربر و کرنل](07-futex-user-kernel-split.fa.md) | ۴.۴ | `kernel/futex/syscalls.c`، `waitwake.c`، `core.c` | ۰۴ | Q9، Q10 |
| ۰۸ | [RCU (و SMR در OpenBSD)](08-rcu.fa.md) | ۴.۶ | `include/linux/rcupdate.h`، `kernel/rcu/tree.c`، `tree_plugin.h` | — | Q5 |
| ۰۹ | [Deadlock: شرط‌های Coffman، تشخیص، lockdep](09-deadlock-coffman-lockdep.fa.md) | ۴.۷ | `kernel/locking/lockdep.c` (`check_noncircular()`) | ۰۶ | Q6، Q12 |
| ۱۰ | [مسئله‌های کلاسیک](10-classic-problems.fa.md) | ۴.۵ | `kernel/locking/rwsem.c` و `percpu-rwsem.c` | ۰۲، ۰۳ | Q13، Q14 |

مسیر پیشنهادی: ۰۱ ← ۰۲ ← ۰۳ (مدل حافظه)، بعد ۰۴ ← ۰۵ ← ۰۷ (پیاده‌سازی قفل‌ها از پایین به بالا)، بعد ۰۶ ← ۱۰ (منتظرماندن برای شرط)، بعد ۰۸ (خواندن بی‌قفل) و ۰۹ (وقتی همه‌چیز خراب می‌شود).

</div>
