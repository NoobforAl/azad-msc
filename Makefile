# Azad MSc workspace: one entry point for slides, sources, the lab VM, and checks.
# Start with:  make doctor     (checks your machine and says what to install)
# Then:        make view       (downloads what the decks need, starts the lab VM, opens the slides)
# Everything:  make help
#
# Works on Linux, macOS and Windows (from PowerShell, cmd or Git Bash). No Node.js needed.

SHELL       := bash
# Windows outside Git Bash: use Git for Windows' bash explicitly. A plain "bash" there may be
# WSL's C:\Windows\System32\bash.exe, which cannot see this folder's Windows tools.
ifeq ($(OS),Windows_NT)
ifndef MSYSTEM
GIT_BASH := $(firstword $(wildcard C:/PROGRA~1/Git/bin/bash.exe C:/PROGRA~2/Git/bin/bash.exe \
              $(subst \,/,$(USERPROFILE))/scoop/apps/git/current/bin/bash.exe \
              $(subst \,/,$(LOCALAPPDATA))/Programs/Git/bin/bash.exe))
ifeq ($(GIT_BASH),)
$(error Git Bash not found. Install Git for Windows (winget install Git.Git), then run make again)
endif
SHELL := $(GIT_BASH)
endif
endif
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
MAKEFLAGS   += --no-print-directory

# ---- settings (override on the command line: make slides PORT=8080) ----------
PORT    ?= 8000
COURSE  ?= term-1/advanced-operating-systems
M       ?= 01
L       ?= en
LAB     ?=
ALL     ?=
OUT     ?=
VM      ?= aos-lab
VM_USER ?= fred
VM_PORT ?= 2222
SNAP    ?= fresh
KERNEL  ?= mainline

PY  := $(shell for c in python3 python py; do $$c -c 'import sys' >/dev/null 2>&1 && { echo $$c; break; }; done)
VBM := $(shell command -v VBoxManage 2>/dev/null || { [ -x "/c/Program Files/Oracle/VirtualBox/VBoxManage.exe" ] && echo "/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"; } || true)
UNAME := $(shell uname -s)
SSH_OPTS := -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR
SETUP := $(COURSE)/00-setup/labs/01-create-vm
# A server stopped by `make stop` (15/143) or Ctrl+C (130) is a normal end, not an error.
SERVE_OK = case $$rc in 0|15|130|143) ;; *) exit $$rc ;; esac

.PHONY: help doctor view stop assets cache slides deck browser-lab qemu-vm site security fix lint pdf pptx list decks sources cite check clean clean-cache vm-up vm-down \
        vm-create vm-start vm-stop vm-status vm-ssh vm-snapshot vm-restore

help: ## Show this help
	@echo "Usage: make <target> [VAR=value]"
	@echo
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "} {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Variables: PORT=$(PORT) COURSE=$(COURSE) M=$(M) L=$(L) LAB=$(LAB) VM=$(VM)"
	@echo "Examples:  make deck M=04 L=fa      make deck M=02 LAB=03      make cite F=kernel/fork.c S=kernel_clone"

need-py:
	@[ -n "$(PY)" ] || { echo "Python 3 not found. Run: make doctor"; exit 1; }

# ---- setup -------------------------------------------------------------------
doctor: ## Check this machine: tools, sources, VM; prints what to install
	@bash _shared/tools/doctor.sh

sources: ## Fetch the Linux + OpenBSD reference sources (shallow, sparse; ~1 GB)
	@bash _shared/sources/setup-sources.sh

# ---- slides ------------------------------------------------------------------
view: need-py ## One command: cache slide assets, start the lab VM if it exists, open the slides
	@$(PY) _shared/tools/fetch_assets.py || echo "  (continuing online: decks will load reveal.js from the CDN)"
	@$(MAKE) vm-up || true
	@rc=0; $(PY) _shared/tools/serve.py --port $(PORT) $(if $(NOBROWSER),--no-browser) || rc=$$?; $(SERVE_OK)

stop: need-py ## Stop everything make started: slide servers and the lab VM
	@$(PY) _shared/tools/serve.py --stop
	@$(MAKE) vm-down

assets: need-py ## Download reveal.js + fonts into .cache/vendor so slides work offline (~0.6 MB)
	@$(PY) _shared/tools/fetch_assets.py $(if $(FORCE),--force)

cache: need-py ## Pre-download everything (slide assets + VM image + 6.18.63 kernel, ~0.8 GB) into .cache
	@$(PY) _shared/tools/fetch_assets.py --vm

slides: need-py ## Serve the repo and open an index of all decks (Ctrl+C to stop)
	@rc=0; $(PY) _shared/tools/serve.py --port $(PORT) $(if $(NOBROWSER),--no-browser) || rc=$$?; $(SERVE_OK)

deck: need-py ## Open one deck: M=<module no.> [L=en|fa] [LAB=<lab no.>]
	@d=$$(ls -d $(COURSE)/$(M)-*/slides 2>/dev/null | head -1); \
	[ -n "$$d" ] || { echo "no module $(M) in $(COURSE) (try: make list)"; exit 1; }; \
	if [ -n "$(LAB)" ]; then f=$$(ls $$d/labs/$(LAB)-*.$(L).html 2>/dev/null | head -1); \
	else f=$$d/lesson.$(L).html; fi; \
	[ -f "$$f" ] || { echo "deck not found: $$f (try: make list)"; exit 1; }; \
	rc=0; $(PY) _shared/tools/serve.py --port $(PORT) --open "$$f" $(if $(NOBROWSER),--no-browser) || rc=$$?; $(SERVE_OK)

qemu-vm: need-py ## No VirtualBox/Docker? Lab VM with plain QEMU: CMD=create|start|stop|status|ssh|snapshot|restore
	@$(PY) _shared/tools/qemu_vm.py $(or $(CMD),status) $(if $(DRY),--dry-run)

site: need-py ## Build the static website (Home > Term > Course > slides) into site/ for GitHub Pages
	@$(PY) _shared/tools/build_site.py

fix: need-py ## Lint + format the codebase: fixes Python (ruff), whitespace and line endings, then reports what is left
	@$(PY) _shared/tools/fix.py

lint: need-py ## Same checks as 'make fix' but changes nothing (exit code = number of problems; used in CI)
	@$(PY) _shared/tools/fix.py --check

security: need-py ## Scan the repo (and site/ if built) for secrets and private data: run before every push
	@$(PY) _shared/tools/security_scan.py $(if $(wildcard site),--site site)

browser-lab: need-py ## No VM? A real 32-bit Linux kernel + mini-labs in your browser (downloads ~13 MB once)
	@$(PY) _shared/tools/fetch_browser_lab.py
	@rc=0; $(PY) _shared/tools/serve.py --port $(PORT) --open _shared/browser-lab/index.html $(if $(NOBROWSER),--no-browser) || rc=$$?; $(SERVE_OK)

# Export decks with _shared/tools/export_deck.py (it resolves M / LAB / L / ALL itself)
EXPORT = $(PY) _shared/tools/export_deck.py --course "$(COURSE)" --module "$(M)" --lang $(L) $(if $(LAB),--lab "$(LAB)") $(if $(ALL),--all) $(if $(OUT),--out "$(OUT)")

pdf: need-py ## Export a deck to PDF in exports/: M=<module> [L=en|fa] [LAB=<n>] [ALL=1] [OUT=<dir>]
	@$(EXPORT) --format pdf

pptx: need-py ## Export a deck to PowerPoint (pictures + notes + transitions); same options as pdf
	@$(EXPORT) --format pptx

list: ## List modules, notes, labs and decks of COURSE
	@for m in $(COURSE)/[0-9][0-9]-*/; do \
	  n=$$(ls $$m/notes/*.en.md 2>/dev/null | grep -vc INDEX || true); \
	  l=$$(ls -d $$m/labs/*/ 2>/dev/null | wc -l); \
	  printf "  %-34s notes %2s  labs %s  " "$$(basename $$m)" "$$n" "$$l"; \
	  ls $$m/labs 2>/dev/null | grep -E '^[0-9]' | tr '\n' ' '; echo; done

decks: need-py ## Re-render all lab decks from slides/labs.content.py (after editing content)
	@for c in $(COURSE)/*/slides/labs.content.py; do $(PY) _shared/tools/labdeck.py "$$c" >/dev/null && echo "rendered $$c"; done

# ---- reading code ------------------------------------------------------------
cite: ## Print a quoted excerpt: F=<path> S=<symbol|L123> [R=linux|openbsd]
	@[ -n "$(F)" ] && [ -n "$(S)" ] || { echo "usage: make cite F=kernel/fork.c S=kernel_clone [R=linux]"; exit 1; }
	@bash _shared/sources/cite.sh $(or $(R),linux) $(F) $(S)

# ---- lab VM (VirtualBox on Windows/macOS, libvirt on Linux) ------------------
vm-create: ## Create the lab VM in .cache/vm (Ubuntu 24.04 + Linux 6.18.63; downloads cached)
ifneq ($(VBM),)
	@command -v pwsh >/dev/null || { echo "needs PowerShell 7: winget install Microsoft.PowerShell"; exit 1; }
	@VM=$(VM) SSH_PORT=$(VM_PORT) KERNEL=$(KERNEL) pwsh -NoProfile -File $(SETUP)/create-vm-virtualbox.ps1
else
	@VM=$(VM) bash $(SETUP)/create-vm.sh
endif

vm-up: # start the VM if it exists and is not running (used by make view; never fails)
ifneq ($(VBM),)
	@st=$$({ "$(VBM)" showvminfo $(VM) --machinereadable 2>/dev/null || true; } | sed -n 's/^VMState="\(.*\)"/\1/p'); \
	case "$$st" in \
	  "") echo "lab VM: '$(VM)' not created yet (one-time: make vm-create). Slides work without it." ;; \
	  running) echo "lab VM: $(VM) already running (make vm-ssh)" ;; \
	  *) "$(VBM)" startvm $(VM) --type headless >/dev/null && echo "lab VM: $(VM) starting, ready in ~30 s (make vm-ssh; make vm-stop when done)" ;; \
	esac
else
	@if ! command -v virsh >/dev/null; then echo "lab VM: no VirtualBox or libvirt (make doctor). Slides work without it."; \
	elif ! virsh dominfo $(VM) >/dev/null 2>&1; then echo "lab VM: '$(VM)' not created yet (make vm-create)"; \
	elif virsh domstate $(VM) | grep -q running; then echo "lab VM: $(VM) already running"; \
	else virsh start $(VM) >/dev/null && echo "lab VM: $(VM) starting (make vm-ssh)"; fi
endif

vm-down: # shut the VM down if it is running; waits up to 90 s, then forces power-off (used by stop/clean)
ifneq ($(VBM),)
	@st=$$({ "$(VBM)" showvminfo $(VM) --machinereadable 2>/dev/null || true; } | sed -n 's/^VMState="\(.*\)"/\1/p'); \
	if [ "$$st" != running ]; then echo "lab VM: not running"; exit 0; fi; \
	"$(VBM)" controlvm $(VM) acpipowerbutton; printf "lab VM: shutting down"; \
	for i in $$(seq 45); do sleep 2; printf .; \
	  "$(VBM)" showvminfo $(VM) --machinereadable | grep -q 'VMState="poweroff"' && { echo " off"; exit 0; }; done; \
	"$(VBM)" controlvm $(VM) poweroff >/dev/null 2>&1; echo " forced off"
else
	@if command -v virsh >/dev/null && virsh domstate $(VM) 2>/dev/null | grep -q running; then \
	  virsh shutdown $(VM); else echo "lab VM: not running"; fi
endif

vm-start: ## Start the VM headless
ifneq ($(VBM),)
	@"$(VBM)" startvm $(VM) --type headless
else
	@virsh start $(VM)
endif

vm-stop: ## Shut the VM down cleanly
ifneq ($(VBM),)
	@"$(VBM)" controlvm $(VM) acpipowerbutton && echo "shutdown sent to $(VM)"
else
	@virsh shutdown $(VM)
endif

vm-status: ## Show VM state and kernel version
ifneq ($(VBM),)
	@"$(VBM)" showvminfo $(VM) --machinereadable | sed -n 's/^VMState="\(.*\)"/state: \1/p'
	@ssh $(SSH_OPTS) -o ConnectTimeout=5 -p $(VM_PORT) $(VM_USER)@127.0.0.1 'echo "kernel: $$(uname -r)"; uptime' 2>/dev/null || echo "ssh: not reachable (VM off or booting)"
else
	@virsh domstate $(VM); virsh domifaddr $(VM) || true
endif

vm-ssh: ## Open a shell in the VM
ifneq ($(VBM),)
	@ssh $(SSH_OPTS) -p $(VM_PORT) $(VM_USER)@127.0.0.1
else
	@ip=$$(virsh domifaddr $(VM) | awk '/ipv4/{split($$4,a,"/"); print a[1]; exit}'); ssh $(SSH_OPTS) $$USER@$$ip
endif

vm-snapshot: ## Take a snapshot (VM must be off): SNAP=<name>
ifneq ($(VBM),)
	@"$(VBM)" snapshot $(VM) take $(SNAP)
else
	@virsh snapshot-create-as $(VM) $(SNAP)
endif

vm-restore: ## Roll back to a snapshot (VM must be off): SNAP=<name>
ifneq ($(VBM),)
	@"$(VBM)" snapshot $(VM) restore $(SNAP)
else
	@virsh snapshot-revert $(VM) $(SNAP)
endif

# ---- maintenance -------------------------------------------------------------
check: need-py ## Check decks (notes, titles, paths), Python tools and shell scripts
	@$(PY) _shared/tools/check_decks.py
	@$(PY) -m py_compile _shared/tools/*.py $(COURSE)/*/slides/labs.content.py && echo "python: ok"
	@if command -v shellcheck >/dev/null; then \
	  git ls-files -co --exclude-standard -- '*.sh' | grep -v '^_shared/sources/[lo]' | xargs shellcheck -S warning && echo "shellcheck: ok"; \
	 else echo "shellcheck: skipped (not installed)"; fi

clean: ## Stop everything, remove generated files, then ASK about the cache (or CACHE=keep|downloads|all)
	@$(MAKE) stop
	@find . -path ./_shared/sources -prune -o -path ./.cache -prune -o \( -name __pycache__ -o -name '*.pyc' \) -print | xargs rm -rf
	@rm -rf tags .tags cscope.* _shared/sources/tags _shared/sources/cscope.* .cache/run
	@echo "removed generated files (pycache, tags, cscope, server pid files)"
	@$(MAKE) clean-cache

clean-cache: # ask what to delete from .cache; CACHE=keep|downloads|all skips the question
	@dl=$$(du -sh .cache/downloads .cache/vendor 2>/dev/null | awk '{print $$1}' | paste -sd+ - || true); \
	vm=$$(du -sh .cache/vm 2>/dev/null | cut -f1 || true); \
	ans="$(CACHE)"; \
	if [ -z "$$ans" ] && [ ! -d .cache/downloads ] && [ ! -d .cache/vendor ] && [ ! -d .cache/vm ]; then echo "cache: empty"; exit 0; fi; \
	if [ -z "$$ans" ]; then \
	  echo "The cache in .cache/ saves downloads for next time:"; \
	  echo "  downloads + slide assets: $${dl:-0}  (Ubuntu image, 6.18.63 kernel, reveal.js, fonts)"; \
	  echo "  lab VM:                   $${vm:-none}  ($(VM), with its snapshots and your ~/work)"; \
	  echo "  [k] keep everything (default)"; \
	  echo "  [d] delete downloads + slide assets (re-downloaded when needed)"; \
	  echo "  [a] delete ALL, including the lab VM (make vm-create rebuilds it)"; \
	  if [ -t 0 ]; then read -r -p "Your choice [k/d/a]: " ans || ans=k; else echo "(no terminal: keeping; pass CACHE=keep|downloads|all)"; ans=k; fi; \
	fi; \
	case "$$ans" in \
	  d|D|downloads) rm -rf .cache/vendor .cache/downloads; echo "cache: deleted downloads and slide assets; VM kept" ;; \
	  a|A|all) \
	    if [ -n "$(VBM)" ] && "$(VBM)" list vms | grep -q '"$(VM)"'; then "$(VBM)" unregistervm $(VM) --delete && echo "deleted VM $(VM)"; \
	    elif command -v virsh >/dev/null && virsh dominfo $(VM) >/dev/null 2>&1; then virsh undefine $(VM) --remove-all-storage --snapshots-metadata; fi; \
	    rm -rf .cache; echo "cache: deleted everything in .cache" ;; \
	  *) echo "cache: kept" ;; \
	esac
