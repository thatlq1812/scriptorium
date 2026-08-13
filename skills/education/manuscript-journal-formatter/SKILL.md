---
name: manuscript-journal-formatter
description: Validates a manuscript's in-text citation format and its declared reference list's format against a caller-declared citation style -- IEEE (numbered bracket citations, sequentially numbered reference list) or APA 7th edition (name-year citations, alphabetically ordered reference list) -- catching a fabricated/mistyped citation number or author-year, a reference never cited in-text, a wrong-style citation mixed into the wrong style, or a reference list out of the required order. Use after drafting a manuscript to check citation-format consistency against the target journal's declared style family before submission. Do NOT use this to generate or reformat BibTeX entries (that's `citation-management`'s job), to select which citation style a target journal requires (the caller must already know and declare it), or to verify that a citation's content actually supports the claim made about it.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (re, json, argparse) -- no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean on Claude Code (2026-07-29); see "Verified" section below for exact test-case detail.
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Two real, publicly documented style guides are encoded, each cited to its actual public source (never invented): IEEE's numbered-bracket in-text citation + sequentially-numbered reference-list convention, from the IEEE Editorial Style Manual for Authors (https://ieeeauthorcenter.ieee.org/wp-content/uploads/IEEE-Editorial-Style-Manual-for-Authors.pdf) and the IEEE Reference Guide (https://journals.ieeeauthorcenter.ieee.org/wp-content/uploads/sites/7/IEEE_Reference_Guide.pdf); APA 7th edition's name-year in-text citation + alphabetically-ordered reference-list convention (including the a/b/c duplicate-author-year disambiguation rule, Ch. 9 section 9.42), from the APA Style website's citation guidance (https://apastyle.apa.org/style-grammar-guidelines/citations). citation-management's own SKILL.md explicitly states it 'doesn't validate citation STYLE consistency across a whole bibliography (APA vs Vancouver etc.)' -- this skill closes exactly that documented gap, applied to a manuscript's body text (in-text markers + reference list ordering), not bibliography generation from an identifier."
  version: 0.1.0
  grounding: required
  object_type: ["manuscript", "citation", "reference-list"]
---

# manuscript-journal-formatter

Validates that a manuscript's in-text citations and reference list are internally consistent with a caller-declared citation style (IEEE or APA 7th edition). Never generates, rewrites, or reformats citations itself -- this is a format/consistency checker, not a citation generator.

## Why this skill, and why this scope

Checked against `citation-management` and `peer-review` (this repo's existing general-tier research cluster) before building. `citation-management` resolves a DOI/PMID/arXiv identifier into a correctly formatted BibTeX entry, and its own SKILL.md states plainly: *"Doesn't validate citation STYLE consistency across a whole bibliography (APA vs Vancouver etc.) -- only produces correct BibTeX; style rendering is a separate concern."* That is exactly this skill's job, and it does not overlap: `citation-management` never looks at manuscript body text or reference-list ordering, and this skill never resolves an identifier or generates a `.bib` entry. `peer-review` reviews a manuscript's argument/evidence quality and channel-separation discipline, not its citation formatting at all. No existing skill covers manuscript-body citation-style consistency -- this is a real, unaddressed gap.

## The 2 styles this skill encodes

Both are real, publicly documented, and cited exactly (see `metadata.elicited_from` for the source URLs) -- no style's rules are invented.

| | IEEE | APA (7th ed.) |
| --- | --- | --- |
| In-text citation | Bracketed number(s): `[1]`, `[1], [2]`, `[1]-[3]` | Name-year, parenthetical `(Smith, 2021)` or narrative `Smith (2021)` |
| Reference list order | Sequential by citation number, `[1]`, `[2]`, ... matching list order | Alphabetical by first author's surname |
| Duplicate handling | N/A (numeric) | Same author + year needs an `a`/`b`/`c` suffix (`2021a`, `2021b`) per APA §9.42 |

## Run

```bash
python scripts/validate_manuscript_style.py --style ieee|apa <manuscript.txt> <references.json>
```

Start from `assets/references_ieee_template.json` or `assets/references_apa_template.json`; see `assets/manuscript_ieee_sample.txt` / `assets/manuscript_apa_sample.txt` for a working example of each. Exit 0 = in-text citations and reference-list ordering are consistent with the declared style (every in-text citation resolves to a real reference-list entry, every reference-list entry is cited at least once, no wrong-style citation forms detected), 1 = errors found (each naming the exact citation/entry and reason), 2 = malformed input.

## What this skill does NOT do

- Doesn't generate or reformat BibTeX/citation entries -- that's `citation-management`.
- Doesn't select which style a target journal requires -- the caller must already know and declare `--style`; this skill has no journal database.
- Doesn't verify a citation's content actually supports the claim made about it, or that a reference's title/authors are factually correct -- only that the *format* is internally consistent (same discipline `legal-research-brief` documents for its own citation-id-only check).
- Doesn't cover any style beyond IEEE and APA 7th ed. (e.g. Vancouver, Chicago, MLA) -- adding one requires citing that style guide's actual rules, not guessing from IEEE/APA's shape.
- Doesn't parse semicolon-separated multi-citation groups in APA form (e.g. `(Ahmadi, 2019; Baker, 2021)`) -- see Known limitations.
- Doesn't call any LLM/AI API -- pure stdlib regex-based structural validation.

## Verified

Ran for real (2026-07-29, Python 3.12.13, this machine's system interpreter -- stdlib only, no venv needed):

1. **IEEE valid**: `assets/manuscript_ieee_sample.txt` (uses `[1]`, `[2]`, `[3]`, `[1]-[3]`) against a 3-entry sequential reference list -- exit 0.
2. **APA valid**: `assets/manuscript_apa_sample.txt` (uses `(Ahmadi, 2019)`, `Baker (2021)`, `Ahmadi (2019)`) against a 2-entry alphabetically sorted reference list -- exit 0.
3. **IEEE broken -- fabricated number + wrong-style mix**: manuscript cites `[4]` (out of range for a 3-entry list) and includes a stray `(Ahmadi, 2019)` name-year citation -- correctly caught the fabricated `[4]`, the wrong-style name-year form, and the uncited `[3]` entry (3 errors), exit 1.
4. **IEEE broken -- non-sequential reference list**: reference list keyed `"1"`, `"3"` (skipping `"2"`) -- correctly caught the non-sequential key and both resulting out-of-range in-text citations (3 errors), exit 1.
5. **APA broken -- fabricated citation + wrong-style bracket**: manuscript cites `Smith (2020)` (not in the reference list) and includes a stray `[1]` bracket citation -- correctly caught both plus the uncited `Baker, 2021` entry (3 errors), exit 1.
6. **APA broken -- unsorted list + unsuffixed duplicate**: reference list ordered Baker/Ahmadi/Ahmadi (not alphabetical) with two distinct `Ahmadi, 2019` entries and no `a`/`b` suffix -- correctly caught both violations (2 errors), exit 1.
7. **Malformed input**: `references.json` with a missing closing brace/bracket (invalid JSON) -- correctly refused with `MALFORMED: cannot read references file: Expecting ',' delimiter: line 5 column 1 (char 108)`, exit 2.

## Known limitations (v0.1.0)

- APA in-text detection does not parse semicolon-separated multi-citation groups (`(Ahmadi, 2019; Baker, 2021)`) as two separate citations -- each citation must currently appear in its own parenthetical or narrative form. A manuscript using grouped parentheticals will need reformatting before this check is meaningful for that sentence.
- The wrong-style detectors (`IEEE_SUSPECT_NAME_YEAR_RE` / `APA_SUSPECT_BRACKET_RE`) are pattern-based heuristics, not a full grammar -- an unusual citation shape may pass undetected in either direction; they catch the common mixing mistakes, not every possible one.
- Surname matching is case-insensitive exact-string matching on the declared `surname`/`authors` fields -- a manuscript citing "Smith" when the reference list declares "Smyth" (a typo either direction) is reported as a fabricated citation, which is the intended fail-loud behavior, but the tool cannot tell a typo from a truly fabricated source.
- Does not check any non-citation formatting a real IEEE/APA submission also requires (page margins, section-heading style, figure/table caption format, abstract word count) -- citation format only.
