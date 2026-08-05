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
import sys
from pathlib import Path

import ffmpeg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_timeline import validate_timeline  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ffmpeg-bootstrap" / "scripts"))
try:
    from resolve_ffmpeg import resolve_ffmpeg_path
except ImportError:
    sys.exit(
        "render_timeline.py requires the 'ffmpeg-bootstrap' skill installed as a "
        "sibling skill folder (.claude/skills/ffmpeg-bootstrap/)."
    )


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
            if duration:
                stream = stream.trim(duration=duration).filter("setpts", "PTS-STARTPTS")
            stream = stream.filter("scale", width, height, force_original_aspect_ratio="decrease")
            stream = stream.filter("pad", width, height, "(ow-iw)/2", "(oh-ih)/2")
            stream = stream.filter("setsar", 1)
            stream = stream.filter("fps", fps=fps)
        segments.append(stream)

    video = segments[0] if len(segments) == 1 else ffmpeg.concat(*segments, v=1, a=0)
    return video


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


def _build_audio_stream(audio_cfg: dict | None, base_dir: Path, total_duration: float | None):
    if not audio_cfg:
        return None

    voice_cfg = audio_cfg.get("voice")
    music_cfg = audio_cfg.get("music")
    voice_stream = ffmpeg.input(str(base_dir / voice_cfg["path"])).audio if voice_cfg else None
    if voice_stream is not None:
        voice_stream = _pad_to_duration(voice_stream, total_duration)

    if not music_cfg:
        return voice_stream

    music_stream = ffmpeg.input(str(base_dir / music_cfg["path"])).audio
    volume = music_cfg.get("volume", 1.0)
    music_stream = music_stream.filter("volume", volume)
    music_stream = _pad_to_duration(music_stream, total_duration)

    if voice_stream is None:
        return music_stream

    if music_cfg.get("duck_under_voice"):
        # sidechaincompress: [main=music][sidechain=voice] -> music ducks whenever voice is loud.
        # Both operands are already padded/trimmed to total_duration above, so
        # the filter's shorter-input-wins behavior no longer truncates the mix.
        # voice_stream is consumed twice (as the sidechain trigger AND in the
        # final amix) -- ffmpeg-python requires an explicit asplit for that,
        # not just reusing the same stream object in two filter calls.
        voice_split = voice_stream.filter_multi_output("asplit")
        ducked_music = ffmpeg.filter([music_stream, voice_split.stream(0)], "sidechaincompress", threshold=0.05, ratio=8, attack=5, release=200)
        return ffmpeg.filter([voice_split.stream(1), ducked_music], "amix", inputs=2, duration="longest", dropout_transition=0)

    return ffmpeg.filter([voice_stream, music_stream], "amix", inputs=2, duration="longest", dropout_transition=0)


def render(timeline: dict, base_dir: Path, output_path: Path, ffmpeg_path: str) -> None:
    width = timeline["output"]["width"]
    height = timeline["output"]["height"]
    fps = timeline["output"]["fps"]

    video = _build_video_stream(timeline["video_track"], base_dir, width, height, fps)

    captions = timeline.get("captions")
    if captions:
        srt_path = output_path.with_suffix(".srt")
        write_srt(captions, srt_path)
        video = video.filter("subtitles", _escape_filter_path(srt_path))

    durations = [item.get("duration") for item in timeline["video_track"]]
    total_duration = sum(durations) if all(isinstance(d, (int, float)) for d in durations) else None
    audio = _build_audio_stream(timeline.get("audio"), base_dir, total_duration)

    if audio is not None:
        out = ffmpeg.output(video, audio, str(output_path), vcodec="libx264", acodec="aac", pix_fmt="yuv420p", shortest=None)
    else:
        out = ffmpeg.output(video, str(output_path), vcodec="libx264", pix_fmt="yuv420p")

    ffmpeg.run(out, cmd=ffmpeg_path, overwrite_output=True, capture_stdout=True, capture_stderr=True)


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
