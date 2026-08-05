#!/usr/bin/env python3
"""Ties image-generator-gemini, video-generator-gemini, audio-generator-gemini,
and video-assembly-composer together into one script -> images -> videos ->
audio -> assembled-video pipeline, driven by a topic.

Stages (state/resume via pipeline_state.PipelineState, embedded in
<project_dir>/project.json -- re-running skips whatever's already `done`):
  script    -- generate_script.py (Gemini text, JSON mode) -> scenes.json.
               PAUSES here unless --approve-script is passed (human-in-the-loop
               checkpoint BEFORE any image/video/audio quota is spent -- the
               Viral-Faceless-Shorts-Generator lesson, data/references/
               e2e-pipeline/NOTES.md #5).
  images    -- one image-generator-gemini call per scene. The FIRST scene's
               image becomes the style anchor for every scene after it
               (auto-anchor, unless --anchor-profile is given instead).
  videos    -- one video-generator-gemini call per scene, anchored on that
               scene's image.
  audio     -- one audio-generator-gemini TTS call per scene, then
               concatenated into one combined voice track.
  assembly  -- builds a video-assembly-composer timeline.json (video clips +
               captions from narration + the combined voice track) and
               renders final.mp4.

Every Gemini call is wrapped in retry.with_retry() (exponential backoff).

Usage:
    python run_pipeline.py my_project --topic "a fox's rainy day" --n-scenes 2
    # review my_project/scenes.json, then:
    python run_pipeline.py my_project --topic "a fox's rainy day" --n-scenes 2 --approve-script
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from google import genai
except ImportError:
    sys.exit("google-genai not installed. Run: pip install -r requirements.txt")

_HERE = Path(__file__).resolve()
_SKILLS_DIR = _HERE.parents[2]

sys.path.insert(0, str(_HERE.parent))
from pipeline_state import PipelineState  # noqa: E402
from retry import with_retry  # noqa: E402
from generate_script import generate_script  # noqa: E402
from concat_audio import concat_wavs  # noqa: E402

sys.path.insert(0, str(_SKILLS_DIR / "image-generator-gemini" / "scripts"))
from generate_image import generate as image_generate, DEFAULT_MODEL as IMAGE_MODEL, _load_anchor_profile_kwargs  # noqa: E402

sys.path.insert(0, str(_SKILLS_DIR / "video-generator-gemini" / "scripts"))
from generate_video import generate as video_generate, DEFAULT_MODEL as VIDEO_MODEL  # noqa: E402

sys.path.insert(0, str(_SKILLS_DIR / "audio-generator-gemini" / "scripts"))
from generate_speech import generate as audio_generate, write_wav, DEFAULT_MODEL as AUDIO_MODEL  # noqa: E402

sys.path.insert(0, str(_SKILLS_DIR / "video-assembly-composer" / "scripts"))
from render_timeline import render as render_timeline  # noqa: E402
from validate_timeline import validate_timeline  # noqa: E402

sys.path.insert(0, str(_SKILLS_DIR / "ffmpeg-bootstrap" / "scripts"))
from resolve_ffmpeg import resolve_ffmpeg_path  # noqa: E402


def _build_timeline(scenes: list[dict], videos_dir: Path, combined_voice_path: Path, width: int, height: int, fps: int) -> dict:
    video_track = []
    captions = []
    cursor = 0.0
    for scene in scenes:
        duration = float(scene["duration_seconds"])
        video_track.append({"type": "video", "path": str((videos_dir / f"{scene['id']}.mp4").resolve()), "duration": duration})
        captions.append({"text": scene["narration"], "start": cursor, "end": cursor + duration})
        cursor += duration
    return {
        "output": {"width": width, "height": height, "fps": fps},
        "video_track": video_track,
        "captions": captions,
        "audio": {"voice": {"path": str(combined_voice_path.resolve())}},
    }


def run(project_dir: Path, args: argparse.Namespace) -> int:
    project_dir.mkdir(parents=True, exist_ok=True)
    state = PipelineState(project_dir / "project.json")
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Missing GEMINI_API_KEY — set the environment variable or use --api-key.")
    client = genai.Client(api_key=api_key)

    scenes_path = project_dir / "scenes.json"

    # --- Stage: script (human-approval checkpoint) ---
    if not state.is_done("script"):
        print("[script] generating...")
        script = with_retry()(generate_script)(client, args.topic, args.n_scenes, args.style_notes)
        scenes_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
        state.mark_done("script", artifacts=[str(scenes_path)])
        print(f"[script] wrote {scenes_path}. Review it, then re-run with --approve-script to continue.")
        return 0

    script = json.loads(scenes_path.read_text(encoding="utf-8"))
    if not args.approve_script:
        print(f"[script] already generated ({scenes_path}). Re-run with --approve-script to continue past this checkpoint.")
        return 0

    scenes = script["scenes"]

    # --- Stage: images ---
    images_dir = project_dir / "images"
    images_dir.mkdir(exist_ok=True)
    if not state.is_done("images"):
        print("[images] generating...")
        anchor_kwargs = _load_anchor_profile_kwargs(Path(args.anchor_profile)) if args.anchor_profile else {}
        chain_style_bytes: bytes | None = None
        for scene in scenes:
            out_path = images_dir / f"{scene['id']}.png"
            if out_path.exists():
                if chain_style_bytes is None and not anchor_kwargs:
                    chain_style_bytes = out_path.read_bytes()
                continue
            kwargs = dict(anchor_kwargs)
            if not anchor_kwargs and chain_style_bytes is not None:
                kwargs["style_refs"] = [chain_style_bytes]
            print(f"  {scene['id']} ...", end="", flush=True)
            data = with_retry()(image_generate)(client, scene["visual_prompt"], IMAGE_MODEL, **kwargs)
            out_path.write_bytes(data)
            print(" OK")
            if not anchor_kwargs and chain_style_bytes is None:
                chain_style_bytes = data
        state.mark_done("images", artifacts=[str(images_dir / f"{s['id']}.png") for s in scenes])

    # --- Stage: videos ---
    videos_dir = project_dir / "videos"
    videos_dir.mkdir(exist_ok=True)
    if not state.is_done("videos"):
        print("[videos] generating (this takes 1+ minute per scene)...")
        for scene in scenes:
            out_path = videos_dir / f"{scene['id']}.mp4"
            if out_path.exists():
                continue
            image_bytes = (images_dir / f"{scene['id']}.png").read_bytes()
            print(f"  {scene['id']} ...", end="", flush=True)
            data = with_retry(max_retries=2)(video_generate)(
                client, scene["visual_prompt"], VIDEO_MODEL,
                image_bytes=image_bytes, motion_intensity=args.motion_intensity,
                duration_seconds=int(scene["duration_seconds"]),
            )
            out_path.write_bytes(data)
            print(" OK")
        state.mark_done("videos", artifacts=[str(videos_dir / f"{s['id']}.mp4") for s in scenes])

    # --- Stage: audio ---
    audio_dir = project_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    combined_voice_path = audio_dir / "combined_voice.wav"
    if not state.is_done("audio"):
        print("[audio] generating...")
        for scene in scenes:
            out_path = audio_dir / f"{scene['id']}.wav"
            if out_path.exists():
                continue
            print(f"  {scene['id']} ...", end="", flush=True)
            pcm = with_retry()(audio_generate)(client, scene["narration"], AUDIO_MODEL, voice=args.voice)
            write_wav(pcm, out_path)
            print(" OK")
        concat_wavs([audio_dir / f"{s['id']}.wav" for s in scenes], combined_voice_path)
        state.mark_done("audio", artifacts=[str(combined_voice_path)])

    # --- Stage: assembly ---
    final_path = project_dir / "final.mp4"
    if not state.is_done("assembly"):
        print("[assembly] rendering final video...")
        timeline = _build_timeline(scenes, videos_dir, combined_voice_path, args.width, args.height, args.fps)
        (project_dir / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
        timeline_errors = validate_timeline(timeline, base_dir=project_dir)
        if timeline_errors:
            sys.exit("Generated timeline.json failed validation (this is a bug, not a content problem):\n" + "\n".join(f"- {e}" for e in timeline_errors))
        render_timeline(timeline, project_dir, final_path, resolve_ffmpeg_path())
        state.mark_done("assembly", artifacts=[str(final_path)])

    print(f"Pipeline complete: {final_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--n-scenes", type=int, required=True)
    parser.add_argument("--style-notes", default="")
    parser.add_argument("--anchor-profile", default=None, help="media-anchor-profile JSON, used for every scene's image instead of auto-anchor chaining")
    parser.add_argument("--motion-intensity", default="moderate", choices=("subtle", "moderate", "energetic"))
    parser.add_argument("--voice", default=None)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--approve-script", action="store_true", help="Confirms scenes.json has been reviewed; proceeds past the script checkpoint")
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    return run(args.project_dir, args)


if __name__ == "__main__":
    sys.exit(main())
