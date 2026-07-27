---
name: image-generator-gemini
description: A designer toolkit using Gemini (google-genai SDK) via the user's OWN API key — optional, not an AI backend managed by Scriptorium. Not just single-image generation: supports style-anchoring (1 reference image), auto-anchor batch (an entire asset set auto-syncs its style around the first image, no sample prep needed beforehand), vision-analysis (reads an existing image, describes its style as text for reuse), and extracting a cover from an existing PDF (no AI needed, local render). Use when the user already has a Gemini API key and needs to create/analyze/extract image assets — from a single icon to a whole synced brand/cover set. Do NOT use if the user doesn't have their own key, and this is not a shortcut around the "Scriptorium doesn't integrate an AI backend" principle (see the note below).
license: MIT
compatibility: Requires Python 3.11+ + `google-genai` + `pypdfium2` (already present via `document-ai-structurer`'s transitive dependency in the shared venv — bootstrapped via `python-env-bootstrap`) + the user's own `GEMINI_API_KEY` environment variable. Verified running clean: Claude Code, Windows (2026-07-26). See "Verified" section below for real test-case detail.
metadata:
  domain: general
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in 3 of the owner's own projects: D:/elix/platform/scripts/gen/ (9 gen_*.py scripts — batch/style-chain/brand-identity/PDF-cover patterns observed via a function-signature survey), D:/UNI/S9_SP26/MLN131/project/scripts/ (gen-images-v2.mjs: batch+skip-if-exists; gen-slide-images.mjs: style-ref anchoring; gen_marketing_images.py generate_pack(): auto-anchor from the batch's first image if no style_ref is set, 'anchor'/'chained' log tag pattern). Rewrote everything from scratch in Python, generalized, dropped the parts hard-coded to GCS/DB/project-specific style-rules from the source projects."
  version: 0.3.0
---

# image-generator-gemini

A designer toolkit, not just a single-image generator: generates images, keeps a consistent style across multiple images (2 ways: manual anchor or auto-anchor), reads/describes an existing image's style, and extracts a cover from a PDF without needing AI.

## Important — doesn't contradict the "no AI backend integration" principle

`docs/specs/STRATEGY_SPEC.md` §2 says Scriptorium doesn't integrate any AI backend — that principle is about **Scriptorium itself** never sitting in the middle as a service calling an LLM on someone's behalf using Scriptorium's own credentials. This skill is different in nature: it's an instruction for the agent to call an API **using the credentials of the user actually running the skill** (bring-your-own-key), entirely optional — like a "send email via SendGrid" skill using the user's own SendGrid key. Scriptorium never issues the key, manages billing, or requires its use.

## Environment bootstrap

A SHARED venv at the repo root (see `skills/python-env-bootstrap/SKILL.md`):

```bash
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\image-generator-gemini\requirements.txt -PyVersion 3.12
```

## A single image

```bash
export GEMINI_API_KEY="your-key"   # or --api-key
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\generate_image.py "description of the image to create" output.png
```

## Manual style-anchoring — consistent style with an existing sample image

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\generate_image.py "description of the new image" output2.png --style-ref output.png
```

`--style-ref` sends the reference image along with a "STRICT style reference" instruction ahead of the main prompt — the model matches the reference image's palette/lighting/line-weight when drawing the new subject.

## Batch with auto-anchor — a whole asset set auto-syncs its style, no prior sample needed

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\generate_image.py --batch manifest.json --out-dir assets/
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

Other characteristics: **skip-if-exists** (safe when a batch fails partway through), a **rate-limit delay** between each request (default 3s, adjustable via `--delay`).

## Vision-analysis — read an existing image, describe its style as text

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\analyze_style.py reference.png
```

Returns a style description (palette, lighting, line-weight, composition — NOT a subject description) usable as a prompt prefix for a future generation, or to understand an existing brand/design system before creating new images that match it. Verified for real: accurate, detailed, matches the required structure (tested 2026-07-26).

## Extract a cover from a PDF — NO AI needed, local render

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\extract_pdf_page.py document.pdf cover.png --page 0 --scale 2.0
```

Uses `pypdfium2` (already present via `document-ai-structurer`'s dependency) to render a PDF page as PNG — no API call, no cost, no `GEMINI_API_KEY` needed. Use when a cover/thumbnail is needed from a document that ALREADY EXISTS (unlike the commands above, which CREATE NEW images from a description).

## What this skill does NOT do

- Doesn't supply/manage the API key for the user.
- Doesn't default to a permanently fixed model — update `DEFAULT_MODEL`/`DEFAULT_TEXT_MODEL` in the script if Gemini renames its models, don't let a stale model silently fail.
- Doesn't run automatically without `GEMINI_API_KEY` (except `extract_pdf_page.py`, which needs no key).
- Doesn't hard-code style-rules/brand identity for any specific project (unlike the source scripts observed, which had style-rules/GCS-upload/DB-insert hard-coded per project) — every style/output-target content is always supplied by the skill's caller, keeping the skill portable.
- Doesn't upload to cloud storage or write to a database itself — only writes local files, unlike the source pipelines tied to specific platform infrastructure.

## Bundled files

- `scripts/generate_image.py` — a 3-mode CLI (single/style-ref/batch with auto-anchor).
- `scripts/analyze_style.py` — vision-analysis, image → text style description.
- `scripts/extract_pdf_page.py` — extracts a PDF page as PNG, no AI needed.
- `scripts/batch_manifest.example.json` — a sample manifest for batch mode.

## Verified

Verified for REAL via actual API calls for all 4 capabilities: single image, batch + skip-if-exists, style-ref anchoring, vision-analysis (accurate, detailed style description), PDF-page-extraction (real PDF page render, text readable).

## Known limitations (v0.3.0)

- Model names as of writing (2026-07-26) — may change over time.
- Batch doesn't yet support automatic retry when 1 image fails within the same run — re-running the batch will auto-skip existing images and only retry the failed one.
- No "true style-chain" yet where each image chains off the image IMMEDIATELY BEFORE it (unlike the current auto-anchor, which fixes 1 anchor for the whole batch) — not yet supported if deliberate style drift across a long sequence is needed.
- Doesn't yet support brand-identity generation (logo + icon + favicon from 1 product description) as a single command — currently requires writing an equivalent batch manifest by hand.
