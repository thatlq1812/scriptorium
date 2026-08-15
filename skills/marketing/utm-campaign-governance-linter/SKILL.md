---
name: utm-campaign-governance-linter
description: A UTM parameter LINTER grounded directly in Google's own official GA4 documentation (support.google.com), not a 3rd-party blog. Checks a set of caller-declared campaign links for lowercase-only UTM values (GA4 treats them as case-sensitive), no spaces (use underscores/hyphens), all 3 required parameters (utm_source/utm_medium/utm_campaign) present on every external link, NO UTM parameters on internal links (tagging an internal link overwrites session-source data and corrupts attribution -- official GA4 guidance), and optionally checks utm_source/utm_medium values against a caller-declared "UTM playbook" of approved values. Use before a campaign's tracking links go live, to catch the exact class of tagging mistake that causes GA4 sessions to fall into "Unassigned". Do NOT use this to verify a link actually resolves or to query GA4 itself -- pure local structural linting.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, re, urllib.parse) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: marketing
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited directly from Google's own official GA4 documentation (references/research_10_digital_marketing_regulations/research_brief.json findings S4/S5, support.google.com's 'Default channel group' and 'URL builders' pages) -- not a 3rd-party blog, upgrading research_08's original UTM-governance finding (which cited only secondary sources) to primary-source grounding, the same discipline vn-ad-compliance-checker applied to Nghị định 342/2025. Flagged in research_10's own synthesis as 'available as a secondary/companion capability if built later' after vn-ad-compliance-checker shipped first as the stronger initial flagship -- this is that companion, built once thatlq1812 directed completing the cluster rather than stopping at one skill."
  version: 0.1.0
  grounding: required
  object_type: ["campaign-link", "utm-parameter"]
---

# utm-campaign-governance-linter

Lints campaign-link UTM parameters against GA4's own official documentation. Does not verify a link resolves, and does not query GA4 itself.

## Why this skill, and why this scope

Digital Marketing's original research (`references/research_08_digital_marketing/research_brief.json`) found UTM-tagging consistency directly determines GA4 attribution accuracy, but grounded that finding in secondary blog sources. A follow-up pass (`references/research_10_digital_marketing_regulations/research_brief.json`, findings S4/S5) went to Google's own official documentation directly and confirmed the same finding from the primary source, plus the specific mechanical rules a linter can actually check: lowercase-only values, no spaces, and the "don't tag internal links" rule (each corroborated directly from `support.google.com`, not inferred). This skill checks exactly those mechanical rules.

## What this skill checks

1. **Case/format, every UTM parameter on an external link**: value must be all-lowercase; value must not contain a space (raw or `%20`) -- use underscores/hyphens.
2. **Required parameters, external links only**: `utm_source`, `utm_medium`, `utm_campaign` must all be present -- a link missing any of these is exactly what falls into GA4's "Unassigned" default channel group.
3. **No UTM parameters, internal links**: a link with `is_internal: true` must carry zero `utm_*` query parameters -- GA4's own guidance is that tagging an internal link overwrites the original session's source data.
4. **Optional playbook check**: if `utm_playbook.approved_sources`/`approved_mediums` is given, each external link's `utm_source`/`utm_medium` must appear in the corresponding approved list.

## Run

```bash
python scripts/validate_utm_links.py <links_record.json>
```

Start from `assets/links_template.json`. `utm_playbook` is optional -- omit it to skip the approved-value check while still getting the lowercase/space/required-parameter/no-internal-tagging checks. Exit 0 = no flags, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Does not verify a link actually resolves (no HTTP request of any kind -- zero network calls).
- Does not query GA4 itself to confirm real-world attribution results -- it lints the URL's declared parameters against GA4's documented rules, it doesn't read your actual GA4 property.
- Does not generate UTM-tagged URLs for you -- it validates links you (or the calling agent) already built.
- Does not check `utm_term`/`utm_content` for required-presence (only `utm_source`/`utm_medium`/`utm_campaign` are required per GA4's own documentation) -- but if `utm_term`/`utm_content` are present, they're still checked for lowercase/no-space like any other UTM parameter.
- Does not call any LLM/AI API -- pure stdlib URL parsing and structural checking.

## Verified

The bundled template (1 correctly-tagged external link, 1 correctly-untagged internal link) passes clean. A deliberately broken record (mixed-case `utm_source`, a `utm_medium` value with both a case issue and an embedded space, a source/medium not in the declared playbook, a second external link missing its required `utm_campaign`, an internal link carrying all 3 UTM parameters, and a link with a non-boolean `is_internal`) correctly caught all 9 issues in one run. An empty `links: []` list and a record missing the `links` key were both correctly refused/flagged (the former as a flagged issue since a governance run checking zero links isn't meaningful, the latter as malformed input). Running with no `utm_playbook` given correctly skipped the approved-value check while still catching a lowercase violation. Malformed JSON correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Only checks the first value of a repeated query parameter (e.g. `?utm_source=a&utm_source=b`) -- a repeated UTM parameter is itself a real tagging bug this version does not separately flag.
- The approved-value playbook check is exact-string-match only, case-sensitive against the already-lowercase-checked value -- no fuzzy matching for near-duplicate source names (e.g. "fb" vs "facebook" would both need to be explicitly listed).
- Does not check `utm_campaign` values against any naming-convention pattern (e.g. a required `<quarter>_<product>` shape) -- only presence/case/space, since no single authoritative campaign-naming pattern was found to be universal across organizations.
- Only verified against hand-authored fixtures this session, not yet exercised against a real campaign's actual link set.
