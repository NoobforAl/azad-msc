"""Lint and format the codebase. One command for everything:

  make fix                          # fix what can be fixed, then report what is left
  make lint                         # check only: change nothing, exit code = number of problems (used in CI)

What it does (each step is skipped with a hint if its tool is missing):
  1. Python    ruff check --fix  +  ruff format        (settings: ruff.toml; install: pip install ruff)
  2. Text      strips trailing spaces, ends every file with one newline, keeps each file's own line endings
               (shell scripts and the Makefile are forced to LF, as .gitattributes requires); Markdown keeps
               its trailing spaces because two of them mean a line break
  3. JavaScript  `node --check` (syntax)                (no formatter is run: Node is optional here)
  4. Shell     shellcheck -S warning
  5. JSON      every .json file must parse

It never touches: the kernel/OpenBSD submodules, generated slide decks (rebuild those with `make decks`), the built
site, caches, binaries and images.
"""

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEXT_SUFFIX = {".py", ".js", ".mjs", ".css", ".sh", ".ps1", ".yml", ".yaml", ".toml", ".json", ".md", ".txt"}
TEXT_NAMES = {"Makefile", ".gitignore", ".gitattributes", ".gitmodules"}
GENERATED = re.compile(r"(^|/)slides/(labs/)?[^/]+\.html$")  # decks: rebuilt by make decks / labdeck.py
SKIP_PREFIX = ("_shared/sources/", ".cache/", "site/", "exports/", "node_modules/")


def project_files():
    out = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True, cwd=ROOT
    ).stdout.splitlines()
    return [f for f in out if not f.startswith(SKIP_PREFIX) and not GENERATED.search(f) and (ROOT / f).is_file()]


def run(cmd, show=True):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if show and (r.stdout.strip() or r.stderr.strip()):
        print("   " + (r.stdout + r.stderr).strip().replace("\n", "\n   "))
    return r


# ---------------------------------------------------------------- 1. Python
def python_step(check):
    if not shutil.which("ruff"):
        print("python: SKIPPED (ruff is not installed: pip install ruff)")
        return 0
    problems = 0
    if check:
        lint = run(["ruff", "check", "--output-format", "concise"])
        fmt = run(["ruff", "format", "--check"], show=False)
        unformatted = [ln for ln in fmt.stdout.splitlines() if ln.startswith("Would reformat")]
        for ln in unformatted:
            print("   " + ln)
        problems = (lint.returncode != 0) + len(unformatted)
        print(f"python: {'clean' if not problems else 'problems found (run: make fix)'}")
    else:
        fixed = run(["ruff", "check", "--fix", "--output-format", "concise"], show=False)
        fmt = run(["ruff", "format"], show=False)
        left = [ln for ln in fixed.stdout.splitlines() if re.match(r"^\S+:\d+:\d+: ", ln)]
        for ln in left:
            print("   " + ln)
        print(
            "python: ruff "
            + (fixed.stderr.strip().splitlines() or ["done"])[-1]
            + " | "
            + (fmt.stdout.strip().splitlines() or ["format done"])[-1]
        )
        problems = len(left)
    return problems


# ---------------------------------------------------------------- 2. whitespace and line endings
def normalized(path):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text.strip():
        return None
    force_lf = path.suffix == ".sh" or path.name == "Makefile"
    eol = "\r\n" if (b"\r\n" in raw and not force_lf) else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    if path.suffix != ".md":
        lines = [ln.rstrip(" \t") for ln in lines]
    while lines and lines[-1] == "":
        lines.pop()
    new = "\n".join(lines) + "\n"
    new = new.replace("\n", eol)
    return None if new.encode("utf-8") == raw else new


def text_step(files, check):
    changed = []
    for f in files:
        p = ROOT / f
        if p.suffix not in TEXT_SUFFIX and p.name not in TEXT_NAMES:
            continue
        new = normalized(p)
        if new is None:
            continue
        changed.append(f)
        if not check:
            p.write_bytes(new.encode("utf-8"))
    verb = "need fixing" if check else "fixed"
    print(f"text: {len(changed)} file(s) {verb} (trailing spaces / final newline / line endings)")
    for f in changed[:8]:
        print("   " + f)
    if len(changed) > 8:
        print(f"   ... and {len(changed) - 8} more")
    return len(changed) if check else 0


# ---------------------------------------------------------------- 3-5. checks that report only
def js_step(files):
    if not shutil.which("node"):
        print("javascript: SKIPPED (node not installed; only a syntax check, optional)")
        return 0
    bad = 0
    js = [f for f in files if f.endswith((".js", ".mjs"))]
    for f in js:
        r = run(["node", "--check", f], show=False)
        if r.returncode != 0:
            bad += 1
            print(f"   {f}: {r.stderr.strip().splitlines()[0] if r.stderr.strip() else 'syntax error'}")
    print(f"javascript: {len(js)} file(s) syntax-checked, {bad} problem(s)")
    return bad


def shell_step(files):
    if not shutil.which("shellcheck"):
        print("shell: SKIPPED (shellcheck not installed)")
        return 0
    sh = [f for f in files if f.endswith(".sh")]
    r = run(["shellcheck", "-S", "warning", *sh], show=True) if sh else None
    bad = 0 if r is None or r.returncode == 0 else 1
    print(f"shell: {len(sh)} script(s) checked with shellcheck, {'clean' if not bad else 'problems above'}")
    return bad


def json_step(files):
    bad = 0
    js = [f for f in files if f.endswith(".json")]
    for f in js:
        try:
            json.loads((ROOT / f).read_text(encoding="utf-8"))
        except ValueError as e:
            bad += 1
            print(f"   {f}: {e}")
    print(f"json: {len(js)} file(s) parsed, {bad} problem(s)")
    return bad


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--check", action="store_true", help="change nothing; exit code = number of problems")
    a = ap.parse_args()
    files = project_files()
    print(f"{'linting' if a.check else 'fixing'} {len(files)} files\n")
    problems = python_step(a.check)
    problems += text_step(files, a.check)
    files = project_files()  # same set; shell/JS checks read the (now fixed) files
    problems += js_step(files) + shell_step(files) + json_step(files)
    print("\n" + ("all clean" if not problems else f"{problems} problem(s) left"))
    sys.exit(min(problems, 100))


if __name__ == "__main__":
    main()
