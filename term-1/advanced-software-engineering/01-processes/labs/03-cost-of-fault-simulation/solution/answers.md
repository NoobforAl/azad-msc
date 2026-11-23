# Lab 01.3 — reference answers

`expected-report.txt` is the output of `python fault_cost.py` (seed 7, 1000 faults, `--r 2.5`).

1. **By hand, 1976-1981 row.** Development is 33% of total cost and coding with unit testing is 36% of development, so coding is 0.33 x 0.36 = 11.9% of the total; a 10% saving is 1.19%. Maintenance is 67% of the total; a 10% saving is 6.7%. The 1992-1998 row gives 0.34 x 0.25 = 8.5% and 0.85%, and 7.5%, the numbers in the book (§1.3.2). The script prints the same values.
2. **Threshold for `--r`.** Using the exact expected values (`expected_cost`, no sampling noise) the inspection process costs 80.0% of the test-only process at `r` = 1.35, so below `r` of about 1.35 it saves less than 20%. At `r` = 1.3 the ratio is 81.8%, at 1.4 it is 78.5%, at the default 2.5 it is 67.5%. A simulation run with `--faults 100000 --r 1.3` gives 82%, `--r 1.4` gives 78%. With 1000 faults the noise (about 5%) is larger than the difference between neighbouring values of `r`.
3. **Why 57% is not 67-75%.** The simulation adds up only the cost of finding and fixing faults, and it charges the faults that users find at the maintenance multiplier. Schach's postdelivery maintenance share counts all work after delivery, including perfective and adaptive changes (new features, new platforms) that have nothing to do with a fault. So the two numbers answer different questions, and the model's 57% depends on assumptions (detection rates, multipliers) while the book's shares are reported averages.

Observation to keep: all conclusions about *early* detection come from the multipliers, which are assumptions. With `--r 1` the ratio is exactly 100%.
