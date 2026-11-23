# Lab 01.3 — What does a late fault cost? Simulation and the 0.85% vs 7.5% argument

**Goal:** reproduce Schach's economic argument (a 10% saving in coding is worth at most 0.85% of total cost, a 10% saving in postdelivery maintenance about 7.5%) and simulate how the phase in which a fault is found changes the total cost.

Runs on: Python >= 3.8, nothing else (stdlib only). Time: 45 min. Difficulty: easy.

## Starting state

- Module state `m0`: no project files are used. This lab is a model, not a change to `project/`. (To keep one habit for the whole module: do it in any directory, for example the scratch directory of lab 02.)
- Ending state: `fault_cost.py` and your written answers. The script joins the `m1` toolbox as `tools/fault_cost.py` (see [`../README.md`](../README.md)).

## Read this first: which numbers are data and which are assumptions

| Number | Status |
|---|---|
| maintenance 67% (1976-1981) and 75% (1992-1998) of total cost; development 33% and 25% | from Schach 8e, ch. 1 §1.3.2, Figure 1.3. Checked against the book text. |
| coding with unit testing = 36% (1976-1981) and 34% (132 Hewlett-Packard projects) of development cost | from Schach 8e, ch. 1 §1.3.2, Figure 1.4. Checked. |
| 0.85% and 7.5% | Schach's own arithmetic (§1.3.2, p. 12): 34% of 25% is 8.5% of total cost, a tenth of that is 0.85%; a tenth of 75% is 7.5%. Reproduced here. |
| 60-70% of faults found in large projects are requirements, analysis or design faults | Schach 8e, ch. 1 §1.4, citing Boehm 1979 (not opened by us). |
| cost multiplier per phase (`--r 2.5`, so 1, 2.5, 6.2, 15.6, 39.1, 97.7) | **ILLUSTRATIVE ASSUMPTION.** Schach's Figure 1.5 (after Boehm 1981) shows relative cost rising steeply from requirements to maintenance, to roughly a factor of 100 on a log axis (our reading of the figure, `UNVERIFIED` as a number). The constant factor 2.5 is invented so that five steps give about 100. |
| fault mix 35/30/35% and the detection rates per phase | **ILLUSTRATIVE ASSUMPTION** (the 65% for requirements and design sits inside the book's 60-70%; everything else is made up). |

Nothing in the simulation output is a measurement. It shows how the conclusion depends on the assumptions.

Schach says the cost of fixing a fault rises steeply with the phase in which it is found. Modern practice says the *shape* is `OPINION / CONTESTED`: the old data come from large 1970s projects; with continuous delivery and feature flags the cost of fixing a bug after release can be small. Keep this in mind in "What to observe".

## Steps

```bash
cd term-1/advanced-software-engineering/01-processes/labs/03-cost-of-fault-simulation
python fault_cost.py                              # both parts
python fault_cost.py --part economics             # the 0.85% / 7.5% table only
python fault_cost.py --part simulation --faults 100000     # law of large numbers: simulation vs expected value
python fault_cost.py --part simulation --r 1      # flat cost: what is left of the argument?
python fault_cost.py --part simulation --r 4      # steeper cost curve
python fault_cost.py --part simulation --multipliers 1,1,1,1,1,1000    # only the user-found fault is expensive
```

Linux / macOS: use `python3` if needed. The output is the same on every platform (the random generator is seeded; `random.random()` gives the same sequence on every Python 3 version).

**Your task:** (1) compute by hand the savings for the 1976-1981 row and compare; (2) find the value of `--r` below which the inspection process saves less than 20% of the total cost; (3) write two sentences on why the maintenance share of the *fault-fixing* cost in the simulation (about 57%) is not the same thing as Schach's 67-75% share of *life-cycle* cost. Compare with [`solution/answers.md`](solution/answers.md).

## Code

[`fault_cost.py`](fault_cost.py):

- `economics()` multiplies the cost shares of the two eras; this is the book's arithmetic.
- `simulate()` is a Monte Carlo run: for each fault draw the phase where it is introduced, then walk through the later phases and let each one catch it with the phase's detection rate; the fault costs the multiplier of the phase that caught it.
- `expected_cost()` computes the same thing exactly, as a cross-check (the `expected` column).

## Expected output

Captured on Windows 11, Git Bash, Python 3.12, 2026-11-23. Same on Linux and macOS.

```text
$ python fault_cost.py
PART 1  The 10% arithmetic with the cost shares of Schach 8e, ch. 1, sec. 1.3.2 (Figures 1.3, 1.4)

era                                        dev % maint % code %  -10% coding -10% maint
1976-81 projects (Fig. 1.3a, 1.4)             33      67     36        1.19%      6.70%
1992-98, 132 HP projects (Fig. 1.3b, 1.4)     25      75     34        0.85%      7.50%
  code % = share of development cost spent on coding + unit testing; savings are % of TOTAL life-cycle cost
  The 1992-1998 row is the book's 0.85% vs 7.5% (34% of 25% = 8.5% of the total, a tenth of that is 0.85%).
  Faults: if 60-70% of all faults are requirements/analysis/design faults (ch. 1, sec. 1.4), a 10% reduction of
  those removes 6-7% of all faults (6.0% to 7.0%).

PART 2  Simulation: 1000 faults, seed 7   (ILLUSTRATIVE ASSUMPTIONS, not data)
  introduced in: requirements 35%, design 30%, implementation 35%
  cost to fix when found in phase (1 unit = requirements): requirements 1, design 2.5, implementation 6.2, integration 15.6, acceptance 39.1, maintenance 97.7

  scenario: test only at the end   detection rate per phase: 0% 0% 30% 40% 50% (maintenance: all that is left)
  found in         faults      cost    expected
  requirements          0         0           0
  design                0         0           0
  implementation      308      1925        1875
  integration         297      4641        4375
  acceptance          201      7852        8203
  maintenance         194     18945       20508
  total              1000     33362       34961
  cost per fault 33.4 units; maintenance share of the cost 57%; faults found by users 19%

  scenario: with inspections   detection rate per phase: 40% 40% 30% 40% 50% (maintenance: all that is left)
  found in         faults      cost    expected
  requirements        167       167         140
  design              192       480         510
  implementation      200      1250        1230
  integration         191      2984        2870
  acceptance          140      5469        5381
  maintenance         110     10742       13453
  total              1000     21092       23584
  cost per fault 21.1 units; maintenance share of the cost 51%; faults found by users 11%

  inspections cut the total cost to 63% of the test-only process
```

With `--faults 100000` the simulated totals approach the expected values (3,492,184 vs 3,496,094 in the test-only scenario) and the inspections ratio is 67%. With `--r 1` (every phase costs the same) the ratio is 100%; with `--r 4` it is 60%.

## What to observe

1. **The book's arithmetic holds for both eras, and the lesson is the same.** Coding is a small slice of total cost (8.5% in the newer data, 11.9% in the older), so a technique that speeds up coding by 10% saves 0.85% to 1.19%; the same 10% on maintenance saves 6.7% to 7.5%. The argument is about *where the money is*, not about coding being unimportant.
2. **Inspections move cost from the right to the left of the table.** In the second scenario 167 + 192 faults are found for 1 and 2.5 units each instead of leaking into expensive phases, and the faults found by users fall from 19% to 11%.
3. **The simulation noise is visible.** At 1000 faults the `cost` and `expected` columns differ by about 5% (33,362 vs 34,961). At 100,000 they differ by 0.1%. One run of a small simulation is an anecdote.
4. **The conclusion is only as good as the cost curve.** With `--r 1` inspections save nothing (100%), because a fault is as cheap in maintenance as in requirements. Everything the model says about early fault detection comes from the assumed multipliers; this is exactly why they are labelled as assumptions and why the real shape (`OPINION / CONTESTED` today) matters.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| numbers differ from this README after you edit the model | the seed is fixed, so only your edits change the output | `git diff fault_cost.py`; keep the three `INTRODUCED` values summing to 1 |
| `--multipliers` is rejected | it needs exactly six comma-separated numbers, one per phase | `--multipliers 1,2,4,8,16,32` |
| a requirements fault found in implementation costs the same as an implementation fault | the model charges by the phase where the fault is *found* | extension task |
| you quote "57% of cost is maintenance" as if it were Schach's number | the simulation counts only fault-fixing cost; Schach's 67-75% covers all postdelivery work (corrective, perfective, adaptive) | read §1.3.1-§1.3.2 |

## Extension task

Make the cost depend on both the phase where the fault was *introduced* and the phase where it was *found* (a requirements fault found late must change documents, design and code; a coding fault only code). Choose and justify a rule, rerun both scenarios and say which conclusion of this lab survives. No solution is provided for this task.

Solution of the lab: [`solution/`](solution/) (`expected-report.txt`, `answers.md`).
