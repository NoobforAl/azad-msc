#!/usr/bin/env bash
# Render every diagram source next to this script into an .svg file.
#   *.mmd   -> Mermaid, through mermaid-cli (needs node/npx and Chrome, Edge or Chromium)
#   *.puml  -> PlantUML, through the plantuml/plantuml Docker image
#   workspace.dsl -> Structurizr: export to Mermaid (c4/*.mmd), then render those like any other .mmd
# Usage: bash render-diagrams.sh            (set BROWSER=/path/to/chrome if it is not found automatically)
set -euo pipefail
cd "$(dirname "$0")"

MERMAID_CLI="@mermaid-js/mermaid-cli@12.2.0"
PLANTUML_IMAGE="plantuml/plantuml:latest"
STRUCTURIZR_IMAGE="structurizr/structurizr:latest"

# Docker needs a Windows-style path for bind mounts in Git Bash; Linux and macOS use $PWD as is.
case "$(uname -s)" in
  MINGW* | MSYS*) HOST_DIR="$(pwd -W)"; export MSYS_NO_PATHCONV=1 ;;
  *) HOST_DIR="$PWD" ;;
esac

find_browser() {
  if [ -n "${BROWSER:-}" ]; then echo "$BROWSER"; return; fi
  for p in \
    "/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)"; do
    if [ -n "$p" ] && [ -x "$p" ]; then echo "$p"; return; fi
  done
}

render_mermaid() { # $1 = source .mmd, $2 = output .svg
  local browser
  browser="$(find_browser)"
  if [ -z "$browser" ]; then
    echo "skip $1: no Chrome/Edge/Chromium found (set BROWSER=...) -- or open mermaid-preview.html" >&2
    return 0
  fi
  # Node is a Windows program: give it a Windows path when running under Git Bash.
  if command -v cygpath >/dev/null 2>&1; then browser="$(cygpath -w "$browser")"; fi
  # Reuse the installed browser instead of letting puppeteer download its own (about 150 MB).
  PUPPETEER_SKIP_DOWNLOAD=1 PUPPETEER_EXECUTABLE_PATH="$browser" npx --yes "$MERMAID_CLI" -i "$1" -o "$2" >/dev/null
  echo "rendered $2"
}

for src in *.mmd; do
  if [ -e "$src" ]; then render_mermaid "$src" "${src%.mmd}.svg"; fi
done

for src in *.puml; do
  [ -e "$src" ] || continue
  docker run --rm -v "$HOST_DIR:/data" -w /data "$PLANTUML_IMAGE" -tsvg "$src"
  echo "rendered ${src%.puml}.svg"
done

if [ -e workspace.dsl ]; then
  docker run --rm -v "$HOST_DIR:/usr/local/structurizr" "$STRUCTURIZR_IMAGE" \
    validate -workspace workspace.dsl
  docker run --rm -v "$HOST_DIR:/usr/local/structurizr" "$STRUCTURIZR_IMAGE" \
    export -workspace workspace.dsl -format mermaid -output c4 >/dev/null
  for src in c4/*.mmd; do
    render_mermaid "$src" "c4-$(basename "${src%.mmd}" | sed 's/^structurizr-//').svg"
  done
fi
