"""Download everything the slide decks load from the internet into .cache/vendor/ (once).

Usage: python _shared/tools/fetch_assets.py [--force]      slide assets (~0.6 MB)
       python _shared/tools/fetch_assets.py --vm            + lab-VM downloads (~0.8 GB) into .cache/downloads

Afterwards serve.py rewrites the CDN links on the fly, so decks work offline.
Nothing is installed: these are plain files (reveal.js 5.1.0 + the three web fonts).
"""

import hashlib
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
VENDOR = ROOT / ".cache" / "vendor"
MANIFEST = VENDOR / "manifest.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

REVEAL = "https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/"
REVEAL_FILES = ["dist/reveal.css", "dist/reveal.js", "plugin/notes/notes.js"]
# SHA-256 of reveal.js 5.1.0 (npm releases never change). A download that does not match is rejected, not used.
REVEAL_SHA256 = {
    "dist/reveal.css": "9cbc5082797d938f0ee780328790a131ae3d7bc5c09c176e77927c174f29e60a",
    "dist/reveal.js": "9736bf3d8918e391e8c07c85c53773800d4004dc25f948916e319ca371ca881a",
    "plugin/notes/notes.js": "288fe7cb27ff696a3e1c137b22b0cd117395a84dba2a703e2bfc3136e65612a8",
}
FONTS = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400..800&family=Vazirmatn:wght@400..800"
    "&family=JetBrains+Mono:wght@500;700&display=swap"
)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


DL = ROOT / ".cache" / "downloads"
MAINLINE = "https://kernel.ubuntu.com/mainline/v6.18.63/amd64/"
MAINLINE_V = "6.18.63-061863.202611101835"
VM_FILES = [  # same names create-vm-virtualbox.ps1 / create-vm.sh look for
    (
        "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.vmdk",
        "noble-server-cloudimg-amd64.vmdk",
    ),
] + [
    (MAINLINE + f, "mainline-6.18.63/" + f)
    for f in (
        f"linux-headers-6.18.63-061863-generic_{MAINLINE_V}_amd64.deb",
        f"linux-headers-6.18.63-061863_{MAINLINE_V}_all.deb",
        f"linux-image-unsigned-6.18.63-061863-generic_{MAINLINE_V}_amd64.deb",
        f"linux-modules-6.18.63-061863-generic_{MAINLINE_V}_amd64.deb",
    )
]


def fetch_vm_files():
    """Download the VM inputs once; later VM builds reuse them."""
    if sys.platform.startswith("linux"):  # libvirt uses the qcow2 .img instead of the .vmdk
        VM_FILES[0] = (
            "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img",
            "noble-server-cloudimg-amd64.img",
        )
    for url, name in VM_FILES:
        dest = DL / name
        if dest.exists():
            print("  cached", name)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        print("  download", url)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        part.replace(dest)
    total = sum(p.stat().st_size for p in DL.rglob("*") if p.is_file())
    print(f"vm downloads: {total // (1 << 20)} MiB in {DL.relative_to(ROOT)}")


def main():
    force = "--force" in sys.argv
    if "--vm" in sys.argv:
        try:
            fetch_vm_files()
        except OSError as e:
            print(f"vm downloads: failed ({e}); rerun to resume")
            return 1
    if MANIFEST.exists() and not force:
        print(f"assets: cached in {VENDOR.relative_to(ROOT)} (use --force to refresh)")
        return 0
    mapping = {}
    try:
        for f in REVEAL_FILES:
            local = VENDOR / "reveal.js@5.1.0" / f
            data = get(REVEAL + f)
            if hashlib.sha256(data).hexdigest() != REVEAL_SHA256[f]:
                print(
                    f"assets: CHECKSUM MISMATCH for {REVEAL + f}. The file was NOT saved. Decks still work online via the CDN."
                )
                return 1
            save(local, data)
            mapping[REVEAL + f] = "/" + local.relative_to(ROOT).as_posix()
            print("  got", REVEAL + f)
        css = get(FONTS).decode("utf-8")
        urls = sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)))
        for i, u in enumerate(urls):
            name = f"font-{i:03d}" + pathlib.PurePosixPath(u).suffix
            font = get(u)
            if font[:4] != b"wOF2":  # only accept real woff2 font files from fonts.gstatic.com
                print(f"assets: {u} is not a woff2 font; refusing it.")
                return 1
            save(VENDOR / "fonts" / name, font)
            css = css.replace(u, name)  # CSS and font files sit in the same folder
        save(VENDOR / "fonts" / "fonts.css", css.encode("utf-8"))
        mapping[FONTS] = "/" + (VENDOR / "fonts" / "fonts.css").relative_to(ROOT).as_posix()
        print(f"  got fonts ({len(urls)} font files)")
    except OSError as e:
        print(f"assets: download failed ({e}). Decks still work online via the CDN.")
        return 1
    save(MANIFEST, json.dumps(mapping, indent=1).encode("utf-8"))
    total = sum(p.stat().st_size for p in VENDOR.rglob("*") if p.is_file())
    print(f"assets: cached {len(mapping)} URLs, {total // 1024} KiB in {VENDOR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
