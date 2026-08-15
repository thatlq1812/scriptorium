---
name: vn-ad-compliance-checker
description: Checks a caller-declared online-ad/campaign record against Vietnam's Nghị định 342/2025/NĐ-CP (detailing the amended Luật Quảng cáo, effective 2026-02-15, currently in force) -- Điều 17's close-button/wait-time rules for closeable ads, Điều 18's 24-hour violation-removal SLA, Điều 19's record-retention/reporting/notification rules for online-ad-service businesses, and a Điều 3 special-product-category router (cosmetics, food, pharma, alcohol, and 7 more categories needing extra content clearance). Use before publishing an online/social-media ad in Vietnam, or when auditing an existing ad-service business's compliance posture. Do NOT use this to verify a special product category's substantive ad-content requirements (Điều 4-12's specific required disclosures) -- it only flags that those extra rules apply, it does not check the ad's actual content against them.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: marketing
  task_type: review-qa
  risk_tier: N3
  source: self-authored
  elicited_from: "Elicited from a real, primary-source-verified deep-research pass (references/research_10_digital_marketing_regulations/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15) -- Nghị định 342/2025/NĐ-CP's actual signed text was read directly, page by page (the government portal's own signed PDF, https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/342-ndcp.signed.pdf), not just secondary summaries; this caught and resolved a real discrepancy where an earlier-stage news report cited a 1.5-second ad-close wait time that the final effective decree text (Điều 17 khoản 3) does not carry -- the correct, in-force figure is 5 seconds for video ads, 0 for static images. A prior scouting round (docs/ROADMAP.md's Digital Marketing cluster section) confirmed neither of the 2 scouted MIT marketing-skill-pack repos (coreyhaines31/marketingskills, kostja94/marketing-skills) carries any Vietnam-specific regulatory content, so this skill is genuinely novel, not a duplicate of scouted prior art."
  version: 0.1.0
  grounding: required
  object_type: ["advertisement", "campaign"]
---

# vn-ad-compliance-checker

Checks a caller-declared online-ad record against Nghị định 342/2025/NĐ-CP's mechanically-checkable rules. Does not verify special-category substantive ad content, and is not legal advice.

## Why this skill, and why this scope

The Digital Marketing cluster's official-source research (`references/research_08_digital_marketing/research_brief.json`, `references/research_10_digital_marketing_regulations/research_brief.json`) found real, large, MIT-licensed marketing-skill-pack prior art (`coreyhaines31/marketingskills` at 44,335 real stars, `kostja94/marketing-skills` at 172 skills) already covering UTM tracking, funnel strategy, and paid-ads-by-platform -- but neither carries any Vietnam-specific regulatory-compliance content, since both are English-language, US/global-market-oriented prompt packs. Nghị định 342/2025/NĐ-CP (effective 2026-02-15, currently in force) sets real, mechanically-checkable rules for online advertising in Vietnam that no scouted repo covers. This skill is scoped to exactly the subset that's honestly deterministic from a caller-declared record -- close-button/wait-time mechanics (Điều 17), a takedown-SLA time calculation (Điều 18), and retention/reporting date arithmetic (Điều 19) -- the same "check what's actually checkable, flag what isn't" discipline `legal-citation-checker` already applies to Vietnamese legal citations.

## What this skill checks

1. **Điều 17 (closeable-ad rules)**: the close control must work with exactly one interaction and must not be fake/hard-to-identify (`close_single_interaction`, `close_icon_fake_or_ambiguous`); a static-image ad requires zero mandatory wait time, a video/moving-image ad allows a maximum of 5 seconds (`wait_time_seconds`, checked against `ad_type`); a violation-reporting mechanism must be present (`report_mechanism_present`).
2. **Điều 3 special-category router**: if `ad.product_category` is one of the 11 regulated categories (mỹ phẩm, thực phẩm, sữa/dinh dưỡng trẻ nhỏ, hóa chất diệt côn trùng/khuẩn, thiết bị y tế, khám chữa bệnh, thuốc bảo vệ thực vật/thú y/thức ăn chăn nuôi, phân bón, giống cây trồng, thuốc, đồ uống có cồn), prints a `ROUTED (not verified)` note citing the specific Điều 4-12 article -- this is a flag that extra rules apply, not a check that the ad's content actually satisfies them.
3. **Điều 18 (takedown SLA), if `takedown_request` is given**: the elapsed time between `request_received_at` and `removed_at` must not exceed 24 hours.
4. **Điều 19 (online-ad-service-business obligations), if `ad_service_business` is given**: `contact_info_notified` must be true; `retention_until` must be at least 3 years after `last_ad_display_date`; `annual_report_filed_date`, if given, must fall on or before November 25 of its year.

## Run

```bash
python scripts/validate_ad_compliance.py <ad_record.json>
```

Start from `assets/ad_record_template.json`. The `ad` key is required; `ad_service_business` and `takedown_request` are optional -- omit them if they don't apply to your situation (e.g. you're an advertiser, not an ad-service business; or there's no active takedown request to check). Exit 0 = no flags, 1 = issues found, 2 = malformed input (including a missing `ad` key). Every run prints a stderr scope-limit reminder before results.

## What this skill does NOT do

- Does not verify a special product category's *substantive* ad-content requirements (Điều 4-12's specific required disclosure text, e.g. cosmetics' mandatory ingredient/warning info) -- it only flags that Điều 4-12 applies and names the article, per the honest "route, don't verify" scope this project already applies elsewhere (`legal-citation-checker`'s Điều-existence check).
- Does not check enforcement/penalty amounts -- that's a separate decree (`Nghị định xử phạt vi phạm hành chính trong lĩnh vực quảng cáo`), not researched for this skill.
- Does not constitute legal advice -- a flagged issue or a special-category routing note is a prompt for real legal/compliance review, not a final determination.
- Does not fetch or scrape any ad platform's live data -- all inputs are caller-declared facts about the ad, same design choice `legal-citation-checker`/`contract-consistency-linter` make (structured input only, no unreliable free-text extraction).
- Does not call any LLM/AI API -- pure stdlib structural/date-arithmetic checking.
- Does not check UTM-tagging/GA4-attribution conventions -- that is a separate, not-yet-built companion capability flagged in `references/research_10_digital_marketing_regulations/research_brief.json`'s synthesis, grounded in Google's own official GA4 documentation.

## Verified

The bundled template (video ad, general category, both optional blocks present) passes clean. A deliberately broken record (fake close icon, close not single-interaction, 8-second wait on a video ad, no report mechanism, `product_category: "thuoc"` special-category routing, contact info not notified, retention 1 year short of the 3-year requirement, annual report filed after November 25, a 48-hour takedown) correctly caught all 8 numeric/structural issues plus the special-category routing note in one run. A static-image ad with a nonzero declared wait time was correctly flagged alone. A leap-year edge case (`last_ad_display_date: 2028-02-29`, 3 years later has no Feb 29) correctly computed the fallback retention floor as 2031-02-28 and passed a `retention_until` of 2031-03-01. A record missing the `ad` key, malformed JSON, and a `takedown_request` mixing a timezone-aware and a naive ISO datetime all correctly refused (exit 2 / flagged respectively).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Special-category routing (Điều 3) is presence/name-only -- it does not check any of Điều 4-12's actual required-disclosure text (e.g. mandatory warning phrases for thực phẩm bảo vệ sức khỏe). Only 2 of the 9 individual special-category articles were read in detail during this skill's grounding research (see `references/research_10_digital_marketing_regulations/research_brief.json`'s own gaps note) -- a future version should read all 9 before attempting substantive content checks.
- Điều 18's national-security carve-out ("phải ngăn chặn, gỡ bỏ kịp thời nhưng không chậm hơn 24 giờ") is enforced as the same 24-hour numeric bound as the general case -- this script cannot judge "kịp thời" (promptly) as a stricter expectation than 24 hours, only the hard ceiling.
- Only verified against hand-authored fixtures this session, not yet exercised against a real ad-service business's actual compliance record.
