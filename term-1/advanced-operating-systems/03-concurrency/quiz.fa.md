<div dir="rtl">

# ۰۳ — آزمونک: هم‌روندی و همگام‌سازی

> ۱۵ پرسش: ۶ مفهومی (۴۰٪)، ۵ خواندن کد یا خروجی (حدود ۳۰٪)، ۴ اشکال‌زدایی یا طراحی (حدود ۳۰٪)، و ۳ پرسش امتحان شفاهی. پاسخ‌ها در پایان آمده‌اند. نسخهٔ انگلیسی: [`quiz.en.md`](quiz.en.md).
> کدها از Linux **v6.18.63** هستند؛ خروجی‌ها اجرای واقعی روی `aos-lab` (Linux 6.18.63، مهمان VirtualBox با ۸ vCPU، 2026-11-15) هستند.

## مفهومی

**Q1.** *race condition*، *data race* و *critical section* را تعریف کنید. مثالی از race conditionی بزنید که data race **نیست**.

**Q2.** تولیدکننده `data = 42;` را می‌نویسد و بعد `ready = 1;`. مصرف‌کننده با `while (!ready);` می‌چرخد و بعد `data` را می‌خواند. با atomicهای C11، روی `ready` (store و load) کدام memory order لازم است و چرا `relaxed` کافی نیست، حتی روی ماشینی که اتفاقاً درست کار می‌کند؟

**Q3.** کدام‌یک از این جابه‌جایی‌ها را یک CPU دیگر روی x86-64 می‌تواند ببیند؟ (الف) store→store (ب) load→load (ج) store و بعد load از آدرس دیگر (د) load و بعد store. ساختار سخت‌افزاری مسئول را نام ببرید.

**Q4.** سه دلیل بیاورید که چرا `spin_lock()` کرنل نباید روی فراخوانی‌ای که ممکن است بخوابد نگه داشته شود، و بگویید `__raw_spin_lock()` پیش از دست‌زدن به کلمهٔ قفل چه می‌کند و چرا.

**Q5.** در RCU، *grace period* چیست و *quiescent state* چیست؟ چرا نویسنده می‌تواند پس از برگشتن `synchronize_rcu()` نسخهٔ قدیم را آزاد کند، با این‌که خواننده‌ها هیچ قفلی نگرفته‌اند؟

**Q6.** چهار شرط Coffman را بگویید. برای هر کدام یک روش عملی که آن را می‌شکند بیاورید، و بگویید lockdep برای گرفتن کدام طراحی شده است.

## خواندن کد یا خروجی

**Q7.** هر خط را توضیح دهید:

</div>

```c
// linux/kernel/locking/mutex.c · __mutex_trylock_fast() · v6.18.63 · L150-161
static __always_inline bool __mutex_trylock_fast(struct mutex *lock)
{
	unsigned long curr = (unsigned long)current;
	unsigned long zero = 0UL;

	MUTEX_WARN_ON(lock->magic != lock);

	if (atomic_long_try_cmpxchg_acquire(&lock->owner, &zero, curr))
		return true;

	return false;
}
```

<div dir="rtl">

چرا `__mutex_unlock_fast()` ممکن است شکست بخورد، حتی وقتی فراخواننده واقعاً مالک mutex است؟

**Q8.** چرا `queued_spin_unlock()` یک store ساده است و نه یک RMW اتمی؟ اگر به‌جای آن از `WRITE_ONCE()` (بدون ترتیب release) روی یک CPU با ترتیب ضعیف استفاده می‌شد چه چیزی خراب می‌شد؟

</div>

```c
// linux/include/asm-generic/qspinlock.h · queued_spin_unlock() · v6.18.63 · L123-129
static __always_inline void queued_spin_unlock(struct qspinlock *lock)
{
	/*
	 * unlock() needs release semantics:
	 */
	smp_store_release(&lock->locked, 0);
}
```

<div dir="rtl">

**Q9.** آزمایش ۰۴ این را چاپ کرد (اجرای واقعی روی aos-lab):

</div>

```
$ sudo bpftrace futex-ops.bt -c './futex_mutex 4 200000'
threads=4 counter=800000 expected=800000 OK futex_wait=6680 futex_wake=8949
@calls[9]: 3
@calls[0]: 6680
@calls[1]: 8949
@usecs[0]:
[0]                 6559 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[1]                   26 |                                                    |
...
[64, 128)             32 |                                                    |
[128, 256)            15 |                                                    |
...
[8K, 16K)              1 |                                                    |
```

<div dir="rtl">

(الف) opهای ۰، ۱ و ۹ چه هستند و op 9 را چه کسی صادر کرده است؟ (ب) ۹۸٪ فراخوانی‌های FUTEX_WAIT زیر ۱ میکروثانیه طول کشیدند. آیا آن نخ‌ها خوابیدند؟ کدام خط‌های `futex_wait_setup()` این را توضیح می‌دهند؟ (ج) چرا WAKE بیشتر از WAIT است؟ (د) همین برنامه زیر `strace -f -c` در شمارنده‌های خودش `futex_wait=0` گزارش کرد. چرا؟

**Q10.** `futex_wait_setup()` قفل hash bucket را **پیش از** خواندن کلمهٔ کاربر می‌گیرد، و توضیح کد می‌گوید: *"If we locked the hash-bucket after testing \*uaddr, that would open a race condition where we could block indefinitely"*. درهم‌آمیزی بدی را که این کار جلویش را می‌گیرد (منتظر و بیدارکننده، روی ۲ CPU) رسم کنید. بعد توضیح دهید `futex_wake()` چطور باز هم می‌تواند وقتی `!futex_hb_waiters_pending(hb)` است قفل را کاملاً نادیده بگیرد.

**Q11.** این گزارش واقعی ThreadSanitizer از آزمایش ۰۱ را توضیح دهید. چرا TSan در اجرایی که نتیجه‌اش درست بود (`lost=0`) race گزارش می‌کند؟ دو راه‌حل متفاوت نام ببرید و بگویید اگر فقط `g_plain` را `volatile` کنید TSan هنوز کدام را علامت می‌زند.

</div>

```
$ ./race-tsan race 2 1000
WARNING: ThreadSanitizer: data race (pid=4446)
  Read of size 8 at 0x55912d33b070 by thread T2:
    #0 worker .../01-data-race/race.c:33 (race-tsan+0x1470)
  Previous write of size 8 at 0x55912d33b070 by thread T1:
    #0 worker .../01-data-race/race.c:33 (race-tsan+0x1483)
  Location is global 'g_plain' of size 8 at 0x55912d33b070 (race-tsan+0x4070)
...
SUMMARY: ThreadSanitizer: data race .../01-data-race/race.c:33 in worker
mode=race   threads=2 expected=2000 got=2000 lost=0 time=1.391s ns/inc=695728.7
```

<div dir="rtl">

## اشکال‌زدایی و طراحی

**Q12.** یک سرویس گیر کرده است. این را می‌گیرید (خروجی واقعی آزمایش ۰۶):

</div>

```
$ ps -L -o pid,lwp,stat,wchan:20,comm -p 27823
    PID     LWP STAT WCHAN                COMMAND
  27823   27826 Sl   futex_do_wait        deadlock
  27823   27827 Sl   futex_do_wait        deadlock
$ sudo gdb -p 27823 -batch -ex "thread apply all bt"
Thread 3 (Thread 0x7c4ab39ff6c0 (LWP 27826) "deadlock"):
#0  futex_wait (private=0, expected=2, futex_word=0x646ef2c58020 <g_acc_b>) ...
#4  transfer (from=...0x646ef2c58060 <g_acc_a>, to=...0x646ef2c58020 <g_acc_b>, amount=10) at deadlock.c:39
#5  a_to_b (arg=<optimized out>) at deadlock.c:49
Thread 2 (Thread 0x7c4ab31fe6c0 (LWP 27827) "deadlock"):
#0  futex_wait (private=0, expected=2, futex_word=0x646ef2c58060 <g_acc_a>) ...
#4  transfer (from=...0x646ef2c58020 <g_acc_b>, to=...0x646ef2c58060 <g_acc_a>, amount=20) at deadlock.c:39
#5  b_to_a (arg=<optimized out>) at deadlock.c:56
```

<div dir="rtl">

چه اتفاقی افتاده؟ کدام خط در کدام تابع کدام قفل را نگه داشته؟ آیا پردازه CPU مصرف می‌کند؟ راه‌حلی پیشنهاد دهید که API تابع `transfer()` را تغییر ندهد، و ابزاری که این باگ را در CI روی اجرایی که گیر نمی‌کند پیدا می‌کرد.

**Q13.** آزمایش ۰۳ این را چاپ کرد:

</div>

```
pref=reader readers=4 secs=3 reads=161806 writes=0 (+1 after stop) writer_wait max=4.281s avg=4.281458s
pref=writer readers=4 secs=3 reads=270250 writes=188 (+1 after stop) writer_wait max=0.036s avg=0.003488s
```

<div dir="rtl">

عددها را توضیح دهید. دو راه‌حل متفاوت طراحی کنید و برای هر کدام یک هزینه بگویید.

**Q14.** بافر محدود یکی از همکاران با ۱ تولیدکننده و ۱ مصرف‌کننده درست کار می‌کند ولی با ۲ مصرف‌کننده داده را خراب می‌کند. کد مصرف‌کننده این است:

</div>

```c
pthread_mutex_lock(&m);
if (count == 0)
    pthread_cond_wait(&not_empty, &m);
v = buf[tail]; tail = (tail + 1) % CAP; count--;
pthread_cond_signal(&not_full);
pthread_mutex_unlock(&m);
```

<div dir="rtl">

درهم‌آمیزی دقیقی را که خرابش می‌کند بگویید و راه‌حل یک‌کلمه‌ای را. چرا mutex باید به `pthread_cond_wait` داده شود؟

**Q15.** یک انحصار متقابل به سبک Dekker/Peterson برای دو نخ با `flag[me] = 1; turn = other; while (flag[other] && turn == other);` و atomicهای relaxed می‌نویسید، و آزمایش ۰۵ نشان می‌دهد روی x86 چطور شکست می‌خورد. fence دقیقاً کجا باید بیاید، gcc روی x86-64 برایش چه دستوری تولید می‌کند، و هزینه‌اش در مقایسه با یک قفل `lock cmpxchg` چقدر است؟

## امتحان شفاهی

**O1.** «mutex لینوکس می‌چرخد، پس در واقع یک spinlock است.» با استفاده از `mutex_spin_on_owner()` و `osq_lock()` از این گزاره دفاع یا آن را رد کنید.

**O2.** تشخیص grace period در RCU لینوکس را با `smr_grace_wait()` در OpenBSD مقایسه کنید. کدام برای ۵۱۲ CPU بهتر مقیاس‌پذیر است و چرا؟ اثبات درستی کدام آسان‌تر است؟

**O3.** چرا پروتکل futex اصلاً نیاز دارد کرنل کلمهٔ فضای کاربر را دوباره بررسی کند؟ آیا طرحی با فقط `FUTEX_SLEEP` (بدون مقدار) و `FUTEX_WAKE` کار می‌کرد؟ پاسختان را به گم‌شدن بیدارباش و condition variableها ربط دهید.

---

## پاسخ‌ها

**A1.** Race condition: نتیجه به زمان‌بندی نسبی بستگی دارد (ویژگی *معنایی*). Data race: دو دسترسی هم‌زمان به یک خانه که دست‌کم یکی نوشتن است و با همگام‌سازی مرتب نشده‌اند (ویژگی *زبانی*؛ در C11 رفتار تعریف‌نشده). Critical section: کدی که به حالت مشترک دست می‌زند و باید انحصاری اجرا شود. race بدون data race: هر نخ `lock; x = read(); unlock; lock; write(x + 1); unlock` اجرا می‌کند؛ همهٔ دسترسی‌ها قفل‌دارند، ولی چون read-modify-write در دو critical section جدا افتاده، به‌روزرسانی می‌تواند گم شود (race از نوع check-then-act یا TOCTOU).

**A2.** `ready` را با `memory_order_release` بنویسید و با `memory_order_acquire` بخوانید. release store همهٔ نوشتن‌های قبلی (`data = 42`) را برای هر نخی که با acquire load مقدار `ready == 1` را می‌خواند قابل‌دیدن می‌کند (synchronizes-with و در نتیجه happens-before). با `relaxed` کامپایلر می‌تواند دو store را جابه‌جا کند یا load مربوط به `data` را بالا ببرد، و Arm و POWER می‌توانند در سخت‌افزار جابه‌جایشان کنند. روی x86 اغلب «کار می‌کند» چون TSO ترتیب store→store و load→load را نگه می‌دارد، ولی کامپایلر باز هم ممکن است جابه‌جا کند و برنامه روی `data` یک data race دارد، یعنی UB. `mp.c` در آزمایش ۰۵ نشان می‌دهد نتیجهٔ ممنوع روی x86 هرگز دیده نمی‌شود؛ این شانس سخت‌افزار است، نه درستی برنامه.

**A3.** فقط (ج). هر هسته یک **store buffer** از نوع FIFO دارد؛ store در آن می‌ماند در حالی که loadهای بعدی به آدرس‌های دیگر از cache می‌خوانند، پس store پس از load برای همه دیده می‌شود. x86-TSO ترتیب store→store، load→load و load→store را نگه می‌دارد. آزمایش ۰۵ مورد (ج) را اندازه می‌گیرد؛ `mfence`، هر دستور با پیشوند `lock` یا `xchg` بافر را خالی می‌کند.

**A4.** (۱) نگه‌دارنده از CPU کنار گذاشته می‌شود و CPUهای دیگر تمام این مدت می‌چرخند؛ CPU هدر می‌رود و اگر منتظر روی همان CPU با preemption خاموش باشد، deadlock هم ممکن است. (۲) spinlock ممکن است در interrupt context گرفته شود که هرگز نمی‌تواند بخوابد. (۳) خوابیدن با preemption خاموش پیام "BUG: scheduling while atomic" می‌دهد و حساب quiescent stateهای RCU-sched را به هم می‌زند. `__raw_spin_lock()` اول `preempt_disable()` را صدا می‌زند (`spinlock_api_smp.h` خط L132) تا نگه‌دارنده روی CPU خودش preempt نشود در حالی که دیگران روی قفل می‌چرخند، بعد lockdep را باخبر می‌کند (`spin_acquire`) و بعد قفل را می‌گیرد.

**A5.** Grace period: بازه‌ای که در آن هر خوانندهٔ RCU که از قبل وجود داشته کارش تمام می‌شود. Quiescent state: نقطه‌ای که در آن یک CPU (یا task) قطعاً داخل هیچ خواننده‌ای نیست: context switch، idle، حالت کاربر؛ در RCU قابل preempt، خوانندهٔ preempt‌شده تا `rcu_read_unlock()` بیرونی‌اش در `blkd_tasks` دنبال می‌شود. پس از `rcu_assign_pointer()` خواننده‌های تازه فقط نسخهٔ تازه را می‌بینند؛ وقتی هر CPU از یک quiescent state گذشت، هیچ خواننده‌ای که بتواند اشاره‌گر قدیم را داشته باشد باقی نمانده، پس آزادکردنش امن است.

**A6.** انحصار متقابل ← منبع را اشتراک‌پذیر کنید (خواننده‌های RCU، دادهٔ lock-free)؛ hold-and-wait ← همهٔ قفل‌ها را یک‌جا بگیرید یا `trylock` و عقب‌نشینی؛ no preemption ← اجازهٔ گرفتن قفل از دیگری یا لغو بدهید (wound/wait در `ww_mutex`، rollback تراکنش)؛ انتظار چرخه‌ای ← یک ترتیب سراسری قفل (بر اساس آدرس یا سطح کلاس قفل). lockdep انتظار چرخه‌ای را بررسی می‌کند: یال‌های «A نگه داشته شد هنگام گرفتن B» را برای هر *کلاس* قفل ثبت می‌کند و هر یالی را که چرخه ببندد گزارش می‌دهد (`check_noncircular()`، `lockdep.c` خط L2176).

**A7.** L152: کلمهٔ مالک `task_struct *` نگه‌دارنده را دارد. L153: مقدار مورد انتظار دقیقاً ۰ است (آزاد، بدون پرچم). L155: بررسی debug (بدون `CONFIG_DEBUG_MUTEXES` حذف می‌شود). L157: یک `lock cmpxchg`: اگر owner == 0 بود `current` را بنویس، با ترتیب **acquire** تا critical section نتواند بالاتر از آن برود؛ اگر موفق شد قفل بدون کار دیگری گرفته شده است. L160: وگرنه فراخواننده به `__mutex_lock_slowpath()` می‌رود. `__mutex_unlock_fast()` کار `cmpxchg_release(owner, current → 0)` را انجام می‌دهد؛ وقتی هر بیت پرچمی روشن باشد شکست می‌خورد، یعنی `MUTEX_FLAG_WAITERS` (کسی در صف است)، `HANDOFF` یا `PICKUP`؛ پس مسیر کند باید یک منتظر را بیدار کند یا قفل را به او تحویل دهد.

**A8.** هنگام آزادکردن فقط مالک روی `locked` می‌نویسد، و x86 (و همهٔ معماری‌های لینوکس) store بایتیِ هم‌تراز را اتمی می‌کند، پس RMW لازم نیست؛ بیت‌های دیگر (pending و tail) دست نمی‌خورند چون `locked` یک بایت جداست. ترتیب **release** تضمین می‌کند همهٔ load و storeهای critical section پیش از آزاد دیده‌شدن قفل دیده شوند. با `WRITE_ONCE` ساده روی Arm64 یا POWER، storeی از داخل critical section می‌توانست پس از آزادکردن دیده شود و مالک بعدی دادهٔ کهنه می‌خواند. روی x86، `smp_store_release` فقط یک compiler barrier و یک `mov` است چون TSO خودش ترتیب را نگه می‌دارد.

**A9.** (الف) `op & 127`: ۰ یعنی `FUTEX_WAIT`، ۱ یعنی `FUTEX_WAKE` (از mutex ما)، ۹ یعنی `FUTEX_WAIT_BITSET` که `pthread_join` در glibc داخل `main` صادر کرده (۳ فراخوانی، ۳ join که باید صبر می‌کردند). (ب) نه. بی‌درنگ با `EAGAIN` برگشتند: `futex_wait_setup()` قفل bucket را می‌گیرد، کلمه را دوباره می‌خواند (L632) و وقتی دیگر ۲ نیست `-EWOULDBLOCK` برمی‌گرداند (L647–649)، یعنی قفل بین `xchg` فضای کاربر و syscall آزاد شده بود. فقط دنبالهٔ ۶۴ میکروثانیه تا ۱۶ میلی‌ثانیه واقعاً خوابید. (ج) آزادکننده حالت ۲ را می‌بیند و WAKE صادر می‌کند حتی اگر رقیب قفل را از قبل در فضای کاربر گرفته یا هنوز نخوابیده باشد؛ حالت ۲ چسبنده است چون نخ بیدارشده با `xchg 2` قفل را دوباره می‌گیرد. (د) `strace` از ptrace استفاده می‌کند: هر نخ در هر syscall (از جمله `clone`) متوقف می‌شود، پس نخ‌ها تقریباً هم‌پوشانی ندارند و قفل هرگز رقابتی نمی‌شود. ردیابی خودِ آزمایش را تغییر داد؛ bpftrace نخ‌ها را متوقف نمی‌کند.

**A10.** درهم‌آمیزی بد اگر کرنل اول کلمه را می‌خواند: منتظر `*uaddr == 2` را می‌خواند (تصمیم به خوابیدن) ← بیدارکننده ۰ را می‌نویسد و `futex_wake()` را صدا می‌زند، bucket را خالی می‌بیند و برمی‌گردد ← منتظر قفل bucket را می‌گیرد، خودش را در صف می‌گذارد و برای همیشه می‌خوابد. گرفتن قفل در ابتدا یعنی بیدارکننده یا پیش‌تر اجرا می‌شود (و منتظر مقدار عوض‌شده را می‌بیند و `-EWOULDBLOCK` می‌گیرد) یا پس از صف‌گذاری منتظر (و بیدارش می‌کند). بررسی بی‌قفل در `futex_wake()` امن است به خاطر جفت barrier در توضیح بالای فایل: منتظر `waiters++; smp_mb(); read *futex` و بیدارکننده `*futex = new; smp_mb(); read waiters`؛ همان الگوی store-buffering که دو barrier کامل حالت `waiters == 0 && futex == old` را ناممکن می‌کنند.

**A11.** دو دسترسی به همان ۸ بایت (`g_plain`) که دست‌کم یکی نوشتن است (*previous write* توسط T1)، از دو نخ متفاوت (T1 و T2)، بدون رابطهٔ happens-before بینشان: یک data race، هر دو در `race.c:33` (`g_plain++`). TSan رابطهٔ happens-before را با vector clock دنبال می‌کند، پس *نبودِ همگام‌سازی* را تشخیص می‌دهد نه نتیجهٔ غلط را؛ اجرایی که درست به نظر می‌رسد باز هم رفتار تعریف‌نشده است. راه‌حل‌ها: افزایش را بین `pthread_mutex_lock/unlock` بگذارید (قفل و آزادکردن یال happens-before می‌سازند)، یا از `atomic_fetch_add` استفاده کنید (دسترسی‌های اتمی هرگز race ندارند). `volatile` به‌تنهایی باز هم علامت می‌خورد: اتمی نیست و ترتیبی نمی‌سازد.

**A12.** یک deadlock از نوع AB-BA. LWP 27826 تابع `a_to_b` ← `transfer(A, B)` را اجرا می‌کند: `g_acc_a` را دارد (در خط ۳۶ گرفته) و در خط ۳۹ منتظر `g_acc_b` است. LWP 27827 تابع `b_to_a` ← `transfer(B, A)` را اجرا می‌کند: `g_acc_b` را دارد و در خط ۳۹ منتظر `g_acc_a` است. `expected=2` همان حالت «قفل‌شده با منتظر» در glibc است. همهٔ نخ‌ها در وضعیت `S` و داخل `futex_do_wait` هستند: هیچ CPUی مصرف نمی‌شود؛ livelock نیست. راه‌حل درون `transfer()`: دو حساب را همیشه با یک ترتیب سراسری قفل کنید، مثلاً اول آدرس کوچک‌تر (حالت `ordered` آزمایش ۰۶)، یا قفل دوم را با `trylock` بگیرید و در صورت شکست عقب بنشینید. در CI: ThreadSanitizer (`lock-order-inversion`) یا helgrind (`lock order ... violated`) روی هر اجرایی که هر دو ترتیب را، حتی پشت‌سرهم، طی کند.

**A13.** rwlock پیش‌فرض glibc خواننده‌ها را ترجیح می‌دهد: خوانندهٔ تازه در حالی پذیرفته می‌شود که نویسنده منتظر است، و چهار خوانندهٔ هم‌پوشان ۱۰۰ میکروثانیه‌ای شمار خواننده‌ها را برای همیشه بالای صفر نگه می‌دارند. پس نویسنده در طول اجرا **۰ بار** وارد می‌شود و تنها نوشتنش پس از توقف خواننده‌ها رخ می‌دهد (۴٫۳ ثانیه انتظار برای اجرای ۳ ثانیه‌ای): گرسنگی نویسنده، همان مسئلهٔ اول readers-writers. با `PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP` خواننده‌های تازه وقتی نویسنده منتظر است مسدود می‌شوند: ۱۸۸ نوشتن و بیشینهٔ انتظار ۳۶ میلی‌ثانیه. راه‌حل ۱: قفل با ترجیح نویسنده؛ هزینه: خواننده‌ها بیشتر صبر می‌کنند و قفل خواندن بازگشتی می‌تواند deadlock بسازد. راه‌حل ۲: قفل منصفانه با turnstile (FIFO بین خواننده و نویسنده، تمرین تکمیلی آزمایش ۰۳)؛ هزینه: همگام‌سازی اضافه در هر بخش خواندن (توان عملیاتی خواندن کمتر). راه‌حل ۳ (طراحی): انتشار به سبک RCU تا خواننده‌ها قفل نگیرند؛ هزینه: کپی و آزادسازی تأخیری.

**A14.** درهم‌آمیزی: بافر خالی است؛ C1 و C2 هر دو منتظرند. تولیدکننده یک آیتم می‌گذارد و signal می‌دهد ← C1 بیدار می‌شود ولی پیش از آن‌که mutex را دوباره بگیرد، C2 (که تازه رسیده، یا او هم بیدار شده، یا بی‌دلیل بیدار شده) mutex را می‌گیرد، `count == 1` را می‌بیند و آیتم را مصرف می‌کند. C1 بعد از `pthread_cond_wait` با mutex در دست برمی‌گردد، `count` را **دوباره بررسی نمی‌کند**، `buf[tail]` را از بافر خالی می‌خواند و `count` را به −۱ می‌رساند. راه‌حل: `if` ← `while`. mutex داده می‌شود تا «بررسی شرط و بعد خوابیدن» نسبت به signal‌دهنده اتمی باشد: `pthread_cond_wait` mutex را آزاد می‌کند و منتظر را در یک گام در صف می‌گذارد (glibc آن را روی futex پیاده می‌کند)، پس signalی بین بررسی و خوابیدن گم نمی‌شود.

**A15.** Peterson نیاز دارد store به `flag[me]` (و `turn`) پیش از load مربوط به `flag[other]` دیده شود؛ این دقیقاً همان ترتیب store→load است که x86 تضمین **نمی‌کند**، پس `atomic_thread_fence(memory_order_seq_cst)` را بین storeها و حلقهٔ چرخش بگذارید (یا همه را `seq_cst` کنید). gcc 13 روی x86-64 یک دستور بی‌اثرِ lockدار روی stack تولید می‌کند (`lock orq $0x0,(%rsp)`، disassembly آزمایش ۰۵)، یعنی یک barrier کامل که store buffer را خالی می‌کند و چند ده cycle هزینه دارد. یک قفل `lock cmpxchg` تقریباً همان هزینه را دارد (آن هم barrier کامل است)، ساده‌تر است و برای N نخ کار می‌کند؛ برای همین قفل‌های واقعی به‌جای Peterson از دستورهای RMW استفاده می‌کنند.

**O1 (نکته‌های کلیدی).** چرخیدن فقط مرحلهٔ خوش‌بینانه است: فقط تا وقتی مالک روی یک CPU است و چرخنده `need_resched()` ندارد اجرا می‌شود، هر بار فقط یک task می‌چرخد (`osq_lock`، یک صف MCS)، و هر کس نتواند بچرخد به `wait_list` از نوع FIFO می‌رود و در `schedule_preempt_disabled()` می‌خوابد. نگه‌دارندهٔ mutex می‌تواند بخوابد؛ نگه‌دارندهٔ spinlock نه. این یک mutex *تطبیقی* (adaptive) است.

**O2 (نکته‌های کلیدی).** لینوکس: گزارش quiescent state هر CPU در درختی از `rcu_node`ها به دست `rcu_gp_kthread` جمع می‌شود؛ بدون جابه‌جایی نخ، رقابت از مرتبهٔ O(log N)، پشتیبانی از خوانندهٔ preempt‌شدنی و grace period سریع (expedited). OpenBSD: یک نخ خودش را یکی‌یکی به هر CPU می‌چسباند (`sched_peg_curproc`)، یعنی O(N) مهاجرت پشت‌سرهم در هر grace period؛ ساده و برای خواننده‌های نخوابنده آشکارا درست. لینوکس بهتر مقیاس می‌پذیرد؛ وارسی SMR آسان‌تر است.

**O3 (نکته‌های کلیدی).** بدون بررسی مقدار، منتظر ممکن است تصمیم به خوابیدن بگیرد، بعد آزادکننده قفل را رها کند و کسی را بیدار نکند، و بعد منتظر برای همیشه بخوابد: گم‌شدن بیدارباش. مقدار همان شرط است که زیر قفل bucket به‌صورت اتمی بررسی می‌شود. خوابیدن بدون مقدار به یک قفل اضافه دور «بررسی و خوابیدن» نیاز داشت، یعنی همان کاری که condition variable با mutexش می‌کند؛ futex این بررسی را درون خود syscall گذاشته است.

</div>
