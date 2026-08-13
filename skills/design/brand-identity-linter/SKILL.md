---
name: brand-identity-linter
description: Signboard/menu brand-identity structural linter. `validate_brand.py` checks (1) a primary color-role is declared, with secondary/accent RESOLVED via a deterministic fallback chain when not explicitly declared (reports "declared" vs. "resolved via fallback" per role, never silently blank), (2) max 3 accent colors, (3) background is never pure white, (4) any element flagged role "cta"/"contact" has a font size at or above the declared body font size (emphasis discipline), (5) every icon element references a declared motif, catching "orphan icons" placed with no thematic anchor. Use when reviewing a signboard/menu/banner's declared color-and-typography spec before final render. Do NOT use this to judge subjective aesthetic quality -- it only checks the mechanical rules above, never a holistic design opinion.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29, re-verified 2026-08-01 for v0.2.0).'
metadata:
  domain: general
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in a real signboard/menu revision session this project has direct access to (D:/elix/temp_project_20260728/brand-data.json + its PROJECT.md client-feedback log, per UPGRADE_PLAN_20260729.md Item 4): the real project's own primary/secondary/accent color-priority system (primary = large blocks, secondary = accent/support, accent = CTA/price), a real client note asking for CTA/contact text to be enlarged relative to body text, and a real client complaint about '4 icon mo coi' (orphan icons with no thematic anchor) that were replaced with themed motifs. Fixture data in assets/ is a generic anonymized restaurant example structurally matching the real project's schema, not the real client's actual business data. v0.2.0 additionally ports concrete numeric thresholds and a color-role fallback-chain algorithm from the owner's own prior production system (real, statistically-grounded, no license issue -- rewritten clean, not blind-copied): D:/elix/archive/platform_archive/modules/presentation/scoring/design_rules.py (COLOR_RULES['max_accent_colors']=3 and the 'background is never pure white' rule + its 8 catalogued real off-white examples, sourced from 10 Canva templates, 149 Slidesgo templates / 7,854 slides / 3,526 font samples, and 8 real presentations) and D:/elix/archive/platform_archive/modules/presentation/template_intel/palette_binding.py (PaletteBinding.role()'s deterministic per-role fallback chain: secondary falls back to first accent then primary; accent falls back to secondary then primary; primary itself has no fallback and roots the whole chain)."
  version: 0.2.2
  changelog_0_2_2: "Doc-only (2026-08-07): repointed 'Chains into' section from poster-generator to html-poster-composer -- poster-generator/svg-poster-builder superseded same date (registry operational_status), content.json contract unchanged so this skill's own chain still holds. No script change."
  changelog_0_2_1: "Doc-only (2026-08-07): added a 'Chains into poster-generator' section, owner-directed after noting the design and media clusters looked disconnected -- verified real: resolved color-role hex values fed directly into a poster-generator content.json render, no conversion needed. No script change."
  grounding: not_applicable
  object_type: ["signboard", "menu"]
---

# brand-identity-linter

Mechanical checks, each traced to a real client-feedback finding or a real statistically-grounded rules corpus -- not invented design theory.

## Why this skill, and why this scope

`UPGRADE_PLAN_20260729.md` Item 4 explicitly scopes the Light Design cluster to deterministic layout/brand utilities, not aesthetic judgment. Rather than invent generic "good design" rules, every check here traces to either a real revision session on a real signboard/menu project or a real statistically-grounded rules corpus: the client asked for green promoted to primary color (color-role system already existed, just re-prioritized), asked for CTA/contact text to be bigger than body text (checked mechanically as a size comparison), and flagged 4 icons placed with no thematic connection to the brand's motif set ("orphan icons") that were replaced with icons referencing an actual declared motif (lá chuối, khói nóng, etc.) -- checked here as a motif-reference requirement. v0.2.0 adds the max-3-accent-colors and never-pure-white-background hard checks (ported from `design_rules.py`'s 10-Canva/149-Slidesgo-template statistical corpus) and upgrades the old flat "primary/secondary/accent all present" check into a deterministic RESOLUTION with a fallback chain (ported from `palette_binding.py`'s `PaletteBinding.role()`), so a caller who only declares `primary` still gets valid secondary/accent values back with the resolution path reported, instead of a bare refusal.

## Run

```bash
python scripts/validate_brand.py <brand.json>
```

Start from `assets/brand_template.json`. Exit 0 = valid, 1 = violations (all printed with the exact element/color role at fault), 2 = malformed input. On success, prints a `Color roles:` report showing each of `primary`/`secondary`/`accent`/`background` and whether it was `declared` or `resolved via fallback` (and which fallback path was taken).

### Schema

```json
{
  "colors": {
    "primary": {"hex": "#RRGGBB"},
    "secondary": {"hex": "#RRGGBB"},
    "accent": {"hex": "#RRGGBB"},
    "background": {"hex": "#RRGGBB"}
  },
  "body_font_size_pt": 14,
  "motifs": ["motif name", "..."],
  "elements": [
    {"id": "string", "type": "text", "role": "cta|contact|<anything else>", "font_size_pt": 22},
    {"id": "string", "type": "icon", "motif_ref": "must match an entry in 'motifs'"}
  ]
}
```

`colors.primary` is the only mandatory color role -- it has no fallback (every other role's fallback chain resolves back to it), so a missing/invalid primary is a hard refusal. `colors.secondary` and `colors.accent` are optional; if omitted (or invalid), they are RESOLVED via the deterministic fallback chain below and reported as `resolved via fallback` rather than causing a refusal:

- `secondary`: declared -> else first declared `accent` color -> else `primary`.
- `accent`: declared -> else `secondary` -> else `primary`. `colors.accent` accepts either a single `{"hex": ...}` object (legacy form, still supported) or a list of up to 3 `{"hex": ...}` objects -- **more than 3 accent colors is a hard refusal** (max 3, ported from `design_rules.py` COLOR_RULES, derived from 10 Canva + 149 Slidesgo templates / 7,854 slides).
- `colors.background` is optional. If declared, it must be a valid `#RRGGBB` hex AND must not be pure white (`#FFFFFF`/`#FFF`, case-insensitive) -- a hard refusal, ported from `design_rules.py`'s "background is never pure white in professional templates" rule. The error message lists 8 real catalogued off-white examples from that same source (`#F2EDE4`, `#FAF7F4`, `#FBFFEA`, `#EFEBE2`, `#FDF8F0`, `#F0F4F8`, `#F5F7F5`, `#FAF5FF`) as reference, not as an exhaustive whitelist -- any non-pure-white hex is accepted.

## What this skill does NOT do

- Does not judge color harmony, contrast/accessibility ratios, or aesthetic quality -- only that color roles resolve (declared or via fallback) to syntactically valid hex values, that accent count stays <= 3, and that background isn't pure white.
- Does not measure actual rendered pixel sizes -- `font_size_pt` is caller-declared metadata, this skill only compares the declared numbers.
- Does not detect every possible "orphan" visual element -- only icon-type elements missing/mismatching a `motif_ref` are caught; a poorly-matched-but-technically-declared motif reference isn't flagged (that's a judgment call, not a mechanical check).
- Does not render anything -- pair with `svg-poster-builder` or a real design tool for the actual visual output.
- Does not restrict `colors.background` to the 8 catalogued off-white examples -- those are real observed samples cited for guidance, not an exhaustive whitelist; only literal pure white is rejected.

## Chains into `html-poster-composer` (media cluster, verified 2026-08-07)

This skill's resolved color-role report (`primary`/`secondary`/`accent`/`background`, each a plain `#RRGGBB` hex whether declared or resolved via fallback) feeds directly into a poster-render `content.json`'s `fill`/`text.color` fields -- no conversion needed, same hex string both places. Verified real: a brand declaring only `primary`+`secondary` resolved `accent` via `fallback-to-secondary`; both resolved hex values were used as-is for 3 zone fills in a real render, producing a correctly color-consistent poster. That original verification ran against `poster-generator` (superseded 2026-08-07 by `html-poster-composer`, same `content.json` contract, unchanged by the migration) -- see `html-poster-composer`'s own `SKILL.md` for the current renderer.

## Verified

The bundled `brand_template.json` (generic anonymized restaurant fixture, structurally matching the real project's schema, using the legacy single-object `accent` form) passed clean, resolution report showing all 3 roles as `declared`. Additional cases run for v0.2.0:

- A brand with `colors.accent` declared as a 4-entry list correctly refused, naming the count and the max (3).
- A brand with `colors.background` set to `#FFFFFF` correctly refused, listing the 8 real catalogued off-white examples.
- A brand declaring only `primary`+`secondary` (no `accent`) correctly PASSED, with the resolution report showing `accent: <secondary's hex> (fallback-to-secondary)` -- not silently blank, not a refusal.
- A brand declaring only `primary` (no `secondary`, no `accent`) correctly PASSED, with both `secondary` and `accent` resolving to `primary`'s hex via `fallback-to-primary`.
- A brand missing `colors.primary` entirely correctly hard-refused (`primary is required and has no fallback`), unchanged from v0.1.0's spirit but now with the explicit "no fallback" reasoning in the error message.
- Regression: the original 5 v0.1.0 broken cases (CTA font too small, orphan icon, undeclared motif_ref, invalid hex string, etc.) re-run and still refuse identically.

## Known limitations (v0.2.0)

- Font-size emphasis check only compares declared numbers for `role: "cta"`/`"contact"` text elements against `body_font_size_pt` -- doesn't check every element pair, only the 2 roles the real client feedback specifically flagged.
- No accessibility/contrast-ratio checking (e.g. WCAG contrast between primary/accent and a background) -- out of scope, could be added if a real need surfaces.
- Motif-reference matching is exact string match, not fuzzy -- a motif declared as "lá chuối" won't match a reference typed "la chuoi" (no diacritics). Deliberate (never guess a match), same discipline as `legal-form-filler`'s exact-match checklist checking.
- The background check only rejects literal pure white; it does not attempt HSL-based "is this actually a near-white" detection (e.g. `#FEFEFE`) -- deliberate, matches the source rule's own literal `#FFFFFF` check rather than inventing a fuzziness threshold the source doesn't specify.
- `chart_series`/`status` (success/warning/danger)/`divider`/`callout_bg` role resolution from `palette_binding.py` is NOT ported -- this linter only resolves the 4 roles its own schema actually declares (primary/secondary/accent/background); the other roles belong to a rendering context this skill doesn't have (no chart/status/divider concept in a signboard/menu spec).

## Changelog

- **0.2.0** (2026-08-01): Ported real numeric thresholds/algorithm from the owner's prior production system (`design_rules.py`, `palette_binding.py`) -- see `metadata.elicited_from`. Upgraded color-role checking from flat presence/absence to deterministic RESOLUTION with a reported fallback chain; primary remains the sole mandatory role. Added max-3-accent-colors hard check. Added optional `colors.background` field with a never-pure-white hard check. `colors.accent` now also accepts a list (1-3 entries) in addition to the legacy single-object form.
- **0.1.0** (2026-07-29): Initial release, 3 mechanical checks grounded in a real signboard/menu revision session.
