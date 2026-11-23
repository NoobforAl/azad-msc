"""Print the versions of the tools the course uses and flag what is missing or too old.

Usage:
    python check_tools.py            # exit code = number of problems with REQUIRED tools
    python check_tools.py --strict   # optional tools count as required too

Standard library only; runs on Python 3.8 or newer.
"""

import argparse
import re
import shutil
import subprocess
import sys
from typing import List, NamedTuple, Optional, Tuple

VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


class Tool(NamedTuple):
    name: str  # name shown in the report
    cmd: str  # executable looked up on PATH
    args: Tuple[str, ...]  # arguments that print the version
    minimum: Optional[Tuple[int, int]]  # (major, minor) or None when any version will do
    required: bool
    why: str


class Result(NamedTuple):
    tool: Tool
    status: str  # OK, OLD, MISSING, BROKEN
    found: str  # version text, "" when missing
    note: str


TOOLS = (
    Tool("go", "go", ("version",), (1, 22), True, "builds the registration-api service"),
    Tool("python", sys.executable, ("--version",), (3, 8), True, "analytics service and lab scripts"),
    Tool("ruff", "ruff", ("--version",), None, True, "Python lint gate used by make lint and CI"),
    Tool("git", "git", ("--version",), (2, 28), True, "git init -b needs 2.28; every lab commits"),
    Tool("make", "make", ("--version",), None, False, "make check; without it run the commands by hand"),
    Tool("docker", "docker", ("--version",), None, False, "compose labs and lab 03 (PlantUML, Structurizr)"),
    Tool("node", "node", ("--version",), None, False, "npx mermaid-cli in lab 03"),
    Tool("java", "java", ("-version",), None, False, "PlantUML jar in lab 03 (alternative to Docker)"),
)


def parse_version(text: str) -> Optional[Tuple[int, ...]]:
    """Return the first dotted version number found in text, e.g. 'go1.27.4' -> (1, 27, 4)."""
    match = VERSION_RE.search(text)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def run(cmd: List[str], timeout: float = 15.0) -> Tuple[int, str]:
    """Run a command and return (exit code, stdout + stderr). Some tools print their version on stderr."""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def check(tool: Tool) -> Result:
    """Look one tool up and compare its version with the minimum."""
    exe = tool.cmd if tool.cmd == sys.executable else shutil.which(tool.cmd)
    if exe is None:
        return Result(tool, "MISSING", "", "not on PATH")
    try:
        code, out = run([exe, *tool.args])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Result(tool, "BROKEN", "", str(exc))
    version = parse_version(out)
    if code != 0 or version is None:
        return Result(tool, "BROKEN", "", "could not read a version from: " + out.strip()[:60])
    found = ".".join(str(part) for part in version)
    note = ""
    if tool.cmd == "docker":
        # The CLI can be installed while the daemon is stopped; labs need the daemon.
        daemon_code, _ = run([exe, "info"], timeout=20.0)
        note = "daemon reachable" if daemon_code == 0 else "daemon NOT reachable"
    if tool.minimum is not None and version[:2] < tool.minimum:
        return Result(tool, "OLD", found, "need >= %d.%d" % tool.minimum)
    return Result(tool, "OK", found, note)


def format_row(result: Result) -> str:
    tool = result.tool
    need = ">= %d.%d" % tool.minimum if tool.minimum else "any"
    kind = "required" if tool.required else "optional"
    note = result.note or tool.why
    return "%-8s %-9s %-8s %-9s %-8s %s" % (tool.name, need, result.found or "-", kind, result.status, note)


def problems(results: List[Result], strict: bool) -> List[Result]:
    """A problem is a required tool (or any tool with --strict) whose status is not OK."""
    return [r for r in results if r.status != "OK" and (strict or r.tool.required)]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="treat optional tools as required")
    args = parser.parse_args(argv)

    results = [check(tool) for tool in TOOLS]
    print("%-8s %-9s %-8s %-9s %-8s %s" % ("tool", "need", "found", "kind", "status", "note"))
    for result in results:
        print(format_row(result))
    bad = problems(results, args.strict)
    optional_gaps = [r.tool.name for r in results if r.status != "OK" and not r.tool.required]
    print()
    if bad:
        print("PROBLEMS: " + ", ".join(r.tool.name for r in bad))
    else:
        print("all required tools present")
    if optional_gaps and not args.strict:
        print("optional tools not ready: " + ", ".join(optional_gaps))
    return len(bad)


if __name__ == "__main__":
    sys.exit(main())
