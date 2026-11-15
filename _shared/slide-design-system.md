# Slide Design System v3 — Azad University · Modern Projector Edition

The single source of truth for **every slide deck in every course** (Term 1–4).
Give this file to any agent together with a course's `slides-outline.md` and it can build the deck.

| | |
|---|---|
| **Audience** | Professors and master's students in a lit classroom |
| **Medium** | Classroom projector: low contrast, washed-out colors, viewers up to 8 m away |
| **Look** | Modern editorial: white space, Azad blue identity, big confident type, bento cards, motion that explains |
| **Default language** | Persian (RTL). Code, identifiers, and terminal output stay English (LTR) |
| **Build targets** | reveal.js HTML (primary) → PDF export · PowerPoint (fallback, section 15) |

---

## 1. Principles

1. **Projector first.** If you can't read it at 8 m on a washed-out projector, the slide fails.
2. **One idea per slide.** The title is that idea, written as a full sentence.
3. **Show it, then say it.** Use a diagram for any flow, layer, or state. Text comes second.
4. **Use real material.** Show real code, real tool output, and real numbers. No toy examples.
5. **Every color has a job.** Azad blue marks identity and emphasis. Each semantic color (section 5) keeps one meaning for the whole course.
6. **Motion shows order and cause.** Animate only to show what happens first and what causes what.
7. **Keep it calm.** Leave a lot of empty space, use few colors, and limit each slide to one accent.

## 2. Canvas & Grid

- 16:9, **1920 × 1080 px** (1 pt = 2 px).
- Safe margins: **120 px** left and right, **96 px** top, **144 px** bottom when the slide has a footer.
- **12-column grid**: 64 px gutters, column ≈ 81 px. Every block snaps to the grid.
- **8 px spacing scale**: 8 · 16 · 24 · 32 · 48 · 64 · 96 · 128. Use no other values.
- Footer: one 24 px row at `bottom: 56px`. Course tag goes at the start edge, slide number `07 / 18` at the end edge. No footer on TITLE or SECTION slides.

## 3. Brand: Islamic Azad University

### 3.1 Identity

- The university's flag and logo are a **blue emblem on a white field**. Every slide follows that: white surface, Azad blue ink, one warm accent.
- **Official hex values:** no public brand guide with exact codes was found. The values below are a **close approximation** of the logo's royal blue. Before the final presentation, sample the real blue from the official logo file (3.3) and replace `--brand`. The other brand tokens derive from it.

### 3.2 Logo rules

- Use the **official logo file** only (SVG or PNG with transparency, ≥ 1000 px). Never redraw, recolor, stretch, outline, shadow, or animate it.
- Place it on **white**. On blue slides, put it on a white rounded tile (radius 24 px, padding 24 px).
- Clear space must be at least **half the logo's height** on every side.
- Size: **160 px** tall on TITLE, **64 px** on SECTION, **48 px** in the content-slide corner (top-left in RTL decks, top-right in LTR).
- No logo file yet? Put a labeled dashed placeholder `[University logo]` and say so in the build notes.
- File location convention: `_shared/brand/azad-logo.svg` (or `.png`).

### 3.3 Get the exact brand blue from the logo

```python
# extract_brand_color.py — prints the dominant non-white color of the logo.
# Usage: python3 extract_brand_color.py _shared/brand/azad-logo.png
import sys
from collections import Counter
from PIL import Image  # pip install pillow

img: Image.Image = Image.open(sys.argv[1]).convert("RGBA").resize((200, 200))
pixels: list[tuple[int, int, int, int]] = list(img.getdata())
colored: list[tuple[int, int, int]] = [
    (r // 8 * 8, g // 8 * 8, b // 8 * 8)
    for r, g, b, a in pixels
    if a > 200 and not (r > 230 and g > 230 and b > 230)
]
(r, g, b), _ = Counter(colored).most_common(1)[0]
print(f"--brand: #{r:02X}{g:02X}{b:02X};")
```

Then check that the result reaches **≥ 7:1** contrast on white (e.g. webaim.org/resources/contrastchecker). If it doesn't, darken it until it does and keep the original only for large shapes.

### 3.4 Title-slide fields (never invent these)

`[Course name]` · `[Presenter]` · `[Professor]` · `[Faculty / Branch]` · `[Term]` · `[Date, Jalali]`

## 4. Color Tokens

### 4.1 Azad Light (default, for projectors)

```css
:root, .reveal {
  /* Brand: replace --brand with the sampled logo blue (section 3.3) */
  --brand:         #1F4FA8;  /* Azad royal blue, ~7.6:1 on white */
  --brand-deep:    #0C2763;  /* TITLE / SECTION backgrounds, h1 ink */
  --brand-ink:     #123A86;  /* links, emphasis inside body text */
  --brand-soft:    #E6EEFC;  /* tints, chips, soft panels */
  --brand-line:    #9FB6E3;  /* dividers on brand-soft */

  /* Neutrals: cool, slightly blue to match the brand */
  --bg:            #FFFFFF;
  --bg-alt:        #F4F7FC;  /* alternating panels, code cards */
  --border:        #8C9DBF;  /* >= 3:1 on white */
  --text:          #0A1633;  /* ~17:1 */
  --text-muted:    #3B4868;  /* >= 7:1, never lighter */

  /* One warm accent, used for fills and bars only, never as text on white */
  --accent:        #F5B301;  /* Azad gold */
  --accent-soft:   #FFF1C2;  /* highlighted line / current step */

  /* Status */
  --danger:  #B4123A;  --danger-bg:  #FDE4EA;
  --success: #12733A;  --success-bg: #DDF3E4;
  --warning: #9A4A00;  --warning-bg: #FDEBD3;

  /* Shape */
  --r-card: 28px;  --r-code: 20px;  --r-box: 14px;  --r-pill: 999px;
  --stroke: 3px;   --stroke-strong: 4px;

  /* Motion */
  --ease:    cubic-bezier(.22, 1, .36, 1);   /* expo-out */
  --dur:     520ms;
  --stagger: 90ms;
}
```

### 4.2 Azad Night (dark rooms or recorded videos only)

```css
.reveal.night {
  --brand:#8DB0FF; --brand-deep:#071739; --brand-ink:#B9CDFF;
  --brand-soft:#132A5E; --brand-line:#36508C;
  --bg:#0A132B; --bg-alt:#101D3D; --border:#4C5F8E;
  --text:#F2F6FF; --text-muted:#B6C3E1;
  --accent:#FFC93D; --accent-soft:#4B3A06;
  --danger:#FF7A93; --danger-bg:#3F1522;
  --success:#4FDB86; --success-bg:#0F3320;
  --warning:#FFB25C; --warning-bg:#3D2508;
}
```

### 4.3 Projector color rules

- Body text needs **≥ 7:1** contrast. Text ≥ 44 px needs ≥ 4.5:1.
- **No pale gray text and no hairlines.** Borders are ≥ 3 px and ≥ 3:1 against their background.
- Use a tinted fill (`--*-bg`) only together with a solid border in the matching color.
- **At most 3 colors per slide** besides neutrals and brand.
- Never use red vs. green alone. Always add a label (`BUG` / `FIX`, `BEFORE` / `AFTER`) or an icon.
- Gradients are allowed in one place only: the large soft brand shape on TITLE and SECTION slides.
- **No drop shadows.** They disappear on projectors. Use borders for depth.

## 5. Semantic Palettes (per course)

Each course gets **four semantic roles**. A role keeps the same color across the whole course, so students learn the code. Each role has an ink color (border, text, icon) and a `-bg` tint.

| Token | Ink | Tint |
|---|---|---|
| `--role-1` | `#0E7490` teal | `#DFF4F8` |
| `--role-2` | `#B45309` amber | `#FDEFD9` |
| `--role-3` | `#6D28D9` violet | `#EEE6FB` |
| `--role-4` | `#047857` green | `#DCF3EA` |

Night theme inks: `#38BDF8` · `#FBBF24` · `#A78BFA` · `#34D399`. Night tints: `#0E2A3A` · `#3A2A0A` · `#2A1F4D` · `#0C3326`.

### 5.1 Role mapping by course

| Course | role-1 (teal) | role-2 (amber) | role-3 (violet) | role-4 (green) |
|---|---|---|---|---|
| **Advanced OS** | User space | Kernel | Hardware | Data / memory |
| **Advanced Network Security** | Trusted zone / defender | Attacker / threat | Crypto / keys | Network / traffic |
| **Advanced Software Engineering** | Client / UI | Service / domain logic | Infrastructure / platform | Data / storage |
| *Term 2–4 courses* | *define in the course `agent-prompt.md`, using the same 4 tokens* | | | |

Alias the roles in CSS so slide code stays readable:

```css
/* Advanced OS */
.course-os  { --user:var(--role-1); --kernel:var(--role-2); --hardware:var(--role-3); --data:var(--role-4); }
/* Advanced Network Security */
.course-sec { --trusted:var(--role-1); --threat:var(--role-2); --crypto:var(--role-3); --net:var(--role-4); }
/* Advanced Software Engineering */
.course-se  { --client:var(--role-1); --service:var(--role-2); --infra:var(--role-3); --store:var(--role-4); }
```

Exception: in security decks, **amber (threat) is never used for the "good" side**, and `--danger` red is kept for real compromise or impact.

## 6. Typography

| Role | Latin | Persian | Size (px) | Weight | Line height |
|---|---|---|---|---|---|
| Display (cover h1) | Inter Display / Inter | Vazirmatn | 112 | 800 | 1.1 |
| Slide title (h2) | Inter | Vazirmatn | 64 | 750 | 1.2 |
| Card title (h3) | Inter | Vazirmatn | 40 | 650 | 1.3 |
| Body | Inter | Vazirmatn | **34** (never below 30) | 450 | 1.35 / Persian 1.55 |
| Eyebrow / kicker | Inter | Vazirmatn | 24, `letter-spacing:.12em`, UPPERCASE for Latin | 700 | 1.2 |
| Caption / footer | Inter | Vazirmatn | 26 / 24 | 500 | 1.3 |
| Code | JetBrains Mono | JetBrains Mono | **28** (never below 26) | 500 | 1.45 |
| Big stat | Inter | Vazirmatn | 160–200, tabular numerals | 800 | 1.0 |

- Persian text is set **+2 px** larger than the matching Latin text.
- Use at most **5 sizes per deck**. For emphasis use weight or `--brand-ink`, not a new size.
- Fonts (Google Fonts, all free): `Inter`, `Vazirmatn`, `JetBrains Mono`.
  Fallbacks: `Inter, system-ui, sans-serif` · `Vazirmatn, Tahoma, sans-serif` · `'JetBrains Mono', Menlo, monospace`.
- Code and identifiers (`task_struct`, `nft add rule`, `OrderService`) are always monospace, even inline.
- Turn on `font-feature-settings: "tnum"` for numbers in tables and charts.

## 7. Modern Look: Shapes & Components

| Component | Spec |
|---|---|
| **Eyebrow** | Small kicker above h2 (`Module 4 · Memory`), `--brand`, 24 px bold, followed by a 48 × 6 px `--accent` bar |
| **Card** | `--bg` fill, `--stroke` border `--border`, radius `--r-card`, padding 40 px. Optional **8 px top edge** in its semantic color |
| **Bento grid** | 2–5 cards of different sizes on the 12-col grid (e.g. 7+5, 4+4+4, 8 / 4+4). The most important card is the largest |
| **Pill / tag** | `--brand-soft` fill, `--brand-ink` text, 24 px bold, radius `--r-pill`, padding 8 × 20 |
| **Callout number** | 56 px circle, `--brand` fill, white numeral 28 px bold: ① ② ③ |
| **Big numeral** | Section number 320 px, weight 800, `--brand` outline (4 px) with 12% fill, behind the title |
| **Highlight** | `--accent-soft` background + 8 px `--accent` start-edge bar |
| **Divider** | 3 px `--brand-line`, never a thin gray hairline |
| **Brand motif** | One per TITLE/SECTION slide: 3 large overlapping circles bleeding off one corner in `--brand`, `--brand-ink`, `--brand-soft` at 18–30% opacity. Never behind text |
| **Corner logo** | 48 px, top-left (RTL) / top-right (LTR), content slides only |
| **Icons** | Lucide or Tabler line icons, 2.5 px stroke, 48–64 px, colored with the role ink |

- **Whitespace:** fill about 60% of the content area. Never fill every corner.
- **Alignment:** everything aligns to the grid's start edge. Center text only on TITLE, QUIZ, and BIG_STAT.

## 8. Layout Library

Name the layout in outlines (`Layout: CODE_WALKTHROUGH`).

| Layout | Use | Key rules |
|---|---|---|
| **TITLE** | Cover | `--brand-deep` full bleed, white display title, logo on a white tile, brand motif, fields from 3.4 |
| **SECTION** | Module start | `--brand-deep`, giant numeral, module title, one sentence on why it matters, 3 topic pills |
| **AGENDA** | Overview | 4–6 numbered rows. The current one is filled `--brand` with white text, the rest outlined |
| **CONCEPT_DIAGRAM** | Most used | Eyebrow + title + diagram on ~65% of the area + ≤ 3 numbered callouts + one-line takeaway |
| **BENTO** | 3–5 related facts or features | Bento grid (section 7), one icon + title + ≤ 15 words per card |
| **LAYER_STACK** | Stacks (user→kernel→HW, OSI, app→infra) | Horizontal bands in role colors, a dashed **boundary** line with a label |
| **TWO_COLUMN_COMPARE** | X vs Y | Same 4–6 rows on both sides. Brand on one side, accent outline on the other, never red/green |
| **FLOW_TIMELINE** | Ordered process (≤ 7 steps) | The current step uses `--accent-soft` with a `--brand` border. Flows right→left in RTL |
| **SEQUENCE** | Protocols, races, attacks, RPC | Actors as columns, time going down, one fragment per message |
| **STATE_MACHINE** | Lifecycles | Circles + labeled arrows; the current state is filled |
| **ARCHITECTURE** | System / network topology | ≤ 10 boxes, zones as tinted rounded rectangles (e.g. DMZ, VPC), arrows labeled with the protocol |
| **CODE_WALKTHROUGH** | Real code | Code on 7/12 columns, 3–4 numbered notes on 5/12; ≤ 15 lines; highlighted line groups |
| **TERMINAL_DEMO** | `strace`, `nmap`, `kubectl`… | Dark terminal card (`#0A1633`, text `#E6EEFC`) even in Light theme; ≤ 12 lines; 1–2 highlighted |
| **BIG_STAT** | One striking number | Number at 180 px in `--brand`, one-line meaning, source caption |
| **DATA_CHART** | One finding | One chart, the title states the finding, units on axes, source caption, role colors only |
| **MEMORY_LAYOUT** | Address space / packet / header layout | Vertical (memory) or horizontal (packet) stacked fields, with sizes labeled |
| **BUG_AND_FIX** | Bug, vulnerability, anti-pattern | Left card `--danger` + `BUG`/`VULN` pill, right card `--success` + `FIX` pill, one line on why the fix works |
| **QUOTE / DEFINITION** | A key definition or paper claim | 48 px text, `--brand` 8 px start bar, source + year below |
| **QUIZ** | Check understanding | Question centered, 3–4 option pills; the answer goes on the **next** slide |
| **SUMMARY** | End of topic | ≤ 3 takeaways with big ①②③, plus a "Next:" line |
| **REFERENCES** | Sources | Books, RFCs, papers, docs, links; 26 px, two columns |

## 9. Persian (RTL) Rules

- Use `dir="rtl"` on the deck root. Text blocks get `text-align: start`. Use logical CSS properties (`margin-inline-start`, `inset-inline-end`) so layouts mirror on their own.
- Mirror everything: titles and bullets on the right, timelines flowing right → left, logo top-left, highlight bars on the right edge, "Next" arrow pointing left.
- Wrap English terms inline so punctuation doesn't flip: `<span dir="ltr">Context Switch</span>`. Use `<bdi>` for user-supplied names.
- Code, terminals, URLs, and diagrams that contain identifiers stay **LTR** inside RTL slides.
- Use Persian digits (۰۱۲۳) in prose. Use Latin digits in code, IPs, addresses, units, versions, and slide numbers.
- Never put a Persian sentence and a code snippet on the same line.
- Use the Persian comma `،` and question mark `؟` in Persian sentences.

## 10. Diagram Conventions

- Boxes: radius `--r-box`, `--stroke` border in the role ink, role tint fill, labels **≥ 26 px**.
- Arrows: solid 4 px = call/control flow. Dashed = data/return flow. Thick `--accent` = hot path or the current step.
- Number the steps ①②③ in `--brand` and refer to them in the callouts.
- Label every arrow with a verb, function, or protocol (`read()`, `TLS ClientHello`, `POST /orders`).
- Boundaries are dashed lines with a label: `syscall boundary`, `trust boundary`, `service boundary`, `Ring 3 / Ring 0`.
- **≤ 10 nodes per diagram.** If you need more, split it across two slides with `magic` transition.
- Use inline **SVG**, which stays sharp on a projector. Use Mermaid only if it is restyled with these tokens (11.4).

## 11. Code & Terminal on Slides

- ≤ 15 lines, ≤ 60 characters per line, 28 px. Never shrink the font to fit more. Cut lines with `/* ... */` or `# ...`.
- Code card: `--bg-alt` fill, 3 px `--border`, radius `--r-code`, with a **file chip** on top (`kernel/sched/core.c · v6.12`, `nftables.conf`, `order_service.go`).
- Syntax colors (Light): keywords `--brand`, functions `--role-2`, types `--role-3`, strings and numbers `--role-4`, comments `--text-muted` (italic).
- Highlight lines with `--accent-soft` + an 8 px `--accent` start bar. Use one highlight per fragment.
- **English comments only.** Use explicit types in examples.
- Show only verified code and real output. If code is unverified, mark it `UNVERIFIED` in the speaker notes.

### 11.4 Mermaid restyle (if Mermaid is used)

```js
mermaid.initialize({
  theme: "base",
  themeVariables: {
    fontFamily: "Inter, Vazirmatn, sans-serif", fontSize: "26px",
    primaryColor: "#E6EEFC", primaryBorderColor: "#1F4FA8", primaryTextColor: "#0A1633",
    lineColor: "#3B4868", secondaryColor: "#FFF1C2", tertiaryColor: "#F4F7FC"
  }
});
```

## 12. Motion & Animation

**Philosophy:** motion shows **order** (what happens first) and **causality** (what triggers what). If an animation explains neither, delete it.

### 12.1 Presets

```css
@keyframes rise { from { opacity: 0; transform: translateY(24px); } }
@keyframes fade { from { opacity: 0; } }
@keyframes pop  { from { opacity: 0; transform: scale(.95); } }
@keyframes draw { from { stroke-dashoffset: var(--len, 400); } }   /* SVG arrows */

.present .in   { animation: rise var(--dur) var(--ease) both; }
.present .in-f { animation: fade var(--dur) var(--ease) both; }
.present .in-p { animation: pop  var(--dur) var(--ease) both; }
.present .draw { stroke-dasharray: var(--len, 400); animation: draw 700ms var(--ease) both; }
.d1 { animation-delay: calc(var(--stagger) * 1); }  .d2 { animation-delay: calc(var(--stagger) * 2); }
.d3 { animation-delay: calc(var(--stagger) * 3); }  .d4 { animation-delay: calc(var(--stagger) * 4); }

@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
```

The plain CSS rule is always the **finished look**, which is what PDF export shows. Animation only defines the starting state.

### 12.2 Where to use what

| Situation | Motion |
|---|---|
| Eyebrow + title | Title `rise`, eyebrow bar `fade` (d1) |
| Parallel cards / bento | `rise`, staggered (max 5) |
| Diagram build | Follow the story: zones → boxes → arrows (`draw`) → callouts. A line never appears before the boxes it connects |
| Current step in a flow | Click step (`fragment`): background changes to `--accent-soft` |
| Code walkthrough | One fragment per highlighted region, with the matching note on the other side |
| Sequence / protocol / attack | Each message is a fragment |
| BUG → FIX | Bug card on arrival, fix card on click (`pop`) |
| Big stat | Number `pop`, caption `fade` (d2) |
| Section | Numeral `fade`, title `rise` |
| Quiz → answer | No animation. The answer goes on the next slide |

### 12.3 Transitions

- Default `fade` (300 ms). Use `slide` for SECTION. Use `auto-animate` only when the same element visibly continues on the next slide.

### 12.4 Hard limits

- The whole slide is visible within **1 s** of arriving, except click steps.
- ≤ 2 animations per element. Animate only `opacity`, `transform`, `background-color`, `border-color`, `color`, `stroke-dashoffset`.
- **No loops** near text. No bouncing, spinning, parallax, or flashing faster than 3 per second.
- Nothing depends on hover. Every build step has a static final state.

## 13. Speaker Notes Template

```
SAY (EN): (2–4 sentences, English)
SAY (FA): (the same 2–4 sentences, Persian)
KEY POINT: (the one thing to remember)
EXAMPLE: (real command / real output / real case)
PITFALL: (common misconception)
ASK: (one question to the audience, optional)
TIME: (seconds)
```

## 14. Outline Format (what agents output in `slides-outline.md`)

```
## Slide 7 — CONCEPT_DIAGRAM
Eyebrow: Module 4 · Memory
Title: A page fault is a controlled trap into the kernel
Diagram: <nodes, arrows, roles (role-1..4), boundaries>
Callouts: ① CPU raises exception  ② Kernel finds the VMA  ③ Page mapped, instruction retried
Takeaway: The program never notices a page fault happened.
Source: mm/memory.c · handle_mm_fault() · v6.x
Motion: boxes → arrows (draw) → callouts (stagger 90 ms); ③ on click
Notes:
  SAY: ...
  KEY POINT: ...
  EXAMPLE: ...
  PITFALL: ...
  TIME: 90
```

Per module: **12–18 slides**, starting with SECTION and ending with SUMMARY. At least 60% of slides should be visual (diagram, code, terminal, chart).

## 15. Build Recipe

### 15.1 reveal.js starter (primary)

```html
<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400..800&family=Vazirmatn:wght@400..800&family=JetBrains+Mono:wght@500;700&display=swap">
  <link rel="stylesheet" href="azad-theme.css"> <!-- tokens from sections 4, 5, 7, 12 -->
</head>
<body>
  <div class="reveal course-os">
    <div class="slides">
      <section class="layout-title" data-transition="fade">...</section>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script>
    Reveal.initialize({ width: 1920, height: 1080, margin: 0, hash: true,
                        transition: "fade", rtl: true, center: false });
  </script>
</body>
</html>
```

- Export PDF: open `deck.html?print-pdf` in Chrome → Print → Save as PDF (background graphics on).
- Put the shared theme at `_shared/theme/azad-theme.css` once it is built, and reuse it in every course.

### 15.2 PowerPoint fallback

- Use the same tokens and type sizes. Build the theme as a Slide Master with one master per layout from section 8.
- Animations: **Fade**, **Appear**, and **Wipe** only. Use one transition type (Fade) for the whole deck.

## 16. Pre-Delivery Checklist

- [ ] Squint test: the title and the main shape are still readable
- [ ] Body ≥ 32 px, code ≥ 28 px, diagram labels ≥ 26 px
- [ ] Text contrast ≥ 7:1, no pale gray text, borders ≥ 3 px
- [ ] One idea per slide, ≤ 35 words of body text
- [ ] Role colors match the course mapping (5.1). Brand blue is used only for identity and emphasis
- [ ] Logo is the official file, on white, with clear space. `--brand` sampled from it
- [ ] Code and output are real, verified, and sourced (path + version)
- [ ] Motion explains order, slide fully visible ≤ 1 s, no loops, static final states
- [ ] RTL applied to Persian text, code stays LTR, digits follow the rules
- [ ] Speaker notes on every slide
- [ ] PDF export checked on a second screen at low brightness
