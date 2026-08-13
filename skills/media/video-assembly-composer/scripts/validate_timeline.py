#!/usr/bin/env python3
"""Deterministic validator for a video-assembly timeline JSON (the "plan"
half of video-assembly-composer's plan/render split, per the OpenTimelineIO
lesson in data/references/auto-video-editing/NOTES.md #5: describe the
timeline as data BEFORE any ffmpeg call, so a bad path/duration is caught
before burning render time). No AI call, stdlib only.

CLI:
    python validate_timeline.py timeline.json

Importable:
    from validate_timeline import validate_timeline
    errors = validate_timeline(timeline_dict, base_dir=timeline_path.parent)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VIDEO_ITEM_TYPES = ("image", "video")


def _resolve(base_dir: Path, path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else base_dir / p


def _validate_output(output: dict) -> list[str]:
    errors = []
    if not isinstance(output, dict):
        return ["'output' must be an object"]
    for key in ("width", "height"):
        val = output.get(key)
        if not isinstance(val, int) or val <= 0:
            errors.append(f"'output.{key}' must be a positive integer, got {val!r}")
    fps = output.get("fps")
    if not isinstance(fps, (int, float)) or fps <= 0:
        errors.append(f"'output.fps' must be a positive number, got {fps!r}")
    return errors


def _validate_video_track(video_track, base_dir: Path) -> list[str]:
    errors = []
    if not isinstance(video_track, list) or not video_track:
        return ["'video_track' must be a non-empty list"]
    for i, item in enumerate(video_track):
        prefix = f"video_track[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        item_type = item.get("type")
        if item_type not in VIDEO_ITEM_TYPES:
            errors.append(f"{prefix}.type must be one of {VIDEO_ITEM_TYPES}, got {item_type!r}")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{prefix}.path must be a non-empty string")
        elif not _resolve(base_dir, path).is_file():
            errors.append(f"{prefix}.path does not exist on disk: {_resolve(base_dir, path)}")
        duration = item.get("duration")
        if item_type == "image" and (not isinstance(duration, (int, float)) or duration <= 0):
            errors.append(f"{prefix}.duration is required and must be > 0 for type 'image', got {duration!r}")
        if item_type == "video" and duration is not None and (not isinstance(duration, (int, float)) or duration <= 0):
            errors.append(f"{prefix}.duration must be > 0 if set for type 'video', got {duration!r}")
        if "ken_burns" in item and not isinstance(item["ken_burns"], bool):
            errors.append(f"{prefix}.ken_burns must be a boolean, got {item['ken_burns']!r}")
        if item_type == "video" and item.get("ken_burns"):
            errors.append(f"{prefix}.ken_burns is only meaningful for type 'image', not 'video'")
    return errors


def _validate_captions(captions, total_duration: float | None) -> list[str]:
    errors = []
    if captions is None:
        return errors
    if not isinstance(captions, list):
        return ["'captions' must be a list if present"]
    prev_end = 0.0
    for i, cap in enumerate(captions):
        prefix = f"captions[{i}]"
        if not isinstance(cap, dict):
            errors.append(f"{prefix} must be an object")
            continue
        text = cap.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{prefix}.text must be a non-empty string")
        start, end = cap.get("start"), cap.get("end")
        if not isinstance(start, (int, float)) or start < 0:
            errors.append(f"{prefix}.start must be >= 0, got {start!r}")
        if not isinstance(end, (int, float)) or not isinstance(start, (int, float)) or end <= start:
            errors.append(f"{prefix}.end must be > start, got start={start!r} end={end!r}")
        if isinstance(start, (int, float)) and start < prev_end - 1e-6:
            errors.append(f"{prefix} overlaps the previous caption (start={start} < previous end={prev_end})")
        if isinstance(end, (int, float)):
            prev_end = end
        if total_duration is not None and isinstance(end, (int, float)) and end > total_duration + 1e-6:
            errors.append(f"{prefix}.end ({end}) exceeds the video track's total duration ({total_duration})")
    return errors


def _validate_audio(audio, base_dir: Path) -> list[str]:
    errors = []
    if audio is None:
        return errors
    if not isinstance(audio, dict):
        return ["'audio' must be an object if present"]
    unknown = set(audio.keys()) - {"voice", "music"}
    if unknown:
        errors.append(f"'audio' has unknown key(s): {sorted(unknown)}")

    voice = audio.get("voice")
    if voice is not None:
        if not isinstance(voice, dict) or not isinstance(voice.get("path"), str):
            errors.append("'audio.voice.path' must be a string")
        elif not _resolve(base_dir, voice["path"]).is_file():
            errors.append(f"'audio.voice.path' does not exist on disk: {_resolve(base_dir, voice['path'])}")

    music = audio.get("music")
    if music is not None:
        if not isinstance(music, dict) or not isinstance(music.get("path"), str):
            errors.append("'audio.music.path' must be a string")
        elif not _resolve(base_dir, music["path"]).is_file():
            errors.append(f"'audio.music.path' does not exist on disk: {_resolve(base_dir, music['path'])}")
        volume = music.get("volume", 1.0)
        if not isinstance(volume, (int, float)) or not (0.0 <= volume <= 1.0):
            errors.append(f"'audio.music.volume' must be between 0.0 and 1.0, got {volume!r}")
        if music.get("duck_under_voice") and voice is None:
            errors.append("'audio.music.duck_under_voice' is true but no 'audio.voice' is declared to duck under")

    return errors


def validate_timeline(timeline: dict, base_dir: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(timeline, dict):
        return [f"Timeline must be a JSON object, got {type(timeline).__name__}"]

    if "output" not in timeline:
        errors.append("'output' is required (width/height/fps)")
    else:
        errors.extend(_validate_output(timeline["output"]))

    if "video_track" not in timeline:
        errors.append("'video_track' is required")
    else:
        errors.extend(_validate_video_track(timeline["video_track"], base_dir))

    total_duration = None
    if "video_track" in timeline and isinstance(timeline["video_track"], list):
        durations = [item.get("duration") for item in timeline["video_track"] if isinstance(item, dict)]
        if all(isinstance(d, (int, float)) for d in durations) and durations:
            total_duration = sum(durations)

    errors.extend(_validate_captions(timeline.get("captions"), total_duration))
    errors.extend(_validate_audio(timeline.get("audio"), base_dir))

    unknown_top = set(timeline.keys()) - {"output", "video_track", "captions", "audio"}
    if unknown_top:
        errors.append(f"Timeline has unknown top-level key(s): {sorted(unknown_top)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("timeline_path", type=Path)
    args = parser.parse_args()

    if not args.timeline_path.is_file():
        sys.exit(f"Not found: {args.timeline_path}")

    try:
        timeline = json.loads(args.timeline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"Invalid JSON in {args.timeline_path}: {exc}")

    errors = validate_timeline(timeline, base_dir=args.timeline_path.parent)
    if errors:
        print(f"INVALID: {args.timeline_path} ({len(errors)} error(s))")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"OK: {args.timeline_path} is a valid timeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
