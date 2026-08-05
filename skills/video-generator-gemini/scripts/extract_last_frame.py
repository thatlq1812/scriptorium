#!/usr/bin/env python3
"""Extracts the LAST frame of a video as a PNG -- used to chain multiple
generate_video.py calls into a longer video than one Veo call supports: feed
segment N's last frame back in as segment N+1's --image, treating it as the
next fixed frame-0 anchor (the CogVideoX "causal, frame-0" chaining lesson,
data/references/image-to-video/NOTES.md #3).

Usage:
    python extract_last_frame.py segment1.mp4 segment1_last_frame.png
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ffmpeg-bootstrap" / "scripts"))
try:
    from resolve_ffmpeg import resolve_ffmpeg_path
except ImportError:
    sys.exit(
        "extract_last_frame.py requires the 'ffmpeg-bootstrap' skill installed as a "
        "sibling skill folder (.claude/skills/ffmpeg-bootstrap/)."
    )


def extract_last_frame(video_path: Path, output_path: Path, seek_window_s: float = 1.5) -> None:
    """Seeks to `seek_window_s` before EOF, then uses the image2 muxer's
    -update 1 to keep overwriting output_path with each decoded frame -- the
    final write is the true last frame. A well-known ffmpeg idiom, not a
    frame-count-based seek (which would need an extra ffprobe call)."""
    ffmpeg = resolve_ffmpeg_path()
    cmd = [
        ffmpeg, "-y",
        "-sseof", f"-{seek_window_s}",
        "-i", str(video_path),
        "-vsync", "0",
        "-update", "1",
        "-q:v", "1",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if result.returncode != 0 or not output_path.is_file():
        raise RuntimeError(f"ffmpeg failed to extract last frame:\n{result.stderr[-2000:]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument(
        "--seek-window", type=float, default=1.5,
        help="Seconds before end-of-file to start decoding from (default 1.5s -- must be less than the video's total duration)",
    )
    args = parser.parse_args()

    if not args.video_path.is_file():
        sys.exit(f"Not found: {args.video_path}")

    extract_last_frame(args.video_path, args.output_path, args.seek_window)
    print(f"OK: wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
