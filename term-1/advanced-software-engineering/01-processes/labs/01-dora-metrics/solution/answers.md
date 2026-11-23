# Lab 01.1 — reference answers

Reports: `expected-report.txt` (author dates) and `expected-report-committer.txt` (committer dates), produced by `dora.py` on the repository built by `seed_repo.sh`.

1. **Longest repair.** `v0.6.0` (126 h = 5 d 6 h). The release was tagged on 04-09 10:00; the fix commit was written on Monday 04-13 10:00 (after a weekend) and shipped in `v0.6.1` on 04-14 16:00. About 96 of the 126 hours pass before anyone writes the fix (Thursday to Monday), which is what time to restore measures in practice: detection plus queueing plus fixing plus shipping.
2. **Author vs committer date.** "Add CSV export" has author date 03-17 11:00 and committer date 03-18 09:00; it ships in `v0.3.0` (03-19 14:00), so its lead time is 51 h or 29 h. The median over all 30 commits drops from 46.5 h to 45.5 h, the mean from 55.6 h to 54.9 h. The percentile (119 h) does not move.
3. **Without trailers.** The script finds no `Fixes-release:` trailer, so `failed deployments` is empty and the rate is 0%. The three repairs still happened; only your convention changed. Time to restore has no data either.
4. **Not measured.** 2 of 32 commits have no lead time. Hand check for `v0.1.0`: the first commit ("Add course list endpoint", 03-02 09:00) shipped on 03-05 10:00, i.e. 73 h.

Other numbers you can verify by hand with `git log`: 11 tags in 50.2 days is 1.53 per week; 3 failed of 11 is 27%; the median restore time of 22.5 h, 24.0 h and 126.0 h is 24.0 h.
