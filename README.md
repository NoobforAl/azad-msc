# Master's Program — Islamic Azad University

Self-study workspace for a 4-term master's degree. Each course folder has an `agent-prompt.md` that builds the full course (lessons, labs, quizzes, videos, slide decks).

## Quick start

```bash
make doctor   # checks your machine and tells you what to install (no Node.js needed)
make view     # caches what the decks need, starts the lab VM, opens the slides
make stop     # stops the slide server and the VM
make clean    # stops everything, removes generated files, asks before deleting .cache/
make help     # all commands: decks, lab VM, kernel-source quotes, checks
```

Works from PowerShell, cmd or Git Bash on Windows, and on Linux and macOS. Full guide: [USAGE.md](USAGE.md) · فارسی: [USAGE.fa.md](USAGE.fa.md)

```
Colleage/
├── _shared/
│   ├── slide-design-system.md   # v3: one design system for every deck, all terms
│   ├── brand/                   # Azad emblem (azad-logo.png / .svg) + provenance README
│   ├── theme/                   # azad-theme.css + azad-deck.js (look, animations, toolbar)
│   ├── browser-lab/             # a real 32-bit Linux kernel in the browser + 10 mini-labs (make browser-lab)
│   ├── tools/                   # serve.py (deck index), export_deck.py (PDF / PPTX), qemu_vm.py, labdeck.py, …
│   └── sources/                 # git submodules, depth 1 + sparse
│       ├── linux/               #   Linux v6.18.63 (longterm)
│       └── openbsd/             #   OpenBSD src @ 8cada8c
├── term-1/
│   ├── advanced-network-security/      agent-prompt.md
│   ├── advanced-operating-systems/     agent-prompt.md
│   └── advanced-software-engineering/  agent-prompt.md
├── term-2/   # courses TBD
├── term-3/   # courses TBD
└── term-4/   # courses / thesis TBD
```

## How to use

0. After cloning this repo: `bash _shared/sources/setup-sources.sh` (shallow + sparse submodules).
1. Open a course folder and give its `agent-prompt.md` to the agent, together with `_shared/slide-design-system.md`.
2. All notes come in two versions: `*.en.md` (English, written first) and `*.fa.md` (Farsi). Each module also gets a `notes/` folder with 6–12 detailed notes.
3. The agent writes `PLAN.md` first. Review it, then let it build the modules one at a time.
4. Every lesson and every lab gets its own slide deck (`slides/*.en.html` + `*.fa.html`), built with the design system and quoting real Linux/OpenBSD code.

## Adding a new course (term 2–4)

1. Create `term-N/<course-name-kebab-case>/`.
2. Copy the closest existing `agent-prompt.md` and adapt ROLE, SCOPE, and the labs.
3. Add the course's 4 semantic roles to section 5.1 of `_shared/slide-design-system.md`.

## License

[MIT](LICENSE) for everything in this repo. The `_shared/sources/` submodules keep their own licenses (Linux: GPL-2.0, OpenBSD: ISC/BSD).
