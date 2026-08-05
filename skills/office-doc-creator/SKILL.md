---
name: office-doc-creator
description: Creates real Word (.docx), PowerPoint (.pptx), Excel (.xlsx) files from a simple JSON content spec, using MIT-licensed libraries (python-docx, python-pptx, openpyxl) — not hand-writing XML, no dependency on Anthropic or any AI service. Use when an agent's output (a report, contract, official letter, data table, slides) needs to become a real Office file openable in Word/Excel/PowerPoint. Do NOT use to READ/analyze an existing Office file (that's `document-ai-structurer`) — this skill only CREATES new files.
license: MIT
compatibility: 'Requires Python 3.11+ + `python-docx`/`python-pptx`/`openpyxl` (bootstrapped via `python-env-bootstrap`). Verified running clean: Claude Code, Windows via PowerShell (2026-07-26, smoke-tested all 3 formats, confirmed correct Vietnamese-diacritic content by reading it back; 2026-08-01, re-verified the docx path with the rFonts fix and real Word-native numbering — unzipped and inspected `word/styles.xml`/`word/numbering.xml`/`word/document.xml` directly, see "Changelog" below).'
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26): extend scouting beyond Anthropic, build 'office skills' from another source since Anthropic's docx/pdf/pptx/xlsx are license-locked. Scouting found python-docx/python-pptx/openpyxl (MIT, verified directly via pip show + the PyPI JSON API), implementation written from scratch. v0.2.0 (2026-08-01): the Vietnamese-diacritics rFonts fix and the real Word-native numbering pattern (`docx_numbering.py`) are adapted from the owner's own prior production system, `D:/elix/archive/platform_archive/modules/document/v6/renderers/docx/styles.py` and `.../numbering.py` — ported and rewritten for this skill's flat JSON content spec, not blind-copied."
  version: 0.2.0
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
  "font": "Times New Roman",
  "blocks": [
    {"type": "heading", "level": 1, "text": "Section 1"},
    {"type": "paragraph", "text": "Paragraph content."},
    {"type": "paragraph", "text": "Paragraph with a block-level font override.", "font": "Arial"},
    {"type": "table", "headers": ["Column A", "Column B"], "rows": [["1", "2"]]},
    {"type": "list", "ordering": "ordered", "format": "decimal", "items": ["First item", "Second item"]},
    {"type": "list", "ordering": "unordered", "format": "bullet", "items": ["Bullet A", "Bullet B"]}
  ]
}
```

**`font` (top-level, optional):** applied to the `Normal` style and every `Title`/`Heading N` style actually used in `blocks`. **`font` (per-paragraph block, optional):** overrides the global font for that one paragraph's run. Both are validated against an explicit allowlist (`ALLOWED_FONTS` in `create_docx.py`: Times New Roman, Arial, Calibri, Cambria, Courier New, Georgia, Segoe UI, Tahoma, Verdana) — an unrecognized font name is refused (non-zero exit, clear error) rather than silently embedded, since an unverified font name either gets silently substituted by the renderer or renders with missing glyphs. Extend the allowlist only after confirming the font is actually available in the target rendering environment.

Font values go through a Vietnamese/CJK-diacritics-safe path: `python-docx`'s high-level `style.font.name` / `run.font.name` only sets the ASCII slot of the underlying `w:rFonts` XML element, so Vietnamese text (á, ề, ộ, ư, ơ, đ, ...) can silently fall back to Word's theme font even though `run.font.name` reads back "correct". `create_docx.py` sets all four `w:rFonts` attributes (`w:ascii`, `w:hAnsi`, `w:cs`, `w:eastAsia`) directly via OOXML manipulation, both at style level (global `font`) and run level (per-block `font` override).

**`list` block:** `ordering` is `"ordered"` or `"unordered"`; `format` is one of `decimal`, `roman_upper`, `roman_lower`, `alpha_upper`, `alpha_lower`, `bullet` (see `docx_numbering.SUPPORTED_LIST_FORMATS`). Produces a real Word-native list — `w:abstractNum`/`w:num` written into `word/numbering.xml` with a unique `numId` per list block, referenced from each item paragraph's `w:numPr` — not a string-prefixed "1. text" fake list. Each list restarts its own numbering at 1 regardless of other lists in the document. An empty `items` array or an unrecognized `format`/`ordering` value is refused loudly rather than silently producing a degraded or empty list.

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

## Changelog

**v0.2.0 (2026-08-01):** `create_docx.py` gained two capabilities ported from the owner's own prior production system (`D:/elix/archive/platform_archive/modules/document/v6/renderers/docx/`, see `metadata.elicited_from`):
- **Vietnamese/CJK-diacritics-safe fonts** — top-level `font` and per-paragraph-block `font` in the content spec, applied via direct `w:rFonts` XML manipulation (all 4 attributes: `ascii`/`hAnsi`/`cs`/`eastAsia`), not `python-docx`'s high-level `style.font.name` (which only sets the ASCII slot and can silently drop Vietnamese diacritics to Word's fallback theme font). Both `font` values are checked against an explicit allowlist and refused loudly if unrecognized.
- **Real Word-native list numbering** — new `list` block type, new module `scripts/docx_numbering.py`, writing genuine `w:abstractNum`/`w:num` OOXML into `word/numbering.xml` (unique `numId` per list, correct restart-at-1 semantics) instead of the common naive "prefix the paragraph text with '1.'" fake-list anti-pattern.

Why: the prior string-prefix / high-level-API-only approach in v0.1.1 would have silently produced (a) non-Word-native lists that don't auto-renumber and (b) Vietnamese text that reads correctly in the run's XML but can visually fall back to the wrong font in Word — both are the class of silent-wrong-output bug this project's grounding discipline treats as a hard bug, not a style nit.

## `docxtpl` (python-docx-template) evaluation — not adopted

Evaluated `elapouya/python-docx-template` (docxtpl, MIT, jinja2-in-docx templating) as a possible replacement for some of `create_docx.py`'s hand-rolled content-insertion logic, per the upgrade task.

- **Not currently installed anywhere in this repo.** Checked the shared `.venv/Lib/site-packages` and every `requirements.txt` under `skills/` — no `docxtpl` reference except unrelated hits inside `outside_research/` (external reference material, not part of this skill).
- **Recommendation: don't adopt now.** `office-doc-creator` already carries 3 real dependencies (`python-docx`/`python-pptx`/`openpyxl`) beyond stdlib — that's a deliberate, already-justified exception to this project's stdlib-first default (license-verified MIT, no viable stdlib alternative for OOXML). Adding a 4th (`docxtpl`) to replace logic that already works, is small, and is now more capable (fonts + real lists) would trade a working, fully-understood, hand-rolled code path for a jinja2-template-driven one with a different mental model (docx *template* files with `{{ }}` placeholders, not a JSON content spec) — a structural shift in how this skill is used, not a drop-in simplification. It would also reintroduce exactly the kind of "why did we pull in a library for this" question the CLAUDE.md stdlib-first discipline exists to force upfront.
- **Adopt later, if:** a future requirement needs branded/templated output (a fixed company letterhead `.docx` with placeholders) rather than structure-from-JSON generation — that's docxtpl's actual sweet spot, and it's a different use case from what `create_docx.py` does today. If that requirement appears, it should go through `license-compliance-check` (MIT, so expected to clear cleanly) and land as either a new content-spec mode in `create_docx.py` or a genuinely separate skill, not a silent swap-in.

## Known limitations (v0.2.0)

- Doesn't support complex styling/themes, inserted images, or a company-specific template — only produces raw content structure (heading/paragraph/table/list for docx; sheet/row for xlsx; title/bullet for pptx). If branding/templates are needed, extend the script or use `python-docx`'s `Document(template_path)` directly (or see the `docxtpl` note above).
- `list` blocks are single-level only (no nested sub-lists) — matches this skill's flat JSON content spec; the ported numbering logic supports one `w:lvl` per list, not the 3-level nesting the source system had.
- Font allowlist (`ALLOWED_FONTS` in `create_docx.py`) is intentionally small and Windows/cross-renderer-common; an unlisted font is refused, not substituted — expand the list only after confirming real availability in the target renderer.
- Not yet tested on very large files (>100 pages/slides/sheets) — only verified with small content.
- Hasn't officially passed stage 4 (quality eval); security-audit has run (self-audit, no finding — the scripts only read local JSON, write local files, no network calls, no secret handling; re-confirmed 2026-08-01 for the new/modified files, see verification notes).
