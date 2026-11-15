# Using this workspace with `make`

You don't need to know what to install: run `make doctor` and it tells you.

```bash
make doctor     # 1. check your machine; it prints what is missing and how to install it
make view       # 2. download what the decks need, start the lab VM, open the slides in your browser
make stop       # 3. when done: stop the slide server and shut the VM down
```

Labs: `make vm-create` once (builds the VM, ~10 min), then `make vm-ssh`. `make clean` stops everything and **asks** before deleting the cache. `make help` lists every command.

**Windows:** run these from PowerShell, cmd or Git Bash. The Makefile uses Git for Windows' bash internally, so Git must be installed (`make doctor` checks it). Farsi version: [USAGE.fa.md](USAGE.fa.md).

---

## 1. What you need

`make doctor` checks all of this. It installs nothing, and its exit code is the number of required items that are missing.

| Needed for | Tool | Notes |
|---|---|---|
| everything | `git`, `make`, Python ≥ 3.8 | On Windows, Git for Windows provides the bash that `make` uses |
| slides | any modern browser + internet | reveal.js and the fonts load from a CDN |
| reading kernel code | the Linux / OpenBSD source checkouts | `make sources` (~1 GB, shallow + sparse) |
| labs | VirtualBox (Windows/macOS) or libvirt + KVM (Linux), an SSH client and an SSH key | `make vm-create` builds the VM |
| VM on Windows | PowerShell 7 (`winget install Microsoft.PowerShell`), Docker or WSL | Docker or WSL is used once, to build the VM's small setup ISO |
| optional | `shellcheck`, `ctags` | used by `make check` and code navigation |

**Not needed:** Node.js, npm, any build step. The decks are plain HTML files. `make view` downloads the few files they use (reveal.js and three web fonts, ~0.6 MB) into `.cache/`, so after the first run the slides work offline.

### The cache (`.cache/`, git-ignored)

| Folder | What | Size | Filled by |
|---|---|---|---|
| `.cache/vendor/` | reveal.js 5.1.0 + fonts for offline slides | ~0.6 MB | `make view`, `make assets` |
| `.cache/downloads/` | Ubuntu 24.04 cloud image, Linux 6.18.63 kernel `.deb`s, VM setup ISO | ~0.8 GB | `make cache`, `make vm-create` |
| `.cache/vm/` | the lab VM itself (disk, snapshots) | ~8 GB | `make vm-create` |
| `.cache/run/` | process IDs of running slide servers | tiny | `make view`/`slides`, removed by `make stop` |

Nothing is downloaded twice: a second `make vm-create` reuses the image and the kernel files. `make clean` asks what to remove: **k**eep everything, delete **d**ownloads only, or delete **a**ll including the VM. To skip the question, pass `CACHE=keep`, `CACHE=downloads` or `CACHE=all`.

### Installing `make` on Windows
Pick one, then reopen Git Bash:
```powershell
scoop install make          # https://scoop.sh
choco install make          # https://chocolatey.org
winget install ezwinports.make
```

---

## 2. Slides

| Command | What it does |
|---|---|
| `make view` | All-in-one: cache the slide files, start the lab VM if it exists, serve and open the deck index |
| `make stop` | Stop every slide server and shut the VM down (from any terminal) |
| `make slides` | Serves the repo on `http://127.0.0.1:8000/` and opens an index of all decks. Ctrl+C stops it. |
| `make deck M=04` | Opens the Module 04 lesson deck (English) |
| `make deck M=04 L=fa` | The same deck in Farsi |
| `make deck M=02 LAB=03` | The deck for Module 02, lab 03 |
| `make slides PORT=8080` | Uses another port if 8000 is taken |
| `make view NOBROWSER=1` | Same, without opening a browser (for a remote or headless machine) |
| `make list` | Lists modules, notes and labs |
| `make browser-lab` | No VM? Opens the browser lab: a real 32-bit Linux kernel in your browser with 10 mini-labs (downloads ~13 MB once) |
| `make pdf M=04` | Exports the Module 04 lesson to `exports/*.pdf` (one vector page per slide, animations in their final state) |
| `make pptx M=04` | Exports it to PowerPoint `exports/*.pptx`: a picture per slide, speaker notes, slide transitions |
| `make pdf M=02 ALL=1 L=fa` | Every deck of Module 02 (lesson + all labs) in Farsi. Options: `M` `L` `LAB` `ALL=1` `OUT=<dir>` |

On the deck index, pick **English** or **فارسی** once at the top: the whole page switches language (text, direction, module and lab names) and every deck opens in it. Your choice is remembered in the browser.

Inside a deck:
- **S** opens the speaker notes.
- **F** goes fullscreen.
- **Esc** shows the slide overview.
- **A** turns animations on or off. **T** shows the toolbar (also appears when you hover the bottom-right corner): transition style, animation speed, fullscreen, **Export PDF**.
- Slide transitions: `fade` (default), `slide`, `convex`, `concave`, `zoom`, `none`. Pick one in the toolbar, or add `?transition=slide` to the URL.
- Add your own animations with the classes in [`_shared/slide-design-system.md`](_shared/slide-design-system.md) section 12.1 (`fragment anim-up`, `loop-pulse`, `data-auto-animate`, …).

### No VM, no VirtualBox, no Docker?

Best to worst: **a VM** runs every lab; **Docker** is enough for the user-space labs only (a container shares the host kernel); the **browser lab** shows the ideas only. You can use plain **QEMU** instead of VirtualBox (no Docker or WSL needed): `make qemu-vm CMD=create`, then `CMD=start|stop|status|ssh|snapshot|restore` (add `DRY=1` to preview). For the browser lab you must **clone this repository and run it locally**: `git clone <repository-url>`, `cd` into the folder, `make browser-lab`. It cannot be opened as a plain file. Details and limits: [`_shared/browser-lab/README.md`](_shared/browser-lab/README.md).

### Publish the website (GitHub Pages)

The whole workspace can be a website: **Home → Term 1 → Advanced OS → a lesson or lab**, English and Persian, mobile-friendly, with no third-party requests. `make site` builds it into `site/` (check it first with `make security`).

1. The repository must be **public** (private repositories need a paid GitHub plan for Pages).
2. Push to `main`. The workflow `.github/workflows/pages.yml` scans for secrets, builds the site and publishes it.
3. One time: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. The site appears at `https://<owner>.github.io/<repository>/` (for `NoobforAl/azad-msc`: `https://noobforal.github.io/azad-msc/`).
5. Your own subdomain (for example `os.example.com`): add a **CNAME** DNS record pointing to `<owner>.github.io`, then set it under **Settings → Pages → Custom domain** and tick *Enforce HTTPS*. (A `CNAME` file in the repository is ignored by Actions deployments.)

The published pages leave out the **speaker notes** and the unfilled `[Presenter]`-style title fields (your local decks keep them; `python _shared/tools/build_site.py --keep-notes` publishes the notes too). Every page says it is unofficial study material. Run `make fix` and `make security` before you push. The browser lab and the VM tools are not part of the website (they need a local run). More on safety: [`SECURITY.md`](SECURITY.md).

### Further reading

The last slide of every lesson ("Go deeper") and [`term-1/advanced-operating-systems/RESOURCES.en.md`](term-1/advanced-operating-systems/RESOURCES.en.md) list books, papers and tools picked from the GitHub *awesome-os* lists, with every link checked. To change them, edit `_shared/resources/awesome-os.json`, then run `python _shared/tools/add_references.py` (`--check` re-tests the links before a presentation).

### Exporting to PDF or PowerPoint

`make pdf M=04` and `make pptx M=04` need **Edge, Chrome or Chromium** (`make doctor` shows which it found). PowerPoint also needs `pip install python-pptx`. Files land in `exports/` (git-ignored); a 20-slide deck takes about 30 s.

- **PDF** keeps text selectable and shows each slide in its finished state (all click steps visible).
- **PPTX** slides are *pictures* of the deck, so they look identical but the text is not editable, and click-by-click builds become one finished slide. The speaker notes are copied into PowerPoint's notes and each slide has a fade transition (`--transition push|wipe|none` on the Python tool to change it). To change content, edit the HTML deck and export again.
- No terminal handy? Use the **Export PDF** button in the deck toolbar: it opens the print dialog (choose *Save as PDF*, margins *None*, background graphics *on*).

Why a server? Opening the `.html` file directly (`file://`) breaks the shared theme path, so always use `make slides` or `make deck`.

### Editing slides
- **Lesson decks** (`NN-*/slides/lesson.en.html` and `.fa.html`) are hand-written HTML. Edit them directly and reload the browser.
- **Lab decks** are generated. Edit `NN-*/slides/labs.content.py` (English and Farsi side by side), then run `make decks`. Don't edit `slides/labs/*.html` by hand; `make decks` overwrites them.
- Run `make check` after editing. It checks that every slide has speaker notes, a title and working theme paths, and runs shellcheck on the lab scripts.

---

## 3. The lab VM

Kernel-level labs run in a disposable VM, never on your own machine.

| Command | What it does |
|---|---|
| `make vm-create` | Builds `aos-lab` in `.cache/vm/`: Ubuntu 24.04, the lab tools, the course kernel 6.18.63 and a snapshot `fresh`. Windows/macOS use VirtualBox; Linux uses libvirt. About 10 minutes the first time; downloads are cached. With VirtualBox, `KERNEL=stock` keeps Ubuntu's 6.8 kernel; with libvirt, build 6.18.63 in lab 00.3. |
| `make vm-start` / `make vm-stop` | Boots the VM headless, or shuts it down cleanly |
| `make vm-status` | Shows the VM state and running kernel |
| `make vm-ssh` | Opens a shell in the VM. VirtualBox forwards SSH to `127.0.0.1:2222`, user `fred`. |
| `make vm-snapshot SNAP=before-lab4` | Takes a snapshot (VM must be off) |
| `make vm-restore SNAP=fresh` | Rolls back to a snapshot (VM must be off) |

- **Snapshot `fresh`:** the course's VM already has one. It holds Ubuntu 24.04, mainline Linux **6.18.63**, all lab tools and an empty `~/work`.
- **Lab files:** copy them in with `scp -P 2222 -r term-1/advanced-operating-systems/04-memory/labs fred@127.0.0.1:~/work/`.
- **Other names or users:** override them, for example `make vm-ssh VM=my-vm VM_USER=me VM_PORT=2223`.

**Limits of VirtualBox on a Windows host with Hyper-V active** (Docker Desktop and WSL turn Hyper-V on):
- no hardware performance counters (`perf stat -e cycles` shows `<not supported>`);
- no `/dev/kvm` inside the VM.

The lab READMEs say which labs are affected. Most labs work unchanged.

**One rule for tracing:** never enable the kernel's function tracer (ftrace) without a filter in the VM. Use `trace-cmd -g <fn> -l <fn>`, a depth limit and `timeout 10`, or the VM can soft-lock.

---

## 4. Reading kernel code

```bash
make sources                                       # once: fetch Linux v6.18.63 + OpenBSD 8cada8c
make cite F=kernel/fork.c S=kernel_clone           # print a cited excerpt
make cite F=sys/kern/kern_fork.c S=fork1 R=openbsd
make cite F=mm/memory.c S=L6490                    # by line number
```

The output starts with the citation line used throughout the notes, for example `linux/kernel/fork.c · kernel_clone() · v6.18.63 · L2578-2602`.

---

## 5. All commands

| Command | Purpose |
|---|---|
| `make help` | List commands and current settings |
| `make doctor` | Check this machine and print install hints |
| `make view` / `make stop` | Start slides + VM / stop everything |
| `make assets` / `make cache` | Pre-download slide files / everything (incl. VM image, kernel) |
| `make sources` | Fetch the reference source trees |
| `make slides` / `make deck` / `make list` | Browse decks |
| `make browser-lab` | Browser lab: a small real Linux kernel in your browser (no VM needed) |
| `make site` / `make security` | Build the static website into `site/` / scan for secrets and private data before a push |
| `make fix` / `make lint` | Format and lint the codebase (Python with ruff, whitespace and line endings, JS syntax, shellcheck, JSON). `fix` changes files, `lint` only reports (this is what CI runs) |
| `make qemu-vm CMD=…` | Lab VM with plain QEMU instead of VirtualBox (`create`, `start`, `stop`, `status`, `ssh`, `snapshot`, `restore`) |
| `make pdf` / `make pptx` | Export a deck to PDF / PowerPoint (`exports/`) |
| `make decks` | Re-render lab decks after editing `labs.content.py` |
| `make cite` | Quote kernel source with a citation |
| `make vm-create` / `vm-start` / `vm-stop` / `vm-status` / `vm-ssh` | Lab VM |
| `make vm-snapshot` / `vm-restore` | VM snapshots |
| `make check` | Check decks, Python tools and shell scripts |
| `make clean` | Stop everything, remove generated files, ask about `.cache` (`CACHE=keep\|downloads\|all`) |

Settings you can override: `NOBROWSER=1`, `CACHE=keep|downloads|all`, `PORT=8000`, `COURSE=term-1/advanced-operating-systems`, `M=01`, `L=en`, `LAB=`, `ALL=`, `OUT=`, `CMD=`, `DRY=`, `VM=aos-lab`, `VM_USER=fred`, `VM_PORT=2222`, `SNAP=fresh`.

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `make: command not found` | Install make (section 1) |
| `Git Bash not found` | Install Git for Windows: `winget install Git.Git` |
| `make view` says the VM is not created | Run `make vm-create` once; slides work without the VM |
| `cannot listen on 127.0.0.1:8000` | Another program uses the port: `make slides PORT=8080` |
| Deck shows unstyled text | No internet (CDN), or you opened it via `file://`. Use `make slides`. |
| Logo box says `[University logo]` | Put the official logo at `_shared/brand/azad-logo.svg` |
| `make vm-ssh` hangs or is refused | The VM is still booting. Wait 30 s; `make vm-status` shows its state |
| `perf stat -e cycles` shows `<not supported>` | Expected in VirtualBox on Hyper-V. Use software events (`task-clock`, `page-faults`) |
| `stress-ng --cpu` dies with SIGILL in the VM | Use `stress-ng --cpu N --cpu-method int64` |
| The VM is broken after a lab | `make vm-stop && make vm-restore SNAP=fresh && make vm-start` |
