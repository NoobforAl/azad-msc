#!/usr/bin/env bash
# seed_regression.sh: build m0 in a scratch directory, then add 11 scripted commits, one of which is a regression.
#
#   bash seed_regression.sh <scratch-dir>
#
# History after m0 (dates are fixed; the regression is NOT announced in any commit message):
#   c1..c5   harmless changes, then tag v1.0
#   c6       the regression (List() starts returning courses in the wrong order)
#   c7..c11  more changes; c8 does not compile (a "work in progress" commit), c9 repairs it; then tag v1.1
# The commit subjects are the only clue a human has; `git bisect run` finds c6 from the test alone.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${1:?usage: bash seed_regression.sh <scratch-dir>}"
bash "$here/../prepare-m0.sh" "$dest" > /dev/null
cd "$dest"

# commit <iso-date> <subject>  (formats Go code first, so the heredocs below may use spaces)
commit() {
  gofmt -w cmd internal
  git add -A
  GIT_AUTHOR_DATE="${1}Z" GIT_COMMITTER_DATE="${1}Z" git commit -q -m "$2"
}

cat > CHANGELOG.md <<'EOF'
# Changelog

## 1.0 (in progress)
- course catalog with GET /courses
EOF
commit 2026-05-04T09:00:00 "docs: add CHANGELOG"

cat >> internal/catalog/catalog.go <<'EOF'

// Count returns the number of courses.
func (c *Catalog) Count() int { return len(c.courses) }
EOF
cat > internal/catalog/catalog_extra_test.go <<'EOF'
package catalog

import "testing"

func TestCount(t *testing.T) {
    c := New(Course{ID: "SE1"}, Course{ID: "SE2"})
    if got := c.Count(); got != 2 {
        t.Fatalf("Count() = %d, want 2", got)
    }
}
EOF
commit 2026-05-05T10:00:00 "catalog: add Count"

cat >> internal/catalog/catalog.go <<'EOF'

// Titles returns the course titles in ID order.
func (c *Catalog) Titles() []string {
    var titles []string
    for _, course := range c.List() {
        titles = append(titles, course.Title)
    }
    return titles
}
EOF
cat >> internal/catalog/catalog_extra_test.go <<'EOF'

func TestTitles(t *testing.T) {
    c := New(Course{ID: "B", Title: "Second"}, Course{ID: "A", Title: "First"})
    got := c.Titles()
    if len(got) != 2 || got[0] != "First" || got[1] != "Second" {
        t.Fatalf("Titles() = %v, want [First Second]", got)
    }
}
EOF
commit 2026-05-06T11:00:00 "catalog: add Titles"

cat >> README.md <<'EOF'

## API

- `GET /healthz` returns `{"status":"ok"}`.
- `GET /courses` returns all courses ordered by ID.
EOF
commit 2026-05-07T09:30:00 "docs: document the API in README"

cat >> internal/catalog/catalog.go <<'EOF'

// TotalCapacity returns the sum of all course capacities.
func (c *Catalog) TotalCapacity() int {
    total := 0
    for _, course := range c.courses {
        total += course.Capacity
    }
    return total
}
EOF
cat >> internal/catalog/catalog_extra_test.go <<'EOF'

func TestTotalCapacity(t *testing.T) {
    c := New(Course{ID: "A", Capacity: 30}, Course{ID: "B", Capacity: 12})
    if got := c.TotalCapacity(); got != 42 {
        t.Fatalf("TotalCapacity() = %d, want 42", got)
    }
}
EOF
commit 2026-05-08T15:00:00 "catalog: add TotalCapacity"
GIT_COMMITTER_DATE="2026-05-08T16:00:00Z" git tag -a v1.0 -m "Release v1.0"

# c6: the regression. It looks like a harmless presentation tweak and no test in the commit contradicts it.
sed -i.bak 's/return out\[i\].ID < out\[j\].ID/return out[i].ID > out[j].ID/' internal/catalog/catalog.go
rm -f internal/catalog/catalog.go.bak
commit 2026-05-11T10:00:00 "catalog: show newest course IDs first"

cat >> CHANGELOG.md <<'EOF'

## 1.1
- newest courses first
- Count, Titles, TotalCapacity helpers
EOF
commit 2026-05-12T09:00:00 "docs: update CHANGELOG for 1.1"

# c8: does not compile (undefined: lookupTitle). Typical "work in progress" commit.
cat >> internal/catalog/catalog.go <<'EOF'

// GetByTitle returns the first course with the given title.
func (c *Catalog) GetByTitle(title string) (Course, bool) {
    return lookupTitle(c.courses, title)
}
EOF
commit 2026-05-13T11:00:00 "catalog: WIP GetByTitle"

cat >> internal/catalog/catalog.go <<'EOF'

func lookupTitle(courses map[string]Course, title string) (Course, bool) {
    for _, course := range courses {
        if course.Title == title {
            return course, true
        }
    }
    return Course{}, false
}
EOF
cat >> internal/catalog/catalog_extra_test.go <<'EOF'

func TestGetByTitle(t *testing.T) {
    c := New(Course{ID: "A", Title: "First"})
    if _, ok := c.GetByTitle("First"); !ok {
        t.Fatal("GetByTitle(First) not found")
    }
}
EOF
commit 2026-05-14T10:30:00 "catalog: finish GetByTitle"

cat >> internal/catalog/catalog.go <<'EOF'

// Remove deletes a course and reports whether it existed.
func (c *Catalog) Remove(id string) bool {
    _, ok := c.courses[id]
    delete(c.courses, id)
    return ok
}
EOF
cat >> internal/catalog/catalog_extra_test.go <<'EOF'

func TestRemove(t *testing.T) {
    c := New(Course{ID: "A"})
    if !c.Remove("A") || c.Remove("A") {
        t.Fatal("Remove must report true once, then false")
    }
}
EOF
commit 2026-05-15T14:00:00 "catalog: add Remove"

cat >> README.md <<'EOF'

The catalog can also remove courses (`Remove`), used by the admin tools planned for module 02.
EOF
commit 2026-05-18T09:00:00 "docs: mention Remove in README"
GIT_COMMITTER_DATE="2026-05-18T10:00:00Z" git tag -a v1.1 -m "Release v1.1"

echo "seeded $(git rev-list --count m0..HEAD) commits after m0 in $dest (tags: v1.0, v1.1)"
git log --oneline --decorate m0..HEAD
