# Module 01 labs — Software Processes & Lifecycle Models

Seven labs, ordered from easy to hard. Together they take the running project from `m0` (the skeleton of 00-setup) to `m1` (delivery tooling and a contributing guide).

| # | Lab | Tools | Time | Difficulty |
|---|---|---|---|---|
| 1 | [`01-dora-metrics`](01-dora-metrics/README.md): deployment frequency, lead time, change failure rate and time to restore from a Git history | Git, Python | 45 min | easy |
| 2 | [`02-ci-quality-gates`](02-ci-quality-gates/README.md): gofmt, vet, ruff, tests and a coverage threshold, locally and in GitHub Actions | Go, ruff, Python, Git | 60 min | easy-medium |
| 3 | [`03-cost-of-fault-simulation`](03-cost-of-fault-simulation/README.md): cost of a fault by phase, and the 0.85% vs 7.5% argument | Python | 45 min | easy |
| 4 | [`04-git-bisect-worktrees`](04-git-bisect-worktrees/README.md): find a seeded regression with `git bisect run`, compare releases with `git worktree` | Git, Go | 60 min | medium |
| 5 | [`05-kanban-flow-metrics`](05-kanban-flow-metrics/README.md): cycle time, throughput, WIP and Little's law | Python | 45 min | medium |
| 6 | [`06-timebox-vs-waterfall`](06-timebox-vs-waterfall/README.md): the same backlog as a waterfall plan and as 3-week timeboxes | Python | 45 min | medium |
| 7 | [`07-contributing-guide`](07-contributing-guide/README.md): `CONTRIBUTING.md`, a review checklist and a commit-message checker, modelled on Linux `submitting-patches.rst` | Git, Python | 75 min | medium-hard |

Total about 6 hours. Labs 1, 3, 5 and 6 need only Python; lab 2 needs Go and `ruff`; labs 4 and 7 need Git and Go.

## `m0` and `m1`

The course repository has **no Git tags**. Every lab that changes `project/` begins the same way: copy `project/` to a scratch directory outside the course repository, `git init`, commit, and call that state `m0`. [`prepare-m0.sh`](prepare-m0.sh) does it:

```bash
bash prepare-m0.sh "${TMPDIR:-/tmp}/ase-m0"       # copy project/ + ruff.toml, git init, commit, tag m0
```

`m1` is `m0` plus the result of every lab of this module. [`build-m1.sh`](build-m1.sh) builds it from the reference solutions and checks it (ruff on the tools, the five gates, the commit-message rules):

```bash
bash build-m1.sh "${TMPDIR:-/tmp}/ase-m1"
```

| m1 file (in the scratch repository) | From lab |
|---|---|
| `tools/dora.py` | 1 |
| `tools/gates.py`, `.github/workflows/quality-gates.yml` | 2 |
| `tools/fault_cost.py` | 3 |
| `tools/bisect-test.sh` | 4 |
| `tools/gen_issues.py`, `tools/flow_metrics.py` | 5 |
| `tools/plan_compare.py`, `tools/backlog.csv` | 6 |
| `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `tools/check_commit_msgs.py`, `tools/commit-msg` (the hook) | 7 |

Captured output of `build-m1.sh` on Windows 11, Git Bash, 2026-11-23 (the five gates pass, one commit follows the rules; IDs differ on your machine):

```text
== ruff check tools
All checks passed!
== quality gates
gofmt     PASS  all Go files formatted
vet       PASS  go vet ./... is clean
ruff      PASS  All checks passed!
tests     PASS  go test and unittest pass
coverage  PASS  total 72.4% of statements (minimum 70.0%)
0 of 5 gates failed
== commit messages since m0
ok   cac7804 ci: add module 01 tooling, gates and CONTRIBUTING.md
0 of 1 commits violate the rules
```

## Conventions of all labs

- Every lab README has: Goal, Starting state, Steps, Code, Expected output (a real run), What to observe, Pitfalls, Extension task (no solution) and a `solution/` folder.
- Scratch work goes in `${TMPDIR:-/tmp}/ase-labNN`, never inside the course repository. The `seed_*.sh` scripts refuse to write into a non-empty directory.
- Python is standard library only, Python >= 3.8, and passes `ruff check` with the repository's `ruff.toml`. Use `python3` if `python` is not Python 3 on your system.
- The scripts set `commit.gpgsign=false`, `tag.gpgsign=false` and `core.autocrlf=false` in the scratch repositories they create, so commit IDs do not depend on your global Git configuration.
- The data of labs 1, 3, 5 and 6 are **synthetic**: histories, issues, estimates and multipliers are generated or invented for the exercise and marked as such. None of them is a measurement of a real team.
- Sources: Schach, *Object-Oriented and Classical Software Engineering*, 8th ed., cited by chapter and section; Linux `Documentation/process/submitting-patches.rst` at v6.18.63 (lab 7). DORA, Little's law and the Scrum/Kanban literature were not opened for these labs; the labs say so where it matters.
