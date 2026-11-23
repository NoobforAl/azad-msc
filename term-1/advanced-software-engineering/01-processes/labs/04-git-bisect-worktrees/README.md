# Lab 01.4 — `git bisect` and `git worktree` on a seeded regression

**Goal:** find the commit that broke the project with `git bisect run` and a test, then test two releases side by side with `git worktree`.

Runs on: Git, Go >= 1.22, Bash. Time: 60 min. Difficulty: medium.

## Starting state

- Module state `m0`, built in a scratch directory. The course repository has no tags, so `seed_regression.sh` calls [`../prepare-m0.sh`](../prepare-m0.sh) (copy `project/`, `git init`, commit, tag `m0`) and then adds **11 scripted commits** and two tags: `v1.0` (after commit 5) and `v1.1` (the last commit).
- One of the 11 commits breaks `Catalog.List()` ordering (an innocent-looking "presentation tweak"), one commit does not compile (a "work in progress" commit), and the others are harmless.
- Ending state: the repository has the same history; you added no files to it. The oracle script `bisect-test.sh` and the two Git habits join `m1` (see [`../README.md`](../README.md)).

## Background

A regression is a fault that makes a behaviour that worked stop working. When it is noticed late, the question is *which change did it*. `git bisect` answers by binary search over the history: with N commits between a known good and a known bad one it needs about log2(N) tests. `git bisect run <command>` automates it, using the command's exit code: 0 good, 1 to 124 and 126 to 127 bad, **125 "cannot test this commit"** (skip), above 127 abort.

`git worktree` gives you more than one working directory for the same repository (`.git` is shared), so you can build and run two releases at once without cloning or stashing. Schach calls the repeated checking that old behaviour still works *regression testing* (8e, ch. 16, testing during postdelivery maintenance; the section number was not checked); bisect is what you do when regression testing fails and you need the culprit.

## Steps

```bash
cd term-1/advanced-software-engineering/01-processes/labs/04-git-bisect-worktrees
LAB="$PWD"
SCRATCH="${TMPDIR:-/tmp}/ase-lab04"
bash seed_regression.sh "$SCRATCH/repo"
cd "$SCRATCH/repo"
git log --oneline --decorate m0..HEAD
go test ./...                                   # two tests fail on HEAD; v1.0 was fine

# bisect: v1.0 is good, HEAD is bad; the oracle decides for every commit git checks out
git bisect start HEAD v1.0
git bisect run bash "$LAB/bisect-test.sh"
git bisect log | tail -8
git bisect reset                                # back to main

# worktrees: two releases side by side
git worktree add ../rel-v1.0 v1.0
git worktree add ../rel-v1.1 v1.1
git worktree list
(cd ../rel-v1.0 && go test ./internal/catalog -run TestListIsSortedByID -count=1) &
(cd ../rel-v1.1 && go test ./internal/catalog -run TestListIsSortedByID -count=1) &
wait
git worktree remove ../rel-v1.0
git worktree remove ../rel-v1.1
```

**Your task:** (1) name the culprit commit and say what it changed (`git show <hash>`); (2) explain why bisect skipped one commit and why that did not matter; (3) repair `main` with `git revert` on a branch and prove it with `go test ./...`. The script [`solution/run-all.sh`](solution/run-all.sh) does all of it; read it only after your own attempt.

Linux / macOS: the same commands work. Paths print as `/tmp/...`. If `go test` prints `[no test files]` you are in the wrong directory.

## Code

- [`seed_regression.sh`](seed_regression.sh): builds the history. Dates and authors are fixed, so the *subjects* and the order are the same on every machine. The commit IDs below depend on the content of `project/` at `m0`; if `project/` changes, your IDs differ but the story is identical.
- [`bisect-test.sh`](bisect-test.sh): the oracle. It first checks that the code builds (exit 125 if not), then runs one Go test, `TestListIsSortedByID`, from the project's own test suite. Exit code 0 or 1 comes straight from `go test`.

## Expected output

Captured on Windows 11, Git Bash, Git for Windows 2.56.1, Go toolchain 1.27, 2026-11-23 (the worktree paths are shortened to /tmp). Linux and macOS give the same sequence.

```text
$ git log --oneline --decorate m0..HEAD
67a61f9 (HEAD -> main, tag: v1.1) docs: mention Remove in README
f72fb33 catalog: add Remove
e18cd1c catalog: finish GetByTitle
35b06e0 catalog: WIP GetByTitle
792c10a docs: update CHANGELOG for 1.1
f10c4bb catalog: show newest course IDs first
32472f0 (tag: v1.0) catalog: add TotalCapacity
8408ced docs: document the API in README
a62ca60 catalog: add Titles
ae78c2b catalog: add Count
bfa6dc7 docs: add CHANGELOG

$ go test ./...
ok  	example.com/registration/cmd/registration-api	0.733s
--- FAIL: TestTitles (0.00s)
    catalog_extra_test.go:16: Titles() = [Second First], want [First Second]
--- FAIL: TestListIsSortedByID (0.00s)
    catalog_test.go:9: List() = [{ID:SE2 Title:Requirements Capacity:30} {ID:SE1 Title:Processes Capacity:25}], want SE1 then SE2
FAIL
FAIL	example.com/registration/internal/catalog	0.418s

$ git bisect start HEAD v1.0
Bisecting: 2 revisions left to test after this (roughly 2 steps)
[35b06e0730f14af5b5d9ad6cc4ee28ff972dc64c] catalog: WIP GetByTitle

$ git bisect run bash "$LAB/bisect-test.sh"
bisect-test: build fails, skipping this commit
Bisecting: 2 revisions left to test after this (roughly 2 steps)
[e18cd1c242c78e1d816522936d134dbbc3bcb332] catalog: finish GetByTitle
Bisecting: 1 revision left to test after this (roughly 1 step)
[792c10adba22b8fcb2448c7bfa0d1a2ad5588dd3] docs: update CHANGELOG for 1.1
Bisecting: 0 revisions left to test after this (roughly 0 steps)
[f10c4bbc648959059cec1c25bc709ed01e35b123] catalog: show newest course IDs first
f10c4bbc648959059cec1c25bc709ed01e35b123 is the first 'bad' commit
Author: Lab Student <student@example.com>
Date:   Mon May 11 10:00:00 2026 +0000

    catalog: show newest course IDs first

 internal/catalog/catalog.go | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
bisect found first 'bad' commit

$ git worktree list
/tmp/ase-lab04/repo     67a61f9 [main]
/tmp/ase-lab04/rel-v1.0 32472f0 (detached HEAD)
/tmp/ase-lab04/rel-v1.1 67a61f9 (detached HEAD)

$ (side by side)
[v1.0] ok  	example.com/registration/internal/catalog	0.261s
[v1.1] --- FAIL: TestListIsSortedByID (0.00s)
[v1.1]     catalog_test.go:9: List() = [{ID:SE2 Title:Requirements Capacity:30} {ID:SE1 Title:Processes Capacity:25}], want SE1 then SE2
[v1.1] FAIL
[v1.1] FAIL	example.com/registration/internal/catalog	0.375s
[v1.1] FAIL
```

(The `running 'bash' ...` lines that `git bisect run` prints between steps are omitted here.) The full transcript of the reference script, including the `git revert` fix, is in [`solution/expected-transcript.txt`](solution/expected-transcript.txt). The two outputs of `go test` timings (0.733s and so on) will differ on your machine.

## What to observe

1. **Four checkouts for six candidates.** `v1.0..HEAD` holds 6 commits; bisect checked out four of them (one skipped, three judged). With N candidates the cost is about log2(N), so a thousand commits need about ten steps; the saving grows with the history.
2. **Skip is a first-class answer.** The first commit bisect picked (`WIP GetByTitle`) does not build; the oracle returned 125, bisect moved to a neighbour and still converged. Without exit code 125, the oracle would have called the broken commit "bad" and bisect would have reported the WIP commit as the culprit: a wrong answer from a correct tool.
3. **Two tests fail on `HEAD`, one cause.** `TestTitles` (added by commit 3) fails too, but only because `Titles()` calls `List()`. A good oracle tests the *symptom you want to track* (here the ordering), not whatever fails first.
4. **Worktrees run two versions at once.** `v1.0` passes while `v1.1` fails, from the same repository, without checkout or stash. `git worktree list` shows three directories sharing one `.git`.
5. **Bisect only finds the first bad commit.** It assumes "once broken, always broken". A regression that appears and disappears (a flaky test) gives a wrong answer; make the oracle repeat the test several times and call the commit bad on any failure.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| bisect names a commit that is obviously innocent | the oracle returned 1 on a build failure | return 125 for "does not build" (see `bisect-test.sh`) |
| `bisect run` stops with `bisect run failed: exit code N` | the oracle exited with a code above 127 (for example a missing command, 127 counts as bad but 128+ aborts) | run the oracle by hand on one commit and read its error |
| `error: You have local changes` while bisecting | a leftover edit in the working tree | `git stash` or `git checkout .`, then `git bisect reset` |
| `fatal: '../rel-v1.0' already exists` | a worktree from an earlier run | `git worktree remove ../rel-v1.0` (or `git worktree prune` if the folder is gone) |
| `go test` passes in the worktree although the commit is bad | Go's test cache served a result for unchanged files | add `-count=1`, as the oracle does |
| the same branch cannot be checked out in two worktrees | Git forbids it | use a detached HEAD (`git worktree add <dir> <tag>`) or a new branch name |
| you forgot `git bisect reset` | HEAD is detached at the last tested commit | `git bisect reset` returns to `main` |

## Extension task

Replace the unit test by an end-to-end oracle written in Python: start `go run ./cmd/registration-api` on a free port (`ADDR=:18080`), request `GET /courses` with `urllib.request`, check that the first course is `SE101`, stop the server, and return 0 or 1. Use it as the oracle for `git bisect run` and confirm that it finds the same commit. Make it return 125 when the server does not start in 5 seconds. No solution is provided for this task.

Solution of the lab: [`solution/`](solution/) (`run-all.sh`, `expected-transcript.txt`).
