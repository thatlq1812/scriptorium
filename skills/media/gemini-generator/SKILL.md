---
name: gemini-generator
description: 'A media-generation toolkit using Gemini (google-genai SDK) via the user''s OWN API key -- optional, not an AI backend managed by Scriptorium. Covers 3 modalities: IMAGE (single/batch generation, independent identity+style anchoring with multi-image stacking, auto-anchor batches, vision-analysis of an existing image''s style, PDF-page cover extraction needing no AI), VIDEO (text-to-video and image-to-video via Veo, two-keyframe interpolation, phrasing-based motion-intensity, last-frame extraction for chaining longer clips), and AUDIO (Gemini TTS -- single-voice narration, 2-speaker dialogue, voice cloning gated on mandatory recorded consent, never a bare override). Use whenever the user has a Gemini API key and needs to create or analyze image/video/audio assets. Do NOT use if the user lacks their own key -- not a shortcut around the "no AI backend" principle (see the note below).'
license: MIT
compatibility: 'Requires Python 3.11+ + `google-genai` + `pypdfium2` (shared venv, bootstrapped via `toolchain-bootstrap`) + the user''s own `GEMINI_API_KEY`. Verified running clean: Claude Code, Windows -- see "Verified" below for each modality''s real test-case detail (dates carried over from the 3 skills this merges).'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 (2026-08-13): merge of 3 previously-separate skills (image-generator-gemini, video-generator-gemini, audio-generator-gemini) into one skill_id, part of the same thatlq1812-directed generator restructuring that also plans gpt-generator/claude-generator/normal-generator (see those skills' own SKILL.md for status -- scaffolded, not yet built). Approved specifically because all 3 already shared the identical BYOK-Gemini architecture and thatlq1812's own framing was 'mỗi provider nên gộp vào 1 generator' (each provider should merge into one generator), directly matching the precedent already set by toolchain-bootstrap's same-day merge of 5 bootstrap skills. Content/scripts carried forward verbatim from the 3 source skills (see each below for their own original elicitation); only cross-references between the 3 (now-internal) modalities were updated, no detection/generation logic was rewritten. image-generator-gemini elicited_from: grounded in 3 of thatlq1812's own projects (D:/elix/platform/scripts/gen/, a UNI course project's gen-images-v2.mjs/gen-slide-images.mjs/gen_marketing_images.py) plus a GitHub architecture survey of 5 diffusion-adapter repos (IP-Adapter/InstantID/PhotoMaker/PuLID, Apache-2.0; ComfyUI_IPAdapter_plus, GPL-3.0, idea-only) recorded in the GenVid project's data/references/style-anchored-image/NOTES.md. video-generator-gemini elicited_from: a GitHub architecture survey of 5 image-to-video repos (SVD/DynamiCrafter/CogVideo/AnimateDiff, MIT/Apache-2.0; HunyuanVideo-I2V, technique read-only) recorded in data/references/image-to-video/NOTES.md, plus the real Veo API surface verified directly against the installed SDK and a real client.models.list() call. audio-generator-gemini elicited_from: a GitHub architecture survey of 5 TTS/audio repos (chatterbox/kokoro/F5-TTS/audiocraft/coqui-ai-TTS fork) recorded in data/references/audio-voice-gen/NOTES.md, plus the real TTS API surface verified the same way. v0.1.1 (2026-08-13): the video section's audio-steering guidance is grounded in a separate real, completed project thatlq1812 directly pointed at (D:/elix/projects/20260805_GenVid, 3 real AI-generated history-education videos actually delivered) -- docs/AUDIO_STEERING_AND_FOLEY_GUIDE.md's 4-layer prompt schema, plus a real empirical finding recorded in that project's batch_gen_videos_project3.py (reproduced twice: quoting a voiceover line and asking Veo to 'silently lip-sync' it still made veo-3.1-lite invent an unrelated talking host character). Documentation-only addition -- no script/schema change, this is prompt-construction guidance for whoever calls generate_video.py, not a new CLI flag."
  version: 0.1.1
  grounding: not_applicable
  object_type: []
---

# gemini-generator

A media-generation toolkit covering 3 modalities via Gemini (BYOK, the user's own `GEMINI_API_KEY`): image, video, and audio (TTS).

## Important — doesn't contradict the "no AI backend integration" principle

`docs/specs/STRATEGY_SPEC.md` §2 says Scriptorium doesn't integrate any AI backend — that principle is about **Scriptorium itself** never sitting in the middle as a service calling an LLM on someone's behalf using Scriptorium's own credentials. This skill is different in nature: it's an instruction for the agent to call an API **using the credentials of the user actually running the skill** (bring-your-own-key), entirely optional — like a "send email via SendGrid" skill using the user's own SendGrid key. Scriptorium never issues the key, manages billing, or requires its use. Same reasoning applies to all 3 modalities below.

## Environment bootstrap

A SHARED venv at the repo root (see `skills/general/toolchain-bootstrap/SKILL.md`):

```bash
.\skills\general\toolchain-bootstrap\scripts\bootstrap.ps1 -Requirements skills\media\gemini-generator\requirements.txt -PyVersion 3.12
```

## Routing — which modality do you need?

| Need | Script |
|---|---|
| Generate/analyze images, extract a PDF cover | `scripts/generate_image.py`, `scripts/analyze_style.py`, `scripts/extract_pdf_page.py` |
| Generate/animate video | `scripts/generate_video.py`, `scripts/extract_last_frame.py` (chaining) |
| Generate speech/dialogue audio | `scripts/generate_speech.py` |

---

## 1. Image (`generate_image.py` / `analyze_style.py` / `extract_pdf_page.py`)

A designer toolkit, not just a single-image generator: generates images, keeps a consistent IDENTITY and/or STYLE across multiple images (as two independent, combinable channels), reads/describes an existing image's style, and extracts a cover from a PDF without needing AI.

```bash
export GEMINI_API_KEY="your-key"   # or --api-key
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_image.py "description of the image to create" output.png
```

**Style-anchoring** — `--style-ref output.png --style-strength moderate` sends a reference image with a style-matching instruction; `--style-strength` (`strict`/`moderate`/`loose`) controls phrasing intensity (Gemini's prompt-only API has no numeric conditioning-scale knob). Repeat `--style-ref` to stack multiple samples into one unified style.

**Identity-anchoring** — `--identity-ref character_face.png --identity-strength strict` is an INDEPENDENT channel from style: preserves face/character features while leaving pose/camera/background free to change per the new prompt. Combine both for "same character, new pose, new art style." Repeat `--identity-ref` to stack multiple photos of the same subject into one identity.

**Anchor by shared profile file** — `--anchor-profile hero.json` reads a `media-anchor-profile` JSON file (see `skills/media/media-anchor-profile/SKILL.md`) instead of re-typing raw flags every call; mutually exclusive with `--identity-ref`/`--style-ref`.

**Batch with auto-anchor** — `--batch manifest.json --out-dir assets/`. If `manifest.json`'s `style_ref` is `null`, the FIRST generated image automatically becomes the style reference for every image after it — no sample prep needed. A batch can also fix an `identity_ref` for the whole run. Skip-if-exists (safe to re-run a partial batch); rate-limit delay between requests (default 3s, `--delay`).

**Vision-analysis** — `scripts/analyze_style.py reference.png` returns a style description (palette/lighting/line-weight/composition, NOT subject) usable as a prompt prefix or to understand an existing brand/design system.

**PDF cover extraction** — `scripts/extract_pdf_page.py document.pdf cover.png --page 0 --scale 2.0` — no API call, no cost, no `GEMINI_API_KEY` needed (pure `pypdfium2` render).

### What image generation does NOT do

Doesn't supply/manage the API key. Doesn't default to a permanently fixed model without flagging risk. Doesn't hard-code style-rules/brand identity for any specific project. Doesn't upload to cloud storage or write to a database.

---

## 2. Video (`generate_video.py` / `extract_last_frame.py`)

Animates a still image or generates video from text using Gemini's Veo model. An `--image` anchor is treated as a fixed frame 0 — the model animates FROM it, not a subject description it redraws.

```bash
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_video.py "a neon hologram cat driving at top speed" out.mp4
# Image-to-video, anchored:
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_video.py "the character slowly turns its head and blinks" out.mp4 --image anchor.png --motion-intensity subtle
# Two-keyframe interpolation:
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_video.py "a smooth camera pan across the room" out.mp4 --image start.png --last-frame end.png
```

`--motion-intensity` (`subtle`/`moderate`/`energetic`) is phrasing-based — Veo's config has no numeric motion-strength field. `--last-frame` requires `--image`; Veo natively interpolates between the two keyframes.

**Chaining segments into a longer video** — one Veo call produces a short clip; feed the previous segment's final frame back in as the next segment's `--image`:

```bash
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_video.py "..." segment1.mp4 --image anchor.png
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\extract_last_frame.py segment1.mp4 segment1_last_frame.png
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_video.py "..." segment2.mp4 --image segment1_last_frame.png
```

`extract_last_frame.py` uses `toolchain-bootstrap`'s `resolve_ffmpeg_path()` and a `-sseof`/`-update 1` idiom to grab the true last decoded frame. Stitching chained segments into one final file is `video-assembly-composer`'s job, not this skill's.

Other controls: `--duration-seconds` (must be `4`, `6`, or `8` — a real Veo constraint, not a continuous range despite the API's own error text implying otherwise), `--aspect-ratio`, `--resolution`, `--negative-prompt`, `--seed`, `--generate-audio` (Veo generates synced audio directly). `--poll-interval`/`--timeout` control async-job waiting (jobs are long-running, ~1-2 min for a 4s clip).

### A real finding: steering Veo's audio when the real voice comes from elsewhere (`--generate-audio` + a separate TTS track)

Real finding from a completed project (D:/elix/projects/20260805_GenVid — see `metadata.elicited_from`), reproduced twice independently there: when a scene's real spoken voice comes from a SEPARATE TTS call (e.g. `generate_speech.py`, muxed in afterward by `video-assembly-composer`), simply describing the scene visually and expecting Veo to stay quiet does NOT work reliably — even explicitly asking the visual prompt to "silently move lips matching this line" still made `veo-3.1-lite` invent an unrelated talking/waving host character to perform the line, on 2 separate real attempts. Veo needs to be told EXPLICITLY, not just left to infer it. A prompt structured in 4 layers, in this order, closed the gap:

1. **Visual action** — describe what's on screen as normal, silent action (no dialogue described as being spoken).
2. **A hard negative constraint muting vocals** — e.g. *"DO NOT GENERATE ANY SPEECH, VOICE, OR HUMAN DIALOGUE AUDIO."* — explicit and forceful, not implied.
3. **A positive constraint redirecting audio generation** — e.g. *"GENERATE HIGH-QUALITY BACKGROUND ENVIRONMENT SOUND EFFECTS ONLY."* — gives Veo's `--generate-audio` output somewhere real to go instead of inventing dialogue.
4. **A cast-lock constraint** — e.g. *"No additional characters, narrators, or hosts beyond what is explicitly described."* — the specific real failure mode observed was Veo adding an extra on-screen speaker, not just voicing an existing one.

Use this shape whenever `--generate-audio` is on AND the real voice is coming from `generate_speech.py` separately — i.e. exactly the pattern `media-pipeline-orchestrator` uses (Veo's own audio becomes ambient-only, muxed via `video-assembly-composer`'s `include_own_audio`, while the TTS track carries the real narration). Not needed when Veo's own generated audio IS the intended final voice (no separate TTS track to protect).

### What video generation does NOT do

Doesn't stitch chained segments into one file — see `video-assembly-composer`. Doesn't implement a numeric motion-strength control (Veo's config has none). Doesn't verify output fidelity against the anchor image (flagged idea, not built, to avoid a new perceptual-hash dependency for a nice-to-have).

---

## 3. Audio (`generate_speech.py`)

Text-to-speech via Gemini: single narrator voice, 2-speaker dialogue, or a cloned voice (with mandatory proof of consent). Music/SFX generation is explicitly out of scope — Gemini's music model (Lyria) is only an experimental real-time WebSocket session (`AsyncLiveMusic`), a fundamentally different transport than this script's request/response TTS calls.

```bash
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_speech.py "Say cheerfully: Welcome to the show!" out.wav --voice Kore
```

**2-speaker dialogue** — `--speaker NAME:VOICE`, repeated **exactly twice** (a real Gemini API requirement), speaker names must match the labels in the dialogue text.

**Voice cloning — consent is mandatory, no override**:

```bash
.venv\Scripts\python.exe skills\media\gemini-generator\scripts\generate_speech.py "Hello, this is a cloned voice." out.wav --clone-voice-sample my_voice.wav --clone-consent my_consent.wav
```

Both a voice sample AND a separately recorded consent clip are required — this script hard-refuses `--clone-voice-sample` without `--clone-consent`, not workaround-able. **Not independently API-tested** (no real consent-clip recording available in this environment) — code-reviewed against the SDK schema, flagged honestly rather than claimed working.

A key real finding: Gemini's raw TTS response is unwrapped PCM (`audio/l16; rate=24000; channels=1`), not a playable WAV file — `generate_speech.py` always wraps it into a real WAV via the stdlib `wave` module before writing to disk.

### What audio generation does NOT do

Does not generate music or sound effects (see above). Does not supply/manage the API key. Does not assert a fixed, verified-correct list of valid `--voice` names (Gemini's own list isn't independently queryable via `models.list()`). Does not post-process, denoise, or normalize output.

---

## Bundled files

```
skills/media/gemini-generator/
├── requirements.txt                          # google-genai, pypdfium2
└── scripts/
    ├── generate_image.py, analyze_style.py,   # §1 image
    │   extract_pdf_page.py, batch_manifest*.example.json
    ├── generate_video.py, extract_last_frame.py  # §2 video
    └── generate_speech.py                     # §3 audio
```

## Verified

Each modality's generation/analysis logic is carried forward unchanged from its original skill (only cross-references between the 3 updated) — see each section above for the real test evidence already recorded before the merge, all 2026-08-05 unless noted: image (real single/batch/identity+style-anchored/vision-analysis/PDF-extraction calls, including a combined identity-strict+style-moderate test that held the reference character through a pose AND style change simultaneously), video (`client.models.list()` confirmed 3 real Veo models against thatlq1812's own key, correcting an initially-assumed model name that 404'd; a real image-to-video generation produced a real 483KB mp4; `extract_last_frame.py` correctly extracted its final frame), audio (real single-speaker and 2-speaker dialogue TTS calls, output format confirmed via `ffmpeg -i` and a real human listening check by thatlq1812 — voice cloning is code-reviewed only, not independently API-tested, same honest flag as before the merge).

Post-merge re-verification (2026-08-13): all 3 scripts re-run from the new `skills/media/gemini-generator/scripts/` location (`generate_image.py --help`, `generate_video.py --help`, `generate_speech.py --help`) confirmed the full argument surface and cross-references resolve correctly; `extract_last_frame.py`'s `toolchain-bootstrap` glob lookup and `generate_image.py`'s `media-anchor-profile` glob lookup (both already domain-agnostic from the earlier same-day domain reorg) re-verified unaffected by this second move. Real Gemini API calls were NOT re-run this round (no `GEMINI_API_KEY` available in this environment) — the merge changed file locations and cross-references only, not generation logic, so the pre-merge real-API verification above still applies to the underlying behavior.

## Known limitations

Same per-modality limitations as before the merge (see each section) — this merge changed file location and cross-references only, not generation logic. Model names (Veo, TTS) are **preview** as of 2026-08-05 — the most likely part of this skill to need updating if Gemini promotes/renames them; re-run `client.models.list()` and update the relevant `DEFAULT_MODEL` if generation starts 404ing. Voice cloning remains not independently API-tested. No automatic segment-chaining loop for video (manual per-segment building block; full orchestration is `media-pipeline-orchestrator`'s job). Hasn't passed stage 4 (quality eval) post-merge — not required for this tier, see `registry/SCHEMA.md`.

## Skills depending on this skill

- `media-pipeline-orchestrator` (all 3 modalities, chained into one script→images→videos→audio→assembled-video pipeline).
- `media-anchor-profile` (consumed BY image generation via `--anchor-profile`, not a dependent of it).
