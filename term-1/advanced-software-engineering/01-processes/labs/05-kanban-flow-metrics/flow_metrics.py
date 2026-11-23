"""Kanban flow metrics from an issue export: cycle time, lead time, throughput, WIP, aging (standard library only).

Usage:
    python flow_metrics.py issues.csv [--wip-limit 3] [--as-of 2026-05-29]

CSV columns: id,title,type,created,started,done  (ISO dates; started is empty if work has not begun, done is empty
if the issue is still open). Durations are counted in calendar days, inclusive: an issue started and finished on the
same day has a cycle time of 1 day. Weekends are therefore part of the elapsed time.
"""
import argparse
import csv
import statistics
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Issue:
    id: str
    title: str
    created: date
    started: Optional[date]
    done: Optional[date]


def parse_date(text: str) -> Optional[date]:
    return date.fromisoformat(text) if text.strip() else None


def load(path: str) -> List[Issue]:
    with open(path, newline="", encoding="utf-8") as handle:
        return [
            Issue(r["id"], r["title"], date.fromisoformat(r["created"]), parse_date(r["started"]), parse_date(r["done"]))
            for r in csv.DictReader(handle)
        ]


def percentile(values: List[float], pct: int) -> float:
    """Nearest-rank percentile (pct is a whole number)."""
    ordered = sorted(values)
    rank = max(1, -(-pct * len(ordered) // 100))
    return ordered[rank - 1]


def days_inclusive(first: date, last: date) -> int:
    return (last - first).days + 1


def working_days(first: date, last: date) -> List[date]:
    """Monday to Friday dates from first to last, inclusive."""
    every = [first + timedelta(days=k) for k in range((last - first).days + 1)]
    return [d for d in every if d.weekday() < 5]


def in_progress_on(issue: Issue, day: date) -> bool:
    """Started on or before `day` and not finished before `day` (an issue finished on `day` was worked on that day)."""
    return issue.started is not None and issue.started <= day and not (issue.done is not None and issue.done < day)


def report(path: str, issues: List[Issue], as_of: date, wip_limit: Optional[int]) -> None:
    first = min(i.created for i in issues)
    finished = [(i, i.started, i.done) for i in issues if i.started and i.done and i.done <= as_of]
    open_started = [i for i in issues if i.started and i.started <= as_of and not (i.done and i.done <= as_of)]
    not_started = [i for i in issues if not i.started or i.started > as_of]
    print("Flow metrics for {}   window {} .. {} ({} days)".format(path, first, as_of, days_inclusive(first, as_of)))
    print("issues: {} total, {} done, {} in progress, {} not started".format(
        len(issues), len(finished), len(open_started), len(not_started)))
    print()

    print("Throughput (issues finished per week, weeks start on Monday)")
    week = first - timedelta(days=first.weekday())
    per_week = []
    while week <= as_of:
        count = sum(1 for _, _, done in finished if week <= done < week + timedelta(days=7))
        per_week.append(count)
        print("  {}  {:>2}  {}".format(week, count, "#" * count))
        week += timedelta(days=7)
    print("  mean {:.2f} per week, min {}, max {}".format(statistics.mean(per_week), min(per_week), max(per_week)))
    print()

    cycle = [float(days_inclusive(started, done)) for _, started, done in finished]
    lead = [float(days_inclusive(i.created, done)) for i, _, done in finished]
    print("Cycle time (started -> done) and lead time (created -> done), days, {} finished issues".format(len(finished)))
    print("  {:<11} {:>6} {:>7} {:>5} {:>5}".format("", "mean", "median", "p85", "max"))
    for name, values in (("cycle time", cycle), ("lead time", lead)):
        print("  {:<11} {:>6.1f} {:>7.1f} {:>5.0f} {:>5.0f}".format(
            name, statistics.mean(values), statistics.median(values), percentile(values, 85), max(values)))
    print()

    days = working_days(first, as_of)
    wip = [sum(1 for i in issues if in_progress_on(i, d)) for d in days]
    print("Work in progress (issues started and not yet finished, working days only)")
    print("  average {:.2f}, maximum {}".format(statistics.mean(wip), max(wip)))
    if wip_limit is not None:
        print("  days above the WIP limit of {}: {} of {}".format(wip_limit, sum(1 for w in wip if w > wip_limit), len(wip)))
    print()

    mean_cycle_working = statistics.mean(len(working_days(started, done)) for _, started, done in finished)
    throughput_per_day = len(finished) / float(len(days))
    print("Little's law check (L = lambda x W, in working days; it holds for a stable system, the window edges disturb it)")
    print("  lambda {:.3f} issues/day x W {:.2f} days = {:.2f}   measured average WIP {:.2f}".format(
        throughput_per_day, mean_cycle_working, throughput_per_day * mean_cycle_working, statistics.mean(wip)))
    print()

    print("Aging work in progress (age in days since start, oldest first)")
    oldest = sorted((i for i in open_started if i.started), key=lambda i: (i.started, i.id))[:5]
    for issue in oldest:
        if issue.started:
            print("  {}  {:>3} d  {}".format(issue.id, days_inclusive(issue.started, as_of), issue.title))
    if not oldest:
        print("  none")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("csv_file", help="issue export")
    parser.add_argument("--wip-limit", type=int, help="report the days above this limit")
    parser.add_argument("--as-of", type=date.fromisoformat, help="measure up to this date (default: last date in the file)")
    args = parser.parse_args(argv)
    issues = load(args.csv_file)
    if not issues:
        print("no issues in " + args.csv_file)
        return 1
    last_seen = max(d for i in issues for d in (i.created, i.started, i.done) if d)
    report(args.csv_file, issues, args.as_of or last_seen, args.wip_limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
