# docs/diagrams: where diagrams live

One folder, one rule: **the text source is the truth, the SVG is a build artifact you also commit** so a pull request shows
the picture and GitHub can display it.

| File | What it is | Rendered by |
|---|---|---|
| `*.mmd` | Mermaid source (flowcharts, class and state diagrams) | `mermaid-cli` (`mmdc`) |
| `*.puml` | PlantUML source (sequence diagrams, precise UML) | `plantuml/plantuml` Docker image |
| `workspace.dsl` | The C4 model in Structurizr DSL (the single model behind all C4 views) | `structurizr/structurizr export`, then Mermaid |
| `*.svg` | Rendered output, committed next to its source | `bash render-diagrams.sh` |
| `c4/` | Intermediate Structurizr export. **Not committed** (listed in `.gitignore`) | `render-diagrams.sh` |

## Rules

1. Edit the source, never the `.svg`. Run `bash docs/diagrams/render-diagrams.sh` and commit both in the same commit.
2. Name a diagram after what it shows, not after the tool: `registration-overview.mmd`, not `diagram1.mmd`.
3. Use Mermaid for quick structure, PlantUML when UML precision matters (lifelines, activations), Structurizr for the C4 views.
4. Pin the tool versions in `render-diagrams.sh` (the `MERMAID_CLI` line) so a render in CI matches your laptop.
5. Every diagram has a one-line caption in the document that embeds it, saying which question it answers.
