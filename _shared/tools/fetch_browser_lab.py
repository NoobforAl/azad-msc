"""Download what the browser lab needs (about 13 MB) into .cache/vendor/browser-lab/.

Usage:  python _shared/tools/fetch_browser_lab.py [--force]

Everything is fetched from a pinned URL and checked against a SHA-256, so you get exactly the files the lab was
tested with. If a checksum ever differs, the tool stops instead of using the file.

  v86 0.5.473        x86 PC emulator in WebAssembly     BSD-2-Clause   (libv86.js, v86.wasm, BIOS files)
  Linux 6.8.12 image 32-bit Buildroot kernel + busybox   GPL           (built by the v86 author, hosted on i.copy.sh)
  xterm.js 5.5.0     terminal widget                     MIT

Nothing here is stored in git; the files only live in .cache/ on the machine that runs the lab.
"""

import argparse
import hashlib
import json
import pathlib
import ssl
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEST = ROOT / ".cache" / "vendor" / "browser-lab"

# name -> (url, size in bytes, sha256)
FILES = {
    "libv86.js": (
        "https://cdn.jsdelivr.net/npm/v86@0.5.473/build/libv86.js",
        359857,
        "e257912c4a1129e36a86c1e2df69904ab969d87bffd24aa6676e84d6ddffc1c6",
    ),
    "v86.wasm": (
        "https://cdn.jsdelivr.net/npm/v86@0.5.473/build/v86.wasm",
        2007347,
        "2f0c4150f266415b754a84a32e6f8e4c975a1d3abb94c78b047fa30027db1ef1",
    ),
    "seabios.bin": (
        "https://raw.githubusercontent.com/copy/v86/315b2b0b758703ef0e6cc7b4088d6068f83f3c20/bios/seabios.bin",
        131072,
        "73e3f359102e3a9982c35fce98eb7cd08f18303ac7f1ba6ebfbe6cdc1c244d98",
    ),
    "vgabios.bin": (
        "https://raw.githubusercontent.com/copy/v86/315b2b0b758703ef0e6cc7b4088d6068f83f3c20/bios/vgabios.bin",
        36352,
        "a4bc0d80cc3ca028c73dafa8fee396b8d054ce87ebd8abfbd31b06b437607880",
    ),
    "buildroot-bzimage68.bin": (
        "https://i.copy.sh/buildroot-bzimage68.bin",
        10068480,
        "507a759c70ab7a490a233be454d0b5b88bc667956a410b531cb4edc091e2eb1c",
    ),
    "xterm.js": (
        "https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/lib/xterm.js",
        289441,
        "1f991ac3b4b283ebf96e60ae23a00a52765dd3a2e46fa6fdda9f1aab032f7495",
    ),
    "xterm.css": (
        "https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/css/xterm.css",
        5559,
        "ba8e6985669488981ccf40c0cefe3aba80722cb6c92de7ad628b0bd717faf2b6",
    ),
    "addon-fit.js": (
        "https://cdn.jsdelivr.net/npm/@xterm/addon-fit@0.10.0/lib/addon-fit.js",
        1497,
        "bdaefa370b1bfc42ee88d46fe6072400902a4d4b2d45cd93438dda9b23c97089",
    ),
    "LICENSE-v86": (
        "https://raw.githubusercontent.com/copy/v86/315b2b0b758703ef0e6cc7b4088d6068f83f3c20/LICENSE",
        1306,
        "3f61ba65e3215b09ef264ba8d777d73c19644309fbb705967634eb5147e500a0",
    ),
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "azad-course-workspace"})
    with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="download again even if the files are already here")
    a = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    total = sum(size for _u, size, _h in FILES.values())
    print(f"browser lab files: {len(FILES)} files, {total / 1e6:.1f} MB -> {DEST.relative_to(ROOT).as_posix()}")
    for name, (url, size, digest) in FILES.items():
        path = DEST / name
        if path.exists() and not a.force and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            print(f"  ok       {name}")
            continue
        print(f"  fetching {name} ({size / 1e6:.1f} MB) ...", flush=True)
        try:
            data = fetch(url)
        except OSError as e:
            sys.exit(f"download failed for {url}: {e}. Check your internet connection and run again.")
        if hashlib.sha256(data).hexdigest() != digest:
            sys.exit(
                f"CHECKSUM MISMATCH for {name} ({url}). The file changed upstream, so it was NOT saved. "
                "Please report this (the lab was tested with the pinned version)."
            )
        path.write_bytes(data)
    (DEST / "manifest.json").write_text(
        json.dumps({n: {"size": s, "sha256": h} for n, (_u, s, h) in FILES.items()}, indent=1), encoding="utf-8"
    )
    print("browser lab ready.")


if __name__ == "__main__":
    main()
