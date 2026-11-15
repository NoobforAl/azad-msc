<div dir="rtl">

# ۰۶ — Semaphore و condition variable

> ماژول ۰۳ · همروندی و همگام‌سازی · Linux v6.18.63 · OpenBSD 8cada8c · نسخهٔ انگلیسی: [06-semaphores-condition-variables.en.md](06-semaphores-condition-variables.en.md)

## ۱. خلاصه

- **Semaphore** یک شمارنده به‌اضافهٔ یک صف انتظار است. `P` (down/wait) یک واحد برمی‌دارد یا می‌خوابد، و `V` (up/post) یک واحد برمی‌گرداند و یک خوابیده را بیدار می‌کند. semaphore **منابع** را می‌شمارد.
- **Condition variable** هیچ حافظه‌ای ندارد. یک صف انتظار است که به یک mutex و یک **شرط (predicate)** بسته شده، و این شرط را باید بعد از هر بیدار شدن در یک حلقهٔ `while` دوباره بررسی کرد.
- در لینوکس هر دو نوع خوابیدن از یک قاعده پیروی می‌کنند: پیش از **آخرین** بررسی شرط، خودت را در صف بگذار و وضعیت task را تنظیم کن، تا هیچ wake-up در این فاصله گم نشود.

## ۲. توضیح

### ۲.۱ Semaphore دایکسترا

دایکسترا در ۱۹۶۵ دو عمل روی یک عدد صحیح نامنفی `S` تعریف کرد:

| عمل | نام | اثر |
|---|---|---|
| `P(S)` | proberen / down / `sem_wait` | اگر `S > 0` باشد `S--`، وگرنه بخواب تا مثبت شود |
| `V(S)` | verhogen / up / `sem_post` | `S++` و اگر کسی خوابیده، یکی را بیدار کن |

بررسی و کم کردن **یک گام اتمی** است، و ارزش کل این مفهوم در همین است.

| نوع | مقدار اولیه | معنا | مثال |
|---|---|---|---|
| Binary | ۱ | انحصار متقابل (ولی بدون owner!) | کدهای قدیمی کرنل پیش از `struct mutex` |
| Counting | N | N منبع یکسان | جاهای خالی یک bounded buffer |
| Signalling | ۰ | «رویداد رخ داد» بین دو نخ | `full` در Producer-Consumer |

Semaphore **owner ندارد** و هر نخی می‌تواند `V` را صدا بزند. این برای signalling درست است، ولی برای قفل نه: کسی نمی‌داند قفل دست کیست، پس priority inheritance نیست، optimistic spin روی owner نیست، و اشکال‌زدایی از نوع «قفل را task اشتباهی باز کرد» هم ممکن نیست. به همین دلیل کرنل بیشتر semaphoreهای binary را با `struct mutex` جایگزین کرده است ([یادداشت ۰۵](05-mutex-optimistic-spinning.fa.md)).

### ۲.۲ ساختار `struct semaphore` در کرنل

</div>

```text
linux/include/linux/semaphore.h · struct semaphore · v6.18.63 · L15-23
   15  struct semaphore {
   16  	raw_spinlock_t		lock;
   17  	unsigned int		count;
   18  	struct list_head	wait_list;
   19
   20  #ifdef CONFIG_DETECT_HUNG_TASK_BLOCKER
   21  	unsigned long		last_holder;
   22  #endif
   23  };
```

<div dir="rtl">

فقط سه فیلد: یک spinlock که از بقیه محافظت می‌کند، شمارنده، و یک فهرست FIFO از منتظرانِ خوابیده. مسیر سریع اتمی وجود ندارد؛ هر `down()` همان spinlock را می‌گیرد.

</div>

```text
linux/kernel/locking/semaphore.c · down() · v6.18.63 · L91-103
   91  void __sched down(struct semaphore *sem)
   92  {
   93  	unsigned long flags;
   94
   95  	might_sleep();
   96  	raw_spin_lock_irqsave(&sem->lock, flags);
   97  	if (likely(sem->count > 0))
   98  		__sem_acquire(sem);
   99  	else
  100  		__down(sem);
  101  	raw_spin_unlock_irqrestore(&sem->lock, flags);
  102  }
  103  EXPORT_SYMBOL(down);
```

<div dir="rtl">

<https://elixir.bootlin.com/linux/v6.18.63/source/kernel/locking/semaphore.c#L91>

- **L95** `might_sleep()`: وقتی debug روشن است، اگر `down()` در atomic context (داخل IRQ یا با یک spinlock در دست) صدا زده شود هشدار می‌دهد.
- **L96**: بررسی و کم کردن زیر `sem->lock` و با وقفه‌های خاموش انجام می‌شود. چون `up()` ممکن است از interrupt handler صدا زده شود، قفل باید در برابر IRQ امن باشد.
- **L97–98**: حالت سریع؛ `__sem_acquire()` شمارنده را کم می‌کند (و برای hung-task detection ثبت می‌کند چه کسی آن را دارد).
- **L100** `__down()`: به `___down_common()` (خط L252) می‌رسد. یک waiter به `wait_list` اضافه می‌کند، وضعیت task را تنظیم می‌کند، **spinlock را رها می‌کند**، `schedule_timeout()` را صدا می‌زند، قفل را دوباره می‌گیرد و `waiter.up` را بررسی می‌کند. بیدارکننده `waiter.up` را زیر همان قفل تنظیم می‌کند، پس wake-up بین «تصمیم به خوابیدن» و «خوابیدن» گم نمی‌شود.

</div>

```text
linux/kernel/locking/semaphore.c · up() · v6.18.63 · L220-233
  220  void __sched up(struct semaphore *sem)
  221  {
  222  	unsigned long flags;
  223  	DEFINE_WAKE_Q(wake_q);
  224
  225  	raw_spin_lock_irqsave(&sem->lock, flags);
  226
  227  	hung_task_sem_clear_if_holder(sem);
  228
  229  	if (likely(list_empty(&sem->wait_list)))
  230  		sem->count++;
  231  	else
  232  		__up(sem, &wake_q);
  233  	raw_spin_unlock_irqrestore(&sem->lock, flags);
```

<div dir="rtl">

<https://elixir.bootlin.com/linux/v6.18.63/source/kernel/locking/semaphore.c#L220>

- **L223** `DEFINE_WAKE_Q`: wake-upها اینجا جمع می‌شوند و **بعد از** رها شدن spinlock انجام می‌شوند (خط‌های بعد از L233)، تا task بیدارشده بلافاصله روی `sem->lock` نچرخد.
- **L229–230**: اگر کسی منتظر نیست، فقط شمارنده زیاد می‌شود.
- **L232** `__up()`: اگر منتظری هست، شمارنده زیاد **نمی‌شود**. واحد مستقیم به اولین منتظر داده می‌شود (`waiter->up = true`). این همان handoff از نوع FIFO است: کسی که دیر رسیده نمی‌تواند واحد را بدزدد.

در فضای کاربر، `sem_wait` و `sem_post` در glibc شمارنده را در یک word از حافظهٔ کاربر نگه می‌دارند و فقط برای خوابیدن یا بیدار کردن `futex()` را صدا می‌زنند. این یک جزئیات پیاده‌سازی glibc است و glibc در checkout ما نیست (اینجا UNVERIFIED است؛ با `strace -f -e futex ./pc_sem` در [آزمایش ۰۳.۲](../labs/02-producer-consumer/README.md) قابل مشاهده است). جزئیات در [یادداشت ۰۷](07-futex-user-kernel-split.fa.md).

### ۲.۳ Condition variable

Semaphore فقط می‌شمارد. Condition variable به نخ اجازه می‌دهد منتظر **هر شرطی روی وضعیت مشترک** بماند (`count > 0`، «صف پر نیست»، «نویسنده‌ای فعال نیست»). سه جزء دارد:

۱. یک **mutex** که از وضعیت محافظت می‌کند،
۲. **شرط**، که یک کد معمولی است،
۳. خود condvar، که فقط یک صف از خوابیده‌هاست.

`pthread_cond_wait(&cv, &m)` به‌طور اتمی **`m` را باز می‌کند و می‌خوابد**، و وقتی برمی‌گردد `m` دوباره در دست است. دو نتیجه:

- **چرا mutex را می‌دهیم؟** بدون «باز کردن و خوابیدن» اتمی، مشکل lost wake-up برمی‌گردد: شرط را بررسی می‌کنید (نادرست است)، producer وضعیت را تغییر می‌دهد و signal می‌دهد (هنوز کسی در صف نیست)، و شما برای همیشه می‌خوابید.
- **چرا `while` و نه `if`؟** POSIX از **معنای Mesa** پیروی می‌کند: `signal` فقط منتظر را runnable می‌کند. تا آن نخ mutex را دوباره بگیرد، ممکن است نخ دیگری آیتم را برداشته باشد (یک *stolen wake-up*، که با بیش از یک consumer رایج است). علاوه بر این، POSIX صراحتاً **spurious wake-up** را مجاز می‌داند. پس شرط باید دوباره بررسی شود.

| معنا | پس از `signal()` | بررسی منتظر | استفاده |
|---|---|---|---|
| Hoare (۱۹۷۴) | signal‌دهنده monitor را مستقیم به منتظر می‌دهد و منتظر **همان لحظه** اجرا می‌شود | `if` کافی است | کتاب‌های درسی، بعضی monitorهای RTOS |
| Mesa (۱۹۸۰) | منتظر runnable می‌شود و بعداً برای mutex **رقابت** می‌کند | **`while`** لازم است | POSIX threads، Java، `sync.Cond` در Go، `wait_event` در لینوکس |

| فراخوانی | چه کسانی را بیدار می‌کند | کِی |
|---|---|---|
| `pthread_cond_signal` | دست‌کم یک منتظر | همهٔ منتظرها برای یک چیز صبر می‌کنند و هر کدام می‌تواند ادامه دهد |
| `pthread_cond_broadcast` | همهٔ منتظرها | منتظرها روی یک condvar منتظر شرط‌های مختلف‌اند، یا یک تغییر وضعیت راه چند نفر را باز می‌کند (shutdown) |

### ۲.۴ نسخهٔ کرنل: `wait_event()`

کرنل نوعی به نام «condvar» ندارد. wait queue دارد و ماکروی `wait_event(wq, condition)` که حلقه را برایتان می‌سازد:

</div>

```text
linux/include/linux/wait.h · wait_event · v6.18.63 · L345-351
  345  #define wait_event(wq_head, condition)						\
  346  do {										\
  347  	might_sleep();								\
  348  	if (condition)								\
  349  		break;								\
  350  	__wait_event(wq_head, condition);					\
  351  } while (0)
```

<div dir="rtl">

<https://elixir.bootlin.com/linux/v6.18.63/source/include/linux/wait.h#L345>

- **L348**: بررسی سریع؛ اگر شرط از قبل درست است، صف را اصلاً لمس نکن.
- **L350** `__wait_event` به `___wait_event()` (خط L302) باز می‌شود. حلقهٔ آن این است: `prepare_to_wait_event()` (ورود به صف و تنظیم وضعیت task)، سپس `if (condition) break;`، سپس `schedule()`، و دوباره بررسی. ورود به صف و تغییر وضعیت **پیش از** بررسی انجام می‌شود؛ همان قاعدهٔ ترتیب در `futex_wait_setup()` ([یادداشت ۰۷](07-futex-user-kernel-split.fa.md)). `wake_up()` وضعیت را دوباره RUNNING می‌کند، پس اگر wake-up بین بررسی و `schedule()` برسد، `schedule()` فوراً برمی‌گردد.
- `condition` بعد از هر بیدار شدن دوباره ارزیابی می‌شود؛ یعنی همان معنای Mesa، این بار در قالب یک ماکرو.

## ۳. نمودار

</div>

```mermaid
sequenceDiagram
  participant C as Consumer
  participant M as mutex m
  participant Q as condvar not_empty
  participant P as Producer
  C->>M: lock(m)
  C->>C: while (count == 0)
  C->>Q: cond_wait: enqueue + unlock(m) atomically
  P->>M: lock(m)
  P->>P: buf[head]=v; count++
  P->>Q: cond_signal(not_empty)
  Q-->>C: runnable (not running yet)
  P->>M: unlock(m)
  C->>M: re-lock(m) inside cond_wait
  C->>C: re-check count == 0 ? (Mesa)
  C->>C: take item; count--
  C->>M: unlock(m)
```

<div dir="rtl">

## ۴. مثال حل‌شده

دو نسخهٔ C از bounded buffer در [آزمایش ۰۳.۲](../labs/02-producer-consumer/README.md):

</div>

```c
// labs/02-producer-consumer/pc_sem.c · producer() · L22-29
    for (long i = 1; i <= g_items; i++) {
        sem_wait(&g_empty);                 // P(empty): wait for a free slot
        pthread_mutex_lock(&g_lock);
        g_buf[g_head] = i;
        g_head = (g_head + 1) % g_cap;
        pthread_mutex_unlock(&g_lock);
        sem_post(&g_full);                  // V(full): one more item
    }
```

<div dir="rtl">

- `g_empty` از `cap` و `g_full` از ۰ شروع می‌شود. این دو با هم شرط `0 ≤ items ≤ cap` را بدون هیچ `if`ای تضمین می‌کنند؛ شمارنده‌ها خودشان شرط هستند.
- mutex فقط از به‌روزرسانی اندیس‌ها محافظت می‌کند. با یک producer و یک consumer می‌شود حذفش کرد، ولی با چند producer و چند consumer لازم است.
- **ترتیب مهم است:** `sem_wait(&g_empty)` **قبل از** `mutex_lock`. اگر جایشان را عوض کنید، producerی که mutex را دارد روی بافر پر می‌خوابد و consumer هیچ‌وقت نمی‌تواند mutex را بگیرد تا جایی خالی کند. نتیجه deadlock است ([یادداشت ۰۹](09-deadlock-coffman-lockdep.fa.md)).

</div>

```c
// labs/02-producer-consumer/pc_cond.c · consumer() · L41-50
        pthread_mutex_lock(&g_lock);
        while (g_count == 0) {
            g_waits_empty++;
            pthread_cond_wait(&g_not_empty, &g_lock);
        }
        long v = g_buf[g_tail];
        g_tail = (g_tail + 1) % g_cap;
        g_count--;
        pthread_cond_signal(&g_not_full);
        pthread_mutex_unlock(&g_lock);
```

<div dir="rtl">

- شرط `g_count == 0` یک کد معمولی است که زیر mutex خوانده می‌شود.
- `g_waits_empty` می‌شمارد consumer چند بار واقعاً خوابیده است. آزمایش آن را چاپ می‌کند و نشان می‌دهد اندازهٔ بافر چطور تعداد خوابیدن‌ها را تغییر می‌دهد.
- `signal(not_full)` در حالی فرستاده می‌شود که mutex در دست است. این کار مجاز و ساده است. signal بعد از unlock باعث می‌شود producer بیدارشده بلافاصله پشت mutex گیر نکند، ولی در آن حالت هم شرط باید زیر قفل تغییر کند.
- نسخهٔ Go (`pc_chan.go`) همین بافر است، با این تفاوت که runtime شمارش، قفل و park را انجام می‌دهد: `ch <- i` تا وقتی بافر پر است مسدود می‌ماند و `range ch` تا وقتی خالی است.

اجرا کنید و `ns/item` و `waits(...)` را برای `cap=1` و `cap=1024` مقایسه کنید. خروجی ثبت‌شده در README آزمایش است.

## ۵. حالت‌های مرزی و دام‌ها

| دام | نشانه | راه درست |
|---|---|---|
| `if` به‌جای `while` دور `cond_wait` | به‌ندرت آیتم غلط یا underflow، با ۲ consumer یا بیشتر یا یک spurious wake-up | همیشه `while (!predicate)` |
| تغییر شرط بدون mutex | lost wake-up: منتظر برای همیشه می‌خوابد | وضعیت را زیر همان mutexی تغییر دهید که منتظر استفاده می‌کند |
| `signal` وقتی منتظرها روی یک condvar منتظر شرط‌های مختلف‌اند | نخ بیدارشده شرطش نادرست است و نخ درست خواب می‌ماند (گیر شبیه deadlock) | `broadcast`، یا یک condvar برای هر شرط (`not_full` / `not_empty`) |
| اول mutex، بعد `sem_wait` | deadlock در Producer-Consumer | اول روی semaphore منتظر بمانید، بعد قفل بگیرید |
| استفاده از semaphore binary به‌جای قفل | owner ندارد: نه PI، نه بررسی owner در lockdep، و آزاد کردن توسط نخ دیگر هم مجاز است | `pthread_mutex` / `struct mutex` کرنل |
| `down()` کرنل در IRQ context | خوابیدن در atomic context ← BUG | `down_trylock()`، یا انتقال کار به process context |
| shutdown با consumerهای مسدود | consumerها تا ابد منتظر می‌مانند | poison pill یا flag `done` همراه با `broadcast` (تمرین تکمیلی آزمایش) |

## ۶. نکته‌های کلیدی امتحان

- Semaphore = شمارنده + صف انتظار، با بررسی و کم کردن اتمی. کاربردها: binary، counting و signalling.
- Semaphore **owner ندارد** ولی mutex دارد؛ به همین دلیل کرنل برای قفل کردن `struct mutex` را ترجیح می‌دهد.
- `down()` و `up()` در کرنل `sem->lock` را با irqsave می‌گیرند. اگر منتظری باشد، `up()` **واحد را به اولین منتظر می‌دهد** (FIFO) و شمارنده را زیاد نمی‌کند.
- Condvar = mutex + شرط + صف. `cond_wait` به‌طور اتمی قفل را باز می‌کند و می‌خوابد، و با mutex در دست برمی‌گردد.
- **معنای Mesa ← `while`**. با معنای Hoare `if` کافی بود. POSIX علاوه بر این spurious wake-up را هم مجاز می‌داند.
- `signal` دست‌کم یک منتظر را بیدار می‌کند و `broadcast` همه را. برای هر شرط یک condvar بگذارید.
- قاعدهٔ lost wake-up (در `___wait_event` کرنل، futex و semaphore): **ورود به صف و تنظیم وضعیت پیش از بررسی نهایی**.
- Producer-Consumer: `empty = N`، `full = 0` و یک mutex برای اندیس‌ها. ترتیب: اول `P(empty)`، بعد `lock`.

## ۷. پیوندها

- درس: [بخش ۴.۵: نخ‌ها چطور منتظر یک شرط می‌مانند؟](../lesson.fa.md#45-how-do-threads-wait-for-a-condition)
- مرور کد کرنل: [kernel-walkthrough.fa.md](../kernel-walkthrough.fa.md)
- آزمایش‌ها: [۰۳.۲ Producer-Consumer (semaphore ← condvar ← کانال Go)](../labs/02-producer-consumer/README.md)، [۰۳.۳ Readers-Writers و گرسنگی نویسنده](../labs/03-readers-writers/README.md)
- آزمونک: [پرسش ۱۴ (`if` یا `while` برای condvar)](../quiz.fa.md)، پرسش ۱۳ (گرسنگی در readers-writers)
- یادداشت‌های مرتبط: [۰۷ futex](07-futex-user-kernel-split.fa.md)، [۰۵ mutex](05-mutex-optimistic-spinning.fa.md)، [۰۹ deadlock](09-deadlock-coffman-lockdep.fa.md)، [۱۰ مسئله‌های کلاسیک](10-classic-problems.fa.md)

### مقایسه با OpenBSD

OpenBSD نوعی مثل `struct semaphore` برای semaphore شمارشی در کرنل ندارد. کد کرنل روی یک **wait channel** می‌خوابد، که می‌تواند هر آدرسی باشد. `sleep_setup(ident, prio, wmesg)` پیش از بررسی نهایی شرط و `sleep_finish(timeout, do_sleep)` بعد از آن صدا زده می‌شود (`sys/kern/kern_synch.c` خط‌های L284 و L320). `wakeup(ident)` و `wakeup_n()` خوابیده‌های روی آن آدرس را بیدار می‌کنند. این الگو را در `rw_do_enter_write()` می‌بینید:

</div>

```text
openbsd/sys/kern/kern_rwlock.c · rw_do_enter_write() · 8cada8c · L292-298
  292  	rw_inc(&rwl->rwl_waiters);
  293  	membar_producer();
  294  	do {
  295  		sleep_setup(&rwl->rwl_waiters, prio, rwl->rwl_name);
  296  		membar_consumer();
  297  		owner = atomic_load_long(&rwl->rwl_owner);
  298  		error = sleep_finish(RW_SLEEP_TMO, owner != 0);
```

<div dir="rtl">

<https://github.com/openbsd/src/blob/8cada8c/sys/kern/kern_rwlock.c#L292>

- **L292–293**: خودت را منتظر اعلام کن و این را با یک store barrier منتشر کن.
- **L295**: پیش از خواندن owner روی کانال `&rwl->rwl_waiters` ثبت‌نام کن؛ همان قاعدهٔ «اول صف، بعد بررسی نهایی».
- **L298** `sleep_finish(..., owner != 0)`: فقط اگر شرط هنوز همین را می‌گوید بخواب. حلقهٔ `do { } while` دور آن همان بررسی دوبارهٔ Mesa است.

| انتخاب طراحی | Linux | OpenBSD | بده‌بستان |
|---|---|---|---|
| شیء انتظار | `wait_queue_head_t` نوع‌دار، `struct semaphore` | هر آدرسی به‌عنوان wait channel | لینوکس: type-safe با فهرست جدا برای هر شیء. OpenBSD: API ساده‌تر با یک sleep queue مشترک و hash‌شده |
| حلقهٔ شرط | ماکروی `wait_event()` | دنبالهٔ دست‌نویس `sleep_setup` / بررسی / `sleep_finish` | ماکرو قاعدهٔ ترتیب را پنهان می‌کند. حالت دستی آن را آشکار می‌کند، ولی اشتباه کردن در آن آسان است |
| semaphore شمارشی در کرنل | دارد (`down`/`up` با handoff از نوع FIFO) | نوع جداگانه ندارد | لینوکس آن را برای کدهای قدیمی و موارد شمارشی نگه داشته است |
| بیدار کردن | `wake_up()` (برای منتظرهای exclusive فقط یکی) | `wakeup()` همه / `wakeup_n()` | بیدار کردن همه ساده‌تر است، ولی باعث thundering herd می‌شود |

</div>
