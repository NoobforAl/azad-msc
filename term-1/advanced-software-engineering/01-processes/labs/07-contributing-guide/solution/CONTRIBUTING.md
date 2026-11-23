# Contributing to the Course Registration Platform

This guide is the `m1` result of lab 01.7. Its shape follows `Documentation/process/submitting-patches.rst` of the Linux kernel (v6.18.63); the rules and numbers below are this project's own choices, adapted from it. The rules are checked by `tools/check_commit_msgs.py`.

## 1. Before you start

- Run `python tools/gates.py` (gofmt, `go vet`, `ruff`, tests, coverage >= 70%). A change that makes a gate red is not ready for review. CI runs the same script.
- Look for an existing issue. For anything larger than a bug fix, describe the problem in an issue first.

## 2. One logical change per commit

Each commit makes one change that a reviewer can understand and verify on its own: a bug fix and a refactoring are two commits, a change that touches ten files in the same way is one. The test of a commit is that you can describe it in one sentence without the word "and". Commits must build and pass the tests, so that `git bisect` works (lab 01.4).

## 3. Commit messages

```text
area: summary in the imperative mood

Why the change is needed (the problem), what it changes, and what the user
or the caller notices. Wrap lines at 75 columns.

Signed-off-by: Your Name <you@example.com>
```

| # | Rule | Checked as |
|---|---|---|
| 1 | The subject is `area: summary`, at most 72 characters, no trailing period. `area` is the package or folder you change (`catalog`, `api`, `analytics`, `ci`, `docs`). | S2, S3, S4 |
| 2 | Write the subject in the imperative mood: "add Count", not "added" or "adds". | review only (a script cannot judge it) |
| 3 | A blank line follows the subject. The body explains the problem first, then the change. | B1 |
| 4 | Body lines are at most 75 characters; code, URLs and trailers may be longer. | B2 |
| 5 | Every commit has a `Signed-off-by:` line with the name and address of its author (`git commit -s`). Reverts too. | T1, T2 |
| 6 | A commit that repairs a broken release carries the trailer `Fixes-release: v0.3.0` (the release it repairs). The DORA script of lab 01.1 reads it. | review |
| 7 | A commit that fixes an earlier commit may add `Fixes: <12-character hash> ("subject of that commit")`. | review |

By adding `Signed-off-by:` you certify the Developer's Certificate of Origin 1.1, the text of which is in `Documentation/process/submitting-patches.rst` in the Linux sources: you wrote the change or have the right to submit it under the project's licence. We do not repeat the text here.

Install the hook to catch mistakes before they are committed:

```bash
cp tools/commit-msg .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg
python tools/check_commit_msgs.py origin/main..HEAD      # check a whole branch before you push
```

## 4. Branches, pull requests and releases

- `main` is always releasable. Work on short-lived branches named `<area>/<topic>` (for example `catalog/count`) and merge them back within days, not weeks: long branches are what makes the lead time of lab 01.1 long.
- Open a pull request with the template in `.github/PULL_REQUEST_TEMPLATE.md`. Keep it small: if a reviewer cannot read it in one sitting, split it.
- In the description say: the problem, the user-visible impact, what you changed, and how you tested it. Convince the reviewer that the problem is worth fixing before you describe the fix.
- Merge only when CI is green and a reviewer approved. If you squash, the squashed commit must follow section 3 and keep every `Signed-off-by:` line.
- Releases are annotated tags `vMAJOR.MINOR.PATCH` on `main`, created after the gates are green: `git tag -a v0.3.0 -m "Release v0.3.0"`. Lab 01.1 counts these tags as deployments.

## 5. Review etiquette

- Reviewers: review the change, not the person; ask a question when you do not understand, because the next reader will not either; say clearly which comments must be fixed before merging and which are suggestions.
- Authors: answer every comment. If a comment does not lead to a code change, say why, or add a comment in the code so the next reader gets the answer. Say what you changed in the next version, and thank the reviewer.
- Do not take silence as approval, and do not merge your own change without a review.

## 6. Reviewer checklist

See `.github/PULL_REQUEST_TEMPLATE.md`; it is the checklist both sides use.
