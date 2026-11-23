# Lab 01.5 — reference answers

Produced with `python gen_issues.py --wip-limit L > limit-L.csv` and `python flow_metrics.py limit-L.csv` for each `L` (same 55 issues in every run, 12 weeks from 2026-03-02).

| WIP limit | issues done | throughput / week | mean cycle time (d) | p85 cycle (d) | mean lead time (d) | average WIP |
|---|---|---|---|---|---|---|
| 1 | 16 | 1.33 | 4.6 | 10 | 28.1 | 1.00 |
| 2 | 30 | 2.50 | 4.8 | 10 | 19.5 | 1.95 |
| 3 | 52 | 4.33 | 3.9 | 6 | 8.9 | 2.83 |
| 4 | 52 | 4.33 | 5.5 | 8 | 9.2 | 3.67 |
| 5 | 52 | 4.33 | 6.6 | 13 | 9.3 | 4.38 |
| 6 | 52 | 4.33 | 7.5 | 13 | 9.1 | 5.07 |
| none | 51 | 4.25 | 9.9 | 18 | 9.9 | 6.55 |

Decision: **3**, the team size. Below it throughput collapses (the team is idle although work waits), above it throughput stays the same while cycle time grows with every extra item (Little's law: same throughput, more WIP, longer cycle time). The lead time is almost flat from 3 to 6 because the same work is waiting either in the backlog or on the board; WIP limits move the waiting to where it is visible and cheap, they do not remove it.

Caveats to state in an answer: the table is one run of a synthetic model with 55 issues (no confidence interval); the cycle time at limits 1 and 2 looks short because only the issues that finished are counted (the long ones are still open or not started); the best limit equals the team size only because the model lets one developer work on one issue.
