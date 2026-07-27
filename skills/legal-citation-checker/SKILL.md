---
name: legal-citation-checker
description: Validates the FORMAT of Vietnamese legal citations (Điều/Khoản/Điểm + văn bản số hiệu, e.g. "Điều 12 Khoản 2 Điểm a, Nghị định 30/2020/NĐ-CP") against known numbering conventions, and flags the same document being cited with two different titles. Optionally, given a --catalog from document-ai-structurer's build_catalog.py, also checks that a cited Điều number actually exists in a structured local corpus; given a --web-record from legal-web-search, also surfaces a disclosed live-source hint (what an official source page displayed, dated). Reports an explicit access_mode (no-source/user-supplied/live-source) per citation. Use when finalizing a legal document's citations before it goes to a client or gets filed. Do NOT use this to verify that a cited document is currently in effect (hiệu lực) — no free Vietnamese legal-document database exists for this project to query, and neither local corpus existence nor a live-source hint is the same claim as hiệu lực; that verification remains a human task.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (re, json, argparse) — no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26, 2026-07-27). See "Verified" section below for real test-case detail.
metadata:
  domain: legal
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from survey item 2 (outside_research/research_01_survey.md: 'Trích dẫn quy định pháp luật trong các văn bản pháp luật — tìm kiếm, trích dẫn điều, khoản, điểm... đính kèm nguồn'). The item's own note flags the real difficulty directly: 'Tự động cập nhật khi văn bản được sửa đổi, thay thế hoặc hết hiệu lực. (Maybe nhưng hơi khó vì VBPL thay đổi liên tục)' -- automatically tracking amendment/repeal status is explicitly called out by the survey respondent as hard. This skill deliberately does NOT attempt that part: no free, official Vietnamese legal-document database or API exists for this project to query (unlike CrossRef for academic DOIs used by citation-management), so asserting a hiệu lực status without a real source would be exactly the fabrication this project's citation-management skill exists to avoid. Scoped down to what IS honestly deterministic: citation format validation against known Vietnamese legal-document numbering conventions, and flagging when the same document is cited under two different titles within a set (a real, mechanically-detectable error). Full gap rationale: docs/ROADMAP.md §'Legal-cluster consolidation survey.' Owner (2026-07-27): directed wiring this skill into document-ai-structurer's new legal-article structuring/catalog capability so a cited Điều's existence, not just its format, can be checked against a real local corpus — still explicitly not a hiệu lực claim."
  version: 0.3.0
  changelog_0_3_0: "Added optional --web-record flag + explicit per-citation access_mode reporting (no-source/user-supplied/live-source), adapted from a 3-state Access-Modes pattern found independently in 3 outside LegalTech skill repos surveyed this session (claude-for-legal, awesome-legal-skills, lq-skills). --web-record points to a legal-web-search record (already disciplined by that skill's validate_search_record.py) -- when a citation's van_ban_so_hieu matches a result's document_ref, prints a disclosed live-source hint (what the source page displayed, or a disclosed js_shell/WebSearch-snippet note, dated and sourced). Never asserts hiệu lực -- exactly the same discipline legal-web-search itself already enforces, now surfaced at the citation-check step instead of staying siloed in that skill. Backward-compatible: omitting --web-record behaves exactly as v0.2.0. adapted_from note: the Access-Modes framing itself (not any code) is adapted from lq-skills' sgcite/uk-citation-verification/corporate-registry-investigation skills (outside_research/research_03_legal-repo/lq-skills, license varies per-skill in that repo, not redistributed -- only the naming/structure of the 3-state model was reused, no code or content copied)."
  changelog_0_2_0: "Added optional --catalog flag: given a catalog.json from document-ai-structurer's build_catalog.py, also checks that each citation's Điều number exists in the structured corpus for documents the catalog covers (by van_ban_so_hieu match). A document not present in the catalog is left format/consistency-checked as before, never falsely flagged as nonexistent. Backward-compatible — omitting --catalog behaves exactly as v0.1.0."
  grounding: not_applicable
  object_type: ["citation"]
---

# legal-citation-checker

Validates the *format* of Vietnamese legal citations and flags internal title inconsistency. Does not, and cannot, verify a document's real-world hiệu lực status.

## Why this skill, and why this scope

Survey item 2 (`outside_research/research_01_survey.md`) asked for citation lookup with automatic hiệu lực (in-effect) status tracking — but the survey respondent's own note flags this as genuinely hard: *"Tự động cập nhật khi văn bản được sửa đổi, thay thế hoặc hết hiệu lực... hơi khó vì VBPL thay đổi liên tục"* (auto-updating for amendments/repeals is hard because Vietnamese legal documents change constantly). This project has no free, official Vietnamese legal-document API to query for that status — unlike `citation-management`'s use of CrossRef/PubMed/arXiv for academic identifiers. Rather than fabricate a hiệu lực check without a real data source (which would produce exactly the kind of confidently-wrong output this project's grounding principles exist to prevent), this skill is deliberately scoped to what's honestly checkable without external data: **citation format** and **internal title consistency**.

## What this skill checks

1. **Điều/Khoản/Điểm structure**: `dieu` must be a positive integer; `khoan` (if present) must be a positive integer; `diem` (if present) must be a single lowercase letter (`a`, `b`, `c`, ...).
2. **Văn bản số hiệu format**: must match one of the two real Vietnamese legal-document numbering conventions — with a year (`<số>/<năm>/<loại>-<cơ quan>`, e.g. `30/2020/NĐ-CP`) or without one, a công văn/directive style (`<số>/<cơ quan>-<đơn vị>`, e.g. `5512/BGDĐT-GDTrH` — note the mixed-case agency abbreviation, a real convention, not a typo).
3. **Title consistency**: if the same `van_ban_so_hieu` appears in multiple citations, every occurrence must use the same `van_ban_ten` (title) — catches the real error of citing "30/2020/NĐ-CP" once correctly and once under the wrong document's title.
4. **Access mode, reported per citation** (v0.3.0): `no-source` (default, format-only), `user-supplied` (a `--catalog` corpus covers this document), `live-source` (a `--web-record` result matches this document). A citation can carry more than one mode at once. This is a disclosure label, not a quality score — `no-source` is not "worse," it's simply honest about what wasn't checked.

## Run

```bash
python scripts/validate_citation_format.py <citations.json> [--catalog catalog.json] [--web-record record.json]
```

Start from `assets/citations_template.json`. Every run prints a stderr reminder of the scope limit (format/consistency, plus Điều-existence when `--catalog` is given, plus disclosed live-source hints when `--web-record` is given — never hiệu lực verification) before results, so this can never be silently mistaken for a full legal-validity check. Exit 0 = well-formed and consistent (and, with `--catalog`, every cited Điều exists in the corpus for documents it covers), 1 = issues found, 2 = malformed input.

`--catalog catalog.json` points to output from `document-ai-structurer`'s `build_catalog.py` (see that skill's "Multi-document catalog" section). This adds one more check per citation: if the cited `van_ban_so_hieu` is a document the catalog covers, the cited `dieu` number must actually appear in that document's structured corpus. A citation to a document the catalog doesn't cover is left alone (not flagged) — the catalog isn't assumed complete.

`--web-record record.json` points to a search record produced by `legal-web-search` and already run through that skill's own `validate_search_record.py` (this script does not re-check search-record discipline itself, only reads `document_ref`/`as_displayed_status`/`js_shell_detected`/`snippet_note`). When a citation's `van_ban_so_hieu` matches a result's `document_ref`, prints a `live-source hint` to stderr: what the source page displayed (or a disclosed WebSearch-summary snippet if the page was JS-rendered), plus the source URL and access date. This is always a disclosed hint for a human to read, never an asserted hiệu lực fact — same discipline `legal-web-search` already enforces on itself, applied here at the point where a citation is actually being checked.

## What this skill does NOT do

- Doesn't verify a document is currently in effect, amended, or repealed — no data source exists for this; see "Why this skill" above. **Điều-existence in a local corpus (the `--catalog` check) is not a hiệu lực claim either** — a real Điều number that was repealed last year still "exists" if the corpus that structured it is out of date.
- Doesn't parse free-text legal citations out of a document automatically — citations must already be supplied as structured fields (dieu/khoan/diem/van_ban_so_hieu/van_ban_ten), the same design choice `lesson-plan-builder`/`legal-research-brief` make, since regex-parsing free Vietnamese legal prose reliably is not achievable without real fragility.
- Doesn't call any LLM/AI API — pure stdlib regex/structural checking.
- Doesn't check that the cited Điều/Khoản/Điểm actually says what a document claims it says — that's a human review step (or `legal-research-brief`'s job for a full brief, which at least confirms a source was declared, though not its content).

## Verified

The bundled 2-citation template passed clean after a real bug was found and fixed during testing (the regex rejected the template's own "5512/BGDĐT-GDTrH" example — mixed-case agency abbreviations like "GDTrH" are real and weren't handled by the initial uppercase-only pattern); a deliberately broken set (negative Điều, invalid Khoản/Điểm, an unrecognized văn bản số hiệu format, the same document cited under two different titles) correctly caught all 5 issues; missing citations list and malformed JSON both correctly refused (exit 2).

`--catalog` mode verified real against `document-ai-structurer`'s `build_catalog.py` output — a citation to a real, existing Điều passed, a citation to a nonexistent Điều number was correctly flagged, a citation to a document not covered by the catalog was correctly left unflagged (not a false positive), malformed/missing catalog file both correctly refused, and the pre-existing bundled-template regression check still passes with no catalog given.

`--web-record` mode (v0.3.0) verified real against `legal-web-search`'s actual `assets/verified_real_example.json` (a real WebSearch/WebFetch result for Nghị định 30/2020/NĐ-CP) — the matching citation correctly reported `access_mode=no-source,live-source` plus a live-source hint citing the real source URL/date; the non-matching citation stayed `no-source` only (no false hint). Also verified the `js_shell_detected`/`snippet_note` hint path with a synthetic record (correctly labeled "WebSearch-summary snippet", not presented as a direct quote), a malformed web-record (missing `results`, correctly refused exit 2), and a combined `--catalog` + `--web-record` run (a citation correctly showed all 3 access modes at once). Running with neither flag regression-checked unchanged from v0.2.0 behavior.

## Known limitations (v0.3.0)

- The `_SEGMENT` regex accepts any mixed-case letter sequence starting with an uppercase letter for agency abbreviations — this is permissive by design (real abbreviations vary, e.g. "GDTrH"), so it will NOT catch every possible malformed số hiệu, only ones that clearly don't fit either known pattern.
- No support yet for citations to Bộ luật (codes, e.g. Bộ luật Dân sự) which use a different numbering style than Nghị định/Thông tư/Công văn — a real gap for a future version if legal-research-brief work surfaces the need.
- `--catalog` matches documents by exact `van_ban_so_hieu` string equality only — a citation and a `doc_meta.json` that both refer to the same real document but format the số hiệu slightly differently (extra whitespace, different case) will not match, and the citation will silently fall back to format-only checking rather than being flagged as unmatched. Not yet fuzzy or case-insensitive.
- `--web-record` matches by the same exact-string rule on `van_ban_so_hieu`/`document_ref` — same fuzzy-matching gap as `--catalog`.
- `--web-record` does not itself re-validate the record's search discipline (allowlisted domains, dated access, contradiction surfacing) — it trusts that `legal-web-search`'s own `validate_search_record.py` already ran on the file. A caller passing a record that was never validated will still get hints printed from it; this script only guards against structurally malformed input, not undisciplined search records.
- Only verified against a small synthetic 2-document corpus and 1 real Nghị định 30/2020 web-search record this session — not yet exercised on a real multi-document legal corpus, a catalog built from real Docling OCR output, or a batch of real (not synthetic) web-search records across many documents.
