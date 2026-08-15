# Provenance

`design_systems.json` (192 entries), `font_pairings.json` (74 entries), and `landing_patterns.json` (34 entries) are adapted from real, curated reference data harvested from `nextlevelbuilder/ui-ux-pro-max-skill` (MIT License, Copyright (c) 2024 Next Level Builder), a real, actively-maintained repository verified via `gh api` at **116,839 stars** as of 2026-08-15 (not a blog-inflated figure).

- Source repo: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Source commit: `a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5`
- Source files: `.claude/skills/ui-ux-pro-max/data/colors.csv`, `products.csv`, `typography.csv`, `landing.csv`
- License: MIT (root `LICENSE` file read directly, no nested override found at the `.claude/skills/ui-ux-pro-max/` level — checked per this project's `license-compliance-check` discipline of reading the license at the exact folder level being harvested, not just the repo root)
- Classification: **SAFE** — permissive license, adapt/harvest allowed with attribution

## What was adapted vs. dropped

Adapted (converted from CSV to JSON, column names normalized to snake_case, re-joined by `Product Type`):
- `colors.csv` → each row's 16-token semantic color palette (Primary/On Primary/Secondary/.../Ring), verified 0 malformed color values across all 192 rows (16-token check across 192 rows = 3,072 individual color-value checks, all passed either `#RRGGBB` or a valid `rgba(...)` form).
- `products.csv` → product type, keywords, style recommendation, landing-pattern reference, key considerations. Verified 192/192 `Product Type` values have an exact 1:1 match in `colors.csv` (no orphaned rows either direction).
- `typography.csv` → all 74 font pairings (name, heading/body font, mood keywords, best-for description, Google Fonts URL). Google Fonts themselves are OFL-licensed (a separate, standard, well-known open font license), not re-licensed by this adaptation.
- `landing.csv` → all 34 landing-page pattern archetypes (pattern id/name, section order, primary CTA placement) — the "Conversion Optimization" column's accessibility guidance (WCAG contrast, reduced-motion handling) was read but not copied verbatim into these JSON files; see `landing-page-composer`'s own SKILL.md for how that guidance is applied.

Deliberately NOT adapted by this skill (harvested separately in sibling skills the same session, once thatlq1812 flagged the initial 2-skill harvest as too narrow — see each skill's own PROVENANCE/elicited_from for its own scope):
- `styles.csv` (88 rows) → harvested into `skills/design/ui-style-guide-lookup`.
- `icons.csv` (105 rows) → harvested into `skills/design/ui-icon-recommender`.
- `ux-guidelines.csv` (119 rows) + `app-interface.csv` (32 rows) → merged and harvested into `skills/webpage/ui-guideline-lookup`.

Still NOT adapted by anything this session:
- `google-fonts.csv` (1,935 rows, the full Google Fonts catalog metadata) — out of scope for a product-type/style lookup; a future skill could adapt this separately if a real need arises (e.g. browsing fonts directly rather than via a curated pairing).
- `ui-reasoning.csv`'s JSON decision-rule column (`if_ux_focused`, `if_data_heavy`, etc.) — a more complex conditional-reasoning engine than any of this session's simple deterministic lookups attempt; not adapted.
- `charts.csv` (25 chart types), `motion.csv` (18 GSAP presets), `react-performance.csv` (45 rows) — real, potentially valuable datasets, not yet harvested; flagged as real future-extension candidates, not silently dropped.
- All Python source (`search.py`'s BM25 engine, `design_system.py`, `reasoning_contract.py`) — not copied by any skill this session; each harvested skill's own script is a from-scratch, much simpler exact-match/keyword-overlap lookup, not a port of the source's more sophisticated search engine.
- The 6 other `.claude/skills/` sub-skills in the source repo (`design-system`, `design`, `ui-styling`, `banner-design`, `brand`, `slides`) — inspected but not harvested: most are thin routers referencing external tooling (Node.js scripts, other npm packages) not vendored in the git repo itself, except `design-system` which has real slide/presentation-generation code+data (`slide-*.csv`) — deliberately not harvested since Scriptorium already has a real, different presentation mechanism (`slide-deck-composer`, clone-and-inject `.pptx`) and duplicating that capability via a different tech stack (HTML+Chart.js) wasn't judged worth the dedup risk this round.

## Freshness

The source repository's own `data-provenance.json` records most entries as `verifiedAt: 2026-08-12`, with a 90-day `needs-review` SLA policy. This adaptation was made 2026-08-15, 3 days after that verification date. No freshness-tracking mechanism was built into this skill's own data (a real, honest gap, not silently assumed away) — a future update should re-diff against the source repo's latest commit before treating this data as current beyond a few months out.
