"""Build the course site (Home -> Term -> Course -> slides) as plain static files, for GitHub Pages.

Usage:  python _shared/tools/build_site.py [--out site]        (or: make site)

The output folder holds only what the site needs: the generated pages, every slide deck with its images, the shared
theme and the emblem. No kernel sources, notes or tools. All links are relative, so the same folder works at
https://<owner>.github.io/<repo>/, on a custom subdomain, or opened through any web server.

Security of the published site:
  * reveal.js and the fonts are copied INTO the site (_vendor/), from pinned, checksum-verified downloads, so visitors'
    browsers contact no third-party server at all (no Google Fonts, no CDN, nothing to track or compromise);
  * every page gets a strict Content-Security-Policy (<meta>) that only allows its own files, and Referrer-Policy
    no-referrer. GitHub Pages cannot send HTTP headers, so <meta> is the way to do it.

After building it checks that every internal link resolves and scans the output for e-mail addresses, so nothing
broken or private is published by accident. The exit code is the number of problems.
"""

import argparse
import base64
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sitegen  # noqa: E402

ROOT = sitegen.ROOT
VENDOR = ROOT / ".cache" / "vendor"  # reveal.js + fonts, written by fetch_assets.py
NOT_FOUND = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found</title><style>body{font:18px/1.6 system-ui,sans-serif;max-width:640px;margin:15vh auto;padding:0 20px;color:#0A1633}
a{color:#2F4BB0;font-weight:700}</style></head><body>
<h1>Page not found</h1><p>That page does not exist (anymore).</p>
<p><a id="home" href="/">Go to the course slides</a></p>
<script>/* project sites live under /<repo>/, so link to the first path segment there */
if (location.hostname.endsWith(".github.io")) { var s = location.pathname.split("/")[1]; if (s) document.getElementById("home").href = "/" + s + "/"; }</script>
</body></html>
"""


def ensure_vendor():
    """reveal.js and the fonts must exist locally so the site can serve them itself."""
    if not (VENDOR / "manifest.json").exists():
        print("downloading reveal.js and the fonts (pinned, checksum-verified) ...")
        subprocess.call([sys.executable, str(ROOT / "_shared" / "tools" / "fetch_assets.py")])
    if not (VENDOR / "manifest.json").exists():
        sys.exit(
            "cannot build the site without reveal.js and the fonts (the download failed). Check your internet connection."
        )


def localize(text, depth, mapping):
    """Point the CDN links at the site's own copies (_vendor/), relative to this file."""
    prefix = "../" * depth
    for remote, local in mapping.items():
        target = prefix + local.lstrip("/").replace(".cache/vendor/", "_vendor/", 1)
        for r in (remote, remote.replace("&", "&amp;")):
            text = text.replace(r, target)
    return text


def strip_private(text):
    """Published decks omit the speaker notes (teaching scripts) and the unfilled [Presenter] / [Professor] ... fields
    of the title slide. Your local decks keep both; use --keep-notes to publish the notes too."""
    text = re.sub(r'[ \t]*<aside class="notes">.*?</aside>[ \t]*\n?', "", text, flags=re.S)
    return re.sub(r'<div class="fields">.*?</div>', lambda m: "" if "[" in m.group(0) else m.group(0), text, flags=re.S)


def sha(content):
    return "'sha256-" + base64.b64encode(hashlib.sha256(content.encode("utf-8")).digest()).decode() + "'"


def is_deck(f, out):
    """A slide deck lives in a slides/ folder. (Term and Course pages are under term-N/ too but are not decks.)"""
    return "slides" in f.relative_to(out).parts


_JS_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "b": "\b", "f": "\f", "v": "\v"}


def speaker_view_hashes():
    """reveal.js's speaker view (key S) opens a popup and document.write()s a page with ONE inline <script> into it; the
    popup inherits our Content-Security-Policy, so that exact script must be allowed (by hash) or the view is dead.
    reveal.js is checksum-pinned, so the script is a fixed string: read it out of the vendored notes plugin and hash it."""
    js = (VENDOR / "reveal.js@5.1.0" / "plugin" / "notes" / "notes.js").read_text(encoding="utf-8")
    i = js.index('document.write("') + len("document.write(") + 1  # first character after the opening quote
    out = []
    while js[i] != '"':
        c = js[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        n = js[i + 1]
        if n == "x":
            out.append(chr(int(js[i + 2 : i + 4], 16)))
            i += 4
        elif n == "u":
            out.append(chr(int(js[i + 2 : i + 6], 16)))
            i += 6
        else:
            out.append(_JS_ESCAPES.get(n, n))
            i += 2
    page = "".join(out)
    scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
    if len(scripts) != 1:
        sys.exit(
            f"unexpected speaker view markup ({len(scripts)} inline scripts): update speaker_view_hashes() for this reveal.js version"
        )
    return [sha(s) for s in scripts]


def csp_for(text, deck):
    """Strict policy: only this site's own files. Generated pages allow exactly their own inline script/style by hash;
    decks have no inline scripts but use style="" attributes, so they need 'unsafe-inline' for styles only."""
    if deck:
        script, style = " ".join(["'self'", *speaker_view_hashes()]), "'self' 'unsafe-inline'"
        frame = "'self'"  # the speaker view shows the current and next slide in iframes of the same deck
    else:
        scripts = [sha(m) for m in re.findall(r"<script>(.*?)</script>", text, re.S)]
        styles = [sha(m) for m in re.findall(r"<style>(.*?)</style>", text, re.S)]
        script, style = " ".join(["'self'"] + scripts), " ".join(["'self'"] + styles)
        frame = "'none'"
    return (
        f"default-src 'none'; script-src {script}; style-src {style}; img-src 'self' data:; font-src 'self'; "
        f"connect-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; frame-src {frame}; manifest-src 'none'"
    )


def harden(out, keep_notes=False):
    """Rewrite every page: self-hosted assets, CSP and referrer policy."""
    mapping = json.loads((VENDOR / "manifest.json").read_text(encoding="utf-8"))
    for f in sorted(out.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        depth = len(f.relative_to(out).parts) - 1
        text = localize(text, depth, mapping)
        if not keep_notes and is_deck(f, out):
            text = strip_private(text)
        meta = (
            f'<meta http-equiv="Content-Security-Policy" content="{csp_for(text, is_deck(f, out))}">\n'
            '<meta name="referrer" content="no-referrer">'
        )
        text, n = re.subn(r'(<meta charset="utf-8">)', lambda m, meta=meta: m.group(1) + "\n" + meta, text, count=1)
        if n != 1:
            sys.exit(f"{f}: no <meta charset> to attach the security policy to")
        write(f, text)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build(out, keep_notes=False):
    if out.exists():
        if out.resolve() in (ROOT, ROOT.parent) or ROOT.resolve() not in out.resolve().parents:
            sys.exit(
                f"refusing to delete {out}: the output folder must be a new folder inside the repository (default: site/)"
            )
        shutil.rmtree(out)
    out.mkdir(parents=True)
    terms = sitegen.discover()
    n_decks = 0

    write(out / "index.html", sitegen.render_home(local=False))
    for tname, term in terms.items():
        if not any(c["ndecks"] for c in term["courses"]):
            continue
        write(out / tname / "index.html", sitegen.render_term(tname))
        for c in term["courses"]:
            if not c["ndecks"]:
                continue
            write(out / tname / c["slug"] / "index.html", sitegen.render_course(tname, c["slug"]))
            for mod in c["modules"]:
                for d in mod["decks"]:
                    for p in (d["en"], d["fa"]):
                        if p:
                            copy(p, out / p.relative_to(ROOT))
                            n_decks += 1
                assets = c["dir"] / mod["id"] / "slides" / "assets"
                for f in assets.rglob("*") if assets.is_dir() else []:
                    if f.is_file():
                        copy(f, out / f.relative_to(ROOT))

    for name in ("azad-theme.css", "azad-deck.js"):
        copy(ROOT / "_shared" / "theme" / name, out / "_shared" / "theme" / name)
    for name in ("azad-logo.png", "azad-logo.svg"):
        copy(ROOT / "_shared" / "brand" / name, out / "_shared" / "brand" / name)
    ensure_vendor()
    for sub in ("reveal.js@5.1.0", "fonts"):
        shutil.copytree(VENDOR / sub, out / "_vendor" / sub)
    write(out / "_decks.json", sitegen.decks_json())
    write(out / ".nojekyll", "")  # serve files as they are, no Jekyll processing
    write(out / "404.html", NOT_FOUND)
    harden(out, keep_notes)
    return n_decks


def check(out):
    """Every relative href/src must exist; no e-mail addresses in the published files."""
    problems = 0
    for f in sorted(out.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src|data-hen|data-hfa)="([^"]*)"', text):
            ref = m.group(1)
            if not ref or ref.startswith(("http:", "https:", "//", "#", "data:", "mailto:", "javascript:")):
                continue
            ref = re.split(r"[?#]", ref)[0]
            if not ref:
                continue
            target = (f.parent / ref).resolve()
            if ref.endswith("/"):
                target = target / "index.html"
            if not target.exists() and f.name != "404.html":
                problems += 1
                print(f"BROKEN LINK  {f.relative_to(out).as_posix()}: {m.group(1)}")
        for e in set(re.findall(r"[\w.+-]+@[A-Za-z][\w-]*\.[A-Za-z]{2,}", text)):
            if not e.endswith((".png", ".svg", ".js", ".css")):
                problems += 1
                print(f"E-MAIL FOUND {f.relative_to(out).as_posix()}: {e}")
    return problems


def check_private(out):
    """Nothing the published decks must hide may remain: speaker notes, unfilled placeholder fields."""
    problems = 0
    for f in sorted(out.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        if 'class="notes"' in text or re.search(r'<div class="fields">[^<]*<span>[^<]*<b>[^<]*</b>\[', text):
            problems += 1
            print(
                f"PRIVATE      {f.relative_to(out).as_posix()}: speaker notes or placeholder fields are still published"
            )
    return problems


def check_csp(out):
    """Every page must carry a policy, and each inline <script>/<style> of a generated page must be allowed by its hash
    (otherwise the browser would silently refuse to run it). Decks must have no inline script at all."""
    problems = 0
    for f in sorted(out.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        m = re.search(r'Content-Security-Policy" content="([^"]+)"', text)
        rel = f.relative_to(out).as_posix()
        if not m:
            problems += 1
            print(f"NO CSP       {rel}")
            continue
        csp = m.group(1)
        scripts = [s for s in re.findall(r"<script>(.*?)</script>", text, re.S) if s.strip()]
        styles = re.findall(r"<style>(.*?)</style>", text, re.S)
        if is_deck(f, out):
            if scripts or re.search(r"\son\w+=\"", text):
                problems += 1
                print(f"INLINE CODE  {rel}: a deck has inline script or event handlers (the policy forbids them)")
            continue
        for kind, items in (("script", scripts), ("style", styles)):
            for item in items:
                if sha(item) not in csp:
                    problems += 1
                    print(f"CSP MISMATCH {rel}: an inline <{kind}> is not allowed by the page's policy")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--out", type=pathlib.Path, default=ROOT / "site", help="output folder (default: site/, deleted and rebuilt)"
    )
    ap.add_argument(
        "--keep-notes", action="store_true", help="also publish the speaker notes (default: they stay private)"
    )
    a = ap.parse_args()
    n = build(a.out, a.keep_notes)
    files = [p for p in a.out.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print(f"site built: {a.out}  ({len(files)} files, {size / 1e6:.1f} MB, {n} slide decks)")
    bad = check(a.out) + check_csp(a.out) + (0 if a.keep_notes else check_private(a.out))
    print(
        "checks: "
        + (
            "internal links resolve, no e-mail addresses, every page has a matching security policy"
            if not bad
            else f"{bad} problem(s) above"
        )
    )
    sys.exit(bad)


if __name__ == "__main__":
    main()
