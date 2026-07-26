---
name: literature-review
description: Runs a structured literature review — searches arXiv, PubMed, and CrossRef by keyword (no API key needed), merges duplicate records across sources by DOI or title, filters by year, optionally pulls abstracts for screening, and reports the record counts a PRISMA screening flow needs. Use when writing the literature-review section of a paper/thesis, scoping the state of the art on a topic, or doing a systematic/scoping review. Do NOT use to resolve an identifier you already have into a citation — that's `citation-management`'s job; this skill is for discovering sources by keyword, not verifying a known one.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (urllib, xml.etree), network access to export.arxiv.org / eutils.ncbi.nlm.nih.gov / api.crossref.org — no API key for any of the three, no venv/shared-venv dependency. Verified running clean on Claude Code (2026-07-26, v0.2.0); the run evidence is in `metadata.verified_runs`. No other harness verified — do not add one without testing it directly.
metadata:
  domain: general
  task_type: research
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills skills/literature-review (MIT, verified via gh api + per-folder license check 2026-07-26) for the overall workflow shape (plan -> search -> screen -> extract -> synthesize -> verify -> generate). Rewritten from scratch: dropped the OPENROUTER_API_KEY-gated parallel-web/scientific-schematics/gget/bioservices dependencies (paid API, mandatory AI-generated figures, biology-specific databases) entirely. Replaced multi-database search with 3 free no-key APIs (arXiv, PubMed E-utils, CrossRef) covering any field, not just biomedical. Citation verification is delegated to this project's own `citation-management` skill rather than a bundled script, to avoid duplicating that logic. PDF generation is NOT bundled -- delegate to this project's `office-doc-creator`/`document-ai-structurer` if a PDF/docx is needed, keeping this skill focused on search+synthesis."
  version: 0.2.0
  verified_runs: "2026-07-26, v0.2.0, Claude Code: real combined 3-source search for \"CRISPR sickle cell\" (5 per source, 15 raw, 15 distinct papers, abstracts fetched from all three sources); overwrite guard and inverted year-range each refused with exit 2. Offline fixtures: an arXiv record and its CrossRef record now collapse into one row listing both sources (the case v0.1.0 always missed), a pipe/newline title no longer breaks the table, and year filtering reports out-of-range and unknown-year exclusions separately."
  changelog_0_2_0: "Fixed 3 defects found by re-testing v0.1.0: (1) deduplication never matched a DOI-carrying record against a title-only record, so an arXiv preprint and its published CrossRef/PubMed record always survived as two rows -- the most common duplicate shape, and it corrupted the PRISMA 'after deduplication' count; dedup now merges on either key and records every source a paper came from. (2) A title containing a pipe or newline broke the markdown table. (3) The script exited 0 even when every source failed, so an agent could report an empty search as a completed one. Added: --from-year/--to-year with explicit exclusion counts, --abstracts (arXiv summary, CrossRef abstract, PubMed efetch) so the documented abstract-screening step is actually possible, per-source raw counts rendered as a PRISMA-ready table, published-DOI extraction from arXiv entries, bounded retry/backoff, and an overwrite guard on --output."
---

# literature-review

Runs the search-and-synthesis core of a literature review: find sources by keyword across 3 free bibliographic databases, deduplicate, screen, and write a themed synthesis — not a study-by-study summary.

## Why this differs from the original K-Dense-AI skill

The source skill required a paid `OPENROUTER_API_KEY`-backed web-search CLI (`parallel-cli`), mandated at least 1-2 AI-generated figures per review via a "scientific-schematics" (Nano Banana Pro) skill, and leaned on biology-specific database skills (`gget`, `bioservices`) baked into the core workflow. All of that violates Scriptorium's no-AI-backend, no-mandatory-paid-dependency principles and biology-couples a workflow that should work for any field (law, education, engineering, etc.). This version keeps the methodology (PRISMA-lite screening documentation, thematic synthesis, verified citations) and replaces every dependency with free, no-key alternatives or an explicit handoff to another Scriptorium skill.

## Workflow

### 1. Plan and scope

Define the research question, review type (narrative/scoping/systematic/meta-analysis), and inclusion/exclusion criteria (date range, language, study types) BEFORE searching — write these into a copy of `assets/review_template.md` §1-2 first.

### 2. Search

```bash
python scripts/search_literature.py "<query>" --sources arxiv pubmed crossref --max-results 10 \
    --from-year 2015 --abstracts --output sources/search_results.md
```

Records are merged across sources when they share a DOI **or** a normalized title, so an arXiv preprint and its published CrossRef/PubMed record become one row listing both sources — the reason the "after deduplication" count can be trusted. Run multiple queries (synonyms, related terms) and combine results manually if the first query is too narrow; the script does not do query expansion itself.

- **Exit codes**: 0 = every requested source answered, 1 = some failed (results are partial and say so), 2 = every source failed / refused to overwrite. Never report counts from a run that exited 1 as a complete search.
- `--from-year`/`--to-year` apply the date range defined in step 1. Records whose year is unknown are excluded and counted separately — they are not silently dropped.
- `--abstracts` is required for step 3's abstract screening; without it only titles come back.

### 3. Screen

Manually apply the inclusion/exclusion criteria from step 1: title screening → abstract screening → full-text screening. The search output already contains the raw-per-source, combined, after-dedup, and year-excluded counts as a table — copy those into the template's screening-flow block (§2.3) and add your own title/abstract/full-text stage counts. This is the PRISMA-lite documentation, kept as a plain-text flow diagram, no image-generation dependency needed.

### 4. Synthesize

Fill `assets/review_template.md` §3 organized BY THEME, not study-by-study. Compare and contrast across studies within each theme; note consensus vs. controversy.

### 5. Verify every citation

Before finalizing, resolve every DOI/PMID/arXiv ID that will appear in §8 References through the **`citation-management`** skill — never hand-type bibliographic details from memory or trust a search result's fields as final without going through the verified resolver.

### 6. Optional: generate PDF/DOCX output

Not bundled here. If a polished PDF/DOCX is needed, hand the finished markdown to `office-doc-creator` or `document-ai-structurer`.

## Bundled files

- `scripts/search_literature.py` — searches arXiv Atom API, PubMed E-utils (esearch+esummary, plus efetch for abstracts), and CrossRef works API by keyword; merges duplicates across sources; filters by year; outputs a markdown table + screening counts (+ abstracts section), or `--json` carrying the same counts.
- `assets/review_template.md` — the structured template (Introduction, Search Strategy, Screening Flow, Results-by-theme, Critical Analysis, Discussion, Limitations, Future Directions, References).

## What this skill does NOT do

- Doesn't verify individual identifiers — that's `citation-management` (step 5 above always delegates there).
- Doesn't call any LLM/AI API for search, summarization, or figure generation — pure keyword search against 3 factual bibliographic APIs, and manual/human synthesis.
- Doesn't search biology-specific databases (ChEMBL, KEGG, UniProt, AlphaFold) — out of scope for a general-tier skill; a future specialized-tier skill could add this.
- Doesn't generate PDF/DOCX itself — delegate to `office-doc-creator`/`document-ai-structurer`.
- Doesn't do citation-count/venue-tier "impact" ranking automatically — CrossRef/PubMed/arXiv don't reliably expose citation counts via their free APIs; if impact ranking is needed, it's a manual step using each source's own web interface.

## Known limitations (v0.2.0)

- No query expansion/synonym handling — a too-narrow query misses papers; run several queries and merge manually.
- CrossRef's free-text `query` parameter is relevance-ranked by CrossRef itself, not by citation count — match quality varies by field.
- Title-based merging normalizes case/punctuation only. Two genuinely different papers with identical titles would merge (rare); a paper whose title differs between sources beyond punctuation (translated or corrected titles) will not merge unless a shared DOI is present. Check the `Sources` column when the dedup count matters.
- Year filtering is applied client-side after fetching, so `--max-results` caps the records fetched per source *before* the filter — a narrow year range may return few rows; raise `--max-results` rather than assuming the literature is thin.
- Abstract availability varies: arXiv always has one, CrossRef often does not, PubMed needs the extra efetch call (a failure there is reported as a WARN and leaves abstracts empty rather than failing the search).
