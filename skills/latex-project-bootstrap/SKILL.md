---
name: latex-project-bootstrap
description: Scaffolds a LaTeX project (book/report) correctly from the start — XeLaTeX + fontspec/polyglossia for Vietnamese (not pdfLaTeX + babel, which is prone to diacritic bugs), biblatex + biber for bibliography, plus a build script in the correct 4-pass order. Use when starting a new LaTeX document (book, research report, thesis) containing Vietnamese. Do NOT use to write actual book/chapter content (that's separate drafting work) — this skill only scaffolds the correct technical setup, avoiding the 2 most common mistakes when starting a Vietnamese LaTeX project from scratch.
license: MIT
compatibility: Requires XeLaTeX (`xelatex`) + `biber` already installed (MiKTeX/TeX Live). The scaffold script is pure Python 3 stdlib, no venv needed. Verified running clean: Claude Code, Windows (2026-07-26, real 4-pass build, 5-page PDF, correctly-rendered Vietnamese diacritics via MiKTeX 25.12).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in the owner's real LaTeX project (D:/elix/researches/textbooks — a textbook program in real production use): the XeLaTeX + polyglossia/fontspec engine, the xelatex->biber->xelatex->xelatex build sequence, observed directly from textbooks/templates/core/elix-textbook.cls and docs/methodology/idea_to_book_series.md Phase 6. Wrote a generic scaffold from scratch, didn't copy the owner's 476-line .cls file specific to their K-12 program."
  version: 0.1.0
---

# latex-project-bootstrap

Scaffolds a LaTeX project correctly on the first try — avoiding the 2 most common mistakes someone makes starting on their own: using the wrong engine for Vietnamese, and forgetting the 4-pass build order when a bibliography is involved.

## Source lesson (from a real LaTeX project)

Read `references/vietnamese-latex-setup.md` before writing a single `.tex` file — a lesson drawn from a real production LaTeX program (not theory): pdfLaTeX + babel `vietnamese` is prone to tone-mark bugs when paired with modern fonts; XeLaTeX + `fontspec`/`polyglossia` handles Unicode directly, far more stable.

## Scaffold the project

```bash
python scripts/init_project.py <output_dir> --title "Document title" --font "Noto Serif"
```

Produces: `main.tex` (a correct XeLaTeX preamble + biblatex/biber), `chapters/01_intro.tex`, a sample `bibliography.bib`, `build.sh`/`build.ps1`.

## Build

```bash
# Unix:
bash build.sh
# Windows PowerShell:
.\build.ps1
```

Required order (see `references/vietnamese-latex-setup.md` for why each step is needed): `xelatex → biber → xelatex → xelatex`. Skipping any pass can produce a PDF missing citations or with a wrong table of contents/page numbers.

## What this skill does NOT do

- Doesn't write actual chapter content — only scaffolds the technical setup (preamble, build script).
- Doesn't install a TeX distribution (MiKTeX/TeX Live) — assumes one is already on the machine, check with `xelatex --version` before using this skill.
- Doesn't use a complex custom class (like the source project's `elix-textbook.cls`, with its own macros for a specific textbook program) — uses the standard `book` class + a minimal preamble, keeping the skill portable for any kind of document, not just textbooks.

## Bundled files

- `scripts/init_project.py` — the scaffold script, pure stdlib.
- `references/vietnamese-latex-setup.md` — technical lessons + a sample preamble + common errors.

## Known limitations (v0.1.0)

- Only scaffolds a simple `book` class (1 sample chapter) — doesn't yet support multi-volume, TikZ figures, or custom environments (things the source project has but which are project-specific, not immediately generalizable).
- Not tested with fonts other than "Noto Serif"/"Times New Roman" — if a font isn't on the build machine, `xelatex` reports a clear error ("Font not found"), no silent failure.
