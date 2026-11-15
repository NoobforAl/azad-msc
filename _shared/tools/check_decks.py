"""Sanity-check every slide deck: speaker notes on every slide, a <title>, theme paths resolve.

Usage: python _shared/tools/check_decks.py   (exit code = number of decks with problems)
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
bad = 0
decks = sorted(ROOT.glob("term-*/*/*/slides/*.html")) + sorted(ROOT.glob("term-*/*/*/slides/labs/*.html"))
for deck in decks:
    s = deck.read_text(encoding="utf-8")
    problems = []
    # Top-level slides: <section ...> not nested in a vertical stack (decks here are flat).
    sections = len(re.findall(r"<section\b", s))
    notes = len(re.findall(r'<aside class="notes"', s))
    if sections == 0:
        problems.append("no <section> slides")
    elif notes < sections:
        problems.append(f"{sections - notes} slide(s) without speaker notes ({notes}/{sections})")
    if not re.search(r"<title>[^<]+</title>", s):
        problems.append("missing <title>")
    for ref in re.findall(r'(?:href|src)="(\.\.[^"#?]+)"', s):
        target = (deck.parent / ref).resolve()
        if not target.exists() and "brand/azad-logo" not in ref:  # logo is optional (placeholder)
            problems.append(f"broken path {ref}")
    if problems:
        bad += 1
        print(f"FAIL {deck.relative_to(ROOT).as_posix()}: " + "; ".join(sorted(set(problems))))
print(f"{len(decks)} decks checked, {bad} with problems")
sys.exit(bad)
