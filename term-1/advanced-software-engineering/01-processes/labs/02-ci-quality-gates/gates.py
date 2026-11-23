"""Run the quality gates of the Course Registration Platform locally; CI runs this same script (standard library only).

Usage:
    python gates.py [--project PATH] [--min-coverage 70] [--only gofmt,vet,ruff,tests,coverage]

Gates (each prints PASS / FAIL / SKIP, all gates run even after a failure, exit code = number of failed gates):
    gofmt     no Go file under cmd/ and internal/ needs reformatting      (gofmt -l)
    vet       go vet ./...
    ruff      ruff check analytics                                        (rules come from ruff.toml)
    tests     go test ./... and python -m unittest discover
    coverage  total statement coverage of the Go code >= --min-coverage   (go test -coverprofile + go tool cover -func)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List, Optional, Tuple

Result = Tuple[str, str]  # (status, detail)  status is PASS, FAIL or SKIP

TOTAL_LINE = re.compile(r"^total:\s+\(statements\)\s+([0-9.]+)%\s*$", re.MULTILINE)


def run(cmd: List[str], cwd: str) -> Tuple[int, str]:
    """Run cmd in cwd and return (exit code, combined output). A missing tool gives exit code 127."""
    if shutil.which(cmd[0]) is None:
        return 127, "{}: command not found".format(cmd[0])
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.returncode, proc.stdout


def last_lines(text: str, count: int = 3) -> str:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return " | ".join(line.strip() for line in lines[-count:])


def failure_lines(text: str, prefixes: Tuple[str, ...], count: int = 3) -> str:
    """Lines that start with one of prefixes (the failing test names); the tail of the output if there are none."""
    picked = [line.strip() for line in text.splitlines() if line.strip().startswith(prefixes)]
    return " | ".join(picked[:count]) if picked else last_lines(text)


def parse_total_coverage(cover_func_output: str) -> Optional[float]:
    """Return the number on the `total:` line of `go tool cover -func` output, or None if there is none."""
    match = TOTAL_LINE.search(cover_func_output)
    return float(match.group(1)) if match else None


def gate_gofmt(project: str, _: argparse.Namespace) -> Result:
    code, out = run(["gofmt", "-l", "cmd", "internal"], project)
    if code == 127:
        return "SKIP", out
    files = [line for line in out.splitlines() if line.strip()]
    if code != 0:
        return "FAIL", last_lines(out)
    if files:
        return "FAIL", "needs gofmt: " + ", ".join(files)
    return "PASS", "all Go files formatted"


def gate_vet(project: str, _: argparse.Namespace) -> Result:
    code, out = run(["go", "vet", "./..."], project)
    if code == 127:
        return "SKIP", out
    return ("PASS", "go vet ./... is clean") if code == 0 else ("FAIL", last_lines(out))


def gate_ruff(project: str, _: argparse.Namespace) -> Result:
    code, out = run(["ruff", "check", "--output-format=concise", "analytics"], project)
    if code == 127:
        return "SKIP", out
    if code == 0:
        return "PASS", last_lines(out, 1)
    return "FAIL", failure_lines(out, ("analytics",))


def gate_tests(project: str, _: argparse.Namespace) -> Result:
    code, out = run(["go", "test", "./..."], project)
    if code == 127:
        return "SKIP", out
    if code != 0:
        return "FAIL", "go test: " + failure_lines(out, ("--- FAIL", "FAIL"))
    code, out = run([sys.executable, "-m", "unittest", "discover", "-s", "analytics/tests"], project)
    if code != 0:
        return "FAIL", "unittest: " + failure_lines(out, ("FAIL:", "ERROR:"))
    return "PASS", "go test and unittest pass"


def gate_coverage(project: str, args: argparse.Namespace) -> Result:
    if shutil.which("go") is None:
        return "SKIP", "go: command not found"
    with tempfile.TemporaryDirectory() as tmp:
        profile = os.path.join(tmp, "cover.out")
        code, out = run(["go", "test", "-coverprofile=" + profile, "./..."], project)
        if code != 0:
            return "FAIL", "go test: " + last_lines(out)
        code, out = run(["go", "tool", "cover", "-func=" + profile], project)
    total = parse_total_coverage(out)
    if code != 0 or total is None:
        return "FAIL", "cannot read coverage: " + last_lines(out)
    verdict = "PASS" if total >= args.min_coverage else "FAIL"
    return verdict, "total {:.1f}% of statements (minimum {:.1f}%)".format(total, args.min_coverage)


GATES: Dict[str, Callable[[str, argparse.Namespace], Result]] = {
    "gofmt": gate_gofmt,
    "vet": gate_vet,
    "ruff": gate_ruff,
    "tests": gate_tests,
    "coverage": gate_coverage,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--project", default=".", help="folder with go.mod and analytics/ (default: current folder)")
    parser.add_argument("--min-coverage", type=float, default=70.0, help="minimum total Go coverage in percent")
    parser.add_argument("--only", default="", help="comma-separated gate names (default: all)")
    args = parser.parse_args(argv)

    names = [n for n in args.only.split(",") if n] or list(GATES)
    unknown = [n for n in names if n not in GATES]
    if unknown:
        parser.error("unknown gate(s): {} (choose from {})".format(", ".join(unknown), ", ".join(GATES)))

    failed = 0
    for name in names:
        status, detail = GATES[name](args.project, args)
        failed += status == "FAIL"
        print("{:<9} {:<5} {}".format(name, status, detail))
    print("{} of {} gates failed".format(failed, len(names)))
    return failed


if __name__ == "__main__":
    sys.exit(main())
