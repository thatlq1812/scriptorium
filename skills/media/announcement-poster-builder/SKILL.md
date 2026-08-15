---
name: announcement-poster-builder
description: Generates a valid html-poster-composer layout.json + content.json for a Vietnamese social/administrative announcement poster -- NO zone taxonomy or x/y/w/h math required. Covers 3 shapes a non-technical fanpage manager/intern/HR person actually needs: decree/directive summary (số hiệu, ngày ban hành, nội dung chính, cơ quan ban hành), general notice/thông báo (tiêu đề, nội dung, đơn vị phát hành, thời hạn), contest/competition result (tên cuộc thi, 1-3 hạng mục kết quả, ngày công bố). Caller picks canvas "square" (1080x1080, FB/IG post) or "a4" (print) and supplies content fields only. Does NOT render pixels -- the calling agent runs the generated files through html-poster-composer's compose.py unchanged. Use for a real poster draft from specified content fast, no layout schema needed. Do NOT expect arbitrary free-form layouts -- exactly 3 fixed templates, by design.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed for this skill itself. Rendering the actual poster (a separate step, via html-poster-composer) additionally requires that skill''s own playwright/Chromium dependency. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 (2026-08-15): a direct, concrete persona/scenario probe after this session's design/webpage cluster work -- 'một người, ví dụ như giáo viên phụ trách fanpage facebook, thực tập sinh, HR nào đó... cần thiết kế poster dạng Vuông, hoặc A4, bao gồm nội dung được chỉ định, ví dụ như tóm tắt một nghị định, một thông báo, hoặc kết quả một cuộc thi... Tôi nghĩ là chưa có, và nếu có thì chưa ổn.' Investigated html-poster-composer directly and confirmed the assessment: it existed but had 2 real gaps for this exact persona -- no square canvas preset (only A1/A4/VIDEO_HD, fixed the same round, see html-poster-composer changelog_0_5_0), and no way to produce a poster without hand-authoring a zone-taxonomy layout.json, not something a non-technical fanpage manager can do. This skill is the direct answer to the 2nd gap: 3 fixed, pre-designed templates for the exact 3 content shapes thatlq1812 named, taking only content fields as input. The 40%-max-text-coverage constraint (inherited from html-poster-composer/layout_schema.py) was violated by this skill's own first hand-calculated template zone budget (forgot to include the kicker zone's own area) -- caught for real by actually running compose.py against the generated output, not just eyeballing the percentages; fixed, and a runtime self-check added to catch a future recurrence."
  version: 0.1.0
  grounding: required
  object_type: ["poster", "announcement"]
---

# announcement-poster-builder

Generates poster layout.json + content.json for 3 real Vietnamese announcement content shapes. Does not render pixels itself -- chains into `html-poster-composer`.

## Why this skill, and why this scope

thatlq1812 posed a direct, concrete test: for a Facebook-fanpage-managing teacher, an intern, or an HR person who needs a square or A4 poster summarizing a decree, a notice, or a contest result -- which skill would actually get pulled up, and would it be good enough? Investigating `html-poster-composer` directly confirmed the concern was real: that skill's zone-taxonomy `layout.json` requires design/technical literacy (percentage-based x/y/w/h zone geometry) no calling agent should assume of this persona, and it had no square preset at all (only A1/A4 print sizes and a 16:9 video frame) despite square being the actual standard size for a Facebook/Instagram feed post. The square-preset gap was fixed directly in `html-poster-composer` itself (v0.5.0, a small, clearly-justified, backward-compatible addition). This skill solves the bigger gap: a caller supplies only real content fields, no layout knowledge required.

## What this skill does

1. **`decree_summary`**: fields `so_hieu` (văn bản số hiệu), `ngay_ban_hanh`, `tieu_de`, `noi_dung_chinh`, `co_quan_ban_hanh` (all required), optional `hieu_luc_tu_ngay`.
2. **`announcement`**: fields `tieu_de`, `noi_dung`, `don_vi_phat_hanh` (all required), optional `thoi_han`.
3. **`contest_result`**: fields `ten_cuoc_thi`, `ngay_cong_bo` (required), `top_results` (required, a list of 1-3 `{hang, ten, giai_thuong}` objects -- fewer than 3 are padded with "Chưa công bố" placeholders so the fixed 3-rank layout always has valid content).

Each template shares a consistent visual family (a colored header band + kicker label + content zones + footer), pre-designed to stay under `html-poster-composer`'s real 40%-max-text-coverage constraint. Colors default to a neutral blue/white scheme, overridable via an optional top-level `colors` object (`header_band`/`kicker_text`/`background`/`title_text`/`body_text`/`footer_text`).

## Run

```bash
python scripts/build_announcement_poster.py <request.json> --out-dir <dir>
```

Writes `<dir>/layout.json` and `<dir>/content.json`. Start from `assets/decree_summary_template.json` / `announcement_template.json` / `contest_result_template.json`. `canvas` must be `"square"` or `"a4"`. Exit 0 = generated, 1 = a required field is missing/invalid, 2 = malformed input.

**Next step** (this skill does not do this itself): render the generated files through `html-poster-composer`:

```bash
python <path-to-html-poster-composer>/scripts/compose.py <dir>/layout.json <dir>/content.json -o poster.png
```

## Chains into `html-poster-composer`

This skill's whole output IS that skill's real input contract (`layout.json`/`content.json`, unchanged schema) -- same "generate valid input for a real render engine" shape as `design-system-recommender` → `landing-page-composer`.

## What this skill does NOT do

- Does not render any pixels -- produces layout.json/content.json only; rendering is `html-poster-composer`'s job, a separate step the calling agent runs.
- Does not support arbitrary/custom layouts -- exactly 3 fixed, pre-designed templates. A genuinely different content shape needs its own new template (a real, flagged future-extension point), not a workaround inside these 3.
- Does not summarize or write content for you -- "tóm tắt nội dung chính" of a real decree, or the wording of a real notice, is the caller's/calling agent's own judgment; this skill only structures and lays out content it's given.
- Does not verify the factual accuracy of any field (a wrong `so_hieu` or `ngay_ban_hanh` renders exactly as declared) -- structural/layout tool only, not a content fact-checker.
- Does not call any LLM/AI API -- pure stdlib template generation.

## Verified

All 3 bundled templates generated valid `layout.json`/`content.json` and were rendered for REAL end-to-end through `html-poster-composer`'s actual `compose.py` (shared venv's real Playwright/Chromium) -- confirmed by direct visual inspection of all 3 resulting PNGs (correct Vietnamese diacritics throughout, correct canvas aspect ratio for both `square` and `a4`, no overlapping/clipped text, no invisible-text compositing bugs). This caught a real bug in the process: this skill's own first hand-calculated zone-area budget for `decree_summary`/`announcement` forgot to include the `kicker` zone's own area, exceeding `html-poster-composer`'s real 40%-max-text-coverage limit (44.0%/43.2% vs. the 40.0% ceiling) -- caught by `compose.py`'s own downstream refusal when actually run, not just by eyeballing the numbers; fixed (35.2%/36.8%), re-verified rendering correctly, and a runtime self-check was added to `build()` so a future edit to the hardcoded template geometry can't silently reintroduce the same class of mistake. Broken-input testing: empty required fields (`ten_cuoc_thi`, `top_results[0].ten`) correctly flagged; an invalid `content_type` and an invalid `canvas` value both correctly flagged; a `top_results` list of 1 item correctly padded ranks 2-3 with "Chưa công bố"; a `top_results` list of 4 items correctly refused (max 3); malformed JSON correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Exactly 3 content-type templates -- a real, deliberate v0.1.0 scope limit matching the 3 examples thatlq1812 named, not full coverage of every possible announcement shape.
- `contest_result` is hard-capped at 3 ranks -- a contest with more real winners needs a different template (a real, flagged future-extension point, not silently truncated without disclosure -- the current behavior correctly REFUSES more than 3, it does not drop extras silently).
- The default blue/white color scheme is a reasonable general-purpose choice, not chained to `design-system-recommender`'s harvested palettes (those are commercial/SaaS-oriented product types, not a good semantic fit for civic/administrative content) -- a caller wanting a different palette uses the optional `colors` override.
- Does not chain into `ui-guideline-lookup`/`ui-style-guide-lookup` automatically -- a caller wanting to sanity-check the generated poster against real UX/accessibility guidance runs that skill separately.
- Only verified against hand-authored fixtures this session, not yet exercised against a real fanpage manager's/intern's/HR person's actual content.
