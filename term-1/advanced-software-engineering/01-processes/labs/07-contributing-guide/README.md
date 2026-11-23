# Lab 01.7 — A CONTRIBUTING guide and a commit-message checker, modelled on the Linux kernel

**Goal:** write `CONTRIBUTING.md` and a review checklist for the project, adapted from the Linux kernel's patch-submission rules, and enforce the mechanical part of them with a small Python checker and a Git hook.

Runs on: Git, Python >= 3.8 (stdlib only), Bash. Time: 75 min. Difficulty: medium to hard (this is the capstone of the module).

## Starting state

- Module state `m0`, built in a scratch directory with [`../prepare-m0.sh`](../prepare-m0.sh) (copy `project/`, `git init`, commit, tag `m0`; the course repository has no tags). `seed_commits.sh` calls it and adds six commits with mixed message quality.
- Ending state: the scratch repository has `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `tools/check_commit_msgs.py` and a working `commit-msg` hook. This completes `m1`: CI gates (lab 02), DORA script (lab 01), `CONTRIBUTING.md` (this lab) (see [`../README.md`](../README.md)).

## Background: what the Linux kernel asks of a patch

The kernel's own guide is `Documentation/process/submitting-patches.rst` (checkout pinned to v6.18.63). Three passages matter for this lab. Excerpts are copied unchanged from the checkout.

**1. The shape of a patch message.** `linux/Documentation/process/submitting-patches.rst · "Subject Line" (L649-666) · v6.18.63`

```rst
The canonical patch subject line is::

    Subject: [PATCH 001/123] subsystem: summary phrase

The canonical patch message body contains the following:

  - A ``from`` line specifying the patch author, followed by an empty
    line (only needed if the person sending the patch is not the author).

  - The body of the explanation, line wrapped at 75 columns, which will
    be copied to the permanent changelog to describe this patch.

  - An empty line.

  - The ``Signed-off-by:`` lines, described above, which will
    also go in the changelog.

  - A marker line containing simply ``---``.
```

- L649-651: the subject has the form `subsystem: summary phrase` (the `[PATCH 001/123]` part belongs to e-mail workflows and is not needed for a Git hosting service).
- L655-656: the `from` line is needed only when the sender is not the author; in a pull-request workflow Git records the author itself.
- L658-659: the body explains the change and is wrapped at 75 columns; it becomes the permanent changelog.
- L661-664: an empty line, then the `Signed-off-by:` lines.
- L666: the `---` marker ends the changelog; text below it is for reviewers and is dropped when the patch is applied. We have no such marker: the pull-request description plays that role.

**2. How long the summary may be.** `linux/Documentation/process/submitting-patches.rst · "Subject Line" (L696-699) · v6.18.63`

```rst
For these reasons, the ``summary`` must be no more than 70-75
characters, and it must describe both what the patch changes, as well
as why the patch might be necessary.  It is challenging to be both
succinct and descriptive, but that is what a well-written summary
```

- L696-697: the limit is "70-75" characters; the document is vague on purpose. Our checker needs one number, so we choose 72 (a project decision, not the kernel's).
- L697-699: the summary must say *what* changes and *why*; a subject like "Fixed stuff." fails this test even before any script looks at it.

**3. Marking a fix.** `linux/Documentation/process/submitting-patches.rst · "Describe your changes" (L145-151) · v6.18.63`

```rst
If your patch fixes a bug in a specific commit, e.g. you found an issue using
``git bisect``, please use the 'Fixes:' tag with at least the first 12
characters of the SHA-1 ID, and the one line summary.  Do not split the tag
across multiple lines, tags are exempt from the "wrap at 75 columns" rule in
order to simplify parsing scripts.  For example::

	Fixes: 54a4f0239f2e ("KVM: MMU: make kvm_mmu_zap_page() return the number of pages it actually freed")
```

- L145-146: "e.g. you found an issue using `git bisect`": the output of lab 04 (the culprit) is exactly what goes after `Fixes:`.
- L147-148: tags are exempt from the 75-column rule so scripts can parse them; our checker exempts trailers for the same reason.
- Our adaptation: the same idea for releases, `Fixes-release: <tag>`, which the DORA script of lab 01 reads.

**A different setting.** The kernel relies on mailing-list review and on chains of `Signed-off-by:` lines through maintainers; a course project on a Git hosting service uses pull requests, so a pull-request template plays the role of the e-mail conventions. How the OpenBSD project handles commits is part of the module 01 case study and was not checked for this lab. Whether mandatory sign-off is worth the friction for a small team is `OPINION / CONTESTED`.

## Steps

```bash
cd term-1/advanced-software-engineering/01-processes/labs/07-contributing-guide
LAB="$PWD"
python -m unittest test_check_commit_msgs -v 2>&1 | tail -4        # tests of the checker
SCRATCH="${TMPDIR:-/tmp}/ase-lab07"
bash seed_commits.sh "$SCRATCH"                                     # m0 plus six commits
cd "$SCRATCH"
mkdir -p tools .github
cp "$LAB/check_commit_msgs.py" tools/
python tools/check_commit_msgs.py m0..HEAD; echo "exit code $?"     # 4 of 6 commits violate the rules
git log --oneline m0..HEAD | head -3                                # see how git shows the commit without a blank line

# your task: write CONTRIBUTING.md and .github/PULL_REQUEST_TEMPLATE.md (compare with $LAB/solution/ afterwards)

# enforce the rules when committing
cp "$LAB/solution/commit-msg" .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg
echo "// note" >> internal/catalog/catalog.go && git add -A
git commit -m "wip stuff"                                           # rejected by the hook
git commit -s -m "catalog: add a note about ordering"              # accepted
```

**Your task:** (1) write `CONTRIBUTING.md` for the project with at least: one logical change per commit, the commit-message format with the rules the checker enforces, sign-off, how to open and review a pull request, and how releases are tagged; (2) write a pull-request template with an author checklist and a reviewer checklist; (3) say, for each rule, whether it is **mechanical** (the checker enforces it) or **judgement** (only a reviewer can), and explain why "imperative mood" is in the second group. Then compare with [`solution/CONTRIBUTING.md`](solution/CONTRIBUTING.md) and [`solution/PULL_REQUEST_TEMPLATE.md`](solution/PULL_REQUEST_TEMPLATE.md).

Linux / macOS: the hook calls `python`; if your system only has `python3`, edit the last line of the hook. Windows: run the commands in Git Bash so the hook (a Bash script) runs.

## Code

- [`check_commit_msgs.py`](check_commit_msgs.py): `check_message()` applies rules S1-S4 (subject), B1-B2 (body), T1-T2 (trailers) to one message and returns the violations; `commits()` reads a range with `git log`; `--message-file` mode serves the hook. Exit code = number of bad commits.
- [`test_check_commit_msgs.py`](test_check_commit_msgs.py): 11 unit tests, one per rule and a few edge cases.
- [`seed_commits.sh`](seed_commits.sh): the scratch history (commits 1 and 5 are good; 2, 3, 4, 6 each break something).
- [`solution/commit-msg`](solution/commit-msg): the hook.

## Expected output

Captured on Windows 11, Git Bash, Python 3.12, 2026-11-23. Commit IDs depend on the content of `project/` at `m0`, so yours will differ.

```text
$ python tools/check_commit_msgs.py m0..HEAD; echo "exit code $?"
ok   4dd6d8a catalog: add Count
FAIL 7aa6165 Fixed stuff.
       [S3] subject ends with a period
       [S4] subject does not start with "area: " (example: "catalog: add Count")
       [T1] no Signed-off-by: line (git commit -s adds it)
FAIL 0c34022 catalog: add a method that returns how many courses are currently stored in the in-memory catalog
       [S2] subject is 97 characters (maximum 72)
FAIL 9acf462 docs: explain the API
       [B1] no blank line between the subject and the body
       [B2] line 2 is 123 characters (maximum 75)
       [T2] no Signed-off-by: line matches the author Lab Student <student@example.com>
ok   3ddd400 docs: point the README to CONTRIBUTING.md
FAIL 71b6b6c WIP
       [S4] subject does not start with "area: " (example: "catalog: add Count")
       [T1] no Signed-off-by: line (git commit -s adds it)
4 of 6 commits violate the rules
exit code 4

$ git log --oneline m0..HEAD | head -3
71b6b6c WIP
3ddd400 docs: point the README to CONTRIBUTING.md
9acf462 docs: explain the API The README lacked any description of the two endpoints, which made it hard for new contributors to try the service by hand.
```

Installing the hook and committing (captured in the same scratch repository):

```text
$ git commit -m "wip stuff"
commit message rejected: [S4] subject does not start with "area: " (example: "catalog: add Count")
commit message rejected: [T1] no Signed-off-by: line (git commit -s adds it)

$ git commit -s -m "catalog: add a note about ordering"
[main 237a98d] catalog: add a note about ordering
 2 files changed, 122 insertions(+)
 create mode 100644 tools/check_commit_msgs.py
```

## What to observe

1. **Four of six commits fail, for three different kinds of reason.** S3 and S4 are style; T1 and T2 (sign-off) are about *provenance*; B1 is about how the tools treat the message: with no blank line, `git log --oneline` glues the body to the subject (commit `9acf462`) and the "one line per change" history that Linux describes in the lines just before L696 stops being readable. S2 (a 97-character subject) breaks the same history in another way.
2. **The checker cannot judge meaning.** "catalog: add Count" and "catalog: add stuff" both pass. The rule "describe both what the patch changes and why" (Linux, L697-699) is a review rule. A script can only guard the form; the template's reviewer checklist guards the content.
3. **A hook moves the failure to the cheapest moment.** The rejected commit costs seconds to fix; the same message found in CI or in review costs a round trip. This is the "cost of a late fault" of lab 03 applied to messages.
4. **Every number is a choice.** Linux says 70-75; the checker says 72. When you adopt a rule, write the number and the reason in `CONTRIBUTING.md`, or people will argue about it in each review.
5. **Rules are linked.** `Fixes-release:` ties this lab to lab 01 (DORA), `Fixes:` to lab 04 (bisect), the gates script to lab 02. A contributing guide is where those separate habits become one process.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| hook does nothing | file is not executable, or not named exactly `commit-msg` | `chmod +x .git/hooks/commit-msg`; on Windows use Git Bash |
| hook fails with `python: command not found` | the system only has `python3` | edit the hook's last line |
| `git commit` opens an editor and the checker sees `#` lines | the editor template contains comment lines | the checker ignores lines that start with `#` |
| T2 fires although the sign-off looks right | name or address differs from `git config user.name`/`user.email` | `git commit -s` uses exactly the configured identity |
| `git rebase` rewrites messages and the hook blocks it | the hook runs on rewords too | fix the message there; use `--no-verify` only on a throw-away branch |
| the checker rejects a merge commit | merge commits are skipped in range mode but not through `--message-file` | do not run the hook for merges, or amend the hook to skip `Merge ` subjects |
| you copied sentences from the kernel into `CONTRIBUTING.md` | tempting | quote at most a few lines with the source and version, and adapt the rest (this is also a licensing question: Linux documentation is GPL-licensed, `UNVERIFIED` here for the file's exact licence header) |

## Extension task

(a) Add rule T3: if a commit message has a `Fixes:` trailer, its first 12 characters must name a commit that exists in the repository (use `git cat-file -e`), and the quoted subject must match that commit's subject. Add unit tests. (b) Add a GitHub Actions job to the workflow of lab 02 that runs `python tools/check_commit_msgs.py origin/main..HEAD` on pull requests. (c) Write 5 lines on whether *your* team should require sign-off, and what would change your mind. No solution is provided for this task.

Solution of the lab: [`solution/`](solution/) (`CONTRIBUTING.md`, `PULL_REQUEST_TEMPLATE.md`, `commit-msg`).
