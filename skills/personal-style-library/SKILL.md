---
name: personal-style-library
description: Local-only personal catalog of reusable creative reference data -- 4 categories (palettes, styles, motifs, fonts), one JSON entry per named item, under `personal/style_library/` (gitignored, like personal-profile-manager). `init_library.py` scaffolds the 4 folders. `validate_library.py` checks every entry, reusing brand-identity-linter's color-role resolution for `palettes/` and media-anchor-profile's anchor-block rules for `styles/` (never duplicated). `extract_palette.py` proposes ranked color swatches from a real image via deterministic pixel quantization -- role assignment stays a human/agent call, never guessed. `export_anchor_profile.py` composes a `styles/` entry into a valid media-anchor-profile anchor profile, re-validated against that skill's own validator before writing. Use to remember and reuse a palette/style/motif-set/font-pairing across future projects instead of re-declaring it each time. Do NOT use to generate, analyze, or edit any image -- catalog + pixel-extraction only, no AI call.
license: MIT
compatibility: 'Requires Python 3.11+ + Pillow (extract_palette.py only -- init_library.py/validate_library.py/export_anchor_profile.py are stdlib-only) + the brand-identity-linter and media-anchor-profile skills installed as sibling skill folders (reused for validation, never duplicated). Zero network calls. Verified running clean: Claude Code, Windows (2026-08-07).'
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner direction 2026-08-07 (PROJECT.md item 4): a personal store for color palettes and style samples, later reusable as 'generate a poster with this content, this style, that color'. Category taxonomy beyond the owner's original 2 (palettes, styles) was delegated to this session's own research (\"nhiều cái khác, bạn sẽ nghiên cứu và bổ sung\") -- grounded in: (1) the W3C Design Tokens Community Group (DTCG) JSON format, the real public standard for named/typed color+typography tokens adopted by Figma Variables/Style Dictionary/Tokens Studio (web-surveyed 2026-08-07, informs the 'named reusable reference data' framing generally, though the actual palettes/ schema reuses brand-identity-linter's own primary/secondary/accent/background shape directly rather than DTCG's generic token array, since that composes with an already-verified skill in this registry instead of introducing an unrelated shape); (2) this registry's own already-elicited schemas, extended rather than re-invented -- palettes/ reuses brand-identity-linter's color-role schema verbatim (that skill's own elicited_from remains the real source: a real signboard/menu client project + design_rules.py's 10-Canva/149-Slidesgo statistical corpus), styles/ reuses media-anchor-profile's style-anchor-block schema verbatim (that skill's own elicited_from: IP-Adapter/InstantID/PuLID/PhotoMaker's identity/style-anchor concept), motifs/ generalizes brand-identity-linter's per-brand 'motifs' list field into a reusable named catalog, fonts/ is a lighter, non-safety-checked companion to light-logo-arranger's font_fallback_map.json (a pairing memory, not a system-font-safety table -- that check still belongs to resolve_font_fallback.py, deliberately not duplicated here). extract_palette.py's dominant-color-via-pixel-quantization technique is a standard, publicly documented CS approach (web-surveyed 2026-08-07: color-quantization/color-extraction tooling is a well-established public category), implemented here via Pillow's own built-in adaptive quantization, not adapted from any specific external repo's code."
  version: 0.1.1
  changelog_0_1_1: "Doc-only (2026-08-07): repointed poster-generator references to html-poster-composer -- poster-generator/svg-poster-builder superseded same date (registry operational_status), content.json contract unchanged so this skill's own chain still holds. No script change."
  grounding: not_applicable
  object_type: ["color-palette", "style-profile", "motif-set", "font-pairing"]
---

# personal-style-library

A personal catalog, not a generator: remembers color palettes, visual styles, motif sets, and font pairings across projects so they don't have to be re-declared (or re-described from memory, drifting slightly each time) every time a new poster/brand/design project starts.

## Why this skill, and why this scope

Two skills already validate structured creative data for a SINGLE project at a time: `brand-identity-linter` (color roles + motifs for one signboard/menu) and `media-anchor-profile` (identity/style anchor for one generation call). Neither persists anything between runs -- each run's input is exactly what the caller declares that run. The real gap: a user doing many creative projects over time (see `project-workspace-initializer`'s new `brand-design-project`/`media-content-creator` templates) has real, reusable preferences -- "this palette", "this watercolor style", "this motif set" -- that currently have nowhere to live except being retyped or re-described from memory each time. This skill is that one place, deliberately built on top of the 2 existing schemas rather than inventing new ones (see `metadata.elicited_from`).

## Directory layout

```
personal/style_library/
  palettes/<palette_id>.json
  styles/<style_id>.json
  motifs/<motif_set_id>.json
  fonts/<font_pairing_id>.json
```

Lives under `personal/` at the repo root -- already gitignored by convention (see `personal-profile-manager`'s own "Privacy" note), so real personal creative data never gets committed.

## Run

### 1. Initialize the library (once)

```bash
python scripts/init_library.py <personal_dir> [--force]
```

Creates `<personal_dir>/style_library/{palettes,styles,motifs,fonts}/`, all empty -- no seed content, since every real entry is the caller's own reference material. Refuses (exit 1) if `style_library/` already exists, unless `--force` (existing entries are never touched either way).

### 2. Add an entry

No dedicated "add" script -- each entry is a small, hand-writable JSON file (see `assets/example_*.json` for a filled-in example of each category). Write it directly into the matching category folder, named `<id>.json`.

**`palettes/<id>.json`** -- reuses `brand-identity-linter`'s own color schema verbatim:
```json
{"palette_id": "string, required", "colors": {"primary": {"hex": "#RRGGBB"}, "secondary": {"hex": "#RRGGBB"}}, "source": "declared | extracted_from_image", "source_image": "path, required if source is extracted_from_image", "notes": "optional"}
```
`secondary`/`accent`/`background` resolve via the same fallback chain `brand-identity-linter` uses (see that skill's `SKILL.md`) -- only `primary` is mandatory.

**`styles/<id>.json`** -- reuses `media-anchor-profile`'s own style-anchor-block schema verbatim:
```json
{"style_id": "string, required", "description": "string, optional", "reference_images": ["path", "..."], "strength": "strict | moderate | loose"}
```
Must have a non-empty `description` and/or a non-empty `reference_images` list (an entry with neither anchors nothing).

**`motifs/<id>.json`**:
```json
{"motif_set_id": "string, required", "motifs": ["string", "..."], "notes": "optional"}
```

**`fonts/<id>.json`**:
```json
{"font_pairing_id": "string, required", "heading_font": "string, required", "body_font": "string, required", "notes": "optional"}
```
This only remembers a pairing you like -- it does NOT check system-font safety. Run `light-logo-arranger`'s `resolve_font_fallback.py` on `heading_font`/`body_font` separately before trusting either is safe to use as-is.

### 3. Validate

```bash
python scripts/validate_library.py <style_library_dir> [--category palettes|styles|motifs|fonts]
```

Checks every `*.json` entry in every category (or just one, via `--category`). Reuses `brand-identity-linter`'s `resolve_colors()` for `palettes/` and `media-anchor-profile`'s `_validate_anchor_block()` for `styles/` directly (cross-skill import, same reuse-not-duplicate discipline this registry applies wherever one skill's validator is another's authoritative source) -- never a second, drifting copy of those rules. Exit 0 = all valid (prints a per-category count), 1 = one or more entries invalid or a required sibling skill isn't installed (all errors printed), 2 = `style_library_dir` itself doesn't exist.

### 4. Extract a palette from a real image (optional, before writing a palette entry)

```bash
python scripts/extract_palette.py <image_path> -o swatches.json [--colors N]
```

Real, deterministic pixel quantization (Pillow's adaptive method) -- ranks the image's actual dominant colors by pixel share, `N` defaults to 6. Output is UNASSIGNED swatches (`hex` + `pixel_share_pct`), never a guessed role -- a script has no way to know which extracted color the caller intends as "primary" vs "accent"; look at the image, pick roles, then hand-write the `palettes/<id>.json` entry using the real extracted hex values. Same "script proposes, agent decides" discipline this project applies elsewhere (e.g. `document-ai-structurer`'s catalog step).

### 5. Export a style entry for one generation call

```bash
python scripts/export_anchor_profile.py <styles/id.json> <profile_id> -o anchor_profile.json
```

Composes a library `styles/` entry into a `media-anchor-profile`-shaped anchor profile (`{"profile_id": ..., "style": {...}}`), then validates the RESULT against that skill's own `validate_anchor_profile()` before writing -- never assumed valid just because the source entry passed `validate_library.py` (a moved/deleted `reference_images` path since the entry was last validated is caught here). Feed the output directly to `image-generator-gemini --anchor-profile` (see that skill's `SKILL.md`).

## Chains into (verified 2026-08-07)

```
extract_palette.py (optional) ──> hand-written palettes/<id>.json ──┐
                                                                      ├──> brand-identity-linter (validate/resolve) ──> html-poster-composer content.json fills
                                   hand-written styles/<id>.json ────┤
                                                                      └──> export_anchor_profile.py ──> image-generator-gemini --anchor-profile ──> html-poster-composer image zones
                                   hand-written motifs/<id>.json ──────> brand-identity-linter's per-brand 'motifs' declaration
                                   hand-written fonts/<id>.json ───────> light-logo-arranger's resolve_font_fallback.py (safety check, separate step)
```

Real end-to-end verified this session: `extract_palette.py` run against a real PNG (5 real dominant colors extracted, e.g. `#F9D0C4` at 25.72% pixel share); a hand-written `styles/watercolor-adventure-poster.json` entry exported via `export_anchor_profile.py` into a `profile_id`-stamped anchor profile, then independently re-validated clean by `media-anchor-profile`'s own `validate_profile.py` run directly (not just trusted from this skill's own check); a deliberately broken style entry (a `reference_images` path pointing nowhere) correctly refused at export time, naming the missing file. `palettes/`/`motifs/`/`fonts/` category validation exercised against both the bundled valid examples and a broken variant of each (missing `primary`, invalid `strength`, empty `motifs` list, missing `body_font`) -- all correctly accepted/refused.

## What this skill does NOT do

- Does not generate, analyze, or edit any image, video, or audio -- pure local JSON catalog + one deterministic pixel-extraction helper (`extract_palette.py`), no AI/LLM call anywhere in this skill.
- Does not assign semantic roles (primary/secondary/accent) to extracted colors -- `extract_palette.py` only ranks by pixel share; role assignment is always a human/agent decision made by looking at the image.
- Does not duplicate `brand-identity-linter`'s color-resolution rules or `media-anchor-profile`'s anchor-block rules -- both are imported directly from those skills, so this catalog's validation can never silently drift from theirs.
- Does not check font system-safety -- `fonts/` entries are a preference memory only; safety resolution stays `light-logo-arranger`'s `resolve_font_fallback.py` job.
- Does not track which entry was used on which project, or version/diff entries over time -- each entry is a flat JSON file the caller edits directly; no history, no state beyond the filesystem.
- Does not migrate or convert entries automatically if `brand-identity-linter`/`media-anchor-profile`'s own schemas change later -- both are read at validation time via live cross-skill import, so a schema change there is visible here immediately, but no entry is auto-rewritten.

## Known limitations (v0.1.0)

- No "add"/"list"/"search" convenience script -- entries are small enough to hand-write and `ls`/`grep` directly; a catalog-management CLI can be added later if a real need for one surfaces with real usage.
- `extract_palette.py`'s quantization is whole-image, not region-aware -- a photo with a small but visually important accent area may not surface it if it covers few pixels; `--colors N` (raise it) is the only current lever.
- `fonts/` pairings are not cross-checked against each other for legibility/contrast -- purely a name-pairing memory, no typographic judgment.
- The 4-category taxonomy (palettes/styles/motifs/fonts) reflects this session's own research into what's reusable across this registry's existing design/media skills -- not a formal design-system survey; extend with a 5th category only when a real recurring need for one surfaces (e.g. layout templates), not preemptively.
