#!/usr/bin/env bash
# make doctor: check that this machine can use the course (slides, sources, lab VM).
# Prints OK / MISSING / WARN per item with an install hint for your OS.
# Exit code = number of REQUIRED items that are missing (0 = ready).
# Works in Git Bash (Windows), Linux and macOS. Read-only: installs nothing.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM="${VM:-aos-lab}"
fail=0

if [ -t 1 ]; then G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; B=$'\e[1m'; N=$'\e[0m'; else G='' R='' Y='' B='' N=''; fi
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) OS=windows ;;
  Darwin)               OS=mac ;;
  *)                    OS=linux ;;
esac

ok()   { printf "  %sOK%s       %-22s %s\n" "$G" "$N" "$1" "$2"; }
miss() { printf "  %sMISSING%s  %-22s %s\n" "$R" "$N" "$1" "$2"; fail=$((fail+1)); }
warn() { printf "  %sWARN%s     %-22s %s\n" "$Y" "$N" "$1" "$2"; }
hint() { # hint <windows> <linux> <mac>
  case "$OS" in windows) echo "$1" ;; linux) echo "$2" ;; mac) echo "$3" ;; esac
}
have() { command -v "$1" >/dev/null 2>&1; }

echo "${B}Course doctor${N}  (OS: $OS, repo: $ROOT)"

# ---------------------------------------------------------------- core
echo "${B}== Core (needed for everything)${N}"
if have git; then ok git "$(git --version | awk '{print $3}')"
else miss git "install: $(hint 'winget install Git.Git' 'sudo apt install git' 'xcode-select --install')"; fi

if have make; then ok make "$(make --version | head -1)"
else miss make "install: $(hint 'scoop install make  (or: choco install make / winget install ezwinports.make)' 'sudo apt install make' 'xcode-select --install')"; fi

PY=""
for c in python3 python py; do
  if have "$c" && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -n "$PY" ]; then ok python "$("$PY" -c 'import sys; print(sys.version.split()[0])') ($PY)"
else miss "python >= 3.8" "install: $(hint 'winget install Python.Python.3.12' 'sudo apt install python3' 'brew install python')"; fi

echo "  ${G}--${N}       node.js                not needed (decks are plain HTML; reveal.js loads from a CDN)"

# ---------------------------------------------------------------- slides
echo "${B}== Slides${N}"
browser=""
case "$OS" in
  windows)
    for p in "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
             "/c/Program Files/Google/Chrome/Application/chrome.exe" \
             "/c/Program Files/Mozilla Firefox/firefox.exe"; do
      [ -x "$p" ] && { browser="$(basename "$p")"; break; }
    done ;;
  mac)   for a in "Google Chrome" "Microsoft Edge" Firefox Safari; do
           [ -d "/Applications/$a.app" ] && { browser="$a"; break; }; done ;;
  linux) for b in google-chrome chromium chromium-browser microsoft-edge firefox; do
           have "$b" && { browser="$b"; break; }; done ;;
esac
if [ -n "$browser" ]; then ok browser "$browser"
else warn browser "none found; any modern browser works (Chrome/Edge/Firefox)"; fi

# PDF / PPTX export (optional): needs Edge, Chrome or Chromium; PPTX also needs python-pptx
if [ -n "$browser" ] && { [ "$browser" != firefox.exe ] && [ "$browser" != Firefox ] && [ "$browser" != Safari ] && [ "$browser" != firefox ]; }; then
  ok "pdf export" "make pdf M=01  ($browser)"
else warn "pdf export" "optional: needs Edge, Chrome or Chromium (Firefox cannot be used for make pdf / make pptx)"; fi
if [ -n "$PY" ] && "$PY" -c 'import pptx' >/dev/null 2>&1; then ok "pptx export" "python-pptx installed: make pptx M=01"
else warn "pptx export" "optional: pip install python-pptx   (only needed for make pptx)"; fi
if [ -f "$ROOT/.cache/vendor/browser-lab/manifest.json" ]; then ok "browser lab" "files cached: make browser-lab"
else warn "browser lab" "optional, for people without a VM: make browser-lab (downloads ~13 MB)"; fi

if [ -n "$PY" ]; then
  if "$PY" - <<'EOF' >/dev/null 2>&1
import urllib.request
for u in ("https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js",
          "https://fonts.googleapis.com/css2?family=Inter"):
    urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=8)
EOF
  then ok "CDN reachable" "cdn.jsdelivr.net, fonts.googleapis.com"
  else warn "CDN reachable" "cannot reach cdn.jsdelivr.net: decks will show unstyled text offline"; fi
fi

for f in _shared/theme/azad-theme.css _shared/theme/azad-deck.js _shared/tools/labdeck.py _shared/tools/serve.py; do
  [ -f "$ROOT/$f" ] || miss "$f" "file missing from the repo (git status / git pull)"
done
[ -f "$ROOT/_shared/theme/azad-theme.css" ] && ok theme "_shared/theme/"
if ls "$ROOT"/_shared/brand/azad-logo.* >/dev/null 2>&1; then ok logo "$(ls "$ROOT"/_shared/brand/azad-logo.* | head -1 | xargs basename)"
else warn logo "_shared/brand/azad-logo.svg missing: decks show a [University logo] placeholder"; fi

# ---------------------------------------------------------------- sources
echo "${B}== Kernel sources (for reading/quoting code)${N}"
if [ -f "$ROOT/_shared/sources/linux/kernel/fork.c" ]; then
  ok "linux sources" "_shared/sources/linux ($(git -C "$ROOT/_shared/sources/linux" describe --tags 2>/dev/null || echo pinned))"
else miss "linux sources" "run: make sources"; fi
if [ -f "$ROOT/_shared/sources/openbsd/sys/kern/kern_fork.c" ]; then
  ok "openbsd sources" "_shared/sources/openbsd ($(git -C "$ROOT/_shared/sources/openbsd" rev-parse --short=7 HEAD 2>/dev/null))"
else miss "openbsd sources" "run: make sources"; fi
if have ctags; then ok ctags "optional code navigation"; else warn ctags "optional: $(hint 'scoop install universal-ctags' 'sudo apt install universal-ctags' 'brew install universal-ctags')"; fi

# ---------------------------------------------------------------- lab VM
echo "${B}== Lab VM (needed for the labs, not for reading or slides)${N}"
if have ssh; then ok ssh "$(ssh -V 2>&1 | cut -d, -f1)"
else miss ssh "install: $(hint 'Settings > Optional features > OpenSSH Client' 'sudo apt install openssh-client' 'built in')"; fi
key=""
for k in id_ed25519 id_rsa id_ecdsa; do [ -f "$HOME/.ssh/$k.pub" ] && { key=$k; break; }; done
if [ -n "$key" ]; then ok "ssh key" "$HOME/.ssh/$key.pub"
else miss "ssh key" "run: ssh-keygen -t ed25519"; fi

VBM=""
for c in VBoxManage "/c/Program Files/Oracle/VirtualBox/VBoxManage.exe" /usr/local/bin/VBoxManage; do
  if have "$c" || [ -x "$c" ]; then VBM="$c"; break; fi
done
hyper=""
if [ -n "$VBM" ]; then
  ok VirtualBox "$("$VBM" --version 2>/dev/null)"; hyper=vbox
  if "$VBM" list vms 2>/dev/null | grep -q "\"$VM\""; then
    state=$("$VBM" showvminfo "$VM" --machinereadable 2>/dev/null | sed -n 's/^VMState="\(.*\)"/\1/p')
    ok "VM $VM" "exists, state: $state  (make vm-start / vm-ssh / vm-stop)"
  else
    warn "VM $VM" "not created yet: make vm-create"
  fi
fi
if have virsh; then
  ok libvirt "$(virsh --version 2>/dev/null)"; hyper="${hyper:-libvirt}"
  if [ -e /dev/kvm ]; then ok /dev/kvm "hardware virtualization available"
  else warn /dev/kvm "missing: enable VT-x/AMD-V in BIOS"; fi
fi
if [ -z "$hyper" ]; then
  miss hypervisor "install one: $(hint 'VirtualBox: winget install Oracle.VirtualBox' 'libvirt: sudo apt install qemu-kvm libvirt-daemon-system virtinst' 'VirtualBox or UTM')"
fi
if [ "$OS" = windows ] && have docker; then
  if docker info >/dev/null 2>&1; then ok docker "optional (used to build the cloud-init seed ISO)"
  else warn docker "installed but not running (only needed by make vm-create without WSL)"; fi
elif [ "$OS" = windows ]; then
  have wsl && ok wsl "used by make vm-create to build the seed ISO" \
           || warn "docker or wsl" "make vm-create needs one of them to build the seed ISO"
fi

if [ "$OS" = windows ]; then
  if have pwsh; then ok "PowerShell 7" "used by make vm-create"
  else warn "PowerShell 7" "needed by make vm-create: winget install Microsoft.PowerShell"; fi
fi

# ---------------------------------------------------------------- cache
echo "${B}== Cache (.cache/, git-ignored; make clean asks before deleting it)${N}"
size() { du -sh "$1" 2>/dev/null | cut -f1; }
if [ -f "$ROOT/.cache/vendor/manifest.json" ]; then ok "slide assets" "$(size "$ROOT/.cache/vendor") cached: slides work offline"
else warn "slide assets" "not cached yet: make view / make assets downloads them (~0.6 MB)"; fi
if [ -d "$ROOT/.cache/downloads" ]; then ok "VM downloads" "$(size "$ROOT/.cache/downloads") cached: make vm-create will not re-download"
else warn "VM downloads" "not cached yet: make cache (or make vm-create) downloads ~0.8 GB once"; fi
if [ -d "$ROOT/.cache/vm" ]; then ok "VM folder" "$(size "$ROOT/.cache/vm") in .cache/vm"; fi

# ---------------------------------------------------------------- authoring
echo "${B}== Authoring checks (optional)${N}"
if have shellcheck; then ok shellcheck "used by make check"; else warn shellcheck "optional: $(hint 'scoop install shellcheck' 'sudo apt install shellcheck' 'brew install shellcheck')"; fi

echo
if [ "$fail" -eq 0 ]; then echo "${G}${B}Ready.${N} Next: ${B}make view${N} (slides + lab VM), ${B}make stop${N} when done."
else echo "${R}${B}$fail required item(s) missing.${N} Install them, then run make doctor again."; fi
exit "$fail"
