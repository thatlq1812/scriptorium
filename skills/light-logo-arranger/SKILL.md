---
name: light-logo-arranger
description: Deterministic icon/logo anchor-position calculator. `compute_anchor.py` computes the (x, y) top-left placement of a logo/icon within a canvas given a named anchor point (top-left/top-right/top-center/bottom-left/bottom-right/bottom-center/center) and a margin, then refuses if the resulting rectangle overlaps any caller-declared exclusion zone -- never silently places a logo over another element. Unit-agnostic (mm, px, or percentage -- whatever units the caller's canvas/logo sizes use). Use to compute exact logo placement for a signboard/poster/document header without manual pixel math. Do NOT use this for automatic multi-element layout optimization -- it places exactly one logo per run, against exactly the anchor point the caller names.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Anchor-then-exclude placement concept lightly grounded in a real production layout pipeline's own component-chaining idea (fixed anchor point -> dependent placement, D:/Document/May052026/scripts/component_types.md's master_anchor/group_anchor chain hierarchy, per UPGRADE_PLAN_20260729.md Item 4), simplified here to single-point named-anchor placement against canvas corners/edges/center rather than a full multi-component chain -- that fuller chaining behavior is out of scope for this deterministic utility."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["logo", "diagram"]
---

# light-logo-arranger

One computation, one refusal condition: compute a named-anchor placement, refuse if it collides with a declared exclusion zone.

## Why this skill, and why this scope

A companion utility to `svg-poster-builder`/`brand-identity-linter` within the Light Design cluster (`UPGRADE_PLAN_20260729.md` Item 4) — placing a logo/icon by hand means manual pixel/mm arithmetic for every canvas size change; this does the arithmetic and, critically, refuses rather than silently overlapping something already placed (a real, cheap way to avoid the exact "orphan icon"/misplaced-element class of problem `brand-identity-linter` catches from a different angle).

## Run

```bash
python scripts/compute_anchor.py <placement.json>
```

Start from `assets/placement_template.json`. Prints `x=...` / `y=...` on success. Exit 0 = placement computed, 1 = placement is geometrically impossible with the given margin, or overlaps a declared exclusion zone (named exactly which one), 2 = malformed input (bad anchor name, logo larger than canvas, missing keys).

### Schema

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

## What this skill does NOT do

- Does not place more than one logo per run, and does not optimize placement across multiple elements — it computes exactly the named anchor's position, nothing else.
- Does not resize the logo to fit — if the requested margin makes the placement fall outside the canvas, it refuses (exit 1) rather than silently shrinking anything.
- Does not read or write any actual image/SVG file — pure coordinate arithmetic; pair with `svg-poster-builder` or another rendering tool to actually place the logo.

## Verified

Computed all 7 anchor points against the bundled `placement_template.json` (210x297 canvas, 30x20 logo, margin 8) and hand-verified each result: `top-left` (8,8), `top-right` (172,8), `top-center` (90,8), `bottom-left` (8,269), `bottom-right` (172,269), `bottom-center` (90,269), `center` (90,138.5) — all matched manual arithmetic exactly. 4 deliberately broken/edge cases: a `top-left` placement overlapping a declared exclusion zone correctly refused, naming the exact overlapping zone; a logo declared larger than the canvas correctly refused (exit 2); a margin of 250 on a 297-tall canvas correctly refused as geometrically impossible (exit 1, showing the resulting out-of-bounds coordinates); an unknown anchor name (`"middle-ish"`) correctly refused (exit 2), listing the 7 valid values.

## Known limitations (v0.1.0)

- Single logo per run only — no multi-component chaining like the real production pipeline's master/group anchor hierarchy this concept is lightly grounded in; that fuller behavior is explicitly out of scope for v0.1.0.
- Exclusion-zone overlap check is a simple axis-aligned rectangle test — no rotation/non-rectangular exclusion shapes.
- Unit-agnostic by design (no built-in mm/px conversion) — the caller must ensure `canvas_w`/`canvas_h`/`logo_w`/`logo_h`/`margin`/exclusion zones are all in the same unit; mixing units silently produces a wrong-but-not-caught placement.
