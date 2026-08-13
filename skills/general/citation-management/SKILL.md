---
name: citation-management
description: Resolves a DOI, PMID, or arXiv ID into a correctly formatted, LaTeX-safe BibTeX entry, fetching real metadata (title, authors, journal, year) from free bibliographic databases (CrossRef, PubMed, arXiv) — no API key needed. Use when building a bibliography, converting an identifier list into citations, or verifying that a citation's metadata actually matches the real publication. Do NOT use to search for papers by topic (that's `literature-review`'s job) — this skill only resolves an identifier you already have into a citation.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (urllib, xml.etree), network access to api.crossref.org / eutils.ncbi.nlm.nih.gov / export.arxiv.org — no API key for any of the three, no venv/shared-venv dependency. Verified running clean on Claude Code (2026-07-26, v0.2.0); the run evidence is in `metadata.verified_runs`. No other harness verified — do not add one without testing it directly.
metadata:
  domain: general
  task_type: research
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills skills/general/citation-management (MIT, verified via gh api + per-folder license check 2026-07-26) for the overall problem shape (identifier -> verified BibTeX). Rewritten from scratch: dropped the OPENROUTER_API_KEY/NCBI-credential dependency and the coupling to their scientific-schematics image-gen skill, replaced with plain free-API lookups (CrossRef/PubMed E-utils/arXiv Atom) -- no AI backend, no paid dependency, works for any citation need (legal, education, any field), not science-specific."
  version: 0.2.0
  verified_runs: "2026-07-26, v0.2.0, Claude Code: real lookups for a DOI in URL form (Nature/AlphaFold), a PMID (Nature), and an old-style arXiv ID (cond-mat/0102536, whose published DOI was picked up automatically); 3 real non-resolving identifiers (unknown PMID, unknown arXiv ID, 404 DOI) each failed loudly with exit 1 and nothing written; a mixed batch of 3 valid + 1 invalid wrote the 3 valid entries and still exited 1. Offline: LaTeX escaping/markup mapping, identifier normalization across 9 pasted forms, and BibTeX key collision suffixing."
  changelog_0_2_0: "Fixed 3 defects found by re-testing v0.1.0: (1) an unresolvable PMID produced a placeholder entry (@article{Unknownnd, title={Untitled}}) and exit 0 -- the exact fabricated-citation failure this skill exists to prevent; every resolver now validates the returned record and fails loudly. (2) An unknown arXiv ID crashed with an AttributeError traceback, killing the whole batch. (3) BibTeX values were interpolated raw, so a title containing & % _ # or JATS markup produced a .bib file that breaks a LaTeX build. Added: LaTeX escaping + i/em/sub/sup markup mapping, title case protection, URL/doi:/arXiv:/PMID: prefix handling, old-style arXiv IDs, BibTeX key collision suffixing, bounded retry/backoff on 429/5xx, optional CROSSREF_MAILTO polite-pool header, and an overwrite guard on --output."
---

# citation-management

Turns an identifier you already have (DOI, PMID, or arXiv ID) into a real, verified BibTeX entry — not a guess, an actual metadata fetch from the publisher's own record.

## Why not use an LLM to write the BibTeX

An LLM can hallucinate author names, years, page numbers — exactly the kind of fabricated-citation risk `docs/specs/STRATEGY_SPEC.md` §5 flags for the legal vertical (same failure mode as fabricated case law). This skill only reports what CrossRef/PubMed/arXiv's own records actually say; if an identifier doesn't resolve, it fails loudly instead of inventing plausible-looking metadata.

## Run

```bash
python scripts/resolve_citation.py <doi_or_pmid_or_arxiv_id> [<id2> ...] [--output refs.bib] [--force]
```

Identifier type is auto-detected: `10.xxxx/...` → DOI (CrossRef), all-digits → PMID (PubMed), `YYMM.NNNNN` or old-style `cond-mat/0102536` → arXiv (Atom API). Pasted forms are normalized too: `https://doi.org/10.x/y`, `doi:10.x/y`, `arXiv:2401.12345`, `PMID: 33057196`.

Multiple identifiers in one call produce one combined `.bib` file. A failed identifier is reported to stderr, skipped, and the run exits 1 — the resolved entries are still written, so a partial batch is never lost, but a non-zero exit always means "not every citation in this list is real."

- **Exit codes**: 0 = every identifier resolved, 1 = at least one did not (named on stderr), 2 = usage/write refusal.
- `--output` refuses to overwrite an existing file unless `--force` is passed.
- Set `CROSSREF_MAILTO` to a real address to join CrossRef's polite pool (optional; no fake address is ever sent).

## Guarantee: never invents a citation

Every resolver validates the record it got back — an unknown PMID, a withdrawn arXiv ID, or a 404 DOI ends as `FAILED <id>: <reason>` on stderr with nothing written for it. There is no code path that emits an entry with placeholder authors/title. This is the single most important behavior of this skill; if a change ever makes an unresolvable identifier produce output, that is a regression, not a convenience.

Field values are escaped for LaTeX (`&`, `%`, `$`, `#`, `_`, `~`, `^`, braces, backslash), publisher markup is mapped (`<i>`/`<em>` → `\emph{}`, `<sub>`/`<sup>` → `\textsubscript{}`/`\textsuperscript{}`) and other tags are stripped, so the `.bib` compiles as-is. Titles are brace-protected to keep their original capitalization. Identifier fields (`doi`, `eprint`, `pmid`) are left verbatim apart from the characters that would break `.bib` parsing, because biblatex prints them through its own URL machinery.

## What this skill does NOT do

- Doesn't search for papers by topic/keyword — that's `literature-review`.
- Doesn't call any LLM/AI API — pure factual metadata lookup, no hallucination risk by construction.
- Doesn't validate citation STYLE consistency across a whole bibliography (APA vs Vancouver etc.) — only produces correct BibTeX; style rendering is a separate concern (e.g. via a `.bst` file or a reference manager).
- Doesn't handle books, websites, or other non-DOI/PMID/arXiv sources — those need manual BibTeX entry; this skill covers the 3 identifier types with reliable free APIs.

## Known limitations (v0.2.0)

- Retry/backoff covers 429 and 5xx with 2 retries by default (`--retries`), honoring `Retry-After` up to 30s. A sustained rate-limit block still fails those identifiers — it is reported, never silently retried forever.
- Entry type is inferred from CrossRef's `type` field for DOIs and fixed to `@misc` for arXiv / `@article` for PubMed. A PMID pointing at a book chapter is still emitted as `@article`.
- Preprint-then-published DOI mismatch is not reconciled: resolving the arXiv ID gives the arXiv record (plus the published DOI when arXiv exposes one), resolving the journal DOI gives the published record. The skill does not merge the two — pick which version the bibliography should cite.
- Author name parsing follows each API's own convention (CrossRef family/given, PubMed "Family II" collapsed) — it is reported as returned, never reformatted or guessed at.
