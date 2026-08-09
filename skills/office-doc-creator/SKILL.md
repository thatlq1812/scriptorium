---
name: office-doc-creator
description: Creates real Word (.docx), PowerPoint (.pptx), Excel (.xlsx) files from a simple JSON content spec, using MIT-licensed libraries (python-docx, python-pptx, openpyxl) — not hand-writing XML, no dependency on Anthropic or any AI service. Use when an agent's output (a report, contract, official letter, data table, slides) needs to become a real Office file openable in Word/Excel/PowerPoint. Do NOT use to READ/analyze an existing Office file (that's `document-ai-structurer`) — this skill only CREATES new files.
license: MIT
compatibility: 'Requires Python 3.11+ + `python-docx`/`python-pptx`/`openpyxl` (bootstrapped via `python-env-bootstrap`). Verified running clean: Claude Code, Windows via PowerShell (2026-07-26, smoke-tested all 3 formats, confirmed correct Vietnamese-diacritic content by reading it back; 2026-08-01, re-verified the docx path with the rFonts fix and real Word-native numbering — unzipped and inspected `word/styles.xml`/`word/numbering.xml`/`word/document.xml` directly; 2026-08-08, verified the new `cover_page` block AND the heading-color fix by rendering real output to PDF/PNG via Word COM + pdftoppm and visually inspecting it, see "Changelog" below).'
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26): extend scouting beyond Anthropic, build 'office skills' from another source since Anthropic's docx/pdf/pptx/xlsx are license-locked. Scouting found python-docx/python-pptx/openpyxl (MIT, verified directly via pip show + the PyPI JSON API), implementation written from scratch. v0.2.0 (2026-08-01): the Vietnamese-diacritics rFonts fix and the real Word-native numbering pattern (`docx_numbering.py`) are adapted from the owner's own prior production system, `D:/elix/archive/platform_archive/modules/document/v6/renderers/docx/styles.py` and `.../numbering.py` — ported and rewritten for this skill's flat JSON content spec, not blind-copied. v0.3.0 (2026-08-08): owner directly compared a docx built by this skill against one built by a competing agentic IDE (Google Antigravity) for the same real essay task and found this skill's output 'không thiết kế được Docx đẹp cho lắm, chỉ đơn giản thôi' (not well-designed, too plain) -- investigation traced it to a real, named gap in this skill's own 'Known limitations' section ('no company-specific template', i.e. no cover-page capability at all), not a general styling problem; grounded in the standard Vietnamese academic/business trang bìa convention the comparison document demonstrated (institution header block, colored document-type label, colored title, label/value metadata table, closing location/date line), public-source convention, general-capability tier, no additional expert elicitation needed per principle 4. v0.3.1 (2026-08-08, same day): owner separately flagged the actual body heading colors as 'nhạt lại còn hướng nhạt dần' (already pale AND trending paler) versus the dark navy/near-black text color expected, and explicitly directed 'có thể tự do, miễn giữ cấu trúc là được' (free to deviate on specifics as long as structure holds) rather than a rigid fixed palette -- confirmed by reading the generated style XML directly: python-docx's default template's Heading 1/2/3 theme colors run #365F91 -> #4F81BD -> #4F81BD, i.e. levels 2-3 are BOTH lighter than level 1, not darker, a real bug in the template default this skill was silently inheriting, not a style preference."
  version: 0.3.1
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
    {"type": "list", "ordering": "unordered", "format": "bullet", "items": ["Bullet A", "Bullet B"]},
    {
      "type": "cover_page",
      "org_lines": ["MINISTRY / ORGANIZATION", "INSTITUTION NAME", "DEPARTMENT"],
      "divider": true,
      "document_type": "REPORT TYPE LABEL",
      "document_type_color": "C00000",
      "title": "Document Title",
      "title_color": "1F4E79",
      "metadata": [
        {"label": "Prepared by:", "value": "Name"},
        {"label": "Date:", "value": "2026-08-08"}
      ],
      "footer_line": "CITY – YEAR",
      "page_break_after": true
    }
  ]
}
```

**`font` (top-level, optional):** applied to the `Normal` style and every `Title`/`Heading N` style actually used in `blocks`. **`font` (per-paragraph block, optional):** overrides the global font for that one paragraph's run. Both are validated against an explicit allowlist (`ALLOWED_FONTS` in `create_docx.py`: Times New Roman, Arial, Calibri, Cambria, Courier New, Georgia, Segoe UI, Tahoma, Verdana) — an unrecognized font name is refused (non-zero exit, clear error) rather than silently embedded, since an unverified font name either gets silently substituted by the renderer or renders with missing glyphs. Extend the allowlist only after confirming the font is actually available in the target rendering environment.

Font values go through a Vietnamese/CJK-diacritics-safe path: `python-docx`'s high-level `style.font.name` / `run.font.name` only sets the ASCII slot of the underlying `w:rFonts` XML element, so Vietnamese text (á, ề, ộ, ư, ơ, đ, ...) can silently fall back to Word's theme font even though `run.font.name` reads back "correct". `create_docx.py` sets all four `w:rFonts` attributes (`w:ascii`, `w:hAnsi`, `w:cs`, `w:eastAsia`) directly via OOXML manipulation, both at style level (global `font`) and run level (per-block `font` override).

**`list` block:** `ordering` is `"ordered"` or `"unordered"`; `format` is one of `decimal`, `roman_upper`, `roman_lower`, `alpha_upper`, `alpha_lower`, `bullet` (see `docx_numbering.SUPPORTED_LIST_FORMATS`). Produces a real Word-native list — `w:abstractNum`/`w:num` written into `word/numbering.xml` with a unique `numId` per list block, referenced from each item paragraph's `w:numPr` — not a string-prefixed "1. text" fake list. Each list restarts its own numbering at 1 regardless of other lists in the document. An empty `items` array or an unrecognized `format`/`ordering` value is refused loudly rather than silently producing a degraded or empty list.

**`heading_colors` (top-level, optional, v0.3.1):** `{"1": "1B365D", "2": "2C4D75", ...}` — per-level hex color override for `Title`/`Heading N` styles. Every heading level used in the document gets an explicit dark color by default (`DEFAULT_HEADING_COLORS` in `create_docx.py`: Title `0F2942`, H1 `1B365D`, H2 `2C4D75`, H3+ `1F3A52`) regardless of whether `heading_colors` is set at all -- this isn't an opt-in feature, it replaces `python-docx`'s own default template theme colors, which run Heading 1 `#365F91` -> Heading 2/3 `#4F81BD` (i.e. get *lighter*, not darker, at deeper levels -- confirmed by reading the generated style XML, see Changelog v0.3.1). `heading_colors` only needs setting for a genuinely different palette. **`color` (per `heading` block, optional):** overrides the color for that one heading only, same hex format. Neither is restricted to an allowlist the way `font` is -- an arbitrary 6-digit hex always renders correctly (unlike a font name, which can be missing on the renderer), so only the *shape* is validated, not the specific value; the caller has real freedom here as long as the document's structural rules (heading levels map to real Word Heading styles, etc.) still hold.

**`cover_page` block (docx only, v0.3.0):** a formal title page — institution/org header lines (`org_lines`, each its own centered bold line), an optional `divider` (default `true`), a colored `document_type` label (`document_type_color`, default `C00000`/dark red), a colored `title` (`title_color`, default `1F4E79`/dark blue), a `metadata` label/value table (borderless, bold labels + italic values — `[{"label": "...", "value": "..."}]`), a closing `footer_line`, and `page_break_after` (default `true`) so body content starts on its own fresh page. `font` on the block overrides the document's global `font` for just the cover. If a top-level `content.title` is also present, it is suppressed when a `cover_page` block exists (the cover's own `title` replaces it — emitting both would print the title twice). Vertical spacing between sections (`spacing_before_metadata_lines`, `spacing_before_footer_lines`, both default line-counts) is real paragraph `space_before`/`space_after`, not a run of empty paragraphs — see Changelog v0.3.0 for why that distinction is load-bearing, not cosmetic.

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

**v0.3.1 (2026-08-08, same day as v0.3.0):** All `Title`/`Heading N` styles now get an explicit, always-dark text color (`DEFAULT_HEADING_COLORS`) instead of inheriting whatever `python-docx`'s default template theme defines. Root cause (confirmed by reading the generated `word/styles.xml` directly, not assumed): the default template's Heading 1/2/3 theme colors are `#365F91` -> `#4F81BD` -> `#4F81BD` -- Heading 2 and 3 are *lighter* than Heading 1, not darker, so a document with several nesting levels visibly faded the deeper it went, backwards from how a heading hierarchy should read. New optional `heading_colors` (top-level) and `color` (per `heading` block) let a caller override the specific hex per level or per heading; per owner direction, neither is restricted to a fixed palette/allowlist the way `font` is -- validated for hex *shape* only, real freedom on the value as long as the structural contract (each level maps to a real Word heading style) still holds.

**v0.3.0 (2026-08-08):** New `cover_page` block type for `create_docx.py` — see `metadata.elicited_from` for what prompted it (a real side-by-side comparison against another agentic IDE's output on the same task) and the content-spec section above for the exact fields.

Two real bugs found and fixed during verification (rendering real output to PDF/PNG via Word COM automation + `pdftoppm`, then actually looking at it — not assumed from the XML):
- **Duplicate title.** `build()` already unconditionally rendered `content.title` as a Title-style heading before any block ran; adding a `cover_page` block (which has its own, differently-styled `title`) printed the title twice, stacked on top of each other. Fixed: `build()` now skips the top-level title heading whenever any block is `cover_page`.
- **A genuinely blank page between the cover and the real content.** Root-caused by ablation (isolated minimal repro vs. the real multi-page document, comparing `ComputeStatistics(wdStatisticPages)` across variants) to the original spacing approach: multiple consecutive empty `doc.add_paragraph()` calls used to fake vertical gaps (13 empty paragraphs total across the cover). Each carries Word's own default Normal-style line height + `space_after`, and stacked back-to-back before a real `add_page_break()`, this made Word's PDF-export pagination reserve a whole extra blank page that plain on-screen editing didn't show — invisible unless the actual rendered output is inspected. Fixed by replacing every "N empty paragraphs" spacer with a single paragraph carrying an explicit `space_after` in points; same visual gap, one paragraph mark instead of N, and the blank page is gone (confirmed: page count dropped back to exactly cover + body, matching a version with no cover at all plus one page for the forced break). Also switched the `metadata` table from `autofit=False` with no explicit widths to explicit `Cm` widths on both the table and every cell — not the actual cause of the blank page (confirmed by the same ablation), but `autofit=False` with unset widths is undefined layout behavior regardless and worth not leaving in place once found.

Lesson generalized beyond this one block: **a Word document that looks correct in python-docx's own object model, or even opened once in Word, is not verified until the actual rendered output (PDF/image) has been looked at** — this is the same "grounding over confidence" discipline this repo already applies elsewhere, now with a concrete docx-specific example of what it catches that inspecting XML/API state alone would not.

**v0.2.0 (2026-08-01):** `create_docx.py` gained two capabilities ported from the owner's own prior production system (`D:/elix/archive/platform_archive/modules/document/v6/renderers/docx/`, see `metadata.elicited_from`):
- **Vietnamese/CJK-diacritics-safe fonts** — top-level `font` and per-paragraph-block `font` in the content spec, applied via direct `w:rFonts` XML manipulation (all 4 attributes: `ascii`/`hAnsi`/`cs`/`eastAsia`), not `python-docx`'s high-level `style.font.name` (which only sets the ASCII slot and can silently drop Vietnamese diacritics to Word's fallback theme font). Both `font` values are checked against an explicit allowlist and refused loudly if unrecognized.
- **Real Word-native list numbering** — new `list` block type, new module `scripts/docx_numbering.py`, writing genuine `w:abstractNum`/`w:num` OOXML into `word/numbering.xml` (unique `numId` per list, correct restart-at-1 semantics) instead of the common naive "prefix the paragraph text with '1.'" fake-list anti-pattern.

Why: the prior string-prefix / high-level-API-only approach in v0.1.1 would have silently produced (a) non-Word-native lists that don't auto-renumber and (b) Vietnamese text that reads correctly in the run's XML but can visually fall back to the wrong font in Word — both are the class of silent-wrong-output bug this project's grounding discipline treats as a hard bug, not a style nit.

## `docxtpl` (python-docx-template) evaluation — not adopted

Evaluated `elapouya/python-docx-template` (docxtpl, MIT, jinja2-in-docx templating) as a possible replacement for some of `create_docx.py`'s hand-rolled content-insertion logic, per the upgrade task.

- **Not currently installed anywhere in this repo.** Checked the shared `.venv/Lib/site-packages` and every `requirements.txt` under `skills/` — no `docxtpl` reference except unrelated hits inside `outside_research/` (external reference material, not part of this skill).
- **Recommendation: don't adopt now.** `office-doc-creator` already carries 3 real dependencies (`python-docx`/`python-pptx`/`openpyxl`) beyond stdlib — that's a deliberate, already-justified exception to this project's stdlib-first default (license-verified MIT, no viable stdlib alternative for OOXML). Adding a 4th (`docxtpl`) to replace logic that already works, is small, and is now more capable (fonts + real lists) would trade a working, fully-understood, hand-rolled code path for a jinja2-template-driven one with a different mental model (docx *template* files with `{{ }}` placeholders, not a JSON content spec) — a structural shift in how this skill is used, not a drop-in simplification. It would also reintroduce exactly the kind of "why did we pull in a library for this" question the CLAUDE.md stdlib-first discipline exists to force upfront.
- **Adopt later, if:** a future requirement needs branded/templated output (a fixed company letterhead `.docx` with placeholders) rather than structure-from-JSON generation — that's docxtpl's actual sweet spot, and it's a different use case from what `create_docx.py` does today. If that requirement appears, it should go through `license-compliance-check` (MIT, so expected to clear cleanly) and land as either a new content-spec mode in `create_docx.py` or a genuinely separate skill, not a silent swap-in.

## Known limitations (v0.3.0)

- Still no inserted images or a company-specific branded template (a fixed letterhead file with placeholders) — `cover_page` (v0.3.0) covers the common "formal title page" structure via the JSON spec, but doesn't embed a logo or match an exact corporate template. If a real branded template is needed, extend the script or use `python-docx`'s `Document(template_path)` directly (or see the `docxtpl` note above).
- `list` blocks are single-level only (no nested sub-lists) — matches this skill's flat JSON content spec; the ported numbering logic supports one `w:lvl` per list, not the 3-level nesting the source system had.
- Font allowlist (`ALLOWED_FONTS` in `create_docx.py`) is intentionally small and Windows/cross-renderer-common; an unlisted font is refused, not substituted — expand the list only after confirming real availability in the target renderer.
- Not yet tested on very large files (>100 pages/slides/sheets) — only verified with small content.
- Hasn't officially passed stage 4 (quality eval); security-audit has run (self-audit, no finding — the scripts only read local JSON, write local files, no network calls, no secret handling; re-confirmed 2026-08-01 for the new/modified files, see verification notes).
