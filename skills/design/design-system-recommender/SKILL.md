---
name: design-system-recommender
description: A curated LOOKUP tool, never a generator. Given a declared product/industry type (e.g. "SaaS (General)", "E-commerce", "Portfolio") or free-text keywords, deterministically returns a real, curated design system -- a 16-token semantic color palette (primary/secondary/accent/background/foreground/card/muted/border/destructive/ring, each with its "on-X" contrast pairing), a matched Google Fonts heading/body pairing, and a recommended landing-page section order -- from a bundled reference dataset of 192 product types, 74 font pairings, and 34 landing patterns. Use at the start of a web/UI design task to get a real, professionally-curated starting point instead of guessing colors/fonts from scratch. Chains directly into `landing-page-composer` (its output feeds that skill's `design_system` input). Do NOT use this expecting AI-generated or brand-new design suggestions -- every result traces to a real, pre-existing curated entry, never invented.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: design
  task_type: research
  risk_tier: N1
  source: harvested
  elicited_from: "Harvested from a real, actively-maintained repository (nextlevelbuilder/ui-ux-pro-max-skill, verified 116,839 stars via `gh api`, MIT license read directly at the root and confirmed with no nested override) -- full provenance, exact source commit, and what was/wasn't adapted documented in references/PROVENANCE.md. thatlq1812 directed this harvest directly after asking to read the repo and confirming it was worth adapting from ('làm luôn nhỉ'), per this project's scout-harvester -> license-compliance-check -> skill-creator pipeline. Upgrades Scriptorium's `design` cluster (previously brand-identity-linter/light-logo-arranger/personal-style-library/slogan-copy-linter, all validators with no curated-content lookup capability) with real, professionally-curated reference data rather than this project inventing color/font recommendations from scratch, which this project's own principles explicitly warn against (SkillsBench: self-generated content underperforms curated content)."
  version: 0.1.0
  grounding: required
  object_type: ["color-palette", "font-pairing", "design-system"]
---

# design-system-recommender

Looks up a real, curated design system for a declared product type. Never generates or invents a new one.

## Why this skill, and why this scope

thatlq1812 asked to read `nextlevelbuilder/ui-ux-pro-max-skill` (a real, verified 116,839-star repo) and, finding it genuinely valuable, directed harvesting from it directly rather than reinventing color-theory/typography-pairing knowledge from scratch -- exactly the kind of real, curated prior art this project's own principles prefer over self-generated content (SkillsBench: curated skills +16.2pp average pass rate vs. self-generated). This skill is a thin, deterministic lookup layer over that harvested data (`references/design_systems.json`/`font_pairings.json`/`landing_patterns.json`, full provenance in `references/PROVENANCE.md`) -- it adds no AI judgment, only exact-match and keyword-overlap retrieval.

## What this skill does

1. **Exact lookup** (`--product-type "SaaS (General)"`): returns the curated color-token palette, font pairing, landing pattern, and key considerations for that exact product type. Use `--list-product-types` to see all 192 recognized values.
2. **Fuzzy lookup** (`--keywords "saas b2b cloud software"`): scores every product type by keyword overlap and returns the best match, with the matched product type and overlap count printed to stderr so you know what was actually matched, not just trusting a silent guess.
3. **Font pairing selection**: among the 74 bundled pairings, picks the one whose mood keywords/best-for description best overlaps with the matched product type's own keywords -- deterministic scoring, not AI judgment.

## Run

```bash
python scripts/recommend_design_system.py --product-type "SaaS (General)"
python scripts/recommend_design_system.py --keywords "ecommerce shop retail"
python scripts/recommend_design_system.py --list-product-types
```

`-o/--output <path>` writes the result JSON to a file instead of stdout -- convenient for piping directly into `landing-page-composer`'s `design_system` input. Exit 0 = match found, 1 = no match, 2 = malformed input/missing args.

## Chains into `landing-page-composer`

The result's `color_tokens` + `font_pairing` map directly onto `landing-page-composer`'s `design_system` input shape -- run this skill first, feed its output (or the relevant fields) into that skill's input JSON. See that skill's own "Chains from `design-system-recommender`" note for the exact field mapping.

## What this skill does NOT do

- Does not generate a new color palette or font pairing -- every result is a real, pre-existing curated entry from the bundled dataset, never invented or AI-generated.
- Does not verify WCAG contrast for a specific real use (e.g. a specific text size/weight against the returned background) beyond what the source dataset itself already curated for the general token pairing -- the source's own accessibility notes (per-style contrast risk) are documented in the harvested `styles.csv` but not adapted into this skill's dataset (see `references/PROVENANCE.md`'s "deliberately not adapted" list).
- Does not adapt the palette to a specific real brand's existing logo/photography -- it's a curated starting point, not a brand audit.
- Does not track freshness against the upstream source automatically -- a real, documented gap (see `references/PROVENANCE.md`'s "Freshness" section).
- Does not call any LLM/AI API -- pure stdlib lookup/scoring.

## Verified

Data integrity verified during harvest/conversion: all 192 `products.csv` product types have an exact 1:1 match in `colors.csv` (no orphans either direction); all 3,072 individual color-token values (192 entries × 16 tokens) pass a `#RRGGBB`-or-valid-`rgba()` format check. Script-tested for real: an exact `--product-type` match returns the full expected structure; a `--keywords` fuzzy match correctly identifies and discloses the matched product type + overlap score; a nonexistent `--product-type` and a zero-overlap `--keywords` query both correctly refuse (exit 1); missing all 3 required-choice arguments correctly refuses (exit 2); `--list-product-types` correctly prints all 192 entries.

## Known limitations (v0.1.0, not yet through official quality-eval)

- Keyword matching is exact-token-overlap only (case-insensitive), no stemming/synonym expansion -- "e-commerce" and "ecommerce" are treated as different tokens unless both happen to appear in a product's own keyword list (most do, since the source data anticipated common variants, but not guaranteed for every entry).
- Font-pairing selection score can tie across multiple pairings; the first one encountered in file order wins with no documented tie-breaking rule beyond that.
- Only the product-type → design-system half of the source repo's data was adapted (see `references/PROVENANCE.md`) -- `styles.csv`'s 88 detailed visual styles and `ui-reasoning.csv`'s conditional decision rules remain unharvested, flagged as real future-extension candidates, not silently dropped.
- Only verified against the full bundled dataset's own internal consistency this session, not yet exercised as part of a real end-to-end design task by a human designer.
