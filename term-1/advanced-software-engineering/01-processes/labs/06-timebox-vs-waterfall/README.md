# Lab 01.6 — Timeboxed sprints vs a waterfall plan for the project backlog

**Goal:** plan the same backlog of the Course Registration Platform as a waterfall project and as 3-week timeboxes, then see what each plan delivers by the deadline when the estimates turn out wrong.

Runs on: Python >= 3.8 (stdlib only). Time: 45 min. Difficulty: medium (a written exercise with a script).

## Starting state

- Module state `m0`: the project skeleton exists; this lab plans the *next* work on it and changes no code. The backlog (`backlog.csv`) is a made-up list of 12 features for the next releases of the platform.
- Ending state: `plan_compare.py`, `backlog.csv` and your written comparison; the script joins `m1` as `tools/plan_compare.py` (see [`../README.md`](../README.md)).

## Read this first: what is data and what is assumed

Everything in the model is an **assumption of this lab**, not data about real projects:

| Input | Value | Source |
|---|---|---|
| backlog, priorities, value points, estimates (100 developer-days in total, 68 value points) | invented for the exercise | `backlog.csv` |
| team of 3 developers, 80% focus (12 developer-days per week) | invented | `--devs`, `--focus` |
| waterfall phase shares: requirements 18%, design 19%, coding with unit testing 34%, integration 29% | the average cost percentages of 132 Hewlett-Packard projects, Schach 8e, ch. 1 §1.3.2, Figure 1.4. Reused here as an assumption about how a waterfall project spends its time (the book gives them as cost shares of the classical development phases, not as a schedule). | checked against the book |
| timebox of 3 weeks | Schach 8e, ch. 2 §2.9.5, p. 60: the book mentions delivering working software every 2 or 3 weeks and timeboxing as a way to do it | checked against the book |
| `--overrun` (share by which real effort exceeds the estimate) | a parameter you vary | `--overrun` |

Schach (ch. 2 §2.9.2, §2.9.5) presents the waterfall model and agile processes as alternatives to be chosen by project type, and ch. 2 §2.10 compares them. The model here is deliberately crude: items are independent and can be delivered one by one, value is a fixed number per item, and no requirement changes. It shows *one* effect, the **fixed time, variable scope** trade of a timebox. It cannot show waterfall's strengths (less coordination overhead on stable, well-understood problems) and it ignores the cost of agile overhead (planning, reviews). Which is better is `OPINION / CONTESTED` and depends on the project.

## Steps

```bash
cd term-1/advanced-software-engineering/01-processes/labs/06-timebox-vs-waterfall
cat backlog.csv
python plan_compare.py                              # estimates are exact
python plan_compare.py --overrun 0.3                # every item takes 30% longer than estimated
python plan_compare.py --overrun 0.6
for o in 0.08 0.09; do python plan_compare.py --overrun $o | grep -E "everything|items delivered"; done
python plan_compare.py --deadline-weeks 12 --timebox-weeks 2 --overrun 0.3     # shorter timeboxes
```

**Your task:** (1) at which overrun does the waterfall plan first miss the 9-week deadline? Derive it by hand from the numbers in the output, then confirm it with the last loop. (2) Explain why, at the overrun you found, the timeboxed plan delivers *fewer* items than the waterfall plan. (3) With `--overrun 0.3`, write three sentences for the client: what do they get in week 3, week 6 and week 9 under each plan, and what is missing? Compare with [`solution/answers.md`](solution/answers.md).

Linux / macOS: use `python3` if needed; the output is identical.

## Code

[`plan_compare.py`](plan_compare.py):

- `waterfall()`: total real effort divided by the weekly capacity gives the length; the four phases take their fixed shares of it; all items are delivered at the end.
- `timeboxed()`: for each sprint, plan by estimate (highest priority first, first fit into the capacity), execute with the real effort, deliver what is finished, **cut** what is not (it returns to the backlog with its progress).
- `summary()`: value delivered at each timebox boundary, as a share of the 68 value points.

## Expected output

Captured on Windows 11, Git Bash, Python 3.12, 2026-11-23.

```text
$ python plan_compare.py
Backlog backlog.csv: 12 items, 100 developer-days estimated, 68 value points
Team: 3 developers, focus 80% = 12.0 developer-days per week. Deadline: week 9.
Real effort = estimate x 1.00  (overrun 0%)

WATERFALL  (phase shares: Schach 8e ch. 1 Fig. 1.4, 132 HP projects, used as an assumption)
  requirements         week   0.0 ->   1.5
  design               week   1.5 ->   3.1
  coding + unit tests  week   3.1 ->   5.9
  integration          week   5.9 ->   8.3
  everything is delivered at week 8.3 (meets the deadline); nothing is delivered earlier

TIMEBOXED  (3 sprints of 3 weeks, capacity 36.0 developer-days per sprint, plans use the estimates)
  sprint 1 (week 3): committed 36.0 d  delivered REG-01, REG-02, REG-03, REG-04  cut -
  sprint 2 (week 6): committed 34.0 d  delivered REG-05, REG-06, REG-07, REG-08  cut -
  sprint 3 (week 9): committed 30.0 d  delivered REG-09, REG-10, REG-11, REG-12  cut -
  not delivered at the deadline: -

SUMMARY
                                  waterfall  timeboxed
  value delivered by week 3              0%        62%
  value delivered by week 6              0%        88%
  value delivered by week 9            100%       100%
  items delivered at the deadline      12/12      12/12
  first delivery (week)                 8.3          3

$ python plan_compare.py --overrun 0.3
...
WATERFALL  (phase shares: Schach 8e ch. 1 Fig. 1.4, 132 HP projects, used as an assumption)
  everything is delivered at week 10.8 (MISSES the deadline by 1.8 weeks); nothing is delivered earlier

TIMEBOXED  (3 sprints of 3 weeks, capacity 36.0 developer-days per sprint, plans use the estimates)
  sprint 1 (week 3): committed 36.0 d  delivered REG-01, REG-02, REG-03  cut REG-04
  sprint 2 (week 6): committed 32.3 d  delivered REG-04, REG-05, REG-06  cut REG-08
  sprint 3 (week 9): committed 35.6 d  delivered REG-07, REG-08, REG-09, REG-10  cut REG-12
  not delivered at the deadline: REG-11, REG-12

SUMMARY
                                  waterfall  timeboxed
  value delivered by week 3              0%        50%
  value delivered by week 6              0%        76%
  value delivered by week 9              0%        96%
  items delivered at the deadline       0/12       10/12
  first delivery (week)                10.8          3

$ for o in 0.08 0.09; do python plan_compare.py --overrun $o | grep -E "everything|items delivered"; done
  everything is delivered at week 9.0 (meets the deadline); nothing is delivered earlier
  items delivered at the deadline      12/12      11/12
  everything is delivered at week 9.1 (MISSES the deadline by 0.1 weeks); nothing is delivered earlier
  items delivered at the deadline       0/12      11/12
```

The full reports of three runs are in [`solution/`](solution/) (`expected-overrun-0.txt`, `-30.txt`, `-60.txt`).

## What to observe

1. **With exact estimates both plans deliver everything; only the timing differs.** The timeboxed plan has delivered 62% of the value by week 3 and the waterfall plan delivers its first (and only) release at week 8.3.
2. **A 30% overrun turns the waterfall into a miss.** It finishes at week 10.8 and delivers nothing at the deadline, while the timeboxed plan keeps its dates, delivers 10 of 12 items (96% of the value) and tells the client exactly which two are missing (REG-11, REG-12, the lowest priorities). Fixed time and variable scope is the timebox principle: what is cut is decided by priority, not by whatever happens to be unfinished.
3. **At 60% overrun the timebox still delivers 7 of 12 items (84% of the value)**; the waterfall would finish at week 13.3.
4. **The timebox is not free.** At an overrun of only 8%, the waterfall just meets the deadline (week 9.0) with 12 of 12 items while the timeboxed plan delivers 11 of 12: items must fit whole into a sprint, so a little capacity is left unused or an item is cut. If the deadline is firm and scope is not, a timebox gives up some capacity to gain control.
5. **What the model does not show.** Requirements changes, integration risk at the end of a waterfall project, rework, the cost of sprint ceremonies and the value of early feedback. Lab 03 models one of them (the cost of finding a fault late). The conclusion "timeboxing is better" does **not** follow from this lab alone.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| the waterfall always "misses" in your own backlog | total estimate exceeds capacity x deadline | compare `sum(estimate) / 12` with the deadline before running |
| the timeboxed plan delivers less than its capacity | whole items must fit; the first-fit rule skips big items | allow splitting an item (extension) or reorder the backlog |
| `ValueError: could not convert string to float` | a comma in a title shifted the CSV columns | quote titles that contain commas |
| `FileNotFoundError: backlog.csv` | you ran the script from another directory | pass the path: `python plan_compare.py path/to/backlog.csv` |
| you quote the value percentages as results | the values are invented | say "in this model" |
| the waterfall plan is blamed for the overrun | the same overrun hits both plans; they differ in what happens next | compare the *consequences*, not the overrun |

## Extension task

Add a mid-flight change: `--new-item "ID:title:priority:value:estimate" --at-week N` injects an urgent item. In the timeboxed plan it competes for the next sprint; in the waterfall plan it forces a replan (decide and justify what happens to the phases already finished: for a requirements change after week 4 the work of the requirements and design phases is partly lost). Compare the two plans for an urgent 10-day item arriving in week 4, and say which assumption of yours decides the result. No solution is provided for this task.

Solution of the lab: [`solution/`](solution/) (expected reports and `answers.md`).
