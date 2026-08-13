---
name: document-ai-structurer
description: Converts any source document (PDF, DOCX, PPTX, XLSX, HTML, scanned image) into a directory structure optimized for AI reading — full.md (full text), sections/*.md (split by heading), index.json (table of contents/manifest). Use when a long/unstructured document (including scans) needs to enter an agent's context without loading the whole thing at once, or when the document needs to be in a form another agent can reuse. For Vietnamese legal-article documents (Điều/Khoản/Điểm structure), a second workflow lets the reviewing agent scan and confirm article boundaries itself instead of trusting a fixed heading-split rule — see "Legal-article structuring mode" below. A third workflow aggregates multiple legal-article-mode outputs into one queryable catalog.json across documents — see "Multi-document catalog" below. Do NOT use to present a document to a human reader directly (the output is optimized for machines, not for printing/viewing).
license: MIT
compatibility: 'Requires Python 3.11+ and the `docling` package (installed via the bundled `requirements.txt`). Verified running clean: Antigravity CLI (2026-07-26, real PDF smoke test, 37 sections; 2026-07-27, legal-article mode + catalog mode against synthetic Vietnamese legal-text fixtures). Not yet verified: OpenAI Codex CLI, Kimi Code CLI.'
metadata:
  domain: general
  task_type: document-conversion
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26): idea of turning any document type into an AI-optimized structure (folder + JSON index) using Python; grounded in research on Docling/MinerU/unstructured.io/the llms.txt convention and chunking best practice. Owner (2026-07-27): legal-article structuring mode — chunk boundaries must not be hardcoded into script logic alone; the reviewing agent scans and confirms structure itself, and must not blindly trust Docling's OCR/layout extraction either. Owner (2026-07-27, same session): directed building a multi-document catalog/index next, specifically to let legal-citation-checker verify a cited Điều actually exists in the structured corpus. Built for the Legal-cluster's 2 flagged real gaps (docs/STATUS.md) — legal-citation-checker's deferred hiệu lực verification and legal-form-filler's missing checklist data — as a structural reading capability, not a fix for either gap by itself (no effective-date/status data is invented; those fields stay caller-supplied)."
  engine: "docling==2.115.0"
  version: 0.3.1
  changelog_0_2_0: "Added legal-article structuring mode: suggest_legal_boundaries.py proposes candidate Điều/Khoản/Điểm boundaries by regex (explicitly labeled unverified), apply_legal_structure.py mechanically builds sections/index.json from an agent-reviewed structure.json. Fixed a real bug found during testing: slugify() stripped Vietnamese diacritics instead of transliterating them, producing garbled filenames (e.g. 'i-u-1-ph-m-vi...' instead of 'dieu-1-pham-vi...') — affected both the original heading-split mode and the new legal mode; fixed in both. Also fixed a Windows console UnicodeEncodeError (cp1252) when printing Vietnamese text to stdout/stderr, found the same way."
  changelog_0_3_0: "Added build_catalog.py: aggregates multiple legal-article-mode outputs (folders with index.json) into one catalog.json, parsing an integer Điều number out of each section heading. Per-document van_ban_so_hieu/van_ban_ten are read from an optional caller-declared doc_meta.json sibling (never invented) — a folder without one is still included, identified by folder name only, flagged as unmatched rather than silently dropped. legal-citation-checker v0.2.0 now accepts this catalog via --catalog to check that a cited Điều number actually exists in the corpus for documents the catalog covers — an existence check, explicitly not a hiệu lực (in-effect) check, documented as such in both SKILL.md files."
  changelog_0_3_1: "build_catalog.py now also copies each Điều's khoan list (verbatim, from the source index.json) into catalog.json — legal-form-filler v0.2.0's checklist_from_catalog.py consumes this to extract a document checklist from a real Điều instead of requiring a hand-typed one."
---

# document-ai-structurer

Converts a source document (PDF including scans, DOCX, PPTX, XLSX, HTML, images) into a directory structure optimized for an agent to read back — there's no industry standard for this (already researched, see the related `docs/specs/STRATEGY_SPEC.md`), so this is Scriptorium's own design, borrowing 2 validated ideas: Docling-style hierarchical JSON + the `llms.txt` curated-index convention.

## When to use

Use when: the document is long, has no AI-ready structure (raw PDF, scan, DOCX...), and the agent needs to read it back multiple times or only needs part of it (doesn't want to load the whole file every time). Especially useful for legal documents, textbooks, research reports, books — any domain with long source documents.

Don't use when: the document is already clean, short markdown/text (no conversion needed); or the goal is presenting it to a human reader (this output has no styling, isn't meant for printing).

## Environment bootstrap (required, run once per machine)

**Don't use a pre-committed `.venv` — there isn't one, because a venv is a binary tied to the OS/architecture, not portable.** Use the `toolchain-bootstrap` skill — a SHARED venv at the repo root, not specific to this skill (doesn't assume the machine already has Python):

```bash
# From the repo root:
bash skills/general/toolchain-bootstrap/scripts/bootstrap.sh skills/office/document-ai-structurer/requirements.txt 3.12
# Windows: .\skills\general\toolchain-bootstrap\scripts\bootstrap.ps1 -Requirements skills\office\document-ai-structurer\requirements.txt -PyVersion 3.12
```

On first run, Docling downloads its layout-detection + OCR (RapidOCR) models from HuggingFace/ModelScope to `~/.cache` or local site-packages — needs network, a few dozen MB, only downloaded once.

## Run

```bash
# From the repo root, shared venv:
.venv/bin/python skills/office/document-ai-structurer/scripts/structure_doc.py <input_file> <output_dir>
# Windows: .venv\Scripts\python.exe skills\office\document-ai-structurer\scripts\structure_doc.py <input_file> <output_dir>
```

## Output

```
<output_dir>/
  index.json          # manifest: source_file, title, engine, sections[], images[]
  full.md              # full text markdown (read when the whole flow is needed)
  full_artifacts/       # images extracted from the document (auto-generated by Docling when present)
  sections/
    00-<slug>.md
    01-<slug>.md
    ...                # each file is one section, split on level-2 headings (##)
```

`index.json.sections[].file` points to each file under `sections/` — the consuming agent should read `index.json` first to decide which section to read, instead of always loading `full.md`.

## Legal-article structuring mode (Điều/Khoản/Điểm)

For a Vietnamese legal-article document, the default heading-split (`##`) is the wrong unit — Docling rarely emits "Điều N." as a markdown heading, and even when it does, a fixed rule can't be trusted to get OCR/layout noise right. This mode instead makes the **reviewing agent** responsible for confirming section boundaries — the script only proposes candidates and only mechanically executes a boundary list the agent has already checked. Deliberately not a background/silent process: skipping the review step defeats the reason this mode exists.

1. Run `structure_doc.py` as above to get `full.md` from Docling.
2. **Read `full.md` yourself before trusting it.** Docling's OCR/layout extraction on a scanned Vietnamese legal PDF is not verified by this skill — spot-check a few Điều against the source for garbled diacritics, dropped lines, or merged paragraphs before proceeding.
3. Run the candidate scanner (regex heuristics only, explicitly unverified):
   ```bash
   .venv/bin/python skills/office/document-ai-structurer/scripts/suggest_legal_boundaries.py <output_dir>/full.md -o structure.json
   ```
4. **Review `structure.json` yourself.** `khoan`/`diem` entries are regex guesses (any numbered/lettered list matches) — false positives are expected and must be removed or corrected; `_dieu` boundaries are more reliable but still check each one against `full.md` (open it with line numbers visible — `start_line` is 1-indexed, matching how the Read tool numbers lines). Edit `structure.json` directly to fix anything wrong.
5. Once `structure.json` reflects what you actually verified, mechanically build the output:
   ```bash
   .venv/bin/python skills/office/document-ai-structurer/scripts/apply_legal_structure.py <output_dir>/full.md structure.json <output_dir> [--overwrite]
   ```

Output differs from the default mode: `index.json` gets `"structure_mode": "legal"`, each section is one Điều (the citable unit — "Điều 5 Khoản 2" still needs Điều 5's full text for context), and `khoan`/`diem` are recorded as line-anchored metadata inside each section entry, not split into their own files.

This mode is a **reading/structuring capability only** — it does not verify hiệu lực (in-effect) status, and it never invents effective-date/status/amendment metadata; those fields simply don't exist in the output unless a caller adds them separately. See `skills/legal/legal-citation-checker/SKILL.md` and `skills/legal/legal-form-filler/SKILL.md` for the 2 real data gaps this was built to eventually support (not yet wired together — those skills don't consume this output yet).

See `assets/legal_text_sample.md` for a synthetic (not real) test fixture used to verify both scripts.

## Multi-document catalog (cross-document lookup)

Once several documents have gone through legal-article structuring mode, aggregate them into one catalog an agent (or `legal-citation-checker`) can query without knowing which folder holds which document:

```bash
.venv/bin/python skills/office/document-ai-structurer/scripts/build_catalog.py <corpus_root_dir> -o catalog.json
```

`<corpus_root_dir>` is a directory containing one subfolder per structured document (each with its own `index.json` from `apply_legal_structure.py`). To let a document be matched by `van_ban_so_hieu` (the exact field name `legal-citation-checker` uses), add a `doc_meta.json` next to that document's `index.json`:

```json
{ "van_ban_so_hieu": "30/2020/NĐ-CP", "van_ban_ten": "Nghị định ..." }
```

This is caller-declared, never invented by the script — a folder without `doc_meta.json` is still included in `catalog.json` (identified by folder name only), reported clearly as unmatched rather than silently skipped. `catalog.json` records, per document, every Điều number found, its section file path, and its Khoản list (verbatim, copied from that Điều's own `index.json` entry) — `legal-citation-checker --catalog catalog.json` uses the Điều numbers to flag a citation to an Điều that doesn't exist in the corpus for a document the catalog covers, and `legal-form-filler`'s `checklist_from_catalog.py` uses the Khoản list to extract a document checklist from a real Điều instead of one being hand-typed with no source. The Điều-existence check is **existence, not hiệu lực** — a real Điều number that was repealed last year still "exists" in an out-of-date corpus; see `legal-citation-checker/SKILL.md` for the exact scope boundary.

## Known limitations (v0.3.1, not yet through official quality-eval)

- Default mode: sections only split on level-2 headings (`##`). A document with no headings (or only level-1/3+ headings) will produce a single section or unexpected segmentation — check `index.json.sections` after running, don't assume it always splits cleanly.
- Images are extracted by Docling into `full_artifacts/` and referenced in `full.md`; the script doesn't yet split images per section or generate a separate caption/OCR-text per image in `index.json.images` (only records Docling's internal `id` + `ref`) — needs improvement for image/chart-heavy source documents.
- Default mode only smoke-tested on 1 English-language academic PDF (`D:/elix/researches/papers/_pdf_export/a1_3_vn_misconceptions.pdf`, 37 sections, 0 images). Not yet tested on DOCX/PPTX/XLSX/HTML/Vietnamese scans.
- Legal-article mode verified against a synthetic fixture only (`assets/legal_text_sample.md`, hand-authored, not a real government document) — 4 Điều, 6 Khoản, 5 Điểm all correctly boundary-detected and correctly split; refusal paths verified for real (malformed JSON, empty sections, out-of-order/out-of-bounds `start_line`, existing-output without `--overwrite`, no-Điều-found). **Not yet verified against real Docling output from a scanned Vietnamese legal PDF** — no such source document was available this session (owner confirmed: not needed to build this capability, but still an open real-world verification gap before relying on it for an actual scan).
- Chương (chapter-level) grouping above Điều is not modeled — out of scope for this version.
- `build_catalog.py` verified against a synthetic 2-document corpus (`assets/legal_text_sample.md` reused twice, one with `doc_meta.json`, one deliberately without) — correctly parsed 4 Điều numbers per document, correctly flagged the undeclared document as unmatched rather than silently dropping it, correctly refused an empty/nonexistent corpus root. Not yet exercised on a real multi-document legal corpus.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit — re-audit needed at v0.3.0, new script).
