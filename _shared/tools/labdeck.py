"""Render lab decks (EN + FA) from one content file.

Usage:  python _shared/tools/labdeck.py <module>/slides/labs.content.py

The content file defines:
  COURSE = {"en": "...", "fa": "..."}          footer text
  LABS   = [dict(slug, num, title, goal, where, setup_cards, steps,
                 expected, observe, pitfalls, ext, captured=None), ...]
Every text field is {"en": ..., "fa": ...}. If en == fa it is treated as code.
`captured` (optional, {"en","fa"}): where/when the expected output was really
captured. Without it the slide says EXPECTED (quality rule 2).
Decks are written to <content dir>/labs/<slug>.<lang>.html.
Structure (agent-prompt §6): Goal → Setup → Steps → Expected → Observe → Pitfalls → Extension.
"""

import html
import pathlib
import re
import runpy
import sys

_LTR = re.compile(r'([A-Za-z0-9_$"./=+:(*#<>\-][A-Za-z0-9_$"./=+:()*#<>\- ]*[A-Za-z0-9_$"./=+:)*#<>\-]|[A-Za-z0-9])')


def tx(text):
    """In mixed Persian text, isolate Latin/code runs (split first, escape each piece)."""
    if text.isascii():
        return html.escape(text)
    out, last = [], 0
    for m in _LTR.finditer(text):
        a, b = m.start(), m.end()
        # Unbalanced brackets belong to the surrounding Persian text, not the Latin run.
        while b > a and text[b - 1] == ")" and text[a:b].count("(") < text[a:b].count(")"):
            b -= 1
        while b > a and text[a] == "(" and text[a:b].count("(") > text[a:b].count(")"):
            a += 1
        out.append(html.escape(text[last:a]))
        if b > a:
            out.append('<bdi dir="ltr">' + html.escape(text[a:b]) + "</bdi>")
        last = b
    out.append(html.escape(text[last:]))
    return "".join(out)


def is_code(d):
    return d["en"] == d["fa"]


THEME = "../../../../../_shared/theme"
LOGO = "../../../../../_shared/brand/azad-logo.svg"
# Speaker-note tails, kept out of the f-strings below: a backslash inside an f-string expression needs Python 3.12.
PITFALL_NUMBERS = "PITFALL: Your numbers will differ; the shape should not.\nTIME: 60"
ASK_SURPRISE = "ASK: Which of these surprised you?\nTIME: 90"


def term(title, lines):
    out = []
    for ln in lines:
        hl = ln.startswith("!")
        ln = ln[1:] if hl else ln
        if ln.startswith("$ "):
            body = '<span class="p">$</span> ' + html.escape(ln[2:])
        elif ln.startswith("# "):
            body = '<span class="dim">' + html.escape(ln) + "</span>"
        else:
            body = html.escape(ln) if ln else " "
        out.append(f'<span class="ln{" hl" if hl else ""}">{body}</span>')
    return (
        f'<div class="term in d1"><div class="bar"><i></i><i></i><i></i>&nbsp; {html.escape(title)}</div>'
        f"<pre><code>{''.join(out)}</code></pre></div>"
    )


def notes(say_en, say_fa, key, extra=""):
    return f"""<aside class="notes">
SAY (EN): {say_en}
SAY (FA): {say_fa}
KEY POINT: {key}
{extra}
  </aside>"""


T = {
    "en": dict(
        dir="ltr",
        lang="en",
        lab="Lab",
        goal="Goal",
        setup="Setup",
        steps="Steps",
        expected="Expected output",
        observe="What to observe",
        pitfalls="Common pitfalls",
        ext="Extension task",
        nosol="Solution is in solution/ — not on slides.",
        notcap="EXPECTED: not yet captured on your machine; replace with your real run.",
        captured="Captured on {}.",
        course="",
        where="Runs on",
        symptom="Symptom",
        fix="Fix",
    ),
    "fa": dict(
        dir="rtl",
        lang="fa",
        lab="آزمایش",
        goal="هدف",
        setup="آماده‌سازی",
        steps="گام‌ها",
        expected="خروجی مورد انتظار",
        observe="به چه دقت کنید",
        pitfalls="اشتباه‌های رایج",
        ext="تمرین تکمیلی",
        nosol="راه‌حل در پوشهٔ solution/ است، نه روی اسلاید.",
        notcap="مورد انتظار: هنوز روی ماشین شما گرفته نشده؛ با خروجی واقعی خودتان جایگزین کنید.",
        captured="خروجی واقعی، گرفته‌شده روی {}.",
        course="",
        where="محل اجرا",
        symptom="نشانه",
        fix="رفع",
    ),
}


def deck(lab, L):
    t = T[L]
    num = lab["num"]
    title = lab["title"][L]
    cards = "".join(
        f'<div class="c-6 card edge {cls} in d{i + 1}"><h3>{tx(h[L])}</h3>'
        + (f'<p class="ltr-mono"><code>{html.escape(b[L])}</code></p>' if is_code(b) else f"<p>{tx(b[L])}</p>")
        + "</div>"
        for i, (cls, h, b) in enumerate(lab["setup_cards"])
    )
    observe = "".join(
        f'<li class="in d{i + 1}"><span class="callout-num">{i + 1}</span><div><b>{tx(h[L])}</b><br>'
        f'<span class="caption{" mono" if is_code(b) else ""}">{tx(b[L])}</span></div></li>'
        for i, (h, b) in enumerate(lab["observe"])
    )
    rows = "".join(
        f'<div class="pit in d{i + 1}"><span class="tag r-danger">{tx(s[L])}</span><span class="arrow-s">{"←" if L == "fa" else "→"}</span><span class="tag r-ok">{tx(f[L])}</span></div>'
        for i, (s, f) in enumerate(lab["pitfalls"])
    )
    eyebrow = f"{t['lab']} {num}"
    S = []
    S.append(f"""<section class="layout-section" data-transition="slide">
  <div class="numeral in-f">{num}</div>
  <span class="eyebrow in-f">{eyebrow} · {t["goal"]}</span>
  <h2 class="in">{tx(title)}</h2>
  <p class="why in d1">{tx(lab["goal"][L])}</p>
  <div class="pills in d2"><span class="pill">{t["where"]}: {html.escape(lab["where"][L])}</span></div>
  {notes("State the goal in one sentence and where the lab runs.", "هدف را در یک جمله بگویید و بگویید آزمایش کجا اجرا می‌شود.", lab["goal"]["en"], "TIME: 30")}
</section>""")
    S.append(f"""<section>
  <span class="eyebrow in-f">{eyebrow} · {t["setup"]}</span>
  <h2 class="in">{t["setup"]}</h2>
  <div class="grid tight">{cards}</div>
  {notes("Walk through what must be true before the first command.", "پیش از اولین دستور چه چیزهایی باید برقرار باشد.", "Preconditions decide whether the lab is reproducible.", "TIME: 60")}
</section>""")
    S.append(f"""<section>
  <span class="eyebrow in-f">{eyebrow} · {t["steps"]}</span>
  <h2 class="in">{t["steps"]}</h2>
  {term(lab["slug"], lab["steps"])}
  {notes("Run each command and say what it changes.", "هر دستور را اجرا کنید و بگویید چه چیزی را تغییر می‌دهد.", "Commands are copied from the lab README.", "TIME: 90")}
</section>""")
    S.append(f"""<section>
  <span class="eyebrow in-f">{eyebrow} · {t["expected"]}</span>
  <h2 class="in">{t["expected"]}</h2>
  {term("output", lab["expected"])}
  <p class="caption" style="margin-top:24px">{tx(t["captured"].format(lab["captured"][L]) if lab.get("captured") else t["notcap"])}</p>
  {notes("Point at the highlighted lines: these prove success.", "به خط‌های برجسته اشاره کنید؛ این‌ها موفقیت را ثابت می‌کنند.", ("Real output from the test VM." if lab.get("captured") else "Output is marked EXPECTED until captured from a real run (quality rule 2)."), PITFALL_NUMBERS)}
</section>""")
    S.append(f"""<section>
  <span class="eyebrow in-f">{eyebrow} · {t["observe"]}</span>
  <h2 class="in">{t["observe"]}</h2>
  <ul class="summary observe">{observe}</ul>
  {notes("Each observation previews a later module.", "هر مشاهده پیش‌نمایشی از یک ماژول بعدی است.", "Observation turns a setup task into a lesson.", ASK_SURPRISE)}
</section>""")
    S.append(f"""<section>
  <span class="eyebrow in-f">{eyebrow} · {t["pitfalls"]}</span>
  <h2 class="in">{t["pitfalls"]}</h2>
  <div class="pits">{rows}</div>
  {notes("Symptom on the left, fix on the right; the README has the full table.", "نشانه در یک سو و رفع در سوی دیگر؛ جدول کامل در README است.", "Read the error message before searching.", "TIME: 60")}
</section>""")
    S.append(f"""<section>
  <span class="eyebrow in-f">{eyebrow} · {t["ext"]}</span>
  <h2 class="in">{t["ext"]}</h2>
  <p class="highlight in d1" style="font-size:38px">{tx(lab["ext"][L])}</p>
  <p class="caption in d2" style="margin-top:32px">{html.escape(t["nosol"])}</p>
  {notes("Give the task, not the solution.", "تمرین را بدهید، نه راه‌حل را.", "Solutions live in solution/, never on slides.", "TIME: 30")}
</section>""")
    body = "\n\n".join(S)
    return f'''<!doctype html>
<html lang="{t["lang"]}" dir="{t["dir"]}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(eyebrow)} · {html.escape(title)}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400..800&family=Vazirmatn:wght@400..800&family=JetBrains+Mono:wght@500;700&display=swap">
  <link rel="stylesheet" href="{THEME}/azad-theme.css">
</head>
<body>
<!-- Generated from one EN/FA content table so both versions stay in sync. -->
<div class="reveal course-os">
<div class="slides">

{body}

</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js"></script>
<script src="{THEME}/azad-deck.js" data-course="{html.escape(t["course"])}" data-logo="{LOGO}"></script>
</body>
</html>
'''


def main():
    src = pathlib.Path(sys.argv[1]).resolve()
    data = runpy.run_path(str(src))
    out = src.parent / "labs"
    out.mkdir(parents=True, exist_ok=True)
    for L in ("en", "fa"):
        T[L]["course"] = data["COURSE"][L]
    for lab in data["LABS"]:
        for L in ("en", "fa"):
            p = out / f"{lab['slug']}.{L}.html"
            p.write_text(deck(lab, L), encoding="utf-8", newline="\n")
            print("wrote", p.relative_to(src.parent.parent.parent))


if __name__ == "__main__":
    main()
