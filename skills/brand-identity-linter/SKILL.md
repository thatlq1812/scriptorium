---
name: brand-identity-linter
description: Signboard/menu brand-identity structural linter. `validate_brand.py` checks 3 things grounded in a real signboard/menu revision session: (1) a primary/secondary/accent color-role system is fully declared with valid hex values, (2) any element flagged role "cta"/"contact" has a font size at or above the declared body font size (emphasis discipline), (3) every icon element references a declared motif, catching "orphan icons" placed with no thematic anchor. Use when reviewing a signboard/menu/banner's declared color-and-typography spec before final render. Do NOT use this to judge subjective aesthetic quality -- it only checks the 3 mechanical rules above, never a holistic design opinion.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, re, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).
metadata:
  domain: general
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in a real signboard/menu revision session this project has direct access to (D:/elix/temp_project_20260728/brand-data.json + its PROJECT.md client-feedback log, per UPGRADE_PLAN_20260729.md Item 4): the real project's own primary/secondary/accent color-priority system (primary = large blocks, secondary = accent/support, accent = CTA/price), a real client note asking for CTA/contact text to be enlarged relative to body text, and a real client complaint about '4 icon mo coi' (orphan icons with no thematic anchor) that were replaced with themed motifs. Fixture data in assets/ is a generic anonymized restaurant example structurally matching the real project's schema, not the real client's actual business data."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["signboard", "menu"]
---

# brand-identity-linter

3 mechanical checks, each traced to a real client-feedback finding, not invented design theory.

## Why this skill, and why this scope

`UPGRADE_PLAN_20260729.md` Item 4 explicitly scopes the Light Design cluster to deterministic layout/brand utilities, not aesthetic judgment. Rather than invent generic "good design" rules, all 3 checks here trace to a real revision session on a real signboard/menu project: the client asked for green promoted to primary color (color-role system already existed, just re-prioritized -- this skill checks the role system is complete and valid, not which color is "better"), asked for CTA/contact text to be bigger than body text (checked mechanically as a size comparison), and flagged 4 icons placed with no thematic connection to the brand's motif set ("orphan icons") that were replaced with icons referencing an actual declared motif (lá chuối, khói nóng, etc.) -- checked here as a motif-reference requirement.

## Run

```bash
python scripts/validate_brand.py <brand.json>
```

Start from `assets/brand_template.json`. Exit 0 = valid, 1 = violations (all printed with the exact element/color role at fault), 2 = malformed input.

### Schema

```json
{
  "colors": {"primary": {"hex": "#RRGGBB"}, "secondary": {"hex": "#RRGGBB"}, "accent": {"hex": "#RRGGBB"}},
  "body_font_size_pt": 14,
  "motifs": ["motif name", "..."],
  "elements": [
    {"id": "string", "type": "text", "role": "cta|contact|<anything else>", "font_size_pt": 22},
    {"id": "string", "type": "icon", "motif_ref": "must match an entry in 'motifs'"}
  ]
}
```

## What this skill does NOT do

- Does not judge color harmony, contrast/accessibility ratios, or aesthetic quality -- only that the primary/secondary/accent roles are declared with syntactically valid hex values.
- Does not measure actual rendered pixel sizes -- `font_size_pt` is caller-declared metadata, this skill only compares the declared numbers.
- Does not detect every possible "orphan" visual element -- only icon-type elements missing/mismatching a `motif_ref` are caught; a poorly-matched-but-technically-declared motif reference isn't flagged (that's a judgment call, not a mechanical check).
- Does not render anything -- pair with `svg-poster-builder` or a real design tool for the actual visual output.

## Verified

The bundled `brand_template.json` (generic anonymized restaurant fixture, structurally matching the real project's schema) passed clean. 5 deliberately broken cases: a CTA element with `font_size_pt` below `body_font_size_pt` correctly refused, naming the exact values; an icon missing `motif_ref` correctly flagged as an orphan icon; an icon's `motif_ref` pointing at an undeclared motif correctly refused; a brand missing the `accent` color role correctly refused; an invalid hex value (`"green"` instead of `#RRGGBB`) correctly refused.

## Known limitations (v0.1.0)

- Font-size emphasis check only compares declared numbers for `role: "cta"`/`"contact"` text elements against `body_font_size_pt` -- doesn't check every element pair, only the 2 roles the real client feedback specifically flagged.
- No accessibility/contrast-ratio checking (e.g. WCAG contrast between primary/accent and a background) -- out of scope for v0.1.0, could be added if a real need surfaces.
- Motif-reference matching is exact string match, not fuzzy -- a motif declared as "lá chuối" won't match a reference typed "la chuoi" (no diacritics). Deliberate (never guess a match), same discipline as `legal-form-filler`'s exact-match checklist checking.
