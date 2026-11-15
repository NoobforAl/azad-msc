<div dir="rtl">

# یادداشت ۰۴ — مسیر دستور `syscall`

> ماژول ۰۱ · معماری · نسخهٔ انگلیسی: [`04-syscall-path.en.md`](04-syscall-path.en.md) · فهرست: [`INDEX.fa.md`](INDEX.fa.md) · **ARCH-SPECIFIC (x86-64)**

## ۱. خلاصه

- system call یک درخواست شماره‌دار است: شماره در `rax`، حداکثر شش آرگومان در `rdi, rsi, rdx, r10, r8, r9`، و نتیجه (یا `-errno`) دوباره در `rax`. دستور `syscall` به آدرس داخل `MSR_LSTAR` می‌پرد.
- مسیر لینوکس: `entry_SYSCALL_64` (اسمبلی: `swapgs`، پشتهٔ کرنل، `pt_regs`) ← `do_syscall_64()` (کارهای ورود، توزیع، کارهای خروج) ← `x64_sys_call()` (یک `switch` روی شماره) ← `__x64_sys_<name>()`.
- خروج سریع `sysretq` است؛ وقتی وضعیت ذخیره‌شده برای `sysret` امن نباشد، کرنل به `iretq` برمی‌گردد. ردیابی (strace)، seccomp و signalها به کارهای ورود و خروج وصل‌اند، نه به تک‌تک syscallها.

## ۲. توضیح

### شهود

syscall یک فراخوانی تابع از روی مرز دسترسی است. فراخوانی‌کننده نمی‌تواند به هر آدرسی در کرنل بپرد، پس از یک در ثابت استفاده می‌کند و «کدام تابع» را با یک شماره می‌گوید. کرنل در آن طرف نباید به هیچ چیز اعتماد کند: نه به اشاره‌گر پشته، نه به رجیسترها، نه به اشاره‌گرهای داخل آرگومان‌ها.

### گام به گام

**۰. wrapper در libc.** تابع `read(fd, buf, n)` در glibc مقدار `eax = 0` (یعنی `__NR_read`) را بار می‌کند، آرگومان‌ها را سر جایشان می‌گذارد و `syscall` را اجرا می‌کند. هنگام برگشت `rax` را بررسی می‌کند: مقداری در بازهٔ `[-4095, -1]` یعنی خطا، پس `-rax` را در `errno` می‌گذارد و `-1` برمی‌گرداند.

**۱. این دستور در سخت‌افزار چه می‌کند** (از توضیح بالای `entry_SYSCALL_64`):

`linux/arch/x86/entry/entry_64.S · entry_SYSCALL_64 (comment) · v6.18.63` (L62–78)

</div>

```text
 * 64-bit SYSCALL saves rip to rcx, clears rflags.RF, then saves rflags to r11,
 * then loads new ss, cs, and rip from previously programmed MSRs.
 * rflags gets masked by a value from another MSR (so CLD and CLAC
 * are not needed). SYSCALL does not save anything on the stack
 * and does not change rsp.
 *
 * Registers on entry:
 * rax  system call number
 * rcx  return address
 * r11  saved rflags (note: r11 is callee-clobbered register in C ABI)
 * rdi  arg0
 * rsi  arg1
 * rdx  arg2
 * r10  arg3 (needs to be moved to rcx to conform to C ABI)
 * r8   arg4
 * r9   arg5
 * (note: r12-r15, rbp, rbx are callee-preserved in C ABI)
```

<div dir="rtl">

جملهٔ کلیدی: **«SYSCALL does not save anything on the stack and does not change rsp.»** کرنل روی پشته‌ای شروع می‌کند که کاربر کنترلش می‌کند و باید پیش از هر کار دیگری از آن خارج شود.

**۲. `entry_SYSCALL_64` (اسمبلی، `entry_64.S` خط L87).** `swapgs` (دسترسی به دادهٔ per-CPU)، ذخیرهٔ `rsp` کاربر در یک خانهٔ per-CPU، `SWITCH_TO_KERNEL_CR3` (فقط با PTI)، بار کردن `cpu_current_top_of_stack` در `rsp`، push کردن یک قاب شبیه قاب سخت‌افزاری و همهٔ رجیسترهای عمومی (یعنی `struct pt_regs`)، صفر کردن رجیسترهای عمومی، وصله‌های Spectre، و `call do_syscall_64(regs, nr)` (walkthrough بخش ۲).

**۳. `do_syscall_64()` (به زبان C، `syscall_64.c` خط L87، با برچسب `noinstr`).**
- `syscall_enter_from_user_mode()`: interruptها را روشن می‌کند؛ اگر پرچم‌های `syscall_work` تنظیم باشند، `syscall_trace_enter()` این‌ها را به ترتیب اجرا می‌کند: **syscall user dispatch ← ptrace (یعنی strace) ← seccomp ← tracepoint به نام `sys_enter` ← audit** (`kernel/entry/syscall-common.c` خط‌های L20–67).
- `do_syscall_x64()`: بررسی محدوده با مقایسهٔ `unsigned`، `array_index_nospec()`، بعد `x64_sys_call(regs, nr)`؛ نتیجه در `regs->ax`.
- `syscall_exit_to_user_mode()`: حلقهٔ `exit_to_user_mode_loop()` ← اگر `need_resched` باشد `schedule()`، تحویل signal، `resume_user_mode_work`؛ بعد tracepoint به نام `sys_exit` یا توقف ptrace.
- اگر `sysret` امن باشد `true` برمی‌گرداند (بررسی `rcx == rip`، `r11 == flags`، RIP کانونی، نبودِ `RF`/`TF`).

**۴. `x64_sys_call()` ← `__x64_sys_read(regs)`.** یک `switch` که از `syscall_64.tbl` ساخته شده. stub که `SYSCALL_DEFINE3` ساخته، `regs->di, regs->si, regs->dx` را برمی‌دارد و بدنهٔ واقعی را صدا می‌زند (walkthrough بخش‌های ۴ و ۵).

**۵. برگشت.** دوباره در اسمبلی: `POP_REGS`، رفتن به پشتهٔ trampoline، `SWITCH_TO_USER_CR3`، `swapgs`، `sysretq` (خط L166) یعنی `rip ← rcx`، `rflags ← r11`، `CPL ← 3`. یا مسیر `iretq` از طریق `swapgs_restore_regs_and_return_to_usermode`.

### مسیر سریع در برابر مسیر کند

دیگر تابع «مسیر سریع» جداگانه‌ای وجود ندارد. تفاوت هزینه همان پرچم‌های `syscall_work` است: بدون tracer، بدون فیلتر seccomp و بدون audit، `syscall_enter_from_user_mode` تقریباً کاری نمی‌کند. `strace` را وصل کنید تا **هر** syscall از `ptrace_report_syscall_entry()` بگذرد؛ این تابع task را متوقف و پردازهٔ tracer را بیدار می‌کند: دو context switch برای هر ورود syscall و دو تا برای هر خروج. برای همین برنامه‌ها زیر strace چند برابر کندتر اجرا می‌شوند (آزمایش ۰۴ آن را اندازه می‌گیرد).

### در یک syscall چه چیزی وقت می‌گیرد

| بخش | چرا | سهم تقریبی |
|---|---|---|
| دستورهای `syscall` و `sysret` | سریال شدن pipeline، مقصد از MSR | ثابت، ده‌ها نانوثانیه |
| نوشتن `CR3` برای PTI (اگر CPU در برابر Meltdown آسیب‌پذیر باشد) | دو بار بار کردن `CR3` در هر syscall؛ با PCID کل TLB خالی نمی‌شود | می‌تواند هزینه را دو برابر کند |
| وصله‌های Spectre (`IBRS_ENTER`، `UNTRAIN_RET`، `CLEAR_BRANCH_HISTORY`، `CLEAR_CPU_BUFFERS`) | وابسته به CPU | از صفر تا زیاد |
| کارهای ورود و خروج | وضعیت RCU/lockdep، بررسی `need_resched` و signal | وقتی کاری نیست، کم |
| بدنهٔ syscall | `getpid` ≈ هیچ؛ `read` = VFS + FS + کپی | متغیر |

CPU خودتان را بررسی کنید: `grep . /sys/devices/system/cpu/vulnerabilities/*`.

### vDSO: syscallهایی که syscall نیستند

بعضی فراخوانی‌ها فقط داده‌ای را که کرنل نگه می‌دارد *می‌خوانند*: زمان (`clock_gettime`، `gettimeofday`، `time`)، `getcpu`، و از v6.11 `getrandom`. کرنل یک ELF کوچک (`[vdso]` در `/proc/self/maps`) به‌اضافهٔ صفحه‌های داده (`[vvar]`) را در هر پردازه map می‌کند و glibc آن را مثل یک تابع کتابخانه‌ای عادی صدا می‌زند. mode switch نیست، به شرط آنکه منبع ساعت از حالت کاربر خواندنی باشد (TSC یا یک ساعت paravirt)؛ وگرنه خود vDSO به یک `syscall` واقعی برمی‌گردد. سورس: `arch/x86/entry/vdso/vclock_gettime.c` و `lib/vdso/gettimeofday.c`.

## ۳. نمودار

</div>

```mermaid
sequenceDiagram
  participant U as user code
  participant CPU
  participant A as entry_SYSCALL_64 (asm)
  participant D as do_syscall_64 (C)
  participant W as entry/exit work
  participant S as __x64_sys_getpid
  U->>CPU: eax=39; syscall
  CPU->>A: rcx=RIP, r11=RFLAGS, RIP=LSTAR, CPL=0, IF=0
  A->>A: swapgs · save rsp · [CR3] · kernel rsp · pt_regs
  A->>D: call do_syscall_64(regs, 39)
  D->>W: syscall_enter_from_user_mode: IRQs on, [ptrace/seccomp/trace]
  D->>S: x64_sys_call → case 39
  S-->>D: regs->ax = tgid
  D->>W: syscall_exit_to_user_mode: [schedule()] [signals]
  D-->>A: true (sysret OK)
  A->>A: pop regs · [CR3] · swapgs
  A-->>U: sysretq → rax = pid
```

<div dir="rtl">

## ۴. مثال عملی: wrapper و نمادهای کرنل روی VM

wrapper در glibc واقعاً چند دستور دور `syscall` است، و در سمت کرنل همان stub قرار دارد که `x64_sys_call` به آن می‌پرد (خروجی واقعی، aos-lab، ۱۴۰۵/۰۸/۲۴):

</div>

```text
$ gdb -batch -ex 'disassemble read' /lib/x86_64-linux-gnu/libc.so.6 | head -9
Dump of assembler code for function __GI___libc_read:
   0x000000000011bce0 <+0>:	endbr64
   0x000000000011bce4 <+4>:	cmpb   $0x0,0xf0355(%rip)        # 0x20c040 <__libc_single_threaded>
   0x000000000011bceb <+11>:	je     0x11bd00 <__GI___libc_read+32>
   0x000000000011bced <+13>:	xor    %eax,%eax
   0x000000000011bcef <+15>:	syscall
   0x000000000011bcf1 <+17>:	cmp    $0xfffffffffffff000,%rax
   0x000000000011bcf7 <+23>:	ja     0x11bd48 <__GI___libc_read+104>
   0x000000000011bcf9 <+25>:	ret

$ grep -w -e do_syscall_64 -e x64_sys_call -e __x64_sys_read /proc/kallsyms
ffffffffb5929b60 T x64_sys_call
ffffffffb5ea3d60 T __x64_sys_read
ffffffffb6c8a1d0 T do_syscall_64
```

<div dir="rtl">

- `xor %eax,%eax` و بعد `syscall`: مقدار `__NR_read` برابر ۰ است (`syscall_64.tbl` خط L12) و xor کوتاه‌ترین راه بار کردن صفر است. در `getpid` دستور `mov $0x27,%eax` (یعنی ۳۹) است.
- `cmp $0xfffffffffffff000,%rax` به‌همراه `ja`: بررسی خطای `-4095..-1`.
- `__x64_sys_read`، `x64_sys_call` و `do_syscall_64` نمادهای واقعی در `/proc/kallsyms` هستند؛ `__do_sys_read` از نوع `static inline` است و معمولاً داخل `__x64_sys_read` inline می‌شود.

## ۵. حالت‌های خاص و دام‌ها

- **`r10`، نه `rcx`.** صدا زدن syscallی با ۴ آرگومان یا بیشتر از inline asm با آرگومان چهارم در `rcx` بی‌صدا مقدار بی‌معنی می‌فرستد (تمرین تکمیلی آزمایش ۰۲).
- **`rcx` و `r11` از بین می‌روند.** inline asm باید آن‌ها را فهرست کند، و اگر کرنل در حافظهٔ کاربر می‌نویسد، `"memory"` را هم.
- **مقدار برگشتی ≠ مقدار برگشتی libc.** کرنل `-EBADF` (یعنی `-9`) برمی‌گرداند؛ `syscall(3)` و wrapperها `-1` با `errno = 9` برمی‌گردانند.
- **فراخوانی‌های قابل شروع دوباره.** `read`ی که با signal قطع شود، در داخل `-ERESTARTSYS` برمی‌گرداند؛ کد signal یا آن را دوباره شروع می‌کند (با SA_RESTART مقدار `rip` را ۲ بایت، یعنی طول `syscall`، عقب می‌برد) یا آن را به `-EINTR` تبدیل می‌کند.
- **مسیرهای ۳۲ بیتی نقطه‌های ورود دیگری‌اند**: `int 0x80` ← `do_int80_emulation()`، و `sysenter` و `syscall` ۳۲ بیتی ← `entry_SYSENTER_compat` / `entry_SYSCALL_compat`، با شماره‌های i386 (`read` = ۳).
- **FRED** (Flexible Return and Event Delivery در CPUهای جدید Intel): یک سازوکار ورود برای syscall و رویدادها؛ وقتی FRED روشن باشد `syscall_init()` تنظیم LSTAR را رد می‌کند (`common.c` خط‌های L2280–2281). VERSION-DEPENDENT؛ روی VM ما فعال نیست.
- **`do_syscall_64` از نوع `noinstr` است**: نمی‌توانید با ftrace یا kprobe آن را ردیابی کنید. به‌جایش `x64_sys_call`، `__x64_sys_*` یا tracepoint به نام `raw_syscalls:sys_enter` را probe کنید.

## ۶. نکته‌های کلیدی امتحانی

- ABI: `rax` = شماره، آرگومان‌ها `rdi rsi rdx r10 r8 r9`، نتیجه در `rax`، `rcx`/`r11` از بین می‌روند، خطاها `-4095..-1`.
- `syscall`: `rcx ← RIP`، `r11 ← RFLAGS`، `CS/SS ← STAR`، `RIP ← LSTAR`، `RFLAGS &= ~SFMASK`؛ **تعویض پشته ندارد**.
- اسمبلی ورود: `swapgs`، ذخیرهٔ `rsp` کاربر، `CR3` برای PTI، پشتهٔ کرنل، ساختن `pt_regs`، صفر کردن رجیسترهای عمومی.
- `do_syscall_64`: کارهای ورود (ptrace/seccomp/tracepoint/audit) ← `switch` در `x64_sys_call` ← کارهای خروج (زمان‌بندی، signal) ← انتخاب `sysret` یا `iret`.
- `SYSCALL_DEFINEn(name, ...)` سه تابع `__x64_sys_name(regs)`، `__se_sys_name` و `__do_sys_name` را می‌سازد.
- strace باعث می‌شود هر syscall در `ptrace_report_syscall_entry/exit` متوقف شود ← کند.
- vDSO: `clock_gettime` و مشابه‌هایش در حالت کاربر از داده‌ای که کرنل به‌روز می‌کند اجرا می‌شوند؛ جایگزین آن یک syscall واقعی است.
- برگشت از syscall یک نقطهٔ preemption و تحویل signal است.

## ۷. پیوندها

- درس: [بخش ۲.۲ وقتی برنامه `read()` را صدا می‌زند](../lesson.fa.md)، [بخش ۲.۴ vDSO](../lesson.fa.md)
- Walkthrough: [بخش‌های ۲ تا ۵](../kernel-walkthrough.fa.md)
- آزمایش‌ها: [01 نقشهٔ strace](../labs/01-strace-map/README.md)، [02 syscall خام](../labs/02-raw-syscall/README.md)، [04 هزینهٔ syscall](../labs/04-syscall-cost/README.md)
- آزمونک: پرسش‌های ۷، ۸، ۹ و ۱۲ در [`quiz.fa.md`](../quiz.fa.md)

</div>
