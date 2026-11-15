<div dir="rtl">

# راهنمای استفاده با `make`

لازم نیست بدانید چه چیزی نصب کنید: `make doctor` را بزنید تا خودش بگوید.

</div>

```bash
make doctor     # 1. check your machine; it prints what is missing and how to install it
make view       # 2. download what the decks need, start the lab VM, open the slides in your browser
make stop       # 3. when done: stop the slide server and shut the VM down
```

<div dir="rtl">

برای labها یک بار `make vm-create` (ساخت VM، حدود ۱۰ دقیقه) و بعد `make vm-ssh`. دستور `make clean` همه‌چیز را متوقف می‌کند و پیش از پاک کردن cache **می‌پرسد**. `make help` همهٔ دستورها را فهرست می‌کند.

**ویندوز:** این دستورها را از PowerShell، cmd یا Git Bash اجرا کنید. Makefile در پشت صحنه از bash ِ Git for Windows استفاده می‌کند، پس Git باید نصب باشد (`make doctor` بررسی می‌کند). نسخهٔ انگلیسی: [USAGE.md](USAGE.md).

---

## ۱. چه چیزهایی لازم است

`make doctor` همهٔ این‌ها را بررسی می‌کند. چیزی نصب نمی‌کند و exit code آن برابر تعداد موارد ضروریِ نصب‌نشده است.

</div>

| برای | ابزار | توضیح |
|---|---|---|
| همه‌چیز | `git`، `make`، Python ≥ 3.8 | در ویندوز، bash لازم برای `make` را Git for Windows فراهم می‌کند |
| اسلایدها | یک مرورگر به‌روز + اینترنت | reveal.js و فونت‌ها از CDN بار می‌شوند |
| خواندن کد kernel | سورس Linux و OpenBSD | `make sources` (حدود ۱ گیگابایت، shallow و sparse) |
| labها | VirtualBox (ویندوز و macOS) یا libvirt + KVM (لینوکس)، کلاینت SSH و کلید SSH | `make vm-create` ماشین را می‌سازد |
| VM در ویندوز | PowerShell 7 (`winget install Microsoft.PowerShell`)، Docker یا WSL | Docker یا WSL فقط یک بار برای ساختن ISO کوچک راه‌اندازی VM |
| اختیاری | `shellcheck`، `ctags` | برای `make check` و پیمایش کد |

<div dir="rtl">

**لازم نیست:** Node.js، npm یا هیچ مرحلهٔ build. اسلایدها فایل HTML ساده‌اند. `make view` چند فایلی را که لازم دارند (reveal.js و سه فونت، حدود ۰.۶ مگابایت) در `.cache/` دانلود می‌کند؛ پس از اولین اجرا اسلایدها آفلاین هم کار می‌کنند.

### cache (پوشهٔ `.cache/`، بیرون از git)

</div>

| پوشه | محتوا | حجم | پرکننده |
|---|---|---|---|
| `.cache/vendor/` | reveal.js 5.1.0 و فونت‌ها برای اسلاید آفلاین | حدود ۰.۶ MB | `make view`، `make assets` |
| `.cache/downloads/` | image ابری Ubuntu 24.04، فایل‌های `.deb` کرنل 6.18.63، ISO راه‌اندازی VM | حدود ۰.۸ GB | `make cache`، `make vm-create` |
| `.cache/vm/` | خود VM آزمایشگاه (دیسک و snapshotها) | حدود ۸ GB | `make vm-create` |
| `.cache/run/` | شمارهٔ پردازهٔ سرورهای اسلاید در حال اجرا | ناچیز | `make view`/`slides`؛ با `make stop` پاک می‌شود |

<div dir="rtl">

هیچ چیز دو بار دانلود نمی‌شود: `make vm-create` بعدی همان image و فایل‌های کرنل را دوباره استفاده می‌کند. `make clean` می‌پرسد چه چیزی پاک شود: **k** (نگه‌داشتن همه)، **d** (فقط دانلودها) یا **a** (همه، شامل VM). برای رد شدن از سؤال: `CACHE=keep`، `CACHE=downloads` یا `CACHE=all`.

### نصب `make` در ویندوز
یکی از این‌ها را اجرا کنید و Git Bash را دوباره باز کنید:

</div>

```powershell
scoop install make          # https://scoop.sh
choco install make          # https://chocolatey.org
winget install ezwinports.make
```

<div dir="rtl">

---

## ۲. اسلایدها

</div>

| دستور | کار |
|---|---|
| `make view` | همه در یک دستور: cache فایل‌های اسلاید، روشن کردن VM اگر ساخته شده، سرو و باز کردن فهرست deckها |
| `make stop` | توقف همهٔ سرورهای اسلاید و خاموش کردن VM (از هر ترمینالی) |
| `make slides` | مخزن را روی `http://127.0.0.1:8000/` سرو می‌کند و فهرست همهٔ deckها را باز می‌کند؛ با Ctrl+C متوقف می‌شود |
| `make deck M=04` | deck درس ماژول ۰۴ (انگلیسی) |
| `make deck M=04 L=fa` | همان deck به فارسی |
| `make deck M=02 LAB=03` | deck آزمایش ۰۳ از ماژول ۰۲ |
| `make slides PORT=8080` | اگر پورت 8000 اشغال است |
| `make view NOBROWSER=1` | همان، بدون باز کردن مرورگر (برای ماشین راه‌دور یا بدون صفحه‌نمایش) |
| `make list` | فهرست ماژول‌ها، noteها و labها |
| `make browser-lab` | VM ندارید؟ آزمایشگاه مرورگر را باز می‌کند: یک کرنل واقعی ۳۲ بیتی Linux داخل مرورگر با ۱۰ آزمایش کوچک (یک بار حدود ۱۳ مگابایت دانلود می‌شود) |
| `make pdf M=04` | خروجی PDF درس ماژول ۰۴ در `exports/` (هر اسلاید یک صفحهٔ وکتور، انیمیشن‌ها در حالت نهایی) |
| `make pptx M=04` | خروجی PowerPoint در `exports/`: هر اسلاید یک تصویر، همراه با یادداشت‌های سخنران و افکت گذار |
| `make pdf M=02 ALL=1 L=fa` | همهٔ deckهای ماژول ۰۲ (درس و همهٔ labها) به فارسی. گزینه‌ها: `M` `L` `LAB` `ALL=1` `OUT=<dir>` |

<div dir="rtl">

داخل deck:
- **S** یادداشت‌های سخنران را باز می‌کند.
- **F** تمام‌صفحه می‌کند.
- **Esc** نمای کلی اسلایدها را نشان می‌دهد.
- در فهرست اسلایدها (صفحهٔ اصلی) یک بار **English** یا **فارسی** را بالای صفحه انتخاب کنید: کل صفحه (متن، جهت، نام ماژول‌ها و آزمایش‌ها) به همان زبان درمی‌آید و همهٔ اسلایدها با همان زبان باز می‌شوند. انتخاب شما در مرورگر به خاطر سپرده می‌شود.
- کلید **A** انیمیشن را روشن/خاموش می‌کند. کلید **T** نوار ابزار را نشان می‌دهد (با بردن ماوس به گوشهٔ پایین‌راست هم ظاهر می‌شود): نوع افکت گذار، سرعت انیمیشن، تمام‌صفحه و **خروجی PDF**.
- افکت‌های گذار: `fade` (پیش‌فرض)، `slide`، `convex`، `concave`، `zoom`، `none`. از نوار ابزار انتخاب کنید یا `?transition=slide` را به URL اضافه کنید.
- برای انیمیشن‌های دلخواه از کلاس‌های بخش ۱۲٫۱ در <bdi dir="ltr">_shared/slide-design-system.md</bdi> استفاده کنید (`fragment anim-up`، `loop-pulse`، `data-auto-animate`، …).

### VM و VirtualBox و Docker ندارید؟

از بهتر به بدتر: **VM** همهٔ آزمایش‌ها را اجرا می‌کند؛ **Docker** فقط برای آزمایش‌های user-space کافی است (container از کرنل میزبان استفاده می‌کند)؛ **آزمایشگاه مرورگر** فقط ایده‌ها را نشان می‌دهد. به‌جای VirtualBox می‌توانید از **QEMU** ساده استفاده کنید (بدون Docker یا WSL): `make qemu-vm CMD=create` و بعد `CMD=start|stop|status|ssh|snapshot|restore` (با `DRY=1` فقط پیش‌نمایش می‌دهد). برای آزمایشگاه مرورگر باید **این مخزن را clone کنید و محلی اجرا کنید**: `git clone <repository-url>`، وارد پوشه شوید و `make browser-lab` را بزنید. به‌صورت فایل ساده باز نمی‌شود. جزئیات و محدودیت‌ها: <bdi dir="ltr">_shared/browser-lab/README.md</bdi>.

### انتشار وب‌سایت (GitHub Pages)

کل فضای کار می‌تواند یک وب‌سایت باشد: **خانه ← ترم ۱ ← سیستم‌عامل پیشرفته ← درس یا آزمایش**، فارسی و انگلیسی، سازگار با موبایل و بدون هیچ درخواست به سرویس‌های بیرونی. دستور `make site` آن را در `site/` می‌سازد (پیش از انتشار `make security` را بزنید).

۱. مخزن باید **عمومی (public)** باشد (برای مخزن خصوصی، Pages به پلن پولی GitHub نیاز دارد).
۲. روی `main` push کنید. workflow به نام `.github/workflows/pages.yml` ابتدا دنبال secret می‌گردد، سپس سایت را می‌سازد و منتشر می‌کند.
۳. یک بار: **Settings ← Pages ← Build and deployment ← Source: GitHub Actions**.
۴. سایت در `https://<owner>.github.io/<repository>/` ظاهر می‌شود (برای `NoobforAl/azad-msc`: `https://noobforal.github.io/azad-msc/`).
۵. ساب‌دامنهٔ خودتان (مثلاً `os.example.com`): در DNS یک رکورد **CNAME** به `<owner>.github.io` بسازید و بعد در **Settings ← Pages ← Custom domain** وارد کنید و *Enforce HTTPS* را بزنید. (فایل `CNAME` داخل مخزن در انتشار با Actions نادیده گرفته می‌شود.)

صفحه‌های منتشرشده **یادداشت‌های سخنران** و فیلدهای پرنشدهٔ اسلاید عنوان (مثل `[Presenter]`) را ندارند (deckهای محلی شما آن‌ها را نگه می‌دارند؛ با `python _shared/tools/build_site.py --keep-notes` یادداشت‌ها هم منتشر می‌شوند). هر صفحه می‌گوید که مطلب مطالعاتی غیررسمی است. پیش از push دستورهای `make fix` و `make security` را بزنید. آزمایشگاه مرورگر و ابزارهای VM جزو وب‌سایت نیستند (اجرای محلی می‌خواهند). دربارهٔ امنیت: <bdi dir="ltr">SECURITY.md</bdi>.

### منابع بیشتر برای مطالعه

آخرین اسلاید هر درس («ادامهٔ مطالعه») و فایل <bdi dir="ltr">term-1/advanced-operating-systems/RESOURCES.fa.md</bdi> کتاب، مقاله و ابزارهایی را فهرست می‌کنند که از فهرست‌های *awesome-os* در GitHub انتخاب شده‌اند و همهٔ لینک‌هایشان بررسی شده است. برای تغییر، فایل <bdi dir="ltr">_shared/resources/awesome-os.json</bdi> را ویرایش کنید و <bdi dir="ltr">python _shared/tools/add_references.py</bdi> را اجرا کنید (گزینهٔ `--check` پیش از ارائه لینک‌ها را دوباره می‌آزماید).

### خروجی PDF یا PowerPoint

`make pdf M=04` و `make pptx M=04` به **Edge، Chrome یا Chromium** نیاز دارند (`make doctor` نشان می‌دهد کدام پیدا شد). برای PowerPoint باید `pip install python-pptx` هم اجرا شود. فایل‌ها در `exports/` (در git نادیده گرفته می‌شود) ذخیره می‌شوند؛ یک deck بیست‌اسلایدی حدود ۳۰ ثانیه طول می‌کشد.

- **PDF**: متن قابل انتخاب است و هر اسلاید در حالت نهایی (همهٔ مراحل کلیکی نمایان) ذخیره می‌شود.
- **PPTX**: اسلایدها *تصویرِ* deck هستند؛ ظاهر دقیقاً یکی است ولی متن قابل ویرایش نیست و مراحل کلیکی در یک اسلاید نهایی ادغام می‌شوند. یادداشت‌های سخنران به بخش notes در PowerPoint کپی می‌شوند و هر اسلاید افکت گذار fade دارد. برای تغییر محتوا، deck با فرمت HTML را ویرایش و دوباره خروجی بگیرید.
- ترمینال در دسترس نیست؟ دکمهٔ **خروجی PDF** در نوار ابزار deck پنجرهٔ چاپ را باز می‌کند (گزینهٔ *Save as PDF*، حاشیه *None*، background graphics روشن).

چرا سرور لازم است؟ اگر فایل `.html` را مستقیم باز کنید (`file://`)، مسیر theme مشترک خراب می‌شود. همیشه از `make slides` یا `make deck` استفاده کنید.

### ویرایش اسلایدها
- **deckهای درس** (<bdi dir="ltr">NN-*/slides/lesson.en.html</bdi> و `.fa.html`) HTML دست‌نویس‌اند. مستقیم ویرایش کنید و صفحه را تازه کنید.
- **deckهای lab** ساختنی‌اند. فایل <bdi dir="ltr">NN-*/slides/labs.content.py</bdi> را ویرایش کنید (انگلیسی و فارسی کنار هم) و `make decks` را بزنید. فایل‌های <bdi dir="ltr">slides/labs/*.html</bdi> را دستی ویرایش نکنید؛ `make decks` آن‌ها را بازنویسی می‌کند.
- پس از ویرایش `make check` را بزنید. این دستور بررسی می‌کند که هر اسلاید یادداشت سخنران و عنوان دارد و مسیر theme درست است، و اسکریپت‌های lab را با shellcheck بررسی می‌کند.

---

## ۳. ماشین مجازی آزمایشگاه

labهای سطح kernel داخل یک VM یک‌بارمصرف اجرا می‌شوند، هرگز روی ماشین خودتان.

</div>

| دستور | کار |
|---|---|
| `make vm-create` | ساخت `aos-lab` در `.cache/vm/`: Ubuntu 24.04، ابزارهای lab، کرنل درس 6.18.63 و snapshot `fresh`. ویندوز و macOS با VirtualBox و لینوکس با libvirt. بار اول حدود ۱۰ دقیقه؛ دانلودها cache می‌شوند. با VirtualBox، `KERNEL=stock` کرنل 6.8 خود Ubuntu را نگه می‌دارد |
| `make vm-start` / `make vm-stop` | روشن کردن بدون صفحه‌نمایش / خاموش کردن تمیز |
| `make vm-status` | وضعیت VM و kernel در حال اجرا |
| `make vm-ssh` | shell داخل VM. در VirtualBox، SSH روی `127.0.0.1:2222` با کاربر `fred` |
| `make vm-snapshot SNAP=before-lab4` | گرفتن snapshot (VM باید خاموش باشد) |
| `make vm-restore SNAP=fresh` | برگشت به snapshot (VM باید خاموش باشد) |

<div dir="rtl">

- **snapshot `fresh`:** VM این درس از قبل این snapshot را دارد: Ubuntu 24.04، لینوکس mainline نسخهٔ **6.18.63**، همهٔ ابزارهای lab و یک `~/work` خالی.
- **فایل‌های lab:** با این دستور کپی کنید: <bdi dir="ltr">scp -P 2222 -r term-1/advanced-operating-systems/04-memory/labs fred@127.0.0.1:~/work/</bdi>
- **نام یا کاربر دیگر:** متغیرها را عوض کنید، مثلاً <bdi dir="ltr">make vm-ssh VM=my-vm VM_USER=me VM_PORT=2223</bdi>.

**محدودیت‌های VirtualBox روی ویندوزی که Hyper-V در آن فعال است** (Docker Desktop و WSL، Hyper-V را روشن می‌کنند):
- شمارنده‌های سخت‌افزاری کارایی وجود ندارند؛ <bdi dir="ltr">perf stat -e cycles</bdi> عبارت `<not supported>` نشان می‌دهد.
- داخل VM، `/dev/kvm` وجود ندارد.

README هر lab می‌گوید کدام آزمایش‌ها تحت تأثیرند؛ بیشتر آزمایش‌ها بدون تغییر کار می‌کنند.

**یک قاعده برای trace:** هرگز tracer توابع kernel (ftrace) را بدون filter روشن نکنید. از <bdi dir="ltr">trace-cmd -g &lt;fn&gt; -l &lt;fn&gt;</bdi>، محدودیت عمق و <bdi dir="ltr">timeout 10</bdi> استفاده کنید؛ وگرنه VM ممکن است دچار soft lockup شود.

---

## ۴. خواندن کد kernel

</div>

```bash
make sources                                       # once: fetch Linux v6.18.63 + OpenBSD 8cada8c
make cite F=kernel/fork.c S=kernel_clone           # print a cited excerpt
make cite F=sys/kern/kern_fork.c S=fork1 R=openbsd
make cite F=mm/memory.c S=L6490                    # by line number
```

<div dir="rtl">

خروجی با همان خط ارجاعی شروع می‌شود که در همهٔ noteها آمده، مثلاً <bdi dir="ltr">linux/kernel/fork.c · kernel_clone() · v6.18.63 · L2578-2602</bdi>.

---

## ۵. همهٔ دستورها

</div>

| دستور | کاربرد |
|---|---|
| `make help` | فهرست دستورها و تنظیمات فعلی |
| `make doctor` | بررسی ماشین و راهنمای نصب |
| `make view` / `make stop` | روشن کردن اسلایدها و VM / توقف همه‌چیز |
| `make assets` / `make cache` | دانلود پیشاپیش فایل‌های اسلاید / همه‌چیز (شامل image و کرنل VM) |
| `make sources` | دریافت سورس‌های مرجع |
| `make slides` / `make deck` / `make list` | مرور اسلایدها |
| `make browser-lab` | آزمایشگاه مرورگر: یک کرنل کوچک واقعی Linux داخل مرورگر (بدون نیاز به VM) |
| `make site` / `make security` | ساخت وب‌سایت ثابت در `site/` / جست‌وجوی secret و اطلاعات خصوصی پیش از push |
| `make fix` / `make lint` | قالب‌بندی و lint کل کد (Python با ruff، فاصله‌های اضافی و پایان خط، بررسی نحو JS، shellcheck، JSON). `fix` فایل‌ها را تغییر می‌دهد و `lint` فقط گزارش می‌دهد (همین در CI اجرا می‌شود) |
| `make qemu-vm CMD=…` | VM آزمایشگاه با QEMU ساده به‌جای VirtualBox (`create`، `start`، `stop`، `status`، `ssh`، `snapshot`، `restore`) |
| `make pdf` / `make pptx` | خروجی PDF / PowerPoint از deck (`exports/`) |
| `make decks` | ساخت دوبارهٔ deckهای lab پس از ویرایش `labs.content.py` |
| `make cite` | نقل کد kernel همراه با ارجاع |
| `make vm-create` / `vm-start` / `vm-stop` / `vm-status` / `vm-ssh` | VM آزمایشگاه |
| `make vm-snapshot` / `vm-restore` | snapshotهای VM |
| `make check` | بررسی deckها، ابزارهای Python و اسکریپت‌های shell |
| `make clean` | توقف همه‌چیز، حذف فایل‌های ساختنی، پرسش دربارهٔ `.cache` (`CACHE=keep\|downloads\|all`) |

<div dir="rtl">

تنظیماتی که می‌توانید عوض کنید: `NOBROWSER=1`، `CACHE=keep|downloads|all`، `PORT=8000`، `COURSE=term-1/advanced-operating-systems`، `M=01`، `L=en`، `LAB=`، `ALL=`، `OUT=`، `CMD=`، `DRY=`، `VM=aos-lab`، `VM_USER=fred`، `VM_PORT=2222`، `SNAP=fresh`.

## ۶. رفع اشکال

</div>

| نشانه | راه‌حل |
|---|---|
| `make: command not found` | make را نصب کنید (بخش ۱) |
| `Git Bash not found` | Git for Windows را نصب کنید: `winget install Git.Git` |
| `make view` می‌گوید VM ساخته نشده | یک بار `make vm-create` را بزنید؛ اسلایدها بدون VM هم کار می‌کنند |
| `cannot listen on 127.0.0.1:8000` | برنامهٔ دیگری پورت را گرفته: `make slides PORT=8080` |
| deck بدون استایل است | اینترنت (CDN) قطع است یا فایل را با `file://` باز کرده‌اید؛ از `make slides` استفاده کنید |
| جای لوگو نوشته `[University logo]` | فایل `_shared/brand/azad-logo.png` را بررسی کنید (در مخزن هست؛ اگر پاک شده، دوباره بگذارید) |
| `make vm-ssh` گیر می‌کند یا رد می‌شود | VM هنوز در حال بوت است؛ ۳۰ ثانیه صبر کنید و `make vm-status` را ببینید |
| `perf stat -e cycles` می‌گوید `<not supported>` | در VirtualBox روی Hyper-V طبیعی است؛ از رویدادهای نرم‌افزاری (`task-clock`، `page-faults`) استفاده کنید |
| `stress-ng --cpu` در VM با SIGILL می‌میرد | از `stress-ng --cpu N --cpu-method int64` استفاده کنید |
| VM پس از یک lab خراب شده | `make vm-stop && make vm-restore SNAP=fresh && make vm-start` |
