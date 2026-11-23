"""Relative cost of faults by phase, and the 10%-saving arithmetic (standard library only).

Usage:
    python fault_cost.py [--part economics|simulation|all] [--faults 1000] [--seed 7] [--r 2.5]
                         [--multipliers 1,2.5,6.3,15.6,39,98]

EVERYTHING BELOW THE PERCENTAGES OF PART 1 IS AN ILLUSTRATIVE ASSUMPTION, NOT MEASURED DATA.

Part 1 (economics) uses the average cost shares that Schach 8e, ch. 1 §1.3.2 reports (Figures 1.3 and 1.4) and
reproduces his argument that a 10% saving in coding is worth at most 0.85% of total cost, while a 10% saving in
postdelivery maintenance is worth about 7.5%.

Part 2 (simulation) injects faults into phases and lets each phase catch some of them. A fault that is caught in
phase j costs MULTIPLIERS[j] units to fix (1 unit = fixing it in the requirements phase). The multipliers grow by
a constant factor r per phase. That shape (steeply rising cost, Schach 8e, ch. 1 §1.4, Figure 1.5) is the book's
point; the numbers r, the fault mix and the detection rates are made up for this lab. Change them and see.
"""
import argparse
import random
import sys
from typing import Dict, List, Optional, Sequence, Tuple

PHASES = ["requirements", "design", "implementation", "integration", "acceptance", "maintenance"]

# Where faults are introduced (assumption). Schach 8e, ch. 1 §1.4 (citing Boehm 1979) says that 60-70% of the faults
# found in large projects are requirements, analysis or design faults; 0.35 + 0.30 = 0.65 sits inside that range.
INTRODUCED = {"requirements": 0.35, "design": 0.30, "implementation": 0.35}

# Chance that the activity of a phase finds a fault that is present when the phase starts (assumption).
# Postdelivery maintenance finds everything that is left (users report it).
DETECTION = {
    "test only at the end": [0.00, 0.00, 0.30, 0.40, 0.50, 1.00],
    "with inspections": [0.40, 0.40, 0.30, 0.40, 0.50, 1.00],
}

# Figures from Schach 8e, ch. 1 §1.3.2 (percent of total cost; approximate averages reported by the book).
ERAS = [
    # label, development share, postdelivery maintenance share, share of development spent on coding + unit testing
    ("1976-81 projects (Fig. 1.3a, 1.4)", 33.0, 67.0, 36.0),
    ("1992-98, 132 HP projects (Fig. 1.3b, 1.4)", 25.0, 75.0, 34.0),
]


def multipliers_from_r(r: float) -> List[float]:
    return [r ** k for k in range(len(PHASES))]


def economics(saving: float = 10.0) -> List[Tuple[str, float, float]]:
    """For each era return (label, total saving from `saving`% less coding cost, total saving from less maintenance)."""
    rows = []
    for label, development, maintenance, coding in ERAS:
        coding_share_of_total = development * coding / 100.0
        rows.append((label, saving * coding_share_of_total / 100.0, saving * maintenance / 100.0))
    return rows


def expected_cost(
    detection: Sequence[float], multipliers: Sequence[float], faults: int
) -> Tuple[List[float], List[float]]:
    """Exact expected faults found per phase and cost per phase (no randomness), as a cross-check for the simulation."""
    found = [0.0] * len(PHASES)
    for phase, share in INTRODUCED.items():
        alive = faults * share
        for j in range(PHASES.index(phase), len(PHASES)):
            caught = alive * detection[j]
            found[j] += caught
            alive -= caught
    return found, [f * m for f, m in zip(found, multipliers)]


def simulate(
    detection: Sequence[float], multipliers: Sequence[float], faults: int, seed: int
) -> Tuple[List[int], List[float]]:
    """Monte Carlo run: draw an origin and a detection phase for every fault. Returns (found per phase, cost per phase)."""
    rng = random.Random(seed)
    origins = list(INTRODUCED)
    weights = [INTRODUCED[o] for o in origins]
    found = [0] * len(PHASES)
    for _ in range(faults):
        draw, origin = rng.random(), origins[-1]
        acc = 0.0
        for name, weight in zip(origins, weights):
            acc += weight
            if draw < acc:
                origin = name
                break
        for j in range(PHASES.index(origin), len(PHASES)):
            if rng.random() < detection[j]:
                found[j] += 1
                break
    return found, [f * m for f, m in zip(found, multipliers)]


def print_economics() -> None:
    print("PART 1  The 10% arithmetic with the cost shares of Schach 8e, ch. 1, sec. 1.3.2 (Figures 1.3, 1.4)")
    print()
    print("{:<42} {:>5} {:>7} {:>6} {:>12} {:>10}".format("era", "dev %", "maint %", "code %", "-10% coding", "-10% maint"))
    for (label, development, maintenance, coding), (_, save_coding, save_maint) in zip(ERAS, economics()):
        print("{:<42} {:>5.0f} {:>7.0f} {:>6.0f} {:>11.2f}% {:>9.2f}%".format(
            label, development, maintenance, coding, save_coding, save_maint))
    print("  code % = share of development cost spent on coding + unit testing; savings are % of TOTAL life-cycle cost")
    print("  The 1992-1998 row is the book's 0.85% vs 7.5% (34% of 25% = 8.5% of the total, a tenth of that is 0.85%).")
    print("  Faults: if 60-70% of all faults are requirements/analysis/design faults (ch. 1, sec. 1.4), a 10% reduction of")
    print("  those removes 6-7% of all faults ({:.1f}% to {:.1f}%).".format(0.10 * 60, 0.10 * 70))


def print_simulation(faults: int, seed: int, multipliers: Sequence[float]) -> None:
    print("PART 2  Simulation: {} faults, seed {}   (ILLUSTRATIVE ASSUMPTIONS, not data)".format(faults, seed))
    print("  introduced in: " + ", ".join("{} {:.0%}".format(k, v) for k, v in INTRODUCED.items()))
    print("  cost to fix when found in phase (1 unit = requirements): " + ", ".join(
        "{} {:g}".format(p, round(m, 1)) for p, m in zip(PHASES, multipliers)))
    totals: Dict[str, float] = {}
    for scenario, detection in DETECTION.items():
        found, cost = simulate(detection, multipliers, faults, seed)
        _, exp_cost = expected_cost(detection, multipliers, faults)
        print()
        print("  scenario: {}   detection rate per phase: {}".format(
            scenario, " ".join("{:.0%}".format(d) for d in detection[:-1]) + " (maintenance: all that is left)"))
        print("  {:<15} {:>7} {:>9} {:>11}".format("found in", "faults", "cost", "expected"))
        for j, phase in enumerate(PHASES):
            print("  {:<15} {:>7d} {:>9.0f} {:>11.0f}".format(phase, found[j], cost[j], exp_cost[j]))
        total, exp_total = sum(cost), sum(exp_cost)
        totals[scenario] = total
        print("  {:<15} {:>7d} {:>9.0f} {:>11.0f}".format("total", sum(found), total, exp_total))
        print("  cost per fault {:.1f} units; maintenance share of the cost {:.0%}; faults found by users {:.0%}".format(
            total / faults, cost[-1] / total, found[-1] / faults))
    names = list(DETECTION)
    print()
    print("  inspections cut the total cost to {:.0%} of the test-only process".format(totals[names[1]] / totals[names[0]]))


def parse_multipliers(text: str) -> List[float]:
    values = [float(x) for x in text.split(",")]
    if len(values) != len(PHASES):
        raise argparse.ArgumentTypeError("need exactly {} numbers (one per phase)".format(len(PHASES)))
    return values


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--part", choices=("economics", "simulation", "all"), default="all")
    parser.add_argument("--faults", type=int, default=1000, help="number of faults to inject (default 1000)")
    parser.add_argument("--seed", type=int, default=7, help="random seed (default 7)")
    parser.add_argument("--r", type=float, default=2.5, help="cost growth factor per phase (default 2.5; 2.5^5 is ~98)")
    parser.add_argument("--multipliers", type=parse_multipliers, help="six comma-separated costs, overrides --r")
    args = parser.parse_args(argv)
    multipliers = args.multipliers or multipliers_from_r(args.r)
    if args.part in ("economics", "all"):
        print_economics()
    if args.part == "all":
        print()
    if args.part in ("simulation", "all"):
        print_simulation(args.faults, args.seed, multipliers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
