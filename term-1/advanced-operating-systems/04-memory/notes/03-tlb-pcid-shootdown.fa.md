<div dir="rtl">

# ۰۳ — TLB، ASID/PCID و shootdown

> ماژول ۰۴ · مدیریت حافظه · Linux v6.18.63 · `ARCH-SPECIFIC (x86-64)` · نسخهٔ انگلیسی: [`03-tlb-pcid-shootdown.en.md`](03-tlb-pcid-shootdown.en.md)

## ۱. خلاصه

- TLB ترجمه‌های اخیر VA به PA را cache می‌کند. hit تقریباً هیچ چرخهٔ اضافه‌ای ندارد و miss یک پیمایش جدول هزینه دارد (یادداشت ۰۲). **برد** TLB (تعداد مدخل ضرب در اندازهٔ صفحه) با صفحه‌های ۴ کیلوبایتی فقط چند مگابایت است.
- PCID (نسخهٔ x86 از ASID) روی هر مدخل یک شناسهٔ فضای آدرس می‌گذارد تا context switch مجبور به flush نباشد. لینوکس برای هر CPU **۶** PCID پویا نگه می‌دارد و آن‌ها را چرخشی دوباره استفاده می‌کند.
- تغییر PTEای که CPUهای دیگر شاید cache کرده باشند به **TLB shootdown** نیاز دارد: یک IPI به هر CPU در `mm_cpumask(mm)`، یا روی CPUهای جدید AMD، پخش سخت‌افزاری با INVLPGB.

## ۲. توضیح مفصل

**شهود.** page table در RAM است و اگر برای هر load پیمایش می‌شد، ترافیک حافظه تا پنج برابر می‌شد. TLB یک cache کوچک، سریع و set-associative *داخل هسته* است که کلیدش شمارهٔ صفحهٔ مجازی است. اندازه‌های معمول در یک هستهٔ امروزی x86 به سازنده بستگی دارد و باید با `cpuid` بررسی شود: L1 dTLB حدود ۶۴ مدخل برای صفحه‌های ۴ کیلوبایتی و حدود ۳۲ مدخل برای ۲ مگابایتی، و یک L2 TLB یکپارچه (STLB) با حدود ۱٫۵ تا ۳ هزار مدخل. با صفحه‌های ۴ کیلوبایتی، ۱۵۳۶ مدخل فقط **۶ مگابایت** را می‌پوشاند؛ با صفحه‌های ۲ مگابایتی، همین تعداد مدخل **۳ گیگابایت** را. برنامه‌هایی که روی heapهای بزرگ دسترسی تصادفی دارند (hash table، کد گراف، پایگاه داده، GC در JVM) گرفتار TLB می‌شوند. آزمایش ۰۴ این پرتگاه را نشان می‌دهد.

**چه چیزی مدخل‌های TLB را باطل می‌کند؟**
1. نوشتن در `CR3` بدون بیت «no-flush»، همهٔ مدخل‌های غیرسراسری PCID قبلی را پاک می‌کند.
2. `INVLPG addr` مدخل یک صفحه را روی CPU فعلی پاک می‌کند.
3. `INVPCID` مدخل‌های یک PCID مشخص را پاک می‌کند: یک آدرس، همه، یا همه به‌جز سراسری‌ها.
4. مدخل‌های سراسری (`_PAGE_GLOBAL`، mappingهای کرنل) بعد از نوشتن CR3 باقی می‌مانند.

TLB با حافظه **coherent نیست**. اگر کرنل یک PTE را عوض کند، CPUهایی که ترجمهٔ قدیمی را cache کرده‌اند تا وقتی flush نکنند همان را به کار می‌برند. پس قاعدهٔ درستی این است: بعد از اینکه یک mapping را *محدودتر* کردید (unmap، محافظت در برابر نوشتن برای COW، مهاجرت، reclaim)، *قبل از* استفادهٔ دوباره از صفحهٔ قدیمی، همهٔ CPUهایی را که شاید آن را دارند flush کنید.

**PCID در لینوکس.** بدون PCID، هر context switch به یک `mm` دیگر TLB را پاک می‌کند. با PCID، لینوکس به هر CPU یک cache کوچک از فضاهای آدرسی که اخیراً اجرا شده‌اند می‌دهد: `cpu_tlbstate.ctxs[0..TLB_NR_DYN_ASIDS-1]` که `TLB_NR_DYN_ASIDS = 6` است (`arch/x86/include/asm/tlbflush.h` خط ۶۶). `switch_mm_irqs_off()` تابع `choose_new_asid()` را صدا می‌زند (گشت در کد، بخش ۷). اگر `mm` بعدی از قبل روی این CPU slot داشته باشد، مدخل‌هایش دوباره به کار می‌روند و flush فقط وقتی لازم است که **tlb_gen** آن mm در غیابش جلو رفته باشد. با KPTI هر فضای آدرس دو PCID لازم دارد، یکی برای جدول‌های کرنل و یکی برای جدول‌های کاربر. نام‌گذاری «kPCID/uPCID» در `tlb.c` (خط‌های ۶۳ تا ۹۰) از همین‌جاست.

**سازوکار shootdown** در `flush_tlb_mm_range(mm, start, end, …)`:
1. `inc_mm_tlb_gen(mm)`: یک شمارهٔ نسل جدید.
2. اگر CPUهای دیگری در `mm_cpumask(mm)` باشند، `flush_tlb_multi()` یک IPI می‌فرستد. هر CPU مقصد `flush_tlb_func()` را اجرا می‌کند که نسل‌ها را مقایسه می‌کند و یا صفحه‌ها را تک‌تک flush می‌کند (با `INVLPG`، تا `tlb_single_page_flush_ceiling` = ۳۳ صفحه) یا همه را.
3. در غیر این صورت flush محلی انجام می‌شود.
4. از ۶٫۱۵ به بعد: `mm_global_asid()` و `broadcast_tlb_flush()` با INVLPGB در AMD همهٔ CPUها را با یک دستور و بدون IPI flush می‌کنند (`VERSION-DEPENDENT` و وابسته به سخت‌افزار).

CPUهایی که پردازه‌های دیگر را اجرا می‌کنند به‌تدریج از `mm_cpumask` حذف می‌شوند. CPUهایی که در حالت **lazy TLB** هستند، یعنی یک نخ کرنل را اجرا می‌کنند که `mm` قبلی را قرض گرفته، ممکن است IPI را رد کنند و هنگام سوئیچ بعدی flush کنند.

**هزینه‌ها.** رفت‌وبرگشت یک IPI چند میکروثانیه است. برنامه‌ای چندنخی که روی ۶۴ CPU پخش شده و در حلقه `munmap` یا `madvise(MADV_DONTNEED)` صدا می‌زند، ممکن است بیشتر وقتش را در shootdown بگذراند. راه‌حل‌ها:
- unmapها را دسته‌ای کنید (`mmu_gather`)؛
- نخ‌های یک پردازه را روی CPUهای کمتری نگه دارید؛
- حافظه را دوباره استفاده کنید به‌جای اینکه پسش بدهید (مثل decay در jemalloc)؛
- از پخش سخت‌افزاری استفاده کنید.

## ۳. نمودار

</div>

```mermaid
sequenceDiagram
  participant C0 as CPU0 (munmap caller)
  participant MM as mm->tlb_gen
  participant C1 as CPU1 (same mm)
  participant C2 as CPU2 (other mm, lazy)
  C0->>C0: clear PTEs (page table lock)
  C0->>MM: inc_mm_tlb_gen() → gen 42
  C0->>C1: IPI flush_tlb_func(info gen 42)
  C1->>C1: INVLPG × n (or full flush), local gen = 42
  C1-->>C0: done
  Note over C2: not in mm_cpumask → no IPI; flushes on next switch_mm if behind
  C0->>C0: free the pages (safe now)
```

<div dir="rtl">

## ۴. مثال کاربردی

سورس cache مربوط به PCID: `linux/arch/x86/mm/tlb.c · choose_new_asid() · v6.18.63 · L252-260` ([Elixir](https://elixir.bootlin.com/linux/v6.18.63/source/arch/x86/mm/tlb.c#L224))

</div>

```c
	for (asid = 0; asid < TLB_NR_DYN_ASIDS; asid++) {
		if (this_cpu_read(cpu_tlbstate.ctxs[asid].ctx_id) !=
		    next->context.ctx_id)
			continue;

		ns.asid = asid;
		ns.need_flush = (this_cpu_read(cpu_tlbstate.ctxs[asid].tlb_gen) < next_tlb_gen);
		return ns;
	}
```

<div dir="rtl">

| خط | معنی |
|---|---|
| `TLB_NR_DYN_ASIDS` | برای هر CPU شش slot. |
| `ctx_id` | یک شناسهٔ ۶۴ بیتی که در کل عمر `mm` یکتاست و برخلاف PCID هرگز دوباره استفاده نمی‌شود. |
| `need_flush = tlb_gen < next_tlb_gen` | slot مال ماست، ولی page tableهایمان در غیابمان تغییر کرده‌اند، پس همین حالا این PCID را flush کن. |

**روی VM:** شمارنده‌های PMU نداریم، پس رویدادهای نرم‌افزاری و شمارنده‌های کرنل را می‌شماریم.

</div>

```bash
grep -o -w -E 'pcid|invpcid|invlpgb' /proc/cpuinfo | sort | uniq -c
grep -E 'nr_tlb_(remote|local)' /proc/vmstat
cat /sys/kernel/debug/x86/tlb_single_page_flush_ceiling   # sudo
```

```
      8 invpcid
      8 pcid
$ sudo cat /sys/kernel/debug/x86/tlb_single_page_flush_ceiling
33
```

<div dir="rtl">

خطی با `nr_tlb_*` نیست، چون این شمارنده‌ها فقط با `CONFIG_DEBUG_TLBFLUSH` وجود دارند و این گزینه در این کرنل خاموش است (`/boot/config-6.18.63-061863-generic`). `invlpgb` هم نیست، پس مسیر پخش سخت‌افزاری اینجا استفاده نمی‌شود.

</div>

<div dir="rtl">

بعد آزمایش ۰۴ برد TLB را مستقیم اندازه می‌گیرد: نانوثانیه برای هر دسترسی در یک pointer chase تصادفی روی N صفحه، با صفحه‌های ۴ کیلوبایتی و ۲ مگابایتی. نسخهٔ `perf stat -e dTLB-load-misses` اینجا **UNVERIFIED** است، چون مهمان VirtualBox هیچ PMU سخت‌افزاری در اختیار نمی‌گذارد.

## ۵. حالت‌های مرزی و دام‌ها

- **TLB مال هر هسته است** (و بین SMT siblingها مشترک)، نه مال هر پردازه. «flush کردن TLB یک پردازه» یعنی flush کردن یک PCID روی هر CPUای که پردازه رویش اجرا شده.
- **faultهای کاذب.** لینوکس گاهی یک PTE را *آزادتر* می‌کند و flush نمی‌کند. CPUای که مدخل فقط‌خواندنی کهنه را دارد fault می‌دهد و کرنل فقط دوباره امتحان می‌کند (`flush_tlb_fix_spurious_fault`، گشت در کد بخش ۳).
- **KPTI مصرف PCID را دو برابر می‌کند** و روی CPUهای بدون PCID باعث می‌شود هر syscall TLB را پاک کند. این کندی بزرگ در ۲۰۱۸ اندازه‌گیری شد.
- **صفحه‌های بزرگ در بسیاری از CPUها TLBهای جداگانه و کوچک‌تری دارند.** مخلوط کردن اندازه‌ها اشکالی ندارد، ولی در همهٔ سطح‌ها انتظار برد ۵۱۲ برابری نداشته باشید.
- **مجازی‌سازی:** TLB miss پیمایش دوبعدی می‌شود (EPT یا NPT) و صفحهٔ بزرگ در *هر دو* سمت میزبان و مهمان مهم است. اعداد مطلق VM ما اعداد سخت‌افزار واقعی نیستند.

## ۶. نکته‌های امتحانی

- برد TLB برابر است با تعداد مدخل ضرب در اندازهٔ صفحه: با صفحهٔ ۴ کیلوبایتی چند مگابایت، با صفحهٔ ۲ مگابایتی چند گیگابایت.
- PCID روی مدخل‌های TLB برچسب می‌گذارد. لینوکس برای هر CPU شش ASID پویا دارد که چرخشی استفاده می‌شوند، و `tlb_gen` تعیین می‌کند flush لازم است یا نه.
- shootdown یعنی IPI به `mm_cpumask(mm)`. تا ۳۳ صفحه هر کدام با `INVLPG`، بیشتر از آن flush کامل.
- مدخل‌های TLB باید قبل از استفادهٔ دوباره از صفحهٔ آزادشده flush شوند و `mmu_gather` همین ترتیب را تضمین می‌کند.
- INVLPGB در AMD و RAR در اینتل flush سخت‌افزاری پخشی می‌دهند. لینوکس از ۶٫۱۵ برای آن‌ها ASID سراسری به کار می‌برد.

## ۷. پیوندها

- درس: [بخش ۲.۳](../lesson.fa.md)
- گشت در کد: [بخش ۷](../kernel-walkthrough.fa.md)
- آزمایش: [04.4، برد TLB و صفحه‌های بزرگ](../labs/04-tlb-hugepages/README.md)
- آزمون: پرسش‌های ۳ و ۹

</div>
