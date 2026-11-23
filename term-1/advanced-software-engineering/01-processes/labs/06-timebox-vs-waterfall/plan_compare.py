"""Plan the same backlog as a waterfall project and as timeboxed sprints, and compare (standard library only).

Usage:
    python plan_compare.py [backlog.csv] [--deadline-weeks 9] [--timebox-weeks 3] [--devs 3] [--focus 0.8]
                           [--overrun 0.0]

THE BACKLOG, THE VALUE POINTS, THE FOCUS FACTOR AND THE OVERRUN ARE ASSUMPTIONS OF THIS LAB, NOT DATA.

Capacity: devs x 5 working days per week x focus (the share of a day that goes into the product; meetings and
reviews take the rest). With the defaults that is 12 developer-days per week.

Waterfall plan: the whole scope goes through four phases one after the other. Each phase takes a fixed share of the
total effort; the shares are the average cost percentages of 132 Hewlett-Packard projects in Schach 8e, ch. 1,
Figure 1.4 (requirements 18, design 19, coding with unit testing 34, integration 29), used here as an assumption
about how a waterfall project spends its time. Nothing is delivered before the last phase ends.

Timeboxed plan: sprints of fixed length. At the start of a sprint the team commits to the highest-priority items that
fit into the sprint capacity (by estimate, first fit). At the end of the sprint what is finished is delivered; work
that did not fit is cut from the sprint and goes back to the backlog with its progress. The timebox never moves.

--overrun is the share by which real effort exceeds the estimates (0.3 means every item takes 30% more). The
plans are made with the estimates; the execution uses the real effort.
"""

import argparse
import csv
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

WATERFALL_PHASES = [("requirements", 0.18), ("design", 0.19), ("coding + unit tests", 0.34), ("integration", 0.29)]
DAYS_PER_WEEK = 5


@dataclass
class Item:
    id: str
    title: str
    priority: int
    value: int
    estimate: float
    worked: float = 0.0  # developer-days already spent (real effort)
    delivered_week: Optional[float] = None


@dataclass
class Sprint:
    number: int
    planned_load: float  # developer-days committed, by estimate
    delivered: List[str]
    cut: List[str]


def load(path: str) -> List[Item]:
    with open(path, newline="", encoding="utf-8") as handle:
        return [
            Item(r["id"], r["title"], int(r["priority"]), int(r["value"]), float(r["estimate_days"]))
            for r in csv.DictReader(handle)
        ]


def waterfall(
    items: List[Item], capacity_per_week: float, overrun: float
) -> Tuple[List[Tuple[str, float, float]], float]:
    """Return ([(phase, start week, end week)], end week of the whole project). All items finish together."""
    total_real = sum(i.estimate for i in items) * (1.0 + overrun)
    weeks_total = total_real / capacity_per_week
    phases, start = [], 0.0
    for name, share in WATERFALL_PHASES:
        end = start + share * weeks_total
        phases.append((name, start, end))
        start = end
    return phases, start


def timeboxed(
    items: List[Item], capacity_per_sprint: float, sprints: int, sprint_weeks: float, overrun: float
) -> List[Sprint]:
    """Run the sprints. Returns one record per sprint with the committed load and the delivered and cut item IDs."""
    log = []
    for number in range(1, sprints + 1):
        open_items = sorted((i for i in items if i.delivered_week is None), key=lambda i: (i.priority, i.id))
        planned, room = [], capacity_per_sprint
        for item in open_items:  # first fit, by estimate
            fraction_left = 1.0 - item.worked / (item.estimate * (1.0 + overrun))
            need = item.estimate * max(fraction_left, 0.0)
            if need <= room:
                planned.append(item)
                room -= need
        budget = capacity_per_sprint
        delivered, cut = [], []
        for item in planned:  # execution with the real effort, in priority order
            real_left = item.estimate * (1.0 + overrun) - item.worked
            spend = min(real_left, budget)
            item.worked += spend
            budget -= spend
            if item.worked >= item.estimate * (1.0 + overrun) - 1e-9:
                item.delivered_week = number * sprint_weeks
                delivered.append(item.id)
            else:
                cut.append(item.id)
        log.append(Sprint(number, capacity_per_sprint - room, delivered, cut))
    return log


def summary(
    items: List[Item], phases_end: float, deadline: float, sprint_weeks: float, sprints: int
) -> List[Tuple[str, List[str]]]:
    total_value = float(sum(i.value for i in items))
    rows = []
    for week in [sprint_weeks * k for k in range(1, sprints + 1)]:
        wf = total_value if phases_end <= week + 1e-9 else 0.0
        tb = sum(i.value for i in items if i.delivered_week is not None and i.delivered_week <= week + 1e-9)
        rows.append(
            (
                "value delivered by week {:g}".format(week),
                ["{:.0%}".format(wf / total_value), "{:.0%}".format(tb / total_value)],
            )
        )
    return rows


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("backlog", nargs="?", default="backlog.csv", help="CSV: id,title,priority,value,estimate_days")
    parser.add_argument("--deadline-weeks", type=float, default=9.0)
    parser.add_argument("--timebox-weeks", type=float, default=3.0)
    parser.add_argument("--devs", type=int, default=3)
    parser.add_argument("--focus", type=float, default=0.8)
    parser.add_argument("--overrun", type=float, default=0.0, help="real effort = estimate x (1 + overrun)")
    args = parser.parse_args(argv)

    items = load(args.backlog)
    per_week = args.devs * DAYS_PER_WEEK * args.focus
    sprints = int(args.deadline_weeks // args.timebox_weeks)
    per_sprint = per_week * args.timebox_weeks
    estimate_total = sum(i.estimate for i in items)

    print(
        "Backlog {}: {} items, {:.0f} developer-days estimated, {} value points".format(
            args.backlog, len(items), estimate_total, sum(i.value for i in items)
        )
    )
    print(
        "Team: {} developers, focus {:.0%} = {:.1f} developer-days per week. Deadline: week {:g}.".format(
            args.devs, args.focus, per_week, args.deadline_weeks
        )
    )
    print("Real effort = estimate x {:.2f}  (overrun {:.0%})".format(1.0 + args.overrun, args.overrun))
    print()

    phases, wf_end = waterfall(items, per_week, args.overrun)
    print("WATERFALL  (phase shares: Schach 8e ch. 1 Fig. 1.4, 132 HP projects, used as an assumption)")
    for name, start, end in phases:
        print("  {:<20} week {:>5.1f} -> {:>5.1f}".format(name, start, end))
    verdict = (
        "meets the deadline"
        if wf_end <= args.deadline_weeks + 1e-9
        else "MISSES the deadline by {:.1f} weeks".format(wf_end - args.deadline_weeks)
    )
    print("  everything is delivered at week {:.1f} ({}); nothing is delivered earlier".format(wf_end, verdict))
    print()

    log = timeboxed(items, per_sprint, sprints, args.timebox_weeks, args.overrun)
    print(
        "TIMEBOXED  ({} sprints of {:g} weeks, capacity {:.1f} developer-days per sprint, plans use the estimates)".format(
            sprints, args.timebox_weeks, per_sprint
        )
    )
    for rec in log:
        print(
            "  sprint {} (week {:g}): committed {:.1f} d  delivered {}  cut {}".format(
                rec.number,
                rec.number * args.timebox_weeks,
                rec.planned_load,
                ", ".join(rec.delivered) or "-",
                ", ".join(rec.cut) or "-",
            )
        )
    left = [i for i in items if i.delivered_week is None]
    print("  not delivered at the deadline: {}".format(", ".join(i.id for i in left) or "-"))
    print()

    print("SUMMARY")
    print("  {:<30} {:>10} {:>10}".format("", "waterfall", "timeboxed"))
    for label, (wf, tb) in summary(items, wf_end, args.deadline_weeks, args.timebox_weeks, sprints):
        print("  {:<30} {:>10} {:>10}".format(label, wf, tb))
    delivered = [i for i in items if i.delivered_week is not None]
    wf_items = len(items) if wf_end <= args.deadline_weeks + 1e-9 else 0
    first_tb = "{:g}".format(min(i.delivered_week for i in delivered if i.delivered_week)) if delivered else "-"
    print(
        "  {:<30} {:>10} {:>10}".format(
            "items delivered at the deadline",
            "{}/{}".format(wf_items, len(items)),
            "{}/{}".format(len(delivered), len(items)),
        )
    )
    print("  {:<30} {:>10} {:>10}".format("first delivery (week)", "{:.1f}".format(wf_end), first_tb))
    return 0


if __name__ == "__main__":
    sys.exit(main())
