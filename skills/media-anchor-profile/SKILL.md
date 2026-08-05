---
name: media-anchor-profile
description: 'Defines and validates the ONE shared "anchor profile" JSON shape for keeping a character/subject (identity) and/or a visual look (style) consistent across multiple generated assets -- used by image-generator-gemini today and intended for video-generator-gemini/poster-generator so each media-generation skill doesn''t re-invent its own anchor schema. `validate_profile.py` is a deterministic, stdlib-only structural validator (non-empty profile_id, at least one of identity/style declared, each declared block has a description and/or existing reference images, strength is one of strict/moderate/loose) -- catches a typo''d reference-image path or an anchor block that constrains nothing BEFORE it burns generation-API quota. `load_profile.py` validates then resolves reference images to bytes, ready for a generator script to consume. Use when a project needs the SAME character/style anchor reused across several generation calls or several skills, instead of re-passing raw image paths/strength flags every time. Do NOT use this to generate, analyze, or edit any image/video itself -- pure schema + validator + loader, no AI call, no rendering.'
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, pathlib, argparse) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code, Windows (2026-08-05).'
metadata:
  domain: media
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Distilled from a recurring pattern across 5 style/identity-anchoring repos surveyed for image-generator-gemini's v0.4.0 upgrade (data/references/style-anchored-image/NOTES.md, GenVid project 2026-08-05): IP-Adapter/InstantID/PuLID/PhotoMaker (Apache-2.0) and ComfyUI_IPAdapter_plus (GPL-3.0, idea-only) all separate an 'identity/style anchor' concept from the per-call generation prompt, and PhotoMaker specifically stacks multiple reference images into one profile rather than using only the first. This skill factors that recurring concept into a shared, generator-agnostic schema instead of letting image-generator-gemini/video-generator-gemini/poster-generator each define their own incompatible version of the same idea -- the schema itself and its strict/moderate/loose strength vocabulary directly reuse image-generator-gemini's own v0.4.0 design (self-authored, same project, same day)."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["character-profile", "style-profile"]
---

# media-anchor-profile

A generator-agnostic schema + validator + loader for one recurring idea: "keep this character/style consistent across many generated assets." Not a generator itself -- it defines the anchor, other skills consume it.

## Why a shared skill instead of each generator skill inventing its own

`image-generator-gemini` v0.4.0 already implements identity/style anchoring with `--identity-ref`/`--style-ref` CLI flags read directly from raw file paths. That's fine for a single command, but the moment a project needs the SAME anchor (e.g. one recurring character) reused across `image-generator-gemini` calls AND a future `video-generator-gemini`/`poster-generator` call, re-typing the same paths/strengths everywhere risks drift (one call using `strict`, another `moderate`, by accident) and duplicates the "what counts as a valid anchor" logic in every skill. This skill is the single place that logic lives.

## Schema

```json
{
  "profile_id": "string, required, human-readable identifier",
  "identity": {
    "description": "string, optional free-text identity description",
    "reference_images": ["path/to/img1.png", "..."],
    "strength": "strict | moderate | loose"
  },
  "style": {
    "description": "string, optional free-text style description",
    "reference_images": ["path/to/img1.png", "..."],
    "strength": "strict | moderate | loose"
  }
}
```

Rules (enforced by `validate_profile.py`, not just documented):
- `profile_id` is required and non-empty.
- At least one of `identity`/`style` must be declared -- an anchor profile with neither anchors nothing.
- Each declared block must have a non-empty `description` and/or a non-empty `reference_images` list -- an anchor block with neither is invalid (it would silently do nothing).
- Every path in `reference_images` is resolved relative to the profile file's own directory (or used as-is if absolute) and must exist on disk -- a typo'd path is a validation error, not a silent skip.
- `strength` defaults to `moderate` if omitted, must be one of `strict`/`moderate`/`loose` if present. This 3-level vocabulary is a deliberate choice, not a placeholder for "later add a numeric scale" -- see `image-generator-gemini`'s own `SKILL.md` Known Limitations: Gemini's prompt-only image API has no equivalent to a diffusion adapter's numeric `ip_adapter_scale`, so strength is instruction-phrasing intensity by design, not a value scriptorium has any way to make continuous.
- Unknown top-level or per-block keys are flagged (catches a typo like `"stregth"` instead of silently ignoring it).

See `assets/example_profile.json` for a filled-in example (identity + style both declared).

## Validate a profile

```bash
python skills/media-anchor-profile/scripts/validate_profile.py my_profile.json
```

Exit 0 + `OK: ...` if valid. Exit 1 + a bulleted list of every error found (not just the first) if not.

## Load a profile for a generator script to consume

```python
import sys
sys.path.insert(0, "skills/media-anchor-profile/scripts")
from load_profile import load_anchor_profile

profile = load_anchor_profile("my_profile.json")
# profile["identity"]["reference_image_bytes"] -> list[bytes] (already read from disk)
# profile["identity"]["description"]           -> str | None
# profile["identity"]["strength"]               -> "strict" | "moderate" | "loose"
# profile["style"]                              -> same shape, or None if not declared
```

`load_anchor_profile()` validates first (raises `ValueError` with the full error list on an invalid profile -- never partially loads a broken one), then reads every declared reference image into bytes. `image-generator-gemini` v0.4.1 consumes this directly via its `--anchor-profile` flag (see that skill's `SKILL.md`) instead of requiring raw `--identity-ref`/`--style-ref` flags to be re-typed.

## What this skill does NOT do

- Does not generate, analyze, edit, or render any image/video/audio itself -- schema + validator + loader only.
- Does not call any LLM/AI API, ever -- pure local JSON/file validation.
- Does not decide what strength level or description text is "correct" for a given use case -- that's always a human/caller decision; this skill only checks the profile is structurally well-formed.
- Does not migrate or convert `image-generator-gemini`'s pre-v0.4.1 raw `--identity-ref`/`--style-ref` flags into a profile automatically -- both remain valid, independent input modes on that skill.

## Bundled files

- `scripts/validate_profile.py` -- CLI + importable `validate_anchor_profile()`.
- `scripts/load_profile.py` -- CLI + importable `load_anchor_profile()` (validates, then resolves images to bytes).
- `assets/example_profile.json` -- a filled-in example (identity + style, matching the fox character used in `image-generator-gemini`'s own real API test).

## Verified

Real run against `assets/example_profile.json` (paths adjusted to point at the actual `character_face.png`/`style_sample.png` generated during `image-generator-gemini`'s v0.4.0 test, `data/test_output/`): `validate_profile.py` reported `OK`. Deliberately-broken variants each correctly rejected with the right error: missing `profile_id` (flagged), a `reference_images` entry pointing at a nonexistent file (flagged with the resolved path), `strength: "extreme"` (flagged, not silently accepted), an `identity` block with neither `description` nor `reference_images` (flagged as anchoring nothing), an unknown top-level key `"style_ref"` (typo for `style`, flagged rather than silently ignored). `load_anchor_profile()` correctly raised `ValueError` with the full error list on the same broken variants instead of partially loading them, and correctly returned resolved bytes + strength + description on the valid profile. Integration-tested end-to-end through `image-generator-gemini --anchor-profile` (see that skill's `SKILL.md` Verified section) -- real Gemini API call, correct identity+style anchoring from a profile file instead of raw flags.

## Known limitations (v0.1.0)

- Only `image-generator-gemini` consumes this schema so far (`video-generator-gemini`/`poster-generator` don't exist yet as of this writing) -- the schema is designed to generalize to them but hasn't been proven against a second consumer yet.
- `image-generator-gemini`'s batch mode (`--batch manifest.json`) does not yet accept `--anchor-profile` -- it has its own equivalent inline `identity_ref`/`style_ref`/`*_strength` manifest fields instead. Unifying batch mode onto this schema is a future option, not done here to avoid changing a working, already-tested batch format without a real need.
- No versioning field on the profile schema itself -- if the schema needs a breaking change later, existing profile files won't self-declare which version they were written against.
