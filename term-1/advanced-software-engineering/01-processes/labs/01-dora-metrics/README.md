# Lab 01.1 — DORA metrics from a Git history

**Goal:** compute deployment frequency, lead time for changes, change failure rate and time to restore from the Git history of a repository with a short Python script, and learn what those numbers can and cannot tell you.

Runs on: any machine with Git and Python >= 3.8 (stdlib only). Time: 45 min. Difficulty: easy.

## Starting state

- Module state `m0`: no project files are needed for this lab. The lab builds its own scratch repository, so nothing in `project/` changes.
- The course repository has no Git tags. In the labs that do change `project/`, you copy it to a scratch directory, run `git init` and commit; that commit is called `m0`. The helper [`../prepare-m0.sh`](../prepare-m0.sh) does exactly that (used from lab 02 on).
- Ending state: `dora.py` exists and gives a report. It joins the `m1` toolbox as `tools/dora.py` (see [`../README.md`](../README.md)).

## Background in five lines

| Metric | Question it answers | What this lab measures (a proxy) |
|---|---|---|
| Deployment frequency | how often do we ship? | tags `v*` per week (a tag stands for "deployed") |
| Lead time for changes | how long from code written to code shipped? | commit date → date of the first tag containing it |
| Change failure rate | how many deployments hurt? | tags named in a `Fixes-release:` trailer, divided by all tags |
| Time to restore service | how long to recover? | failed tag → first tag that contains its fix |

The four metrics come from the DORA research programme (book: *Accelerate*, Forsgren, Humble and Kim, 2018). Neither source was opened for this lab, so treat the exact wording of the definitions as `UNVERIFIED`. DORA's later reports renamed and extended the set (for example "failed deployment recovery time"); that is `VERSION-DEPENDENT`, so check the current DORA report before you quote a definition. This lab does **not** use DORA's performance bands: they change from year to year and the thresholds were not verified.

Schach (8e, ch. 2 and ch. 3) knows nothing about continuous delivery; he measures process maturity (CMM) rather than delivery speed. See the note on DORA in module 01, note 08.

## Steps

```bash
cd term-1/advanced-software-engineering/01-processes/labs/01-dora-metrics
SCRATCH="${TMPDIR:-/tmp}/ase-lab01"                 # any empty place outside the course repo
bash seed_repo.sh "$SCRATCH/dora-demo"              # 32 scripted commits, 11 release tags
git -C "$SCRATCH/dora-demo" log --oneline --decorate -8
python dora.py --repo "$SCRATCH/dora-demo"          # the report (author dates)
python dora.py --repo "$SCRATCH/dora-demo" --date committer
python dora.py --repo "$SCRATCH/dora-demo" --json > dora.json
```

Then answer the four questions in "What to observe" with the script and `git log`, and compare with `solution/answers.md`.

Linux / macOS: use `python3` if `python` is not Python 3. Git must be >= 2.22 (the script uses the `%(trailers:...)` log format).

## Code

- [`seed_repo.sh`](seed_repo.sh): builds the repository. Dates are fixed with `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE`, so every run gives the same history and the same commit IDs. The history is **synthetic**: eight weeks of a small team, three releases that needed a repair, one commit whose author date differs from its commit date (a rebase), and two commits that are not released yet.
- [`dora.py`](dora.py): reads tags with `git for-each-ref`, commits between consecutive tags with `git log prev..tag`, and prints the report (or JSON).

## Expected output

Captured on Windows 11, Git for Windows, Git Bash, Python 3.12, 2026-11-23. Linux and macOS print the same report (the history is built from fixed dates); only the first line, with the repository folder name, depends on your path.

```text
$ bash seed_repo.sh "$SCRATCH/dora-demo"
seeded 32 commits and 11 release tags in /tmp/ase-lab01/dora-demo
fbf9770 (HEAD -> main) Add locale switcher
386743b Add holiday calendar
26070f9 (tag: v0.8.0) Tune database indexes
1737457 Add dashboard widgets
1f239b6 (tag: v0.7.0) Add grade export

$ python dora.py --repo "$SCRATCH/dora-demo"
DORA metrics for dora-demo
(deployment = tag matching the glob, commit time = author date)

Deployment frequency
  deployments            11  (2026-03-05 10:00 to 2026-04-24 15:00, 50.2 days)
  per week               1.53  (in 8 different weeks)
Lead time for changes  (30 released commits, commit -> first tag containing it)
  median                 46.5 h (1 d 22.5 h)
  mean                   55.6 h (2 d 7.6 h)
  90th percentile        119.0 h (4 d 23.0 h)
Change failure rate
  failed deployments     3 of 11  v0.2.0, v0.4.0, v0.6.0
  rate                   27%
Time to restore service
  v0.2.0                 22.5 h
  v0.4.0                 24.0 h (1 d 0.0 h)
  v0.6.0                 126.0 h (5 d 6.0 h)
  median                 24.0 h (1 d 0.0 h)
Not measured
  2 of 32 commits are not in any release yet (they have no lead time)

$ python dora.py --repo "$SCRATCH/dora-demo" --date committer | sed -n 7,9p
Lead time for changes  (30 released commits, commit -> first tag containing it)
  median                 45.5 h (1 d 21.5 h)
  mean                   54.9 h (2 d 6.9 h)
```

The full reports are in [`solution/expected-report.txt`](solution/expected-report.txt) and [`solution/expected-report-committer.txt`](solution/expected-report-committer.txt). Your commit IDs must match the ones above; if not, your Git config changes commits (signing, `core.autocrlf`): the script switches those off locally in the scratch repository, so check for a global `commit.template` or hooks.

## What to observe

1. **Which release took longest to repair, and why?** `v0.6.0` took 126 h, about five times longer than the other two: its fix was written only on the next Monday, after the weekend. Open `git log --format='%h %ad %s' --date=iso v0.6.0..v0.6.1`: the metric includes waiting time, not only coding time.
2. **Does the date you choose change the lead time?** Compare the two reports. One commit ("Add CSV export") was written on 03-17 and rebased on 03-18; with committer dates its lead time is 22 h shorter and the median falls by 1 h. A rebase or squash silently rewrites the clock you measure with.
3. **What would make change failure rate look perfect?** Remove the `Fixes-release:` trailers (or never write them) and the rate is 0%, although the same three repairs happened. The metric measures your *convention*, not reality.
4. **What is missing?** The last line of the report: 2 commits are not released, so they have no lead time. A team that stops releasing would see its median lead time *improve* while its real wait grows.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `no tags match 'v*'` | tags missing, or the repo was cloned without them | `git fetch --tags` |
| commit IDs differ from this README | global Git config changes commits (signing, line endings) | the scripts set `commit.gpgsign=false`, `core.autocrlf=false` locally; check hooks and templates |
| `git log` fails with `unrecognized %(trailers` | Git older than 2.22 | upgrade Git |
| all lead times are 0 or negative | clocks differ between machines, or tags created before the commits | compare `%ad`, `%cd` and the tag date with `git for-each-ref` |
| `python: command not found` | Linux / macOS name the interpreter `python3` | use `python3` |
| numbers shift by hours on your machine | someone changed the timezone handling | the script uses UTC only; do not edit it to use local time |

## Limits of these metrics (read before you quote them)

- A tag is not a deployment: it says nothing about when the code reached users, how many users, or whether it was rolled back.
- Git time is a poor clock: rebases, squash merges, amended commits and cherry-picks change dates. A squash merge makes a week of work look like a one-hour lead time.
- A single repository is not a service. A change can wait for another repository, a manual approval or a release train that Git does not show.
- Medians of 30 commits are noisy. Do not rank teams with them (`OPINION / CONTESTED`: DORA itself warns against using the metrics as targets; the exact wording is `UNVERIFIED` here).

## Extension task

Extend `dora.py` to (a) print the lead time per release so you can see which release had the worst waiting time, and (b) detect failed deployments from commit subjects that start with `Revert` instead of the trailer. Run both versions on the seeded repository and explain which of the three failures the revert rule finds and which it misses. No solution is provided for this task.

Solution of the lab: [`solution/`](solution/) (expected reports and `answers.md`).
