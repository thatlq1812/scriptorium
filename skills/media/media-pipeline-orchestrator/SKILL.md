---
name: media-pipeline-orchestrator
description: 'Ties `gemini-generator` (image/video/audio) and `video-assembly-composer` into one topic → script → images → audio → videos → assembled-video pipeline. State/resume is embedded in the project''s own `project.json` (re-running skips whatever stage/scene is already done). Every Gemini call is wrapped in an exponential-backoff retry. A human-approval checkpoint pauses right after script generation, BEFORE any image/video/audio quota is spent, until `--approve-script` is passed. Audio generates BEFORE video so each scene''s real measured narration length can drive both the video''s requested duration and the final assembly stretch target, instead of a script-guessed duration. Use when the user wants a topic turned into a finished short video end-to-end, or wants to resume a partial run. Do NOT use for one-off single-asset generation -- call the individual skill directly; this skill''s value is the multi-stage state machine, not any one generation call.'
license: MIT
compatibility: 'Requires Python 3.11+ + `google-genai` (shared venv) + the user''s own `GEMINI_API_KEY` + `gemini-generator`, `video-assembly-composer`, and `toolchain-bootstrap` as sibling skill folders (imported as Python modules, not subprocesses). Verified running clean: Claude Code, Windows -- see "Verified" below for both the original 2026-08-05 round and the 2026-08-13 audio-first-duration-stretch reorder.'
metadata:
  domain: media
  task_type: coordination
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in a GitHub architecture survey of 5 end-to-end AI video pipeline repos (youtube-shorts-pipeline -- MIT; Text-To-Video-AI -- MIT; openshorts -- MIT core; OpenMontage -- AGPL-3.0, idea-only; Viral-Faceless-Shorts-Generator -- no license, idea-only), recorded in data/references/e2e-pipeline/NOTES.md (GenVid project 2026-08-05): youtube-shorts-pipeline's state-embedded-in-data + retry-decorator patterns (#1) are reimplemented independently here (pipeline_state.py, retry.py -- same idea, own code, not copied); Viral-Faceless-Shorts-Generator's human-in-the-loop script-approval step (#5) motivated the --approve-script checkpoint; openshorts' CLAUDE.md finding that Gemini performs much better choosing a fixed category than estimating a continuous number (#3, 94-96% accuracy) is the same category-vs-number principle this project's own generate_script.py had to learn the hard way for duration_seconds (see 'A real constraint found by testing'). NOTES.md's own conclusion -- that no surveyed repo does the full chain in pure Gemini -- means this orchestrator's specific 4-skill wiring has no direct prior-art to copy; it is original integration work grounded in the individually-elicited skills it calls, not a ported pipeline. v0.2.0 (2026-08-13): owner directly pointed at a separate real, completed project (D:/elix/projects/20260805_GenVid, 3 real AI-generated history-education videos actually delivered) as reference material -- map_to_veo_duration() and the audio-before-video stage reorder port scripts/pipeline/build_v5_fullmerge.py's own map_to_veo_duration() (identical threshold rule) and batch_gen_tts_multiprocess.py's real-wav-duration-measurement-then-persist-to-scenes.json pattern; the resulting video_track items feed video-assembly-composer's new stretch_from/include_own_audio/own_audio_volume_db fields (see that skill's own SKILL.md metadata.elicited_from for its own half of this same real source)."
  version: 0.2.0
  changelog_0_1_1: "Transfer-review fix (2026-08-05): generate_script.py no longer redefines its own VALID_SCENE_SECONDS=(4,6,8) tuple -- it now imports VALID_DURATIONS_SECONDS directly from video-generator-gemini's generate_video.py (already a mandatory sibling dependency of this skill), removing the duplicate-constant drift risk flagged in v0.1.0's own Known Limitations. No behavior change; re-verified both modules still import and resolve to (4, 6, 8) after the change."
  grounding: not_applicable
  object_type: []
---

# media-pipeline-orchestrator

The "glue" skill: drives `gemini-generator` (image → video → audio) → `video-assembly-composer` from a single topic, with state/resume and retry built in.

## Pipeline stages

```
script    -- Gemini text (JSON mode) -> scenes.json.
             CHECKPOINT: pauses here unless --approve-script is passed.
images    -- 1 gemini-generator image call per scene (auto-anchored: scene_01's
             image becomes the style reference for every scene after it,
             unless --anchor-profile is given instead).
audio     -- 1 gemini-generator TTS call per scene, then concatenated into one
             combined voice track (concat_audio.py, ffmpeg). Each scene's REAL
             measured wav duration is written back into scenes.json as
             actual_audio_duration, plus a veo_duration (the nearest Veo
             discrete duration -- see "Real duration-matching" below).
videos    -- 1 gemini-generator video call per scene, requested at that
             scene's own veo_duration (not the script's original guessed
             duration_seconds), anchored on that scene's image, with Veo's
             own ambient audio generation turned on.
assembly  -- builds a video-assembly-composer timeline.json (video clips,
             stretched to each scene's real actual_audio_duration and mixed
             with Veo's own ambient audio, + captions from narration + the
             combined voice) and renders final.mp4.
```

Audio generates BEFORE video (reversed from this skill's original v0.1.x order) specifically so each scene's real measured narration length is known before the video-generation call that needs it — see "Real duration-matching" below.

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

Verified for real (2026-08-05): a script with `duration_seconds: 7` (chosen from what looked like a reasonable "between 3 and 8" range) was rejected downstream by Veo — it only accepts `4`, `6`, or `8`, not any integer in that range (see `gemini-generator`'s own SKILL.md for the full finding). `generate_script.py`'s prompt and validator still require the script's OWN `duration_seconds` guess be exactly one of `(4, 6, 8)` (a soft pacing target for the writing step), but see below for what actually drives the real Veo call now.

## Real duration-matching: audio drives video, not the other way around

Real problem (found via a real completed project the owner pointed at, D:/elix/projects/20260805_GenVid — see `metadata.elicited_from`): even with `duration_seconds` constrained to Veo's own discrete set, the script's GUESS at how long a scene's narration will take to speak rarely matches the TTS engine's REAL output length exactly — a scene guessed at 6s might actually speak in 5.1s or 7.3s. Previously this drift was simply not corrected (see the old "does NOT do" entry below, now fixed). The real fix: generate audio first, measure each scene's real wav duration (`measure_wav_duration_seconds()`, stdlib `wave` module, no ffprobe needed), map that to Veo's nearest discrete duration (`map_to_veo_duration()`, request VIDEO at that length, and at assembly time, tell `video-assembly-composer` to stretch (`stretch_from`) the video to the real, exact `actual_audio_duration` instead of trusting the two to already match. Both real values are persisted back into `scenes.json` (`actual_audio_duration`, `veo_duration` per scene) so a resumed run doesn't need to re-measure anything.

## What this skill does NOT do

- Does not generate a single one-off asset — see `gemini-generator` for that; this skill's value is the multi-stage state machine, not any one generation call.
- Does not support a separate background MUSIC bed in the assembled output yet — `video-assembly-composer`'s `audio.music` field (with ducking) exists but this orchestrator's `_build_timeline()` doesn't populate it. It DOES now mix in each video clip's own Veo-generated ambient audio (`include_own_audio`, since v0.2.0 — see "Real duration-matching" above), which is a different thing from a separate music track. A caller wanting a music bed must build/render the timeline manually via `video-assembly-composer` directly.
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

**Audio-first duration-matching addition (2026-08-13)**: real, not mocked -- `map_to_veo_duration()` re-verified against GenVid's own exact threshold boundaries (4.2s→4, 5.5s→6, 9.0s→8, matching); `measure_wav_duration_seconds()` re-verified against a real 11.0s test wav (exact match, stdlib `wave` module, no ffprobe); `_build_timeline()` re-verified to correctly emit `stretch_from`/`include_own_audio: true`/`own_audio_volume_db: -12` per scene, using `actual_audio_duration` (not the script's guessed `duration_seconds`) as the timeline slot length — the generated timeline shape independently re-validated clean by `video-assembly-composer`'s own `validate_timeline.py` (only the expected missing-video-file errors, since this test didn't generate real video, confirming the SCHEMA integration is correct). Full module import chain (including the new `wave` stdlib import) re-verified via `run_pipeline.py --help`. NOT re-verified this round: an actual real Gemini API run through the reordered audio→video stages end-to-end (no `GEMINI_API_KEY` available in this environment) — the individual pieces (duration mapping, wav measurement, timeline construction, and separately, `video-assembly-composer`'s own stretch/own-audio rendering — see that skill's own Verified section) are each independently verified real, but not yet chained through one live API-backed run.

## Known limitations (v0.2.0)

- No separate background MUSIC bed support in the built timeline — see "What this skill does NOT do" (per-clip ambient audio from Veo itself IS now mixed in, since v0.2.0 — a different thing).
- ~~No per-scene voice/video duration reconciliation~~ — fixed (2026-08-13, see "Real duration-matching" above): audio now generates first, its real measured length drives both the requested Veo duration and the final assembly stretch target.
- ~~`duration_seconds` is hardcoded to Veo's confirmed set `(4, 6, 8)` in both `generate_script.py` and (separately) `video-generator-gemini`'s own `VALID_DURATIONS_SECONDS`~~ — fixed (2026-08-05, transfer review): `generate_script.py` now imports `VALID_DURATIONS_SECONDS` directly from `gemini-generator`'s `generate_video.py` (same sibling-import pattern `run_pipeline.py` already uses) instead of redefining it — a single source of truth, verified by re-importing both modules cleanly after the change.
- The video-generation prompt reuses each scene's `visual_prompt` (a static scene description) as the motion directive too, rather than a separate "what changes/moves" description — simplistic; a scene where the static description and the desired motion diverge significantly may not animate as intended. See `gemini-generator`'s own SKILL.md for real prompt-schema guidance on steering Veo's audio behavior specifically (added 2026-08-13, a related but distinct concern).
- No cost/quota estimate or confirmation prompt before the images/videos/audio stages (only the script stage has an explicit checkpoint) — a large `--n-scenes` value will spend proportionally more Gemini quota with no additional pause.
- `own_audio_volume_db: -12` (Veo's own ambient audio, mixed under the voice) is a fixed constant, not yet caller-configurable via a CLI flag — matches GenVid's own real dB choice for this exact use case (ambient under narration), not independently re-derived.
