#!/usr/bin/env bash
# seed_repo.sh: create a scratch Git repository with a scripted, fully deterministic history.
#
#   bash seed_repo.sh <scratch-dir>
#
# Commit and tag dates are fixed with GIT_AUTHOR_DATE / GIT_COMMITTER_DATE, and the author is fixed, so every run
# produces the same history (even the same commit IDs). The history is SYNTHETIC: eight weeks of a small team that
# releases often, with three releases that had to be repaired. Real teams look different.
#
# Conventions the history follows (dora.py relies on them):
#   - a deployment is an annotated tag named v*
#   - a commit that repairs a broken release carries the trailer "Fixes-release: <tag>"
set -euo pipefail

dest="${1:?usage: bash seed_repo.sh <scratch-dir>}"
if [ -e "$dest" ] && [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
  echo "refusing to use a non-empty directory: $dest" >&2
  exit 1
fi
mkdir -p "$dest"
cd "$dest"
git init -q -b main
git config user.name "Lab Student"
git config user.email "student@example.com"
git config core.autocrlf false
git config commit.gpgsign false
git config tag.gpgsign false

n=0
# commit <author-date> <subject> [trailer] [committer-date]   (dates are UTC, ISO 8601)
commit() {
  local adate="$1" subject="$2" trailer="${3:-}" cdate="${4:-$1}"
  n=$((n + 1))
  echo "$n $subject" >> work.log
  git add work.log
  local msg="$subject"
  if [ -n "$trailer" ]; then msg="$subject

$trailer"; fi
  GIT_AUTHOR_DATE="${adate}Z" GIT_COMMITTER_DATE="${cdate}Z" git commit -q -m "$msg"
}
# release <date> <tag>
release() {
  GIT_COMMITTER_DATE="${1}Z" git tag -a "$2" -m "Release $2"
}

# week 1
commit 2026-03-02T09:00:00 "Add course list endpoint"
commit 2026-03-02T15:30:00 "Add health check"
commit 2026-03-03T11:00:00 "Validate course capacity"
commit 2026-03-04T10:00:00 "Add seat counter"
release 2026-03-05T10:00:00 v0.1.0
commit 2026-03-05T14:00:00 "Add waitlist model"
commit 2026-03-06T09:30:00 "Return 404 for unknown course"
# week 2
commit 2026-03-09T10:00:00 "Add student endpoint"
commit 2026-03-10T16:00:00 "Add enrollment rules"
commit 2026-03-11T09:00:00 "Fix typo in README"
release 2026-03-12T11:00:00 v0.2.0
commit 2026-03-12T15:00:00 "Add prerequisite check"
commit 2026-03-13T08:00:00 "Fix crash on empty prerequisite list" "Fixes-release: v0.2.0"
release 2026-03-13T09:30:00 v0.2.1
# week 3 (the last commit was written on 03-17 but rebased onto main on 03-18: author date != committer date)
commit 2026-03-16T10:00:00 "Add capacity report"
commit 2026-03-17T11:00:00 "Add CSV export" "" 2026-03-18T09:00:00
commit 2026-03-18T14:00:00 "Refactor catalog sorting"
release 2026-03-19T14:00:00 v0.3.0
# week 4
commit 2026-03-23T10:00:00 "Add email notification stub"
commit 2026-03-24T13:00:00 "Add retry logic"
commit 2026-03-25T15:00:00 "Add audit log"
release 2026-03-26T10:00:00 v0.4.0
commit 2026-03-26T17:00:00 "Revert audit log" "Fixes-release: v0.4.0"
release 2026-03-27T10:00:00 v0.4.1
# week 5
commit 2026-03-30T09:00:00 "Add drop-course endpoint"
commit 2026-03-31T10:30:00 "Add tests for drop-course"
commit 2026-04-01T16:00:00 "Update API documentation"
release 2026-04-02T11:00:00 v0.5.0
# week 6
commit 2026-04-06T10:00:00 "Add course swap endpoint"
commit 2026-04-07T12:00:00 "Add swap audit trail"
commit 2026-04-08T09:00:00 "Speed up course search"
release 2026-04-09T10:00:00 v0.6.0
commit 2026-04-13T10:00:00 "Fix double enrollment on swap" "Fixes-release: v0.6.0"
release 2026-04-14T16:00:00 v0.6.1
# week 7-8
commit 2026-04-15T09:00:00 "Add instructor view"
commit 2026-04-16T11:00:00 "Add attendance import"
commit 2026-04-20T10:00:00 "Add grade export"
release 2026-04-21T10:00:00 v0.7.0
commit 2026-04-22T14:00:00 "Add dashboard widgets"
commit 2026-04-23T10:00:00 "Tune database indexes"
release 2026-04-24T15:00:00 v0.8.0
# two commits that are merged but not released yet
commit 2026-04-27T10:00:00 "Add holiday calendar"
commit 2026-04-28T09:30:00 "Add locale switcher"

echo "seeded $n commits and $(git tag | wc -l | tr -d ' ') release tags in $dest"
git log --oneline --decorate -5
