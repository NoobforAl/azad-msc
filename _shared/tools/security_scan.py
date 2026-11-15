"""Scan what would be published for secrets and private data. Meant to run before every push to a PUBLIC repository.

Usage:  python _shared/tools/security_scan.py [--site site]       (or: make security)
Exit code = number of findings (0 = clean).

It reads the files git would publish (tracked plus untracked-but-not-ignored, minus the kernel/OpenBSD submodules) and,
with --site, the built site folder. It looks for private keys, API tokens, passwords in assignments, e-mail addresses,
public IP addresses, personal local paths, and (for GitHub workflows) risky settings. It cannot prove a repository is
safe; it catches the common accidents.
"""

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKIP_SUFFIX = {".png", ".svg", ".pyc", ".wasm", ".bin", ".ico", ".jpg", ".gif", ".woff2", ".woff", ".pdf", ".pptx"}
# Text that is fine: documentation placeholders and public project addresses.
ALLOW_PATH = re.compile(r"/home/fred/")  # the course lab VM's user ("fred"), not a real person's home
ALLOW_EMAIL = re.compile(r"(@example\.|users\.noreply\.github\.com|@kernel\.org|@lists\.|sales@leaningtech\.com)")

PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{20,}"),
    "Slack/Stripe/Google key": re.compile(
        r"\bxox[baprs]-[A-Za-z0-9-]{10,}|\bsk_live_[A-Za-z0-9]{10,}|\bAIza[0-9A-Za-z_-]{30,}"
    ),
    "secret assigned in code": re.compile(
        r"(?i)\b(api[_-]?key|secret|passwd|password|token|bearer)\b\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']"
    ),
    "e-mail address": re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}"),
    "public IPv4 address": re.compile(
        r"\b(?!127\.|10\.|192\.168\.|0\.|255\.|172\.(?:1[6-9]|2\d|3[01])\.)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    ),
    "personal local path": re.compile(r"(?i)C:\\Users\\[A-Za-z0-9_.-]+|/home/[a-z][a-z0-9_-]+/|/Users/[A-Za-z0-9_.-]+"),
}
# Version-like strings (6.18.63.202611 etc.) look like IPs; only report IPs that are not part of a longer dotted number.
IP_CONTEXT = re.compile(r"[\d.]*\d\.\d+\.\d+\.\d+\.\d+")


def publishable_files():
    out = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True, cwd=ROOT
    ).stdout.splitlines()
    return [ROOT / f for f in out if not f.startswith("_shared/sources/")]


def scan_file(path, rel):
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    for name, rx in PATTERNS.items():
        for m in rx.finditer(text):
            s = m.group(0)
            if name == "e-mail address" and (
                ALLOW_EMAIL.search(s) or s.split("@")[1].lower().endswith((".png", ".js", ".css", ".svg", ".woff2"))
            ):
                continue
            if name == "personal local path" and ALLOW_PATH.search(s):
                continue
            if name == "public IPv4 address":
                # skip version numbers such as 6.18.63.202611 and dotted ids
                around = text[max(0, m.start() - 12) : m.end() + 12]
                if (
                    re.search(r"\d\.\d+\.\d+\.\d+\.\d+|\d+\.\d+\.\d+\.\d+\.\d", around)
                    or any(int(x) > 255 for x in s.split("."))
                    or re.match(r"-[A-Za-z]", text[m.end() : m.end() + 2])
                ):  # 6.18.58.1-microsoft-standard-WSL2
                    continue
            line = text.count("\n", 0, m.start()) + 1
            findings.append((rel, line, name, s[:70]))
    return findings


def check_workflows():
    """GitHub Actions: least privilege, no pull_request_target, no secrets echoed, actions pinned to a version."""
    out = []
    wf = ROOT / ".github" / "workflows"
    for f in sorted(wf.glob("*.y*ml")) if wf.is_dir() else []:
        t = f.read_text(encoding="utf-8")
        rel = f.relative_to(ROOT).as_posix()
        if not re.search(r"^permissions:", t, re.M):
            out.append((rel, 1, "workflow without a top-level permissions block", "add least-privilege permissions"))
        if "pull_request_target" in t:
            out.append((rel, 1, "pull_request_target trigger", "can run untrusted code with secrets"))
        for m in re.finditer(r"uses:\s*([^\s@]+)@(\S+)", t):
            if not re.match(r"v?\d", m.group(2)) and not re.fullmatch(r"[0-9a-f]{40}", m.group(2)):
                out.append((rel, t.count("\n", 0, m.start()) + 1, "action not pinned to a version", m.group(0)))
        if re.search(r"echo\s+.*\$\{\{\s*secrets\.", t):
            out.append((rel, 1, "secret echoed in a workflow", ""))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", type=pathlib.Path, help="also scan this built site folder")
    a = ap.parse_args()
    findings = []
    files = publishable_files()
    for f in files:
        if f.is_file() and f.suffix.lower() not in SKIP_SUFFIX:
            findings += scan_file(f, f.relative_to(ROOT).as_posix())
    n_site = 0
    if a.site and a.site.is_dir():
        for f in a.site.rglob("*"):
            if f.is_file() and f.suffix.lower() not in SKIP_SUFFIX:
                n_site += 1
                findings += scan_file(f, "site/" + f.relative_to(a.site).as_posix())
    findings += check_workflows()
    for rel, line, kind, s in findings:
        print(f"{rel}:{line}: {kind}: {s}")
    print(
        f"scanned {len(files)} repository files"
        + (f" and {n_site} site files" if a.site else "")
        + f": {len(findings)} finding(s)"
    )
    sys.exit(min(len(findings), 100))


if __name__ == "__main__":
    main()
