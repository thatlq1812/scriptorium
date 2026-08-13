---
name: media-pipeline-orchestrator
description: 'Ties `image-generator-gemini`, `video-generator-gemini`, `audio-generator-gemini`, and `video-assembly-composer` into one topic → script → images → videos → audio → assembled-video pipeline. State/resume is embedded in the project''s own `project.json` (re-running skips whatever stage/scene is already done, never a separate checkpoint file that can drift out of sync with the artifacts on disk). Every Gemini API call is wrapped in an exponential-backoff retry. A human-approval checkpoint pauses right after script generation, BEFORE any image/video/audio quota is spent, until the caller passes `--approve-script` -- catches a bad script cheaply instead of after paying for 4 stages. Use when the user wants a topic turned into a finished short video end-to-end, or wants to resume a partial run. Do NOT use for one-off single-asset generation -- call the individual skill directly; this skill''s value is the multi-stage state machine, not any one generation call.'
license: MIT
compatibility: 'Requires Python 3.11+ + `google-genai` (shared venv) + the user''s own `GEMINI_API_KEY` + `image-generator-gemini`, `video-generator-gemini`, `audio-generator-gemini`, `video-assembly-composer`, and `toolchain-bootstrap` as sibling skill folders (imported as Python modules, not subprocesses). Verified running clean: Claude Code, Windows (2026-08-05), a real 2-scene end-to-end run incl. checkpoint pause + resume-after-failure. See "Verified" below.'
metadata:
  domain: media
  task_type: coordination
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in a GitHub architecture survey of 5 end-to-end AI video pipeline repos (youtube-shorts-pipeline -- MIT; Text-To-Video-AI -- MIT; openshorts -- MIT core; OpenMontage -- AGPL-3.0, idea-only; Viral-Faceless-Shorts-Generator -- no license, idea-only), recorded in data/references/e2e-pipeline/NOTES.md (GenVid project 2026-08-05): youtube-shorts-pipeline's state-embedded-in-data + retry-decorator patterns (#1) are reimplemented independently here (pipeline_state.py, retry.py -- same idea, own code, not copied); Viral-Faceless-Shorts-Generator's human-in-the-loop script-approval step (#5) motivated the --approve-script checkpoint; openshorts' CLAUDE.md finding that Gemini performs much better choosing a fixed category than estimating a continuous number (#3, 94-96% accuracy) is the same category-vs-number principle this project's own generate_script.py had to learn the hard way for duration_seconds (see 'A real constraint found by testing'). NOTES.md's own conclusion -- that no surveyed repo does the full chain in pure Gemini -- means this orchestrator's specific 4-skill wiring has no direct prior-art to copy; it is original integration work grounded in the individually-elicited skills it calls, not a ported pipeline."
  version: 0.1.1
  changelog_0_1_1: "Transfer-review fix (2026-08-05): generate_script.py no longer redefines its own VALID_SCENE_SECONDS=(4,6,8) tuple -- it now imports VALID_DURATIONS_SECONDS directly from video-generator-gemini's generate_video.py (already a mandatory sibling dependency of this skill), removing the duplicate-constant drift risk flagged in v0.1.0's own Known Limitations. No behavior change; re-verified both modules still import and resolve to (4, 6, 8) after the change."
  grounding: not_applicable
  object_type: []
---

# media-pipeline-orchestrator

The "glue" skill: drives `image-generator-gemini` → `video-generator-gemini` → `audio-generator-gemini` → `video-assembly-composer` from a single topic, with state/resume and retry built in.

## Pipeline stages

```
script    -- Gemini text (JSON mode) -> scenes.json.
             CHECKPOINT: pauses here unless --approve-script is passed.
images    -- 1 image-generator-gemini call per scene (auto-anchored: scene_01's
             image becomes the style reference for every scene after it,
             unless --anchor-profile is given instead).
videos    -- 1 video-generator-gemini call per scene, anchored on that scene's image.
audio     -- 1 audio-generator-gemini TTS call per scene, then concatenated
             into one combined voice track (concat_audio.py, ffmpeg).
assembly  -- builds a video-assembly-composer timeline.json (video clips +
             captions from narration + the combined voice) and renders final.mp4.
```

## Run

```bash
# 1. Generate + review the script (stops here, no image/video/audio quota spent yet)
.venv\Scripts\python.exe skills\media\media-pipeline-orchestrator\scripts\run_pipeline.py my_project --topic "a fox's rainy day adventure" --n-scenes 2

# 2. Review my_project/scenes.json by hand (edit narration/visual_prompt/duration_seconds if needed), then:
.venv\Scripts\python.exe skills\media\media-pipeline-orchestrator\scripts\run_pipeline.py my_project --topic "a fox's rainy day adventure" --n-scenes 2 --approve-script
```

Re-running the SAME command after a partial failure resumes from whatever stage/scene isn't done yet — verified for real (see below): a video-generation failure on scene 2 left scene 1's image/video on disk and `project.json`'s `_pipeline_state` without a `videos: done` entry; re-running skipped scene 1 entirely and only retried scene 2.

`--anchor-profile profile.json` uses a `media-anchor-profile` file for every scene's image instead of auto-anchor chaining — useful when a specific pre-defined character/style (not just "whatever scene 1 happened to generate") must be held throughout.

## A real constraint found by testing: Veo's duration_seconds is a discrete set

Verified for real (2026-08-05): a script with `duration_seconds: 7` (chosen from what looked like a reasonable "between 3 and 8" range) was rejected downstream by `video-generator-gemini` — Veo only accepts `4`, `6`, or `8`, not any integer in that range (see `video-generator-gemini`'s own SKILL.md for the full finding). `generate_script.py`'s prompt and validator were fixed to require `duration_seconds` be exactly one of `(4, 6, 8)`, matching `video-generator-gemini`'s `VALID_DURATIONS_SECONDS` exactly — a schema-level constraint shared across two skills is enforced identically in both places, not just documented in one.

## What this skill does NOT do

- Does not generate a single one-off asset — see the individual skills (`image-generator-gemini`, `video-generator-gemini`, `audio-generator-gemini`) for that; this skill's value is the 4-stage state machine, not any one generation call.
- Does not support background music in the assembled output yet — `video-assembly-composer`'s `audio.music` field (with ducking) exists but this orchestrator's `_build_timeline()` doesn't populate it. A caller wanting music must build/render the timeline manually via `video-assembly-composer` directly.
- Does not correct a mismatch between a scene's spoken narration length and its declared `duration_seconds` — the combined voice track is a straight back-to-back concatenation of per-scene clips; if a scene's TTS audio runs notably longer/shorter than its video segment, they will drift out of sync within that scene. Not auto-detected or fixed.
- Does not block on an interactive human prompt (`input()`) for the script-approval checkpoint — it requires an explicit re-invocation with `--approve-script`, since these scripts are meant to run non-interactively/in batch.
- Does not retry a failed stage indefinitely — each Gemini call is capped (3 retries for script/image/audio, 2 for video since Veo jobs are expensive/slow) before the whole run exits with a traceback, leaving state exactly where it stopped for a clean resume.

## Bundled files

- `scripts/pipeline_state.py` — `PipelineState` (state embedded in `project.json`).
- `scripts/retry.py` — `with_retry()` exponential-backoff decorator.
- `scripts/generate_script.py` — CLI + importable `generate_script()`/`validate_script()`.
- `scripts/concat_audio.py` — importable `concat_wavs()` (ffmpeg concat demuxer).
- `scripts/run_pipeline.py` — the main CLI tying everything together.
- `requirements.txt` — `google-genai`.

## Verified

Real end-to-end run (2026-08-05), topic "a small fox exploring a rainy city at night, looking for shelter", 2 scenes: (1) script stage correctly paused after writing `scenes.json`, printed the re-run instruction, exited 0 without touching image/video/audio quota; (2) after `--approve-script`, images stage generated scene_01 then auto-anchored scene_02's style from scene_01's output (visually consistent fox across both, confirmed); (3) videos stage hit the real Veo `duration_seconds` discrete-set issue on scene_02 (see above) — the run failed cleanly, `project.json` showed `images: done` but no `videos` entry, scene_01's video file was already on disk; (4) after fixing `scenes.json`'s `duration_seconds` and re-running the SAME command, `videos` stage correctly SKIPPED scene_01 (file already existed) and only generated scene_02, confirming resume-by-artifact works; (5) audio and assembly stages completed on the same run, producing a real 11.92s `final.mp4` (960x540, h264/aac) with correctly synced per-scene captions and narration. The final video was sent to the project owner for review.

## Known limitations (v0.1.0)

- No background-music support in the built timeline — see "What this skill does NOT do".
- No per-scene voice/video duration reconciliation — see "What this skill does NOT do".
- ~~`duration_seconds` is hardcoded to Veo's confirmed set `(4, 6, 8)` in both `generate_script.py` and (separately) `video-generator-gemini`'s own `VALID_DURATIONS_SECONDS`~~ — fixed (2026-08-05, transfer review): `generate_script.py` now imports `VALID_DURATIONS_SECONDS` directly from `video-generator-gemini`'s `generate_video.py` (same sibling-import pattern `run_pipeline.py` already uses) instead of redefining it — a single source of truth, verified by re-importing both modules cleanly after the change.
- The video-generation prompt reuses each scene's `visual_prompt` (a static scene description) as the motion directive too, rather than a separate "what changes/moves" description — simplistic; a scene where the static description and the desired motion diverge significantly may not animate as intended.
- No cost/quota estimate or confirmation prompt before the images/videos/audio stages (only the script stage has an explicit checkpoint) — a large `--n-scenes` value will spend proportionally more Gemini quota with no additional pause.
