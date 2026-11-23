# Lab 00.2 — The project skeleton: build, test, lint, tag `m0`, CI

**Goal:** copy the course project into your own Git repository, make `make check` pass (go vet, ruff, go test, unittest), run the API, and add a CI workflow that runs the same commands.

**Starting state:** the content of `project/` in the course repository. The course repository has no Git tags, so **your own copy is where `m0` is created**: you copy, `git init`, commit, and tag. Every later lab says "start from `m0` / `m1` / …" and means the state of your history (or, if you skipped a lab, the content of `project/` at that point).
**Ending state (your `m0`):** a repository with the skeleton, a `ruff.toml`, a `.gitignore`, a commit tagged `m0`, and a CI workflow in a second commit.

## Steps

Git Bash on Windows, or any shell on Linux and macOS. Run step 1 from the course repository root.

```bash
# 1. copy project/ out of the course repository (your history must not live inside it)
export SRC="$PWD/term-1/advanced-software-engineering"
export WORK="$HOME/ase-work"                      # any folder outside the course repository
mkdir -p "$WORK" && cp -r "$SRC/project" "$WORK/registration"
cd "$WORK/registration"

# 2. ignore build output, and give the project its own lint settings (see "Common pitfalls")
printf '__pycache__/\nbin/\n' > .gitignore
cp "$SRC/00-setup/labs/02-project-skeleton/ruff.toml" .

# 3. build, test and lint in one go
make check

# 4. your own history: this commit is state m0
git init -b main
git config user.name "Your Name" && git config user.email "you@example.com"   # only if git has no identity yet
git add . && git commit -m "m0: course registration skeleton"
git tag m0
git log --oneline --decorate

# 5. run the API (second terminal: curl). Ctrl+C stops it.
make run                                          # same as: go run ./cmd/registration-api
```

In a second terminal:

```bash
curl -s localhost:8080/healthz
curl -s localhost:8080/courses | python -m json.tool
curl -s -o /dev/null -w "%{http_code}\n" localhost:8080/nope                 # unknown path
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8080/courses      # wrong method
```

Port 8080 busy? `ADDR=:8081 make run` (the service reads `ADDR`) and use 8081 in the `curl` lines.

Now the CI workflow:

```bash
# 6. CI that runs the same commands as make check, and a check that GitHub will accept the file
mkdir -p .github/workflows
cp "$SRC/00-setup/labs/02-project-skeleton/project-ci.yml" .github/workflows/project-ci.yml
git add .github && git commit -m "Add CI workflow (same commands as make check)"
docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:latest -color        # prints nothing when the workflow is valid
```

- Git Bash on Windows: put `MSYS_NO_PATHCONV=1` in front of `docker run` and use `-v "$(pwd -W):/repo"`.
- No Docker? Skip the `actionlint` line; pushing to GitHub is the real test.

Optional, with a GitHub repository of your own: `git remote add origin <url> && git push -u origin main --tags`, then open the **Actions** tab.

Docker, optional (the compose file runs only the API in `m0`):

```bash
docker compose up --build        # API on :8080; Ctrl+C, then: docker compose down
```

## Code

The project you copied (read it once, it is small):

| Path | What it is |
|---|---|
| `cmd/registration-api/main.go` | HTTP entry point. `newMux` registers `GET /healthz` and `GET /courses`; `main` reads `ADDR` and starts the server |
| `internal/catalog/catalog.go` | in-memory course catalog (`New`, `List`, `Get`); replaced by PostgreSQL in module 04 |
| `analytics/enrollment_stats.py` | Python stub: `fill_rate` and `fullest_courses` |
| `Makefile` | `lint` = `go vet` + `ruff check`; `test` = `go test` + `unittest`; `check` = both |
| `ci/github-actions.yml` | the template for the CI file (see [`project-ci.yml`](project-ci.yml) for the version that fits your own repository) |
| [`ruff.toml`](ruff.toml) | added by this lab: the lint rules, kept inside the project |

[`project-ci.yml`](project-ci.yml) differs from the template in one way: the template filters by `paths:` and sets `working-directory:` because inside the course repository the project is a sub-folder. In your repository the project is the root, so both are removed.

## Expected output

Captured on Windows 11 with Git Bash on 2026-11-23 (Go 1.27.4, Python 3.12.14, ruff 0.17.6). `make check` exits 0:

```text
$ make check
go vet ./...
ruff check analytics
All checks passed!
go test ./...
ok  	example.com/registration/cmd/registration-api	0.521s
ok  	example.com/registration/internal/catalog	0.298s
python -m unittest discover -s analytics/tests -v
test_half_full (test_enrollment_stats.FillRateTest.test_half_full) ... ok
test_overbooked_is_capped (test_enrollment_stats.FillRateTest.test_overbooked_is_capped) ... ok
test_zero_capacity_is_zero (test_enrollment_stats.FillRateTest.test_zero_capacity_is_zero) ... ok
test_ranks_by_fill_rate_then_id (test_enrollment_stats.FullestCoursesTest.test_ranks_by_fill_rate_then_id) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```

```text
$ git log --oneline --decorate
a71bc41 (HEAD -> main) Add CI workflow (same commands as make check)
1dd2562 (tag: m0) m0: course registration skeleton

$ curl -s localhost:8080/healthz
{"status":"ok"}
$ curl -s localhost:8080/courses | python -m json.tool
[
    {
        "id": "SE101",
        "title": "Software Processes",
        "capacity": 40
    },
    {
        "id": "SE102",
        "title": "Requirements Engineering",
        "capacity": 35
    }
]
404
405
```

Your commit hashes and test times will differ. Full reference output: [`solution/expected-output.txt`](solution/expected-output.txt).

What was and was not run: the API was run from the binary built by `make build`, and the project's `Dockerfile` was built with `docker build` and queried on another port. `make run` (same code through `go run`) and `docker compose up` itself were not run (**UNVERIFIED** as commands; both only wrap what was run). `actionlint` accepted the workflow. The workflow has **not** been run on GitHub (**UNVERIFIED** that it goes green there).

## What to observe

- `GET /nope` is 404 but `POST /courses` is 405: the Go 1.22 `ServeMux` patterns (`"GET /courses"`) know about methods. That is an architectural fact worth noticing: the routing table is the first place where requirements show up in code.
- `go test` is fast and `(cached)` the second time. Go only reruns tests when the code or inputs changed.
- The CI file contains no logic of its own: it calls `make lint` and `make test`. If CI and your laptop disagree, the Makefile is the single place to look (module 01 builds quality gates on this idea).
- `git tag m0` is a pointer, not a copy: `git show m0 --stat` lists what the first commit contained.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `make lint` fails with `UP035`, `UP006`, `RUF100` (9 errors) | you skipped `ruff.toml`. Outside the course repository there is no config, and on ruff 0.17.6 the defaults enforce more rules than the course's | `cp .../ruff.toml .` as in step 2 |
| `make: command not found` (Windows) | `make` is not installed | `scoop install make`, or run the commands in the `Makefile` by hand |
| `warning: LF will be replaced by CRLF` | Git for Windows `core.autocrlf` | harmless; ignore it |
| `bind: address already in use` | something else listens on 8080 | `ADDR=:8081 make run` |
| `go: ... requires go >= 1.22` | Go is too old | lab 01 tells you; install a current Go |
| `Author identity unknown` | git has no name/email | the `git config` line in step 4 |

The real error for the first row, trimmed (captured without `ruff.toml`):

```text
$ make lint
go vet ./...
ruff check analytics
UP035 [*] Import from `collections.abc` instead: `Iterable`
 --> analytics\enrollment_stats.py:2:1
...
Found 9 errors.
make: *** [Makefile:10: lint] Error 1
```

## Extension task

Add a **formatting gate**: a `make fmt-check` target that fails when any Go file is not `gofmt`-clean or any Python file is not `ruff format`-clean, and call it from the CI workflow. First run `make fmt` and commit the result: it will change the project (a blank line in `analytics/enrollment_stats.py`), and the gate must start green. Prove the gate works by breaking the format of one file on purpose.

Solution: [`solution/fmt-check.mk`](solution/fmt-check.mk) (append it to your Makefile) and [`solution/project-ci.yml`](solution/project-ci.yml).
