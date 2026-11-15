# Browser lab: a real Linux kernel in your browser

A small, simplified lab for people who **cannot run the course VM**. It boots a real **32-bit Linux 6.8.12** kernel inside
your browser tab (the [v86](https://github.com/copy/v86) x86 emulator) and walks you through 10 guided mini-labs on
processes, interrupts, scheduling, signals, memory, files and a real race condition. Persian version: the page has an
**English / فارسی** switch.

## Prefer a VM or Docker when you can

| You have | Use | Covers |
|---|---|---|
| VirtualBox, KVM or QEMU | **The course VM** (`make vm-create`, or `make qemu-vm CMD=create` for plain QEMU) | **Every lab**: x86-64 Linux v6.18.63, `strace`, `perf`, `ftrace`, `bpftrace`, kernel modules |
| Docker only | A container for the **user-space labs** (C programs, `strace`, threads, pipes) | Not the kernel-level labs: a container shares the host's kernel |
| Nothing else | **This browser lab** | Concepts only, see "What it can and cannot do" |

The browser lab is the last resort. It is for *seeing* the ideas, not for replacing the real labs.

## How to run it: clone the repository and run it

The lab needs a local web server and about 13 MB of files that are **not stored in git**, so it does not work as a
plain file or from a website. You need **Python 3** and a modern browser (Chrome, Edge or Firefox).

```bash
git clone <repository-url>
cd <repository-folder>
make browser-lab          # downloads ~13 MB once, starts a local server, opens the page
```

No `make`? Run the two steps by hand:

```bash
python _shared/tools/fetch_browser_lab.py
python _shared/tools/serve.py --open _shared/browser-lab/index.html
```

(If port 8000 is taken, add `--port 8765`; with make: `make browser-lab PORT=8765`.)
Then click **Start the virtual machine**, wait about 5–15 seconds for the prompt, and press **Run** on each step.

When you finish a lab, a green **Lab complete** box appears with a **Next lab →** button. After the last lab it points
you back to the slides and to the real VM.

## What it can and cannot do

- **Can:** boot a real kernel; read `/proc` (processes, memory, interrupts, kernel symbols); `nice`, `chrt`, signals,
  pipes, `flock`, `tmpfs`, `dd`, `ps`, `top`; watch a real race condition lose updates.
- **Cannot:** it is **32-bit only**, with 100 MB of RAM on an emulated Pentium III. There is **no compiler, `strace`,
  `perf`, `ftrace` or `bpftrace`**, no kernel modules, and no network. The course's real labs need an **x86-64 Linux
  v6.18.63** machine (see `term-1/advanced-operating-systems/00-setup/guide.en.md`).
- The kernel links on each lab point to the course's pinned source (v6.18.63); the guest runs 6.8.12, so line-level
  details can differ slightly.
- Everything runs inside your browser tab. Nothing is uploaded. Closing the tab resets the machine.

## The mini-labs

| # | Lab | Course module |
|---|---|---|
| 1 | Meet the kernel (`uname`, `kallsyms`, `dmesg`) | 01 Architecture |
| 2 | Interrupts (`/proc/interrupts`, timer ticks) | 01 Architecture |
| 3 | Processes, fork and pipes | 02 Processes & Threads |
| 4 | Scheduling and `nice` | 02 Processes & Threads |
| 5 | Context switches | 02 Processes & Threads |
| 6 | Signals | 02 Processes & Threads |
| 7 | Virtual memory (`maps`, `meminfo`) | 04 Memory |
| 8 | Files are pages (tmpfs) | 04 Memory |
| 9 | Files, inodes and descriptors | 05 File systems & I/O |
| 10 | A real race condition (`flock`) | 03 Concurrency |

Each lab has the commands (one **Run** button per step), a short explanation, a question with a hidden answer, links
to the real kernel source, and which course lab it is a lite version of. Each step also checks that the output is what
was expected and marks itself ✓ when it is.

## Files

| File | Purpose |
|---|---|
| `index.html`, `lab.css`, `lab.js` | The page (no build step, no framework) |
| `labs.mjs` | All lab content, in English and Persian. Edit this to change or add labs |
| `../tools/fetch_browser_lab.py` | Downloads the runtime, pinned by SHA-256, into `.cache/vendor/browser-lab/` (git-ignored) |

## What is downloaded, and licences

| Part | Version | Licence |
|---|---|---|
| [v86](https://github.com/copy/v86) emulator (`libv86.js`, `v86.wasm`, BIOS files) | 0.5.473 | BSD-2-Clause |
| Linux 6.8.12 + busybox image (`buildroot-bzimage68.bin`), built by the v86 author, from `i.copy.sh` | 6.8.12 | GPL (Linux, busybox) |
| [xterm.js](https://github.com/xtermjs/xterm.js) terminal | 5.5.0 | MIT |

Nothing here is committed to this repository; it lives in `.cache/` on the machine that runs the lab. If a download's
checksum ever differs, the tool stops and does not use the file.

## How it was tested

Every step of all 10 labs was run in a real browser (Edge) and headlessly against the real guest, and each one produced
the output its `expect` pattern requires. The page itself was exercised by clicking Start and Run, completing a lab, the
**Next lab** button, and the Persian layout. If you change `labs.mjs`, the page will show a step as "unexpected output"
if its `expect` no longer matches, which is how you notice a mistake.
