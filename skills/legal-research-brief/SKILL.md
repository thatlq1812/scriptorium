---
name: legal-research-brief
description: Validates that a structured legal research brief (legal question → verified facts → statutory grounds → application analysis → alternative interpretations → risk evaluation) grounds every factual/statutory claim in a caller-supplied source — catching a fabricated or mistyped citation before it reaches a client or court filing. Use after drafting a legal brief/memo to verify every claim traces to a real, declared source. Do NOT use this to search the web or a legal database for sources (it has none — sources must already be supplied); do NOT use it to judge whether the legal analysis itself is correct — it validates grounding and structure only.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26) — a real valid brief (2 sources, all 3 grounded sections correctly cited) passed clean and rendered correctly to Markdown with source labels inlined; a deliberately broken brief (a fabricated source id, a missing citation on a grounded claim, a missing required field) correctly caught all 3 errors; duplicate source id, empty sources list, and malformed brief JSON all correctly refused (exit 2).
metadata:
  domain: legal
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "The 7-section output schema (cau_hoi_chinh/su_kien_da_xac_minh/thieu_sot_gia_dinh/can_cu_phap_ly/phan_tich_ap_dung/quan_diem_trai_chieu/danh_gia_rui_ro) is elicited from outside_research/research_01_result_01.md's 'Output Schema Component' table, itself grounded in a description of real Vietnamese legal-opinion practice (tra cứu và lập ý kiến pháp lý). Items 1 and 10 of the real practitioner survey (outside_research/research_01_survey.md: 'Nghiên cứu pháp lý ban đầu', 'Tóm tắt văn bản pháp luật') both carry the note 'Dựa theo nguồn 100%, không tự generate thông tin mới' (base 100% on source, never self-generate information) -- this is the exact principle this skill's validator enforces mechanically: every factual/statutory claim must cite a real, caller-declared source, and a citation to a nonexistent source id is a hard error. Same discipline already applied in this project's citation-management skill ('why not use an LLM to write the BibTeX'), extended here to legal research specifically because Stanford RegLab/HAI's 'Hallucination-Free?' study (cited in docs/specs/STRATEGY_SPEC.md §5.2) found even purpose-built legal-AI tools hallucinate 17-33% of the time."
  version: 0.1.0
  grounding: required
  object_type: ["legal-brief"]
---

# legal-research-brief

Validates that a structured legal research brief grounds every factual/statutory claim in a real, caller-supplied source. Never searches for sources itself — this is a grounding checker, not a research tool.

## Why this skill, and why this scope

Both survey items this skill was elicited from (`outside_research/research_01_survey.md`, items 1 and 10) carry the same handwritten note: *"Dựa theo nguồn 100%, không tự generate thông tin mới"* — base 100% on source, never self-generate information. That is the single most important requirement for this skill, and it's the same discipline `citation-management` already applies to academic citations, now extended to legal research. The stakes are real: Stanford RegLab/HAI's "Hallucination-Free?" study found Lexis+ AI hallucinates ~17% of the time and Westlaw AI-Assisted Research ~33%, even as purpose-built legal tools (`docs/specs/STRATEGY_SPEC.md` §5.2) — and *Mata v. Avianca* resulted in a real Rule 11 sanction for fabricated case citations.

This skill does not do the research itself (no web search, no legal database query — it has neither). It assumes a human or the calling agent has already gathered source material and drafted a brief; this skill's only job is to mechanically verify that every claim in the "grounded" sections (verified facts, statutory grounds, application analysis) actually cites one of the declared sources — and that the cited source id isn't a fabrication.

## The 7-section structure this skill encodes

Elicited from `outside_research/research_01_result_01.md`'s legal-opinion output schema table:

| Section | Grounding required? |
| --- | --- |
| Câu hỏi pháp lý chính (the core legal question) | No — framing |
| Sự kiện đã xác minh (verified facts) | **Yes** — every fact must cite a source |
| Thiếu sót/giả định (gaps and assumptions) | No — analytical note about what's missing |
| Căn cứ pháp lý (statutory grounds) | **Yes** — every legal ground must cite a source |
| Phân tích áp dụng (application analysis) | **Yes** — every application-of-law statement must cite a source |
| Quan điểm trái chiều (alternative interpretations) | No — analytical/strategic note |
| Đánh giá rủi ro (risk evaluation) | No — a judgment call, not a factual claim |

## Run

```bash
python scripts/validate_legal_brief.py <sources.json> <brief.json> [--render brief.md]
```

Start from `assets/sources_template.json` (declare every source you're allowed to cite — a document, an email, a statute excerpt) and `assets/legal_brief_template.json`. Exit 0 = every grounded claim traces to a real declared source, 1 = errors found (each naming the exact section/index and reason), 2 = malformed input. `--render` only writes when validation passes.

## What this skill does NOT do

- Doesn't search the web, a legal database, or any external source — it has zero network access; sources must already be supplied by a human or another process.
- Doesn't verify that a cited source's *content* actually supports the claim made about it (e.g. that "Điều 12 quy định X" is an accurate paraphrase of what Điều 12 actually says) — it only verifies the citation points to a *declared* source, not that the characterization is *correct*. That remains a human review step.
- Doesn't verify a statute is currently in effect (hiệu lực status) — that's the open gap flagged for `legal-citation-checker` (`docs/ROADMAP.md`).
- Doesn't call any LLM/AI API — pure stdlib structural/reference validation.
- Doesn't render the final client-facing document format — delegate to `office-doc-creator` once the brief passes validation.

## Known limitations (v0.1.0)

- Citation checking is purely by source **id**, not by content — a claim that cites a real source id but actually misrepresents that source's content will still pass. A human must still read the underlying source to confirm the characterization is accurate.
- No cross-check between `phan_tich_ap_dung` and `can_cu_phap_ly` (e.g. verifying that an application-analysis item's cited statute was itself declared as a statutory ground) — each grounded section is checked independently against the full source list, not against each other.
