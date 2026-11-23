#!/usr/bin/env bash
# run-all.sh: reference solution of lab 01.4. Does everything the README does and checks the result.
#   bash solution/run-all.sh [scratch-dir]
# Exit code 0 means bisect found the regression commit and the worktree comparison behaved as expected.
set -euo pipefail

lab="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="${1:-${TMPDIR:-/tmp}/ase-lab04}"
rm -rf "$scratch"

bash "$lab/seed_regression.sh" "$scratch/repo"
cd "$scratch/repo"

echo '$ go test ./...   # on HEAD'
go test ./... || true

echo '$ git bisect start HEAD v1.0'
git bisect start HEAD v1.0
echo '$ git bisect run bash bisect-test.sh'
git bisect run bash "$lab/bisect-test.sh" || true
culprit="$(git rev-parse --short refs/bisect/bad)"
git bisect reset
subject="$(git log -1 --format=%s "$culprit")"
echo "culprit: $culprit $subject"
[ "$subject" = "catalog: show newest course IDs first" ] || { echo "unexpected culprit" >&2; exit 1; }

echo '$ git worktree add ../rel-v1.0 v1.0; git worktree add ../rel-v1.1 v1.1'
git worktree add ../rel-v1.0 v1.0
git worktree add ../rel-v1.1 v1.1
git worktree list

echo '$ run the ordering test in both worktrees at the same time'
(cd ../rel-v1.0 && go test ./internal/catalog -run TestListIsSortedByID -count=1 2>&1 | sed 's/^/[v1.0] /') &
(cd ../rel-v1.1 && go test ./internal/catalog -run TestListIsSortedByID -count=1 2>&1 | sed 's/^/[v1.1] /') &
wait

echo '$ fix the regression on a branch with git revert, test, clean up'
git switch -q -c fix-order
git revert --no-edit "$culprit" > /dev/null
go test ./... > /dev/null && echo "fixed: go test ./... passes on fix-order"
git switch -q main
git worktree remove ../rel-v1.0
git worktree remove ../rel-v1.1
git worktree list
