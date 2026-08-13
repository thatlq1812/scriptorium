#!/usr/bin/env python3
"""Renders a validated timeline JSON (see validate_timeline.py / SKILL.md
schema) into a final .mp4, via ffmpeg. This is the "render" half of the
plan/render split borrowed from OpenTimelineIO (data/references/
auto-video-editing/NOTES.md #5): the timeline is plain data, this script is
the only place that turns it into an actual ffmpeg filter graph.

Usage:
    python render_timeline.py timeline.json output.mp4
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import ffmpeg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_timeline import validate_timeline  # noqa: E402

_toolchain_bootstrap = next(Path(__file__).resolve().parents[3].glob("*/toolchain-bootstrap"), None)
if _toolchain_bootstrap is None:
    sys.exit(
        "render_timeline.py requires the 'toolchain-bootstrap' skill installed as a "
        "sibling skill folder."
    )
sys.path.insert(0, str(_toolchain_bootstrap / "scripts"))
from resolve_ffmpeg import resolve_ffmpeg_path


def _fmt_srt_timestamp(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(captions: list[dict], srt_path: Path) -> None:
    lines = []
    for i, cap in enumerate(captions, start=1):
        lines.append(str(i))
        lines.append(f"{_fmt_srt_timestamp(cap['start'])} --> {_fmt_srt_timestamp(cap['end'])}")
        lines.append(cap["text"])
        lines.append("")
    srt_path.write_text("\n".join(lines), encoding="utf-8")


def _escape_filter_path(path: Path) -> str:
    """ffmpeg's filter-graph argument parser treats ':' and '\\' specially --
    a bare Windows path like C:\\foo\\bar.srt breaks the subtitles filter.
    Forward-slash the path, then escape the drive-letter colon."""
    s = str(path).replace("\\", "/")
    return s.replace(":", "\\:")


def _build_video_stream(video_track: list[dict], base_dir: Path, width: int, height: int, fps: float):
    segments = []
    for item in video_track:
        path = str(base_dir / item["path"])
        duration = item.get("duration")
        if item["type"] == "image":
            stream = ffmpeg.input(path, loop=1, t=duration, framerate=fps)
            stream = stream.filter("scale", width * 2, -2)  # upscale first -- reduces zoompan jitter, common idiom
            if item.get("ken_burns", True):
                d_frames = max(1, int(round(duration * fps)))
                stream = stream.filter("zoompan", z="min(zoom+0.0015,1.15)", d=d_frames, s=f"{width}x{height}", fps=fps)
            else:
                stream = stream.filter("scale", width, height)
            stream = stream.filter("setsar", 1)
        else:
            stream = ffmpeg.input(path)
            stretch_from = item.get("stretch_from")
            if stretch_from:
                # Lengthen/compress the clip via slow-motion (setpts) to exactly hit
                # `duration`, rather than trimming -- for a clip whose OWN native
                # length (stretch_from, e.g. a generation API's discrete duration
                # set) doesn't match what this scene actually needs (e.g. the real
                # measured length of a voice track). Never used together with a
                # plain trim -- the two are different fits for the same field.
                stretch_factor = duration / stretch_from
                stream = stream.filter("setpts", f"{stretch_factor}*PTS")
            elif duration:
                stream = stream.trim(duration=duration).filter("setpts", "PTS-STARTPTS")
            stream = stream.filter("scale", width, height, force_original_aspect_ratio="decrease")
            stream = stream.filter("pad", width, height, "(ow-iw)/2", "(oh-ih)/2")
            stream = stream.filter("setsar", 1)
            stream = stream.filter("fps", fps=fps)
        segments.append(stream)

    video = segments[0] if len(segments) == 1 else ffmpeg.concat(*segments, v=1, a=0)
    return video


def _build_watermark_enable_expr(video_track: list[dict]) -> str | None:
    """ffmpeg 'enable' expression covering every time range where a
    video_track item opted into the watermark (validate_timeline.py already
    guarantees every item has a numeric duration whenever any item sets
    watermark=True). Adjacent opted-in items merge into one between() clause
    instead of one per item -- the common real case (every scene except a
    leading intro card and trailing outro card) is exactly one contiguous
    span, but this doesn't assume that; genuinely discontiguous spans still
    work, just as more OR'd clauses."""
    ranges: list[tuple[float, float]] = []
    t = 0.0
    for item in video_track:
        d = item["duration"]
        if item.get("watermark"):
            if ranges and abs(t - ranges[-1][1]) < 1e-6:
                ranges[-1] = (ranges[-1][0], t + d)
            else:
                ranges.append((t, t + d))
        t += d
    if not ranges:
        return None
    if len(ranges) == 1:
        s, e = ranges[0]
        return f"between(t,{s:.3f},{e:.3f})"
    clauses = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in ranges)
    return f"if({clauses},1,0)"


def _has_audio_stream(path: str, ffmpeg_path: str) -> bool:
    """Checks for an audio stream using ONLY the resolved ffmpeg binary (never
    ffprobe -- toolchain-bootstrap's portable ffmpeg resolution bundles ffmpeg
    itself, not ffprobe, and this project's own convention is never to depend
    on a host-system binary being present). `ffmpeg -i <path>` with no output
    always exits non-zero but still prints real stream info to stderr (e.g.
    "Stream #0:1: Audio: ...") -- a well-known, portable technique."""
    try:
        result = subprocess.run([ffmpeg_path, "-i", path], capture_output=True, text=True, timeout=15)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return "Audio:" in result.stderr


def _build_own_audio_segment(item: dict, base_dir: Path, duration: float, ffmpeg_path: str):
    """The real audio segment for one video_track item's own embedded audio
    track (stretch-matched to the same factor as its video, volume-adjusted,
    short edge-faded to avoid a click/pop at the concat boundary) -- or
    silence, if the item doesn't request/have one. Every segment is EXACTLY
    `duration` long so the concatenated own-audio track stays time-aligned
    with the video track's own scene boundaries, whichever branch it takes."""
    path = str(base_dir / item["path"])
    fade = min(0.1, duration / 4)  # never fade more than 1/4 of a very short segment
    if item.get("include_own_audio") and item.get("type") == "video" and _has_audio_stream(path, ffmpeg_path):
        seg = ffmpeg.input(path).audio
        stretch_from = item.get("stretch_from")
        if stretch_from:
            # Same stretch ratio as the video's own setpts, inverted for audio
            # tempo (atempo speeds up/down instead of changing pitch/duration
            # via resampling) -- keeps this ambient track in sync with the
            # now-stretched video. Clamped to ffmpeg's own atempo range.
            atempo = max(0.5, min(2.0, stretch_from / duration))
            seg = seg.filter("atempo", atempo)
        seg = seg.filter("atrim", duration=duration).filter("asetpts", "PTS-STARTPTS")
        volume_db = item.get("own_audio_volume_db", 0)
        if volume_db:
            seg = seg.filter("volume", f"{volume_db}dB")
        seg = seg.filter("afade", t="in", d=fade).filter("afade", t="out", st=max(0, duration - fade), d=fade)
        return seg
    return ffmpeg.input("anullsrc=r=48000:cl=stereo", f="lavfi", t=duration).audio


def _build_own_audio_track(video_track: list[dict], base_dir: Path, ffmpeg_path: str):
    """Concatenates every video_track item's own-audio segment (real or
    silence) into ONE continuous track spanning the whole timeline, time-
    aligned with the video track. Returns None if no item actually requests
    include_own_audio (the common case -- skip building an all-silence track
    nobody asked for)."""
    if not any(item.get("include_own_audio") for item in video_track if isinstance(item, dict)):
        return None
    segments = [
        _build_own_audio_segment(item, base_dir, item["duration"], ffmpeg_path)
        for item in video_track
    ]
    return segments[0] if len(segments) == 1 else ffmpeg.concat(*segments, v=0, a=1)


def _pad_to_duration(stream, total_duration: float | None):
    """sidechaincompress (and several other multi-input audio filters) stop
    producing output the moment their SHORTER input ends -- verified for real
    (2026-08-05): a 3.24s voice track sidechain-ducking a 15s music bed
    truncated the whole mix to 3.24s, not the intended full timeline length.
    Padding both operands to the same known total_duration BEFORE mixing
    fixes this at the source instead of trying to work around it after."""
    if total_duration is None:
        return stream
    return stream.filter("apad").filter("atrim", duration=total_duration).filter("asetpts", "PTS-STARTPTS")


def _build_audio_stream(audio_cfg: dict | None, base_dir: Path, total_duration: float | None, own_audio_stream=None):
    """Mixes whichever of voice / music / per-clip own-audio are actually
    present into one final stream. Ducking is the one real special case
    (music sidechains OFF voice specifically) and is resolved before the
    uniform final amix; everything else just joins an N-input amix."""
    audio_cfg = audio_cfg or {}
    voice_cfg = audio_cfg.get("voice")
    music_cfg = audio_cfg.get("music")

    voice_stream = ffmpeg.input(str(base_dir / voice_cfg["path"])).audio if voice_cfg else None
    if voice_stream is not None:
        voice_stream = _pad_to_duration(voice_stream, total_duration)

    music_stream = None
    if music_cfg:
        music_stream = ffmpeg.input(str(base_dir / music_cfg["path"])).audio
        music_stream = music_stream.filter("volume", music_cfg.get("volume", 1.0))
        music_stream = _pad_to_duration(music_stream, total_duration)

    if own_audio_stream is not None:
        own_audio_stream = _pad_to_duration(own_audio_stream, total_duration)

    if music_stream is not None and voice_stream is not None and music_cfg.get("duck_under_voice"):
        # sidechaincompress: [main=music][sidechain=voice] -> music ducks whenever voice is loud.
        # Both operands are already padded/trimmed to total_duration above, so
        # the filter's shorter-input-wins behavior no longer truncates the mix.
        # voice_stream is consumed twice (as the sidechain trigger AND in the
        # final amix) -- ffmpeg-python requires an explicit asplit for that,
        # not just reusing the same stream object in two filter calls.
        voice_split = voice_stream.filter_multi_output("asplit")
        ducked_music = ffmpeg.filter([music_stream, voice_split.stream(0)], "sidechaincompress", threshold=0.05, ratio=8, attack=5, release=200)
        voice_stream = voice_split.stream(1)
        music_stream = ducked_music

    streams = [s for s in (voice_stream, music_stream, own_audio_stream) if s is not None]
    if not streams:
        return None
    if len(streams) == 1:
        return streams[0]
    return ffmpeg.filter(streams, "amix", inputs=len(streams), duration="longest", dropout_transition=0)


def render(timeline: dict, base_dir: Path, output_path: Path, ffmpeg_path: str) -> None:
    # Resolved to absolute up front: the real ffmpeg subprocess below runs with
    # its OWN cwd set to output_path's directory (see the subtitles-path fix
    # further down), so any path built from a caller-supplied relative
    # base_dir/output_path must be made absolute before that cwd change, not
    # after -- otherwise it would silently resolve against the wrong directory.
    base_dir = base_dir.resolve()
    output_path = output_path.resolve()

    width = timeline["output"]["width"]
    height = timeline["output"]["height"]
    fps = timeline["output"]["fps"]

    video = _build_video_stream(timeline["video_track"], base_dir, width, height, fps)

    captions = timeline.get("captions")
    if captions:
        srt_path = output_path.with_suffix(".srt")
        write_srt(captions, srt_path)
        # A real, reproducible bug (found 2026-08-13, not just theoretical):
        # the subtitles filter's OWN argument parser treats ':' and '\' as
        # structural separators, so a bare absolute Windows path (drive-letter
        # colon) breaks it -- and manually escaping those characters just
        # shifts the problem, since ffmpeg-python's own filter-argument
        # serializer escapes '\' and others AGAIN on top, compounding into
        # garbage no combination of manual pre-escaping fixed (verified
        # empirically against real ffmpeg, not assumed). The actual fix:
        # sidestep the escaping question entirely by referencing the SRT file
        # with a bare relative filename (no colon, no backslash, nothing to
        # escape) and running ffmpeg with its cwd set to the same directory
        # (see the subprocess.run(cwd=...) call below) -- every OTHER path in
        # this render (inputs, output) stays absolute and is unaffected by
        # that cwd, since only the subtitles filter's argument goes through
        # the filter-graph string parser.
        video = video.filter("subtitles", srt_path.name)

    durations = [item.get("duration") for item in timeline["video_track"]]
    total_duration = sum(durations) if all(isinstance(d, (int, float)) for d in durations) else None

    watermark_image = timeline.get("watermark_image")
    if watermark_image:
        # Applied AFTER subtitles -- a persistent brand/disclaimer overlay
        # stays on top rather than getting drawn under burned-in captions.
        # Expected to be a full-output-frame image (matching output.width x
        # output.height, typically a transparent PNG rendered by
        # html-poster-composer's transparent_background mode) with its own
        # visual content already positioned within it -- this filter always
        # overlays at 0:0, it does not itself do corner/margin placement.
        #
        # Real bug found and fixed (2026-08-13): the watermark image input
        # MUST be bounded with t=total_duration. loop=1 alone makes the
        # image source infinite (it never hits its own EOF), and the
        # overlay filter's default framesync behavior does NOT stop at the
        # finite main video's length in that case -- verified empirically:
        # an unbounded version of this ran for 3+ hours (280,000+ frames)
        # instead of finishing a 10-second render. validate_timeline.py
        # already guarantees every item has a numeric duration whenever any
        # item sets watermark=True, so total_duration is always computable
        # here.
        enable_expr = _build_watermark_enable_expr(timeline["video_track"])
        if enable_expr:
            wm = ffmpeg.input(str(base_dir / watermark_image), loop=1, t=total_duration, framerate=fps)
            video = ffmpeg.filter([video, wm], "overlay", x=0, y=0, enable=enable_expr)

    own_audio_stream = _build_own_audio_track(timeline["video_track"], base_dir, ffmpeg_path)
    audio = _build_audio_stream(timeline.get("audio"), base_dir, total_duration, own_audio_stream=own_audio_stream)

    if audio is not None:
        out = ffmpeg.output(video, audio, str(output_path), vcodec="libx264", acodec="aac", pix_fmt="yuv420p", shortest=None)
    else:
        out = ffmpeg.output(video, str(output_path), vcodec="libx264", pix_fmt="yuv420p")

    args = ffmpeg.compile(out, cmd=ffmpeg_path, overwrite_output=True)
    result = subprocess.run(args, cwd=str(output_path.parent), capture_output=True)
    if result.returncode != 0:
        raise ffmpeg.Error("ffmpeg", result.stdout, result.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("timeline_path", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()

    if not args.timeline_path.is_file():
        sys.exit(f"Not found: {args.timeline_path}")

    import json

    timeline = json.loads(args.timeline_path.read_text(encoding="utf-8"))
    base_dir = args.timeline_path.parent

    errors = validate_timeline(timeline, base_dir=base_dir)
    if errors:
        print(f"INVALID timeline, refusing to render ({len(errors)} error(s)):")
        for err in errors:
            print(f"  - {err}")
        return 1

    ffmpeg_path = resolve_ffmpeg_path()
    try:
        render(timeline, base_dir, args.output_path, ffmpeg_path)
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        sys.exit(f"ffmpeg failed:\n{stderr[-3000:]}")

    print(f"OK: wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
