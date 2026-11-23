# Lab-deck content for 01-processes. Render: python _shared/tools/labdeck.py <this file>
COURSE = {"en": "Advanced Software Engineering · 01 Processes", "fa": "مهندسی نرم‌افزار پیشرفته · ۰۱ فرایندها"}
CAP = {
    "en": "Windows 11, Git Bash, Python 3.12, Go, 2026-11-23",
    "fa": "Windows 11، Git Bash، Python 3.12، Go، ۱۴۰۵/۰۹/۰۲",
}

LABS = [
    dict(
        slug="01-dora-metrics",
        num="01.1",
        title={"en": "DORA metrics from a Git history", "fa": "معیارهای DORA از تاریخچهٔ Git"},
        goal={
            "en": "Compute deployment frequency, lead time, change failure rate and time to restore from tags and commits, and learn what each number cannot tell you.",
            "fa": "فرکانس استقرار، lead time، نرخ شکست تغییر و زمان بازیابی را از tagها و commitها حساب کنید و بفهمید هر عدد چه چیزی را نشان نمی‌دهد.",
        },
        where={"en": "any machine with Git and Python", "fa": "هر ماشین دارای Git و Python"},
        setup_cards=[
            (
                "r-store",
                {"en": "Scratch repo", "fa": "مخزن آزمایشی"},
                {"en": "seed_repo.sh: 32 commits, 11 tags", "fa": "seed_repo.sh: ‏۳۲ commit و ۱۱ tag"},
            ),
            ("r-service", {"en": "Script", "fa": "اسکریپت"}, {"en": "dora.py (stdlib only)", "fa": "dora.py (فقط کتابخانهٔ استاندارد)"}),
            (
                "r-infra",
                {"en": "Convention", "fa": "قرارداد"},
                {
                    "en": "deployment = tag v*; Fixes-release: trailer",
                    "fa": "استقرار = tag به شکل v*؛ و trailer به نام Fixes-release:",
                },
            ),
            (
                "r-client",
                {"en": "Report", "fa": "گزارش"},
                {"en": "4 metrics + what is not measured", "fa": "چهار معیار + آنچه اندازه‌گیری نمی‌شود"},
            ),
        ],
        steps=[
            '$ SCRATCH="${TMPDIR:-/tmp}/ase-lab01"',
            '$ bash seed_repo.sh "$SCRATCH/dora-demo"',
            '$ python dora.py --repo "$SCRATCH/dora-demo"',
            '$ python dora.py --repo "$SCRATCH/dora-demo" --date committer',
            '$ python dora.py --repo "$SCRATCH/dora-demo" --json > dora.json',
        ],
        expected=[
            "Deployment frequency",
            "!  deployments            11  (2026-03-05 10:00 to 2026-04-24 15:00, 50.2 days)",
            "  per week               1.53  (in 8 different weeks)",
            "Lead time for changes  (30 released commits, commit -> first tag containing it)",
            "!  median                 46.5 h (1 d 22.5 h)",
            "  90th percentile        119.0 h (4 d 23.0 h)",
            "Change failure rate",
            "!  failed deployments     3 of 11  v0.2.0, v0.4.0, v0.6.0",
            "Time to restore service",
            "  v0.6.0                 126.0 h (5 d 6.0 h)",
            "!  median                 24.0 h (1 d 0.0 h)",
            "Not measured",
            "  2 of 32 commits are not in any release yet (they have no lead time)",
        ],
        observe=[
            (
                {"en": "Restore time includes waiting", "fa": "زمان بازیابی شامل انتظار هم هست"},
                {
                    "en": "v0.6.0: 126 h, the fix was written only after the weekend",
                    "fa": "v0.6.0: ‏۱۲۶ ساعت؛ اصلاح فقط بعد از آخر هفته نوشته شد",
                },
            ),
            (
                {"en": "The clock you choose matters", "fa": "ساعتی که انتخاب می‌کنید مهم است"},
                {
                    "en": "author vs committer date: median 46.5 h vs 45.5 h",
                    "fa": "تاریخ author در برابر committer: میانه ۴۶٫۵ در برابر ۴۵٫۵ ساعت",
                },
            ),
            (
                {"en": "It measures your convention", "fa": "قرارداد شما را اندازه می‌گیرد"},
                {
                    "en": "no Fixes-release trailer: failure rate 0%",
                    "fa": "بدون trailer به نام Fixes-release نرخ شکست ۰٪ می‌شود",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "no tags match 'v*'", "fa": "هیچ tagای با 'v*' نمی‌خواند"},
                {"en": "git fetch --tags", "fa": "git fetch --tags"},
            ),
            (
                {"en": "commit IDs differ from the README", "fa": "شناسهٔ commitها با README فرق دارد"},
                {
                    "en": "global Git config: signing, autocrlf",
                    "fa": "تنظیمات سراسری Git مثل signing و autocrlf",
                },
            ),
            (
                {"en": "unrecognized %(trailers", "fa": "خطای unrecognized %(trailers"},
                {"en": "Git older than 2.22: upgrade", "fa": "Git قدیمی‌تر از ۲٫۲۲ است؛ ارتقا دهید"},
            ),
        ],
        ext={
            "en": "Print the lead time per release, and detect failed deployments from subjects that start with Revert instead of the trailer. Which of the three failures does the revert rule miss?",
            "fa": "lead time هر release را چاپ کنید و شکست‌های استقرار را به‌جای trailer از subjectهایی که با Revert شروع می‌شوند تشخیص دهید. قاعدهٔ revert کدام یک از سه شکست را از دست می‌دهد؟",
        },
        captured=CAP,
    ),
    dict(
        slug="02-ci-quality-gates",
        num="01.2",
        title={
            "en": "CI quality gates: the same checks locally and in CI",
            "fa": "دروازه‌های کیفیت در CI: همان بررسی‌ها روی لپ‌تاپ و در CI",
        },
        goal={
            "en": "Run gofmt, go vet, ruff, tests and a coverage threshold with one script, also in GitHub Actions, and make each gate fail on purpose.",
            "fa": "gofmt، go vet، ruff، تست‌ها و آستانهٔ coverage را با یک اسکریپت اجرا کنید، در GitHub Actions هم، و هر دروازه را عمداً شکست بدهید.",
        },
        where={"en": "Go, Python, ruff, Git", "fa": "Go، Python، ruff و Git"},
        setup_cards=[
            (
                "r-client",
                {"en": "Gates", "fa": "دروازه‌ها"},
                {"en": "gofmt · vet · ruff · tests · coverage", "fa": "gofmt · vet · ruff · tests · coverage"},
            ),
            (
                "r-service",
                {"en": "Runner", "fa": "اجراکننده"},
                {"en": "tools/gates.py, exit code = failed gates", "fa": "tools/gates.py؛ کد خروج = تعداد دروازه‌های شکست‌خورده"},
            ),
            (
                "r-infra",
                {"en": "CI", "fa": "CI"},
                {"en": "GitHub Actions runs the same script", "fa": "GitHub Actions همان اسکریپت را اجرا می‌کند"},
            ),
            (
                "r-store",
                {"en": "Start", "fa": "نقطهٔ شروع"},
                {"en": "m0 scratch copy (prepare-m0.sh)", "fa": "کپی آزمایشی m0 ‏(prepare-m0.sh)"},
            ),
        ],
        steps=[
            '$ bash ../prepare-m0.sh "$SCRATCH" && cd "$SCRATCH"',
            '$ mkdir tools && cp "$LAB/gates.py" tools/',
            "$ python tools/gates.py",
            "$ printf '\\nvar   unformatted=1\\n' >> internal/catalog/catalog.go",
            "$ python tools/gates.py --only gofmt,vet",
            "$ git checkout internal/catalog/catalog.go",
            "# then break lint, tests, coverage the same way (README)",
        ],
        expected=[
            "$ python tools/gates.py",
            "gofmt     PASS  all Go files formatted",
            "vet       PASS  go vet ./... is clean",
            "ruff      PASS  All checks passed!",
            "tests     PASS  go test and unittest pass",
            "coverage  PASS  total 72.4% of statements (minimum 70.0%)",
            "0 of 5 gates failed",
            "$ python tools/gates.py --only gofmt,vet",
            "!gofmt     FAIL  needs gofmt: internal\\catalog\\catalog.go",
            "vet       PASS  go vet ./... is clean",
            "$ python tools/gates.py --only coverage",
            "!coverage  FAIL  total 61.8% of statements (minimum 70.0%)",
        ],
        observe=[
            (
                {"en": "One break, one gate", "fa": "یک خرابی، یک دروازه"},
                {
                    "en": "vet passes unformatted code; gofmt passes untested code",
                    "fa": "vet کد فرمت‌نشده را می‌پذیرد و gofmt کد بدون تست را",
                },
            ),
            (
                {"en": "Coverage caught what tests missed", "fa": "coverage چیزی را گرفت که تست‌ها ندیدند"},
                {
                    "en": "72.4% → 61.8% with every test still green",
                    "fa": "از ۷۲٫۴٪ به ۶۱٫۸٪ در حالی که همهٔ تست‌ها سبزند",
                },
            ),
            (
                {"en": "Local = CI", "fa": "محلی = CI"},
                {
                    "en": "the workflow's real step is python tools/gates.py",
                    "fa": "گام اصلی workflow همان python tools/gates.py است",
                },
            ),
            (
                {"en": "The template had a gap", "fa": "قالب اولیه یک شکاف داشت"},
                {
                    "en": "make lint test passes unformatted code: no gofmt, no coverage",
                    "fa": "make lint test کد فرمت‌نشده را می‌پذیرد؛ نه gofmt دارد نه coverage",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "ruff: command not found", "fa": "ruff: command not found"},
                {"en": "pip install ruff", "fa": "pip install ruff"},
            ),
            (
                {"en": "ruff errors only in the scratch copy", "fa": "خطای ruff فقط در کپی آزمایشی"},
                {
                    "en": "no ruff.toml: prepare-m0.sh copies it",
                    "fa": "ruff.toml نیست؛ prepare-m0.sh آن را کپی می‌کند",
                },
            ),
            (
                {"en": "green locally, red in CI", "fa": "محلی سبز، در CI قرمز"},
                {"en": "compare go version and Python version", "fa": "نسخهٔ Go و Python را مقایسه کنید"},
            ),
            (
                {"en": "workflow never starts", "fa": "workflow هرگز شروع نمی‌شود"},
                {"en": "file must be in .github/workflows/", "fa": "فایل باید در .github/workflows/ باشد"},
            ),
        ],
        ext={
            "en": "Add a sixth gate that runs ruff format --check. It fails on m0, so fix the formatting in a separate commit first. Then add a per-package coverage floor next to the total.",
            "fa": "دروازهٔ ششم را اضافه کنید که ruff format --check را اجرا می‌کند. روی m0 شکست می‌خورد، پس ابتدا فرمت را در یک commit جدا درست کنید. بعد کنار مجموع، حداقل coverage هر package را هم بگذارید.",
        },
        captured=CAP,
    ),
    dict(
        slug="03-cost-of-fault-simulation",
        num="01.3",
        title={
            "en": "What does a late fault cost? Simulation and 0.85% vs 7.5%",
            "fa": "یک خطای دیرهنگام چقدر هزینه دارد؟ شبیه‌سازی و ۰٫۸۵٪ در برابر ۷٫۵٪",
        },
        goal={
            "en": "Reproduce Schach's argument (10% off coding saves at most 0.85%, 10% off maintenance about 7.5%) and simulate the cost of faults by phase.",
            "fa": "استدلال Schach را بازتولید کنید (۱۰٪ صرفه‌جویی در کدنویسی حداکثر ۰٫۸۵٪ و در نگهداری حدود ۷٫۵٪ است) و هزینهٔ خطاها را به تفکیک فاز شبیه‌سازی کنید.",
        },
        where={"en": "Python only", "fa": "فقط Python"},
        setup_cards=[
            (
                "r-store",
                {"en": "Data", "fa": "داده"},
                {"en": "cost shares: Schach 8e ch. 1, Figs. 1.3 and 1.4", "fa": "سهم هزینه‌ها: Schach 8e ch. 1، شکل‌های ۱٫۳ و ۱٫۴"},
            ),
            (
                "r-service",
                {"en": "Model", "fa": "مدل"},
                {"en": "6 phases, cost × r per phase (assumption)", "fa": "۶ فاز، هزینه × r در هر فاز (فرض)"},
            ),
            (
                "r-infra",
                {"en": "Scenarios", "fa": "سناریوها"},
                {"en": "test only at the end vs inspections", "fa": "تست فقط در پایان در برابر inspection"},
            ),
            (
                "r-client",
                {"en": "Output", "fa": "خروجی"},
                {"en": "savings table + cost per phase", "fa": "جدول صرفه‌جویی + هزینه در هر فاز"},
            ),
        ],
        steps=[
            "$ python fault_cost.py --part economics",
            "$ python fault_cost.py --part simulation",
            "$ python fault_cost.py --part simulation --faults 100000",
            "$ python fault_cost.py --part simulation --r 1",
            "$ python fault_cost.py --part simulation --r 4",
        ],
        expected=[
            "era                                        dev % maint % code %  -10% coding -10% maint",
            "1976-81 projects (Fig. 1.3a, 1.4)             33      67     36        1.19%      6.70%",
            "!1992-98, 132 HP projects (Fig. 1.3b, 1.4)     25      75     34        0.85%      7.50%",
            "  scenario: test only at the end",
            "  total              1000     33362       34961",
            "  cost per fault 33.4 units; maintenance share of the cost 57%; faults found by users 19%",
            "  scenario: with inspections",
            "  total              1000     21092       23584",
            "!  cost per fault 21.1 units; maintenance share of the cost 51%; faults found by users 11%",
            "!  inspections cut the total cost to 63% of the test-only process",
        ],
        observe=[
            (
                {"en": "Coding is a small slice", "fa": "کدنویسی سهم کوچکی است"},
                {
                    "en": "-10% coding = 0.85-1.19% of total; -10% maintenance = 6.7-7.5%",
                    "fa": "۱۰٪ کمتر در کدنویسی = ۰٫۸۵ تا ۱٫۱۹٪ کل؛ در نگهداری = ۶٫۷ تا ۷٫۵٪",
                },
            ),
            (
                {"en": "Inspections move cost left", "fa": "inspection هزینه را به چپ می‌برد"},
                {
                    "en": "faults found by users: 19% → 11%",
                    "fa": "خطاهایی که کاربران پیدا می‌کنند: از ۱۹٪ به ۱۱٪",
                },
            ),
            (
                {"en": "Small runs are noisy", "fa": "اجراهای کوچک نویز دارند"},
                {
                    "en": "1000 faults: ~5% off the expected value; 100,000: 0.1%",
                    "fa": "با ۱۰۰۰ خطا حدود ۵٪ اختلاف با مقدار مورد انتظار؛ با ۱۰۰٬۰۰۰ خطا ۰٫۱٪",
                },
            ),
            (
                {"en": "It all hangs on the cost curve", "fa": "همه‌چیز به منحنی هزینه بستگی دارد"},
                {"en": "with r = 1 inspections save nothing", "fa": "با r = 1 هیچ صرفه‌ای از inspection نمی‌ماند"},
            ),
        ],
        pitfalls=[
            (
                {"en": "treating the output as data", "fa": "خروجی را داده فرض کردن"},
                {"en": "multipliers and rates are assumptions", "fa": "ضریب‌ها و نرخ‌ها فرض‌اند"},
            ),
            (
                {"en": "quoting 57% as Schach's number", "fa": "نقل ۵۷٪ به‌عنوان عدد Schach"},
                {
                    "en": "model counts fault fixing only; book: 67-75% of life-cycle cost",
                    "fa": "مدل فقط رفع خطا را می‌شمرد؛ کتاب: ۶۷ تا ۷۵٪ هزینهٔ چرخهٔ عمر",
                },
            ),
            (
                {"en": "--multipliers rejected", "fa": "--multipliers رد می‌شود"},
                {"en": "exactly six comma-separated numbers", "fa": "دقیقاً شش عدد با ویرگول"},
            ),
        ],
        ext={
            "en": "Make the cost depend on both the phase where the fault was introduced and the phase where it was found. Justify your rule and say which conclusion of this lab survives.",
            "fa": "هزینه را هم به فازی که خطا در آن وارد شده و هم به فازی که پیدا شده وابسته کنید. قاعدهٔ خود را توجیه کنید و بگویید کدام نتیجهٔ این آزمایش باقی می‌ماند.",
        },
        captured=CAP,
    ),
    dict(
        slug="04-git-bisect-worktrees",
        num="01.4",
        title={
            "en": "git bisect and git worktree on a seeded regression",
            "fa": "git bisect و git worktree روی یک regression کاشته‌شده",
        },
        goal={
            "en": "Find the commit that broke the project with git bisect run and a test, then test two releases side by side with git worktree.",
            "fa": "با git bisect run و یک تست، commitی را که پروژه را خراب کرد پیدا کنید؛ سپس با git worktree دو release را کنار هم تست کنید.",
        },
        where={"en": "Git, Go, Bash", "fa": "Git، Go و Bash"},
        setup_cards=[
            (
                "r-store",
                {"en": "Repo", "fa": "مخزن"},
                {"en": "m0 + 11 scripted commits, tags v1.0 and v1.1", "fa": "m0 + ‏۱۱ commit اسکریپتی، tagهای v1.0 و v1.1"},
            ),
            (
                "r-service",
                {"en": "Oracle", "fa": "oracle"},
                {"en": "bisect-test.sh: 0 good · 1 bad · 125 skip", "fa": "bisect-test.sh: ‏۰ سالم · ۱ خراب · ۱۲۵ رد کن"},
            ),
            (
                "r-infra",
                {"en": "Worktrees", "fa": "worktreeها"},
                {"en": "two releases side by side, one .git", "fa": "دو release کنار هم با یک .git"},
            ),
            (
                "r-client",
                {"en": "Result", "fa": "نتیجه"},
                {"en": "first bad commit, fix by git revert", "fa": "اولین commit خراب، رفع با git revert"},
            ),
        ],
        steps=[
            '$ bash seed_regression.sh "$SCRATCH/repo" && cd "$SCRATCH/repo"',
            "$ go test ./...                      # fails on HEAD",
            "$ git bisect start HEAD v1.0",
            '$ git bisect run bash "$LAB/bisect-test.sh"',
            "$ git bisect reset",
            "$ git worktree add ../rel-v1.0 v1.0",
            "$ git worktree add ../rel-v1.1 v1.1",
            "$ (cd ../rel-v1.0 && go test ./internal/catalog -run TestListIsSortedByID -count=1) &",
            "$ (cd ../rel-v1.1 && go test ./internal/catalog -run TestListIsSortedByID -count=1); wait",
        ],
        expected=[
            "bisect-test: build fails, skipping this commit",
            "Bisecting: 2 revisions left to test after this (roughly 2 steps)",
            "[e18cd1c242c78e1d816522936d134dbbc3bcb332] catalog: finish GetByTitle",
            "!f10c4bbc648959059cec1c25bc709ed01e35b123 is the first 'bad' commit",
            "    catalog: show newest course IDs first",
            "bisect found first 'bad' commit",
            "$ git worktree list",
            "/tmp/ase-lab04/rel-v1.0 32472f0 (detached HEAD)",
            "/tmp/ase-lab04/rel-v1.1 67a61f9 (detached HEAD)",
            "[v1.0] ok  \texample.com/registration/internal/catalog\t0.261s",
            "![v1.1] --- FAIL: TestListIsSortedByID (0.00s)",
        ],
        observe=[
            (
                {"en": "Six candidates, four checkouts", "fa": "شش کاندیدا، چهار checkout"},
                {"en": "one skipped (no build), three judged", "fa": "یکی رد شد (build نمی‌شود) و سه تا قضاوت شد"},
            ),
            (
                {"en": "Exit code 125 means skip", "fa": "کد خروج ۱۲۵ یعنی رد کن"},
                {
                    "en": "otherwise the WIP commit is named the culprit",
                    "fa": "وگرنه commit نیمه‌کاره به‌عنوان مقصر معرفی می‌شود",
                },
            ),
            (
                {"en": "Two tests fail, one cause", "fa": "دو تست شکست می‌خورد، یک علت"},
                {
                    "en": "the oracle tests the symptom you track",
                    "fa": "oracle باید نشانه‌ای را بسنجد که دنبالش هستید",
                },
            ),
            (
                {"en": "Two versions at once", "fa": "دو نسخه همزمان"},
                {"en": "v1.0 passes, v1.1 fails; no checkout, no stash", "fa": "v1.0 سالم و v1.1 خراب؛ بدون checkout و stash"},
            ),
        ],
        pitfalls=[
            (
                {"en": "bisect names an innocent commit", "fa": "bisect یک commit بی‌گناه را نشان می‌دهد"},
                {"en": "oracle returned 1 on build failure: use 125", "fa": "oracle در شکست build عدد ۱ داده؛ از ۱۲۵ استفاده کنید"},
            ),
            (
                {"en": "go test passes on a bad commit", "fa": "go test روی commit خراب سبز است"},
                {"en": "test cache: add -count=1", "fa": "cache تست؛ -count=1 را اضافه کنید"},
            ),
            (
                {"en": "'../rel-v1.0' already exists", "fa": "'../rel-v1.0' از قبل وجود دارد"},
                {"en": "git worktree remove or prune", "fa": "git worktree remove یا prune"},
            ),
            (
                {"en": "HEAD is detached afterwards", "fa": "بعد از bisect، HEAD جداشده است"},
                {"en": "git bisect reset", "fa": "git bisect reset"},
            ),
        ],
        ext={
            "en": "Write an end-to-end oracle in Python: start the API on a free port, request GET /courses, check that the first course is SE101, and return 0, 1 or 125. Confirm that bisect finds the same commit.",
            "fa": "یک oracle سرتاسری با Python بنویسید: API را روی یک پورت آزاد اجرا کنید، GET /courses بزنید، بررسی کنید اولین درس SE101 باشد و ۰، ۱ یا ۱۲۵ برگردانید. تأیید کنید bisect همان commit را پیدا می‌کند.",
        },
        captured=CAP,
    ),
    dict(
        slug="05-kanban-flow-metrics",
        num="01.5",
        title={
            "en": "Kanban flow metrics: cycle time, WIP and Little's law",
            "fa": "معیارهای جریان در Kanban: cycle time، WIP و قانون Little",
        },
        goal={
            "en": "Compute cycle time, lead time, throughput and WIP from an issue export, and show why a WIP limit shortens cycle time without lowering throughput.",
            "fa": "cycle time، lead time، throughput و WIP را از خروجی issueها حساب کنید و نشان دهید چرا سقف WIP بدون کاهش throughput زمان چرخه را کوتاه می‌کند.",
        },
        where={"en": "Python only", "fa": "فقط Python"},
        setup_cards=[
            (
                "r-store",
                {"en": "Data", "fa": "داده"},
                {"en": "two CSV exports, 55 synthetic issues", "fa": "دو فایل CSV با ۵۵ issue مصنوعی"},
            ),
            (
                "r-service",
                {"en": "Simulation", "fa": "شبیه‌سازی"},
                {"en": "3 developers: round-robin vs WIP limit 3", "fa": "سه توسعه‌دهنده: round-robin در برابر سقف WIP برابر ۳"},
            ),
            (
                "r-infra",
                {"en": "Metrics", "fa": "معیارها"},
                {"en": "cycle · lead · throughput · WIP · aging", "fa": "cycle · lead · throughput · WIP · aging"},
            ),
            (
                "r-client",
                {"en": "Law", "fa": "قانون"},
                {"en": "Little: L = λ × W", "fa": "Little: ‏L = λ × W"},
            ),
        ],
        steps=[
            "$ python flow_metrics.py issues-nolimit.csv --wip-limit 3",
            "$ python flow_metrics.py issues-wip3.csv --wip-limit 3",
            "$ python gen_issues.py > /tmp/check.csv",
            "$ diff /tmp/check.csv issues-nolimit.csv && echo identical",
            "$ for L in 1 2 3 4 5 6 none; do",
            "    python gen_issues.py --wip-limit $L > /tmp/limit-$L.csv; done",
        ],
        expected=[
            "$ python flow_metrics.py issues-nolimit.csv --wip-limit 3",
            "  mean 4.25 per week, min 2, max 8",
            "  cycle time     9.9     8.0    18    41",
            "  average 6.55, maximum 11",
            "!  days above the WIP limit of 3: 50 of 60",
            "$ python flow_metrics.py issues-wip3.csv --wip-limit 3",
            "  mean 4.33 per week, min 1, max 7",
            "!  cycle time     3.9     3.0     6    12",
            "  lead time      8.9     9.0    14    16",
            "  average 2.83, maximum 3",
            "  lambda 0.867 issues/day x W 3.21 days = 2.78   measured average WIP 2.83",
        ],
        observe=[
            (
                {"en": "Same throughput, shorter cycle", "fa": "همان throughput، چرخهٔ کوتاه‌تر"},
                {
                    "en": "4.25 vs 4.33 per week; cycle 9.9 → 3.9 d, p85 18 → 6 d",
                    "fa": "۴٫۲۵ در برابر ۴٫۳۳ در هفته؛ چرخه از ۹٫۹ به ۳٫۹ روز و p85 از ۱۸ به ۶ روز",
                },
            ),
            (
                {"en": "Lead time falls less", "fa": "lead time کمتر کاهش می‌یابد"},
                {
                    "en": "the queue moved to the backlog, it did not vanish",
                    "fa": "صف به backlog رفت، ناپدید نشد",
                },
            ),
            (
                {"en": "Little's law holds", "fa": "قانون Little برقرار است"},
                {"en": "λ × W = 2.78 vs measured WIP 2.83", "fa": "‏λ × W = ۲٫۷۸ در برابر WIP اندازه‌گیری‌شده ۲٫۸۳"},
            ),
            (
                {"en": "A limit below capacity costs throughput", "fa": "سقف کمتر از ظرفیت throughput را کم می‌کند"},
                {"en": "limit 1: 1.33 per week; limit 2: 2.50", "fa": "سقف ۱: ‏۱٫۳۳ در هفته؛ سقف ۲: ‏۲٫۵۰"},
            ),
        ],
        pitfalls=[
            (
                {"en": "cycle time 1 for same-day items", "fa": "cycle time برای کار همان‌روز برابر ۱ است"},
                {"en": "inclusive days by design", "fa": "روزها عمداً شامل دو سر بازه‌اند"},
            ),
            (
                {"en": "weekends inflate cycle time", "fa": "آخر هفته‌ها cycle time را بالا می‌برند"},
                {"en": "count working days if you must", "fa": "در صورت نیاز روزهای کاری را بشمارید"},
            ),
            (
                {"en": "Little's law off by more than 10%", "fa": "قانون Little بیش از ۱۰٪ اختلاف دارد"},
                {"en": "short window or unstable WIP", "fa": "بازهٔ کوتاه یا WIP ناپایدار"},
            ),
        ],
        ext={
            "en": "Print the cumulative flow per week (created, started, done) and explain what a widening gap between started and done looks like. Then add a context-switching penalty to the generator and measure how much worse no-limit gets.",
            "fa": "جریان تجمعی هر هفته را چاپ کنید (ایجاد، شروع، پایان) و توضیح دهید شکاف رو‌به‌رشد بین شروع و پایان چه شکلی است. سپس جریمهٔ تعویض زمینه را به مولد اضافه کنید و بسنجید حالت بدون سقف چقدر بدتر می‌شود.",
        },
        captured=CAP,
    ),
    dict(
        slug="06-timebox-vs-waterfall",
        num="01.6",
        title={
            "en": "Timeboxed sprints vs a waterfall plan",
            "fa": "اسپرینت‌های زمان‌بسته در برابر طرح آبشاری",
        },
        goal={
            "en": "Plan the same backlog as a waterfall project and as 3-week timeboxes, and see what each delivers by the deadline when estimates are wrong.",
            "fa": "همین backlog را یک بار به‌صورت پروژهٔ آبشاری و یک بار با timeboxهای سه‌هفته‌ای برنامه‌ریزی کنید و ببینید وقتی تخمین‌ها غلط‌اند هر کدام تا مهلت چه چیزی تحویل می‌دهد.",
        },
        where={"en": "Python only", "fa": "فقط Python"},
        setup_cards=[
            (
                "r-store",
                {"en": "Backlog", "fa": "backlog"},
                {"en": "12 items, 100 dev-days, 68 value points (invented)", "fa": "۱۲ مورد، ۱۰۰ نفر-روز، ۶۸ امتیاز ارزش (ساختگی)"},
            ),
            (
                "r-service",
                {"en": "Waterfall", "fa": "آبشاری"},
                {"en": "4 phases, shares from Schach Fig. 1.4", "fa": "۴ فاز با سهم‌های شکل ۱٫۴ کتاب Schach"},
            ),
            (
                "r-infra",
                {"en": "Timebox", "fa": "timebox"},
                {"en": "3-week sprints, cut scope when it does not fit", "fa": "اسپرینت سه‌هفته‌ای؛ هرچه جا نشود حذف می‌شود"},
            ),
            (
                "r-client",
                {"en": "Deadline", "fa": "مهلت"},
                {"en": "week 9, overrun 0% to 60%", "fa": "هفتهٔ ۹، فزونی تلاش ۰ تا ۶۰٪"},
            ),
        ],
        steps=[
            "$ cat backlog.csv",
            "$ python plan_compare.py",
            "$ python plan_compare.py --overrun 0.3",
            "$ python plan_compare.py --overrun 0.6",
            "$ for o in 0.08 0.09; do",
            '    python plan_compare.py --overrun $o | grep -E "everything|items delivered"; done',
        ],
        expected=[
            "$ python plan_compare.py --overrun 0.3",
            "!  everything is delivered at week 10.8 (MISSES the deadline by 1.8 weeks); nothing is delivered earlier",
            "  sprint 1 (week 3): committed 36.0 d  delivered REG-01, REG-02, REG-03  cut REG-04",
            "  sprint 3 (week 9): committed 35.6 d  delivered REG-07, REG-08, REG-09, REG-10  cut REG-12",
            "  not delivered at the deadline: REG-11, REG-12",
            "                                  waterfall  timeboxed",
            "  value delivered by week 3              0%        50%",
            "  value delivered by week 9              0%        96%",
            "!  items delivered at the deadline       0/12       10/12",
        ],
        observe=[
            (
                {"en": "Exact estimates: same result, other timing", "fa": "تخمین دقیق: همان نتیجه، زمان‌بندی متفاوت"},
                {
                    "en": "62% of the value by week 3 vs first release at week 8.3",
                    "fa": "۶۲٪ ارزش تا هفتهٔ ۳ در برابر اولین release در هفتهٔ ۸٫۳",
                },
            ),
            (
                {"en": "30% overrun breaks the waterfall", "fa": "۳۰٪ فزونی تلاش آبشاری را می‌شکند"},
                {
                    "en": "week 10.8, nothing at the deadline; timebox: 10 of 12",
                    "fa": "هفتهٔ ۱۰٫۸ و هیچ تحویلی تا مهلت؛ timebox: ‏۱۰ از ۱۲",
                },
            ),
            (
                {"en": "The timebox is not free", "fa": "timebox رایگان نیست"},
                {
                    "en": "at 8% overrun: waterfall 12/12, timebox 11/12",
                    "fa": "با ۸٪ فزونی تلاش: آبشاری ۱۲/۱۲ و timebox ‏۱۱/۱۲",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "quoting value percentages as results", "fa": "درصد ارزش را مثل نتیجهٔ واقعی نقل کردن"},
                {"en": "the values are invented: say 'in this model'", "fa": "ارزش‌ها ساختگی‌اند؛ بگویید «در این مدل»"},
            ),
            (
                {"en": "timebox delivers below capacity", "fa": "timebox کمتر از ظرفیت تحویل می‌دهد"},
                {"en": "whole items must fit: first-fit rule", "fa": "هر مورد باید کامل جا شود (قاعدهٔ first-fit)"},
            ),
            (
                {"en": "ValueError reading backlog.csv", "fa": "ValueError هنگام خواندن backlog.csv"},
                {"en": "quote titles that contain commas", "fa": "عنوان‌های دارای ویرگول را داخل گیومه بگذارید"},
            ),
        ],
        ext={
            "en": "Add a mid-flight change: an urgent 10-day item arrives in week 4. Compare how each plan absorbs it and say which of your assumptions decides the result.",
            "fa": "یک تغییر در میانهٔ کار اضافه کنید: یک مورد فوری ۱۰ روزه در هفتهٔ ۴ می‌رسد. مقایسه کنید هر طرح آن را چگونه جذب می‌کند و بگویید کدام فرض شما نتیجه را تعیین می‌کند.",
        },
        captured=CAP,
    ),
    dict(
        slug="07-contributing-guide",
        num="01.7",
        title={
            "en": "CONTRIBUTING.md and a commit-message checker, after Linux",
            "fa": "CONTRIBUTING.md و بررسی‌کنندهٔ پیام commit، به سبک Linux",
        },
        goal={
            "en": "Write a CONTRIBUTING guide and a review checklist adapted from Linux submitting-patches.rst, and enforce its mechanical rules with a Python checker and a Git hook.",
            "fa": "یک راهنمای CONTRIBUTING و چک‌لیست review بنویسید که از submitting-patches.rst در Linux اقتباس شده، و قاعده‌های مکانیکی آن را با یک checker پایتونی و یک hook در Git اجرا کنید.",
        },
        where={"en": "Git, Python, Bash", "fa": "Git، Python و Bash"},
        setup_cards=[
            (
                "r-store",
                {"en": "Source", "fa": "منبع"},
                {"en": "linux/Documentation/process/submitting-patches.rst · v6.18.63", "fa": "linux/Documentation/process/submitting-patches.rst · v6.18.63"},
            ),
            (
                "r-service",
                {"en": "Checker", "fa": "checker"},
                {"en": "check_commit_msgs.py: S1-S4, B1-B2, T1-T2", "fa": "check_commit_msgs.py: ‏S1-S4، B1-B2، T1-T2"},
            ),
            (
                "r-infra",
                {"en": "Hook", "fa": "hook"},
                {"en": "commit-msg rejects bad messages", "fa": "commit-msg پیام‌های بد را رد می‌کند"},
            ),
            (
                "r-client",
                {"en": "Guide", "fa": "راهنما"},
                {"en": "CONTRIBUTING.md + PR template (your task)", "fa": "CONTRIBUTING.md + قالب PR (تکلیف شما)"},
            ),
        ],
        steps=[
            '$ bash seed_commits.sh "$SCRATCH" && cd "$SCRATCH"',
            '$ mkdir -p tools .github && cp "$LAB/check_commit_msgs.py" tools/',
            "$ python tools/check_commit_msgs.py m0..HEAD",
            "# write CONTRIBUTING.md and .github/PULL_REQUEST_TEMPLATE.md",
            '$ cp "$LAB/solution/commit-msg" .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg',
            '$ git commit -m "wip stuff"',
            '$ git commit -s -m "catalog: add a note about ordering"',
        ],
        expected=[
            "$ python tools/check_commit_msgs.py m0..HEAD",
            "ok   4dd6d8a catalog: add Count",
            "FAIL 7aa6165 Fixed stuff.",
            "!       [S3] subject ends with a period",
            "       [T1] no Signed-off-by: line (git commit -s adds it)",
            "FAIL 9acf462 docs: explain the API",
            "!       [B1] no blank line between the subject and the body",
            "4 of 6 commits violate the rules",
            '$ git commit -m "wip stuff"',
            '!commit message rejected: [S4] subject does not start with "area: " (example: "catalog: add Count")',
            "commit message rejected: [T1] no Signed-off-by: line (git commit -s adds it)",
        ],
        observe=[
            (
                {"en": "Four of six commits fail", "fa": "چهار commit از شش‌تا رد می‌شود"},
                {
                    "en": "style (S3, S4), provenance (T1, T2), tool behaviour (B1)",
                    "fa": "سبک (S3، S4)، ردگیری مسئولیت (T1، T2)، رفتار ابزار (B1)",
                },
            ),
            (
                {"en": "A script checks form, not meaning", "fa": "اسکریپت شکل را می‌سنجد نه معنا را"},
                {
                    "en": "'add Count' and 'add stuff' both pass; review judges why",
                    "fa": "«add Count» و «add stuff» هر دو قبول می‌شوند؛ دلیل را review ارزیابی می‌کند",
                },
            ),
            (
                {"en": "A hook fails at the cheapest moment", "fa": "hook در ارزان‌ترین لحظه خطا می‌دهد"},
                {"en": "seconds now vs a review round-trip later", "fa": "چند ثانیه همین حالا در برابر یک دور رفت‌وبرگشت review بعدتر"},
            ),
            (
                {"en": "Every number is a choice", "fa": "هر عدد یک انتخاب است"},
                {
                    "en": "Linux says 70-75 characters; the checker says 72",
                    "fa": "Linux می‌گوید ۷۰ تا ۷۵ کاراکتر؛ checker عدد ۷۲ را برگزیده",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "hook does nothing", "fa": "hook هیچ کاری نمی‌کند"},
                {"en": "chmod +x; name must be commit-msg; use Git Bash", "fa": "chmod +x؛ نام باید commit-msg باشد؛ از Git Bash استفاده کنید"},
            ),
            (
                {"en": "python: command not found in the hook", "fa": "خطای python: command not found در hook"},
                {"en": "edit the last line to python3", "fa": "خط آخر را به python3 تغییر دهید"},
            ),
            (
                {"en": "T2 fires on a correct-looking sign-off", "fa": "T2 با وجود sign-off درست‌نما خطا می‌دهد"},
                {"en": "name or email differs from git config", "fa": "نام یا ایمیل با git config فرق دارد"},
            ),
            (
                {"en": "copying kernel sentences", "fa": "کپی کردن جمله‌های کرنل"},
                {"en": "quote a few lines with source; adapt the rest", "fa": "چند خط را با ذکر منبع نقل کنید و بقیه را بازنویسی کنید"},
            ),
        ],
        ext={
            "en": "Add rule T3: a Fixes: trailer must name an existing commit by its first 12 characters and quote its real subject. Add unit tests, then run the checker in CI on pull requests.",
            "fa": "قاعدهٔ T3 را اضافه کنید: trailer به نام Fixes: باید با ۱۲ نویسهٔ اول یک commit موجود را نام ببرد و subject واقعی آن را بیاورد. تست واحد بنویسید و سپس checker را در CI روی pull requestها اجرا کنید.",
        },
        captured=CAP,
    ),
]
