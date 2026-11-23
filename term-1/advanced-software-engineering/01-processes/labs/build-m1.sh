#!/usr/bin/env bash
# build-m1.sh: assemble the "m1" state (m0 + the results of all module-01 labs) in a scratch directory and check it.
#
#   bash build-m1.sh <scratch-dir>
#
# It uses the reference solutions, so it also proves that the seven labs fit together: the tools are ruff-clean,
# the quality gates pass on the result, and the commit message of the m1 commit follows the rules of CONTRIBUTING.md.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${1:?usage: bash build-m1.sh <scratch-dir>}"
bash "$here/prepare-m0.sh" "$dest" > /dev/null
cd "$dest"

mkdir -p tools .github/workflows
cp "$here/01-dora-metrics/dora.py" tools/
cp "$here/02-ci-quality-gates/gates.py" tools/
cp "$here/02-ci-quality-gates/solution/quality-gates.yml" .github/workflows/
cp "$here/03-cost-of-fault-simulation/fault_cost.py" tools/
cp "$here/04-git-bisect-worktrees/bisect-test.sh" tools/
cp "$here/05-kanban-flow-metrics/gen_issues.py" "$here/05-kanban-flow-metrics/flow_metrics.py" tools/
cp "$here/06-timebox-vs-waterfall/plan_compare.py" "$here/06-timebox-vs-waterfall/backlog.csv" tools/
cp "$here/07-contributing-guide/check_commit_msgs.py" tools/
cp "$here/07-contributing-guide/solution/commit-msg" tools/commit-msg
cp "$here/07-contributing-guide/solution/CONTRIBUTING.md" CONTRIBUTING.md
cp "$here/07-contributing-guide/solution/PULL_REQUEST_TEMPLATE.md" .github/PULL_REQUEST_TEMPLATE.md
chmod +x tools/bisect-test.sh tools/commit-msg
cp tools/commit-msg .git/hooks/commit-msg

echo "== ruff check tools"
ruff check tools
echo "== quality gates"
python tools/gates.py
echo "== m1 commit"
git add -A
GIT_AUTHOR_DATE="2026-03-02T09:00:00Z" GIT_COMMITTER_DATE="2026-03-02T09:00:00Z" git commit -q -s -F - <<'EOF'
ci: add module 01 tooling, gates and CONTRIBUTING.md

Add the DORA, fault-cost, Kanban and planning scripts, the quality gates
runner with its GitHub Actions workflow, the commit message checker and
hook, CONTRIBUTING.md and the pull-request template.
EOF
git tag -a m1 -m "m1: end of module 01"
echo "== commit messages since m0"
python tools/check_commit_msgs.py m0..HEAD
git log --oneline --decorate
