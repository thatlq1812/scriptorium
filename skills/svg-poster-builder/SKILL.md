---
name: svg-poster-builder
description: Deterministic SVG layout renderer for posters/banners/flyers at real ISO 216 paper sizes (A1 594x841mm, A4 210x297mm). `render_layout.py` reads a caller-declared layout.json (canvas preset + a list of percentage-positioned zones typed as hero_image/content_scene/vignette/decorative_element/background_canvas/typography_frame) and renders labeled placeholder rectangles as valid SVG -- it never generates the actual illustration/imagery content itself. Use for planning/prototyping a poster's composition (zone sizes, positions, overlap-free layout) before real artwork is dropped into each zone by hand or another tool. Do NOT use this for AI image generation -- Scriptorium never calls an AI API (CLAUDE.md principle 8); pair this with image-generator-gemini or a design tool for actual imagery.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Zone taxonomy (hero_image/content_scene/vignette/decorative_element/background_canvas/typography_frame) and full-bleed/no-overflow placement discipline grounded directly in a real production A1-poster rendering pipeline's own documented component-type schema (D:/Document/May052026/scripts/component_types.md, a real system this project has direct access to, per UPGRADE_PLAN_20260729.md Item 4) -- not invented categories. Canvas sizes are the real public ISO 216 standard (A1/A4), not invented dimensions."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["poster", "diagram"]
---

# svg-poster-builder

Renders composition, not content. Every zone becomes a labeled placeholder rectangle -- real artwork replaces each rectangle afterward, by hand or another tool.

## Why this skill, and why this scope

Deterministic SVG/layout tooling is explicitly the Light Design cluster's intended scope (`UPGRADE_PLAN_20260729.md` Item 4) -- staying strictly on the "deterministic composition" side and never drifting into AI image generation, Figma-clone territory, or anything competing with Photoshop/Illustrator (a red ocean off-thesis for a pure-artifact, no-AI-backend project). The zone taxonomy isn't invented: it's the same 6-type schema (`hero_image`, `content_scene`, `vignette`, `decorative_element`, `background_canvas`, `typography_frame`) a real production poster-rendering pipeline actually uses to structure its own layouts, with the same "full-bleed, no overflow past the canvas edge" discipline that pipeline's own docs specify.

## Run

```bash
python scripts/render_layout.py <layout.json> -o poster.svg
```

Start from `assets/layout_template.json`. `canvas.preset` is `"A1"` or `"A4"` (real ISO 216 mm dimensions, used directly as the SVG's `viewBox`/`width`/`height`). Each zone declares `id` (unique), `type` (one of the 6 taxonomy types), `x_pct`/`y_pct`/`w_pct`/`h_pct` (0-100, percentage of canvas), and optionally `fill` (hex, defaults to a per-type placeholder color) and `text_label` (shown inside the rectangle; **required** for `typography_frame` zones, since their whole purpose is holding text). Exit 0 = rendered, 1 = layout violations (all printed), 2 = malformed input.

### Layout schema

```json
{
  "canvas": {"preset": "A4"},
  "zones": [
    {"id": "hero", "type": "hero_image", "x_pct": 10, "y_pct": 8, "w_pct": 80, "h_pct": 45, "text_label": "optional"}
  ]
}
```

## What this skill does NOT do

- Does not generate or place real imagery/illustration -- every zone is a flat-colored labeled rectangle, a composition placeholder only.
- Does not call any AI/image-generation API -- pair with `image-generator-gemini` (or any external design tool) separately for actual artwork once the layout is approved.
- Does not support arbitrary canvas sizes -- only the 2 declared ISO 216 presets (A1, A4) this round; adding more presets is a real, cheap follow-up once a real need for one surfaces (e.g. A2/A3), not preemptively guessed.
- Does not do collision detection between zones beyond canvas-boundary overflow -- two zones can be declared overlapping (e.g. a decorative element intentionally over a background_canvas) and this skill won't flag it, since overlap is sometimes intentional in this taxonomy (decorative elements over content).

## Verified

Rendered the bundled `layout_template.json` (6 zones spanning all 6 taxonomy types) to a real SVG file, confirmed well-formed XML via `xml.etree.ElementTree.parse` and correct `viewBox="0 0 210 297"` (A4 mm dimensions). 4 deliberately broken cases: a zone with `x_pct + w_pct = 105` (overflowing the canvas) correctly refused (exit 1, exact zone id + computed sum); a duplicate zone `id` correctly refused; a `typography_frame` zone missing `text_label` correctly refused; an unknown `canvas.preset` (`"A0"`) correctly refused, listing the valid presets.

## Known limitations (v0.1.0)

- Only 2 canvas presets (A1, A4) — extend when a real need for another ISO size surfaces.
- No overlap/collision detection beyond canvas-boundary overflow (see above) — a caller declaring two zones at the same position gets both rendered, stacked.
- Text labels are rendered at a fixed proportional font size (8% of the zone's shorter dimension) with no line-wrapping — long labels will overflow their rectangle visually; fine for a composition placeholder, not meant to be a final typography decision.
