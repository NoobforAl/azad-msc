"""Generate a SYNTHETIC issue export (CSV) by simulating a small team, deterministically (standard library only).

Usage:
    python gen_issues.py [--wip-limit none|N] [--weeks 12] [--seed 2026] [--arrival 0.85] > issues.csv

The simulation (all numbers are assumptions of this lab, not data from any real team):
    - 3 developers = 3 developer-days of capacity per working day (Monday to Friday), no work at weekends
    - every working day a new issue arrives with probability --arrival; its effort is drawn from EFFORTS (days)
    - one developer can spend at most one day per day on one issue
    - with no WIP limit every new issue is started the day it arrives; the 3 developer-days are shared round-robin
      among all issues in progress (this is what multitasking looks like)
    - with --wip-limit N an issue is started only when fewer than N issues are in progress (oldest first)
The random numbers come from a small linear congruential generator, so the output is the same on every machine.
"""
import argparse
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

EFFORTS = [1, 1, 2, 2, 2, 3, 3, 4, 5, 8]  # developer-days; mean 3.1
VERBS = ["Add", "Fix", "Improve", "Export", "Validate", "Document"]
NOUNS = ["waitlist", "prerequisite check", "capacity report", "CSV import", "audit log", "course search",
         "student profile", "grade export", "email notice", "schedule view"]
START = date(2026, 3, 2)  # a Monday
CAPACITY = 3


class Lcg:
    """x -> (1103515245 x + 12345) mod 2^31. Not good randomness, but identical on every platform."""

    def __init__(self, seed: int) -> None:
        self.state = seed % (2 ** 31)

    def random(self) -> float:
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state / float(2 ** 31)


@dataclass
class Issue:
    id: str
    title: str
    kind: str
    created: date
    left: float
    started: Optional[date] = None
    done: Optional[date] = None


def simulate(weeks: int, seed: int, arrival: float, wip_limit: Optional[int]) -> List[Issue]:
    rng = Lcg(seed)
    issues: List[Issue] = []
    in_progress: List[Issue] = []
    pointer = 0
    day = START
    for _ in range(weeks * 5):
        while day.weekday() >= 5:
            day += timedelta(days=1)
        if rng.random() < arrival:
            title = "{} {}".format(VERBS[int(rng.random() * len(VERBS))], NOUNS[int(rng.random() * len(NOUNS))])
            kind = "bug" if rng.random() < 0.3 else "feature"
            effort = float(EFFORTS[int(rng.random() * len(EFFORTS))])
            issues.append(Issue("ISS-{:03d}".format(len(issues) + 1), title, kind, day, effort))
        for issue in issues:
            if issue.started is None and (wip_limit is None or len(in_progress) < wip_limit):
                issue.started = day
                in_progress.append(issue)
        served = min(CAPACITY, len(in_progress))
        finished = []
        for k in range(served):
            issue = in_progress[(pointer + k) % len(in_progress)]
            issue.left -= 1.0
            if issue.left <= 0:
                issue.done = day
                finished.append(issue)
        pointer += served
        for issue in finished:
            in_progress.remove(issue)
        pointer = pointer % max(len(in_progress), 1)
        day += timedelta(days=1)
    return issues


def to_csv(issues: List[Issue]) -> str:
    lines = ["id,title,type,created,started,done"]
    for issue in issues:
        dates = [d.isoformat() if d else "" for d in (issue.created, issue.started, issue.done)]
        lines.append(",".join([issue.id, issue.title, issue.kind] + dates))
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wip-limit", default="none", help="'none' (default) or a whole number")
    parser.add_argument("--weeks", type=int, default=12, help="weeks to simulate (default 12)")
    parser.add_argument("--seed", type=int, default=2026, help="seed of the random generator (default 2026)")
    parser.add_argument("--arrival", type=float, default=0.85, help="chance of a new issue per working day (default 0.85)")
    args = parser.parse_args(argv)
    limit = None if args.wip_limit == "none" else int(args.wip_limit)
    sys.stdout.write(to_csv(simulate(args.weeks, args.seed, args.arrival, limit)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
