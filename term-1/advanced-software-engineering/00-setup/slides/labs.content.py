# Lab-deck content for 00-setup. Render: python _shared/tools/labdeck.py <this file>
# Roles (Advanced Software Engineering): r-client = teal, r-service = amber, r-infra = violet, r-store = green.
COURSE = {"en": "Advanced SE · 00 Setup", "fa": "مهندسی نرم‌افزار پیشرفته · ۰۰ راه‌اندازی"}

LABS = [
    dict(
        slug="01-toolchain-check",
        num="00.1",
        title={"en": "Toolchain check", "fa": "بررسی ابزارها"},
        goal={
            "en": "One script prints the version of every tool the course needs and flags what is missing or too old.",
            "fa": "یک اسکریپت نسخهٔ همهٔ ابزارهای لازم را چاپ می‌کند و کمبود یا قدیمی بودن را نشان می‌دهد.",
        },
        where={"en": "Your machine (any OS)", "fa": "ماشین خودتان (هر سیستم‌عاملی)"},
        setup_cards=[
            (
                "r-service",
                {"en": "Required", "fa": "لازم"},
                {
                    "en": "Go ≥ 1.22 · Python ≥ 3.8 · ruff · git ≥ 2.28",
                    "fa": "Go ≥ 1.22 · Python ≥ 3.8 · ruff · git ≥ 2.28",
                },
            ),
            (
                "r-infra",
                {"en": "Optional", "fa": "اختیاری"},
                {"en": "make · Docker · Node · Java", "fa": "make · Docker · Node · Java"},
            ),
            (
                "r-client",
                {"en": "The script", "fa": "اسکریپت"},
                {"en": "check_tools.py, standard library only", "fa": "check_tools.py، فقط کتابخانهٔ استاندارد"},
            ),
            (
                "r-store",
                {"en": "The result", "fa": "نتیجه"},
                {"en": "exit code = number of problems", "fa": "کد خروج = تعداد مشکل‌ها"},
            ),
        ],
        steps=[
            "# from the course repository root",
            "$ cd term-1/advanced-software-engineering/\\",
            "    00-setup/labs/01-toolchain-check",
            "$ python check_tools.py",
            "$ echo $?",
            "$ ruff check check_tools.py",
        ],
        expected=[
            "$ python check_tools.py",
            "tool     need      found    kind      status ...",
            "go       >= 1.22   1.27.4   required  OK",
            "python   >= 3.8    3.12.14  required  OK",
            "ruff     any       0.17.6   required  OK",
            "git      >= 2.28   2.56.1   required  OK",
            "docker   any       29.9.3   optional  OK",
            "...",
            "!all required tools present",
        ],
        captured={
            "en": "Windows 11 + Git Bash, 2026-11-23 (note column and some rows cut)",
            "fa": "Windows 11 و Git Bash، ۲۰۲۶-۱۱-۲۳ (ستون توضیح و چند ردیف حذف شده)",
        },
        observe=[
            (
                {
                    "en": "Python is the interpreter running the script",
                    "fa": "Python همان مفسری است که اسکریپت را اجرا می‌کند",
                },
                {
                    "en": "sys.executable, not always the python on PATH",
                    "fa": "sys.executable، که همیشه python موجود در PATH نیست",
                },
            ),
            (
                {"en": "ruff has no minimum, but versions differ", "fa": "ruff حداقل ندارد، ولی نسخه‌ها فرق دارند"},
                {
                    "en": "lab 02 shows what a bare ruff enforces",
                    "fa": "آزمایش ۰۲ نشان می‌دهد ruff بدون تنظیمات چه چیزی را می‌پذیرد",
                },
            ),
            (
                {"en": "Installed is not the same as running", "fa": "نصب بودن با اجرا بودن یکی نیست"},
                {
                    "en": "Docker: 'daemon NOT reachable' is its own status",
                    "fa": "Docker: «daemon NOT reachable» وضعیت جداگانه‌ای است",
                },
            ),
        ],
        pitfalls=[
            (
                {"en": "python: command not found", "fa": "python: command not found"},
                {"en": "run python3 check_tools.py", "fa": "python3 check_tools.py را اجرا کنید"},
            ),
            (
                {"en": "MISSING right after install", "fa": "MISSING درست بعد از نصب"},
                {"en": "open a new terminal", "fa": "ترمینال جدید باز کنید"},
            ),
            (
                {"en": "OLD for Go", "fa": "OLD برای Go"},
                {"en": "install from go.dev/dl", "fa": "از go.dev/dl نصب کنید"},
            ),
        ],
        ext={
            "en": "Write a second script that prints the same report as one JSON document, keeps the exit-code rule, and imports the checks instead of copying them.",
            "fa": "اسکریپت دومی بنویسید که همان گزارش را به‌صورت یک سند JSON چاپ کند، قاعدهٔ کد خروج را نگه دارد و به‌جای کپی کردن، بررسی‌ها را import کند.",
        },
    ),
    dict(
        slug="02-project-skeleton",
        num="00.2",
        title={"en": "The project skeleton and CI", "fa": "اسکلت پروژه و CI"},
        goal={
            "en": "Copy project/ into your own repository, get make check green, run the API, tag m0, and add CI.",
            "fa": "پوشهٔ project/ را در مخزن خودتان کپی کنید، make check را سبز کنید، API را اجرا کنید، m0 را tag بزنید و CI اضافه کنید.",
        },
        where={"en": "Your machine, outside the course repo", "fa": "ماشین خودتان، بیرون از مخزن درس"},
        setup_cards=[
            (
                "r-service",
                {"en": "Go service", "fa": "سرویس Go"},
                {"en": "cmd/registration-api · internal/catalog", "fa": "cmd/registration-api · internal/catalog"},
            ),
            (
                "r-service",
                {"en": "Python analytics", "fa": "تحلیل با Python"},
                {"en": "analytics/enrollment_stats.py", "fa": "analytics/enrollment_stats.py"},
            ),
            (
                "r-infra",
                {"en": "Build and ship", "fa": "ساخت و تحویل"},
                {"en": "Makefile · Dockerfile · CI workflow", "fa": "Makefile · Dockerfile · CI workflow"},
            ),
            (
                "r-store",
                {"en": "Your history", "fa": "تاریخچهٔ شما"},
                {"en": "git init, commit, tag m0", "fa": "git init، commit و tag با نام m0"},
            ),
        ],
        steps=[
            "$ cp -r $SRC/project ~/ase-work/registration",
            "$ cd ~/ase-work/registration",
            "$ printf '__pycache__/\\nbin/\\n' > .gitignore",
            "$ cp $SRC/00-setup/labs/02-project-skeleton/ruff.toml .",
            "$ make check",
            "$ git init -b main && git add . && git commit -m m0",
            "$ git tag m0",
            "$ make run",
            "$ curl -s localhost:8080/courses",
            "$ cp .../project-ci.yml .github/workflows/",
        ],
        expected=[
            "$ make check",
            "go vet ./...",
            "ruff check analytics",
            "!All checks passed!",
            "go test ./...",
            "ok  \texample.com/registration/cmd/registration-api\t0.521s",
            "ok  \texample.com/registration/internal/catalog\t0.298s",
            "...",
            "Ran 4 tests in 0.000s",
            "!OK",
            "$ curl -s localhost:8080/healthz",
            '{"status":"ok"}',
        ],
        captured={
            "en": "Windows 11 + Git Bash, Go 1.27.4, ruff 0.17.6, 2026-11-23",
            "fa": "Windows 11 و Git Bash، Go 1.27.4، ruff 0.17.6، ۲۰۲۶-۱۱-۲۳",
        },
        observe=[
            (
                {"en": "GET /nope is 404, POST /courses is 405", "fa": "GET /nope کد 404 می‌دهد و POST /courses کد 405"},
                {
                    "en": "Go 1.22 ServeMux patterns know methods",
                    "fa": "الگوهای ServeMux در Go 1.22 متد را می‌شناسند",
                },
            ),
            (
                {"en": "go test says (cached) the second time", "fa": "go test بار دوم (cached) می‌گوید"},
                {"en": "tests rerun only when inputs change", "fa": "تست فقط وقتی ورودی عوض شود دوباره اجرا می‌شود"},
            ),
            (
                {"en": "CI calls make lint and make test", "fa": "CI فقط make lint و make test را صدا می‌زند"},
                {"en": "the Makefile is the one place to look", "fa": "Makefile تنها جایی است که باید نگاه کرد"},
            ),
        ],
        pitfalls=[
            (
                {"en": "make lint: UP035, RUF100 (9 errors)", "fa": "خطاهای UP035 و RUF100 (۹ مورد) در make lint"},
                {"en": "copy ruff.toml into the project", "fa": "ruff.toml را داخل پروژه کپی کنید"},
            ),
            (
                {"en": "address already in use", "fa": "address already in use"},
                {"en": "ADDR=:8081 make run", "fa": "ADDR=:8081 make run"},
            ),
            (
                {"en": "Author identity unknown", "fa": "Author identity unknown"},
                {"en": "git config user.name / user.email", "fa": "git config user.name / user.email"},
            ),
        ],
        ext={
            "en": "Add a make fmt-check gate (gofmt and ruff format) and call it from CI. Run make fmt first, then prove the gate fails when a file is badly formatted.",
            "fa": "دروازهٔ make fmt-check (با gofmt و ruff format) اضافه کنید و از CI صدایش بزنید. اول make fmt را بزنید و بعد ثابت کنید با فایلی که بد قالب‌بندی شده دروازه شکست می‌خورد.",
        },
    ),
    dict(
        slug="03-diagram-tooling",
        num="00.3",
        title={"en": "Diagram tooling and C4", "fa": "ابزارهای نمودار و C4"},
        goal={
            "en": "Render Mermaid, PlantUML and a Structurizr C4 model, and commit them under docs/diagrams/.",
            "fa": "Mermaid و PlantUML و یک مدل C4 با Structurizr را رندر کنید و زیر docs/diagrams/ commit کنید.",
        },
        where={"en": "Your m0 repository (Docker, Node, a browser)", "fa": "مخزن m0 شما (Docker، Node و یک مرورگر)"},
        setup_cards=[
            (
                "r-client",
                {"en": "Mermaid", "fa": "Mermaid"},
                {"en": "browser page, or npx mermaid-cli 12.2.0", "fa": "صفحهٔ مرورگر، یا npx mermaid-cli 12.2.0"},
            ),
            (
                "r-infra",
                {"en": "PlantUML", "fa": "PlantUML"},
                {"en": "Docker image plantuml/plantuml", "fa": "ایمیج Docker با نام plantuml/plantuml"},
            ),
            (
                "r-infra",
                {"en": "Structurizr", "fa": "Structurizr"},
                {"en": "Docker image: validate and export", "fa": "ایمیج Docker: validate و export"},
            ),
            (
                "r-store",
                {"en": "The convention", "fa": "قرارداد"},
                {"en": "docs/diagrams: source + SVG, committed", "fa": "docs/diagrams: منبع و SVG، commit شده"},
            ),
        ],
        steps=[
            "$ mkdir -p docs/diagrams",
            "$ cp $SRC/00-setup/labs/03-diagram-tooling/\\",
            "    {registration-overview.mmd,list-courses.puml,\\",
            "     workspace.dsl,render-diagrams.sh} docs/diagrams/",
            "$ bash docs/diagrams/render-diagrams.sh",
            "$ ls -1 docs/diagrams",
            "$ git add . && git commit -m 'Add docs/diagrams'",
        ],
        expected=[
            "$ bash docs/diagrams/render-diagrams.sh",
            "!rendered registration-overview.svg",
            "!rendered list-courses.svg",
            "!rendered c4-containers.svg",
            "!rendered c4-context.svg",
            "$ ls -1 docs/diagrams",
            "c4",
            "c4-containers.svg",
            "c4-context.svg",
            "list-courses.puml",
            "...",
        ],
        captured={
            "en": "Windows 11 + Git Bash, mermaid-cli 12.2.0, PlantUML 1.2026.10, 2026-11-23 (listing cut)",
            "fa": "Windows 11 و Git Bash، mermaid-cli 12.2.0، PlantUML 1.2026.10، ۲۰۲۶-۱۱-۲۳ (فهرست کوتاه شده)",
        },
        observe=[
            (
                {"en": "One system, three pictures", "fa": "یک سیستم، سه تصویر"},
                {
                    "en": "flowchart: who talks · sequence: when · C4: who owns",
                    "fa": "flowchart: چه کسی با چه کسی · sequence: چه زمانی · C4: مالکیت",
                },
            ),
            (
                {"en": "Structurizr keeps one model", "fa": "Structurizr یک مدل نگه می‌دارد"},
                {"en": "views derive from workspace.dsl", "fa": "viewها از workspace.dsl ساخته می‌شوند"},
            ),
            (
                {"en": "Planned parts are labelled Planned", "fa": "بخش‌های طرح‌شده برچسب Planned دارند"},
                {"en": "a diagram must not hide what is not built", "fa": "نمودار نباید آنچه ساخته نشده را پنهان کند"},
            ),
        ],
        pitfalls=[
            (
                {"en": "Tried to find the browser at ...", "fa": "Tried to find the browser at ..."},
                {"en": "BROWSER=<path to chrome or msedge>", "fa": "BROWSER=<path to chrome or msedge>"},
            ),
            (
                {"en": "docker cannot reach the daemon", "fa": "docker به daemon وصل نمی‌شود"},
                {"en": "start Docker Desktop", "fa": "Docker Desktop را روشن کنید"},
            ),
            (
                {"en": "SVG differs between machines", "fa": "SVG روی ماشین‌ها فرق می‌کند"},
                {"en": "pin tool versions, never latest", "fa": "نسخهٔ ابزارها را ثابت کنید، نه latest"},
            ),
        ],
        ext={
            "en": "Write docs/diagrams/catalog-classes.mmd: a Mermaid class diagram of catalog.Course and catalog.Catalog, render it, and check every field and method against catalog.go.",
            "fa": "فایل docs/diagrams/catalog-classes.mmd را بنویسید: نمودار کلاس Mermaid برای catalog.Course و catalog.Catalog. رندرش کنید و هر فیلد و متد را با catalog.go مقایسه کنید.",
        },
    ),
]
