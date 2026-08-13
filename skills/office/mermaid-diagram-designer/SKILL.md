---
name: mermaid-diagram-designer
description: Designs diagram-as-code using Mermaid syntax (flowchart, sequence, class, state, ER, gantt, pie, journey, mindmap, timeline) from a description of a system/process/data relationship. Use when a process, interaction between multiple components, data model, or project timeline needs visualizing as text embeddable in markdown/HTML. Do NOT use for complex multi-series/multi-axis quantitative data charts (that's matplotlib/Recharts/D3's job) — Mermaid is strong at structure/relationships, not data visualization.
license: MIT
compatibility: 'Produces plain text (no rendering needed to hand off to the user — most modern harnesses/markdown viewers auto-render ```mermaid``` code fences). The bundled lint script is pure Python 3 stdlib, no venv needed. Verified running clean: Antigravity CLI, Windows (2026-07-26, lint script tested on both a valid case and an error case).'
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26, docs/ROADMAP.md): scouted mermaid-js/mermaid (MIT, 89,421 stars, verified directly via gh api) as the syntax source. Cheatsheet + diagram-type decision rules rewritten in our own words (not copied verbatim from the original docs), based on public knowledge of Mermaid syntax."
  version: 0.1.0
---

# mermaid-diagram-designer

Turns a description of a system/process/relationship into a valid Mermaid diagram-as-code, the right diagram type for the right kind of information.

## Process

1. **Determine the diagram type** — read `references/choosing-diagram-type.md`, apply the quick decision rules (real time axis? multiple interacting actors? states/events? static data relationships?). Don't default to `flowchart` for everything just because it's the most flexible — picking the wrong diagram type makes the reader misunderstand the system's actual nature.
2. **Write the diagram** — reference the correct syntax for the chosen type in `references/syntax-cheatsheet.md`.
3. **Lint before handing off** — run `scripts/lint_mermaid.py` on the diagram just written:
   ```bash
   python scripts/lint_mermaid.py <file.mmd>
   # or: echo "..." | python scripts/lint_mermaid.py -
   ```
   This is a rough structural lint (valid diagram-type keyword, balanced brackets, balanced quotes) — NOT a real render, doesn't catch every syntax error (e.g. a wrong arrow-type name). If real rendering is available (Mermaid Live Editor, a VS Code extension, or a harness that renders Mermaid directly inline in markdown), always prefer verifying with a real render.
4. **Hand off the diagram** inside a ```` ```mermaid ```` code fence if the output is markdown, or `<pre class="mermaid">...</pre>` if the output is HTML (Artifact convention).

## What this skill does NOT do

- Doesn't render an image (PNG/SVG) itself — needs Node + `@mermaid-js/mermaid-cli` (heavy, needs Puppeteer/Chromium), not built in v0.1.0. Hands off the diagram as text, letting the target harness/viewer render it.
- Not used for multi-dimensional quantitative data charts — see the `dataviz` skill (if one exists) or a dedicated charting tool.

## Bundled files

- `references/syntax-cheatsheet.md` — sample syntax for 10 diagram types.
- `references/choosing-diagram-type.md` — a decision table for picking a diagram type by situation.
- `scripts/lint_mermaid.py` — rough structural lint, pure stdlib.

## Known limitations (v0.1.0)

- The lint only catches surface-level structural errors (keywords, brackets, quotes) — not a real Mermaid parser, may pass something invalid or fail something valid with complex syntax (styling, nested subgraphs, click events).
- Not yet tested on a genuinely large diagram (>50 nodes) — only small cases verified.
