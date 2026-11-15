# Security

This repository is **public**. It holds course notes, slide decks, small helper tools and lab scripts. It must never
contain passwords, tokens, private keys, or personal data.

## Before you push

```bash
make fix             # lint + format the code (CI runs the check-only version, make lint)
make security        # python _shared/tools/security_scan.py: secrets, e-mail addresses, public IPs, personal paths
```

The same scan runs in the publishing workflow (`.github/workflows/pages.yml`) and stops the deployment if it finds
anything. Never commit a `.env` file, an SSH or TLS key, or a cloud credential. Use your GitHub **noreply** e-mail for
commits (Settings > Emails > "Keep my email addresses private").

## What the published website does to stay safe

- **No third-party requests.** reveal.js and the fonts are copied into the site from checksum-pinned downloads, so a
  visitor's browser contacts only the site itself (no CDN, no Google Fonts).
- **Strict Content-Security-Policy** on every page (set with a `<meta>` tag, because GitHub Pages cannot send HTTP
  headers) and `Referrer-Policy: no-referrer`. The build fails if a page's policy does not match its inline code.
- **Private teaching material stays private.** The published decks omit the speaker notes and unfilled title-slide placeholders (`build_site.py --keep-notes` opts in), and every page states that it is unofficial study material.
- **Static files only**: no server code, no forms, no cookies, no accounts. Language choice and lab progress stay in
  the visitor's own browser (`localStorage`).
- Links to outside sites use plain hyperlinks; nothing from those sites is loaded into our pages.

## Local tools

- `serve.py` listens on `127.0.0.1` only, answers only requests addressed to `localhost`/`127.0.0.1` (a defence against
  DNS-rebinding attacks), and never serves the `.git` folder.
- Everything the tools download is verified against a pinned SHA-256 (browser-lab files, reveal.js).
- The lab VM scripts disable SSH host-key checking and give the VM user passwordless `sudo`. That is intended only for
  the **throw-away local VM** reachable on `127.0.0.1` with key-only SSH. Do not copy those settings to a real server.
- `export_deck.py` keeps the browser sandbox on unless you pass `--no-sandbox`.
- `qemu_vm.py` starts QEMU with **no** control/monitor port (an unauthenticated local control socket would let any local
  program drive the VM) and shuts the VM down over SSH instead.

## Reporting a problem

Open a GitHub issue, or use **Security > Report a vulnerability** on the repository page if it is enabled. Please do not
post secrets or exploit details in a public issue.
