# Lab 00.1 — Toolchain check

**Goal:** one script that prints the version of every tool the course needs and says which ones are missing or too old, so you find out now and not in the middle of module 06.

**Starting state:** no project state needed. You only need Python 3.8 or newer to run the script itself.
**Ending state:** nothing is committed; you leave with a table of green lines (or a list of things to install).

## Steps

Run from the root of the course repository (Git Bash on Windows, any shell on Linux and macOS):

```bash
cd term-1/advanced-software-engineering/00-setup/labs/01-toolchain-check
python check_tools.py          # use python3 if `python` is not on your PATH
echo "exit code: $?"           # number of problems with required tools; 0 is what you want
ruff check check_tools.py      # the script is itself lint-clean
```

Install what is missing (the tool list and why each tool is there is in [`../../guide.en.md`](../../guide.en.md), section 3):

| Tool | Windows | Linux / macOS |
|---|---|---|
| Go ≥ 1.22 | `winget install GoLang.Go` | your package manager, or https://go.dev/dl/ |
| Python ≥ 3.8 | `winget install Python.Python.3.12` | your package manager |
| ruff | `pip install ruff` | `pip install ruff` (or `pipx install ruff`) |
| git ≥ 2.28 | `winget install Git.Git` | your package manager |
| make (optional) | `scoop install make` or use WSL | preinstalled or `apt install make` / `xcode-select --install` |
| docker (optional) | Docker Desktop | Docker Engine |

The `winget` and `scoop` lines are the usual package names; they were **not** run on this machine (everything was already installed), so check the package id with `winget search` if one fails (**UNVERIFIED**).

## Code

[`check_tools.py`](check_tools.py) (standard library only, Python 3.8 compatible). Each tool is a row in the `TOOLS` table: executable, the arguments that print its version, the minimum, whether it is required. The comparison uses the first `X.Y` found in the output, so `go version go1.27.4 windows/amd64` is read as 1.27.4 and compared with the minimum 1.22.

```python
TOOLS = (
    Tool("go", "go", ("version",), (1, 22), True, "builds the registration-api service"),
    Tool("python", sys.executable, ("--version",), (3, 8), True, "analytics service and lab scripts"),
    Tool("ruff", "ruff", ("--version",), None, True, "Python lint gate used by make lint and CI"),
    Tool("git", "git", ("--version",), (2, 28), True, "git init -b needs 2.28; every lab commits"),
    # ... make, docker, node and java are optional
)
```

Status values: `OK`, `OLD` (found but below the minimum), `MISSING` (not on `PATH`), `BROKEN` (found but printed no version). The exit code counts only **required** tools; `--strict` counts the optional ones too.

## Expected output

Captured on Windows 11 with Git Bash on 2026-11-23 (Python 3.12.14 ran the script). Exit code 0:

```text
$ python check_tools.py
tool     need      found    kind      status   note
go       >= 1.22   1.27.4   required  OK       builds the registration-api service
python   >= 3.8    3.12.14  required  OK       analytics service and lab scripts
ruff     any       0.17.6   required  OK       Python lint gate used by make lint and CI
git      >= 2.28   2.56.1   required  OK       git init -b needs 2.28; every lab commits
make     any       4.4.1    optional  OK       make check; without it run the commands by hand
docker   any       29.9.3   optional  OK       daemon reachable
node     any       26.13.1  optional  OK       npx mermaid-cli in lab 03
java     any       25.0.5   optional  OK       PlantUML jar in lab 03 (alternative to Docker)

all required tools present
```

The same run with `go` hidden from `PATH` (real run; exit code 1):

```text
go       >= 1.22   -        required  MISSING  not on PATH
...
PROBLEMS: go
```

Your versions will be different; the shape of the table should not. On Linux and macOS the script is identical. `docker` may show `daemon NOT reachable` when Docker is installed but not started; that is a warning for the optional labs, not an error.

## What to observe

- The check says "OK" for Python even though it is the interpreter running the script: `sys.executable` is what you will actually use, which is not always the `python` on your `PATH` (virtual environments).
- `ruff` has no minimum here, but versions differ in what a bare `ruff check` enforces: on ruff 0.17.6 it flags more than the course's `ruff.toml` does (lab 02 shows the exact error). That is why lab 02 puts the rules in a `ruff.toml` inside the project.
- A tool that is "installed but the daemon is down" (Docker) is a different failure from "not installed". Good tooling reports them differently.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `python: command not found` on Linux/macOS | only `python3` exists | run `python3 check_tools.py` |
| `MISSING` for a tool you just installed | the shell started before the install | open a new terminal |
| Windows opens the Microsoft Store when you type `python3` | the Store stub shadows Python | use `python` or `py -3`, or turn off the app execution alias |
| `OLD` for Go | an old distribution package | install from https://go.dev/dl/ |

## Extension task

Make the check machine-readable: write a second script that prints one JSON document (tool, required, minimum, found, status, note), keeps the exit-code rule, and can be saved by CI as a build artifact. Do not copy the version-parsing code; import it from `check_tools.py`.

Solution: [`solution/check_tools_json.py`](solution/check_tools_json.py). The reference table is in [`solution/expected-output.txt`](solution/expected-output.txt).
