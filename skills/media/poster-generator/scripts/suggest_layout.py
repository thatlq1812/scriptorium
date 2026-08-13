#!/usr/bin/env python3
"""Optional: asks Gemini to PROPOSE zone placement (x_pct/y_pct/w_pct/h_pct)
for a caller-declared element list, producing a layout.json in
svg-poster-builder's own zone schema -- so the same file can be previewed as
placeholder SVG (svg-poster-builder) or rendered as a real poster
(render_poster.py) either way. This is the "auto layout" idea surveyed from
PosterLLaVA (data/references/poster-design-ai/NOTES.md #3, CC BY-NC 4.0 --
idea only, no code/weights used, since that license forbids commercial reuse)
adapted onto svg-poster-builder's ALREADY-EXISTING zone taxonomy instead of
inventing a parallel layout format.

Deterministic-first: Gemini's proposed layout is NEVER trusted blindly --
every response is validated against (1) the caller's own element list
(matching ids/types, not invented or dropped by the model) and (2)
svg-poster-builder's real `_validate_layout()` (overflow, text-coverage cap).
An invalid response triggers a bounded retry (feeding the errors back to the
model), not a silent accept.

Usage:
    python suggest_layout.py elements.json layout_out.json
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

_svg_poster_builder = next(Path(__file__).resolve().parents[3].glob("*/svg-poster-builder"), None)
if _svg_poster_builder is None:
    sys.exit(
        "suggest_layout.py requires the 'svg-poster-builder' skill installed as a "
        "sibling skill folder."
    )
sys.path.insert(0, str(_svg_poster_builder / "scripts"))
from render_layout import ZONE_TYPES, _validate_layout

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 3

PROMPT_TEMPLATE = """You are laying out a poster. Canvas preset: {canvas_preset}.
Propose x_pct/y_pct/w_pct/h_pct (0-100, percentage of canvas width/height) for
EACH of the following elements, so the composition looks good and elements
don't awkwardly overlap (a background_canvas element is expected to span the
full canvas and is exempt from overlap concerns). Do NOT rename, drop, add,
or change the type of any element -- return exactly the same ids and types.

Elements:
{elements_json}

Style notes: {style_notes}

Respond with ONLY a JSON object of this exact shape (no markdown fences, no commentary):
{{"canvas": {{"preset": "{canvas_preset}"}}, "zones": [{{"id": "...", "type": "...", "x_pct": 0, "y_pct": 0, "w_pct": 0, "h_pct": 0, "text_label": "..." }}]}}
"text_label" is required (and must be non-empty) ONLY for zones of type "typography_frame" -- omit it for every other type.
{retry_feedback}"""


def _check_elements_preserved(elements: list[dict], proposed_zones: list[dict]) -> list[str]:
    errors = []
    expected = {e["id"]: e["type"] for e in elements}
    proposed = {z.get("id"): z.get("type") for z in proposed_zones if isinstance(z, dict)}
    missing = set(expected) - set(proposed)
    if missing:
        errors.append(f"Model dropped element id(s): {sorted(missing)}")
    extra = set(proposed) - set(expected)
    if extra:
        errors.append(f"Model invented element id(s) not in the request: {sorted(extra)}")
    for eid, etype in expected.items():
        if eid in proposed and proposed[eid] != etype:
            errors.append(f"Model changed type of '{eid}' from {etype!r} to {proposed[eid]!r}")
    return errors


def suggest_layout(
    client: "genai.Client",
    canvas_preset: str,
    elements: list[dict],
    style_notes: str,
    model: str = DEFAULT_MODEL,
    max_attempts: int = MAX_ATTEMPTS,
) -> dict:
    for elem in elements:
        if elem.get("type") not in ZONE_TYPES:
            raise ValueError(f"element '{elem.get('id')}' has invalid type {elem.get('type')!r}, expected one of {sorted(ZONE_TYPES)}")

    retry_feedback = ""
    last_errors: list[str] = []
    for attempt in range(1, max_attempts + 1):
        prompt = PROMPT_TEMPLATE.format(
            canvas_preset=canvas_preset,
            elements_json=json.dumps(elements, ensure_ascii=False, indent=2),
            style_notes=style_notes or "(none)",
            retry_feedback=(f"\nThe previous attempt was rejected for these reasons -- fix them:\n" + "\n".join(f"- {e}" for e in retry_feedback)) if retry_feedback else "",
        )
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            layout = json.loads(response.text)
        except json.JSONDecodeError as exc:
            last_errors = [f"Model response was not valid JSON: {exc}"]
            retry_feedback = last_errors
            continue

        errors = _check_elements_preserved(elements, layout.get("zones", []))
        errors += _validate_layout(layout)
        if not errors:
            return layout
        last_errors = errors
        retry_feedback = errors

    raise RuntimeError(f"Gemini failed to produce a valid layout after {max_attempts} attempt(s). Last errors:\n" + "\n".join(f"- {e}" for e in last_errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("elements_path", type=Path, help='JSON: {"canvas_preset": "A4", "elements": [...], "style_notes": "..."}')
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    if not args.elements_path.is_file():
        sys.exit(f"Not found: {args.elements_path}")

    spec = json.loads(args.elements_path.read_text(encoding="utf-8"))

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing GEMINI_API_KEY. This is the user's OWN key (bring-your-own-key), "
            "not a backend managed by Scriptorium — set the environment variable or use --api-key."
        )
    client = genai.Client(api_key=api_key)

    try:
        layout = suggest_layout(client, spec["canvas_preset"], spec["elements"], spec.get("style_notes", ""), args.model)
    except (ValueError, RuntimeError) as exc:
        sys.exit(str(exc))

    args.output_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
