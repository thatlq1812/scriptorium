#!/usr/bin/env python3
"""Generate an image from a text prompt using Gemini's image model, via the
user's own API key (bring-your-own-key — this is NOT a Scriptorium-managed
AI backend; the caller supplies their own credentials and pays their own
usage). Requires GEMINI_API_KEY in the environment (or --api-key).

Usage:
    python generate_image.py "a watercolor fox in a forest" output.png
    python generate_image.py "..." output.png --model gemini-3-pro-image-preview
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("google-genai not installed. Run: pip install -r requirements.txt")

DEFAULT_MODEL = "gemini-3-pro-image-preview"


def generate(prompt: str, output_path: Path, api_key: str, model: str) -> None:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data is not None:
                output_path.write_bytes(part.inline_data.data)
                return

    raise RuntimeError("Response chứa 0 image part — model không trả ảnh (kiểm tra prompt/quota).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None, help="Mặc định đọc từ biến môi trường GEMINI_API_KEY")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit(
            "Thiếu GEMINI_API_KEY. Đây là key RIÊNG của người dùng (bring-your-own-key), "
            "không phải backend do Scriptorium quản lý — set biến môi trường hoặc dùng --api-key."
        )

    generate(args.prompt, args.output_path, api_key, args.model)
    print(f"OK: wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
