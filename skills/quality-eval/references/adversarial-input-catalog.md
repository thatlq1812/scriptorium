# Adversarial input catalog

The input classes Pass A draws from. Every class here earned its place: it caught at least one real, reproducible defect during the 2026-07-26 hardening round of the 5 harvested skills (`docs/STATUS.md` → "v0.2.0 hardening round"). This is not a list of everything that could go wrong — it is the list of what actually did, in a codebase whose authors had already tested the happy path and written honest limitation sections.

**How to use it**: for each claim extracted in Pass A step A1, find the classes whose "probes" column matches the claim shape, and build that input for the skill under evaluation. `scripts/make_adversarial_fixtures.py` generates the file-shaped ones; the rest are written by hand per skill.

---

## 1. The identifier/record that does not exist

**Probes**: any claim of the form "fails loudly," "reports an error," "does not invent," "verifies against the real source."

Feed the tool a well-formed input that refers to nothing real: an unknown PMID, a DOI that 404s, a withdrawn arXiv ID, a database row whose foreign key is dangling. Well-formed matters — a malformed input usually hits validation early; a *plausible but nonexistent* one reaches the code path that builds a result out of whatever the API returned.

**Caught (2026-07-26)**: `citation-management` returned `@article{Unknownnd, title={Untitled}, author={Unknown}, pmid={99999999}}` and exit 0 for an unknown PMID, while its SKILL.md claimed it "fails loudly instead of inventing plausible-looking metadata." A second variant (unknown arXiv ID) crashed with an uncaught `AttributeError`, killing an entire batch and discarding the identifiers that had already resolved.

**Check**: exit code non-zero, nothing written for that input, and — the part that is easy to miss — no partial artifact containing placeholder values.

## 2. Text encoding that is not UTF-8

**Probes**: "reads a CSV/text file," "handles the user's data," any tool with a file input.

A CSV exported from Excel on a Windows machine is cp1252, not UTF-8. This is the single most common real-world file the tool will meet outside the author's own test directory.

**Caught**: `exploratory-data-analysis` raised `UnicodeDecodeError` as a raw traceback on a cp1252 CSV — in a skill whose stated posture is that every input is untrusted and every refusal is clean.

**Check**: a clean refusal naming the remedy, or correct decoding — never a traceback, never silent replacement of characters (a corrupted value that looks fine is worse than a refusal).

## 3. Structural duplication and raggedness

**Probes**: "per-column report," "one row per record," "preserves the input structure."

Two columns sharing a header name. Rows with more or fewer fields than the header. A header-only file. An empty file.

**Caught**: `exploratory-data-analysis` collapsed duplicate headers into one dict key and silently dropped the later column's data entirely, while reporting a column count that did not match the file.

**Check**: no silent data loss; the report's own counts must be consistent with the file.

## 4. Numeric values that are not numbers

**Probes**: any statistic, aggregate, threshold, or outlier flag.

`inf`, `-Infinity`, `nan`, `1_000` (Python's `float()` accepts underscores), `1e400` (overflows to `inf`), leading-zero strings, thousands separators.

**Caught**: a cell containing `inf` crashed `eda_analyzer.py` inside `statistics.pstdev` with an `AttributeError` — reachable from any file, no hostility required beyond a sentinel value someone's export tool wrote.

**Check**: no crash; non-finite values excluded from statistics and *counted separately* rather than silently dropped.

## 5. Quantitative correctness against an independent implementation

**Probes**: every numeric output — quantiles, percentages, rates, deltas, scores.

Do not eyeball the number. Compute it a second way (a stdlib function, a hand calculation on a small fixture with a known answer) and compare exactly.

**Caught**: `eda_analyzer.py` computed quartiles by raw index (`nums[n//4]`) with no interpolation, giving q1=3.0/q3=8.0 where the correct values are 3.25/7.75 — which shifted the IQR fences that drive the skill's headline outlier flag. The code read plausibly and the smoke test "passed" because nobody checked the arithmetic against `statistics.quantiles`.

**Check**: exact agreement with the independent computation on at least one fixture with a hand-verifiable answer.

## 6. Nesting, size, and field-length limits

**Probes**: "bounded," "capped," "refuses oversized input," any recursive traversal.

JSON nested 1200 levels deep. A CSV field larger than the parser's default limit. A file at and just over the declared byte cap.

**Caught**: `eda_analyzer.py` raised `RecursionError` on deeply nested JSON despite documenting a bounded, refusal-based contract.

**Check**: an explicit refusal at a documented limit; "bounded" claims must name the bound, and memory bounds must hold for the retained data, not just the file size.

## 7. Delimiter and markup injection through data into output

**Probes**: "produces a markdown table," "generates a .bib file," "writes a report," any tool whose output format has special characters.

A value containing `|` or an embedded newline (markdown tables). A title containing `&`, `%`, `_`, `#`, `{`, `}` or JATS/HTML tags (LaTeX/BibTeX). This is not about attacks — it is about the output being valid at all.

**Caught**: `literature-review` emitted broken markdown tables for any title containing a pipe or newline. `citation-management` interpolated CrossRef titles raw, so `&` or `<i>` in a title produced a `.bib` file that fails a LaTeX build — in a repo that has a `latex-project-bootstrap` skill consuming exactly that output.

**Check**: the generated artifact actually parses/compiles in its target format, with the hostile value present.

## 8. Cross-source and cross-record identity

**Probes**: "deduplicates," "merges," "counts unique," any claim about identity across records.

The same paper from two sources where one has a DOI and the other does not. The same key appearing first in record 2, not record 1. Records identical except for punctuation or case.

**Caught**: `literature-review` keyed dedup by DOI *or* normalized title but never matched the two key spaces against each other, so an arXiv preprint and its published CrossRef record always survived as two rows — the most common duplicate shape, corrupting the PRISMA "after deduplication" count the skill exists to produce. `eda_analyzer.py` counted a JSON key as missing only for records *after* its first appearance, undercounting missingness.

**Check**: build the fixture where the two identity keys disagree, and verify the count, not just the absence of an error.

## 9. The template nobody filled in

**Probes**: every gate, every "mandatory" validator, every required-field check.

Take the skill's own bundled template, change the minimum needed to make it type-check (flip booleans, set an enum), and leave every free-text field as the shipped placeholder. This is precisely what a rushed user produces.

**Caught**: `peer-review`'s mandatory intake gate — the skill's entire safety mechanism — returned `READY_FOR_LOCAL_REVIEW` for a template whose authorization, accountable human, and retention plan were all still `<placeholder text>`, because a placeholder string is truthy. Separately, `hypothesis-generation`'s preregistration generator ran on any record at all, so its "a hypothesis is never confirmed by construction" invariant was enforced only by a validator that nothing required it to call.

**Check**: the gate blocks; and every artifact-producing script downstream of a gate actually calls it, with no bypass flag.

---

## The meta-lesson

All 17 defects of the 2026-07-26 round were reachable by running the scripts against inputs like these for about 20 minutes. None required careful source reading, and none were found by re-reading the code — several sat in code that reads perfectly well. **Run the thing against input the author did not imagine; do not review it into correctness.**

Two patterns are worth naming because they recurred across unrelated skills:

- **The guarantee is enforced in the validator but not in the artifact-producing script.** Ask, for every invariant: which code path writes the file someone else will read, and does *that* path check it?
- **The honest limitation section describes a different bug than the one present.** All 5 skills had thoughtful "Known limitations" sections. None of them mentioned any of the 17 defects. A written limitation is evidence of care, never evidence of coverage.
