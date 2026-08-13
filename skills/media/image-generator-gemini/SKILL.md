---
name: image-generator-gemini
description: 'A designer toolkit using Gemini (google-genai SDK) via the user''s OWN API key — optional, not an AI backend managed by Scriptorium. Not just single-image generation: supports INDEPENDENT identity-anchoring and style-anchoring (each with its own strength level and multi-image stacking), auto-anchor batch (an entire asset set auto-syncs its style around the first image, no sample prep needed beforehand), vision-analysis (reads an existing image, describes its style as text for reuse), and extracting a cover from an existing PDF (no AI needed, local render). Use when the user already has a Gemini API key and needs to create/analyze/extract image assets — from a single icon to a whole synced brand/cover set, or a consistent character across many scenes. Do NOT use if the user doesn''t have their own key, and this is not a shortcut around the "Scriptorium doesn''t integrate an AI backend" principle (see the note below).'
license: MIT
compatibility: 'Requires Python 3.11+ + `google-genai` + `pypdfium2` (already present via `document-ai-structurer`''s transitive dependency in the shared venv — bootstrapped via `toolchain-bootstrap`) + the user''s own `GEMINI_API_KEY` environment variable. Verified running clean: Claude Code, Windows (2026-07-26, re-verified 2026-08-05 for the identity/style-separation upgrade). See "Verified" section below for real test-case detail.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in 3 of the owner's own projects: D:/elix/platform/scripts/gen/ (9 gen_*.py scripts — batch/style-chain/brand-identity/PDF-cover patterns observed via a function-signature survey), D:/UNI/S9_SP26/MLN131/project/scripts/ (gen-images-v2.mjs: batch+skip-if-exists; gen-slide-images.mjs: style-ref anchoring; gen_marketing_images.py generate_pack(): auto-anchor from the batch's first image if no style_ref is set, 'anchor'/'chained' log tag pattern). Rewrote everything from scratch in Python, generalized, dropped the parts hard-coded to GCS/DB/project-specific style-rules from the source projects. v0.4.0 upgrade (2026-08-05, GenVid project) additionally grounded in a GitHub architecture survey of 5 diffusion-adapter repos (IP-Adapter, InstantID, PhotoMaker, PuLID — Apache-2.0; ComfyUI_IPAdapter_plus — GPL-3.0, idea-only, no code copied), recorded in data/references/style-anchored-image/NOTES.md: decoupled identity/style channels (IP-Adapter/InstantID), multi-image stacking (PhotoMaker), and the 'preserve identity, don't suppress pose/scene changes' principle (PuLID)."
  version: 0.4.2
  changelog_0_4_2: "Stage-4 (quality-eval) Pass A run (2026-08-05) found and fixed 2 real contract violations in extract_pdf_page.py: a corrupt/unreadable PDF and an out-of-range --page index both crashed with a raw Python traceback instead of failing cleanly (CLAUDE.md's project-wide refuse-loudly-with-a-clear-message discipline, not a literal SKILL.md claim, but the same standard every other script in this skill already met). Fixed with 2 targeted except clauses (pdfium.PdfiumError, ValueError) around the extract() call -- re-verified both cases now exit 1 with a one-line message, valid-page extraction unaffected."
  changelog_0_4_1: "Added --anchor-profile, consuming the new media-anchor-profile skill's shared JSON schema as an alternative to raw --identity-ref/--style-ref flags (mutually exclusive with them). generate()/the instruction builders now also accept an optional identity_description/style_description string, usable with zero reference images (anchor by text alone) or alongside them -- required to fully honor media-anchor-profile's schema, which allows a block to have a description and/or reference images. Real API test (2026-08-05): --anchor-profile pointing at media-anchor-profile's example_profile.json (same fox identity + watercolor style used in the 0.4.0 test) produced a new action pose (surfing a wave) with both identity and style correctly held -- confirms the profile-file path produces the same result as the equivalent raw flags."
  changelog_0_4_0: "Split the single --style-ref channel into two INDEPENDENT channels: --identity-ref (face/character features) and --style-ref (palette/lighting/rendering), each with its own --identity-strength/--style-strength (strict/moderate/loose, phrasing-based since Gemini's prompt-only API has no numeric conditioning-scale equivalent) and multi-image stacking (repeatable flags). Batch manifest gained identity_ref/identity_strength/style_strength fields. Real API test (2026-08-05): identity-ref (strict) + style-ref (moderate) combined correctly preserved the reference character's palette/face/tail while freely changing pose (portrait -> running side-view) and rendering style (flat design -> watercolor) per the new prompt -- see batch_manifest_identity.example.json."
---

# image-generator-gemini

A designer toolkit, not just a single-image generator: generates images, keeps a consistent IDENTITY and/or STYLE across multiple images (as two independent, combinable channels), reads/describes an existing image's style, and extracts a cover from a PDF without needing AI.

## Important — doesn't contradict the "no AI backend integration" principle

`docs/specs/STRATEGY_SPEC.md` §2 says Scriptorium doesn't integrate any AI backend — that principle is about **Scriptorium itself** never sitting in the middle as a service calling an LLM on someone's behalf using Scriptorium's own credentials. This skill is different in nature: it's an instruction for the agent to call an API **using the credentials of the user actually running the skill** (bring-your-own-key), entirely optional — like a "send email via SendGrid" skill using the user's own SendGrid key. Scriptorium never issues the key, manages billing, or requires its use.

## Environment bootstrap

A SHARED venv at the repo root (see `skills/general/toolchain-bootstrap/SKILL.md`):

```bash
.\skills\general\toolchain-bootstrap\scripts\bootstrap.ps1 -Requirements skills\media\image-generator-gemini\requirements.txt -PyVersion 3.12
```

## A single image

```bash
export GEMINI_API_KEY="your-key"   # or --api-key
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\generate_image.py "description of the image to create" output.png
```

## Manual style-anchoring — consistent style with an existing sample image

```bash
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\generate_image.py "description of the new image" output2.png --style-ref output.png --style-strength moderate
```

`--style-ref` sends the reference image along with a style-matching instruction ahead of the main prompt — the model matches the reference image's palette/lighting/line-weight when drawing the new subject. `--style-strength` (`strict`/`moderate`/`loose`, default `moderate`) controls how literally phrased that instruction is — Gemini's prompt-only API has no numeric conditioning-scale knob (unlike a diffusion adapter's `ip_adapter_scale`), so "strength" here is instruction-phrasing intensity, not a continuous value. Repeat `--style-ref` to stack multiple sample images into one unified style (their common palette/lighting/technique, not just the first image's).

## Identity-anchoring — keep a character/subject consistent while everything else changes

```bash
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\generate_image.py "the same character, now running through a forest, side view" output3.png --identity-ref character_face.png --identity-strength strict
```

`--identity-ref` is an INDEPENDENT channel from `--style-ref` — it preserves face/character features (shape, hair, distinctive markings) while explicitly telling the model it's free to change pose, camera angle, background, and composition to match the new prompt (it does NOT copy the reference image's pose unless asked to). Combine both channels for "same character, new pose, new art style":

```bash
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\generate_image.py "..." out.png --identity-ref character_face.png --identity-strength strict --style-ref watercolor_sample.png --style-strength moderate
```

Verified for real (2026-08-05): with a flat-design cartoon fox as `--identity-ref` (strict) and a watercolor lighthouse as `--style-ref` (moderate), the output correctly kept the fox's palette/face/tail while switching to a running side-view pose and a watercolor rendering style — identity held, pose and style both changed as instructed, not copied from either reference image. Repeat `--identity-ref` to stack multiple photos/angles of the same subject into one identity (PhotoMaker's multi-image stacking pattern — averages out a single photo's noise/angle bias).

## Anchor by a shared profile file instead of raw flags

```bash
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\generate_image.py "the character surfing a giant wave" out.png --anchor-profile hero.json
```

`--anchor-profile` reads a `media-anchor-profile` JSON file (see `skills/media/media-anchor-profile/SKILL.md`) instead of requiring `--identity-ref`/`--style-ref`/`--identity-strength`/`--style-strength` to be re-typed on every call — the two are mutually exclusive. Use this when the same identity/style anchor needs reusing across several generation calls (or, in the future, other media-generation skills consuming the same profile). A profile block may anchor by `description` text alone, `reference_images` alone, or both — verified for real (2026-08-05): `--anchor-profile` against `media-anchor-profile`'s own example (the same fox identity + watercolor style) produced a new action pose (surfing) with both correctly held, matching the equivalent raw-flags result.

## Batch with auto-anchor — a whole asset set auto-syncs its style, no prior sample needed

```bash
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\generate_image.py --batch manifest.json --out-dir assets/
```

`manifest.json` (see `scripts/batch_manifest.example.json`):
```json
{
  "style_ref": "path/to/reference.png or null",
  "images": {
    "file-name-1.png": "prompt for image 1",
    "file-name-2.png": "prompt for image 2"
  }
}
```

If `style_ref` is **null**: **auto-anchor** — the FIRST image generated in the batch automatically becomes the style reference for EVERY image after it (a pattern observed for real in the MLN131 project's `generate_pack()` — log tag "(anchor)" for the first image, "(chained)" for the rest). No need to prepare a sample image beforehand — the whole set auto-syncs around the first item. If a partial batch is re-run, an already-existing (skipped) image is also used as the anchor, preserving consistency across runs.

A batch can ALSO fix an `identity_ref` (single path or list of paths) for the whole run — unlike `style_ref`, identity is never auto-derived from a generated image, since it's something the caller deliberately supplies (a real reference photo/character sheet), not something to infer from the batch's own output. See `scripts/batch_manifest_identity.example.json` for a character-consistent multi-scene batch (fixed `identity_ref`, `null` `style_ref` for auto-anchored style). Optional top-level `identity_strength`/`style_strength` (`strict`/`moderate`/`loose`, default `moderate`) apply to every image in the batch.

Other characteristics: **skip-if-exists** (safe when a batch fails partway through), a **rate-limit delay** between each request (default 3s, adjustable via `--delay`).

## Vision-analysis — read an existing image, describe its style as text

```bash
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\analyze_style.py reference.png
```

Returns a style description (palette, lighting, line-weight, composition — NOT a subject description) usable as a prompt prefix for a future generation, or to understand an existing brand/design system before creating new images that match it. Verified for real: accurate, detailed, matches the required structure (tested 2026-07-26).

## Extract a cover from a PDF — NO AI needed, local render

```bash
.venv\Scripts\python.exe skills\media\image-generator-gemini\scripts\extract_pdf_page.py document.pdf cover.png --page 0 --scale 2.0
```

Uses `pypdfium2` (already present via `document-ai-structurer`'s dependency) to render a PDF page as PNG — no API call, no cost, no `GEMINI_API_KEY` needed. Use when a cover/thumbnail is needed from a document that ALREADY EXISTS (unlike the commands above, which CREATE NEW images from a description).

## What this skill does NOT do

- Doesn't supply/manage the API key for the user.
- Doesn't default to a permanently fixed model — update `DEFAULT_MODEL`/`DEFAULT_TEXT_MODEL` in the script if Gemini renames its models, don't let a stale model silently fail.
- Doesn't run automatically without `GEMINI_API_KEY` (except `extract_pdf_page.py`, which needs no key).
- Doesn't hard-code style-rules/brand identity for any specific project (unlike the source scripts observed, which had style-rules/GCS-upload/DB-insert hard-coded per project) — every style/output-target content is always supplied by the skill's caller, keeping the skill portable.
- Doesn't upload to cloud storage or write to a database itself — only writes local files, unlike the source pipelines tied to specific platform infrastructure.

## Bundled files

- `scripts/generate_image.py` — a 3-mode CLI (single/identity+style-ref/batch with auto-anchor), identity and style as independent channels.
- `scripts/analyze_style.py` — vision-analysis, image → text style description.
- `scripts/extract_pdf_page.py` — extracts a PDF page as PNG, no AI needed.
- `scripts/batch_manifest.example.json` — a sample manifest for batch mode (style-only, auto-anchor).
- `scripts/batch_manifest_identity.example.json` — a sample manifest combining a fixed `identity_ref` (character consistency) with auto-anchored `style_ref` across multiple scenes.

## Verified

Verified for REAL via actual API calls for all core capabilities: single image, batch + skip-if-exists, style-ref anchoring, vision-analysis (accurate, detailed style description), PDF-page-extraction (real PDF page render, text readable). v0.4.0 identity/style separation additionally verified for real (2026-08-05): combined `--identity-ref` (strict) + `--style-ref` (moderate) call correctly preserved the reference character across a pose change (portrait -> running side-view) and a style change (flat design -> watercolor) simultaneously — confirming the decoupled-channel design actually works through Gemini's prompt-only API, not just diffusion adapters with dedicated conditioning inputs. Also verified with a fixed `identity_ref` + `null` (auto-anchor) `style_ref` batch across 2 further scenes (park bench reading, jumping a rain puddle) — same character held recognizably across all 4 total generated images in this test run, in a consistent auto-anchored illustration style. v0.4.1 `--anchor-profile` verified for real (2026-08-05): same result as the equivalent raw flags, loading identity+style from `media-anchor-profile`'s example JSON file instead.

## Known limitations (v0.4.1)

- Model names as of writing (2026-07-26) — may change over time.
- "Strength" is instruction-phrasing intensity (`strict`/`moderate`/`loose`), not a continuous numeric scale — Gemini's image API exposes no equivalent to a diffusion adapter's `ip_adapter_scale`/`conditioning_scale`. A caller needing finer control than 3 discrete levels has no lever here yet.
- Batch doesn't yet support automatic retry when 1 image fails within the same run — re-running the batch will auto-skip existing images and only retry the failed one.
- No "true style-chain" yet where each image chains off the image IMMEDIATELY BEFORE it (unlike the current auto-anchor, which fixes 1 anchor for the whole batch) — not yet supported if deliberate style drift across a long sequence is needed.
- Doesn't yet support brand-identity generation (logo + icon + favicon from 1 product description) as a single command — currently requires writing an equivalent batch manifest by hand.
- `--anchor-profile` is only wired into the single-image CLI path, not batch mode (`--batch`) — batch mode keeps its own inline `identity_ref`/`style_ref`/`*_strength` manifest fields, a deliberate scope boundary (see `media-anchor-profile`'s own Known Limitations).
