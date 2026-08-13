---
name: video-assembly-composer
description: 'Renders a final .mp4 from a plain-JSON "timeline" describing a sequence of images/video clips (optional Ken Burns pan/zoom, optional slow-motion stretch-to-duration), burned-in captions, and a voice + optional per-clip ambient audio + optional ducked music-bed mix -- the plan/render split borrowed from OpenTimelineIO (describe the edit as data first, render second, so a bad path/duration is caught before an ffmpeg call). `validate_timeline.py` is a deterministic, stdlib-only structural validator. `render_timeline.py` builds the ffmpeg filter graph (via ffmpeg-python) through `toolchain-bootstrap`''s resolved binary -- concatenating segments, burning captions, mixing/ducking audio, stretching a video clip (setpts/atempo) to exactly match a real measured target duration instead of just trimming it. Use to assemble Gemini-generated images/video/audio into one finished video. Do NOT use to generate the source images/video/audio/captions -- pure assembly, no AI call.'
license: MIT
compatibility: 'Requires Python 3.11+ + `ffmpeg-python` + `imageio-ffmpeg` (shared venv) + the `toolchain-bootstrap` skill installed as a sibling skill folder. No AI credentials needed -- fully local, deterministic rendering. Verified running clean: Claude Code, Windows -- see "Verified" below for both the original 2026-08-05 round and the 2026-08-13 stretch/own-audio addition.'
metadata:
  domain: media
  task_type: document-conversion
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in a GitHub architecture survey of 5 auto-video-editing repos (auto-editor -- Unlicense; auto-subtitle, faster-auto-subtitle, automatic_video_editing -- MIT; OpenTimelineIO -- Apache-2.0), recorded in data/references/auto-video-editing/NOTES.md (GenVid project 2026-08-05): OpenTimelineIO's Timeline/Track/Clip data model (#5) directly motivated the plan/render split (timeline JSON validated BEFORE any ffmpeg call, never generated and rendered in the same pass); auto-subtitle/faster-auto-subtitle's ffmpeg `subtitles` filter pattern (#2-3) motivated burning captions via that native filter instead of a per-frame moviepy TextClip overlay; automatic_video_editing's moviepy subclip+concatenate pattern (#4) motivated the multi-segment image+video concatenation design, reimplemented on ffmpeg-python's filter graph instead of moviepy for consistency with this skill's own ffmpeg-only dependency chain. The audio side (voice+music with sidechain ducking) is a standard, independently-known ffmpeg recipe, not traced to a specific surveyed repo. v0.2.0 (2026-08-13) additionally grounded in a real, separate, completed project the owner directly pointed at: D:/elix/projects/20260805_GenVid (3 real AI-generated history-education videos, actually delivered/submitted) -- the `stretch_from`/`setpts`/`atempo` mechanism ports `scripts/pipeline/build_v5_fullmerge.py`'s `map_to_veo_duration()` + stretch-not-trim technique (real problem: Veo's discrete 4/6/8s durations almost never match the real measured TTS narration length, and a plain `-shortest` mux cuts the voice off mid-sentence); `include_own_audio`/`own_audio_volume_db` + the per-segment edge-fade port `build_ambient_dub_mix.py`'s per-scene `atempo`+`volume`+`afade`-before-concat technique (real problem: concatenating independently-generated per-scene audio produces an audible click/pop at each cut without the edge-fade). Read in full before porting, not skimmed; the audio-steering Veo-prompt guidance found in the same project went into `gemini-generator` instead (a documentation-only addition, not a schema change) -- see that skill's own SKILL.md."
  version: 0.3.0
  changelog_0_3_0: "Persistent watermark overlay (2026-08-13), the last of the 4 GenVid findings ported this round (task tracked separately from 1a/1b/1c/1e as a larger-scope item -- see docs/STATUS.md). Ported from the same elicitation project's build_watermark_overlay.py (a full-frame transparent PNG, its own visual content positioned via HTML/CSS, meant to be ffmpeg-composited over the video body only, not the intro/outro cards) and build_final_video.py (intro card + watermarked body + outro card, concatenated). Investigated intro/outro cards specifically and found they needed NO new schema -- video_track already supports type:'image' with ken_burns:false, a still card held for its declared duration; only documented as a real usage pattern (see 'Intro/outro cards' below), not implemented as new code. The one genuinely new capability is watermark_image (top level) + watermark (per-item bool): every flagged item contributes its [start, start+duration) span to an ffmpeg overlay filter's enable expression (adjacent spans merge, non-adjacent spans OR together), always composited at 0:0 since the source image supplies its own internal layout -- matching the elicitation source's own technique exactly rather than inventing a corner/margin positioning scheme not in the real source. html-poster-composer gained a VIDEO_HD canvas preset + transparent_background rendering mode specifically to produce this kind of image (see that skill's own changelog)."
  grounding: not_applicable
  object_type: ["timeline"]
---

# video-assembly-composer

Turns a plain-JSON edit description into a finished .mp4 via ffmpeg — no AI call anywhere in this skill; it only assembles media that other skills (or a human) already produced.

## Timeline schema

```json
{
  "output": {"width": 1920, "height": 1080, "fps": 30},
  "watermark_image": "watermark.png",
  "video_track": [
    {"type": "image", "path": "intro_card.png", "duration": 2.0, "ken_burns": false},
    {"type": "image", "path": "scene1.png", "duration": 4.0, "ken_burns": true, "watermark": true},
    {"type": "video", "path": "clip1.mp4", "duration": 3.5, "watermark": true},
    {"type": "video", "path": "clip2.mp4", "duration": 6.2, "stretch_from": 4.0, "include_own_audio": true, "own_audio_volume_db": -12, "watermark": true},
    {"type": "image", "path": "outro_card.png", "duration": 3.0, "ken_burns": false}
  ],
  "captions": [
    {"text": "Once upon a time...", "start": 2.0, "end": 5.0}
  ],
  "audio": {
    "voice": {"path": "narration.wav"},
    "music": {"path": "bg_music.mp3", "volume": 0.5, "duck_under_voice": true}
  }
}
```

- `output`: required. `width`/`height` positive ints, `fps` positive number.
- `video_track`: required, non-empty list, played in order. `type` is `image` or `video`. `duration` is REQUIRED (>0) for `image` items (there's no intrinsic duration to fall back on); OPTIONAL for `video` items (omit to use the clip's own full length — but see Known Limitations re: total-duration-dependent features). `ken_burns` (bool, default effectively on when present) only applies to `image` items — a slow zoom-in (`zoompan`, capped at 1.15x) applied for visual interest on an otherwise static image.
  - `stretch_from` (`video` items only, optional): the clip's own real/native duration. When set (together with `duration`, the TARGET length), the clip is slow-motion stretched or compressed (`setpts`) to exactly hit `duration` instead of being trimmed — for a clip whose native length is fixed by whatever generated it (e.g. an AI video API's discrete duration set) but needs to match something measured afterward (e.g. the real length of a voice track), see "Stretch-to-duration" below.
  - `include_own_audio` (`video` items only, optional, default `false`): mix this clip's own embedded audio track into the final audio mix (see "Per-clip ambient audio" below) — atempo-adjusted by the same ratio as `stretch_from`/`duration` if both are set, so it stays in sync with the stretched video. A clip with no audio stream, or an item where this is `false`/absent, contributes silence to its own segment of the mix instead (silently, not an error — the whole point is this is optional per clip).
  - `own_audio_volume_db` (`video` items only, optional, default `0`): dB gain/attenuation applied to this clip's own audio before mixing (only meaningful when `include_own_audio` is `true`).
  - `watermark` (either item type, optional, default `false`): overlay `watermark_image` (see below) for exactly this item's span. See "Persistent watermark overlay" below.
- `captions`: optional list of `{text, start, end}` in seconds relative to the assembled track. Validated for no overlaps and not exceeding the track's total duration (when computable — see below).
- `audio`: optional. `voice.path` and/or `music.path`. `music.volume` (0.0-1.0, default 1.0). `music.duck_under_voice` (bool) lowers the music automatically whenever the voice track is active, via `sidechaincompress` — requires `voice` to also be declared. If any `video_track` item sets `include_own_audio`, its (real-or-silent) per-clip audio joins `voice`/`music` in the final mix automatically — no separate `audio.*` field needed for it.
- `watermark_image` (top-level, optional): path to a single full-output-frame image overlaid at `0:0` for every `video_track` item that sets `watermark: true`. Required if any item sets `watermark: true`; refused if declared but unused.

## Stretch-to-duration — when a clip's native length doesn't match what it needs to be

Real problem this solves (found via a real production project, see `metadata.elicited_from`): a video-generation API often only accepts a small discrete set of clip durations (e.g. Veo's 4/6/8 seconds), which almost never matches the real length of a separately-generated voice track meant to play over it. Trimming the video to the shorter of the two cuts the voice off mid-sentence; trimming the voice is worse (destroys content). The fix is to never trim either — **stretch the video** (real slow-motion via `setpts`, not a fake speed-up/skip) to exactly the target length instead:

```json
{"type": "video", "path": "clip.mp4", "duration": 6.2, "stretch_from": 4.0}
```

`stretch_from` is the clip's own real, already-known native length (the caller already knows this — it's what was requested when the clip was generated); `duration` is the real target (e.g. a separately-measured voice-track length). The stretch factor is `duration / stretch_from`; ffmpeg's `setpts` filter is bidirectional (a factor > 1 slows the clip down/lengthens it, < 1 speeds it up/shortens it), so this also correctly handles a target SHORTER than the native clip, not just longer.

## Per-clip ambient audio — mixing in a video's own embedded track, not just voice+music

A generated video clip sometimes carries its own useful ambient audio (background sound, room tone) that today's `audio.voice`/`audio.music` fields have no way to include — they only ever reference separate, standalone audio files. `include_own_audio: true` pulls a `video_track` item's own embedded audio into the mix:

```json
{"type": "video", "path": "clip.mp4", "duration": 6.2, "stretch_from": 4.0, "include_own_audio": true, "own_audio_volume_db": -12}
```

Internally, every `video_track` item (whether or not it sets `include_own_audio`) contributes exactly one audio segment of exactly its own `duration` — real audio (atempo-matched to any stretch, volume-adjusted, short-edge-faded) if requested and present, real silence otherwise — and these segments are concatenated into ONE continuous track spanning the whole timeline before joining the final `voice`/`music` mix. The short (~0.1s) edge-fade on every real segment specifically prevents an audible click/pop at each scene-cut boundary, a real artifact a plain concatenation of independently-generated clips produces otherwise.

## Intro/outro cards — no new field, an existing pattern

A static held title/credits card (GenVid's real submission pipeline: a 5s intro card + a 15s outro card bracketing the body) needs no new schema — it's just an ordinary `video_track` item of `type: "image"` with `ken_burns: false` (a still frame, not a slow zoom) at the start and/or end of the list. `html-poster-composer`'s `VIDEO_HD` canvas preset (1920x1080, `compose.py <layout.json> <content.json> -o card.png`) is the natural way to generate the card image itself. Simply leave `watermark` unset (or `false`) on card items if the body is watermarked but the cards shouldn't be (matching GenVid's real design — an outro card already carries its own full credits, it doesn't need the body's small corner disclaimer too).

## Persistent watermark overlay — a brand/disclaimer tag composited over part of the timeline

Real problem this solves (`build_watermark_overlay.py`/`build_final_video.py` in the same elicitation project, see `metadata.elicited_from`): a low-key always-on-screen tag (e.g. an AI-content disclaimer + credit line) needs to sit over the BODY of a video for its whole duration, without appearing on the intro/outro cards. Declare `watermark_image` at the top level (a single image, typically a transparent PNG the same size as `output.width`x`output.height`, with its own visual content already positioned inside it — `html-poster-composer`'s `transparent_background: true` content.json field plus the `VIDEO_HD` preset renders exactly this), then flag `watermark: true` on every `video_track` item it should appear over:

```json
{"type": "video", "path": "clip1.mp4", "duration": 3.5, "watermark": true}
```

The overlay is always composited at `0:0` (no corner/margin positioning logic in this skill — the image supplies its own layout, matching the real elicitation source's own technique of a full-frame transparent PNG with CSS-positioned content). Every item that sets `watermark: true` contributes its own `[start, start+duration)` span to the overlay's visible time range (`ffmpeg`'s `overlay` filter `enable` expression) — adjacent flagged items merge into one continuous span; non-adjacent flagged items produce multiple separate spans, both handled correctly. As with `include_own_audio`, flagging any item as `watermark: true` requires EVERY `video_track` item to have a numeric `duration` (needed to compute those spans) — enforced by `validate_timeline.py`.

## Validate before rendering (always — `render_timeline.py` also runs this internally and refuses to render an invalid timeline)

```bash
.venv\Scripts\python.exe skills\media\video-assembly-composer\scripts\validate_timeline.py timeline.json
```

## Render

```bash
.venv\Scripts\python.exe skills\media\video-assembly-composer\scripts\render_timeline.py timeline.json output.mp4
```

Builds one ffmpeg filter-graph (via `ffmpeg-python`) and runs it in a single process through `toolchain-bootstrap`'s `resolve_ffmpeg_path()` — every image is looped/scaled/optionally zoompan'd, every video clip is scaled+padded+letterboxed to the common output size, all segments are joined with the `concat` filter, captions (if any) are written to a temporary `.srt` next to the output and burned in via the native `subtitles` filter, and audio (if any) is mixed as described above.

## Real bugs found and fixed during testing

**sidechaincompress truncates to its SHORTER input** (2026-08-05): a first version fed a 3.24s voice clip as the sidechain trigger for a 15s music bed directly into `sidechaincompress` — the WHOLE final mix (and therefore the whole rendered video, due to `-shortest`) silently truncated to 3.24s instead of the intended 9s timeline length. Root cause: `sidechaincompress` (like several multi-input ffmpeg audio filters) stops producing output the moment its shorter input ends. Fix: both the voice and music streams are padded/trimmed (`apad` + `atrim`) to the timeline's total duration BEFORE being fed into `sidechaincompress`/`amix`, whenever that total duration is computable (every `video_track` item has an explicit numeric `duration`). Re-tested after the fix: a 3-segment, 9-second timeline with a 3.24s voice clip and a 15s music bed correctly rendered a full 9.00s output (confirmed via `ffmpeg -i`), captions burned in sync with each segment (confirmed by extracting and viewing frames at 1.0s/4.5s/8.5s).

**The `subtitles` filter's own path parser breaks on an absolute Windows path** (2026-08-13, found while testing the stretch/own-audio addition, unrelated to it): a bare absolute path with a drive-letter colon (e.g. `C:/Users/...`) breaks the `subtitles` filter's argument parser, which treats `:` and `\` as structural separators — and manually escaping those characters doesn't fix it, since `ffmpeg-python`'s own filter-argument serializer escapes `\` AGAIN on top of any manual escaping, compounding into garbage no combination of manual pre-escaping fixed (verified empirically against real ffmpeg with several candidate escapings, not assumed). Real fix: sidestep the escaping question entirely — reference the SRT file by bare relative filename only (no colon, no backslash, nothing to escape) and run the ffmpeg subprocess with its `cwd` set to that same directory (`ffmpeg.compile()` + `subprocess.run(cwd=...)`, replacing the previous `ffmpeg.run()` call, which has no `cwd` parameter). Every OTHER path in the render (video/audio inputs, the output file) stays absolute and is resolved to absolute up front, specifically so this `cwd` change can't accidentally break them. Re-verified: a real render with burned-in captions from a path containing a drive-letter colon now succeeds; a frame extracted mid-caption visually confirms the correct text is burned in at the right position.

**A looped, unbounded watermark image input runs the ffmpeg process forever instead of stopping at the main video's length** (2026-08-13, found while building the watermark overlay): the first version fed the watermark image into `ffmpeg.input(path, loop=1, framerate=fps)` with no `t=` bound (matching how `_build_video_stream` already handles `type: "image"` items — but those ALSO always set `t=duration`, which this first attempt missed). `loop=1` makes an image input infinite (it never hits its own EOF); the `overlay` filter's default framesync behavior does not, by itself, stop at the finite main video's length once the second input is infinite — verified empirically, not assumed: a real 10-second test timeline ran for 3+ hours (280,000+ frames encoded) instead of finishing in seconds, before being killed manually. Fix: the watermark input now always gets `t=total_duration` (validated to be computable — `validate_timeline.py` already requires every item to have a numeric `duration` whenever `watermark: true` is used anywhere). Re-verified: the same timeline now renders in seconds, exactly 10.00s output duration.

## What this skill does NOT do

- Does not generate any image, video, audio, or caption text itself — pure assembly of already-produced assets. See `gemini-generator` for the generation side.
- Does not call any LLM/AI API, ever.
- Does not support transitions between segments (hard cuts only) — a `concat`-filter limitation this version doesn't attempt to work around with crossfades/wipes.
- Does not loop a music track shorter than the timeline, or trim one longer than needed beyond the padding described above — if `music.path` is much shorter than the total duration, the padded silence after it ends is real silence, not a loop.
- Does not compute a usable `total_duration` (and therefore skips the audio-padding fix and captions' end-of-track bound check) when any `video_track` item is type `video` with `duration` omitted — see Known Limitations.
- Does not support a multi-track crossfaded music bed (2 music files blended together) — GenVid's own real pipeline has this (`acrossfade`), deliberately not ported this round to keep scope controlled; a single `audio.music` file remains the only supported form.
- Does not position the watermark image itself (corner, margin, size) — always composited at `0:0`, full-frame; the image supplies its own internal layout (e.g. via `html-poster-composer`'s zone system). A caller wanting the watermark in a specific corner positions it inside the source image, not via a timeline field.

## Bundled files

- `scripts/validate_timeline.py` — CLI + importable `validate_timeline()`.
- `scripts/render_timeline.py` — CLI + importable `render()`; also writes the SRT file used for caption burn-in as a side effect (`<output>.srt`, next to the rendered video).
- `requirements.txt` — `ffmpeg-python`, `imageio-ffmpeg`.

## Verified

Real end-to-end render (2026-08-05): a 3-segment timeline (a Gemini-produced cartoon-fox portrait with Ken Burns → a real Veo clip of the same character blinking → a second Gemini-generated scene with Ken Burns), 3 non-overlapping captions matching each segment's timing, and a Gemini-produced voice narration ducked under a synthetic test music bed. Confirmed via `ffmpeg -i`: exactly 9.00s output duration (3×3s segments), correct 960x540 h264 video + aac audio streams. Confirmed via extracted frames at 1.0s/4.5s/8.5s: each caption appears burned in and correctly synced to its segment, Ken Burns zoom visibly progresses across the image segments. The rendered file was also sent to the project owner for a real playback check (duration/caption-sync/audio-ducking were verified structurally by this skill's author, not by ear/eye on the final composite).

**Stretch/own-audio/edge-fade addition (2026-08-13)**: real end-to-end render via real ffmpeg `lavfi` test sources (not mocked) — a 2-segment timeline: item 1 a 4s test clip WITH a real embedded audio tone, `duration: 6, stretch_from: 4, include_own_audio: true, own_audio_volume_db: -12`; item 2 a 4s test clip with NO audio stream at all, `duration: 5, stretch_from: 4, include_own_audio: true` (deliberately exercising the no-audio-track fallback), plus an 11s voice track spanning both. Rendered output confirmed via `ffmpeg -i`: ~10.92s duration (expected 11s, the small difference is normal whole-frame rounding at 24fps), correct video (h264, 320x240, 24fps) and audio (aac, 44100Hz) streams both present — confirming the stretch, the real-audio mixing, AND the silent fallback for the audio-less clip all worked correctly together in one render, not just individually. Re-verified with captions enabled (the fix above) — a frame extracted mid-first-scene visually shows the correct caption text burned in at the correct position.

**Watermark overlay + intro/outro cards (2026-08-13)**: real end-to-end render — a 3-item timeline (a solid-blue 2s intro card, `type: "image", ken_burns: false`; a 6s `testsrc` body clip with `watermark: true`; a solid-green 2s outro card) plus a real `watermark_image` (a transparent PNG rendered via `html-poster-composer`'s new `VIDEO_HD` preset + `transparent_background: true`, containing 2 text zones). Confirmed via `ffmpeg -i`: exactly 10.00s output duration (2+6+2), 1920x1080/24fps. Confirmed via 3 extracted frames (t=1s/5s/9s): the intro and outro frames are pure solid color with NO watermark visible; the body frame (t=5s) shows both watermark text lines correctly composited in the bottom corners over the test pattern — confirming the per-item `watermark` flag's time-gating works correctly, not just that the overlay filter runs at all. This same test run is what surfaced and confirmed the runaway-render bug above.

## Known limitations (v0.3.0)

- `total_duration` (needed for the sidechaincompress fix and for the caption-overrun validation check) is only computed when EVERY `video_track` item has an explicit numeric `duration` — a `video`-type item with `duration` omitted (meaning "use the clip's own length") makes both of those features silently skip, falling back to `-shortest`'s cruder truncation behavior. Always set an explicit `duration` on every item when audio ducking, `include_own_audio`, or caption-overrun checking matters (`include_own_audio` is validated as a hard requirement — see `validate_timeline.py`; the other two silently degrade).
- No crossfade/transition support between segments — hard cuts only.
- No music looping, no multi-track music crossfade — see "What this skill does NOT do".
- `zoompan`'s Ken Burns effect uses a single fixed zoom-in curve (`min(zoom+0.0015,1.15)`) — no pan direction, zoom-out, or per-item intensity control yet.
- `subtitles` filter styling (font, size, color, position) is not exposed as a timeline option yet — uses ffmpeg's built-in default caption rendering.
- No transitions/validation for audio format mismatches (e.g. a music file with an unusual sample rate) beyond what ffmpeg itself tolerates.
- `atempo` (used to keep a stretched clip's own audio in sync) is clamped to ffmpeg's native [0.5, 2.0] range — a `duration`/`stretch_from` ratio outside that (e.g. stretching a 4s clip to 10s, ratio 0.4) still stretches the VIDEO correctly but the clip's own audio's pitch/tempo correction saturates at the clamp boundary rather than chaining multiple `atempo` filters to reach the true ratio. Real-world Veo-style discrete-duration-to-narration-length ratios haven't been observed outside this range, but it isn't independently enforced or chained here.
- `_has_audio_stream()`'s "does this clip have audio" check runs a real `ffmpeg -i` subprocess per clip that requests `include_own_audio` (parsing stderr for "Audio:", since the portable `imageio-ffmpeg` binary doesn't bundle `ffprobe` and this project's own convention is never to depend on a host-system binary) — a small, real per-clip cost, not a bug, but worth knowing if rendering many `include_own_audio` clips.
