#!/usr/bin/env python3
"""Generate image(s) from text prompt(s) using Gemini's image model, via the
user's own API key (bring-your-own-key — this is NOT a Scriptorium-managed
AI backend; the caller supplies their own credentials and pays their own
usage). Requires GEMINI_API_KEY in the environment (or --api-key).

Single image:
    python generate_image.py "a watercolor fox in a forest" output.png

Style-anchored (pass a reference image to keep visual consistency across a set):
    python generate_image.py "a watercolor owl" output2.png --style-ref output.png

Identity + style anchored separately (keep a character's face/features while
restyling, or vice versa — see "Identity vs. style" below):
    python generate_image.py "the same hero, now in a spacesuit, side profile" \\
        output3.png --identity-ref hero_face.png --identity-strength strict \\
        --style-ref watercolor_sample.png --style-strength moderate

Multiple reference images stacked into one unified anchor (identity or style):
    python generate_image.py "..." out.png --identity-ref a.png --identity-ref b.png

Using a shared media-anchor-profile instead of raw flags (see
skills/media/media-anchor-profile/SKILL.md):
    python generate_image.py "..." out.png --anchor-profile hero.json

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

STRENGTH_LEVELS = ("strict", "moderate", "loose")

# Strength phrasing: Gemini's image API has no numeric "reference weight" knob
# (unlike diffusion adapters' ip_adapter_scale/controlnet conditioning_scale —
# see data/references/style-anchored-image/NOTES.md). The closest real lever
# available through a prompt-only API is instruction phrasing intensity, so
# each discrete level maps to a different imperative wording instead of a
# continuous scale.
_STRENGTH_PHRASE = {
    "strict": "This is a STRICT constraint — deviate as little as possible from it.",
    "moderate": "Use this as a strong reference — stay close to it but adapt naturally where the new description requires.",
    "loose": "Use this only as loose inspiration — prioritize the text description below over an exact match to it.",
}


def _identity_instruction(strength: str, n_refs: int, description: str | None = None) -> str:
    stack_note = (
        f" The {n_refs} attached images together define ONE identity — synthesize their "
        "common facial features/proportions/markings into a single consistent identity, "
        "don't just copy the first image."
        if n_refs > 1
        else ""
    )
    desc_note = f" Additional identity notes: {description}" if description else ""
    ref_note = "the identity shown in the attached image(s)" if n_refs > 0 else "the identity described below"
    # PuLID lesson (data/references/style-anchored-image/NOTES.md #4): preserving
    # identity must not suppress the model's ability to follow a NEW pose/scene —
    # explicitly decouple "what to keep" (identity) from "what's free to change"
    # (pose/angle/background), matching InstantID's identity-vs-spatial-layout split.
    return (
        f"IDENTITY REFERENCE — preserve {ref_note} "
        "(face shape, proportions, hair color/style, distinctive markings, and other "
        "identifying features) exactly." + stack_note + desc_note + " " + _STRENGTH_PHRASE[strength] +
        " Freely change pose, camera angle, background, lighting, and composition to "
        "match the new description below — do NOT copy the reference image's pose or "
        "scene unless explicitly asked to."
    )


def _style_instruction(strength: str, n_refs: int, description: str | None = None) -> str:
    stack_note = (
        f" The {n_refs} attached images together define ONE visual style — synthesize their "
        "common palette, lighting, and rendering technique into a single consistent style, "
        "don't just copy the first image."
        if n_refs > 1
        else ""
    )
    desc_note = f" Additional style notes: {description}" if description else ""
    ref_note = "the attached image(s)'" if n_refs > 0 else "the following description's"
    return (
        f"STYLE REFERENCE — match {ref_note} palette, lighting, line-weight, "
        "and overall rendering technique." + stack_note + desc_note + " " + _STRENGTH_PHRASE[strength] +
        " Generate a completely new subject as described below; do not repeat the "
        "reference image's subject itself."
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
    *,
    identity_refs: list[bytes] | None = None,
    identity_strength: str = "moderate",
    identity_description: str | None = None,
    style_refs: list[bytes] | None = None,
    style_strength: str = "moderate",
    style_description: str | None = None,
) -> bytes:
    """identity_refs and style_refs are two INDEPENDENT channels (decoupled
    cross-attention lesson from IP-Adapter/InstantID, data/references/
    style-anchored-image/NOTES.md #1-#2): identity_refs constrain WHO/WHAT is
    shown, style_refs constrain HOW it's rendered — either, both, or neither
    may be supplied. Each accepts 1+ images, stacked per PhotoMaker's
    multi-image ID-embedding pattern (NOTES.md #3) rather than only using the
    first. A *_description alone (no ref images) is also valid — matches
    media-anchor-profile's schema, where a block needs a description and/or
    reference images, not necessarily both."""
    parts: list = []
    if identity_refs or identity_description:
        parts.append(_identity_instruction(identity_strength, len(identity_refs or []), identity_description))
        for ref_bytes in identity_refs or []:
            parts.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/png"))
    if style_refs or style_description:
        parts.append(_style_instruction(style_strength, len(style_refs or []), style_description))
        for ref_bytes in style_refs or []:
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
    raise RuntimeError(f"Response contained 0 image parts.{f' Model said: {text[:200]}' if text else ''}")


def run_batch(
    client: "genai.Client",
    manifest_path: Path,
    out_dir: Path,
    model: str,
    delay_s: float,
) -> None:
    """manifest.json shape:
    {
      "style_ref": "optional/path.png" | null,
      "identity_ref": "optional/path.png" | ["a.png", "b.png"] | null,
      "identity_strength": "strict" | "moderate" | "loose",   # default "moderate"
      "style_strength": "strict" | "moderate" | "loose",       # default "moderate"
      "images": {"filename.png": "prompt", ...}
    }

    If style_ref is null: AUTO-ANCHOR — the first image generated (or already
    present from a prior run) automatically becomes the style reference for
    EVERY image after it in the same batch. This is a pattern observed for
    real in D:/UNI/S9_SP26/MLN131/project (gen_marketing_images.py
    generate_pack): no sample image needs preparing beforehand, the whole set
    still auto-syncs its style around the first image.

    identity_ref (if set) is FIXED for the whole batch — unlike style_ref it
    is never auto-derived from a generated image, since identity is something
    the caller supplies deliberately (a real reference photo/character sheet),
    not something to infer from the batch's own output."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    images = manifest.get("images", {})
    style_ref = manifest.get("style_ref")
    identity_strength = manifest.get("identity_strength", "moderate")
    style_strength = manifest.get("style_strength", "moderate")

    identity_ref_raw = manifest.get("identity_ref")
    identity_paths = (
        [Path(p) for p in identity_ref_raw]
        if isinstance(identity_ref_raw, list)
        else [Path(identity_ref_raw)] if identity_ref_raw
        else []
    )
    identity_bytes = [p.read_bytes() for p in identity_paths]

    style_anchor_bytes: bytes | None = None
    style_anchor_path = Path(style_ref) if style_ref else None
    if style_anchor_path is not None:
        style_anchor_bytes = style_anchor_path.read_bytes()
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = skipped = failed = 0
    for filename, prompt in images.items():
        out_path = out_dir / filename
        if out_path.exists():
            print(f"  SKIP  {filename} (already exists)")
            if style_anchor_bytes is None:
                style_anchor_bytes = out_path.read_bytes()  # use as the auto-anchor for the rest
            skipped += 1
            continue
        tag = "(anchor)" if style_anchor_bytes is None else "(chained)"
        print(f"  GEN   {filename} {tag} ...", end="", flush=True)
        try:
            data = generate(
                client,
                prompt,
                model,
                identity_refs=identity_bytes or None,
                identity_strength=identity_strength,
                style_refs=[style_anchor_bytes] if style_anchor_bytes is not None else None,
                style_strength=style_strength,
            )
            out_path.write_bytes(data)
            print(f" OK ({len(data) / 1024:.0f} KB)")
            generated += 1
            if style_anchor_bytes is None:
                style_anchor_bytes = data
        except Exception as exc:
            print(f" FAIL: {exc}")
            failed += 1
        time.sleep(delay_s)

    print(f"\nDone. Generated: {generated}, Skipped: {skipped}, Failed: {failed}")


def _load_anchor_profile_kwargs(profile_path: Path) -> dict:
    """Cross-skill import: media-anchor-profile is a sibling skill folder
    (.claude/skills/media/media-anchor-profile/), not a pip dependency of this one.
    Path-imported at call time rather than bundled/copied, so a fix to the
    loader in that skill doesn't need re-syncing here."""
    skills_dir = Path(__file__).resolve().parents[3]
    target = next(skills_dir.glob("*/media-anchor-profile"), None)
    if target is None:
        sys.exit(
            "--anchor-profile requires the 'media-anchor-profile' skill installed as a "
            "sibling skill folder (not found under skills/<domain>/media-anchor-profile)."
        )
    loader_dir = target / "scripts"
    if str(loader_dir) not in sys.path:
        sys.path.insert(0, str(loader_dir))
    from load_profile import load_anchor_profile

    profile = load_anchor_profile(profile_path)
    identity = profile.get("identity")
    style = profile.get("style")
    return dict(
        identity_refs=identity["reference_image_bytes"] if identity else None,
        identity_strength=identity["strength"] if identity else "moderate",
        identity_description=identity["description"] if identity else None,
        style_refs=style["reference_image_bytes"] if style else None,
        style_strength=style["strength"] if style else "moderate",
        style_description=style["description"] if style else None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt", nargs="?", help="Prompt for a single image (ignored if --batch is used)")
    parser.add_argument("output_path", type=Path, nargs="?", help="Output file for a single image")
    parser.add_argument(
        "--style-ref", type=Path, action="append", default=None, dest="style_refs",
        help="Reference image to anchor STYLE (palette/lighting/rendering). Repeatable to stack multiple images into one unified style.",
    )
    parser.add_argument(
        "--style-strength", choices=STRENGTH_LEVELS, default="moderate",
        help="How strictly to match --style-ref (default: moderate)",
    )
    parser.add_argument(
        "--identity-ref", type=Path, action="append", default=None, dest="identity_refs",
        help="Reference image to anchor IDENTITY (face/character features, independent of style). Repeatable to stack multiple images of the same subject.",
    )
    parser.add_argument(
        "--identity-strength", choices=STRENGTH_LEVELS, default="moderate",
        help="How strictly to preserve --identity-ref (default: moderate)",
    )
    parser.add_argument(
        "--anchor-profile", type=Path, default=None,
        help="Path to a media-anchor-profile JSON file (see skills/media/media-anchor-profile/SKILL.md). "
        "Mutually exclusive with --identity-ref/--style-ref/--identity-strength/--style-strength.",
    )
    parser.add_argument("--batch", type=Path, default=None, help="Path to a JSON manifest for batch generation")
    parser.add_argument("--out-dir", type=Path, default=Path("."), help="Output directory for batch mode (default: current directory)")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds to wait between each request in batch mode (default 3s, avoids rate-limiting)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None, help="Defaults to reading from the GEMINI_API_KEY environment variable")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing GEMINI_API_KEY. This is the user's OWN key (bring-your-own-key), "
            "not a backend managed by Scriptorium — set the environment variable or use --api-key."
        )
    client = genai.Client(api_key=api_key)

    if args.batch:
        run_batch(client, args.batch, args.out_dir, args.model, args.delay)
        return 0

    if not args.prompt or not args.output_path:
        parser.error("prompt + output_path are required for a single image, or use --batch <manifest.json>")

    anchor_kwargs: dict = {}
    if args.anchor_profile:
        if args.identity_refs or args.style_refs or args.identity_strength != "moderate" or args.style_strength != "moderate":
            parser.error("--anchor-profile is mutually exclusive with --identity-ref/--style-ref/--identity-strength/--style-strength")
        anchor_kwargs = _load_anchor_profile_kwargs(args.anchor_profile)
    else:
        identity_bytes = [p.read_bytes() for p in args.identity_refs] if args.identity_refs else None
        style_bytes = [p.read_bytes() for p in args.style_refs] if args.style_refs else None
        anchor_kwargs = dict(
            identity_refs=identity_bytes,
            identity_strength=args.identity_strength,
            style_refs=style_bytes,
            style_strength=args.style_strength,
        )

    data = generate(client, args.prompt, args.model, **anchor_kwargs)
    args.output_path.write_bytes(data)
    print(f"OK: wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
