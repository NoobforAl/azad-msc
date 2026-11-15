"""Export slide decks to PDF or PowerPoint (PPTX).

Usage:
  python _shared/tools/export_deck.py DECK.html [DECK.html ...] [--format pdf|pptx|both]
  python _shared/tools/export_deck.py --module 02 [--lang fa] [--lab 03 | --all]   (or: make pdf M=02 L=fa)
                                      [--out DIR] [--transition fade|push|wipe|none] [--browser PATH]

  PDF   vector pages, one per slide, final state of every animation (needs Edge, Chrome or Chromium).
  PPTX  one full-bleed 1920x1080 picture per slide, speaker notes copied from <aside class="notes">,
        and a slide transition (--transition). Needs:  pip install python-pptx
        The slides are pictures: they look exactly like the deck but their text is not editable, and
        build animations (fragments) are flattened to the final state. Edit the HTML deck instead.

Only the Python standard library is needed for PDF. The deck is served by the same tiny local server as
`make slides`, so the offline asset cache is used when it exists.
"""

import argparse
import concurrent.futures as cf
import functools
import html.parser
import os
import pathlib
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import serve  # noqa: E402  (shares the Handler, the offline asset map and ROOT)

ROOT = serve.ROOT
W, H = 1920, 1080


# ---------------------------------------------------------------- browser
def browser_candidates(explicit=None):
    names = []
    if explicit:
        names.append(explicit)
    if os.environ.get("BROWSER_BIN"):
        names.append(os.environ["BROWSER_BIN"])
    pf = [os.environ.get(k, "") for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    for base in filter(None, pf):
        names += [base + r"\Microsoft\Edge\Application\msedge.exe", base + r"\Google\Chrome\Application\chrome.exe"]
    names += [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for n in (
        "microsoft-edge",
        "msedge",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
    ):
        p = shutil.which(n)
        if p:
            names.append(p)
    seen, out = set(), []
    for n in names:
        if n and n not in seen and pathlib.Path(n).exists():
            seen.add(n)
            out.append(n)
    return out


NO_SANDBOX = False  # set by --no-sandbox: only for containers where Chrome cannot start otherwise


def run_browser(browser, args, url, timeout=180):
    """Run one headless job in a fresh profile. The browser sandbox stays ON unless you pass --no-sandbox."""
    prof = tempfile.mkdtemp(prefix="azad-export-")  # fresh profile: no stale cache, no clash with the user's browser
    try:
        for extra in [["--no-sandbox"]] if NO_SANDBOX else [[]]:
            cmd = [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-first-run",
                "--disable-extensions",
                f"--user-data-dir={prof}",
                "--virtual-time-budget=15000",
                *extra,
                *args,
                url,
            ]
            try:
                r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout)
            except subprocess.TimeoutExpired:
                continue
            if r.returncode == 0:
                return r
        return None
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def pick_browser(explicit, probe_url):
    for b in browser_candidates(explicit):
        r = run_browser(b, ["--dump-dom"], probe_url, timeout=90)
        if r is not None and "<html" in (r.stdout or ""):
            return b, r.stdout
    return None, ""


# ---------------------------------------------------------------- server
def start_server():
    handler = functools.partial(serve.Handler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# ---------------------------------------------------------------- deck parsing (notes + titles)
class DeckParser(html.parser.HTMLParser):
    """Collects, per top-level <section> of .slides: the speaker notes and the first heading."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_slides = False
        self.slides_depth = 0  # div nesting inside .slides is not needed: only section depth matters
        self.sec_depth = 0
        self.cur = None
        self.slides = []
        self.in_notes = False
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "slides" in (a.get("class") or "").split():
            self.in_slides = True
        if not self.in_slides:
            return
        if tag == "section":
            self.sec_depth += 1
            if self.sec_depth == 1:
                self.cur = {"notes": [], "title": ""}
                self.slides.append(self.cur)
        elif self.cur is not None:
            if tag == "aside" and "notes" in (a.get("class") or "").split():
                self.in_notes = True
            elif tag in ("h1", "h2") and not self.cur["title"]:
                self.in_title = True

    def handle_endtag(self, tag):
        if not self.in_slides:
            return
        if tag == "section":
            self.sec_depth -= 1
            if self.sec_depth == 0:
                self.cur = None
        elif tag == "aside":
            self.in_notes = False
        elif tag in ("h1", "h2"):
            self.in_title = False

    def handle_data(self, data):
        if self.cur is None:
            return
        if self.in_notes:
            self.cur["notes"].append(data)
        elif self.in_title:
            self.cur["title"] += data


def parse_deck(path):
    p = DeckParser()
    p.feed(path.read_text(encoding="utf-8"))
    out = []
    for s in p.slides:
        notes = re.sub(r"\n[ \t]+", "\n", "".join(s["notes"])).strip()
        out.append({"title": " ".join(s["title"].split()), "notes": notes})
    return out


# ---------------------------------------------------------------- exporters
def deck_url(httpd, path, query):
    rel = path.resolve().relative_to(ROOT).as_posix()
    return f"http://127.0.0.1:{httpd.server_address[1]}/{rel}?{query}"


def export_pdf(browser, httpd, deck, out_file):
    tmp = out_file.with_suffix(".tmp.pdf")
    r = run_browser(
        browser, ["--no-pdf-header-footer", f"--print-to-pdf={tmp}"], deck_url(httpd, deck, "print-pdf"), 240
    )
    if r is None or not tmp.exists() or tmp.stat().st_size < 1000:
        tmp.unlink(missing_ok=True)
        return None
    data = tmp.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
    tmp.replace(out_file)
    return pages


def is_blank(png):
    """True if the capture is a single flat colour (the page had not rendered when the screenshot fired)."""
    from PIL import Image  # installed together with python-pptx

    with Image.open(png) as im:
        colors = im.convert("RGB").getcolors(maxcolors=4)
    return colors is not None and len(colors) <= 2


def screenshot(browser, httpd, deck, i, png, attempts=4):
    """Headless captures are occasionally empty under load, so verify each one and retry."""
    for _ in range(attempts):
        png.unlink(missing_ok=True)
        r = run_browser(
            browser, [f"--window-size={W},{H}", f"--screenshot={png}"], deck_url(httpd, deck, "export") + f"#/{i}", 180
        )
        if r is not None and png.exists() and png.stat().st_size > 1000 and not is_blank(png):
            return True
    return False


def add_transition(slide, kind):
    from lxml import etree

    if kind == "none":
        return
    ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    inner = {"fade": "<p:fade/>", "push": '<p:push dir="l"/>', "wipe": '<p:wipe dir="l"/>'}[kind]
    el = etree.fromstring(f'<p:transition xmlns:p="{ns}" spd="med">{inner}</p:transition>')
    sld = slide._element
    clr = sld.find(f"{{{ns}}}clrMapOvr")
    (clr.addnext if clr is not None else sld.append)(el)


def export_pptx(browser, httpd, deck, out_file, transition, jobs=1):
    try:
        from pptx import Presentation
        from pptx.util import Inches
    except ImportError:
        sys.exit("PPTX export needs python-pptx:  pip install python-pptx")
    info = parse_deck(deck)
    n = len(info)
    if n == 0:
        return None
    work = pathlib.Path(tempfile.mkdtemp(prefix="azad-slides-"))
    try:
        pngs = [work / f"s{i:03d}.png" for i in range(n)]
        with cf.ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
            ok = list(ex.map(lambda i: screenshot(browser, httpd, deck, i, pngs[i]), range(n)))
        if not all(ok):
            bad = [i + 1 for i, v in enumerate(ok) if not v]
            print(f"  failed to capture slide(s): {bad}", file=sys.stderr)
            return None
        prs = Presentation()
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
        blank = prs.slide_layouts[6]
        for i, png in enumerate(pngs):
            s = prs.slides.add_slide(blank)
            pic = s.shapes.add_picture(str(png), 0, 0, width=prs.slide_width, height=prs.slide_height)
            pic.name = f"Slide {i + 1}"
            pic._element.nvPicPr.cNvPr.set("descr", info[i]["title"] or f"Slide {i + 1}")
            if info[i]["notes"]:
                s.notes_slide.notes_text_frame.text = info[i]["notes"]
            add_transition(s, transition)
        prs.core_properties.title = deck.stem
        prs.save(str(out_file))
        return n
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------- main


def select_decks(a):
    """Resolve --module/--lab/--all/--lang to deck files (same rules as `make deck`)."""
    if not a.module:
        return []
    mods = sorted((ROOT / a.course).glob(f"{a.module}-*/slides"))
    if not mods:
        sys.exit(f"no module {a.module} in {a.course} (try: make list)")
    slides = mods[0]
    lesson = slides / f"lesson.{a.lang}.html"
    labs = sorted(slides.glob(f"labs/*.{a.lang}.html"))
    if a.all:
        found = [lesson] + labs
    elif a.lab:
        found = [p for p in labs if p.name.startswith(f"{a.lab}-")]
    else:
        found = [lesson]
    found = [p for p in found if p.is_file()]
    if not found:
        sys.exit(
            f"deck not found for module {a.module}"
            + (f" lab {a.lab}" if a.lab else "")
            + f" [{a.lang}] (try: make list)"
        )
    return found


def out_name(deck):
    """advanced-operating-systems_01-architecture_lesson.en  (course, module, deck)"""
    parts = deck.resolve().relative_to(ROOT).parts
    course = parts[1] if len(parts) > 1 else ""
    module = parts[2] if len(parts) > 2 else ""
    stem = deck.name[: -len(".html")]
    if deck.parent.name == "labs":
        stem = "lab-" + stem
    return "_".join(x for x in (course, module, stem) if x)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("decks", nargs="*", type=pathlib.Path, help="deck .html files (or use --module)")
    ap.add_argument("--course", default="term-1/advanced-operating-systems", help="course folder (with --module)")
    ap.add_argument("--module", help="module number, e.g. 01: export that module's lesson deck")
    ap.add_argument("--lang", default="en", choices=["en", "fa"])
    ap.add_argument("--lab", help="with --module: the lab deck number instead of the lesson")
    ap.add_argument("--all", action="store_true", help="with --module: the lesson and every lab deck")
    ap.add_argument("--format", choices=["pdf", "pptx", "both"], default="pdf")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "exports")
    ap.add_argument(
        "--transition",
        choices=["fade", "push", "wipe", "none"],
        default="fade",
        help="slide transition written into the PPTX (default: fade)",
    )
    ap.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="parallel slide captures for PPTX (default 1: parallel headless browsers often return blank pages)",
    )
    ap.add_argument(
        "--no-sandbox", action="store_true", help="turn the browser sandbox off (only inside containers that need it)"
    )
    ap.add_argument("--browser", help="path to Edge/Chrome/Chromium (auto-detected otherwise)")
    a = ap.parse_args()

    a.decks = list(a.decks) + select_decks(a)
    if not a.decks:
        ap.error("give deck files, or --module NN")
    global NO_SANDBOX
    NO_SANDBOX = a.no_sandbox
    decks = []
    for d in a.decks:
        d = d if d.is_absolute() else pathlib.Path.cwd() / d
        if not d.is_file() or d.suffix != ".html":
            sys.exit(f"not a deck: {d}")
        try:
            d.resolve().relative_to(ROOT)
        except ValueError:
            sys.exit(f"deck must be inside the repository: {d}")
        decks.append(d)

    httpd = start_server()
    try:
        browser, _ = pick_browser(a.browser, deck_url(httpd, decks[0], "export"))
        if not browser:
            sys.exit(
                "no working Edge/Chrome/Chromium found (tried: %s). Install one or pass --browser PATH."
                % (", ".join(browser_candidates(a.browser)) or "none detected")
            )
        print(f"browser: {browser}")
        a.out.mkdir(parents=True, exist_ok=True)
        failed = 0
        for deck in decks:
            base = out_name(deck)
            print(f"{deck.relative_to(ROOT).as_posix()}")
            if a.format in ("pdf", "both"):
                f = a.out / f"{base}.pdf"
                pages = export_pdf(browser, httpd, deck, f)
                if pages is None:
                    print("  PDF: FAILED", file=sys.stderr)
                    failed += 1
                else:
                    print(f"  PDF : {f}  ({pages} pages, {f.stat().st_size // 1024} KB)")
            if a.format in ("pptx", "both"):
                f = a.out / f"{base}.pptx"
                n = export_pptx(browser, httpd, deck, f, a.transition, a.jobs)
                if n is None:
                    print("  PPTX: FAILED", file=sys.stderr)
                    failed += 1
                else:
                    print(f"  PPTX: {f}  ({n} slides, {f.stat().st_size // 1024} KB)")
        sys.exit(1 if failed else 0)
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
