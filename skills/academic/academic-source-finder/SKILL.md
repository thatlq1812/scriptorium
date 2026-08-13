---
name: academic-source-finder
description: A protocol for finding citable academic sources, not a search service — the calling agent does the actual searching using whatever web/database tools it already has (Google Scholar, JSTOR, PubMed, an institutional library search, etc.); this skill supplies the checklist for what makes a source citable (recognized source_type, honest peer-reviewed declaration, a resolvable doi_or_url, a recorded access date, and an optional recency threshold) and a deterministic validator that checks a caller-declared source list against it, catching an unvetted or under-documented source before it's cited. Use when assembling a source list for an academic essay/paper and you want a mechanical check that every source is honestly documented before citing it. Do NOT use this skill expecting it to search the web or an academic database itself — it has no network access and calls no AI backend; it is a checklist + a validator, executed against a source list the calling agent already assembled with its own tools.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, argparse) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: research
  risk_tier: N2
  source: self-authored
  elicited_from: "General-capability tier per CLAUDE.md principle 4 — public-source grounding, no expert interview needed. The citable-academic-source checklist (peer-reviewed status, source-type distinctions between a journal article/preprint/government report/thesis vs. a non-academic blog, recency relevance, and full bibliographic/access-date documentation) is standard, widely-taught university-library and writing-center guidance (e.g. how academic-library 'evaluating sources' / CRAAP-test guidance and citation-manual conventions like APA/MLA source-type categories describe a citable source), not a niche or tacit practice. Architecturally grounded directly in this repo's own deep-research and legal-web-search precedent (both read in full before building this skill): Scriptorium holds no AI backend and no web-search capability of its own (docs/specs/STRATEGY_SPEC.md, CLAUDE.md non-negotiable principle 8), so 'academic source finder' cannot mean a live search tool — it means the same protocol-plus-validator shape those two skills already established, generalized to the university-student academic-source-evaluation use case instead of general open-ended research or Vietnamese legal search."
  version: 0.1.0
  grounding: required
  object_type: ["citation", "source-list"]
---

# academic-source-finder

A protocol, not a search service. This skill never searches the web, a database, or calls an AI provider, and holds no API key — Scriptorium does not integrate an AI backend (`CLAUDE.md` non-negotiable principle 8). What it provides instead: a checklist for what makes an academic source citable, and a deterministic validator that checks a caller-declared source list against that checklist before the list is trusted for an essay or paper — the same relationship `deep-research` has to general research and `legal-web-search` has to Vietnamese legal search, generalized to academic-source evaluation for a university student's writing.

## Why this scope, and why NOT a search tool

Scriptorium has no AI backend and no web-search capability of its own — every "finder"/"research" skill in this repo (`deep-research`, `legal-web-search`) is a discipline-plus-validator the *calling agent* executes with its own tools, never a service that does the searching itself. Building `academic-source-finder` as anything that attempts a live search would repeat the exact non-goal `deep-research`'s and `legal-web-search`'s own SKILL.md files already rule out. This skill implements exactly the same shape: a checklist for a disciplined academic-source search, and a validator for the resulting record.

## Protocol (followed by the calling agent, not by any script here)

1. **Search recognized academic locations** (`references/source_type_allowlist.json`'s `recognized_academic_search_locations` — Google Scholar, JSTOR, PubMed, IEEE Xplore, ScienceDirect, SpringerLink, ERIC, SSRN, arXiv, Web of Science, Scopus, the institution's own library discovery search, or an official government data portal) rather than a general web search when looking for a source to cite.
2. **Prefer a primary-tier source type** (peer-reviewed journal article, conference paper, academic book/chapter, government report) over a secondary-tier one (thesis/dissertation, preprint, reputable news analysis) when both are available on the same claim — see the allowlist's `tier` field.
3. **Record every source's real bibliographic detail as you find it**: id, title, authors, publication year, source type, an honest `peer_reviewed` true/false, venue or publisher, a resolvable DOI or URL, and the date you accessed it — not retroactively from memory.
4. **Declare `non_academic_justification` explicitly** if a source doesn't fit any recognized academic type (a blog post, a company page, an unreviewed wiki article) — never silently cite it as if it were vetted.
5. **Note recency deliberately** — if the assignment/field requires current sources, check publication year against a stated threshold; an older source isn't automatically wrong (a foundational or historical source may be exactly what's needed), but the age should be a conscious choice, not an oversight.
6. **Validate before trusting the source list**:
   ```bash
   python skills/academic/academic-source-finder/scripts/validate_source_list.py source_list.json \
       [--max-age-years N --current-year Y] [--render sources.md]
   ```
   Exit 0 = every source has a recognized `source_type`, an internally-consistent `peer_reviewed` declaration, a non-empty `doi_or_url`, and a recorded `accessed_date` (warnings may still print for a recency flag or a `peer_reviewed`/`source_type` mismatch worth double-checking). Exit 1 = errors (each naming the exact source id/field and reason). Exit 2 = malformed input, or `--max-age-years`/`--current-year` supplied without the other.

Start from `assets/source_list_template.json` for the exact schema.

## What this skill does NOT do

- Does not search anything itself — zero network calls in `validate_source_list.py`.
- Does not call any LLM/AI API — Scriptorium never does (`CLAUDE.md` non-negotiable principle 8); this is a protocol + validator only, same shape as `deep-research`/`legal-web-search`.
- Does not verify a source's *content* actually supports whatever claim it's cited for, or that the bibliographic details (title, authors, DOI) are accurate — only that the declared fields are present, well-formed, and internally consistent. A human/agent must still confirm the source is real and says what it's cited as saying.
- Does not fetch or resolve the `doi_or_url` to confirm the link actually works — only that a non-empty string was recorded. A dead link or a typo'd DOI still passes.
- Does not infer today's date from the system clock for the recency check — `--current-year` must be explicitly supplied by the caller alongside `--max-age-years`, so the check is fully deterministic and reproducible, never silently dependent on when the script happened to run.
- Does not decide whether a given assignment requires only primary-tier sources, only recent sources, or a minimum source count — those requirements are the assignment's own rules, supplied by the caller via `--max-age-years`/`--current-year` or by manual review of the `tier` field, never hard-coded here.

## Verified

`validate_source_list.py`: the bundled `assets/source_list_template.json` (3 sources: 1 peer-reviewed journal article, 1 government report, 1 preprint, all correctly declared) validated with **zero errors**; with `--max-age-years 5 --current-year 2026` it correctly warned on the 2019 journal article (7 years old, exceeds the threshold) while leaving the other 2 sources unflagged; without the recency flags it passed cleanly (exit 0) and `--render` produced a correct Markdown source list. Supplying `--max-age-years` without `--current-year` was correctly refused (exit 2). An empty `sources: []` list was correctly refused (exit 1). A record with one source missing `accessed_date` and a second source using an unrecognized `source_type` ("made-up-source-type"), a non-boolean `peer_reviewed` ("yes" instead of true/false), and a malformed `accessed_date` ("not-a-date") was correctly refused, naming all 4 issues exactly (exit 1). A duplicate `id` across two otherwise-complete sources was correctly refused, naming both indices (exit 1). Malformed JSON was correctly refused (exit 2, exact parse error reported).

## Known limitations (v0.1.0)

- `non_academic_justification` presence is checked, but its *content* is never judged — an empty-looking but technically non-empty justification string (e.g. "trust me") passes exactly like a substantive one. The check catches a missing justification, not a weak one.
- The `peer_reviewed`/`source_type` consistency check (e.g. a preprint flagged `peer_reviewed: true`) is a warning, not a hard error — declared as a heuristic double-check, since a genuine edge case (an invited, peer-reviewed preprint-server posting) is possible and this skill cannot independently verify the claim either way.
- `recognized_academic_search_locations` in `references/source_type_allowlist.json` is a "where to look first" guide, not an enforced allowlist — unlike `legal-web-search`'s domain allowlist, this validator does not check or record which database a source was actually found through, only the source's own declared fields. A source found via a general web search still passes if honestly documented.
- No DOI/URL resolution or dead-link check — a syntactically non-empty but broken or fabricated `doi_or_url` string passes validation. Confirming a citation actually resolves is `citation-management`'s and the calling agent's responsibility, not this skill's.
- Doesn't check citation-format correctness (APA/MLA/Chicago formatting of the reference list) — that's `citation-management`'s scope; this skill validates the underlying source metadata, not its rendered citation style.
