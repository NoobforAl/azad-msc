#!/usr/bin/env bash
# prepare-m0.sh: build the "m0" state of the running project in a scratch directory.
#
#   bash prepare-m0.sh <scratch-dir>
#
# The course repository has no Git tags. This script copies project/ into <scratch-dir>, adds the repository's
# ruff.toml (so `ruff check` behaves the same outside the course repo), runs `git init`, commits and tags m0.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project="$here/../../project"
ruff_cfg="$here/../../../../ruff.toml"
dest="${1:?usage: bash prepare-m0.sh <scratch-dir>}"

if [ -e "$dest" ] && [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
  echo "refusing to use a non-empty directory: $dest" >&2
  exit 1
fi
mkdir -p "$dest"
cp -R "$project/." "$dest/"
find "$dest" -name __pycache__ -type d -prune -exec rm -rf {} +
cp "$ruff_cfg" "$dest/ruff.toml"
printf '__pycache__/\n.ruff_cache/\nbin/\n*.out\n' > "$dest/.gitignore"

cd "$dest"
git init -q -b main
git config user.name "Lab Student"
git config user.email "student@example.com"
git config core.autocrlf false
git config commit.gpgsign false
git config tag.gpgsign false
git add -A
export GIT_AUTHOR_DATE="2026-03-01T09:00:00Z" GIT_COMMITTER_DATE="2026-03-01T09:00:00Z"   # fixed, so later labs sort after it
git commit -q -m "Import project skeleton (m0)"
git tag -a m0 -m "m0: project skeleton from 00-setup"
unset GIT_AUTHOR_DATE GIT_COMMITTER_DATE
echo "m0 ready in $dest"
git log --oneline --decorate
