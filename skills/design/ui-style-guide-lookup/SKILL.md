---
name: ui-style-guide-lookup
description: A curated LOOKUP tool, never a generator. Given a UI visual-style name (e.g. "glassmorphism", "neumorphism", "brutalism", "bento-grid-showcase") or free-text keywords, deterministically returns real CSS implementation guidance -- colors, effects/animation timing, an implementation checklist, CSS custom-property variables, accessibility risk level, framework compatibility, and explicit "best for" / "do not use for" guidance -- from a bundled reference of 88 curated styles. Use when deciding which visual style fits a project and need real, specific CSS values instead of guessing. Companion to `design-system-recommender` (that skill recommends a style category per product type; this skill gives the actual CSS implementation detail for a chosen style). Do NOT use this expecting AI-generated or brand-new style ideas -- every result is a real, pre-existing curated entry.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: design
  task_type: research
  risk_tier: N1
  source: harvested
  elicited_from: "Harvested from the same source as design-system-recommender (nextlevelbuilder/ui-ux-pro-max-skill, verified 116,839 stars via gh api, MIT, full provenance already documented in that skill's references/PROVENANCE.md, same source commit a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5) -- this skill adapts styles.csv (88 rows), deliberately left unharvested when design-system-recommender/landing-page-composer first shipped. thatlq1812 pushed back on scoping the harvest to just 2 skills/1 webpage-domain skill ('cả cái repo đó bạn trích ra được mỗi 2 skill... cần rộng hơn'), directing a broader harvest of the remaining real, high-quality data this session already had cloned and inspected."
  version: 0.1.0
  grounding: required
  object_type: ["ui-style", "css-implementation"]
---

# ui-style-guide-lookup

Looks up a real, curated UI style's CSS implementation detail. Never generates or invents a new style.

## Why this skill, and why this scope

`design-system-recommender`'s harvest deliberately left `styles.csv` (88 detailed visual-style definitions) unharvested, flagged in its own `PROVENANCE.md` as "a real, valuable dataset, deliberately left for a possible future `ui-style-guide-lookup` skill." thatlq1812 asked for that broader harvest directly after seeing only 2 skills shipped from a repo this rich. This skill is that follow-through: a second, focused lookup over the same source's style-implementation data, distinct from `design-system-recommender`'s product-type → color/font recommendation.

## What this skill does

1. **Exact lookup** (`--style-id glassmorphism`): returns the full curated entry. Use `--list-styles` to see all 88 `style_id` + `style_category` pairs.
2. **Fuzzy lookup** (`--keywords "soft rounded pastel"`): scores every style by keyword overlap, returns the best match with the match score disclosed to stderr.
3. Each result includes: primary/secondary color guidance, effects/animation timing, light/dark-mode support, an `accessibility` risk note (e.g. "risk:high|requires:contrast-text-4.5,keyboard,visible-focus,reduced-motion"), framework compatibility, complexity, a real implementation checklist, and CSS custom-property variable names.

## Run

```bash
python scripts/lookup_style.py --style-id glassmorphism
python scripts/lookup_style.py --keywords "soft rounded pastel"
python scripts/lookup_style.py --list-styles
```

`-o/--output <path>` writes the result JSON to a file. Exit 0 = match found, 1 = no match, 2 = malformed input/missing args.

## What this skill does NOT do

- Does not generate a new style or CSS -- every result is a real, pre-existing curated entry.
- Does not verify WCAG contrast for a specific real color combination -- the `accessibility` field is the source dataset's own risk classification, a starting signal, not a pass/fail audit.
- Does not apply the style to actual page content -- pair with `landing-page-composer`/`design-system-recommender` for that; this skill only supplies the reference detail.
- Does not call any LLM/AI API -- pure stdlib lookup/scoring.

## Verified

Data integrity verified during harvest: all 88 styles have a non-empty `style_id`. Script-tested for real: exact `--style-id` lookup returns the full expected structure; `--keywords` fuzzy match discloses the matched style + overlap score; a nonexistent `--style-id` and missing-args case both correctly refuse (exit 1 / exit 2); `--list-styles` correctly prints all 88 entries.

## Known limitations (v0.1.0, not yet through official quality-eval)

- Keyword matching is exact-token-overlap only (case-insensitive), no stemming/synonym expansion.
- Does not cross-reference against `design-system-recommender`'s product-type recommendations automatically -- the calling agent chains the two manually (look up the recommended style category from that skill, then look up its CSS detail here).
- Only verified against the full bundled dataset's own internal consistency this session, not yet exercised as part of a real design task.
