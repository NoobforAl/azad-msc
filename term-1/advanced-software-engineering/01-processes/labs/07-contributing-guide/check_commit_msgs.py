"""Check commit messages against the rules of CONTRIBUTING.md (standard library only).

Usage:
    python check_commit_msgs.py [--repo PATH] [RANGE]       check every commit in RANGE (default: HEAD, all history)
    python check_commit_msgs.py --message-file FILE         check one message (for a commit-msg hook)

Rules (the numbers are the project's choice, adapted from Linux Documentation/process/submitting-patches.rst):
    S1  the subject line is not empty
    S2  the subject is at most 72 characters           (Linux: "no more than 70-75 characters")
    S3  the subject does not end with a period
    S4  the subject starts with an area and a colon, e.g. "catalog: add Count"   (Linux: "subsystem: summary phrase")
    B1  a blank line separates the subject from the body
    B2  body lines are at most 75 characters            (Linux: "line wrapped at 75 columns"); code, URLs, trailers exempt
    T1  at least one Signed-off-by: line
    T2  one Signed-off-by: line has the name and the e-mail address of the commit's author
The script exits with the number of commits that have a violation (0 = all good), at most 255.
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

SUBJECT_MAX = 72
BODY_MAX = 75
AREA = re.compile(r"^[A-Za-z0-9_./-]+: \S")
SIGNOFF = re.compile(r"^Signed-off-by:\s*(.+?)\s*<([^<>]+)>\s*$", re.IGNORECASE)
TRAILER = re.compile(r"^[A-Za-z][A-Za-z-]*:\s")


@dataclass
class Violation:
    rule: str
    text: str

    def __str__(self) -> str:
        return "[{}] {}".format(self.rule, self.text)


def check_message(message: str, author_name: str, author_email: str) -> List[Violation]:
    """Return the rule violations of one commit message (an empty list means the message is fine)."""
    lines = [line for line in message.rstrip().split("\n") if not line.startswith("#")]
    found: List[Violation] = []
    subject = lines[0].rstrip() if lines else ""
    if not subject:
        return [Violation("S1", "the subject line is empty")]
    if len(subject) > SUBJECT_MAX:
        found.append(Violation("S2", "subject is {} characters (maximum {})".format(len(subject), SUBJECT_MAX)))
    if subject.endswith("."):
        found.append(Violation("S3", "subject ends with a period"))
    if not AREA.match(subject) and not subject.startswith('Revert "'):
        found.append(Violation("S4", 'subject does not start with "area: " (example: "catalog: add Count")'))
    if len(lines) > 1 and lines[1].strip():
        found.append(Violation("B1", "no blank line between the subject and the body"))
    for number, line in enumerate(lines[1:], start=2):
        exempt = line.startswith((" ", "\t")) or "://" in line or TRAILER.match(line)
        if len(line) > BODY_MAX and not exempt:
            found.append(Violation("B2", "line {} is {} characters (maximum {})".format(number, len(line), BODY_MAX)))
            break
    signers = [m.groups() for m in (SIGNOFF.match(line) for line in lines) if m]
    if not signers:
        found.append(Violation("T1", "no Signed-off-by: line (git commit -s adds it)"))
    elif not any(n.strip() == author_name and e.strip().lower() == author_email.lower() for n, e in signers):
        found.append(
            Violation("T2", "no Signed-off-by: line matches the author {} <{}>".format(author_name, author_email))
        )
    return found


def git(repo: str, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )
    if result.returncode != 0:
        raise SystemExit("git {} failed: {}".format(" ".join(args), result.stderr.strip()))
    return result.stdout


def commits(repo: str, rev: str) -> List[Tuple[str, str, str, str]]:
    """Return (short hash, author name, author email, message) for every non-merge commit in rev."""
    out = git(repo, "log", "--no-merges", "--reverse", "--format=%h%x1f%an%x1f%ae%x1f%B%x1e", rev)
    records = []
    for chunk in out.split(chr(30)):
        chunk = chunk.strip(chr(10))
        if chunk:
            short, name, email, message = chunk.split(chr(31), 3)
            records.append((short, name, email, message))
    return records


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("rev", nargs="?", default="HEAD", help="commit range, e.g. m0..HEAD (default: HEAD)")
    parser.add_argument("--repo", default=".", help="path of the Git repository (default: current directory)")
    parser.add_argument("--message-file", help="check this message file instead of the history (commit-msg hook)")
    args = parser.parse_args(argv)

    if args.message_file:
        with open(args.message_file, encoding="utf-8") as handle:
            message = handle.read()
        ident = git(args.repo, "var", "GIT_AUTHOR_IDENT").strip()
        match = re.match(r"^(.*) <([^<>]*)> \d+ [+-]\d{4}$", ident)
        name, email = match.groups() if match else ("", "")
        problems = check_message(message, name, email)
        for problem in problems:
            print("commit message rejected: {}".format(problem), file=sys.stderr)
        return 1 if problems else 0

    bad = 0
    records = commits(args.repo, args.rev)
    for short, name, email, message in records:
        problems = check_message(message, name, email)
        subject = message.split("\n", 1)[0]
        print("{} {} {}".format("FAIL" if problems else "ok  ", short, subject))
        for problem in problems:
            print("       {}".format(problem))
        bad += bool(problems)
    print("{} of {} commits violate the rules".format(bad, len(records)))
    return min(bad, 255)


if __name__ == "__main__":
    sys.exit(main())
