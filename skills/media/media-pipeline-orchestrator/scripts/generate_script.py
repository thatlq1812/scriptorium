#!/usr/bin/env python3
"""Stage 0: generates a scene-by-scene script (narration + visual prompt +
duration per scene) from a topic, via Gemini text generation in JSON mode.
Deterministically validated before being trusted (exact scene count, every
field non-empty, duration in a sane range, unique ids) -- never handed
downstream un-checked.

Usage:
    python generate_script.py "a fox's rainy day adventure" 3 scenes.json
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
    from google.genai import types
except ImportError:
    sys.exit("google-genai not installed. Run: pip install -r requirements.txt")

DEFAULT_MODEL = "gemini-2.5-flash"

# Imported, not redefined -- gemini-generator is already a mandatory
# sibling dependency of this skill (see media-pipeline-orchestrator's
# SKILL.md compatibility section), and duration_seconds's real constraint
# (verified for real, 2026-08-05: Veo rejects 7, accepts 6, despite the
# API's own error text implying a continuous 4-8 range) lives there as the
# single source of truth. Every scene this generates is fed straight into
# gemini-generator's video generation downstream, so an invalid duration
# here means a wasted round-trip there -- keeping one constant instead of
# two in sync manually.
_gemini_generator = next(Path(__file__).resolve().parents[3].glob("*/gemini-generator"), None)
if _gemini_generator is None:
    sys.exit("generate_script.py requires the 'gemini-generator' skill installed as a sibling skill folder.")
sys.path.insert(0, str(_gemini_generator / "scripts"))
from generate_video import VALID_DURATIONS_SECONDS as VALID_SCENE_SECONDS  # noqa: E402

PROMPT_TEMPLATE = """Write a short video script about: {topic}

Break it into EXACTLY {n_scenes} scenes, in order. For each scene provide:
- "id": a short slug like "scene_01", "scene_02", ... (zero-padded, sequential)
- "narration": 1-2 sentences of spoken narration for this scene
- "visual_prompt": a vivid, self-contained description of what should be shown on screen for an AI image/video generator (describe the subject, action, and setting -- don't reference "the previous scene")
- "duration_seconds": MUST be exactly one of {valid_durations} (no other value is accepted downstream)

Style notes: {style_notes}

Respond with ONLY JSON, no markdown fences, no commentary:
{{"topic": "...", "scenes": [{{"id": "scene_01", "narration": "...", "visual_prompt": "...", "duration_seconds": 4}}]}}"""


def validate_script(script: dict, n_scenes: int) -> list[str]:
    errors: list[str] = []
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != n_scenes:
        got = len(scenes) if isinstance(scenes, list) else type(scenes).__name__
        return [f"expected exactly {n_scenes} scenes, got {got}"]

    seen_ids: set[str] = set()
    for i, scene in enumerate(scenes):
        prefix = f"scenes[{i}]"
        if not isinstance(scene, dict):
            errors.append(f"{prefix} must be an object")
            continue
        sid = scene.get("id")
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif sid in seen_ids:
            errors.append(f"{prefix}.id '{sid}' is a duplicate")
        else:
            seen_ids.add(sid)
        for field in ("narration", "visual_prompt"):
            if not isinstance(scene.get(field), str) or not scene[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        duration = scene.get("duration_seconds")
        if duration not in VALID_SCENE_SECONDS:
            errors.append(f"{prefix}.duration_seconds must be exactly one of {VALID_SCENE_SECONDS}, got {duration!r}")
    return errors


def generate_script(
    client: "genai.Client",
    topic: str,
    n_scenes: int,
    style_notes: str = "",
    model: str = DEFAULT_MODEL,
    max_attempts: int = 3,
) -> dict:
    last_errors: list[str] = []
    for attempt in range(1, max_attempts + 1):
        prompt = PROMPT_TEMPLATE.format(
            topic=topic, n_scenes=n_scenes, valid_durations=VALID_SCENE_SECONDS,
            style_notes=style_notes or "(none)",
        )
        if last_errors:
            prompt += "\n\nThe previous attempt was rejected for these reasons -- fix them:\n" + "\n".join(f"- {e}" for e in last_errors)

        response = client.models.generate_content(
            model=model, contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            script = json.loads(response.text)
        except json.JSONDecodeError as exc:
            last_errors = [f"response was not valid JSON: {exc}"]
            continue

        errors = validate_script(script, n_scenes)
        if not errors:
            return script
        last_errors = errors

    raise RuntimeError(f"Gemini failed to produce a valid {n_scenes}-scene script after {max_attempts} attempt(s). Last errors:\n" + "\n".join(f"- {e}" for e in last_errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("topic")
    parser.add_argument("n_scenes", type=int)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--style-notes", default="")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Missing GEMINI_API_KEY — set the environment variable or use --api-key.")
    client = genai.Client(api_key=api_key)

    try:
        script = generate_script(client, args.topic, args.n_scenes, args.style_notes, args.model)
    except RuntimeError as exc:
        sys.exit(str(exc))

    args.output_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {args.output_path} ({args.n_scenes} scenes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
