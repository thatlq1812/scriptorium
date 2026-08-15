---
name: ui-guideline-lookup
description: A curated REFERENCE lookup, not an automated code checker. Given a category (Accessibility/Navigation/Forms/Touch/Performance/...), platform (Web, "iOS/Android/React Native", All, Mobile, VisionOS), severity, and/or free-text keywords, deterministically returns real UI/UX Do/Don't guidance with concrete code examples -- 151 curated entries spanning both WEB interfaces (119 entries: headings, forms, performance, typography) and MOBILE/APP interfaces (32 entries: touch-target sizing, gesture conflicts, safe areas, reduced motion). This is the deliberately broader companion to `landing-page-composer` -- reviewing ANY UI decision (not just assembling a marketing landing page). Use before/during any web or app UI work to check a decision against a real, curated guideline instead of guessing. Do NOT use this expecting it to scan your actual code and find violations automatically -- it returns relevant reference guidance for a human or agent to apply during review.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: webpage
  task_type: review-qa
  risk_tier: N1
  source: harvested
  elicited_from: "Harvested from the same source as design-system-recommender/ui-style-guide-lookup/ui-icon-recommender (nextlevelbuilder/ui-ux-pro-max-skill, verified 116,839 stars via gh api, MIT, same source commit a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5) -- adapts and merges ux-guidelines.csv (119 rows, Web-oriented) with app-interface.csv (32 rows, iOS/Android/React Native-oriented) into one filterable reference. thatlq1812 directly pushed back on the initial harvest ('cả cái repo đó bạn trích ra được mỗi 2 skill, và chỉ 1 cái cho webpage nhỉ... cần rộng hơn, không chỉ landing page ấy') -- this skill is the direct answer: the webpage domain's 2nd skill, deliberately not another page-assembly tool but a UI-review reference spanning both web and mobile/app, the broadest single dataset in the source repo not yet harvested at the time of that feedback."
  version: 0.1.0
  grounding: required
  object_type: ["ui-guideline", "accessibility-rule"]
---

# ui-guideline-lookup

Looks up real, curated UI/UX Do/Don't guidance by category/platform/severity/keyword. A reference tool, not an automated checker.

## Why this skill, and why this scope

thatlq1812 reviewed the first harvest round (2 skills: `design-system-recommender`, `landing-page-composer`) and pushed back directly: only 1 skill for the new `webpage` domain, and it only covers landing pages. This skill is the deliberate answer -- not another page-assembly tool, but a genuinely different capability: a curated Do/Don't reference spanning BOTH web UI (119 real entries: headings, forms, performance, typography, navigation) AND mobile/app UI (32 real entries: touch-target sizing per platform, gesture conflicts, safe-area insets, reduced-motion handling) -- exactly the "broader than landing pages" gap that feedback named.

## What this skill does

1. **Filtered lookup**: any combination of `--category`, `--platform`, `--severity`, `--keywords` narrows the 151-entry reference. `--list-categories` (24 real categories) and `--list-platforms` (`All`/`Mobile`/`VisionOS`/`Web`/`iOS/Android/React Native`) show the real recognized values.
2. Every result includes: `issue` name, `platform`, `description`, `do`/`dont` guidance, `severity` (Critical/High/Medium/Low), and `source_dataset` (which of the 2 harvested source files it came from).

## Run

```bash
python scripts/lookup_guideline.py --category Accessibility --platform Web
python scripts/lookup_guideline.py --severity Critical --platform "iOS/Android/React Native"
python scripts/lookup_guideline.py --keywords "touch target size"
python scripts/lookup_guideline.py --list-categories
python scripts/lookup_guideline.py --list-platforms
```

`-o/--output <path>` writes the result JSON to a file. Exit 0 = at least one match, 1 = no match, 2 = malformed input (no filter given).

## What this skill does NOT do

- Does not scan or analyze your actual HTML/app code to detect violations -- it's a reference lookup; applying the guidance to a real review is a human/calling-agent task.
- Does not generate new guidance -- every entry is a real, pre-existing curated row from the 2 harvested source datasets.
- Does not resolve conflicts between web and mobile guidance for a cross-platform app -- both are returned, filtering by `--platform` is the caller's responsibility.
- Does not call any LLM/AI API -- pure stdlib filtering.

## Verified

Data integrity verified during harvest: 151 entries loaded cleanly (119 web + 32 app), 5 distinct real platform values, 4 distinct real severity values (Critical/High/Medium/Low), 24 distinct real categories. Script-tested for real: category+platform combined filter returns correct results (10 matches for Accessibility+Web); severity+platform filter returns correct results (7 Critical entries for iOS/Android/React Native); keyword filter matches on issue/description text; `--list-categories`/`--list-platforms` print real values; a filter combination matching nothing correctly refuses (exit 1); no filter given correctly refuses (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Keyword matching is a simple whitespace-tokenized overlap against `issue`+`description` text only, no stemming/synonym expansion, no matching against the `do`/`dont`/code-example fields.
- `--category`/`--platform` require an exact (case-insensitive) match against the real recognized values -- no fuzzy category matching.
- Does not de-duplicate near-identical entries across the 2 source datasets (e.g. an Accessibility guideline that conceptually applies to both web and app is 2 separate entries, one per platform, not merged).
- Only verified against the full bundled dataset's own internal consistency this session, not yet exercised as part of a real UI review by a human or agent.
