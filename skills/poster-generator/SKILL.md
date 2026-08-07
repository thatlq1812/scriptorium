---
name: poster-generator
description: 'SUPERSEDED 2026-08-07 by html-poster-composer -- do not use for new work, see Known limitations. Renders a FINAL flattened poster/banner PNG by filling a svg-poster-builder-compatible layout.json''s zones with real content (an image, a solid fill color, or auto-wrapped text) -- deterministic, PIL-based. Also includes an OPTIONAL Gemini-powered `suggest_layout.py` proposing zone placement, validated against the caller''s element list, bounded retry loop. Do NOT use this for layout composition/validation itself -- that lived in `svg-poster-builder`.'
license: MIT
compatibility: 'Requires Python 3.11+ + `Pillow` (deterministic render path, no key needed) + `google-genai` + the user''s own `GEMINI_API_KEY` (ONLY for the optional `suggest_layout.py` step) + the `svg-poster-builder` skill installed as a sibling skill folder (reused for its zone schema/validator). Verified running clean: Claude Code, Windows (2026-08-05, re-verified 2026-08-07 for the Light Design cluster chain), real end-to-end render including a real Gemini layout-suggestion call. See "Verified" below.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in a GitHub architecture survey of 4 poster/graphic-design-AI repos (PosterCraft -- FLUX.1 non-commercial, idea-only; CreatiPoster -- no license, idea-only; PosterLLaVA -- CC BY-NC 4.0, idea-only; auto-poster-generator -- Apache-2.0, pattern reused directly), recorded in data/references/poster-design-ai/NOTES.md (GenVid project 2026-08-05): auto-poster-generator's config-driven template+PIL-overlay pattern (#4, the only license-clean, AI-free repo of the 4) is the direct basis for render_poster.py; PosterLLaVA's 'LLM proposes layout JSON, a separate step renders it' split (#3, idea only -- CC BY-NC forbids reusing its code/weights) motivated suggest_layout.py, deliberately mapped onto this project's ALREADY-EXISTING svg-poster-builder zone schema instead of inventing a new layout format, since NOTES.md's own comparison table identified 'auto layout' (not 'auto image generation') as the real gap between image-generator-gemini and the Light Design cluster. The zone schema/validator/render_layout module itself is not re-elicited here -- it's svg-poster-builder's own (already-elicited from a real production A1-poster pipeline, see that skill's SKILL.md), reused via cross-skill import per this project's dedup-over-parallel-implementation discipline."
  version: 0.1.1
  changelog_0_1_1: "Doc-only (2026-08-07): added a 'Chains into (Light Design cluster)' section documenting and verifying real composability with brand-identity-linter (resolved color roles -> content.json fills) and light-logo-arranger (compute_anchor.py's collision-checked placement -> a decorative_element zone), owner-directed after noting the media and design clusters looked disconnected. Verified end-to-end with a real deterministic render (no Gemini call needed for this chain): brand-identity-linter's resolved hex values and light-logo-arranger's computed logo position both round-tripped correctly into a real rendered poster.png. No script change -- the schemas already lined up."
  grounding: not_applicable
  object_type: ["poster"]
---

# poster-generator

> **SUPERSEDED (owner decision, 2026-08-07) — use `html-poster-composer` instead.** `skill-exporter` refuses to export this skill (`registry/skills.json`'s `operational_status.state == "superseded"`). Same real migration reason as `svg-poster-builder` (which this skill depended on) -- see that skill's own superseded note and `docs/ROADMAP.md`'s 2026-08-07 entry. `html-poster-composer` accepts the same `layout.json`/`content.json` contract this skill used; a caller switches by pointing at the new skill's `compose.py`, no content format changes needed. `suggest_layout.py`'s Gemini-based layout suggestion was NOT ported to the new skill (out of scope for this migration round, flagged as a real open follow-up, not silently dropped) -- see `html-poster-composer/SKILL.md`'s "Known limitations".

Fills a `svg-poster-builder` layout's zones with real content and flattens it into a finished poster PNG. The layout schema and its structural validation are NOT reinvented here — both are imported directly from `svg-poster-builder`, so a layout.json always means the same thing whether it's being previewed as placeholder SVG or rendered as a real poster.

## Pipeline this skill sits in

```
suggest_layout.py (optional, Gemini)  ──┐
hand-written layout.json ───────────────┴──> svg-poster-builder's render_layout.py (SVG preview, sanity-check)
                                          │
image-generator-gemini (art per zone) ───┤
content.json (text/fill per zone) ───────┘──> render_poster.py ──> final poster.png
```

`svg-poster-builder`'s own SVG preview step is optional but recommended before spending time on content — it catches overflow/text-coverage violations as a quick visual, without needing any real assets yet.

## Chains into (Light Design cluster, verified 2026-08-07)

This skill's `content.json`/`layout.json` inputs are deliberately plain (hex strings, mm-percentage coordinates) so the Light Design cluster's deterministic tools can feed them directly, no AI call needed for these steps:

- **`brand-identity-linter`** resolves a project's color roles (primary/secondary/accent, with a real fallback chain when only some are declared) — feed the resolved hex values straight into `content.json`'s `fill`/`text.color` fields instead of re-picking colors by eye. Verified real: `validate_brand.py` on a 2-color brand (`primary`/`secondary` declared) resolved `accent` via `fallback-to-secondary`; the exact resolved hex values were used as `fill` colors in a `poster-generator` render and produced a correctly color-consistent poster.
- **`light-logo-arranger`**'s `compute_anchor.py` computes a collision-checked logo/ornament position (refusing if it overlaps a declared exclusion zone, e.g. a `typography_frame`) — convert its `x`/`y`/margin output (mm) to `x_pct`/`y_pct` of the canvas and declare that as a `decorative_element` zone in `layout.json`. Verified real: computed a top-left placement against a `placement.json` excluding the poster's own `title_frame` box, confirmed it refuses when forced to collide with an equivalent exclusion zone, converted the passing placement's mm coordinates to percentages, declared the zone, and rendered a real poster with the logo/ornament at exactly that computed position.
- **`image-generator-gemini`** (paired with `media-anchor-profile` for identity/style consistency across zones) supplies real `image`-type content for `hero_image`/`content_scene` zones — see that skill's own `SKILL.md` for the real Gemini-backed example; this skill's `content.json` schema accepts its output paths directly, no conversion step.

No new code was needed for any of this — the schemas already lined up; the gap was that none of the 4 `SKILL.md`s said so.

## Content schema (content.json)

```json
{
  "zones": {
    "master_anchor": {"type": "fill", "color": "#F5E6C8"},
    "hero": {"type": "image", "path": "hero.png", "fit": "cover"},
    "title_frame": {"type": "text", "text": "CONTEST TITLE", "color": "#222222", "font_size_pct": 40, "align": "center", "font_path": null},
    "corner_ornament": {"type": "fill", "color": "#D9822B"}
  }
}
```

Every zone id in the layout must have exactly one matching content entry (checked by `validate_content.py` — a missing OR an extra/typo'd zone id is a hard error, never a silent skip). `type` is `image` (a real asset, `fit`: `cover` crops to fill / `contain` letterboxes), `fill` (solid color, for `background_canvas`/`decorative_element`/any non-text zone with no dedicated art), or `text` (only valid on `typography_frame` zones — auto-wrapped and centered by width, font size derived from `font_size_pct` of the zone's height). `font_path` is optional; if omitted, a portable fallback chain is tried (common system fonts, then Pillow's own scalable default font — verified never crashes even with zero fonts available on a machine).

## Render (deterministic, no AI call)

```bash
.venv\Scripts\python.exe skills\poster-generator\scripts\render_poster.py layout.json content.json poster.png --dpi 150
```

Re-validates BOTH the layout (via `svg-poster-builder`'s own `_validate_layout()`) and the content cross-reference before touching a single pixel — refuses to render an invalid combination rather than producing a half-broken poster. `--dpi` controls the mm-to-pixel conversion (default 150; use 300 for print-quality output).

## Optional: let Gemini propose the layout

```bash
.venv\Scripts\python.exe skills\poster-generator\scripts\suggest_layout.py elements.json suggested_layout.json
```

`elements.json`: `{"canvas_preset": "A4", "elements": [{"id": "hero", "type": "hero_image"}, ...], "style_notes": "free text"}`. Gemini proposes `x_pct`/`y_pct`/`w_pct`/`h_pct` for each declared element — it may NOT rename, drop, add, or retype any element (checked explicitly, not assumed), and the resulting layout must pass `svg-poster-builder`'s real structural validator (overflow, 40% text-coverage cap). Either check failing triggers a bounded retry (up to 3 attempts, feeding the specific errors back into the next prompt) rather than a silent accept of a broken layout or an infinite loop.

## What this skill does NOT do

- Does not define or validate the zone/layout schema itself — that's `svg-poster-builder`'s job, reused here via cross-skill import (`ZONE_TYPES`, `CANVAS_PRESETS_MM`, `_validate_layout`), never duplicated.
- Does not generate the actual artwork for `image`-type content entries — supply a path from `image-generator-gemini` (or any other source); this skill only composites what it's given.
- Does not require a Gemini API key for the core render path — `suggest_layout.py` is the only part of this skill that calls an AI API, and it's entirely optional.
- Does not support multi-page posters, bleed/trim marks, or CMYK color profiles — RGB PNG output only, matching `svg-poster-builder`'s own ISO 216 mm-based scope, not a full print-production pipeline.
- Does not loop/tile a fill or texture — `fill` is a single flat solid color.

## Bundled files

- `scripts/validate_content.py` — CLI + importable `validate_content()`.
- `scripts/render_poster.py` — CLI + importable `render()`; re-validates layout + content before rendering.
- `scripts/suggest_layout.py` — CLI + importable `suggest_layout()` (Gemini, optional).
- `requirements.txt` — `google-genai`, `Pillow`.

## Verified

Real end-to-end run (2026-08-05) using `svg-poster-builder`'s own bundled `assets/layout_template.json` (6 zones: background/hero/title/2 scenes/ornament) as the layout, filled with 3 real `image-generator-gemini`-produced images (the same fox character across different scenes) + 2 solid fills + auto-wrapped title text: rendered a real 827x1169px PNG at 100dpi, all 6 zones correctly positioned/fit/wrapped (visually confirmed). A deliberately broken layout (a zone with `w_pct: 200`, exceeding canvas width, and a `typography_frame` missing its required `text_label`) was correctly refused with all 3 specific errors, no file written. `suggest_layout.py` tested for real against the owner's own Gemini API key: given the same 6-element request with only type/id declared (no coordinates), Gemini produced a fully valid layout on the FIRST attempt (no retry needed) — all 6 element ids/types preserved exactly, passed `svg-poster-builder`'s structural validator with no violations, and produced a real poster (via `render_poster.py`) with sensible spacing, arguably better whitespace balance than the hand-authored comparison layout.

**Light Design cluster chain (2026-08-07)**: real end-to-end run with zero AI calls. `brand-identity-linter`'s `validate_brand.py` on a 2-color brand (`primary: #2F6F4F`, `secondary: #E8A33D`, no `accent` declared) resolved `accent -> #E8A33D (fallback-to-secondary)`; those exact 2 hex values were used as `fill` colors for 3 zones in a real `content.json`. `light-logo-arranger`'s `compute_anchor.py` computed a `top-left` placement (`x=6.00, y=6.00`) against a `placement.json` excluding the poster's own `title_frame` box -- confirmed the exclusion check is real by re-running with a colliding exclusion zone (correctly refused, exit 1); the passing placement's mm coordinates were converted to `x_pct`/`y_pct` and declared as a `decorative_element` zone in `layout.json`. Rendered via `render_poster.py`: a real 827x1169px PNG with the resolved brand colors and the collision-checked logo position both landed exactly where computed (visually confirmed).

## Known limitations (v0.1.0)

- `suggest_layout.py`'s retry loop is capped at 3 attempts — a persistently uncooperative model response surfaces as an error, not an infinite loop, but also not a guaranteed success.
- Text rendering is single-style per zone (one font/size/color/alignment) — no per-word styling (bold spans, mixed colors) within one `typography_frame`.
- `fill` content is a single flat color only — no gradients or texture fills.
- Font fallback chain (`_SYSTEM_FONT_CANDIDATES` in `render_poster.py`) hardcodes 3 common OS paths (Windows Arial, macOS Helvetica, Linux DejaVuSans) — a machine without any of these AND without a caller-supplied `font_path` falls back to Pillow's default font, which is legible but generic, not tested for CJK/Vietnamese diacritics rendering quality specifically.
- No automatic content-vs-zone-aspect-ratio warning (e.g. a portrait photo forced into a very wide `hero_image` zone via `cover` will crop aggressively) — `fit: contain` is available as an alternative but not auto-selected.
