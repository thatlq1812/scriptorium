---
name: light-logo-arranger
description: Deterministic icon/logo anchor-position calculator plus two companion checklist tools. `compute_anchor.py` computes (x, y) placement of a logo/icon within a canvas given a named anchor point and margin, refusing if the result overlaps a caller-declared exclusion zone. Unit-agnostic (mm/px/percentage). `check_asset_completeness.py` reports which deliverables from a standard brand-identity asset checklist (icon, wordmark variants, banners, splash, login background, pattern tile) are missing from a caller-declared produced-assets set. `resolve_font_fallback.py` reports whether a declared wordmark font is system-safe or needs a substitute, against a fixed geometric-similarity mapping table, refusing loudly for unmapped fonts. Use to compute logo placement, gap-check a brand-asset set, or resolve a font substitute — no manual pixel math or guessing. Do NOT use for automatic layout optimization, actual asset generation, or font file download/embedding — pure coordinate arithmetic and checklist lookup.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29, 2026-08-01).'
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Anchor-then-exclude placement concept lightly grounded in a real production layout pipeline's own component-chaining idea (fixed anchor point -> dependent placement, D:/Document/May052026/scripts/component_types.md's master_anchor/group_anchor chain hierarchy, per UPGRADE_PLAN_20260729.md Item 4), simplified here to single-point named-anchor placement against canvas corners/edges/center rather than a full multi-component chain -- that fuller chaining behavior is out of scope for this deterministic utility. Asset-completeness checklist (assets/asset_checklist.json) elicited from a real production brand-asset generation system's own deliverable manifest: D:/elix/archive/platform_archive/scripts/gen/gen_brand_identity.py and gen_brand_icon.py -- only the checklist of what a full brand-identity deliverable set consists of (8 core assets + 7 derived favicon/adaptive-icon/splash-icon variants) was ported; the source scripts' AI-image-generation mechanism (Gemini 3 Pro Image Preview) was deliberately NOT ported -- out of scope per this project's no-AI-backend principle. Font-fallback table (assets/font_fallback_map.json) ported verbatim (actual name -> substitute data, not just the concept) from a real production presentation-rendering pipeline's empirically-derived geometric-similarity map: D:/elix/archive/platform_archive/modules/presentation/pptx/font_fallback_map.py."
  version: 0.2.0
  grounding: not_applicable
  object_type: ["logo", "diagram"]
---

# light-logo-arranger

Three deterministic checks, each with one refusal condition: `compute_anchor.py` computes a named-anchor placement and refuses if it collides with a declared exclusion zone; `check_asset_completeness.py` reports missing required brand assets against a fixed checklist and refuses on any unrecognized asset key; `resolve_font_fallback.py` resolves a wordmark font to a safe substitute and refuses if no mapping exists.

## Why this skill, and why this scope

A companion utility to `svg-poster-builder`/`brand-identity-linter` within the Light Design cluster (`UPGRADE_PLAN_20260729.md` Item 4) — placing a logo/icon by hand means manual pixel/mm arithmetic for every canvas size change; this does the arithmetic and, critically, refuses rather than silently overlapping something already placed (a real, cheap way to avoid the exact "orphan icon"/misplaced-element class of problem `brand-identity-linter` catches from a different angle). v0.2.0 adds two more deterministic checks that come up in the same logo-placement context: whether a full brand-identity deliverable set is actually complete, and whether a declared wordmark font needs a substitute — both pure checklist/lookup, no generation.

## Run

### `compute_anchor.py` — named-anchor placement

```bash
python scripts/compute_anchor.py <placement.json>
```

Start from `assets/placement_template.json`. Prints `x=...` / `y=...` on success. Exit 0 = placement computed, 1 = placement is geometrically impossible with the given margin, or overlaps a declared exclusion zone (named exactly which one), 2 = malformed input (bad anchor name, logo larger than canvas, missing keys).

#### Schema

```json
{
  "canvas_w": 210, "canvas_h": 297,
  "logo_w": 30, "logo_h": 20,
  "anchor": "top-right",
  "margin": 8,
  "exclusion_zones": [{"x": 0, "y": 0, "w": 50, "h": 15}]
}
```

Valid `anchor` values: `top-left`, `top-right`, `top-center`, `bottom-left`, `bottom-right`, `bottom-center`, `center`.

### `check_asset_completeness.py` — brand-asset checklist gap report

```bash
python scripts/check_asset_completeness.py <declared_assets.json>
```

Input: `{"declared_assets": ["logo-icon", "banner-hero", ...]}` — the asset-type keys the caller has already produced. Checked against the bundled `assets/asset_checklist.json` (8 required core assets + 7 derived/auto-generated variants — see that file for the full key list and descriptions). Exit 0 = all 8 required assets declared, 1 = one or more required assets missing (listed by name; any not-yet-declared derived assets are also listed as informational, non-blocking), 2 = malformed input or a declared key not recognized by the checklist at all (listed by name, alongside every recognized key) — an unrecognized key is never silently ignored or counted as satisfying a requirement.

### `resolve_font_fallback.py` — wordmark font substitution lookup

```bash
python scripts/resolve_font_fallback.py <font_declaration.json>
```

Input: `{"font": "Montserrat"}`. Checked against the bundled `assets/font_fallback_map.json` (28 pre-installed system fonts needing no substitute, 50 non-system fonts mapped to a geometric-similarity substitute). Exit 0 = resolved (either `SYSTEM_FONT: ... no substitute needed` or `SUBSTITUTE: '<font>' -> '<mapped substitute>'`), 2 = malformed input, or the font name is in neither list — refused loudly rather than guessing a plausible-looking substitute or assuming it can be downloaded.

## What this skill does NOT do

- Does not place more than one logo per run, and does not optimize placement across multiple elements — `compute_anchor.py` computes exactly the named anchor's position, nothing else.
- Does not resize the logo to fit — if the requested margin makes the placement fall outside the canvas, it refuses (exit 1) rather than silently shrinking anything.
- Does not read or write any actual image/SVG file — pure coordinate arithmetic and checklist lookup; pair with `svg-poster-builder` or another rendering tool to actually place the logo or generate assets.
- Does not generate, download, or fetch any image, icon, or font file — `check_asset_completeness.py` and `resolve_font_fallback.py` are gap-reports and lookups against fixed local data only. No AI image generation (the source system's Gemini-based generation mechanism was explicitly not ported), no font downloading, no network calls of any kind.
- Does not track asset production over time or persist any state between runs — each run's `declared_assets` list is exactly what the caller passes that run; nothing is remembered or written to disk.
- Does not attempt fuzzy/approximate font-name matching — `resolve_font_fallback.py` does an exact match (case-insensitive) against its fixed table only; a near-miss spelling is treated as unknown, not auto-corrected.

## Verified

`compute_anchor.py`: computed all 7 anchor points against the bundled `placement_template.json` (210x297 canvas, 30x20 logo, margin 8) and hand-verified each result: `top-left` (8,8), `top-right` (172,8), `top-center` (90,8), `bottom-left` (8,269), `bottom-right` (172,269), `bottom-center` (90,269), `center` (90,138.5) — all matched manual arithmetic exactly. 4 deliberately broken/edge cases: a `top-left` placement overlapping a declared exclusion zone correctly refused, naming the exact overlapping zone; a logo declared larger than the canvas correctly refused (exit 2); a margin of 250 on a 297-tall canvas correctly refused as geometrically impossible (exit 1, showing the resulting out-of-bounds coordinates); an unknown anchor name (`"middle-ish"`) correctly refused (exit 2), listing the 7 valid values.

`check_asset_completeness.py` (v0.2.0): declaring 2 of 8 required assets (`logo-icon`, `banner-hero`) correctly reported the other 6 missing by name (`logo-wordmark`, `logo-wordmark-light`, `banner-og`, `splash-screen`, `admin-login-bg`, `pattern-tile`), exit 1; declaring all 8 required assets correctly reported `COMPLETE`, exit 0; declaring a typo'd key (`logo-icoon` alongside two valid keys) correctly refused with the unrecognized key named explicitly and the full recognized-key lists shown, exit 2 (not silently ignored, not counted toward completeness); a nonexistent input file correctly refused, exit 2.

`resolve_font_fallback.py` (v0.2.0): a known system font (`Georgia`) correctly reported "no substitute needed", exit 0; a known non-system font (`Montserrat`) correctly resolved to its real mapped substitute (`Montserrat` -> `Montserrat`, an identity mapping since it's itself on Google Fonts), exit 0; a condensed-display font (`Bebas Neue`) correctly resolved to its real mapped substitute (`Oswald`), exit 0; an unknown/unmapped font name (`ComicNeueXtremePro9000`) correctly refused with a clear message that no mapping exists, exit 2 (never silently guessing a plausible-looking substitute).

## Known limitations (v0.2.0)

- Single logo per run only — no multi-component chaining like the real production pipeline's master/group anchor hierarchy this concept is lightly grounded in; that fuller behavior is explicitly out of scope.
- Exclusion-zone overlap check is a simple axis-aligned rectangle test — no rotation/non-rectangular exclusion shapes.
- Unit-agnostic by design (no built-in mm/px conversion) — the caller must ensure `canvas_w`/`canvas_h`/`logo_w`/`logo_h`/`margin`/exclusion zones are all in the same unit; mixing units silently produces a wrong-but-not-caught placement.
- The asset checklist (`assets/asset_checklist.json`) is a fixed, generic 8-required/7-derived brand-identity set ported from one real production system's manifest — it does not adapt to a caller's project-specific deliverable list, and does not verify that a declared asset actually exists on disk or meets any quality bar; it only checks whether the key was declared.
- The font-fallback table (`assets/font_fallback_map.json`) is a fixed snapshot of 28 system fonts + 50 mapped substitutes ported from one real production pipeline — it is not exhaustive of all fonts in existence, and is never auto-updated; a legitimate font simply missing from the table is refused (exit 2), not silently assumed safe.

## Changelog

- **v0.2.0** (2026-08-01): Added `check_asset_completeness.py` (brand-identity deliverable checklist gap report) and `resolve_font_fallback.py` (wordmark font substitution lookup), each with a bundled JSON data reference (`assets/asset_checklist.json`, `assets/font_fallback_map.json`). Both elicited from real prior production systems (see `metadata.elicited_from`); their AI-generation/network-fetch mechanisms were explicitly not ported, only the deterministic checklist/data. No new dependency, no file writes, no network calls — skill remains stdlib-only.
- **v0.1.0** (2026-07-29): Initial release — `compute_anchor.py` named-anchor placement with exclusion-zone collision refusal.
