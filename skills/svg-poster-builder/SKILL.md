---
name: svg-poster-builder
description: 'SUPERSEDED 2026-08-07 by html-poster-composer -- do not use for new work, see Known limitations. Deterministic SVG layout renderer for posters/banners/flyers at real ISO 216 paper sizes (A1 594x841mm, A4 210x297mm). `render_layout.py` reads a caller-declared layout.json (canvas preset + a list of percentage-positioned zones typed as hero_image/content_scene/vignette/decorative_element/background_canvas/typography_frame) and renders labeled placeholder rectangles as valid SVG -- it never generates the actual illustration/imagery content itself. Enforces a max-40%-canvas-area text-coverage cap across typography_frame zones. Do NOT use this for AI image generation -- Scriptorium never calls an AI API (CLAUDE.md principle 8).'
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29, re-verified 2026-08-01 for v0.2.0, 2026-08-07 for v0.3.0).'
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Zone taxonomy (hero_image/content_scene/vignette/decorative_element/background_canvas/typography_frame) and full-bleed/no-overflow placement discipline grounded directly in a real production A1-poster rendering pipeline's own documented component-type schema (D:/Document/May052026/scripts/component_types.md, a real system this project has direct access to, per UPGRADE_PLAN_20260729.md Item 4) -- not invented categories. Canvas sizes are the real public ISO 216 standard (A1/A4), not invented dimensions. v0.2.0 additionally ports the max-text-coverage-pct=40.0 numeric threshold from the owner's own prior production system (real, statistically-grounded, no license issue -- rewritten clean, not blind-copied): D:/elix/archive/platform_archive/modules/presentation/scoring/design_rules.py, CONTENT_DENSITY['max_text_coverage_pct'], sourced from 10 Canva templates, 149 Slidesgo templates / 7,854 slides / 3,526 font samples, and 8 real presentations. The companion min_whitespace_pct=30.0 rule from the same source was deliberately NOT ported -- see 'Known limitations' for why it's a forced fit for this zone taxonomy."
  version: 0.3.0
  grounding: not_applicable
  object_type: ["poster", "diagram"]
---

# svg-poster-builder

> **SUPERSEDED (owner decision, 2026-08-07) — use `html-poster-composer` instead.** `skill-exporter` refuses to export this skill (`registry/skills.json`'s `operational_status.state == "superseded"`). Real migration reason: the SVG-string+Pillow render backend had no way to verify a text zone's actual rendered size against its declared zone height, silently overflowing rather than refusing (see `docs/ROADMAP.md`'s 2026-08-07 entry for the real bug that surfaced this and the real A/B test that motivated the HTML/CSS+headless-browser replacement). `html-poster-composer` reuses this skill's exact zone-taxonomy/layout.json schema and validation rules -- a layout.json written for this skill works unchanged there. Left in place (not deleted) since the code is still correct for what it does, just superseded by a strictly more capable renderer.

Renders composition, not content. Every zone becomes a labeled placeholder rectangle -- real artwork replaces each rectangle afterward, by hand or another tool.

## Why this skill, and why this scope

Deterministic SVG/layout tooling is explicitly the Light Design cluster's intended scope (`UPGRADE_PLAN_20260729.md` Item 4) -- staying strictly on the "deterministic composition" side and never drifting into AI image generation, Figma-clone territory, or anything competing with Photoshop/Illustrator (a red ocean off-thesis for a pure-artifact, no-AI-backend project). The zone taxonomy isn't invented: it's the same 6-type schema (`hero_image`, `content_scene`, `vignette`, `decorative_element`, `background_canvas`, `typography_frame`) a real production poster-rendering pipeline actually uses to structure its own layouts, with the same "full-bleed, no overflow past the canvas edge" discipline that pipeline's own docs specify.

## Run

```bash
python scripts/render_layout.py <layout.json> -o poster.svg
```

Start from `assets/layout_template.json`. `canvas.preset` is `"A1"` or `"A4"` (real ISO 216 mm dimensions, used directly as the SVG's `viewBox`/`width`/`height`). Each zone declares `id` (unique), `type` (one of the 6 taxonomy types), `x_pct`/`y_pct`/`w_pct`/`h_pct` (0-100, percentage of canvas), and optionally `fill` (hex, defaults to a per-type placeholder color) and `text_label` (shown inside the rectangle; **required** for `typography_frame` zones, since their whole purpose is holding text). Exit 0 = rendered, 1 = layout violations (all printed), 2 = malformed input.

**Text-coverage cap (v0.2.0):** the sum of `w_pct * h_pct / 100` across all `typography_frame` zones (i.e. their combined area as a % of the total canvas area) must not exceed 40% -- a hard refusal if it does, naming the computed percentage. Ported from `design_rules.py`'s `CONTENT_DENSITY['max_text_coverage_pct']`. Zone area is used as the text-density proxy since it's the only content measure this zone taxonomy actually carries.

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
- Does not enforce a minimum-whitespace / max-total-zone-coverage rule across all zone types (see "Known limitations" below for why this was deliberately skipped as a forced fit) -- the text-coverage cap applies only to `typography_frame` zones specifically.
- Does not measure actual rendered pixel/character text density -- the text-coverage check uses declared zone area (`w_pct * h_pct`) as a proxy, not real glyph coverage inside the zone.

## Verified

Rendered the bundled `layout_template.json` (6 zones spanning all 6 taxonomy types) to a real SVG file, confirmed well-formed XML via `xml.etree.ElementTree.parse` and correct `viewBox="0 0 210 297"` (A4 mm dimensions); its `typography_frame` zone covers 8.4% of the canvas, well under the new 40% cap. 4 pre-existing deliberately broken cases (unchanged, re-verified): a zone with `x_pct + w_pct = 105` (overflowing the canvas) correctly refused (exit 1, exact zone id + computed sum); a duplicate zone `id` correctly refused; a `typography_frame` zone missing `text_label` correctly refused; an unknown `canvas.preset` (`"A0"`) correctly refused, listing the valid presets. New for v0.2.0: a single `typography_frame` zone sized 90%x50% (45% of canvas) correctly refused, naming the computed percentage and the 40% cap; two `typography_frame` zones summing to 48% of canvas (60%x40% + 60%x40%) correctly refused with the combined percentage; a layout with `typography_frame` area at exactly the 40.0% boundary correctly PASSED (only "exceeds" triggers refusal, not "equals"); a layout with multiple small `typography_frame` zones summing to 28% correctly PASSED.

**v0.3.0**: owner-reported real usability complaint ("toàn box đè lên nhau, không rõ ràng") confirmed directly by rendering `layout_template.json` and reading the raw SVG -- the old `font_size = min(w, h) * 0.08` formula had no floor, producing a 1.3mm (~3.7pt) label on the bundled `corner_ornament` zone (16.8x17.8mm), effectively invisible; inline labels also concatenated `id (type)` regardless of zone size, worsening overflow on small zones. Fixed: `_clamp_font_size()` bounds every inline label to [3.5mm, 11.0mm]; non-`typography_frame` zones now show only their `id` inline (shorter, less overflow-prone) instead of `id (type)`; a legend band is appended below the real canvas (outside the `viewBox` area that maps to the poster's actual print dimensions) listing every zone's id/type/fill-swatch/declared `text_label` in a fixed, always-readable 3.6mm font -- so a zone's identity is always recoverable from the legend even when its own inline label is small or visually crowded. Re-verified: re-rendered `layout_template.json`, confirmed well-formed XML, `corner_ornament`'s inline label now renders at the 3.5mm floor (was 1.3mm) and is listed in full in the legend; all 4 pre-existing broken-case refusals (overflow, duplicate id, missing text_label, unknown preset) and both new v0.2.0 text-coverage refusal/pass cases re-run unchanged, since none of this touched `_validate_layout()`. No schema change -- `layout.json`'s shape and every validation rule are unchanged; only `_render_svg()`'s visual output changed, and only this skill's own preview SVG consumes it (confirmed via repo-wide grep: `poster-generator` computes zone pixel positions directly from `layout.json` via imported `CANVAS_PRESETS_MM`/`_validate_layout`, never parses this skill's rendered SVG file, so the added legend band and the total SVG height it introduces have zero downstream impact).

## Known limitations (v0.2.0)

- Only 2 canvas presets (A1, A4) — extend when a real need for another ISO size surfaces.
- No overlap/collision detection beyond canvas-boundary overflow (see above) — a caller declaring two zones at the same position gets both rendered, stacked.
- Text labels are rendered at a proportional font size (8% of the zone's shorter dimension, clamped to [3.5mm, 11.0mm] since v0.3.0) with no line-wrapping — a long label or a very small zone can still overflow its rectangle visually; the legend band is the authoritative fallback for exact zone identity, this inline text is a quick-glance aid, not a final typography decision.
- `design_rules.py`'s companion `min_whitespace_pct=30.0` rule ("at least 30% of the canvas must be empty") was deliberately NOT ported. This taxonomy's own bundled fixture has a `background_canvas` zone spanning 100% of the canvas by design (`assets/layout_template.json`'s "master_anchor" zone) -- a canvas-wide whitespace measure built from summing zone areas would either always fail (full-bleed background "fills" 100% by design) or be wrong (zones are documented as allowed to intentionally overlap, e.g. decorative elements over content, so summed area overcounts real coverage). Forcing this rule onto a schema built around full-bleed background zones and intentional overlap would contort the skill rather than genuinely apply the source rule, so it's skipped -- if a real need for whitespace enforcement surfaces, it belongs on a zone taxonomy that tracks actual non-overlapping coverage, not this one's percentage-positioned, overlap-tolerant zones.

## Changelog

- **0.3.0** (2026-08-07): Fixed a real label-legibility bug (owner-reported: "toàn box đè lên nhau, không rõ ràng") -- inline label font size now floored/ceilinged to [3.5mm, 11.0mm] instead of an unbounded proportional formula that rendered near-invisible text on small zones; non-`typography_frame` zones show only their `id` inline instead of `id (type)`; added a legend band below the canvas (id + type + fill swatch + declared `text_label`, always at a fixed readable size) so every zone is identifiable regardless of its own inline label's size. No schema/validation change.
- **0.2.0** (2026-08-01): Ported the `max_text_coverage_pct=40.0` numeric threshold from the owner's prior production system (`design_rules.py`) -- see `metadata.elicited_from`. Added a hard check: the combined area of all `typography_frame` zones must not exceed 40% of the canvas area. Deliberately did not port the companion `min_whitespace_pct` rule (see "Known limitations" for why it's a forced fit here).
- **0.1.0** (2026-07-29): Initial release, deterministic SVG layout rendering for 6 zone taxonomy types across A1/A4 canvases.
