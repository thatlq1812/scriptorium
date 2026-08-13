---
name: video-assembly-composer
description: 'Renders a final .mp4 from a plain-JSON "timeline" describing a sequence of images/video clips (optional Ken Burns pan/zoom), burned-in captions, and a voice + optional ducked music-bed mix -- the plan/render split borrowed from OpenTimelineIO (describe the edit as data first, render second, so a bad path/duration is caught before an ffmpeg call). `validate_timeline.py` is a deterministic, stdlib-only structural validator (every item''s path exists, image items require a positive duration, captions don''t overlap/exceed track length, duck_under_voice requires a voice track). `render_timeline.py` builds the ffmpeg filter graph (via ffmpeg-python) through `toolchain-bootstrap`''s resolved binary -- concatenating segments, burning captions via the native `subtitles` filter, mixing/ducking audio via `sidechaincompress`. Use to assemble Gemini-generated images/video/audio into one finished video. Do NOT use to generate the source images/video/audio/captions -- pure assembly, no AI call.'
license: MIT
compatibility: 'Requires Python 3.11+ + `ffmpeg-python` + `imageio-ffmpeg` (shared venv) + the `toolchain-bootstrap` skill installed as a sibling skill folder. No AI credentials needed -- fully local, deterministic rendering. Verified running clean: Claude Code, Windows (2026-08-05), a real 3-segment render (2 Gemini-generated images with Ken Burns + 1 real Veo clip) with burned captions and a voice+ducked-music audio mix. See "Verified" below.'
metadata:
  domain: media
  task_type: document-conversion
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in a GitHub architecture survey of 5 auto-video-editing repos (auto-editor -- Unlicense; auto-subtitle, faster-auto-subtitle, automatic_video_editing -- MIT; OpenTimelineIO -- Apache-2.0), recorded in data/references/auto-video-editing/NOTES.md (GenVid project 2026-08-05): OpenTimelineIO's Timeline/Track/Clip data model (#5) directly motivated the plan/render split (timeline JSON validated BEFORE any ffmpeg call, never generated and rendered in the same pass); auto-subtitle/faster-auto-subtitle's ffmpeg `subtitles` filter pattern (#2-3) motivated burning captions via that native filter instead of a per-frame moviepy TextClip overlay; automatic_video_editing's moviepy subclip+concatenate pattern (#4) motivated the multi-segment image+video concatenation design, reimplemented on ffmpeg-python's filter graph instead of moviepy for consistency with this skill's own ffmpeg-only dependency chain. The audio side (voice+music with sidechain ducking) is a standard, independently-known ffmpeg recipe, not traced to a specific surveyed repo."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["timeline"]
---

# video-assembly-composer

Turns a plain-JSON edit description into a finished .mp4 via ffmpeg — no AI call anywhere in this skill; it only assembles media that other skills (or a human) already produced.

## Timeline schema

```json
{
  "output": {"width": 1920, "height": 1080, "fps": 30},
  "video_track": [
    {"type": "image", "path": "scene1.png", "duration": 4.0, "ken_burns": true},
    {"type": "video", "path": "clip1.mp4", "duration": 3.5}
  ],
  "captions": [
    {"text": "Once upon a time...", "start": 0.0, "end": 3.0}
  ],
  "audio": {
    "voice": {"path": "narration.wav"},
    "music": {"path": "bg_music.mp3", "volume": 0.5, "duck_under_voice": true}
  }
}
```

- `output`: required. `width`/`height` positive ints, `fps` positive number.
- `video_track`: required, non-empty list, played in order. `type` is `image` or `video`. `duration` is REQUIRED (>0) for `image` items (there's no intrinsic duration to fall back on); OPTIONAL for `video` items (omit to use the clip's own full length — but see Known Limitations re: total-duration-dependent features). `ken_burns` (bool, default effectively on when present) only applies to `image` items — a slow zoom-in (`zoompan`, capped at 1.15x) applied for visual interest on an otherwise static image.
- `captions`: optional list of `{text, start, end}` in seconds relative to the assembled track. Validated for no overlaps and not exceeding the track's total duration (when computable — see below).
- `audio`: optional. `voice.path` and/or `music.path`. `music.volume` (0.0-1.0, default 1.0). `music.duck_under_voice` (bool) lowers the music automatically whenever the voice track is active, via `sidechaincompress` — requires `voice` to also be declared.

## Validate before rendering (always — `render_timeline.py` also runs this internally and refuses to render an invalid timeline)

```bash
.venv\Scripts\python.exe skills\media\video-assembly-composer\scripts\validate_timeline.py timeline.json
```

## Render

```bash
.venv\Scripts\python.exe skills\media\video-assembly-composer\scripts\render_timeline.py timeline.json output.mp4
```

Builds one ffmpeg filter-graph (via `ffmpeg-python`) and runs it in a single process through `toolchain-bootstrap`'s `resolve_ffmpeg_path()` — every image is looped/scaled/optionally zoompan'd, every video clip is scaled+padded+letterboxed to the common output size, all segments are joined with the `concat` filter, captions (if any) are written to a temporary `.srt` next to the output and burned in via the native `subtitles` filter, and audio (if any) is mixed as described above.

## A real bug found and fixed during testing: sidechaincompress truncates to its SHORTER input

Verified for real (2026-08-05): a first version fed a 3.24s voice clip as the sidechain trigger for a 15s music bed directly into `sidechaincompress` — the WHOLE final mix (and therefore the whole rendered video, due to `-shortest`) silently truncated to 3.24s instead of the intended 9s timeline length. Root cause: `sidechaincompress` (like several multi-input ffmpeg audio filters) stops producing output the moment its shorter input ends. Fix: both the voice and music streams are padded/trimmed (`apad` + `atrim`) to the timeline's total duration BEFORE being fed into `sidechaincompress`/`amix`, whenever that total duration is computable (every `video_track` item has an explicit numeric `duration`). Re-tested after the fix: a 3-segment, 9-second timeline with a 3.24s voice clip and a 15s music bed correctly rendered a full 9.00s output (confirmed via `ffmpeg -i`), captions burned in sync with each segment (confirmed by extracting and viewing frames at 1.0s/4.5s/8.5s).

## What this skill does NOT do

- Does not generate any image, video, audio, or caption text itself — pure assembly of already-produced assets. See `image-generator-gemini`, `video-generator-gemini`, `audio-generator-gemini` for the generation side.
- Does not call any LLM/AI API, ever.
- Does not support transitions between segments (hard cuts only) — a `concat`-filter limitation this version doesn't attempt to work around with crossfades/wipes.
- Does not loop a music track shorter than the timeline, or trim one longer than needed beyond the padding described above — if `music.path` is much shorter than the total duration, the padded silence after it ends is real silence, not a loop.
- Does not compute a usable `total_duration` (and therefore skips the audio-padding fix and captions' end-of-track bound check) when any `video_track` item is type `video` with `duration` omitted — see Known Limitations.

## Bundled files

- `scripts/validate_timeline.py` — CLI + importable `validate_timeline()`.
- `scripts/render_timeline.py` — CLI + importable `render()`; also writes the SRT file used for caption burn-in as a side effect (`<output>.srt`, next to the rendered video).
- `requirements.txt` — `ffmpeg-python`, `imageio-ffmpeg`.

## Verified

Real end-to-end render (2026-08-05): a 3-segment timeline (a `image-generator-gemini`-produced cartoon-fox portrait with Ken Burns → a real `video-generator-gemini` Veo clip of the same character blinking → a second Gemini-generated scene with Ken Burns), 3 non-overlapping captions matching each segment's timing, and an `audio-generator-gemini`-produced voice narration ducked under a synthetic test music bed. Confirmed via `ffmpeg -i`: exactly 9.00s output duration (3×3s segments), correct 960x540 h264 video + aac audio streams. Confirmed via extracted frames at 1.0s/4.5s/8.5s: each caption appears burned in and correctly synced to its segment, Ken Burns zoom visibly progresses across the image segments. The rendered file was also sent to the project owner for a real playback check (duration/caption-sync/audio-ducking were verified structurally by this skill's author, not by ear/eye on the final composite).

## Known limitations (v0.1.0)

- `total_duration` (needed for the sidechaincompress fix and for the caption-overrun validation check) is only computed when EVERY `video_track` item has an explicit numeric `duration` — a `video`-type item with `duration` omitted (meaning "use the clip's own length") makes both of those features silently skip, falling back to `-shortest`'s cruder truncation behavior. Always set an explicit `duration` on every item when audio ducking or caption-overrun checking matters.
- No crossfade/transition support between segments — hard cuts only.
- No music looping — see "What this skill does NOT do".
- `zoompan`'s Ken Burns effect uses a single fixed zoom-in curve (`min(zoom+0.0015,1.15)`) — no pan direction, zoom-out, or per-item intensity control yet.
- `subtitles` filter styling (font, size, color, position) is not exposed as a timeline option yet — uses ffmpeg's built-in default caption rendering.
- No transitions/validation for audio format mismatches (e.g. a music file with an unusual sample rate) beyond what ffmpeg itself tolerates.
