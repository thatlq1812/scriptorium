---
name: literature-review
description: Runs a structured literature review — searches arXiv, PubMed, and CrossRef by keyword (no API key needed), deduplicates results across sources, and synthesizes them into a themed markdown document following PRISMA-lite screening documentation. Use when writing the literature-review section of a paper/thesis, scoping the state of the art on a topic, or doing a systematic/scoping review. Do NOT use to resolve an identifier you already have into a citation — that's `citation-management`'s job; this skill is for discovering sources by keyword, not verifying a known one.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (urllib, xml.etree), network access to export.arxiv.org / eutils.ncbi.nlm.nih.gov / api.crossref.org — no API key for any of the three. No venv/shared-venv dependency needed (stdlib only). Verified running clean: Claude Code (2026-07-26) — real combined search across all 3 sources for "CRISPR sickle cell" returned 15 correctly deduplicated results (from 3 arxiv + 5 pubmed + 5 crossref raw, no lost or duplicated DOI).
metadata:
  domain: general
  task_type: research
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills skills/literature-review (MIT, verified via gh api + per-folder license check 2026-07-26) for the overall workflow shape (plan -> search -> screen -> extract -> synthesize -> verify -> generate). Rewritten from scratch: dropped the OPENROUTER_API_KEY-gated parallel-web/scientific-schematics/gget/bioservices dependencies (paid API, mandatory AI-generated figures, biology-specific databases) entirely. Replaced multi-database search with 3 free no-key APIs (arXiv, PubMed E-utils, CrossRef) covering any field, not just biomedical. Citation verification is delegated to this project's own `citation-management` skill rather than a bundled script, to avoid duplicating that logic. PDF generation is NOT bundled -- delegate to this project's `office-doc-creator`/`document-ai-structurer` if a PDF/docx is needed, keeping this skill focused on search+synthesis."
  version: 0.1.0
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
python scripts/search_literature.py "<query>" --sources arxiv pubmed crossref --max-results 10 --output sources/search_results.md
```

Deduplicates by DOI (primary) or normalized title (fallback) across all 3 sources in one pass. Run multiple queries (synonyms, related terms) and combine results manually if the first query is too narrow — the script does not do query expansion itself.

### 3. Screen

Manually apply the inclusion/exclusion criteria from step 1: title screening → abstract screening → full-text screening. Record counts at each stage in the template's screening-flow block (§2.3) — this is the PRISMA-lite documentation, kept as a plain-text flow diagram, no image-generation dependency needed.

### 4. Synthesize

Fill `assets/review_template.md` §3 organized BY THEME, not study-by-study. Compare and contrast across studies within each theme; note consensus vs. controversy.

### 5. Verify every citation

Before finalizing, resolve every DOI/PMID/arXiv ID that will appear in §8 References through the **`citation-management`** skill — never hand-type bibliographic details from memory or trust a search result's fields as final without going through the verified resolver.

### 6. Optional: generate PDF/DOCX output

Not bundled here. If a polished PDF/DOCX is needed, hand the finished markdown to `office-doc-creator` or `document-ai-structurer`.

## Bundled files

- `scripts/search_literature.py` — searches arXiv Atom API, PubMed E-utils (esearch+esummary), and CrossRef works API by keyword; deduplicates; outputs markdown table or `--json`.
- `assets/review_template.md` — the structured template (Introduction, Search Strategy, Screening Flow, Results-by-theme, Critical Analysis, Discussion, Limitations, Future Directions, References).

## What this skill does NOT do

- Doesn't verify individual identifiers — that's `citation-management` (step 5 above always delegates there).
- Doesn't call any LLM/AI API for search, summarization, or figure generation — pure keyword search against 3 factual bibliographic APIs, and manual/human synthesis.
- Doesn't search biology-specific databases (ChEMBL, KEGG, UniProt, AlphaFold) — out of scope for a general-tier skill; a future specialized-tier skill could add this.
- Doesn't generate PDF/DOCX itself — delegate to `office-doc-creator`/`document-ai-structurer`.
- Doesn't do citation-count/venue-tier "impact" ranking automatically — CrossRef/PubMed/arXiv don't reliably expose citation counts via their free APIs; if impact ranking is needed, it's a manual step using each source's own web interface.

## Known limitations (v0.1.0)

- No query expansion/synonym handling — a too-narrow query misses papers; run several queries and merge manually.
- CrossRef's free-text `query` parameter is relevance-ranked by CrossRef itself, not by citation count — matches quality varies by field.
- Same rate-limit caveat as `citation-management`: no retry/backoff; a failed source is skipped with a stderr message, other sources still proceed.
