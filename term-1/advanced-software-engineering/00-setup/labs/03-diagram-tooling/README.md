# Lab 00.3 — Diagram tooling: Mermaid, PlantUML, Structurizr (C4)

**Goal:** render a Mermaid, a PlantUML and a Structurizr C4 diagram of the Course Registration Platform, and commit them under a `docs/diagrams/` convention that every later module reuses.

**Starting state:** your `m0` from lab 02 (`~/ase-work/registration` in that lab). Nothing in the Go or Python code changes.
**Ending state:** `docs/diagrams/` with four sources, their rendered SVGs and a README with the rules; one commit.

## Which tool for what

| Tool | Use it for | Source file | Needs |
|---|---|---|---|
| Mermaid | quick structure in the text of a README (flowchart, class, state, sequence) | `.mmd` | **browser only** (path A) or node + Chrome/Edge (path B) |
| PlantUML | precise UML (sequence with activations, component, deployment) | `.puml` | Docker (verified), or Java + the PlantUML jar (**UNVERIFIED**, see below) |
| Structurizr | the C4 model: one model, several views (context, container, ...) | `workspace.dsl` | Docker (verified) |

## Steps

Run from the root of your own repository (the `registration` folder of lab 02). `$SRC` is the course folder, as in lab 02; set it again if you opened a new terminal: `export SRC=<course repository>/term-1/advanced-software-engineering`.

```bash
# 1. Path A, no install: Mermaid in the browser. Open the file, edit the diagram, watch it render.
#    (Windows: start ""   macOS: open   Linux: xdg-open)
start "" "$SRC/00-setup/labs/03-diagram-tooling/mermaid-preview.html"

# 2. Put the sources and the render script in the project (the convention folder)
mkdir -p docs/diagrams
cp "$SRC"/00-setup/labs/03-diagram-tooling/{registration-overview.mmd,list-courses.puml,workspace.dsl,render-diagrams.sh} docs/diagrams/

# 3. Path B: render everything: Mermaid (npx mermaid-cli), PlantUML (Docker), Structurizr -> Mermaid (Docker)
bash docs/diagrams/render-diagrams.sh
ls -1 docs/diagrams

# 4. Look at the results (any browser opens SVG)
start "" docs/diagrams/c4-containers.svg

# 5. Commit the convention: README with the rules, .gitignore for the intermediate export
cp "$SRC/00-setup/labs/03-diagram-tooling/solution/docs/diagrams/README.md" docs/diagrams/README.md
echo "docs/diagrams/c4/" >> .gitignore
git add . && git commit -m "Add docs/diagrams: sources, rendered SVGs, conventions"
```

Notes by system:

- **Git Bash on Windows:** the script converts paths for Docker and Node by itself. `start ""` opens a file; Linux uses `xdg-open`, macOS `open`.
- **Linux / macOS:** the script looks for `google-chrome`, `chromium`, `chromium-browser` and the macOS Chrome app. Set `BROWSER=/path/to/browser` if yours is elsewhere. On a Linux **CI** machine running as root, Chrome refuses to start without `--no-sandbox` (**UNVERIFIED**, not tried here).
- **No Docker:** the PlantUML and Structurizr parts fail. Mermaid (path A or B) still works. PlantUML without Docker: install Java and the jar from https://plantuml.com/download, then `java -jar plantuml.jar -tsvg list-courses.puml` (**UNVERIFIED**: I did not download and run the jar on this machine; Java 25 is installed, which is the only thing that was checked).
- **No Chrome/Edge/Chromium:** the script skips Mermaid files and says so. Use `mermaid-preview.html` and save the SVG from the page, or let GitHub render a fenced ```` ```mermaid ```` block (**UNVERIFIED** here; GitHub documents it).
- **Structurizr in the browser** (`structurizr/structurizr local` is documented as an interactive viewer): not run here (**UNVERIFIED**). This lab uses `validate` and `export`, which were run.

## Code

| File | What it is |
|---|---|
| [`registration-overview.mmd`](registration-overview.mmd) | the architecture diagram of the platform (same as `PLAN.md`, section 2), Mermaid flowchart |
| [`list-courses.puml`](list-courses.puml) | PlantUML sequence diagram of `GET /courses` (Client → API → `catalog.Catalog.List()`) |
| [`workspace.dsl`](workspace.dsl) | Structurizr DSL: 2 people, 1 system, 5 containers, 7 relationships, 2 views. The colors are the course roles: client teal, service amber, infrastructure violet, store green |
| [`render-diagrams.sh`](render-diagrams.sh) | renders every `.mmd`, `.puml` and the C4 workspace; pins `@mermaid-js/mermaid-cli@12.2.0`, so a render in CI matches yours |
| [`mermaid-preview.html`](mermaid-preview.html) | zero-install Mermaid editor (loads Mermaid 11.4.1 from a CDN) |

The C4 part of the script is two commands: `structurizr export -format mermaid` writes `c4/structurizr-*.mmd`, then each file goes through the same Mermaid renderer. That is why the C4 views come out as `c4-context.svg` and `c4-containers.svg`.

## Expected output

Captured on Windows 11 with Git Bash on 2026-11-23: mermaid-cli 12.2.0 using the installed Chrome, PlantUML 1.2026.10 and Structurizr from Docker (images already pulled). The first run took about 22 seconds because `npx` downloads mermaid-cli once.

```text
$ bash docs/diagrams/render-diagrams.sh
rendered registration-overview.svg
rendered list-courses.svg
rendered c4-containers.svg
rendered c4-context.svg

$ ls -1 docs/diagrams
c4
c4-containers.svg
c4-context.svg
list-courses.puml
list-courses.svg
registration-overview.mmd
registration-overview.svg
render-diagrams.sh
workspace.dsl
```

The first run of each Docker image also prints `Pulling from ...` lines; they are not errors. `structurizr validate` prints nothing when the workspace is valid. In `c4-containers.svg` the four role colors appear (teal client, amber `registration-api` and `analytics`, violet broker, green PostgreSQL cylinder). A second run produced identical SVG files in this environment (no diff), so committing them gives clean diffs. Reference: [`solution/expected-output.txt`](solution/expected-output.txt).

## What to observe

- The same system appears three times: as a flowchart (what talks to what), as a sequence (what happens in time for one request) and as a C4 container view (who owns what). Each hides what the other shows; module 03 builds on that.
- Structurizr keeps **one model** (`workspace.dsl`) and derives several views. Mermaid and PlantUML files are one drawing each, so they can disagree with each other and with the code.
- Planned parts (PostgreSQL, broker) are labelled "Planned" in the model. A diagram that mixes today's system with the intended one without saying so is a lie waiting to happen.
- Diagram source is plain text, so `git diff` shows exactly what changed in a design.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `Tried to find the browser at the configured path (...), but no executable was found` | the path given to mermaid-cli is not a path Node understands (seen with a Git Bash `/c/...` path) or the browser is not there | set `BROWSER=<path to chrome or msedge>`; the script converts it with `cygpath` under Git Bash |
| `no Chrome/Edge/Chromium found` | the script's search list found nothing | same, or path A |
| Docker commands fail to reach the daemon | Docker Desktop is not running | start it, then run the script again (lab 01 reports `daemon NOT reachable`) |
| Docker cannot see your files (Git Bash) | Git Bash rewrites `/c/...` paths | the script uses `pwd -W` and `MSYS_NO_PATHCONV=1`; copy that in your own commands (not tested without them) |
| `.svg` changes on every run in CI but not locally | different tool versions | pin versions (the `MERMAID_CLI` line); do not use `latest` for mermaid-cli |
| Structurizr `validate` exits non-zero | a DSL syntax error (error text not checked here) | fix `workspace.dsl`; run `validate` alone to iterate |

## Extension task

Document the Go code with a diagram generated from the source of truth you control: write `docs/diagrams/catalog-classes.mmd`, a Mermaid **class diagram** of `catalog.Course` and `catalog.Catalog` (fields and the three methods, one composition/aggregation edge). Render it with the script, and check by reading `internal/catalog/catalog.go` that every field and method on the diagram exists there.

Solution: [`solution/catalog-classes.mmd`](solution/catalog-classes.mmd). The convention README is [`solution/docs/diagrams/README.md`](solution/docs/diagrams/README.md).
