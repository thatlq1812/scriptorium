#!/usr/bin/env python3
"""Analyze an EXISTING image's visual style with Gemini's vision capability
and return a text style-description — bridges "match this existing design"
workflows to text-based style rules (usable later as a prompt prefix, or to
decide whether image-based --style-ref is even needed). Uses the user's own
GEMINI_API_KEY (bring-your-own-key, same as generate_image.py).

Usage:
    python analyze_style.py reference.png
    python analyze_style.py reference.png --model gemini-2.5-flash
"""
from __future__ import annotations

import argparse
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

DEFAULT_TEXT_MODEL = "gemini-2.5-flash"
ANALYSIS_PROMPT = (
    "Describe this image's visual STYLE (not its subject) in a short, dense "
    "paragraph a designer could paste as a prompt prefix to generate new "
    "images in the same style. Cover: color palette (name actual colors), "
    "lighting/mood, line-weight or rendering technique (flat/photorealistic/"
    "watercolor/etc.), composition tendencies, and any distinctive motifs. "
    "Do not describe what the subject IS, only HOW it is rendered."
)


def analyze(client: "genai.Client", image_path: Path, model: str) -> str:
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime),
            ANALYSIS_PROMPT,
        ],
    )
    return response.text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_path", type=Path)
    parser.add_argument("--model", default=DEFAULT_TEXT_MODEL)
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    if not args.image_path.exists():
        sys.exit(f"Not found: {args.image_path}")

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Missing GEMINI_API_KEY — set the environment variable or use --api-key.")

    client = genai.Client(api_key=api_key)
    description = analyze(client, args.image_path, args.model)
    print(description)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
