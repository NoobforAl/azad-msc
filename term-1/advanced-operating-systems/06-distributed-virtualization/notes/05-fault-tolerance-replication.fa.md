<div dir="rtl">

# ۰۵ — مبانی تحمل خطا: مدل‌های خرابی، تکثیر، quorum و پیش‌نمایش اجماع

> ماژول ۰۶ · سیستم‌عامل توزیع‌شده و مجازی‌سازی · نسخه‌های ثابت: Linux **v6.18.63** و OpenBSD **`8cada8c`** · نسخهٔ انگلیسی: [`05-fault-tolerance-replication.en.md`](05-fault-tolerance-replication.en.md)

## واژه‌نامه

| اصطلاح | تعریف |
|---|---|
| **مدل خرابی (Failure model)** | گرهٔ معیوب چه کاری ممکن است بکند: crash (متوقف شود)، omission (پیام بیندازد)، timing (بیش از حد کند باشد)، Byzantine (هر کاری، حتی دروغ گفتن). |
| **Failure detector** | جزئی که گره‌ها را *مشکوک* اعلام می‌کند، معمولاً با نرسیدن heartbeat. در شبکهٔ ناهمگام ممکن است اشتباه کند. |
| **Primary-backup** | یک primary اجرا می‌کند و وضعیت یا log را به backupها می‌فرستد؛ هنگام خرابی یک backup جایش را می‌گیرد. |
| **State machine replication (SMR)** | همهٔ replicaها همان فرمان‌های قطعی را با همان ترتیب اجرا می‌کنند (ترتیب با اجماع توافق می‌شود). |
| **Quorum** | زیرمجموعه‌ای از replicaها که توافقشان کافی است؛ هر دو quorum با هم اشتراک دارند. |
| **اجماع (Consensus)** | توافق روی یک مقدار (یا یک ورودی log) با وجود خرابی‌ها: Paxos و Raft. |
| **Term در Raft** | شمارهٔ دورهٔ منطقی؛ در هر term حداکثر یک leader وجود دارد. |

## ۱. خلاصه

- تحمل خطا = **افزونگی + قاعده‌ای برای توافق با وجود خرابی**. تعداد replica لازم به مدل خرابی بستگی دارد: `f+1` برای تحمل f crash اگر خرابی قابل‌تشخیص باشد، `2f+1` برای crash با quorum اکثریت در شبکهٔ ناهمگام، و `3f+1` برای خرابی Byzantine.
- دو سبک تکثیر: **primary-backup** (ساده، ولی به تشخیص مطمئن خرابی نیاز دارد) و **state machine replication** (replicaها با اجماع روی log فرمان‌ها توافق می‌کنند؛ Raft و Paxos پروتکل‌های استانداردند).
- quorumها این را ممکن می‌کنند: با N replica، خواندن از R و نوشتن روی W هر وقت `R + W > N` باشد هم‌پوشانی دارند؛ اکثریت‌ها (`⌊N/2⌋+1`) همیشه اشتراک دارند و به همین دلیل اقلیتِ جداشده در partition نمی‌تواند پیش برود؛ و FLP (۱۹۸۵) می‌گوید در سیستم کاملاً ناهمگام با حتی یک crash هیچ پروتکل قطعی نمی‌تواند هم ایمنی و هم پایان‌پذیری را تضمین کند.

## ۲. توضیح مفصل

**Fault، error، failure.** یک *fault* (برگشتن بیت، دیسک مرده، کابل بریده) باعث *error* (وضعیت نادرست) می‌شود که ممکن است به *failure* (سرویس نادرست) برسد. تحمل خطا جلوی تبدیل error به failure را می‌گیرد، عمدتاً با افزونگی: در زمان (تکرار، یادداشت ۰۱)، در اطلاعات (checksum، ECC، parity در RAID) و در مکان (replicaها، همین یادداشت).

**مدل‌های خرابی، از ضعیف‌ترین تا قوی‌ترین فرض دربارهٔ گرهٔ معیوب:**

| مدل | گرهٔ معیوب ممکن است | تعداد replica برای تحمل f | نمونه |
|---|---|---|---|
| Fail-stop | crash کند و بقیه با اطمینان بفهمند | f + 1 | سخت‌افزار با watchdog که برق را قطع می‌کند |
| Crash (ناهمگام) | crash کند؛ بقیه crash را از کندی تشخیص نمی‌دهند | 2f + 1 (اکثریت) | Raft، Paxos، ZooKeeper، etcd |
| Omission / timing | پیام بیندازد یا دیر کند | 2f + 1 به‌اضافهٔ timeout | شبکه‌های پراتلاف |
| Byzantine | هر کاری: دروغ، پیام متناقض | 3f + 1 | PBFT، BFT در بلاک‌چین |

چرا 2f+1 برای crash: هر تصمیم به تأیید یک quorum به اندازهٔ Q نیاز دارد؛ برای زنده ماندن با f گرهٔ خاموش باید `Q ≤ N − f`؛ برای ایمنی هر دو quorum باید اشتراک داشته باشند (`2Q > N`). هر دو با `N = 2f+1` و `Q = f+1` برقرارند. چرا 3f+1 برای Byzantine: اشتراک دو quorum باید حتی اگر f عضوش دروغ بگویند دست‌کم یک گرهٔ *درستکار* داشته باشد: `2Q − N ≥ f + 1` با `Q = N − f` نتیجه می‌دهد `N ≥ 3f + 1`.

**تشخیص خرابی** یعنی heartbeat به‌اضافهٔ timeout. در شبکهٔ ناهمگام گرهٔ کند و گرهٔ مرده یکسان دیده می‌شوند (همان «پاسخی نیامد» در RPC، یادداشت ۰۱). detectorی که زود مشکوک شود دو primary می‌سازد (**split brain**)؛ و آن‌که دیر مشکوک شود قطعی طولانی. کرنل لینوکس همین الگو را داخل یک ماشین دارد: هر CPU باید مرتب یک timestamp را «لمس» کند و اگر نکند، soft-lockup detector فعال می‌شود (بخش ۴).

**Primary-backup.** clientها با primary حرف می‌زنند؛ primary عملیات را اعمال می‌کند، به‌روزرسانی را به backupها می‌فرستد، منتظر تأییدشان می‌ماند و بعد پاسخ می‌دهد. اگر primary بمیرد یک backup جایش را می‌گیرد. ساده و ارزان (f+1 نسخه)، ولی به failure detector اعتماد می‌کند: اگر primary قبلی فقط کند بوده باشد، حالا دو تا داریم. راه‌حل: **lease/epoch** (primary فقط در مدت leaseی که اکثریت داده اجازهٔ عمل دارد و epochهای کهنه رد می‌شوند؛ به این fencing هم می‌گویند).

**State machine replication.** هر replica را یک state machine قطعی کنید و همان فرمان‌ها را با همان ترتیب به همه بدهید. «همان ترتیب» یک مسئلهٔ اجماع است که برای هر خانهٔ log یک بار حل می‌شود.

**پیش‌نمایش Raft** (Ongaro و Ousterhout، ۲۰۱۴):

۱. **انتخاب leader.** followerهایی که در یک election timeout تصادفی heartbeat نگیرند candidate می‌شوند، **term** را یکی بالا می‌برند، به خودشان رأی می‌دهند و رأی می‌خواهند. رأی اکثریت leader می‌سازد؛ یک رأی برای هر گره در هر term تضمین می‌کند در هر term حداکثر یک leader باشد.
۲. **تکثیر log.** leader فرمان را اضافه می‌کند و `AppendEntries(term, prevIndex, prevTerm, entries)` می‌فرستد؛ follower فقط وقتی می‌پذیرد که در `prevIndex` ورودی‌ای با `prevTerm` داشته باشد (**log matching**). ورودی وقتی روی اکثریت ذخیره شد **committed** است و سپس اعمال می‌شود.
۳. **ایمنی.** به candidateی که log او از رأی‌دهنده کمتر به‌روز است رأی داده نمی‌شود؛ پس هر leader جدید همهٔ ورودی‌های committed را از قبل دارد.

**FLP** (Fischer، Lynch و Paterson، ۱۹۸۵): در سیستم ناهمگام با امکان حتی یک crash، هیچ پروتکل اجماع قطعی‌ای نمی‌تواند پایان‌پذیری را تضمین کند. سیستم‌های واقعی **ایمنی را همیشه** حفظ می‌کنند و **زنده بودن را وقتی شبکه خوب رفتار کند** می‌گیرند (timeout، انتخابات تصادفی)؛ دقیقاً طراحی Raft.

**تکثیر با quorum بدون leader** (Dynamo، Cassandra): روی W replica بنویس، از R بخوان؛ `R + W > N` باعث می‌شود هر خواندن با آخرین نوشتن اشتراک داشته باشد. نوشتن‌های همروند هنوز برای تشخیص تعارض به نسخه‌گذاری نیاز دارند (ساعت برداری، یادداشت ۰۲).

## ۳. نمودار

</div>

```mermaid
sequenceDiagram
  participant C as Client
  participant L as Leader (term 3)
  participant F1 as Follower 1
  participant F2 as Follower 2
  C->>L: put(x, 5)
  L->>L: append log[7] = (term 3, x=5)
  par replicate
    L->>F1: AppendEntries(term 3, prev=6/3, [x=5])
    L->>F2: AppendEntries(term 3, prev=6/3, [x=5])
  end
  F1-->>L: ok (match log[7])
  Note over L: 2 of 3 have log[7] → committed
  L->>L: apply x=5
  L-->>C: ok
  F2--xL: (slow or partitioned; catches up later)
```

<div dir="rtl">

## ۴. مثال عملی: هم‌پوشانی quorum با جستجوی کامل، و failure detector خود کرنل

**(الف) کدام (R, W) برای N = 5 امن است؟** یک برنامهٔ کوتاه Go همهٔ مجموعه‌های خواندن به اندازهٔ R و همهٔ مجموعه‌های نوشتن به اندازهٔ W را می‌شمارد و زوج‌های بی‌اشتراک را حساب می‌کند (زوج بی‌اشتراک = خواندنی که ممکن است آخرین نوشتن را نبیند):

</div>

```go
for rs := uint(0); rs <= full; rs++ {
	if bits.OnesCount(rs) != r {
		continue
	}
	for ws := uint(0); ws <= full; ws++ {
		if bits.OnesCount(ws) == w && rs&ws == 0 {
			disjoint++
		}
	}
}
```

<div dir="rtl">

اجرای واقعی در container با image `golang:1.22` روی میزبان (`go1.22.12`)، 2026-11-15:

</div>

```text
N=5 R=1 W=5  R+W>N=true   disjoint (R,W) pairs=0
N=5 R=2 W=4  R+W>N=true   disjoint (R,W) pairs=0
N=5 R=3 W=3  R+W>N=true   disjoint (R,W) pairs=0
N=5 R=2 W=3  R+W>N=false  disjoint (R,W) pairs=10
N=5 R=1 W=1  R+W>N=false  disjoint (R,W) pairs=20
```

<div dir="rtl">

- سه سطر اول شرط `R + W > N` را دارند: صفر زوج بی‌اشتراک؛ هر خواندن آخرین نوشتن را می‌بیند.
- `R=2, W=3`: هر کدام از C(5,2) = 10 زوج خواندن دقیقاً یک مجموعهٔ نوشتن بی‌اشتراک دارد (سه گرهٔ دیگر): ۱۰ حالت خواندن کهنه.
- `R=1, W=1`: ۵ × ۴ = ۲۰. سریع، و نادرست در همروندی.
- بده‌بستان: `R=1, W=5` خواندن سریع می‌دهد ولی اگر حتی یک گره خاموش باشد نوشتن گیر می‌کند؛ `R=W=3` (اکثریت) برای هر دو خرابی دو گره را تحمل می‌کند.

**(ب) یک failure detector از نوع heartbeat داخل لینوکس.** نخ watchdog هر CPU یک timestamp را به‌روز می‌کند و یک timer آن را بررسی می‌کند:

`linux/kernel/watchdog.c · is_softlockup() · v6.18.63` ([Elixir L690](https://elixir.bootlin.com/linux/v6.18.63/source/kernel/watchdog.c#L690))

</div>

```c
  690  static int is_softlockup(unsigned long touch_ts,
  691  			 unsigned long period_ts,
  692  			 unsigned long now)
  693  {
  694  	if ((watchdog_enabled & WATCHDOG_SOFTOCKUP_ENABLED) && watchdog_thresh) {
  ...
  712  		if (time_after_eq(now, period_ts + get_softlockup_thresh() * 3 / 4))
  713  			scx_softlockup(now - touch_ts);
  714  
  715  		/* Warn about unreasonable delays. */
  716  		if (time_after(now, period_ts + get_softlockup_thresh()))
  717  			return now - touch_ts;
  718  	}
  719  	return 0;
  720  }
```

<div dir="rtl">

- `period_ts` همان heartbeat است: آخرین باری که این CPU توانسته task مربوط به watchdog را اجرا کند.
- **خط‌های ۷۱۶ و ۷۱۷**: اگر بیش از آستانه heartbeat نیامده باشد ← گزارش «soft lockup» همراه با طول توقف. آستانه `watchdog_thresh * 2` است (`get_softlockup_thresh()` در خط‌های ۶۰۱ تا ۶۰۳) و `watchdog_thresh` به‌طور پیش‌فرض ۱۰ است (خط ۴۹): یعنی ۲۰ ثانیه.
- **خط‌های ۷۱۲ و ۷۱۳**: در سه‌چهارم آستانه اول یک بازیابی ارزان‌تر امتحان می‌شود: از sched_ext خواسته می‌شود scheduler بدرفتار BPF را بیرون بیندازد. واکنش پله‌ای، مثل «اول مشکوک شو، بعد عمل کن».
- همان بده‌بستان detectorهای توزیع‌شده: CPUی که فقط گرسنه مانده (مثلاً یک بخش طولانی غیرقابل‌preempt) دقیقاً مثل CPUی که واقعاً گیر کرده گزارش می‌شود. آستانهٔ کوتاه‌تر گیرهای واقعی را زودتر و هشدارهای نادرست را بیشتر می‌دهد.

## ۵. حالت‌های مرزی و دام‌ها

- **Split brain**: بعد از partition دو گره هر دو خود را primary می‌دانند. جلوگیری با lease اکثریت، epoch/term و fencing token که storage بررسی‌شان می‌کند.
- **اندازهٔ زوج cluster** چیزی نمی‌خرد: ۴ گره مثل ۳ گره فقط ۱ crash را تحمل می‌کند و partition دوبه‌دو هر دو نیمه را متوقف می‌کند.
- **خرابی‌های هم‌بسته** (یک rack، یک باگ کرنل، یک پیکربندی بد که همه‌جا push شده) فرض استقلال پشت f را می‌شکنند.
- **غیرقطعی بودن در SMR** (timestamp، عدد تصادفی، زمان‌بندی نخ‌ها، ترتیب پیمایش hash map) باعث واگرایی replicaها با وجود log یکسان می‌شود. leader باید این مقادیر را تعیین و در log ثبت کند.
- **committed ≠ applied ≠ تأییدشده برای client**: crash بین این مراحل نباید فرمان را گم یا دو بار اعمال کند؛ clientها همچنان به شناسهٔ درخواست نیاز دارند (یادداشت ۰۱).
- **خواندن از follower** ممکن است دادهٔ کهنه بدهد؛ خواندن linearizable از leader با بررسی quorum یا lease انجام می‌شود.
- **timeoutهای خیلی تنگ** روی شبکهٔ پرترافیک طوفان انتخابات می‌سازند: cluster وقتش را صرف انتخاب leader می‌کند به‌جای سرویس‌دهی.

## ۶. نکته‌های امتحانی

- Fail-stop: f+1؛ crash در شبکهٔ ناهمگام: 2f+1 (quorum اکثریت)؛ Byzantine: 3f+1.
- ایمنی quorum: `R + W > N` (و `2W > N` برای مرتب کردن نوشتن‌های همروند)؛ اکثریت = `⌊N/2⌋ + 1`.
- primary-backup به تشخیص خرابی تکیه دارد؛ SMR به اجماع روی log.
- Raft: election timeout تصادفی، term، یک رأی در هر term، `AppendEntries` با log matching روی `(prevIndex, prevTerm)`، commit با اکثریت، بررسی به‌روز بودن هنگام رأی.
- FLP: هیچ اجماع قطعی‌ای در سیستم ناهمگام با یک crash پایان‌پذیری را تضمین نمی‌کند؛ ایمنی را نگه دار و زنده بودن را با timeout بگیر.
- failure detector مشکوک می‌شود، نمی‌داند. معادل کرنلی: soft-lockup detector (`is_softlockup()`، آستانهٔ `2 × watchdog_thresh` یعنی ۲۰ ثانیه به‌طور پیش‌فرض).
- مقاله‌ها: Fischer، Lynch و Paterson (۱۹۸۵)؛ Lamport، *Paxos Made Simple* (۲۰۰۱)؛ Ongaro و Ousterhout (۲۰۱۴)، *In Search of an Understandable Consensus Algorithm*.

## ۷. پیوندها

- درس: [`../lesson.fa.md`](../lesson.fa.md) بخش ۴.۵ (تحمل خطا)
- آزمایش‌ها: [`../labs/02-rpc-idempotency/`](../labs/02-rpc-idempotency/) (تکرار و idempotency سمت client تحمل خطاست)؛ [`../labs/01-lamport-vector-clocks/`](../labs/01-lamport-vector-clocks/) (مسئلهٔ ترتیبی که اجماع حل می‌کند)
- آزمون: [`../quiz.fa.md`](../quiz.fa.md) پرسش ۱۳ (طراحی KV store تکثیرشده)، پرسش شفاهی O2 (هزینهٔ ساعت برداری و جایگزین‌ها)
- مرتبط: [`01-rpc-semantics.fa.md`](01-rpc-semantics.fa.md) · [`02-lamport-vector-clocks.fa.md`](02-lamport-vector-clocks.fa.md)

</div>
