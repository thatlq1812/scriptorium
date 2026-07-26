#!/usr/bin/env python3
"""Generate image(s) from text prompt(s) using Gemini's image model, via the
user's own API key (bring-your-own-key — this is NOT a Scriptorium-managed
AI backend; the caller supplies their own credentials and pays their own
usage). Requires GEMINI_API_KEY in the environment (or --api-key).

Single image:
    python generate_image.py "a watercolor fox in a forest" output.png

Style-anchored (pass a reference image to keep visual consistency across a set):
    python generate_image.py "a watercolor owl" output2.png --style-ref output.png

Batch (asset set from a JSON manifest — see batch_manifest.example.json):
    python generate_image.py --batch manifest.json --out-dir assets/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("google-genai not installed. Run: pip install -r requirements.txt")

DEFAULT_MODEL = "gemini-3-pro-image-preview"
PNG_MAGIC = b"\x89PNG"
JPEG_MAGIC = b"\xff\xd8\xff"
STYLE_REF_INSTRUCTION = (
    "Use the attached image as a STRICT style reference — match its palette, "
    "lighting, line-weight and overall art style. Generate a completely new "
    "subject as described below; do not repeat the reference subject itself."
)


def decode_image_bytes(raw_b64_or_bytes) -> bytes:
    """Gemini's inline_data.data has been observed double-base64-encoded in
    some responses (raw bytes vs base64-of-base64) — check magic bytes and
    unwrap once more if the first decode isn't a real image. Mirrors a fix
    already applied in a sibling project's own generation scripts."""
    data = raw_b64_or_bytes if isinstance(raw_b64_or_bytes, bytes) else bytes(raw_b64_or_bytes)
    if data[:4] == PNG_MAGIC or data[:3] == JPEG_MAGIC:
        return data
    try:
        import base64

        decoded = base64.b64decode(data)
        if decoded[:4] == PNG_MAGIC or decoded[:3] == JPEG_MAGIC:
            return decoded
    except Exception:
        pass
    return data


def generate(
    client: "genai.Client",
    prompt: str,
    model: str,
    style_ref_path: Path | None = None,
    anchor_bytes: bytes | None = None,
) -> bytes:
    parts = []
    ref_bytes = anchor_bytes if anchor_bytes is not None else (
        style_ref_path.read_bytes() if style_ref_path is not None else None
    )
    if ref_bytes is not None:
        parts.append(STYLE_REF_INSTRUCTION)
        parts.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/png"))
    parts.append(prompt)

    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data is not None:
                return decode_image_bytes(part.inline_data.data)

    text = " ".join(
        p.text for c in response.candidates for p in c.content.parts if getattr(p, "text", None)
    )
    raise RuntimeError(f"Response chứa 0 image part.{f' Model nói: {text[:200]}' if text else ''}")


def run_batch(client: "genai.Client", manifest_path: Path, out_dir: Path, model: str, delay_s: float) -> None:
    """manifest.json shape: {"style_ref": "optional/path.png" | null, "images": {"filename.png": "prompt", ...}}

    Nếu style_ref là null: AUTO-ANCHOR — ảnh đầu tiên sinh ra (hoặc đã có sẵn từ
    lần chạy trước) tự động trở thành style reference cho MỌI ảnh sau đó trong
    cùng batch. Đây là pattern quan sát thật từ D:/UNI/S9_SP26/MLN131/project
    (gen_marketing_images.py generate_pack): không cần chuẩn bị ảnh mẫu trước,
    cả bộ vẫn tự đồng bộ phong cách quanh ảnh đầu tiên."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    images = manifest.get("images", {})
    style_ref = manifest.get("style_ref")
    anchor_bytes: bytes | None = None
    anchor_path = Path(style_ref) if style_ref else None
    if anchor_path is not None:
        anchor_bytes = anchor_path.read_bytes()
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = skipped = failed = 0
    for filename, prompt in images.items():
        out_path = out_dir / filename
        if out_path.exists():
            print(f"  SKIP  {filename} (đã tồn tại)")
            if anchor_bytes is None:
                anchor_bytes = out_path.read_bytes()  # dùng làm auto-anchor cho phần còn lại
            skipped += 1
            continue
        tag = "(anchor)" if anchor_bytes is None else "(chained)"
        print(f"  GEN   {filename} {tag} ...", end="", flush=True)
        try:
            data = generate(client, prompt, model, anchor_bytes=anchor_bytes)
            out_path.write_bytes(data)
            print(f" OK ({len(data) / 1024:.0f} KB)")
            generated += 1
            if anchor_bytes is None:
                anchor_bytes = data
        except Exception as exc:
            print(f" FAIL: {exc}")
            failed += 1
        time.sleep(delay_s)

    print(f"\nXong. Generated: {generated}, Skipped: {skipped}, Failed: {failed}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt", nargs="?", help="Prompt cho ảnh đơn lẻ (bỏ qua nếu dùng --batch)")
    parser.add_argument("output_path", type=Path, nargs="?", help="File output cho ảnh đơn lẻ")
    parser.add_argument("--style-ref", type=Path, default=None, help="Ảnh tham chiếu để anchor phong cách (ảnh đơn lẻ)")
    parser.add_argument("--batch", type=Path, default=None, help="Đường dẫn manifest JSON cho batch generation")
    parser.add_argument("--out-dir", type=Path, default=Path("."), help="Thư mục output cho batch (mặc định thư mục hiện tại)")
    parser.add_argument("--delay", type=float, default=3.0, help="Giây chờ giữa mỗi request trong batch (mặc định 3s, tránh rate-limit)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None, help="Mặc định đọc từ biến môi trường GEMINI_API_KEY")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit(
            "Thiếu GEMINI_API_KEY. Đây là key RIÊNG của người dùng (bring-your-own-key), "
            "không phải backend do Scriptorium quản lý — set biến môi trường hoặc dùng --api-key."
        )
    client = genai.Client(api_key=api_key)

    if args.batch:
        run_batch(client, args.batch, args.out_dir, args.model, args.delay)
        return 0

    if not args.prompt or not args.output_path:
        parser.error("cần prompt + output_path cho ảnh đơn lẻ, hoặc --batch <manifest.json>")

    data = generate(client, args.prompt, args.model, args.style_ref)
    args.output_path.write_bytes(data)
    print(f"OK: wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
