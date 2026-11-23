# 01 · Processes — lesson deck outline

Design system: `_shared/slide-design-system.md` v3 · theme: `_shared/theme/azad-theme.css` + `azad-deck.js` · roles: Advanced Software Engineering (client = teal, service = amber, infrastructure = violet, data/storage = green). This file covers the **lesson deck**; the lab decks are described by `labs.content.py` (not edited here).

| Deck | EN | FA | Slides |
|---|---|---|---|
| Lesson | [`lesson.en.html`](lesson.en.html) | [`lesson.fa.html`](lesson.fa.html) | 17 |

Open it through a local web server so the relative theme path resolves: `python -m http.server` at the repo root, then `http://127.0.0.1:8000/term-1/advanced-software-engineering/01-processes/slides/lesson.en.html`. Press `S` for speaker notes, add `?print-pdf` for PDF export. Sources: `../lesson.en.md`, `../case-study.en.md`, `../notes/`.

## Slide 1 — TITLE
Title: Software processes and life-cycle models · Fields: placeholders from §3.4 (never invented)

## Slide 2 — SECTION
Eyebrow: Module 01 · Title: Processes · Why: every model answers a failure of the one before it; the numbers say which failures cost most · Pills: economics · models · evidence

## Slide 3 — AGENDA
Five questions: economics → vocabulary → models → Linux and OpenBSD → evidence (current = 1)

## Slide 4 — DATA_CHART
Title: A 10% saving in maintenance is worth about nine times a 10% saving in coding
Chart: `assets/economics.svg`, two bars (coding 10% cheaper = 0.85%, maintenance 10% cheaper = 7.5% of total life-cycle cost); coding = service/amber, maintenance = infrastructure/violet
Source: Schach 8e, ch. 1 §1.3.2, p. 12 (34% of 25% = 8.5%; maintenance 75%)
Notes: the shares are industry averages from older data; measure your own

## Slide 5 — CONCEPT_DIAGRAM
Title: Real projects iterate and increment in every workflow
Diagram: `assets/iterative-incremental.svg`: rows = five workflows, columns = three builds; artifacts get a new version per build (iteration, gold arrows), implementation adds a feature per build (incrementation), tests accumulate
Callouts: ① each build adds a piece ② each artifact gets better ③ every build runs the tests
Source: Schach 8e, ch. 2 §2.5, §2.7 (cell labels are illustrative)

## Slide 6 — TWO_COLUMN_COMPARE
Iteration (rewrite after a load test, revised design, refactoring commits) vs Incrementation (tagged releases, each build adds functionality, feature merged with passing tests)

## Slide 7 — TWO_COLUMN_COMPARE
Plan-driven (documents and sign-off, stable requirements, wrong product found late) vs Agile (short feedback loop, unclear needs, evidence mostly observational)

## Slide 8 — QUOTE / DEFINITION
Royce draws the straight-line sequence, then says implementing it "is risky and invites failure" · Source: Royce 1970, IEEE WESCON, pp. 1-9 (opened as a reprint on 2026-11-23) · Schach 8e, ch. 2 §2.9.2 · Boehm 1988 NOT opened (UNVERIFIED, said in the notes)

## Slide 9 — FLOW_TIMELINE
Unified Process phases: Inception → Elaboration → Construction → Transition (fragment moves the highlight; all steps always visible) · Takeaway: the spiral asks one question per loop · Source: Schach 8e, ch. 3 §3.10

## Slide 10 — CODE_WALKTHROUGH
Source: `linux/Documentation/process/2.Process.rst · merge window · v6.18.63 · L49-55` (7 lines, copied with `sed -n 49,55p`)
Highlights: ① about two weeks ② `-rc1` is the signal ③ stabilize the next kernel · Callouts: big changes in a bounded window / -rc1 closes it / then fixes only

## Slide 11 — CODE_WALKTHROUGH
Source: `openbsd/share/man/man9/style.9 · DESCRIPTION · 8cada8c · L38-43` (6 lines, copied with `sed -n 38,43p`)
Highlights: ① "should be followed for all new code" ② new code = 50% or more of the file ③ enough to break precedents

## Slide 12 — TWO_COLUMN_COMPARE
Linux v6.18.63 vs OpenBSD 8cada8c: release rhythm, style authority, style on old code, form of the document · Takeaway: OpenBSD review and commit rules are UNVERIFIED (case study §6)

## Slide 13 — BENTO
Five DORA metrics: change lead time · deployment frequency · failed-deployment recovery time · change fail rate · deployment rework rate · Takeaway: diagnostics, not targets; VERSION-DEPENDENT (dora.dev page of 2026-01-05)

## Slide 14 — BENTO
Choosing a model: stable/safety-critical → plan-driven · large/risky → spiral or UP · unclear needs → agile · unpredictable arrival → Kanban · Takeaway: mix, with agile inside and plan-driven gates around · Source: Schach 8e, ch. 2 §2.10

## Slide 15 — QUIZ
A team adds one endpoint per sprint and never touches the design. A iteration · **B incrementation** · C both · D neither

## Slide 16 — DEFINITION (answer)
Adding pieces is incrementation; reworking one is iteration · Source: Schach 8e, ch. 2 §2.5 · lesson §2.3

## Slide 17 — SUMMARY
① maintenance dominates cost, so order is an economic decision ② iterate to improve, increment to add ③ read real processes, judge changes with metrics · Next: Module 02

## Build notes

- **Excerpts:** the two code slides were copied from `_shared/sources/` with `sed -n` (Linux `2.Process.rst` lines 49-55; OpenBSD `style.9` lines 38-43) and match the line numbers in `case-study.en.md`.
- **Illustrative content:** the cell labels in the iteration/incrementation diagram and the Team A/B example in the speaker notes of slide 13 are illustrative, not data; both are said so on the slide or in the notes.
- **Logo:** `_shared/brand/azad-logo.svg` is used if present; otherwise `azad-deck.js` shows the dashed placeholder.
