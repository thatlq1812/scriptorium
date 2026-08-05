---
name: video-generator-gemini
description: 'Generates video from text and/or an anchor image using Gemini''s video model (Veo), via the user''s OWN API key -- optional, not an AI backend managed by Scriptorium. Supports text-to-video, image-to-video (the image is a fixed frame-0 anchor the model animates FROM, not a subject it redraws), image+last-frame interpolation (Veo natively interpolates motion between two given keyframes), a phrasing-based motion-intensity knob (subtle/moderate/energetic -- Veo''s API has no numeric motion-strength field), and optional synced audio generation. `extract_last_frame.py` (via `ffmpeg-bootstrap`) pulls a generated clip''s last frame back out as a PNG so a caller can chain multiple generate_video.py calls into a video longer than one Veo job supports, using each segment''s final frame as the next segment''s anchor. Use when the user already has a Gemini API key and needs to animate a still image (e.g. from `image-generator-gemini`, optionally anchored via `media-anchor-profile`) or generate a video clip from a text description. Do NOT use if the user doesn''t have their own key, and this is not a shortcut around the "Scriptorium doesn''t integrate an AI backend" principle (see `image-generator-gemini`''s SKILL.md, same reasoning applies here).'
license: MIT
compatibility: 'Requires Python 3.11+ + `google-genai` (shared venv, same package already installed for `image-generator-gemini`) + the user''s own `GEMINI_API_KEY` + (for `extract_last_frame.py` only) the `ffmpeg-bootstrap` skill installed as a sibling skill folder. Verified running clean: Claude Code, Windows (2026-08-05), real Veo API call. See "Verified" below.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in a GitHub architecture survey of 5 image-to-video repos (Stability-AI/generative-models (SVD) -- MIT; Doubiiu/DynamiCrafter, zai-org/CogVideo, guoyww/AnimateDiff -- Apache-2.0; Tencent-Hunyuan/HunyuanVideo-I2V -- Tencent Community License, technique read-only, no code/weights used), recorded in data/references/image-to-video/NOTES.md (GenVid project, 2026-08-05): image-as-fixed-frame-0 (CogVideoX's causal-VAE framing) motivated treating --image as an anchor the model animates from rather than redraws, and the dual-channel visual-anchor/motion-directive split (DynamiCrafter, SVD) motivated the --motion-intensity phrasing wrapper kept separate from the scene-description prompt. Exact API surface (client.models.generate_videos/operations.get/files.download, GenerateVideosConfig fields, and the real available model names veo-3.1-generate-preview/veo-3.1-fast-generate-preview/veo-3.1-lite-generate-preview) verified directly against the installed google-genai SDK source and a real client.models.list() call against the owner's own API key (2026-08-05) -- not guessed or copied from documentation that could be stale."
  version: 0.1.1
  changelog_0_1_1: "Stage-4 (quality-eval) Pass A run (2026-08-05) found and fixed a real contract violation: --last-frame/--image were read via .read_bytes() BEFORE the '--last-frame requires --image' validation and before checking either path exists -- a nonexistent --last-frame/--image path crashed with a raw FileNotFoundError traceback instead of the clean parser.error() the SKILL.md's own CLI already used for other invalid-argument cases. Fixed by moving both existence checks and the requires-image check before any file read. Re-verified: missing-image-with-last-frame, missing-file paths, and the valid-file case all now behave as documented (clean exit 2 for the first two, normal flow for the third)."
  grounding: not_applicable
  object_type: []
---

# video-generator-gemini

Animates a still image or generates video from text using Gemini's Veo model. The image, when given, is treated as a fixed anchor (frame 0) -- the model animates from it, per the "image-as-frame-0" pattern observed across CogVideoX/DynamiCrafter/SVD, not a subject description it's free to redraw.

## Important — doesn't contradict the "no AI backend integration" principle

Same reasoning as `image-generator-gemini`'s own SKILL.md: this is bring-your-own-key, the caller's own Gemini credentials and quota, never a Scriptorium-managed backend.

## Environment bootstrap

Same shared venv as every other Python skill here (see `skills/python-env-bootstrap/SKILL.md`):

```bash
uv pip install --python .venv -r skills/video-generator-gemini/requirements.txt
```

## Text-to-video

```bash
.venv\Scripts\python.exe skills\video-generator-gemini\scripts\generate_video.py "a neon hologram cat driving at top speed" out.mp4
```

## Image-to-video — animate an existing image, anchored

```bash
.venv\Scripts\python.exe skills\video-generator-gemini\scripts\generate_video.py "the character slowly turns its head and blinks" out.mp4 --image anchor.png --motion-intensity subtle
```

`--image` is sent as the fixed starting frame; the prompt describes what happens NEXT, not what the image already shows. `--motion-intensity` (`subtle`/`moderate`/`energetic`, default `moderate`) is a phrasing-based wrapper prepended to the prompt -- Veo's `GenerateVideosConfig` has no numeric motion-strength/motion-bucket field (checked directly against the installed SDK, 2026-08-05), so intensity is expressed through instruction wording, the same design language as `image-generator-gemini`'s `strict`/`moderate`/`loose` strength levels.

## Image + last-frame interpolation

```bash
.venv\Scripts\python.exe skills\video-generator-gemini\scripts\generate_video.py "a smooth camera pan across the room" out.mp4 --image start.png --last-frame end.png
```

Veo natively interpolates motion between two given keyframes when both `--image` (start) and `--last-frame` (end) are supplied, via `GenerateVideosConfig.last_frame`. `--last-frame` requires `--image`.

## Chaining segments into a longer video

```bash
.venv\Scripts\python.exe skills\video-generator-gemini\scripts\generate_video.py "..." segment1.mp4 --image anchor.png
.venv\Scripts\python.exe skills\video-generator-gemini\scripts\extract_last_frame.py segment1.mp4 segment1_last_frame.png
.venv\Scripts\python.exe skills\video-generator-gemini\scripts\generate_video.py "..." segment2.mp4 --image segment1_last_frame.png
```

One Veo call produces a short clip (a handful of seconds); to make a longer video, feed the previous segment's final frame back in as the next segment's `--image` -- the same "causal, frame-0" chaining idea CogVideoX uses internally, applied across separate API calls instead of within one. `extract_last_frame.py` uses `ffmpeg-bootstrap`'s `resolve_ffmpeg_path()` and a well-known `-sseof`/`-update 1` ffmpeg idiom to grab the true last decoded frame without an extra `ffprobe` call. Stitching the resulting segments into one final file is `video-assembly-composer`'s job, not this skill's.

## Other generation controls

`--duration-seconds` (must be one of `4`, `6`, `8` -- see "A real constraint found by testing" below), `--aspect-ratio` (`16:9`/`9:16`), `--resolution` (`720p`/`1080p`), `--negative-prompt`, `--seed` (reproducibility), `--generate-audio` (Veo generates synced audio directly, no separate `audio-generator-gemini` call needed for simple cases). `--poll-interval`/`--timeout` control how `generate()` waits on the async operation (Veo jobs are long-running; default polls every 10s up to 600s).

## A real constraint found by testing: duration_seconds is a DISCRETE set, not a range

Verified for real (2026-08-05, during `media-pipeline-orchestrator`'s end-to-end test): `duration_seconds=7` was rejected with `"The number value for durationSeconds is out of bound. Please provide a value between 4 and 8, inclusive."`, while `duration_seconds=6` succeeded moments earlier on an equivalent call. The error message's own wording ("between 4 and 8, inclusive") is misleading — it implies any integer in that range is valid, but 7 is rejected. `generate()`/the CLI now validate client-side against `VALID_DURATIONS_SECONDS = (4, 6, 8)` before spending an API call, rather than trusting the API's own error text. If Veo's real accepted set changes in a future model version, update this tuple after re-confirming with a real test — don't assume the API's error message is a reliable range description.

## What this skill does NOT do

- Doesn't supply/manage the API key for the user.
- Doesn't default to a permanently fixed model without flagging the risk — `DEFAULT_MODEL` (`veo-3.1-generate-preview`) is a **preview** model name as of 2026-08-05, confirmed via a real `client.models.list()` call against the owner's own API key, not from documentation. Preview models are the most likely of any model name in this project to change/be retired; verify with `--model` override or a fresh `list()` call if this skill starts returning 404s.
- Doesn't stitch multiple chained segments into one final file — see `video-assembly-composer`.
- Doesn't implement a numeric motion-strength control — Veo's config has none; see "Image-to-video" above.
- Doesn't implement the "verify output fidelity against the anchor image" idea noted in `data/references/image-to-video/NOTES.md` #5 (a DDIM-inversion-inspired consistency check) — flagged as a real idea, not built here to avoid a new dependency (perceptual-hash comparison) for a nice-to-have the core workflow doesn't strictly need yet.

## Bundled files

- `scripts/generate_video.py` — text-to-video / image-to-video / image+last-frame interpolation CLI.
- `scripts/extract_last_frame.py` — pulls a video's true last frame as PNG (ffmpeg, via `ffmpeg-bootstrap`).
- `requirements.txt` — `google-genai`.

## Verified

Real API call (2026-08-05): `client.models.list()` against the owner's own key confirmed exactly 3 video-capable models (`veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview`, all `predictLongRunning`) — the initially-assumed model name `veo-3.0-generate-001` returned a real 404 and was corrected before shipping, not left as a guess. Real image-to-video generation: fed the same cartoon-fox `character_face.png` used in `image-generator-gemini`'s tests as `--image` with `--motion-intensity subtle` and a "turn head and blink" prompt, `--duration-seconds 4` — produced a real 483KB .mp4, operation polling (submit → done) worked end-to-end. `extract_last_frame.py` run against that output correctly produced a PNG of the final frame, same character/pose held, confirming the ffmpeg extraction idiom works on a real Veo output file.

## Known limitations (v0.1.0)

- Model names are **preview** as of 2026-08-05 — the highest-risk model reference in this project for going stale. Re-run `client.models.list()` and update `DEFAULT_MODEL` if generation starts 404ing.
- `--last-frame` interpolation mode wasn't exercised in the real test above (only single-image-anchor mode was) — code-reviewed against the SDK's documented field, not independently API-verified yet.
- No automatic segment-chaining loop (submit N segments, auto-feed each last frame into the next) — `extract_last_frame.py` is a manual per-segment building block; full chaining orchestration belongs to `media-pipeline-orchestrator`.
- No anchor-fidelity verification step — see "What this skill does NOT do".
- Veo job latency (real test: roughly 1-2 minutes for a 4s clip) means a caller should expect `generate()` to block for a while; no async/background-job variant is offered here.
