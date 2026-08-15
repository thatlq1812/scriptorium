---
name: campaign-funnel-brief-validator
description: A completeness/arithmetic CHECKER, not a brief-writing tool. Validates a marketing campaign brief you (or the calling agent) have already drafted and structured as JSON, against a real, widely-corroborated 9-element convention (a measurable objective+deadline, audience, one-sentence key message, channels+each channel's role, deliverables/asset list, timeline, total budget with a channel split that must sum to the total, KPIs with metric+target+window, and mandatories). Optionally, if funnel_stages are declared, checks that each stage (awareness/consideration/conversion/loyalty -- supports both a 3-stage TOFU/MOFU/BOFU and a 4-stage +loyalty funnel) has its own objective and metric rather than reusing one campaign-wide metric. Use before a campaign brief is circulated for sign-off, to catch missing fields or budget-math errors. Do NOT use this to judge whether the objective is realistic or the creative strategy will work -- structure and arithmetic only.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: marketing
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from a deep-research pass (references/research_12_marketing_funnel_campaign/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15) covering both English and Vietnamese-language sources, per thatlq1812's direction to search Vietnamese sources too. The 9-element campaign-brief structure is corroborated across 2 independent English sources (Firstpier, Pedowitz Group). The funnel-stage-needs-its-own-metric finding is corroborated across 2 English sources (Genroe, Metricdesk) using the TOFU/MOFU/BOFU 3-stage model, then cross-checked against Vietnamese-language material (PhucTdigital, MarketingTrips) which independently uses a 4-stage model (adding a post-purchase 'trung thanh'/loyalty stage) -- reconciled by supporting both stage counts rather than hardcoding one as canonical, since both are real, valid conventions found in the wider literature (matching this project's own earlier research_08 finding, which already used a 4-stage model). Neither of the 2 scouted MIT marketing-skill-pack repos' own topic listing (docs/ROADMAP.md's Digital Marketing cluster section) named a dedicated brief-completeness checker, so this is genuinely novel, not a duplicate of scouted prior art."
  version: 0.1.0
  grounding: required
  object_type: ["campaign-brief", "funnel-stage"]
---

# campaign-funnel-brief-validator

Validates the *structure* of a marketing campaign brief and, optionally, per-funnel-stage objective/metric completeness. Does not judge whether the strategy itself is good, and does not write the brief for you.

## Why this skill, and why this scope

Digital Marketing's original research (`references/research_08_digital_marketing/research_brief.json`) found the funnel model requires a distinct objective/metric per stage, but didn't ground a specific checkable brief structure. A follow-up research pass (`references/research_12_marketing_funnel_campaign/research_brief.json`) found a real, corroborated 9-element campaign-brief convention and reconciled a real 3-stage-vs-4-stage funnel discrepancy between English and Vietnamese sources by supporting both rather than picking one. This skill checks exactly those structural/arithmetic facts, mirroring `vn-ad-compliance-checker`/`utm-campaign-governance-linter`'s validator-not-generator shape for the Marketing cluster.

## What this skill checks

1. **The 9 brief elements**: non-empty `campaign_name`; `objective.statement` (non-empty) with a real `objective.deadline` (ISO date); non-empty `audience`; a `key_message` under 200 characters (a real proxy check for "reads like one sentence, not a paragraph"); a non-empty `channels` list where every entry has `name` and `role`; a non-empty `deliverables` list; a non-empty `timeline` list where every entry has a `milestone` and a real ISO `date`; a `budget` whose `split` amounts sum exactly to `total`; a non-empty `kpis` list where every entry has `metric`/`target`/`window`; and a `mandatories` list (may be empty, but the key must be present).
2. **Funnel stages, if `funnel_stages` is declared**: each entry's `stage` must be one of `awareness`/`consideration`/`conversion`/`loyalty` (supports a 3-stage or 4-stage funnel, caller's choice), no stage repeated, and every declared stage has its own non-empty `objective` and `metric`.

## Run

```bash
python scripts/validate_campaign_brief.py <brief.json>
```

Start from `assets/campaign_brief_template.json`. `funnel_stages` is optional -- omit it entirely if the brief doesn't need per-stage breakdown yet. Exit 0 = structurally complete, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Does not write or generate the campaign brief for you -- validates a structured record you (or the calling agent) already drafted.
- Does not judge whether the objective is realistic, the audience definition is well-targeted, or the creative strategy will actually work -- pure structural/arithmetic checking, the same content/structure boundary this project's other validators draw.
- Does not extract structured fields from a free-text brief document automatically -- input must already be structured.
- Does not check `utm_campaign` tagging on any links the brief references -- that's `utm-campaign-governance-linter`'s job, a real chain worth running together once a brief's channels/links are finalized.
- Does not check Vietnam-specific advertising-content compliance -- that's `vn-ad-compliance-checker`'s job for the actual ad creative, a separate, later step in the pipeline (brief → creative → compliance check).
- Does not call any LLM/AI API -- pure stdlib structural/arithmetic checking.

## Verified

The bundled template (full 9-element brief plus a 3-stage funnel breakdown) passes clean. A deliberately broken brief (empty `campaign_name`, empty `objective.statement`, an unparseable `deadline`, an over-length `key_message`, empty `channels`/`deliverables` lists, an empty `timeline` milestone with an invalid calendar date (month 13), a `budget.split` that doesn't sum to `budget.total`, an empty `kpis` entry with a null `target`, a non-list `mandatories`, a duplicate `funnel_stages` entry, and an unrecognized funnel-stage name) correctly caught all 15 issues in one run. A brief missing every key except `campaign_name` was correctly flagged (9 issues, one per missing required key). Malformed JSON and a non-object root both correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- The key-message length check (200 characters) is a loose mechanical proxy for "reads like one sentence," not real sentence-boundary parsing -- a genuinely long single sentence would still pass, and several short sentences totaling under 200 characters would still fail to be flagged as multi-sentence.
- Timeline milestones are not checked for chronological ordering (a `timeline` entry dated before an earlier one in the list is not flagged) -- campaigns can legitimately have parallel workstreams with non-sequential milestone lists.
- `funnel_stages` uses a fixed 4-name vocabulary (`awareness`/`consideration`/`conversion`/`loyalty`) -- an organization using different stage-naming conventions (e.g. literal TOFU/MOFU/BOFU) must map to this vocabulary before running the check.
- Only verified against hand-authored fixtures this session, not yet exercised against a real marketing team's actual campaign brief.
