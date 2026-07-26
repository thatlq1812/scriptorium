---
name: legal-citation-checker
description: Validates the FORMAT of Vietnamese legal citations (Điều/Khoản/Điểm + văn bản số hiệu, e.g. "Điều 12 Khoản 2 Điểm a, Nghị định 30/2020/NĐ-CP") against known numbering conventions, and flags the same document being cited with two different titles. Use when finalizing a legal document's citations before it goes to a client or gets filed. Do NOT use this to verify that a cited document is currently in effect (hiệu lực) — no free Vietnamese legal-document database exists for this project to query; that verification remains a human task. This checks citation syntax and internal title consistency only.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (re, json, argparse) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26) — the bundled 2-citation template passed clean after a real bug was found and fixed during testing (the regex rejected the template's own "5512/BGDĐT-GDTrH" example — mixed-case agency abbreviations like "GDTrH" are real and weren't handled by the initial uppercase-only pattern); a deliberately broken set (negative Điều, invalid Khoản/Điểm, an unrecognized văn bản số hiệu format, the same document cited under two different titles) correctly caught all 5 issues; missing citations list and malformed JSON both correctly refused (exit 2).
metadata:
  domain: legal
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from survey item 2 (outside_research/research_01_survey.md: 'Trích dẫn quy định pháp luật trong các văn bản pháp luật — tìm kiếm, trích dẫn điều, khoản, điểm... đính kèm nguồn'). The item's own note flags the real difficulty directly: 'Tự động cập nhật khi văn bản được sửa đổi, thay thế hoặc hết hiệu lực. (Maybe nhưng hơi khó vì VBPL thay đổi liên tục)' -- automatically tracking amendment/repeal status is explicitly called out by the survey respondent as hard. This skill deliberately does NOT attempt that part: no free, official Vietnamese legal-document database or API exists for this project to query (unlike CrossRef for academic DOIs used by citation-management), so asserting a hiệu lực status without a real source would be exactly the fabrication this project's citation-management skill exists to avoid. Scoped down to what IS honestly deterministic: citation format validation against known Vietnamese legal-document numbering conventions, and flagging when the same document is cited under two different titles within a set (a real, mechanically-detectable error). Full gap rationale: docs/ROADMAP.md §'Legal-cluster consolidation survey.'"
  version: 0.1.0
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

## Run

```bash
python scripts/validate_citation_format.py <citations.json>
```

Start from `assets/citations_template.json`. Every run prints a stderr reminder of the scope limit (format/consistency only, no hiệu lực verification) before results, so this can never be silently mistaken for a full legal-validity check. Exit 0 = well-formed and consistent, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Doesn't verify a document is currently in effect, amended, or repealed — no data source exists for this; see "Why this skill" above.
- Doesn't parse free-text legal citations out of a document automatically — citations must already be supplied as structured fields (dieu/khoan/diem/van_ban_so_hieu/van_ban_ten), the same design choice `lesson-plan-builder`/`legal-research-brief` make, since regex-parsing free Vietnamese legal prose reliably is not achievable without real fragility.
- Doesn't call any LLM/AI API — pure stdlib regex/structural checking.
- Doesn't check that the cited Điều/Khoản/Điểm actually says what a document claims it says — that's a human review step (or `legal-research-brief`'s job for a full brief, which at least confirms a source was declared, though not its content).

## Known limitations (v0.1.0)

- The `_SEGMENT` regex accepts any mixed-case letter sequence starting with an uppercase letter for agency abbreviations — this is permissive by design (real abbreviations vary, e.g. "GDTrH"), so it will NOT catch every possible malformed số hiệu, only ones that clearly don't fit either known pattern.
- No support yet for citations to Bộ luật (codes, e.g. Bộ luật Dân sự) which use a different numbering style than Nghị định/Thông tư/Công văn — a real gap for a future version if legal-research-brief work surfaces the need.
