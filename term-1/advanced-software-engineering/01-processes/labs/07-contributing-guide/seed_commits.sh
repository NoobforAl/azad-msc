#!/usr/bin/env bash
# seed_commits.sh: build m0 in a scratch directory, then add six commits with deliberately mixed message quality.
#
#   bash seed_commits.sh <scratch-dir>
#
# Commit 1 and 5 follow the rules of CONTRIBUTING.md. Commits 2, 3, 4 and 6 each break one or more of them, so the
# checker (check_commit_msgs.py) has something to find. Dates and authors are fixed.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${1:?usage: bash seed_commits.sh <scratch-dir>}"
bash "$here/../prepare-m0.sh" "$dest" > /dev/null
cd "$dest"

# commit <iso-date>   (the message comes from standard input)
commit() {
  git add -A
  GIT_AUTHOR_DATE="${1}Z" GIT_COMMITTER_DATE="${1}Z" git commit -q -F -
}

printf '\n// Count returns the number of courses.\nfunc (c *Catalog) Count() int { return len(c.courses) }\n' >> internal/catalog/catalog.go
commit 2026-06-01T09:00:00 <<'EOF'
catalog: add Count

The catalog had no way to report its size, so callers had to call List()
and take the length of the copy. Count reads the map directly.

Signed-off-by: Lab Student <student@example.com>
EOF

printf '\nNotes: work in progress.\n' >> README.md
commit 2026-06-02T09:00:00 <<'EOF'
Fixed stuff.
EOF

printf '\nA second note.\n' >> README.md
commit 2026-06-03T09:00:00 <<'EOF'
catalog: add a method that returns how many courses are currently stored in the in-memory catalog

Signed-off-by: Lab Student <student@example.com>
EOF

printf '\nAPI notes.\n' >> README.md
commit 2026-06-04T09:00:00 <<'EOF'
docs: explain the API
The README lacked any description of the two endpoints, which made it hard for new contributors to try the service by hand.

Signed-off-by: Pat Reviewer <pat@example.com>
EOF

printf '\nDocs: see CONTRIBUTING.md.\n' >> README.md
commit 2026-06-05T09:00:00 <<'EOF'
docs: point the README to CONTRIBUTING.md

New contributors read the README first. Link the rules from there.

Signed-off-by: Lab Student <student@example.com>
EOF

printf '\nTODO list.\n' >> README.md
commit 2026-06-08T09:00:00 <<'EOF'
WIP
EOF

echo "seeded 6 commits after m0 in $dest"
git log --oneline --decorate m0..HEAD
