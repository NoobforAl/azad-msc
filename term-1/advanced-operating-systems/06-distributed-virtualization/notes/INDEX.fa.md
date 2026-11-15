<div dir="rtl">

# یادداشت‌های ماژول ۶ — فهرست

> ماژول ۶ · سیستم‌عامل توزیع‌شده و مجازی‌سازی · نسخه‌های ثابت: Linux **v6.18.63** و OpenBSD **`8cada8c`** · نسخهٔ انگلیسی: [`INDEX.en.md`](INDEX.en.md) · درس: [`../lesson.fa.md`](../lesson.fa.md)

به ترتیب بخوانید. یادداشت‌های ۰۱ تا ۰۵ نیمهٔ توزیع‌شده‌اند (نظریه + آزمایش‌های Go)؛ یادداشت‌های ۰۶ تا ۰۸ نیمهٔ مجازی‌سازی (کد کرنل + آزمایش‌های C). هر یادداشت همان ۷ بخش را دارد: خلاصه، توضیح، نمودار، مثال کاربردی، دام‌ها، نکته‌های امتحانی، پیوندها.

| # | یادداشت | در یک خط | درس | آزمایش | زمان |
|---|---|---|---|---|---|
| ۰۱ | [معناشناسی RPC](01-rpc-semantics.fa.md) | یک فراخوانی راه دور وقتی پیام‌ها گم می‌شوند چه قولی می‌تواند بدهد: at-most-once، at-least-once و فیلتر تکراری‌ها برای *اثر* exactly-once | ۴.۱ | [02-rpc-idempotency](../labs/02-rpc-idempotency/) | ۴۰ دقیقه |
| ۰۲ | [ساعت‌های Lamport و برداری](02-lamport-vector-clocks.fa.md) | مرتب کردن رخدادها بدون ساعت مشترک: رابطهٔ happened-before، برچسب زمانی Lamport، و ساعت برداری که هم‌زمانی را تشخیص می‌دهد | ۴.۲ | [01-lamport-vector-clocks](../labs/01-lamport-vector-clocks/) | ۵۰ دقیقه |
| ۰۳ | [همگام‌سازی ساعت: NTP، PTP و chrony](03-clock-sync-ntp-ptp.fa.md) | ساعت‌های واقعی چطور نزدیک هم نگه داشته می‌شوند: تخمین offset و delay، تنظیم تدریجی با `adjtimex`، برچسب زمانی سخت‌افزاری | ۴.۳ | — | ۳۵ دقیقه |
| ۰۴ | [بن‌بست توزیع‌شده و snapshot](04-distributed-deadlock-snapshots.fa.md) | گراف انتظار روی چند ماشین، edge chasing، بن‌بست‌های شبح، snapshot سازگار Chandy–Lamport | ۴.۴ | — | ۴۰ دقیقه |
| ۰۵ | [تحمل خطا و تکثیر](05-fault-tolerance-replication.fa.md) | مدل‌های خرابی، f+1 / 2f+1 / 3f+1، primary-backup در برابر state machine replication، quorum و پیش‌نمایشی از Raft | ۴.۵ | — | ۴۵ دقیقه |
| ۰۶ | [Hypervisorها: trap-and-emulate، VT-x و EPT](06-hypervisors-vtx-ept.fa.md) | قضیهٔ Popek–Goldberg، چرا x86 به VT-x نیاز داشت، حالت root/non-root، VMCS، VM exit، پیمایش ۲۴ دسترسی EPT | ۴.۶ | [05-vmexit-cost](../labs/05-vmexit-cost/) | ۴۵ دقیقه |
| ۰۷ | [معماری KVM](07-kvm-architecture.fa.md) | مسیر `/dev/kvm` ← fd مربوط به VM ← fd مربوط به vCPU، حلقهٔ `KVM_RUN`، exit داخل کرنل در برابر exit به فضای کاربر؛ مقایسه با vmm/vmd در OpenBSD | ۴.۷ | [04-kvm-client](../labs/04-kvm-client/) | ۵۰ دقیقه |
| ۰۸ | [Container = namespaceها + cgroup v2](08-containers-namespaces-cgroups.fa.md) | `nsproxy`، ۸ نوع namespace، قاعدهٔ fork در PID namespace، محدودیت‌های cgroup v2؛ مقایسه با pledge/unveil در OpenBSD | ۴.۸ | [03-mini-container](../labs/03-mini-container/) | ۵۰ دقیقه |

**جمع:** حدود ۶ ساعت مطالعه، پیش از آزمایش‌ها.

مسیر پیشنهادی:

۱. اگر اول نظریه را دوست دارید: ۰۲ ← ۰۱ ← ۰۴ ← ۰۵ ← ۰۳ (برای تعریف cut سازگار در ۰۴ به ساعت‌ها نیاز دارید).
۲. اگر از سمت کرنل شروع می‌کنید: ۰۶ ← ۰۷ ← ۰۸؛ یادداشت ۰۶ پیش‌نیاز ۰۷ است.
۳. هر آزمایش را درست بعد از یادداشتش انجام دهید؛ آزمون ([`../quiz.fa.md`](../quiz.fa.md)) برای هر پرسش یادداشت مربوط را ذکر می‌کند.

کد کرنل یادداشت‌های ۰۶ تا ۰۸ در [`../kernel-walkthrough.fa.md`](../kernel-walkthrough.fa.md) جمع شده است.

</div>
