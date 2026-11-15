"""The course site's pages: Home -> Term -> Course -> slide decks.

One generator for both uses, so what you test locally is what gets published:
  * serve.py renders these pages on request (make slides / make view);
  * build_site.py writes them to a folder for GitHub Pages (make site).

Every link is relative (../../ and so on), so the pages work at any URL: http://localhost:8000/,
https://<owner>.github.io/<repo>/, or a custom subdomain. The text switches between English and Persian in the
page (the choice is remembered in the browser); module and lab names are read from each deck's own <title>.
"""

import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
FONTS_LINK = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400..800&family=Vazirmatn:wght@400..800"
    "&family=JetBrains+Mono:wght@500;700&display=swap"
)  # same URL the decks use, so the offline cache applies
# Persian names for courses that have no deck yet (a course with decks takes its name from its lesson deck).
COURSE_FA = {
    "advanced-network-security": "امنیت شبکهٔ پیشرفته",
    "advanced-software-engineering": "مهندسی نرم‌افزار پیشرفته",
}
CREDIT_URL = "https://commons.wikimedia.org/wiki/File:Azad_University_logo.png"

STRINGS = {
    "en": {
        "siteTitle": "Course slides",
        "siteSub": "Islamic Azad University · MSc courses",
        "home": "Home",
        "open": "Open →",
        "soon": "Coming soon",
        "lesson": "Lesson",
        "noFa": "English only",
        "ph": "Search modules and labs…  (press / )",
        "langLabel": "Slides language",
        "none": "No deck matches your search.",
        "termsH": "Terms",
        "coursesH": "Courses",
        "chooseCourse": "Choose a course",
        "chooseModule": "Choose a module, then a lesson or lab",
        "tipsH": "Inside a deck",
        "tip0": "Pick the slides language once at the top; every deck then opens in it (remembered in this browser).",
        "tip1": "<kbd>S</kbd> speaker notes · <kbd>F</kbd> fullscreen · <kbd>Esc</kbd> overview · <kbd>A</kbd> animations on/off · <kbd>T</kbd> toolbar (transition, speed, export, back to the course)",
        "tip1site": "<kbd>F</kbd> fullscreen · <kbd>Esc</kbd> overview · <kbd>A</kbd> animations on/off · <kbd>T</kbd> toolbar (transition, speed, PDF export, back to the course)",
        "tip2": "On a deck's last slide a bar offers the next deck (a lesson leads to its labs, then to the next module).",
        "one": "1 deck",
        "many": "{n} decks",
        "credit": 'Unofficial study material: not affiliated with, or endorsed by, Islamic Azad University. Azad University emblem: <a href="%s" rel="noopener">Wikimedia Commons</a> (CC BY-SA 4.0). Slides built with reveal.js. Kernel excerpts: Linux (GPL-2.0) and OpenBSD (BSD).'
        % CREDIT_URL,
        "labTitle": "No virtual machine? Try the browser lab",
        "labBody": "A real 32-bit Linux kernel running inside your browser, with 10 guided mini-labs. A simplified stand-in: use a VM (or Docker for user-space labs) when you can.",
        "labGo": "Open the browser lab →",
    },
    "fa": {
        "siteTitle": "اسلایدهای درس‌ها",
        "siteSub": "دانشگاه آزاد اسلامی · درس‌های کارشناسی ارشد",
        "home": "صفحهٔ اصلی",
        "open": "باز کردن ←",
        "soon": "به‌زودی",
        "lesson": "درس",
        "noFa": "فقط انگلیسی",
        "ph": "جست‌وجوی ماژول‌ها و آزمایش‌ها…  (کلید / )",
        "langLabel": "زبان اسلایدها",
        "none": "اسلایدی با این جست‌وجو پیدا نشد.",
        "termsH": "ترم‌ها",
        "coursesH": "درس‌ها",
        "chooseCourse": "یک درس را انتخاب کنید",
        "chooseModule": "یک ماژول و سپس درس یا آزمایش را انتخاب کنید",
        "tipsH": "داخل اسلاید",
        "tip0": "زبان اسلایدها را یک بار بالای صفحه انتخاب کنید؛ همهٔ اسلایدها با همان زبان باز می‌شوند (در همین مرورگر به خاطر سپرده می‌شود).",
        "tip1": "<kbd>S</kbd> یادداشت سخنران · <kbd>F</kbd> تمام‌صفحه · <kbd>Esc</kbd> نمای کلی · <kbd>A</kbd> روشن/خاموش کردن انیمیشن · <kbd>T</kbd> نوار ابزار (جلوهٔ گذار، سرعت، خروجی، بازگشت به درس)",
        "tip1site": "<kbd>F</kbd> تمام‌صفحه · <kbd>Esc</kbd> نمای کلی · <kbd>A</kbd> روشن/خاموش کردن انیمیشن · <kbd>T</kbd> نوار ابزار (جلوهٔ گذار، سرعت، خروجی PDF، بازگشت به درس)",
        "tip2": "در آخرین اسلاید هر deck یک نوار، deck بعدی را پیشنهاد می‌دهد (درس به آزمایش‌هایش و سپس به ماژول بعدی می‌رسد).",
        "one": "۱ deck",
        "many": "{n} deck",
        "credit": 'مطالب مطالعاتی غیررسمی؛ وابسته به دانشگاه آزاد اسلامی نیست و از سوی آن تأیید نشده است. نشان دانشگاه آزاد: <a href="%s" rel="noopener">Wikimedia Commons</a> (مجوز CC BY-SA 4.0). اسلایدها با reveal.js ساخته شده‌اند. بخش‌های کد کرنل: Linux (‏GPL-2.0) و OpenBSD (‏BSD).'
        % CREDIT_URL,
        "labTitle": "ماشین مجازی ندارید؟ آزمایشگاه مرورگر را امتحان کنید",
        "labBody": "یک کرنل واقعی ۳۲ بیتی Linux که داخل مرورگر شما اجرا می‌شود، با ۱۰ آزمایش کوچک گام‌به‌گام. یک جایگزین ساده‌شده است: هر وقت می‌توانید از ماشین مجازی (یا Docker برای آزمایش‌های user-space) استفاده کنید.",
        "labGo": "باز کردن آزمایشگاه مرورگر ←",
    },
}

CSS = """
:root{--bg:#F4F6FC;--card:#fff;--fg:#0A1633;--muted:#4A5780;--brand:#2F4BB0;--soft:#ECF0FD;--line:#D5DDF5;--accent:#F5B301;
--shadow:0 2px 4px rgba(34,47,106,.06),0 16px 32px -16px rgba(34,47,106,.28)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 Inter,system-ui,-apple-system,"Segoe UI",sans-serif;display:flex;flex-direction:column;min-height:100vh}
html[lang=fa] body{font-family:Vazirmatn,Tahoma,"Segoe UI",sans-serif;line-height:1.7}
a{color:var(--brand)}
.hero{background:radial-gradient(900px 500px at 90% -30%,rgba(100,124,208,.28),transparent 65%),#fff;color:#222F6A;border-bottom:3px solid var(--line);padding:26px 24px 64px}
html[dir=rtl] .hero{background:radial-gradient(900px 500px at 10% -30%,rgba(100,124,208,.28),transparent 65%),#fff}
.wrap{max-width:1100px;margin:0 auto}
.crumbs{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 22px;padding:0;list-style:none;font-size:14px;font-weight:600}
.crumbs li{display:flex;align-items:center;gap:6px}
.crumbs li+li::before{content:"›";color:var(--muted);font-weight:700}
html[dir=rtl] .crumbs li+li::before{content:"‹"}
.crumbs a{text-decoration:none;padding:4px 10px;border-radius:999px;background:var(--soft)}
.crumbs a:hover,.crumbs a:focus-visible{outline:2px solid var(--brand);outline-offset:1px}
.crumbs [aria-current]{color:var(--muted);padding:4px 4px}
.brand{display:flex;align-items:center;gap:20px}
.brand .tile{background:#fff;border:2px solid var(--line);border-radius:18px;padding:10px 14px;box-shadow:var(--shadow);display:flex}
.brand img{height:72px;width:auto;display:block}
h1{margin:0;font-size:clamp(28px,4vw,42px);letter-spacing:-.02em;line-height:1.2}
html[lang=fa] h1{letter-spacing:0}
.sub{margin:6px 0 0;color:var(--muted)}
.search{margin-top:26px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.search input{flex:1 1 320px;font:inherit;padding:14px 20px;border-radius:999px;border:2px solid var(--line);background:#fff;color:var(--fg);outline:0;box-shadow:var(--shadow)}
.search input::placeholder{color:var(--muted)}
.search input:focus{border-color:var(--brand)}
.count{color:var(--muted);font-size:14px}
main{margin-top:-34px;padding:0 24px 48px;flex:1}
h2{font-size:14px;letter-spacing:.12em;text-transform:uppercase;color:var(--brand);margin:40px 0 16px;display:flex;align-items:center;gap:12px}
html[lang=fa] h2{letter-spacing:0;text-transform:none;font-size:16px}
h2::before{content:"";width:32px;height:6px;border-radius:3px;background:var(--accent)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));gap:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:22px;box-shadow:var(--shadow)}
.card h3{margin:0 0 14px;font-size:18px;display:flex;gap:12px;align-items:center}
.card h3 .n{display:inline-grid;place-items:center;min-width:38px;height:38px;border-radius:50%;color:#fff;font-weight:800;font-size:15px;flex:none;
background:linear-gradient(135deg,#647CD0,#2F4BB0 55%,#222F6A);font-family:Inter,system-ui,sans-serif}
a.nav{display:flex;flex-direction:column;gap:14px;text-decoration:none;color:inherit;border:2px solid var(--line)}
a.nav:hover,a.nav:focus-visible{border-color:var(--brand);outline:0}
a.nav h3{margin:0}
.nav .d{color:var(--muted);font-size:14px}
.nav .go,.lablink .go{align-self:flex-start;font-size:14px;font-weight:700;color:#fff;background:var(--brand);padding:7px 18px;border-radius:999px;white-space:nowrap}
.card.soon{opacity:.75;border-style:dashed;box-shadow:none}
.badge{display:inline-block;font-size:12px;font-weight:800;color:#5C2D00;background:#FDEBD3;border:1px solid #E3B27A;padding:3px 10px;border-radius:999px;align-self:flex-start}
.row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 12px;margin:0 -12px;border-radius:12px;color:inherit;text-decoration:none}
.row + .row{border-top:1px solid var(--line);border-top-left-radius:0;border-top-right-radius:0}
.row .t{display:flex;flex-direction:column;min-width:0}
.row b{font-weight:650}
.row small{color:var(--muted);font-size:12px;font-weight:600}
.row.lesson b{color:var(--brand)}
.row .go{flex:none;font-size:13px;font-weight:700;color:var(--brand);background:var(--soft);padding:5px 14px;border-radius:999px;border:1px solid transparent;white-space:nowrap}
.row:hover,.row:focus-visible{background:var(--soft);outline:0}
.row:hover .go,.row:focus-visible .go{border-color:var(--brand)}
.row .note{font-size:12px;font-weight:600;color:var(--muted);margin-inline-end:10px;display:none}
body.fa .row.noFa .note{display:inline}
.lang{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:22px;color:var(--muted);font-size:14px;font-weight:600}
.seg{display:inline-flex;padding:4px;border:2px solid var(--line);border-radius:999px;background:#fff;box-shadow:var(--shadow)}
.seg button{font:inherit;font-size:15px;font-weight:700;color:var(--brand);background:transparent;border:0;border-radius:999px;padding:8px 22px;cursor:pointer}
.seg button:hover{background:var(--soft)}
.seg button[aria-pressed="true"]{background:var(--brand);color:#fff}
.seg button[data-l="fa"]{font-family:Vazirmatn,Tahoma,sans-serif}
.lablink{display:flex;gap:16px;align-items:center;justify-content:space-between;flex-wrap:wrap;text-decoration:none;color:inherit;margin-top:28px;background:var(--card);border:2px solid var(--line);border-radius:22px;padding:18px 22px;box-shadow:var(--shadow)}
.lablink:hover,.lablink:focus-visible{border-color:var(--brand);outline:0}
.lablink b{display:block;color:#222F6A;font-size:18px}.lablink span.d{color:var(--muted);font-size:14px}
.tips{margin-top:48px;background:var(--card);border:1px solid var(--line);border-radius:22px;padding:22px;color:var(--muted);box-shadow:var(--shadow)}
.tips h3{margin:0 0 10px;color:var(--fg);font-size:16px}
kbd,code{font:600 .88em ui-monospace,Consolas,monospace;background:var(--soft);color:var(--brand);padding:2px 8px;border-radius:8px;direction:ltr;unicode-bidi:isolate;display:inline-block}
.tips ul{margin:0;padding-inline-start:20px}.tips li{margin:4px 0}
footer{padding:22px 24px 30px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);background:#fff}
.hidden{display:none!important}
.empty{padding:40px;text-align:center;color:var(--muted)}
img,svg{max-width:100%}
.row .t b,.row small,.card h3 span,h1,.sub{overflow-wrap:anywhere}
@media (max-width:640px){
 .hero{padding:16px 16px 56px}
 main{padding:0 14px 36px;margin-top:-30px}
 .brand{gap:14px}.brand img{height:52px}.brand .tile{padding:7px 9px;border-radius:14px}
 h1{font-size:26px}
 .crumbs{font-size:13px;margin-bottom:16px}
 .search{margin-top:18px}.search input{padding:12px 16px;flex-basis:100%}
 .lang{margin-top:16px}
 .grid{gap:14px}.card{padding:16px;border-radius:18px}.card h3{font-size:17px}
 .row{padding:12px 8px;margin:0 -8px;min-height:48px}
 .tips,.lablink{padding:16px;border-radius:18px}
 h2{margin:28px 0 12px}
 footer{padding:16px 16px 24px}
}
@media (max-width:380px){.row .go{padding:5px 10px}.seg button{padding:8px 16px}.brand img{height:44px}}
"""

JS = r"""
const I=__I18N__;
const q=document.getElementById('q'),cards=[...document.querySelectorAll('.card')],c=document.getElementById('count');
let lang='en';
/* In Farsi text, isolate each English run (names, calls like vfs_read()) so punctuation does not jump around. */
const esc=t=>t.replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const TOK='(?:[\'’][0-9]{2}|[\\/~]?[A-Za-z0-9_][A-Za-z0-9_.+#:%@=\\/~-]*(?:\\([A-Za-z0-9_*&.,:+\\/ \\-\\[\\]]*\\))*)';
const PAR='\\([A-Za-z0-9_*&.,:+\\/ \\-\\[\\]]*\\)';
const RUN=new RegExp(TOK+'(?: '+TOK+'| '+PAR+')*','g');
const bidi=t=>{let o='',l=0;for(const m of t.matchAll(RUN)){let r=m[0];const tl=r.match(/[.,:;=]+$/);if(tl)r=r.slice(0,-tl[0].length);
 if(!/[A-Za-z0-9]/.test(r))continue;o+=esc(t.slice(l,m.index))+'<bdi dir="ltr">'+esc(r)+'</bdi>';l=m.index+r.length;}return o+esc(t.slice(l));};
function f(){
 if(!q)return;
 const s=q.value.trim().toLowerCase();let n=0;
 document.querySelectorAll('.row').forEach(r=>{const m=!s||r.dataset.t.includes(s);r.classList.toggle('hidden',!m);if(m)n++;});
 cards.forEach(k=>k.classList.toggle('hidden',!!k.querySelector('.row')&&!k.querySelector('.row:not(.hidden)')));
 const S=I[lang];c.textContent=n===1?S.one:S.many.replace('{n}',n);
 document.getElementById('empty').classList.toggle('hidden',n>0);}
function setLang(l){
 lang=l;const S=I[l];
 document.documentElement.lang=l;document.documentElement.dir=l==='fa'?'rtl':'ltr';
 document.body.classList.toggle('fa',l==='fa');
 document.querySelectorAll('[data-k]').forEach(e=>{e.innerHTML=S[e.dataset.k];});
 document.querySelectorAll('[data-en]').forEach(e=>{
  if(l==='fa'&&e.dataset.fa){e.innerHTML=bidi(e.dataset.fa);}else{e.textContent=e.dataset.en;}});
 document.querySelectorAll('a.row').forEach(r=>{r.href=(l==='fa'&&r.dataset.hfa)?r.dataset.hfa:r.dataset.hen;});
 if(q)q.placeholder=S.ph;
 const pt=document.body.dataset;document.title=(l==='fa'?pt.tfa:pt.ten);
 document.querySelectorAll('.seg button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.l===l)));
 try{localStorage.setItem('azad.lang',l);}catch(e){}
 f();}
if(q)q.addEventListener('input',f);
let lang0=new URLSearchParams(location.search).get('lang');
if(lang0!=='fa'&&lang0!=='en'){try{lang0=localStorage.getItem('azad.lang');}catch(e){lang0=null;}}
setLang(lang0==='fa'?'fa':'en');
document.querySelector('.seg').addEventListener('click',e=>{const b=e.target.closest('button');if(b)setLang(b.dataset.l);});
addEventListener('keydown',e=>{if(q&&e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}});
"""


# ------------------------------------------------------------------ reading the course tree
def deck_title(path):
    """The <title> of a deck file (decks are bilingual: lesson.en.html / lesson.fa.html each have their own)."""
    try:
        m = re.search(r"<title>(.*?)</title>", path.read_text(encoding="utf-8"), re.S)
    except OSError:
        return ""
    return html.unescape(m.group(1)).strip() if m else ""


def split_title(title):
    """'03 · Concurrency — Advanced OS' -> ('03', 'Concurrency', 'Advanced OS'); lab titles have no course suffix."""
    num, _, rest = title.partition(" · ")
    name, _, course = rest.rpartition(" — ")
    if not name:
        name, course = rest, ""
    return num.strip(), name.strip(), course.strip()


def rel(p):
    return p.relative_to(ROOT).as_posix()


def discover():
    """{'term-1': {'n': '1', 'courses': [course, ...]}} where course = {'slug','en','fa','modules':[...],'ndecks'}."""
    terms = {}
    for term_dir in sorted(ROOT.glob("term-*")):
        if not term_dir.is_dir():
            continue
        courses = []
        for cdir in sorted(p for p in term_dir.iterdir() if p.is_dir()):
            modules, ndecks = [], 0
            fa_name = None
            for slides in sorted(cdir.glob("*/slides")):
                mod = slides.parent
                num, _, slug = mod.name.partition("-")
                decks = []
                for en in sorted(slides.glob("*.en.html")) + sorted(slides.glob("labs/*.en.html")):
                    fa = en.with_name(en.name.replace(".en.html", ".fa.html"))
                    fa = fa if fa.exists() else None
                    kind = "lab" if en.parent.name == "labs" else "lesson"
                    n_en, nm_en, _c = split_title(deck_title(en))
                    n_fa, nm_fa, c_fa = split_title(deck_title(fa)) if fa else (n_en, nm_en, "")
                    if kind == "lesson" and c_fa and not fa_name:
                        fa_name = c_fa
                    decks.append(
                        {
                            "kind": kind,
                            "name": en.name[: -len(".en.html")],
                            "en": en,
                            "fa": fa,
                            "num_en": n_en,
                            "num_fa": n_fa,
                            "t_en": nm_en,
                            "t_fa": nm_fa or nm_en,
                        }
                    )
                if not decks:
                    continue
                lesson = next((d for d in decks if d["kind"] == "lesson"), decks[0])
                modules.append(
                    {
                        "id": mod.name,
                        "num": num,
                        "en": lesson["t_en"] or slug.replace("-", " ").title(),
                        "fa": lesson["t_fa"] or slug.replace("-", " ").title(),
                        "decks": decks,
                    }
                )
                ndecks += len(decks)
            en_name = cdir.name.replace("-", " ").title()
            courses.append(
                {
                    "slug": cdir.name,
                    "dir": cdir,
                    "en": en_name,
                    "fa": fa_name or COURSE_FA.get(cdir.name, en_name),
                    "modules": modules,
                    "ndecks": ndecks,
                }
            )
        terms[term_dir.name] = {"n": re.sub(r"\D", "", term_dir.name) or term_dir.name, "courses": courses}
    return terms


def decks_json():
    """Every deck in teaching order (paths relative to the site root), so a deck can offer "next" on its last slide."""
    out = []
    for tname, term in discover().items():
        for course in term["courses"]:
            for mod in course["modules"]:
                for d in mod["decks"]:
                    lab = d["kind"] == "lab"
                    label = lambda n, t: f"{n} · {t}" if n and t else (t or n)  # noqa: E731
                    out.append(
                        {
                            "en": rel(d["en"]),
                            "fa": rel(d["fa"]) if d["fa"] else "",
                            "course": f"{tname}/{course['slug']}",
                            "title": {"en": label(d["num_en"], d["t_en"]), "fa": label(d["num_fa"], d["t_fa"])},
                            "lab": lab,
                        }
                    )
    return json.dumps(out, ensure_ascii=False)


# ------------------------------------------------------------------ page building
def _a(s):
    return html.escape(s, quote=True)


def _i18n(en, fa):
    return f'data-en="{_a(en)}" data-fa="{_a(fa)}"'


def _page(depth, crumbs, h1, sub_key, body, title_en, title_fa, search=False, tips=False, extra="", local=True):
    up = "../" * depth
    crumb_html = "".join(
        (
            f'<li><a href="{_a(href)}" {_i18n(en, fa)}></a></li>'
            if href
            else f'<li><span aria-current="page" {_i18n(en, fa)}></span></li>'
        )
        for en, fa, href in crumbs
    )
    search_html = (
        (
            '<div class="search"><input id="q" type="search" aria-label="Search decks" autofocus>'
            '<span class="count" id="count"></span></div>'
        )
        if search
        else ""
    )
    tips_html = (
        (
            '<div class="tips"><h3 data-k="tipsH"></h3><ul><li data-k="tip0"></li><li data-k="'
            + ("tip1" if local else "tip1site")
            + '"></li>'
            '<li data-k="tip2"></li></ul></div>'
        )
        if tips
        else ""
    )
    empty = '<p class="empty hidden" id="empty" data-k="none"></p>' if search else ""
    js = JS.replace("__I18N__", json.dumps(STRINGS, ensure_ascii=False))
    return f"""<!doctype html><html lang="en" dir="ltr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{_a(title_en)}</title>
<link rel="icon" href="{up}_shared/brand/azad-logo.png"><link rel="stylesheet" href="{FONTS_LINK}"><style>{CSS}</style></head>
<body data-ten="{_a(title_en)}" data-tfa="{_a(title_fa)}">
<header class="hero"><div class="wrap">
  <nav aria-label="Breadcrumb"><ol class="crumbs">{crumb_html}</ol></nav>
  <div class="brand"><span class="tile"><img src="{up}_shared/brand/azad-logo.png" alt="Islamic Azad University"></span>
  <div><h1 {_i18n(*h1)}></h1><p class="sub" data-k="{sub_key}"></p></div></div>
  {search_html}
  <div class="lang"><span data-k="langLabel"></span>
  <div class="seg" role="group" aria-label="Slides language"><button data-l="en" aria-pressed="true">English</button><button data-l="fa" aria-pressed="false">فارسی</button></div></div>
</div></header>
<main><div class="wrap">{extra}{body}{empty}{tips_html}</div></main>
<footer><div class="wrap" data-k="credit"></div></footer>
<script>{js}</script></body></html>"""


def _count_text(n_mod, n_deck):
    return (f"{n_mod} modules · {n_deck} slide decks", f"{n_mod} ماژول · {n_deck} اسلاید")


def render_home(local=False):
    terms = discover()
    cards = []
    for n in range(1, 5):
        name = f"term-{n}"
        courses = terms.get(name, {}).get("courses", [])
        with_slides = [c for c in courses if c["ndecks"]]
        if with_slides:
            nd = sum(c["ndecks"] for c in with_slides)
            en = f"{len(courses)} courses · {len(with_slides)} with slides · {nd} decks"
            fa = f"{len(courses)} درس · {len(with_slides)} با اسلاید · {nd} اسلاید"
            cards.append(
                f'<a class="card nav" href="{name}/"><h3><span class="n">{n}</span><span {_i18n(f"Term {n}", f"ترم {n}")}></span></h3>'
                f'<span class="d" {_i18n(en, fa)}></span><span class="go" data-k="open"></span></a>'
            )
        else:
            cards.append(
                f'<div class="card nav soon"><h3><span class="n">{n}</span><span {_i18n(f"Term {n}", f"ترم {n}")}></span></h3>'
                f'<span class="badge" data-k="soon"></span></div>'
            )
    lab = (
        (
            '<a class="lablink" href="_shared/browser-lab/index.html"><span><b data-k="labTitle"></b><span class="d" data-k="labBody"></span></span>'
            '<span class="go" data-k="labGo"></span></a>'
        )
        if local
        else ""
    )
    body = f'<h2 data-k="termsH"></h2><div class="grid">{"".join(cards)}</div>'
    return _page(
        0,
        [("Home", "صفحهٔ اصلی", None)],
        ("Course slides", "اسلایدهای درس‌ها"),
        "siteSub",
        body,
        "Course slides · Azad MSc",
        "اسلایدهای درس‌ها · کارشناسی ارشد آزاد",
        extra=lab,
    )


def render_term(tname):
    term = discover().get(tname)
    if not term:
        return None
    n = term["n"]
    cards = []
    for c in term["courses"]:
        if c["ndecks"]:
            en, fa = _count_text(len(c["modules"]), c["ndecks"])
            cards.append(
                f'<a class="card nav" href="{_a(c["slug"])}/"><h3><span class="n">{len(cards) + 1}</span><span {_i18n(c["en"], c["fa"])}></span></h3>'
                f'<span class="d" {_i18n(en, fa)}></span><span class="go" data-k="open"></span></a>'
            )
        else:
            cards.append(
                f'<div class="card nav soon"><h3><span class="n">{len(cards) + 1}</span><span {_i18n(c["en"], c["fa"])}></span></h3>'
                f'<span class="badge" data-k="soon"></span></div>'
            )
    body = f'<h2 data-k="coursesH"></h2><div class="grid">{"".join(cards)}</div>'
    return _page(
        1,
        [("Home", "صفحهٔ اصلی", "../"), (f"Term {n}", f"ترم {n}", None)],
        (f"Term {n}", f"ترم {n}"),
        "chooseCourse",
        body,
        f"Term {n} · Azad MSc",
        f"ترم {n} · کارشناسی ارشد آزاد",
    )


def render_course(tname, slug, local=True):
    term = discover().get(tname)
    course = next((c for c in (term or {"courses": []})["courses"] if c["slug"] == slug), None)
    if not course or not course["ndecks"]:
        return None
    n = term["n"]
    cards = []
    for mod in course["modules"]:
        lines = []
        for d in mod["decks"]:
            if d["kind"] == "lesson":
                t = '<b data-k="lesson"></b>'
                search = f"{mod['id']} lesson {d['t_en']} {d['t_fa']}"
            else:
                t = f"<b {_i18n(d['t_en'], d['t_fa'])}></b><small {_i18n(d['num_en'], d['num_fa'])}></small>"
                search = f"{mod['id']} {d['name']} {d['num_en']} {d['t_en']} {d['t_fa']}"
            hen = d["en"].relative_to(course["dir"]).as_posix()
            hfa = d["fa"].relative_to(course["dir"]).as_posix() if d["fa"] else ""
            lines.append(
                f'<a class="row {d["kind"]}{"" if d["fa"] else " noFa"}" href="{_a(hen)}" data-hen="{_a(hen)}" data-hfa="{_a(hfa)}" '
                f'data-t="{_a(search.lower())}"><span class="t">{t}</span>'
                f'<span><span class="note" data-k="noFa"></span><span class="go" data-k="open"></span></span></a>'
            )
        cards.append(
            f'<article class="card"><h3><span class="n">{html.escape(mod["num"])}</span><span {_i18n(mod["en"], mod["fa"])}></span></h3>{"".join(lines)}</article>'
        )
    body = f'<section class="course"><h2 {_i18n(course["en"], course["fa"])}></h2><div class="grid">{"".join(cards)}</div></section>'
    crumbs = [("Home", "صفحهٔ اصلی", "../../"), (f"Term {n}", f"ترم {n}", "../"), (course["en"], course["fa"], None)]
    return _page(
        2,
        crumbs,
        (course["en"], course["fa"]),
        "chooseModule",
        body,
        f"{course['en']} · Azad MSc",
        f"{course['fa']} · کارشناسی ارشد آزاد",
        search=True,
        tips=True,
        local=local,
    )


def render(path, local=True):
    """URL path -> ('html', text) | ('redirect', url) | None (not one of our pages)."""
    path = path.split("?", 1)[0].split("#", 1)[0]
    if path in ("/", "/index.html", "/slides"):
        return "html", render_home(local)
    m = re.fullmatch(r"/(term-\d+)(/|/index\.html)?", path)
    if m:
        page = render_term(m.group(1))
        if page is None:
            return None
        return ("html", page) if m.group(2) else ("redirect", f"/{m.group(1)}/")
    m = re.fullmatch(r"/(term-\d+)/([A-Za-z0-9_-]+)(/|/index\.html)?", path)
    if m:
        page = render_course(m.group(1), m.group(2), local)
        if page is None:
            return None
        return ("html", page) if m.group(3) else ("redirect", f"/{m.group(1)}/{m.group(2)}/")
    return None
