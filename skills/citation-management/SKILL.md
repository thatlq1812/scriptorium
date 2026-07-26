---
name: citation-management
description: Resolves a DOI, PMID, or arXiv ID into a correctly formatted BibTeX entry, fetching real metadata (title, authors, journal, year) from free bibliographic databases (CrossRef, PubMed, arXiv) — no API key needed. Use when building a bibliography, converting an identifier list into citations, or verifying that a citation's metadata actually matches the real publication. Do NOT use to search for papers by topic (that's `literature-review`'s job) — this skill only resolves an identifier you already have into a citation.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (urllib, xml.etree), network access to api.crossref.org / eutils.ncbi.nlm.nih.gov / export.arxiv.org — no API key for any of the three. No venv/shared-venv dependency needed (stdlib only). Verified running clean: Claude Code (2026-07-26) — real lookups for a DOI (Nature/AlphaFold), a PMID (Nature), an arXiv ID, and a real invalid-input failure case, all correct.
metadata:
  domain: general
  task_type: research
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills skills/citation-management (MIT, verified via gh api + per-folder license check 2026-07-26) for the overall problem shape (identifier -> verified BibTeX). Rewritten from scratch: dropped the OPENROUTER_API_KEY/NCBI-credential dependency and the coupling to their scientific-schematics image-gen skill, replaced with plain free-API lookups (CrossRef/PubMed E-utils/arXiv Atom) -- no AI backend, no paid dependency, works for any citation need (legal, education, any field), not science-specific."
  version: 0.1.0
---

# citation-management

Turns an identifier you already have (DOI, PMID, or arXiv ID) into a real, verified BibTeX entry — not a guess, an actual metadata fetch from the publisher's own record.

## Why not use an LLM to write the BibTeX

An LLM can hallucinate author names, years, page numbers — exactly the kind of fabricated-citation risk `docs/specs/STRATEGY_SPEC.md` §5 flags for the legal vertical (same failure mode as fabricated case law). This skill only reports what CrossRef/PubMed/arXiv's own records actually say; if an identifier doesn't resolve, it fails loudly instead of inventing plausible-looking metadata.

## Run

```bash
python scripts/resolve_citation.py <doi_or_pmid_or_arxiv_id> [<id2> ...] [--output refs.bib]
```

Identifier type is auto-detected: `10.xxxx/...` → DOI (CrossRef), all-digits → PMID (PubMed), `YYMM.NNNNN` → arXiv ID (arXiv Atom API). Multiple identifiers in one call produce one combined `.bib` file; a failed identifier is reported to stderr and skipped, not silently dropped.

## What this skill does NOT do

- Doesn't search for papers by topic/keyword — that's `literature-review`.
- Doesn't call any LLM/AI API — pure factual metadata lookup, no hallucination risk by construction.
- Doesn't validate citation STYLE consistency across a whole bibliography (APA vs Vancouver etc.) — only produces correct BibTeX; style rendering is a separate concern (e.g. via a `.bst` file or a reference manager).
- Doesn't handle books, websites, or other non-DOI/PMID/arXiv sources — those need manual BibTeX entry; this skill covers the 3 identifier types with reliable free APIs.

## Known limitations (v0.1.0)

- CrossRef/PubMed/arXiv have their own rate limits — no retry/backoff logic yet; a burst of many identifiers in one call may hit a 429, not currently handled gracefully (fails that one identifier, continues with the rest).
- BibTeX key generation is simple (`FirstAuthorFamilyYear`) — no collision handling if two different papers would generate the same key.
- Only tested with real, well-formed identifiers for papers that exist — hasn't been tested against edge cases like preprint-then-published-version DOI mismatches or PMIDs for non-article record types (books, datasets).
