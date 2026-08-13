---
name: audio-generator-gemini
description: 'Generates speech audio (TTS) from text using Gemini, via the user''s OWN API key -- optional, not an AI backend managed by Scriptorium. Supports single prebuilt-voice narration, 2-speaker dialogue (labelled script + a voice per speaker), and voice cloning (a sample of the target voice PLUS a separate recorded consent clip -- refuses to clone without proof of consent, no override). Output is always wrapped into a proper .wav file (Gemini''s raw response is unwrapped PCM, not playable on its own -- verified 2026-08-05). Use when the user already has a Gemini API key and needs narration/dialogue audio, or a cloned voice with real consent recorded. Do NOT use for music/sound-effect generation -- Gemini''s music model (Lyria) is only an experimental real-time WebSocket session (`AsyncLiveMusic`), a fundamentally different API shape than this skill''s request/response TTS calls; deliberately not implemented here rather than half-built.'
license: MIT
compatibility: 'Requires Python 3.11+ + `google-genai` (shared venv) + the user''s own `GEMINI_API_KEY`. Verified running clean: Claude Code, Windows (2026-08-05), real API calls for single-speaker and 2-speaker dialogue TTS. See "Verified" below.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in a GitHub architecture survey of 5 TTS/audio repos (chatterbox, kokoro, F5-TTS, audiocraft -- MIT/Apache-2.0 code, non-commercial weight licenses flagged; coqui-ai-TTS fork -- MPL-2.0), recorded in data/references/audio-voice-gen/NOTES.md (GenVid project 2026-08-05): the recurring 3-axis prompt schema (content/text, voice identity, expressive-control parameters) motivated keeping voice/speaker config strictly separate from the spoken text argument; chatterbox's built-in output watermarking for AI-generated audio motivated treating Gemini's own consent_audio requirement for voice cloning as a hard, non-optional gate rather than an inconvenience to route around. Exact API surface (response_modalities=['AUDIO'], SpeechConfig/VoiceConfig/PrebuiltVoiceConfig/MultiSpeakerVoiceConfig/ReplicatedVoiceConfig, and the real output format audio/l16 rate=24000 channels=1 raw PCM) verified directly against the installed google-genai SDK source and real API calls against the owner's own key (2026-08-05), including the real available TTS model names (gemini-3.1-flash-tts-preview, gemini-2.5-flash-preview-tts, gemini-2.5-pro-preview-tts) from a live client.models.list() call -- not copied from documentation that could be stale."
  version: 0.1.1
  changelog_0_1_1: "Stage-4 (quality-eval) Pass A run (2026-08-05) found and fixed a real contract violation: --clone-voice-sample/--clone-consent were read via .read_bytes() before checking either path exists -- a nonexistent path crashed with a raw FileNotFoundError traceback instead of the clean sys.exit() message the consent-gate logic right below it already used. Fixed with an explicit existence check for both paths before any read. Re-verified: a missing-consent-file case and a nonexistent-sample-path case both now exit 1 with a one-line message; the existing 2-speaker-count and consent-gate checks unaffected."
  grounding: not_applicable
  object_type: []
---

# audio-generator-gemini

Text-to-speech via Gemini: single narrator voice, 2-speaker dialogue, or a cloned voice (with mandatory proof of consent). Music/SFX generation is explicitly out of scope for this version — see below.

## Important — doesn't contradict the "no AI backend integration" principle

Same reasoning as `image-generator-gemini`/`video-generator-gemini`: bring-your-own-key, the caller's own credentials and quota.

## A key real finding: Gemini's TTS output is raw PCM, not a WAV file

Verified against a real API response (2026-08-05): `part.inline_data.mime_type` is `"audio/l16; rate=24000; channels=1"` — 16-bit signed little-endian PCM, 24kHz, mono, with **no container/header**. Writing those bytes straight to a `.wav` extension produces a file most players will refuse to open correctly. This skill always wraps the raw PCM into a real WAV via the stdlib `wave` module (`write_wav()` in `generate_speech.py`) before writing to disk — verified via `ffmpeg -i` reporting a correct `pcm_s16le, 24000 Hz, mono` stream on the wrapped output.

## Environment bootstrap

```bash
uv pip install --python .venv -r skills/media/audio-generator-gemini/requirements.txt
```

## Single-speaker narration

```bash
.venv\Scripts\python.exe skills\media\audio-generator-gemini\scripts\generate_speech.py "Say cheerfully: Welcome to the show!" out.wav --voice Kore
```

`--voice` is a prebuilt voice name (default `Kore`) — valid names come from Gemini's own published TTS voice list; this skill doesn't hardcode/assert a full enum since that list isn't independently queryable via `models.list()` and could go stale. Gemini's TTS style control is done through the text itself (e.g. prefixing "Say cheerfully:" / "Say in a whisper:") rather than a separate parameter — verified for real, produced an audibly different result than a plain sentence.

## 2-speaker dialogue

```bash
.venv\Scripts\python.exe skills\media\audio-generator-gemini\scripts\generate_speech.py \
  "TTS the following conversation between Joe and Jane:
Joe: How's it going today, Jane?
Jane: Pretty good, how about you?" out.wav --speaker Joe:Charon --speaker Jane:Kore
```

`--speaker NAME:VOICE`, repeated **exactly twice** — a real Gemini API requirement (`MultiSpeakerVoiceConfig.speaker_voice_configs` docstring: "Exactly two speaker voice configurations must be provided"), enforced by this script before the API call rather than surfacing a confusing 400 later. The speaker names in `--speaker` must match the labels used in the dialogue text.

## Voice cloning — consent is mandatory, no override

```bash
.venv\Scripts\python.exe skills\media\audio-generator-gemini\scripts\generate_speech.py "Hello, this is a cloned voice." out.wav \
  --clone-voice-sample my_voice.wav --clone-consent my_consent.wav
```

Both a voice sample AND a separately recorded consent clip are required (both 16-bit LE WAV, 24kHz per Gemini's `ReplicatedVoiceConfig` spec) — this script raises a hard error and refuses to proceed if `--clone-voice-sample` is given without `--clone-consent`. This isn't a workaround-able validation; it mirrors the API's own built-in consent-verification field, and matches the ethics precedent in `data/references/audio-voice-gen/NOTES.md` #1 (chatterbox/Resemble AI watermark AI-generated audio by default). **Not independently API-tested** — recording a real consent clip requires actual voice hardware/consent workflow not available in this environment; the code path is built and reviewed against the SDK's documented schema, not verified end-to-end. Flagged honestly rather than claimed working.

## What this skill does NOT do

- Does not generate music or sound effects — Gemini's music model (Lyria) is exposed only via `google.genai.live_music.AsyncLiveMusic`, an **experimental**, session-based real-time WebSocket API (connect → stream `set_music_generation_config`/`set_weighted_prompts` → receive a continuous audio stream → explicit `play`/`pause`/`stop` control) — a fundamentally different transport/programming model than this skill's simple "send text, get bytes back" TTS calls. Building a half-working synchronous wrapper around a streaming session API was deliberately avoided (`CLAUDE.md`: "No half-finished implementations"). If music/SFX generation is needed later, it should be its own skill (or a v2 of this one) designed around the Live API's actual session shape, not bolted onto this one.
- Does not supply/manage the API key for the user.
- Does not assert a fixed, verified-correct list of valid `--voice` names — see "Single-speaker narration" above.
- Does not allow voice cloning without a consent clip — see "Voice cloning" above; this is enforced code, not just documentation.
- Does not post-process, denoise, or normalize the generated audio — raw model output, wrapped into WAV, nothing else.

## Bundled files

- `scripts/generate_speech.py` — single-speaker / 2-speaker dialogue / voice-cloning CLI, always outputs a real WAV.
- `requirements.txt` — `google-genai`.

## Verified

Real API calls (2026-08-05): `client.models.list()` against the owner's own key confirmed 3 real TTS-capable models (`gemini-3.1-flash-tts-preview`, `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`). Single-speaker call ("Say cheerfully: The quick brown fox...", voice `Kore`) produced real audio, confirmed via raw response inspection (`mime_type = audio/l16; rate=24000; channels=1`) and via the wrapped `.wav` file's `ffmpeg -i` output (`pcm_s16le, 24000 Hz, mono`, 3.24s duration for a one-sentence narration). 2-speaker dialogue call (Joe/Charon + Jane/Kore) produced a real 3.64s wav with the correct format. Both output files were additionally sent to the project owner for a real listening check (this skill's own author cannot hear audio) rather than relying on format-correctness alone as "verified."

## Known limitations (v0.1.0)

- Music/sound-effect generation not implemented — see "What this skill does NOT do".
- Voice cloning is code-reviewed against the SDK schema but not independently API-tested (no real consent-clip recording available in this environment) — treat as unverified until exercised for real.
- Model names are **preview** as of 2026-08-05 (all 3 discovered TTS models carry a `-preview` suffix) — the most likely part of this skill to need updating if Gemini promotes/renames them.
- No streaming output — waits for the full response before writing the file, fine for narration-length text but not designed for very long scripts (Gemini's own context/output limits apply, not independently stress-tested here).
