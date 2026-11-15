#!/usr/bin/env bash
# cite.sh: print a verified excerpt + its citation line, straight from the local checkout.
# Every course uses this so quotes are never typed from memory.
#
#   bash _shared/sources/cite.sh linux   kernel/fork.c   kernel_clone        [max_lines=25]
#   bash _shared/sources/cite.sh openbsd sys/kern/kern_fork.c fork1          [max_lines=25]
#   bash _shared/sources/cite.sh linux   fs/read_write.c L552                # start at a line number
#
# Output: a citation line (repo/path · symbol() · pin · Lstart-end), then the numbered excerpt.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="${1:?repo: linux|openbsd}"; path="${2:?path inside the repo}"; sym="${3:?symbol or L<line>}"
max="${4:-25}"
root="$here/$repo"
file="$root/$path"
[ -f "$file" ] || { echo "not in checkout: $repo/$path (try: git -C $root sparse-checkout add $(dirname "$path"))" >&2; exit 1; }

case "$repo" in
  linux)   pin="v6.18.63" ;;
  openbsd) pin="$(git -C "$root" rev-parse --short=7 HEAD)" ;;
  *) echo "unknown repo $repo" >&2; exit 2 ;;
esac

if [[ "$sym" =~ ^L([0-9]+)$ ]]; then
  start="${BASH_REMATCH[1]}"; label="L$start"
else
  # A definition: the symbol followed by "(" on a line that is not indented and is not a call
  # ending in ";". Kernel style puts the return type either on the same line or the previous one.
  start="$(grep -nE "^([A-Za-z_].*[^A-Za-z0-9_])?${sym}\(" "$file" | grep -vE ';[[:space:]]*$' | head -1 | cut -d: -f1 || true)"
  [ -n "$start" ] || start="$(grep -nE "\b${sym}\b" "$file" | head -1 | cut -d: -f1 || true)"
  [ -n "$start" ] || { echo "symbol '$sym' not found in $repo/$path" >&2; exit 1; }
  # include the return-type line above (e.g. "static int\nfoo(...)")
  prev=$((start - 1))
  if [ "$prev" -ge 1 ] && sed -n "${prev}p" "$file" | grep -qE '^[a-z_][a-z_ *]*$'; then start="$prev"; fi
  label="${sym}()"
fi

end=$((start + max - 1))
total="$(wc -l < "$file")"
[ "$end" -le "$total" ] || end="$total"

echo "${repo}/${path} · ${label} · ${pin} · L${start}-${end}"
sed -n "${start},${end}p" "$file" | awk -v n="$start" '{ printf "%5d  %s\n", n++, $0 }'
