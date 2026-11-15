<div dir="rtl">

# یادداشت ۰۵ — Context switch: رجیسترها، پشته‌ها، `CR3`

> ماژول ۰۱ · معماری · نسخهٔ انگلیسی: [`05-context-switch.en.md`](05-context-switch.en.md) · فهرست: [`INDEX.fa.md`](INDEX.fa.md) · جزئیات رجیسترها **ARCH-SPECIFIC (x86-64)** است

## ۱. خلاصه

- context switch همیشه **داخل کرنل** و در `__schedule()` ← `context_switch()` رخ می‌دهد. رجیسترهای کاربرِ task در حال خروج، از وقتی وارد کرنل شد، در `pt_regs` خودش ذخیره شده‌اند.
- خود سوئیچ سه کار می‌کند: شاید فضای آدرس جدیدی بار کند (`switch_mm_irqs_off()` ← نوشتن `CR3`)، **پشتهٔ کرنل** را عوض کند (`__switch_to_asm`: push شش رجیستر callee-saved و تعویض `rsp`)، و وضعیت CPU مخصوص هر task را درست کند (`__switch_to()`: FPU، پایهٔ `FS`/`GS`، `current`، بالای پشته).
- سوئیچ بین دو نخ یک پردازه، یا به یک نخ کرنل، نوشتن `CR3` را رد می‌کند. هزینهٔ مستقیم در حد میکروثانیه است (آزمایش ۳ ماژول ۰۲ آن را روی همین VM اندازه می‌گیرد)؛ هزینهٔ غیرمستقیم (cache و TLB سرد) اغلب بیشتر است.

## ۲. توضیح

### شهود

هر task پشتهٔ کرنل خودش را دارد. taskی که در حال اجرا نیست، وسط یک فراخوانی تابع «یخ زده» است: `context_switch()` ← `switch_to()`. پشته‌اش آدرس‌های برگشت همان زنجیرهٔ فراخوانی را نگه می‌دارد. عوض کردن task یعنی: جایی را که هستم ذخیره کنم (اشاره‌گر پشته‌ام) و روی پشتهٔ task دیگری ادامه دهم که دقیقاً در همان نقطه از کد یخ زده است. وقتی `switch_to` «برمی‌گردد»، روی پشتهٔ task *دیگر* و به فراخوانی `context_switch()` همان task برمی‌گردد. همهٔ taskها در یک خط می‌خوابند و در همان خط بیدار می‌شوند.

### چرا فقط ۶ رجیستر؟

`switch_to()` یک فراخوانی تابع از C است. ABI سیستم V برای x86-64 می‌گوید فراخوانی‌کننده هر رجیستر caller-saved (`rax, rcx, rdx, rsi, rdi, r8–r11`) را که لازم دارد از قبل ذخیره کرده است. پس فراخوانی‌شونده فقط باید رجیسترهای **callee-saved** را نگه دارد: `rbx, rbp, r12–r15`. `__switch_to_asm` دقیقاً همین شش تا را به ترتیب `struct inactive_task_frame` push می‌کند:

`linux/arch/x86/include/asm/switch_to.h · struct inactive_task_frame · v6.18.63` (L23–42)

</div>

```c
struct inactive_task_frame {
#ifdef CONFIG_X86_64
	unsigned long r15;
	unsigned long r14;
	unsigned long r13;
	unsigned long r12;
#else
	unsigned long flags;
	unsigned long si;
	unsigned long di;
#endif
	unsigned long bx;

	/*
	 * These two fields must be together.  They form a stack frame header,
	 * needed by get_frame_pointer().
	 */
	unsigned long bp;
	unsigned long ret_addr;
};
```

<div dir="rtl">

- از پایین به بالا بخوانید، چون پشته رو به پایین رشد می‌کند: `call __switch_to_asm` مقدار `ret_addr` را push کرد، بعد `pushq %rbp`، `%rbx`، `%r12`…`%r15`. `thread.sp` به `r15` اشاره می‌کند.
- یک task تازه fork‌شده یک `inactive_task_frame` دست‌ساز با `ret_addr = ret_from_fork_asm` می‌گیرد (`struct fork_frame`، خط L44)، پس اولین «برگشت از `switch_to`» آن در مسیر برگشت fork فرود می‌آید.

رجیسترهای حالت کاربر (`rip`، `rsp`، همهٔ رجیسترهای عمومی، `rflags`) اینجا دست نمی‌خورند: در `pt_regs` بالای پشتهٔ کرنل هر task هستند، هنگام ورود ذخیره و هنگام خروج برگردانده می‌شوند.

### `context_switch()` چه تصمیمی می‌گیرد

| حالت | `next->mm` | کار روی فضای آدرس |
|---|---|---|
| کاربر ← کاربر، پردازهٔ دیگر | غیر NULL و ≠ قبلی | `switch_mm_irqs_off()`: نوشتن `CR3` (با PCID، برچسب ASID، بدون خالی کردن کامل TLB) |
| نخ ← نخ، همان پردازه | غیر NULL و = قبلی | `switch_mm_irqs_off()` می‌بیند `prev == next`: معمولاً `CR3` نوشته نمی‌شود |
| هر چیز ← نخ کرنل | NULL | **lazy TLB**: همان `mm` قبلی بار می‌ماند (`active_mm`)، `CR3` نوشته نمی‌شود |
| نخ کرنل ← کاربر | غیر NULL | `next->mm` بار می‌شود؛ `mm` قرضی بعداً در `finish_task_switch()` رها می‌شود |

نخ‌های کرنل فقط در نیمهٔ کرنل فضای آدرس زندگی می‌کنند که در همهٔ `mm`ها یکسان است، پس می‌توانند هر کدام را قرض بگیرند.

### `__switch_to()` چه می‌کند (C، مخصوص هر معماری)

از `arch/x86/kernel/process_64.c` خط‌های L611–700:
۱. `switch_fpu(prev_p, cpu)`: رجیسترهای FPU/SSE/AVX مربوط به `prev` را همین حالا **ذخیره** می‌کند (`save_fpregs_to_fpstate()`) و `TIF_NEED_FPU_LOAD` را رویش تنظیم می‌کند (`arch/x86/include/asm/fpu/sched.h` خط‌های L32–52). رجیسترها فقط در مسیر برگشت به حالت کاربر **برگردانده** می‌شوند، و اگر این CPU هنوز وضعیت آن task را داشته باشد، این کار رد می‌شود.
۲. `save_fsgs()`، `load_TLS()`، `x86_fsgsbase_load()`: پایهٔ `FS` اشاره‌گر نخ (TLS) در فضای کاربر است؛ برای بعضی برنامه‌ها پایهٔ `GS` هم.
۳. `x86_pkru_load()`: کلیدهای حفاظت حافظه.
۴. `raw_cpu_write(current_task, next_p)`: حالا `current` همان `next` است.
۵. `raw_cpu_write(cpu_current_top_of_stack, …)`: syscall بعدی روی این CPU روی پشتهٔ کرنل `next` فرود می‌آید (walkthrough بخش ۷).
۶. `switch_to_extra()`: ویژگی‌های کم‌کاربرد (bitmap ورودی/خروجی، کنترل speculation).

### سوئیچ چه وقت رخ می‌دهد؟

- **داوطلبانه**: task مسدود می‌شود (`read` روی pipe خالی، انتظار `futex`، `nanosleep`) و `schedule()` را صدا می‌زند. در `/proc/<pid>/status` به نام `voluntary_ctxt_switches` شمرده می‌شود.
- **غیرداوطلبانه (preemption)**: tick تایمر یا یک بیدار شدن، `need_resched` را تنظیم می‌کند؛ کرنل هنگام خروج از interrupt یا syscall (یا بسته به حالت `PREEMPT_DYNAMIC`، در یک نقطهٔ preemption داخل کرنل) `schedule()` را صدا می‌زند. به نام `nonvoluntary_ctxt_switches` شمرده می‌شود.

### هزینه

- **مستقیم**: ورود به کرنل، انتخاب زمان‌بند، کد سوئیچ، نوشتن `CR3`. در حد میکروثانیه.
- **غیرمستقیم**: task بعدی cacheها و TLB را پر از دادهٔ task قبلی می‌یابد. با PCID ورودی‌های TLB باقی می‌مانند، اما cacheهای L1/L2 همچنان سردند. برای همین سنجاق کردن یک جفت ping-pong روی یک CPU برای بعضی بارها از دو CPU سریع‌تر و برای بعضی کندتر است (آزمایش ۳ ماژول ۰۲ اندازه‌اش می‌گیرد).

## ۳. نمودار

</div>

```mermaid
sequenceDiagram
  participant A as task A (kernel stack A)
  participant S as __schedule / context_switch
  participant M as switch_mm_irqs_off
  participant W as __switch_to_asm
  participant C as __switch_to
  participant B as task B (kernel stack B)
  A->>S: blocks or is preempted (user regs already in pt_regs A)
  S->>M: next->mm differs: write CR3 (ASID)
  S->>W: switch_to(A, B)
  W->>W: push rbp rbx r12-r15 on stack A
  W->>W: A->thread.sp = rsp ; rsp = B->thread.sp
  W->>W: pop r15-r12 rbx rbp (B's saved values)
  W->>C: jmp __switch_to(A, B)
  C->>C: FPU, FS/GS, current_task = B, top_of_stack = B
  C-->>B: ret: returns into B's old context_switch()
  B->>B: finish_task_switch(A), back up B's call chain → sysret/iret to B's user code
```

<div dir="rtl">

## ۴. مثال عملی

روی VM (۱۴۰۵/۰۸/۲۴) سوئیچ‌ها را برای taskی که زیاد مسدود می‌شود (یک subshell که منتظر ۲۰ فرزند `sleep` کوتاه می‌ماند) و taskی که هرگز مسدود نمی‌شود (`yes > /dev/null`) بشمارید:

</div>

```text
$ ( for i in $(seq 1 20); do sleep 0.05; done ) & P=$!; sleep 0.5; grep ctxt /proc/$P/status
voluntary_ctxt_switches:	11
nonvoluntary_ctxt_switches:	0
$ yes > /dev/null & Y=$!; sleep 3; grep ctxt /proc/$Y/status; kill $Y
voluntary_ctxt_switches:	2
nonvoluntary_ctxt_switches:	2
$ perf stat -e context-switches,cpu-migrations,task-clock sleep 1
                 1      context-switches                 #  419.104 /sec
                 0      cpu-migrations                   #    0.000 /sec
              2.39 msec task-clock                       #    0.001 CPUs utilized
       1.605512149 seconds time elapsed
```

<div dir="rtl">

- subshell: بعد از ۰٫۵ ثانیه ۱۱ سوئیچ داوطلبانه و ۰ غیرداوطلبانه. هر `wait()` برای یک فرزند `sleep` مسدود می‌شود، یعنی `schedule()` داوطلبانه صدا زده می‌شود.
- `yes`: در ۳ ثانیه کار خالص CPU فقط ۲ + ۲ سوئیچ. یک task پرمصرف CPU فقط وقتی preempt می‌شود که task دیگری CPU *خودش* را بخواهد؛ با ۸ vCPU معمولاً یکی آزاد بود. سوئیچ غیرداوطلبانه با رقابت زیاد می‌شود، نه با زمان.
- `perf stat` روی `sleep 1`: یک context switch (همان خواب) و ۲٫۳۹ میلی‌ثانیه CPU در ۱٫۶ ثانیه زمان واقعی.

## ۵. حالت‌های خاص و دام‌ها

- **syscall یک context switch نیست** (یادداشت ۰۲). `getpid()` هرگز `schedule()` را صدا نمی‌زند، مگر اینکه هنگام خروج `need_resched` از قبل تنظیم شده باشد.
- **«کرنل در context switch همهٔ رجیسترها را ذخیره می‌کند.»** در `__switch_to_asm` شش تا را ذخیره می‌کند؛ بقیه را کامپایلر یا ورود به کرنل ذخیره کرده‌اند.
- **ذخیرهٔ FPU فوری است و بازگرداندنش با تأخیر** (لینوکس از نسخه‌های 4.x سوئیچ کاملاً lazy برای FPU را به‌خاطر آسیب‌پذیری LazyFP کنار گذاشت). جزئیات VERSION-DEPENDENT است.
- **`__switch_to` را نمی‌شود با function_graph ردیابی کرد** (`__notrace_funcgraph`، process_64.c خط L610): تابع روی پشته‌ای غیر از پشته‌ای که صدا زده شده برمی‌گردد.
- **نخ‌ها فقط در بخش `CR3`/TLB از پردازه‌ها سریع‌تر سوئیچ می‌کنند**؛ هزینهٔ زمان‌بندی یکسان است.
- **پارامتر `last` در `switch_to(prev, next, last)`**: وقتی B ادامه می‌دهد، متغیر محلی `prev` آن کهنه است (همان چیزی را دارد که B هنگام خارج شدن *خودش* دیده بود). ماکرو task قبلی واقعی را برمی‌گرداند تا `finish_task_switch()` درست همان را پاک‌سازی کند.
- **interruptها هنگام سوئیچ خاموش‌اند** (قفل `rq` گرفته شده، پسوند `_irqs_off`)؛ `finish_task_switch()` دوباره روشنشان می‌کند.

## ۶. نکته‌های کلیدی امتحانی

- context switch = `__schedule()` ← `context_switch()` ← `switch_mm_irqs_off()` (به‌اضافهٔ `CR3`) ← `switch_to()` ← `__switch_to_asm` ← `__switch_to()`.
- رجیسترهای کاربر در `pt_regs` هستند (هنگام ورود ذخیره شده‌اند)؛ سوئیچ فقط `rbx, rbp, r12–r15` و `rsp` (در `thread.sp`) را ذخیره می‌کند.
- سوئیچ واقعی یک دستور است: `movq TASK_threadsp(%rsi), %rsp`.
- برای نخ‌های یک `mm` و برای نخ‌های کرنل (lazy TLB، `active_mm`) نوشتن `CR3` رد می‌شود.
- `__switch_to()` مقدار `current_task` و `cpu_current_top_of_stack` را به‌روز می‌کند (که ورود syscall بعدی از آن استفاده می‌کند).
- taskهای جدید با یک `inactive_task_frame` ساختگی از `ret_from_fork_asm` شروع می‌کنند.
- سوئیچ داوطلبانه (مسدود شدن) و غیرداوطلبانه (preemption) در `/proc/<pid>/status` شمرده می‌شوند.
- هزینهٔ غیرمستقیم (cache/TLB) اغلب از هزینهٔ مستقیم بیشتر است.

## ۷. پیوندها

- درس: [بخش ۲.۵ context switch دقیقاً چه چیزی را عوض می‌کند؟](../lesson.fa.md)
- Walkthrough: [بخش ۷ Context switch](../kernel-walkthrough.fa.md)
- آزمایش: تمرین تکمیلی [05 ftrace روی vfs_read](../labs/05-ftrace-vfs-read/README.md)؛ آزمایش ۳ ماژول ۰۲ (هزینهٔ ping-pong)
- آزمونک: پرسش‌های ۱۰، ۱۴ و پرسش شفاهی O2 در [`quiz.fa.md`](../quiz.fa.md)

</div>
