---
name: office-doc-creator
description: Creates real Word (.docx), PowerPoint (.pptx), Excel (.xlsx) files from a simple JSON content spec, using MIT-licensed libraries (python-docx, python-pptx, openpyxl) — not hand-writing XML, no dependency on Anthropic or any AI service. Use when an agent's output (a report, contract, official letter, data table, slides) needs to become a real Office file openable in Word/Excel/PowerPoint. Do NOT use to READ/analyze an existing Office file (that's `document-ai-structurer`) — this skill only CREATES new files.
license: MIT
compatibility: Requires Python 3.11+ + `python-docx`/`python-pptx`/`openpyxl` (bootstrapped via `python-env-bootstrap`). Verified running clean: Claude Code, Windows via PowerShell (2026-07-26, smoke-tested all 3 formats, confirmed correct Vietnamese-diacritic content by reading it back).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26): extend scouting beyond Anthropic, build 'office skills' from another source since Anthropic's docx/pdf/pptx/xlsx are license-locked. Scouting found python-docx/python-pptx/openpyxl (MIT, verified directly via pip show + the PyPI JSON API), implementation written from scratch."
  version: 0.1.1
---

# office-doc-creator

Creates real Office files (not a simulation) from content the agent has already prepared as JSON. Three independent scripts, one per format — not a single shared "mega script."

## Why write it from scratch instead of using Anthropic's docx/pptx/xlsx skill

Already scouted (`scout-harvester`) and license-checked (`license-compliance-check`) — Anthropic's corresponding skill has a contractual clause absolutely banning extract/copy/derive/distribute, fully BLOCKED. `python-docx`/`python-pptx`/`openpyxl` are independent MIT libraries, unrelated to Anthropic, license verified directly (`pip show`, the PyPI JSON API) on 2026-07-26 — safe to write our own implementation.

## Environment bootstrap

A SHARED venv at the repo root (not specific to this skill — see `skills/python-env-bootstrap/SKILL.md`):

```bash
# Recommended: via python-env-bootstrap (PowerShell on Windows, NOT Git Bash):
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\office-doc-creator\requirements.txt -PyVersion 3.12
```

## Create a Word file (.docx)

```bash
# From the repo root, shared venv:
.venv\Scripts\python.exe skills\office-doc-creator\scripts\create_docx.py <content.json> <output.docx>
```

`content.json`:
```json
{
  "title": "Document title",
  "blocks": [
    {"type": "heading", "level": 1, "text": "Section 1"},
    {"type": "paragraph", "text": "Paragraph content."},
    {"type": "table", "headers": ["Column A", "Column B"], "rows": [["1", "2"]]}
  ]
}
```

## Create an Excel file (.xlsx)

```bash
.venv\Scripts\python.exe skills\office-doc-creator\scripts\create_xlsx.py <content.json> <output.xlsx>
```

`content.json`: `{ "sheets": [{ "name": "Sheet1", "headers": [...], "rows": [[...], ...] }] }`

## Create a PowerPoint file (.pptx)

```bash
.venv\Scripts\python.exe skills\office-doc-creator\scripts\create_pptx.py <content.json> <output.pptx>
```

`content.json`: `{ "slides": [{ "title": "...", "bullets": ["...", "..."] }] }` — uses PowerPoint's default "Title and Content" layout, no custom theme.

## Known limitations (v0.1.1)

- Doesn't support complex styling/themes, inserted images, or a company-specific template — only produces raw content structure (heading/paragraph/table for docx; sheet/row for xlsx; title/bullet for pptx). If branding/templates are needed, extend the script or use `python-docx`'s `Document(template_path)` directly.
- Not yet tested on very large files (>100 pages/slides/sheets) — only verified with small content.
- Hasn't officially passed stage 4 (quality eval); security-audit has run (self-audit, no finding — the scripts only read local JSON, write local files, no network calls, no secret handling).
