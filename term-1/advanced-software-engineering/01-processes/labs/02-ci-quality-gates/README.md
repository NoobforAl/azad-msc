# Lab 01.2 — CI quality gates: the same checks on your laptop and in CI

**Goal:** add quality gates (format, static analysis, lint, tests, coverage threshold) to the project as one script that runs locally and in GitHub Actions, and watch each gate fail on purpose.

Runs on: Go >= 1.22, Python >= 3.8, `ruff`, Git. Time: 60 min. Difficulty: easy to medium.

## Starting state

- Module state `m0`: the project skeleton from 00-setup (Go API, Python analytics, `Makefile`, CI template `project/ci/github-actions.yml`).
- The course repository has no tags, so build `m0` yourself: `bash ../prepare-m0.sh <scratch-dir>` copies `project/` into a scratch directory, adds the repo's `ruff.toml`, runs `git init`, commits and tags `m0`.
- Ending state: the scratch repository has `tools/gates.py` and `.github/workflows/quality-gates.yml`, committed. These two files are part of `m1` (see [`../README.md`](../README.md)).

## Background

A **quality gate** is an automatic check that must pass before a change is accepted. The point is not the tool but the rule: *the pipeline, not a person's memory, decides.* Gates differ in cost and in what they catch:

| Gate | Catches | Cost | Tool here |
|---|---|---|---|
| format | style noise in diffs | seconds | `gofmt -l` |
| static analysis | suspicious code that compiles | seconds | `go vet` |
| lint | unused imports, bug patterns | seconds | `ruff check` (rules `E,F,W,B` from `ruff.toml`) |
| tests | regressions the tests describe | seconds to minutes | `go test`, `unittest` |
| coverage threshold | new code that no test executes | one extra test run | `go test -coverprofile`, `go tool cover -func` |

Coverage says which statements ran, not that they were checked. A threshold is a floor, not a quality score (`OPINION / CONTESTED`; module 06 measures this with mutation testing). The default threshold of 70% is **a choice made for this lab**: `m0` has 72.4%, so any sizeable untested addition trips the gate.

`ruff format --check` is deliberately not a gate: the `m0` skeleton is not format-clean (one Python file would be reformatted), and a gate that is red from day one is ignored. Making it green first is the extension task.

The course template `project/ci/github-actions.yml` runs `make lint` and `make test`. Those cover `go vet`, `ruff` and the tests, but **not** `gofmt` and **not** coverage. This lab closes that gap.

## Steps

```bash
cd term-1/advanced-software-engineering/01-processes/labs/02-ci-quality-gates
LAB="$PWD"
python -m unittest test_gates -v                 # tests of the runner itself
SCRATCH="${TMPDIR:-/tmp}/ase-lab02"
bash ../prepare-m0.sh "$SCRATCH"                 # copy project/, git init, commit, tag m0
cd "$SCRATCH"
mkdir tools && cp "$LAB/gates.py" tools/
git add tools && git commit -qm "ci: add quality gates runner"
python tools/gates.py                            # all gates green on m0

# 1. break the format gate
printf '\nvar   unformatted=1\n' >> internal/catalog/catalog.go
python tools/gates.py --only gofmt,vet; echo "exit code $?"
git checkout internal/catalog/catalog.go

# 2. break the lint gate
python -c "p='analytics/enrollment_stats.py'; s=open(p).read(); open(p,'w').write('import os\n' + s)"
python tools/gates.py --only ruff
git checkout analytics

# 3. break the test gate
python -c "p='analytics/enrollment_stats.py'; s=open(p).read(); open(p,'w').write(s.replace('min(enrolled / capacity, 1.0)', 'enrolled / capacity'))"
python tools/gates.py --only tests
git checkout analytics

# 4. break the coverage gate: add code that no test runs
cat > internal/catalog/stats.go <<'EOF'
package catalog

// Summary is deliberately untested: it makes the coverage gate fail.
func (c *Catalog) Summary() (total, large int) {
	for _, course := range c.courses {
		total += course.Capacity
		if course.Capacity >= 30 {
			large++
		}
	}
	return total, large
}
EOF
python tools/gates.py --only coverage
rm internal/catalog/stats.go
```

**Your task:** write `.github/workflows/quality-gates.yml` that installs Go, Python and `ruff` and runs `python tools/gates.py`, then compare it with [`solution/quality-gates.yml`](solution/quality-gates.yml). Commit both files. Read `project/ci/github-actions.yml` first: it shows the action versions and the `paths:` filter that a monorepo needs. In your scratch repository `project/` *is* the repository root, so no `working-directory` is needed.

Linux / macOS: use `python3` if needed. Windows (Git Bash): `gofmt` prints paths with a backslash (`internal\catalog\catalog.go`), Linux and macOS print a slash.

## Code

- [`gates.py`](gates.py): runs five gates, each printing `PASS`, `FAIL` or `SKIP` (tool missing). All gates run even after a failure; the exit code is the number of failed gates, which is what CI needs.
- [`test_gates.py`](test_gates.py): unit tests of the parsing helpers (`parse_total_coverage`, `failure_lines`, `last_lines`).
- [`solution/quality-gates.yml`](solution/quality-gates.yml): the reference workflow.

## Expected output

Captured on Windows 11, Git Bash, Go (toolchain 1.27), Python 3.12, ruff 0.17, 2026-11-23, from a fresh `m0` scratch repository.

```text
$ python tools/gates.py
gofmt     PASS  all Go files formatted
vet       PASS  go vet ./... is clean
ruff      PASS  All checks passed!
tests     PASS  go test and unittest pass
coverage  PASS  total 72.4% of statements (minimum 70.0%)
0 of 5 gates failed

$ python tools/gates.py --only gofmt,vet; echo "exit code $?"
gofmt     FAIL  needs gofmt: internal\catalog\catalog.go
vet       PASS  go vet ./... is clean
1 of 2 gates failed
exit code 1

$ python tools/gates.py --only ruff
ruff      FAIL  analytics\enrollment_stats.py:1:8: F401 [*] `os` imported but unused | analytics\enrollment_stats.py:3:1: E402 Module level import not at top of file
1 of 1 gates failed

$ python tools/gates.py --only tests
tests     FAIL  unittest: FAIL: test_overbooked_is_capped (test_enrollment_stats.FillRateTest.test_overbooked_is_capped)
1 of 1 gates failed

$ python tools/gates.py --only coverage
coverage  FAIL  total 61.8% of statements (minimum 70.0%)
1 of 1 gates failed
$ python tools/gates.py --only coverage --min-coverage 60
coverage  PASS  total 61.8% of statements (minimum 60.0%)
0 of 1 gates failed
```

Not captured: the GitHub Actions run itself. The workflow file was only parsed as YAML here (keys `on`, `jobs.gates.steps`); it has not been executed on a GitHub runner (`UNVERIFIED` until you push it). Action versions are copied from the course template.

## What to observe

1. **The break is caught by exactly one gate.** Each of the four changes makes one gate fail and leaves the others green. `go vet` passes on badly formatted code, `gofmt` passes on code with no tests, and so on: gates are complementary, not redundant.
2. **The coverage gate caught a change the tests never noticed.** The new untested function pulls the total from 72.4% to 61.8% while every test still passes. Lowering the threshold to 60 turns the same code green: the threshold is a policy decision someone must own and write down.
3. **Local = CI.** The workflow's only real step is `python tools/gates.py`. When CI is red you reproduce it with one command, without pushing.
4. **The template had a gap.** Run `make lint test` in the scratch repo after break 1: it passes, because `make lint` does not run `gofmt`. A pipeline only enforces what it runs.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `ruff` gate says `SKIP ruff: command not found` | `ruff` not on `PATH` | `pip install ruff` (CI does this in its own step) |
| `ruff` finds errors in a scratch copy that the course repo accepts | the scratch copy has no `ruff.toml`, so ruff uses its defaults | `prepare-m0.sh` copies it; copy it yourself if you made the scratch directory by hand |
| coverage gate says `cannot read coverage` | `go tool cover` printed no `total:` line, usually because `go test` failed first | run `go test ./...` and read its first error |
| the gates pass locally and fail in CI | different Go or Python version, or a file that is git-ignored locally | compare `go version` with the workflow, run `git status --ignored` |
| `git checkout analytics` prints nothing but the file is unchanged | the break was already reverted | `git status` shows what is dirty |
| the workflow does not start | file is not under `.github/workflows/`, or YAML indentation is wrong | `python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <file>` (needs PyYAML) |

## Extension task

Add a sixth gate `pyformat` that runs `ruff format --check analytics`. It fails on `m0`, so first fix the formatting in a separate commit (`make fmt`), then enable the gate. Then add a **per-package** coverage floor (for example `internal/catalog` >= 90%) next to the total, parsing `go test -cover ./...` instead of the profile. No solution is provided.

Solution of the lab: [`solution/`](solution/) (the workflow).
