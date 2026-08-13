#!/usr/bin/env python3
"""Generate a video from text and/or an anchor image using Gemini's video
model (Veo), via the user's own API key (bring-your-own-key — this is NOT a
Scriptorium-managed AI backend). Requires GEMINI_API_KEY in the environment
(or --api-key).

Text-to-video:
    python generate_video.py "a neon hologram cat driving at top speed" out.mp4

Image-to-video (the image is treated as a fixed frame-0 anchor -- data/
references/image-to-video/NOTES.md's "causal, image-as-frame-0" lesson from
CogVideoX -- the model animates FROM it, it does not redraw it):
    python generate_video.py "the cat slowly turns its head and blinks" out.mp4 --image anchor.png

Image-to-video with frame interpolation (start AND end keyframe given; Veo
interpolates the motion between them):
    python generate_video.py "a smooth camera pan" out.mp4 --image start.png --last-frame end.png

Motion intensity (phrasing-based, like generate_image.py's strength
knobs -- Veo's API exposes no numeric motion-intensity parameter, see Known
limitations):
    python generate_video.py "..." out.mp4 --image anchor.png --motion-intensity subtle
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("google-genai not installed. Run: pip install -r requirements.txt")

DEFAULT_MODEL = "veo-3.1-generate-preview"
MOTION_LEVELS = ("subtle", "moderate", "energetic")

# Verified for real (2026-08-05): Veo rejects duration_seconds=7 with "must be
# between 4 and 8, inclusive" while duration_seconds=6 succeeds -- the error
# message is misleading boilerplate; the real constraint is a DISCRETE set,
# not a continuous range. Checked client-side before spending an API call.
VALID_DURATIONS_SECONDS = (4, 6, 8)

# Veo's GenerateVideosConfig has no numeric motion-intensity/motion-bucket
# equivalent (checked against the installed google-genai SDK's
# types.GenerateVideosConfig field list, 2026-08-05: fps, duration_seconds,
# seed, aspect_ratio, resolution, person_generation, negative_prompt,
# enhance_prompt, generate_audio, last_frame -- no motion-strength field) --
# same situation as generate_image.py's identity/style strength, so the
# same phrasing-based-level pattern is reused here for consistency across
# this skill's own generation scripts, not because it's the only conceivable design.
_MOTION_PHRASE = {
    "subtle": "Subtle, slow, minimal motion — small gestures, gentle camera drift, nothing sudden.",
    "moderate": "Natural, moderate motion — normal-paced movement and camera work.",
    "energetic": "Energetic, fast-paced, dynamic motion — pronounced movement and camera work.",
}


def _build_source(
    prompt: str,
    image_bytes: bytes | None,
    image_mime: str,
) -> "types.GenerateVideosSource":
    image = types.Image(image_bytes=image_bytes, mime_type=image_mime) if image_bytes else None
    return types.GenerateVideosSource(prompt=prompt, image=image)


def generate(
    client: "genai.Client",
    prompt: str,
    model: str,
    *,
    image_bytes: bytes | None = None,
    image_mime: str = "image/png",
    last_frame_bytes: bytes | None = None,
    last_frame_mime: str = "image/png",
    motion_intensity: str = "moderate",
    duration_seconds: int | None = None,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    negative_prompt: str | None = None,
    generate_audio: bool | None = None,
    seed: int | None = None,
    poll_interval_s: float = 10.0,
    timeout_s: float = 600.0,
) -> bytes:
    """Blocks until the async video-generation operation completes (Veo jobs
    typically take 1+ minutes), polling client.operations.get(). Returns the
    generated video's raw bytes."""
    if duration_seconds is not None and duration_seconds not in VALID_DURATIONS_SECONDS:
        raise ValueError(
            f"duration_seconds={duration_seconds} is not valid for Veo -- must be one of {VALID_DURATIONS_SECONDS} "
            "(a discrete set, not any integer in the range the API's own error message implies)."
        )

    full_prompt = f"{_MOTION_PHRASE[motion_intensity]} {prompt}"
    source = _build_source(full_prompt, image_bytes, image_mime)

    config_kwargs: dict = {}
    if duration_seconds is not None:
        config_kwargs["duration_seconds"] = duration_seconds
    if aspect_ratio is not None:
        config_kwargs["aspect_ratio"] = aspect_ratio
    if resolution is not None:
        config_kwargs["resolution"] = resolution
    if negative_prompt is not None:
        config_kwargs["negative_prompt"] = negative_prompt
    if generate_audio is not None:
        config_kwargs["generate_audio"] = generate_audio
    if seed is not None:
        config_kwargs["seed"] = seed
    if last_frame_bytes is not None:
        config_kwargs["last_frame"] = types.Image(image_bytes=last_frame_bytes, mime_type=last_frame_mime)
    config = types.GenerateVideosConfig(**config_kwargs) if config_kwargs else None

    operation = client.models.generate_videos(model=model, source=source, config=config)

    elapsed = 0.0
    while not operation.done:
        if elapsed >= timeout_s:
            raise TimeoutError(f"Video generation exceeded {timeout_s}s without completing.")
        time.sleep(poll_interval_s)
        elapsed += poll_interval_s
        operation = client.operations.get(operation)

    if operation.error:
        raise RuntimeError(f"Video generation failed: {operation.error}")

    generated = operation.result.generated_videos
    if not generated:
        raise RuntimeError("Operation completed but returned 0 generated videos.")

    video = generated[0].video
    data = client.files.download(file=video)  # sets video.video_bytes as a side effect too
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt", help="Text prompt describing the motion/scene")
    parser.add_argument("output_path", type=Path, help="Output .mp4 file")
    parser.add_argument("--image", type=Path, default=None, help="Anchor image (frame-0) for image-to-video generation")
    parser.add_argument("--last-frame", type=Path, default=None, help="End keyframe -- Veo interpolates motion between --image and this")
    parser.add_argument("--motion-intensity", choices=MOTION_LEVELS, default="moderate")
    parser.add_argument("--duration-seconds", type=int, default=None, choices=VALID_DURATIONS_SECONDS)
    parser.add_argument("--aspect-ratio", choices=("16:9", "9:16"), default=None)
    parser.add_argument("--resolution", choices=("720p", "1080p"), default=None)
    parser.add_argument("--negative-prompt", default=None)
    parser.add_argument("--generate-audio", action="store_true", default=None, help="Let Veo generate synced audio along with the video")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--poll-interval", type=float, default=10.0, help="Seconds between operation-status polls (default 10s)")
    parser.add_argument("--timeout", type=float, default=600.0, help="Max seconds to wait for the operation (default 600s)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing GEMINI_API_KEY. This is the user's OWN key (bring-your-own-key), "
            "not a backend managed by Scriptorium — set the environment variable or use --api-key."
        )
    client = genai.Client(api_key=api_key)

    if args.last_frame and not args.image:
        parser.error("--last-frame requires --image (interpolates between the two)")
    for path_arg in (args.image, args.last_frame):
        if path_arg and not path_arg.is_file():
            parser.error(f"Not found: {path_arg}")

    image_bytes = args.image.read_bytes() if args.image else None
    last_frame_bytes = args.last_frame.read_bytes() if args.last_frame else None

    print("Submitting video generation job (Veo jobs typically take 1+ minutes)...")
    data = generate(
        client,
        args.prompt,
        args.model,
        image_bytes=image_bytes,
        last_frame_bytes=last_frame_bytes,
        motion_intensity=args.motion_intensity,
        duration_seconds=args.duration_seconds,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        negative_prompt=args.negative_prompt,
        generate_audio=args.generate_audio,
        seed=args.seed,
        poll_interval_s=args.poll_interval,
        timeout_s=args.timeout,
    )
    args.output_path.write_bytes(data)
    print(f"OK: wrote {args.output_path} ({len(data) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
