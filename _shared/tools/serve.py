"""Serve the repository so the slide decks work, with an index page of every deck.

Usage:  python _shared/tools/serve.py [--port 8000] [--open PATH]

Only the Python standard library is needed (no Node.js). reveal.js and the
fonts load from public CDNs, so the browser needs internet access.
Decks need a web server (not file://) because they load ../../_shared/theme.
"""

import argparse
import functools
import http.server
import json
import os
import pathlib
import re
import signal
import socketserver
import sys
import webbrowser

import sitegen  # Home / Term / Course pages and the deck list, shared with build_site.py

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / ".cache" / "vendor" / "manifest.json"  # written by fetch_assets.py


def offline_map():
    """CDN URL -> local path, if `make assets` has cached them; else {} (decks use the CDN)."""
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = dict(m)
    out.update({k.replace("&", "&amp;"): v for k, v in m.items()})  # HTML may escape '&'
    return out


class Handler(http.server.SimpleHTTPRequestHandler):
    # ES modules (.mjs) must be served as JavaScript or browsers refuse them; the browser lab needs this.
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mjs": "text/javascript",
        ".wasm": "application/wasm",
    }

    LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]", "::1"}

    def _forbidden(self):
        """DNS rebinding defence: a web page on another site can point its own hostname at 127.0.0.1 and then read this
        server. Real browsers send the page's hostname in Host, so refuse anything that is not localhost.
        Also never serve the git folder (history, config)."""
        host = (
            (self.headers.get("Host") or "").rsplit(":", 1)[0]
            if not (self.headers.get("Host") or "").startswith("[")
            else "[::1]"
        )
        path = self.path.split("?", 1)[0]
        return host not in self.LOCAL_HOSTS or re.search(r"(^|/)\.git(/|$)", path) is not None

    def do_HEAD(self):
        if self._forbidden():
            return self.send_error(403, "Forbidden")
        return super().do_HEAD()

    def _send(self, ctype, text, no_cache=False):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if no_cache:
            self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self._forbidden():
            return self.send_error(403, "Forbidden")
        if self.path.split("?", 1)[0] == "/_decks.json":
            return self._send("application/json; charset=utf-8", sitegen.decks_json(), no_cache=True)
        page = sitegen.render(self.path, local=True)  # "/", "/term-1/", "/term-1/<course>/"
        if page:
            kind, value = page
            if kind == "redirect":
                self.send_response(301)
                self.send_header("Location", value)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            for remote, here in offline_map().items():  # fonts: use the offline cache when it exists
                value = value.replace(remote, here)
            return self._send("text/html; charset=utf-8", value)
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path == "/favicon.ico":  # browsers ask for this on every page; answer with the emblem
            self.path = "/_shared/brand/azad-logo.png"
            return super().do_GET()
        local = ROOT / path.lstrip("/")
        mapping = offline_map()
        if mapping and path.endswith(".html") and local.is_file() and ROOT in local.resolve().parents:
            text = local.read_text(encoding="utf-8")
            for remote, here in mapping.items():
                text = text.replace(remote, here)
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, fmt, *args):  # keep the terminal quiet except errors
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


RUN = ROOT / ".cache" / "run"  # one <port>.pid per running server, so `make stop` can find them


def stop_all():
    """Stop every server started by this script (any port). Returns how many were stopped."""
    n = 0
    for pidfile in sorted(RUN.glob("serve-*.pid")):
        try:
            pid = int(pidfile.read_text().strip())
            os.kill(pid, signal.SIGTERM)  # TerminateProcess on Windows
            n += 1
            print(f"stopped slide server pid {pid} ({pidfile.stem.replace('serve-', 'port ')})")
        except (ValueError, OSError):
            pass  # already gone
        pidfile.unlink(missing_ok=True)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument(
        "--open", metavar="PATH", default=None, help="open this repo-relative page in the browser (default: the index)"
    )
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--stop", action="store_true", help="stop all running slide servers and exit")
    a = ap.parse_args()
    if a.stop:
        if not stop_all():
            print("no slide server running")
        return

    handler = functools.partial(Handler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.ThreadingTCPServer(("127.0.0.1", a.port), handler)
    except OSError as e:
        sys.exit(f"cannot listen on 127.0.0.1:{a.port} ({e}). Try: make slides PORT={a.port + 1}")
    url = f"http://127.0.0.1:{a.port}/" + (a.open.lstrip("/") if a.open else "")
    mode = "offline: cached assets" if offline_map() else "online: CDN (run make assets to cache)"
    print(f"Serving {ROOT}  [{mode}]\n  index: http://127.0.0.1:{a.port}/\n  open:  {url}\nCtrl+C to stop.", flush=True)
    RUN.mkdir(parents=True, exist_ok=True)
    pidfile = RUN / f"serve-{a.port}.pid"
    pidfile.write_text(str(os.getpid()))
    if not a.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        pidfile.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
