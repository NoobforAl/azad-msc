"""Compute the four DORA delivery metrics from the Git history of a repository (standard library only).

Usage:
    python dora.py [--repo PATH] [--tag-glob 'v*'] [--date author|committer] [--json]

What the script treats as what (read the limits in the lab README before trusting the numbers):
    deployment            an annotated or lightweight tag that matches --tag-glob (default v*)
    commit time           author date (when the work was written) or committer date (when it was last rewritten)
    failed deployment     a tag named by a "Fixes-release: <tag>" trailer in some later commit
    restored              the first tag that contains such a fixing commit
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

TRAILER = "Fixes-release"
HOUR = 3600.0
NEWLINE = chr(10)


def git(repo: str, *args: str) -> str:
    """Run a git command in repo and return its stdout (raises on a non-zero exit code)."""
    result = subprocess.run(
        ["git", "-C", repo] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )
    if result.returncode != 0:
        raise RuntimeError("git {} failed: {}".format(" ".join(args), result.stderr.strip()))
    return result.stdout


def list_releases(repo: str, tag_glob: str) -> List[Tuple[str, int]]:
    """Return (tag, unix time) pairs sorted by time. The time is the tagger date, or the commit date if lightweight."""
    out = git(repo, "for-each-ref", "refs/tags/" + tag_glob, "--format=%(refname:short) %(creatordate:unix)")
    releases = []
    for line in out.splitlines():
        name, stamp = line.rsplit(" ", 1)
        releases.append((name, int(stamp)))
    return sorted(releases, key=lambda item: (item[1], item[0]))


def commits_between(repo: str, previous: Optional[str], tag: str, date_kind: str) -> List[Dict[str, Any]]:
    """Commits reachable from tag but not from previous: hash, commit time, and Fixes-release targets."""
    stamp = "%at" if date_kind == "author" else "%ct"
    fmt = "%H%x1f{}%x1f%(trailers:key={},valueonly,separator=%x2c)%x1e".format(stamp, TRAILER)
    rev = tag if previous is None else "{}..{}".format(previous, tag)
    out = git(repo, "log", "--no-merges", "--format=" + fmt, rev)
    commits = []
    for record in out.split("\x1e"):
        record = record.strip(NEWLINE)  # not str.strip(): it would also strip the trailing unit separator
        if not record:
            continue
        sha, when, fixes = record.split("\x1f")
        targets = [t.strip() for t in fixes.replace("\n", ",").split(",") if t.strip()]
        commits.append({"sha": sha, "time": int(when), "fixes": targets})
    return commits


def percentile(values: List[float], pct: float) -> float:
    """Nearest-rank percentile (no interpolation), good enough for small samples."""
    ordered = sorted(values)
    rank = max(1, int(-(-pct * len(ordered) // 100)))
    return ordered[rank - 1]


def fmt_hours(hours: float) -> str:
    days, rest = divmod(hours, 24)
    if days >= 1:
        return "{:.1f} h ({:d} d {:.1f} h)".format(hours, int(days), rest)
    return "{:.1f} h".format(hours)


def analyse(repo: str, tag_glob: str, date_kind: str) -> Dict[str, Any]:
    releases = list_releases(repo, tag_glob)
    if not releases:
        raise SystemExit("no tags match {!r} in {}".format(tag_glob, repo))
    release_time = dict(releases)
    lead_hours: List[float] = []
    fixes_by_release: Dict[str, List[str]] = {}
    previous: Optional[str] = None
    for tag, when in releases:
        for commit in commits_between(repo, previous, tag, date_kind):
            lead_hours.append((when - commit["time"]) / HOUR)
            for target in commit["fixes"]:
                fixes_by_release.setdefault(target, []).append(tag)
        previous = tag

    failed = sorted(t for t in fixes_by_release if t in release_time)
    restore_hours = []
    for tag in failed:
        first_fix = min(fixes_by_release[tag], key=lambda t: release_time[t])
        restore_hours.append((release_time[first_fix] - release_time[tag]) / HOUR)

    span_days = (releases[-1][1] - releases[0][1]) / 86400.0
    per_week = Counter(datetime.fromtimestamp(w, timezone.utc).isocalendar()[:2] for _, w in releases)
    total_commits = int(git(repo, "rev-list", "--count", "--no-merges", "HEAD").strip())
    unreleased = int(git(repo, "rev-list", "--count", "--no-merges", "{}..HEAD".format(releases[-1][0])).strip())

    result: Dict[str, Any] = {}
    result["repo"] = os.path.basename(os.path.abspath(repo))
    result["commit_time"] = date_kind + " date"
    result["deployments"] = len(releases)
    result["first_deployment"] = datetime.fromtimestamp(releases[0][1], timezone.utc).strftime("%Y-%m-%d %H:%M")
    result["last_deployment"] = datetime.fromtimestamp(releases[-1][1], timezone.utc).strftime("%Y-%m-%d %H:%M")
    result["span_days"] = round(span_days, 1)
    result["deployments_per_week"] = round(len(releases) / (span_days / 7.0), 2) if span_days else None
    result["weeks_with_a_deployment"] = len(per_week)
    result["lead_time_commits"] = len(lead_hours)
    result["lead_time_median_h"] = round(statistics.median(lead_hours), 1)
    result["lead_time_mean_h"] = round(statistics.mean(lead_hours), 1)
    result["lead_time_p90_h"] = round(percentile(lead_hours, 90), 1)
    result["failed_deployments"] = failed
    result["change_failure_rate"] = round(len(failed) / len(releases), 3)
    result["time_to_restore_h"] = [round(h, 1) for h in restore_hours]
    result["time_to_restore_median_h"] = round(statistics.median(restore_hours), 1) if restore_hours else None
    result["commits_total"] = total_commits
    result["commits_unreleased"] = unreleased
    return result


def print_report(m: Dict[str, Any]) -> None:
    print("DORA metrics for {}".format(m["repo"]))
    print("(deployment = tag matching the glob, commit time = {})".format(m["commit_time"]))
    print()
    print("Deployment frequency")
    print("  deployments            {}  ({} to {}, {} days)".format(
        m["deployments"], m["first_deployment"], m["last_deployment"], m["span_days"]))
    print("  per week               {}  (in {} different weeks)".format(
        m["deployments_per_week"], m["weeks_with_a_deployment"]))
    print("Lead time for changes  ({} released commits, commit -> first tag containing it)".format(
        m["lead_time_commits"]))
    print("  median                 {}".format(fmt_hours(m["lead_time_median_h"])))
    print("  mean                   {}".format(fmt_hours(m["lead_time_mean_h"])))
    print("  90th percentile        {}".format(fmt_hours(m["lead_time_p90_h"])))
    print("Change failure rate")
    print("  failed deployments     {} of {}  {}".format(
        len(m["failed_deployments"]), m["deployments"], ", ".join(m["failed_deployments"])))
    print("  rate                   {:.0%}".format(m["change_failure_rate"]))
    print("Time to restore service")
    for tag, hours in zip(m["failed_deployments"], m["time_to_restore_h"]):
        print("  {:<22} {}".format(tag, fmt_hours(hours)))
    if m["time_to_restore_median_h"] is not None:
        print("  median                 {}".format(fmt_hours(m["time_to_restore_median_h"])))
    print("Not measured")
    print("  {} of {} commits are not in any release yet (they have no lead time)".format(
        m["commits_unreleased"], m["commits_total"]))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", default=".", help="path of the Git repository (default: current directory)")
    parser.add_argument("--tag-glob", default="v*", help="tags that count as deployments (default: v*)")
    parser.add_argument("--date", choices=("author", "committer"), default="author", help="which commit date to use")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead of the report")
    args = parser.parse_args(argv)
    metrics = analyse(args.repo, args.tag_glob, args.date)
    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print_report(metrics)
    return 0


if __name__ == "__main__":
    sys.exit(main())
