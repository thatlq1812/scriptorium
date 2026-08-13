#!/usr/bin/env python3
"""Ties gemini-generator (image/video/audio) and video-assembly-composer
together into one script -> images -> videos ->
audio -> assembled-video pipeline, driven by a topic.

Stages (state/resume via pipeline_state.PipelineState, embedded in
<project_dir>/project.json -- re-running skips whatever's already `done`):
  script    -- generate_script.py (Gemini text, JSON mode) -> scenes.json.
               PAUSES here unless --approve-script is passed (human-in-the-loop
               checkpoint BEFORE any image/video/audio quota is spent -- the
               Viral-Faceless-Shorts-Generator lesson, data/references/
               e2e-pipeline/NOTES.md #5).
  images    -- one gemini-generator image call per scene. The FIRST scene's
               image becomes the style anchor for every scene after it
               (auto-anchor, unless --anchor-profile is given instead).
  videos    -- one gemini-generator video call per scene, anchored on that
               scene's image.
  audio     -- one gemini-generator TTS call per scene, then
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

import wave

try:
    from google import genai
except ImportError:
    sys.exit("google-genai not installed. Run: pip install -r requirements.txt")


def map_to_veo_duration(audio_duration_seconds: float) -> int:
    """Rounds a real measured audio duration to Veo's discrete duration set
    (4, 6, 8) -- Veo has no continuous duration parameter (see
    gemini-generator's own SKILL.md 'A real constraint found by testing').
    Real technique from a real completed project the owner pointed at
    (D:/elix/projects/20260805_GenVid/scripts/pipeline/build_v5_fullmerge.py's
    map_to_veo_duration(), same threshold rule, ported 2026-08-13)."""
    if audio_duration_seconds <= 5.0:
        return 4
    elif audio_duration_seconds <= 7.0:
        return 6
    else:
        return 8


def measure_wav_duration_seconds(wav_path: Path) -> float:
    """Stdlib-only real duration measurement (no ffprobe needed) -- same
    technique as gemini-generator's own generate_speech.py output and the
    real GenVid project's batch_gen_tts_multiprocess.py."""
    with wave.open(str(wav_path), "rb") as wf:
        return round(wf.getnframes() / float(wf.getframerate()), 2)

_HERE = Path(__file__).resolve()
_SKILLS_DIR = _HERE.parents[3]


def _sibling_skill_scripts(skill_id: str) -> Path:
    """Resolve a sibling skill's scripts/ dir by globbing one level for its
    domain folder (skills/<domain>/<skill_id>/scripts) -- robust to a
    sibling skill living in a different domain folder than this one."""
    target = next(_SKILLS_DIR.glob(f"*/{skill_id}"), None)
    if target is None:
        sys.exit(f"run_pipeline.py requires the '{skill_id}' skill installed as a sibling skill folder.")
    return target / "scripts"


sys.path.insert(0, str(_HERE.parent))
from pipeline_state import PipelineState  # noqa: E402
from retry import with_retry  # noqa: E402
from generate_script import generate_script  # noqa: E402
from concat_audio import concat_wavs  # noqa: E402

sys.path.insert(0, str(_sibling_skill_scripts("gemini-generator")))
from generate_image import generate as image_generate, DEFAULT_MODEL as IMAGE_MODEL, _load_anchor_profile_kwargs  # noqa: E402
from generate_video import generate as video_generate, DEFAULT_MODEL as VIDEO_MODEL  # noqa: E402
from generate_speech import generate as audio_generate, write_wav, DEFAULT_MODEL as AUDIO_MODEL  # noqa: E402

sys.path.insert(0, str(_sibling_skill_scripts("video-assembly-composer")))
from render_timeline import render as render_timeline  # noqa: E402
from validate_timeline import validate_timeline  # noqa: E402

sys.path.insert(0, str(_sibling_skill_scripts("toolchain-bootstrap")))
from resolve_ffmpeg import resolve_ffmpeg_path  # noqa: E402


def _build_timeline(scenes: list[dict], videos_dir: Path, combined_voice_path: Path, width: int, height: int, fps: int) -> dict:
    """Each scene's timeline slot is exactly `actual_audio_duration` long (the
    REAL measured narration length, not the script's own guessed
    duration_seconds) -- the video clip, generated at Veo's nearest discrete
    duration (`veo_duration`, see map_to_veo_duration), is stretched
    (video-assembly-composer's stretch_from) to fit exactly, and its own
    ambient audio (if Veo generated any) is mixed in rather than discarded.
    Real technique, not invented here -- see run_pipeline.py's own module
    docstring / map_to_veo_duration for the real elicitation source."""
    video_track = []
    captions = []
    cursor = 0.0
    for scene in scenes:
        duration = float(scene["actual_audio_duration"])
        veo_duration = float(scene["veo_duration"])
        video_track.append({
            "type": "video",
            "path": str((videos_dir / f"{scene['id']}.mp4").resolve()),
            "duration": duration,
            "stretch_from": veo_duration,
            "include_own_audio": True,
            "own_audio_volume_db": -12,
        })
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

    # --- Stage: audio (BEFORE videos, deliberately -- see below) ---
    # Ordering: audio now generates before video, reversing this pipeline's
    # original order. Real reason (2026-08-13, see map_to_veo_duration's own
    # docstring for the elicitation source): Veo only accepts a small
    # discrete set of clip durations, which almost never matches the real
    # length of the separately-generated narration meant to play over it.
    # Generating audio FIRST lets each scene's real measured duration drive
    # which Veo duration to request (nearest-fit, not a script-guessed one)
    # and, at assembly time, drives the exact stretch target -- rather than
    # generating video first and hoping the two line up.
    audio_dir = project_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    combined_voice_path = audio_dir / "combined_voice.wav"
    if not state.is_done("audio"):
        print("[audio] generating...")
        for scene in scenes:
            out_path = audio_dir / f"{scene['id']}.wav"
            if not out_path.exists():
                print(f"  {scene['id']} ...", end="", flush=True)
                pcm = with_retry()(audio_generate)(client, scene["narration"], AUDIO_MODEL, voice=args.voice)
                write_wav(pcm, out_path)
                print(" OK")
            # Real measured duration drives the video stage's own Veo
            # duration choice and the final assembly stretch target -- always
            # (re-)measured here, even on a skip-if-exists resume, so a
            # manually-replaced audio file is picked up correctly too.
            scene["actual_audio_duration"] = measure_wav_duration_seconds(out_path)
            scene["veo_duration"] = map_to_veo_duration(scene["actual_audio_duration"])
        concat_wavs([audio_dir / f"{s['id']}.wav" for s in scenes], combined_voice_path)
        # Persisted back into scenes.json (the same file the human already
        # reviewed at the script checkpoint) -- appends actual_audio_duration/
        # veo_duration per scene, never touches narration/visual_prompt/the
        # script's own duration_seconds guess. Needed for a clean resume: if
        # the process restarts after this stage, the videos/assembly stages
        # below still need these real values without re-measuring every wav.
        script["scenes"] = scenes
        scenes_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
        state.mark_done("audio", artifacts=[str(combined_voice_path)])
    elif "actual_audio_duration" not in scenes[0]:
        # Resuming from an OLDER project.json (audio stage already marked
        # done before this ordering/measurement change existed) -- the
        # in-memory `scenes` loaded above won't have the new fields yet even
        # though the real wav files are already on disk. Measure them now,
        # without re-generating anything or re-marking the stage done.
        for scene in scenes:
            scene["actual_audio_duration"] = measure_wav_duration_seconds(audio_dir / f"{scene['id']}.wav")
            scene["veo_duration"] = map_to_veo_duration(scene["actual_audio_duration"])
        script["scenes"] = scenes
        scenes_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

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
                duration_seconds=scene["veo_duration"],
                generate_audio=True,  # ambient track for video-assembly-composer's include_own_audio to mix in
            )
            out_path.write_bytes(data)
            print(" OK")
        state.mark_done("videos", artifacts=[str(videos_dir / f"{s['id']}.mp4") for s in scenes])

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
