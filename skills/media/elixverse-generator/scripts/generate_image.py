#!/usr/bin/env python3
"""Generate image(s) from a text prompt using Elixverse's OpenAI-compatible
REST API (BYOK -- bring-your-own-key; this is the user's OWN Elixverse API
key, not a backend managed or held by Scriptorium -- see "Doesn't
contradict the no-AI-backend principle" in this skill's SKILL.md). Requires
ELIXVERSE_API_KEY in the environment (or --api-key).

Single image:
    python generate_image.py "a watercolor fox in a forest" output.png

Style-anchored (pass a reference image to keep visual consistency):
    python generate_image.py "a watercolor owl" out2.png --style-ref out.png

Identity + style anchored separately (independent channels, same vocabulary
as this registry's gemini-generator):
    python generate_image.py "the same hero, now in a spacesuit" out3.png \\
        --identity-ref hero_face.png --identity-strength strict \\
        --style-ref watercolor_sample.png --style-strength moderate

Pure-text anchor, no reference image:
    python generate_image.py "..." out.png --style-description "flat pastel gouache, thick outlines"

Using a shared media-anchor-profile instead of raw flags (see
skills/media/media-anchor-profile/SKILL.md):
    python generate_image.py "..." out.png --anchor-profile hero.json

Elixverse's /images/generations has NO native reference-image input (see
elixverse_client.py's module docstring) -- --identity-ref/--style-ref work
by first describing the reference image in words via a vision
/chat/completions call, then folding that description into the prompt as a
strength-graded instruction. --identity-description/--style-description
(no image) skip that step entirely.
"""
from __future__ import annotations

import argparse
import base64
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from elixverse_client import describe_images, generate_images, resolve_api_key

STRENGTH_LEVELS = ("strict", "moderate", "loose")

# Strength phrasing: like gemini-generator, there's no numeric conditioning
# knob available through a prompt-only image API -- each discrete level maps
# to a different imperative wording instead of a continuous scale (kept in
# the same vocabulary as gemini-generator for cluster consistency).
_STRENGTH_PHRASE = {
    "strict": "This is a STRICT constraint — deviate as little as possible from it.",
    "moderate": "Use this as a strong reference — stay close to it but adapt naturally where the new description requires.",
    "loose": "Use this only as loose inspiration — prioritize the new description below over an exact match to it.",
}


def _identity_instruction(strength: str, description: str) -> str:
    return (
        f"IDENTITY REFERENCE — preserve this identity exactly: {description} "
        + _STRENGTH_PHRASE[strength]
        + " Freely change pose, camera angle, background, lighting, and composition "
        "to match the new description below — do not copy a specific pose or scene "
        "unless explicitly asked to."
    )


def _style_instruction(strength: str, description: str) -> str:
    return (
        f"STYLE REFERENCE — match this visual style: {description} "
        + _STRENGTH_PHRASE[strength]
        + " Generate a completely new subject as described below; do not repeat "
        "the reference's own subject."
    )


def _resolve_anchor_text(
    kind: str,
    refs_bytes: list[bytes] | None,
    description: str | None,
    api_key: str,
    vision_model: str | None,
) -> str | None:
    parts = []
    if refs_bytes:
        parts.append(describe_images(refs_bytes, kind, api_key, vision_model))
    if description:
        parts.append(description)
    if not parts:
        return None
    return " ".join(parts)


def _load_anchor_profile_kwargs(profile_path: Path) -> dict:
    """Cross-skill import: media-anchor-profile is a sibling skill folder,
    not a pip dependency of this one. Path-imported at call time so a fix to
    the loader there doesn't need re-syncing here (same pattern this
    registry's gemini-generator already uses)."""
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
        identity_refs_bytes=identity["reference_image_bytes"] if identity else None,
        identity_strength=identity["strength"] if identity else "moderate",
        identity_description=identity["description"] if identity else None,
        style_refs_bytes=style["reference_image_bytes"] if style else None,
        style_strength=style["strength"] if style else "moderate",
        style_description=style["description"] if style else None,
    )


def build_prompt(
    user_prompt: str,
    identity_text: str | None,
    identity_strength: str,
    style_text: str | None,
    style_strength: str,
) -> str:
    parts = []
    if identity_text:
        parts.append(_identity_instruction(identity_strength, identity_text))
    if style_text:
        parts.append(_style_instruction(style_strength, style_text))
    parts.append(user_prompt)
    return "\n\n".join(parts)


_PNG_MAGIC = b"\x89PNG"
_JPEG_MAGIC = b"\xff\xd8\xff"


def _detect_format(data: bytes) -> str | None:
    if data[:4] == _PNG_MAGIC:
        return "png"
    if data[:3] == _JPEG_MAGIC:
        return "jpeg"
    return None


def _write_image(entry: dict, out_path: Path) -> None:
    if "b64_json" in entry:
        data = base64.b64decode(entry["b64_json"])
    elif "url" in entry:
        with urllib.request.urlopen(entry["url"], timeout=60) as resp:
            data = resp.read()
    else:
        raise RuntimeError(f"Response image entry has neither b64_json nor url: {entry}")

    # Real finding (2026-08-19): Elixverse's "auto" provider routing does NOT
    # guarantee a fixed image format -- a request for output.png can come
    # back as real JPEG bytes depending on which backend model was routed to.
    # Warn loudly rather than silently writing mismatched bytes under a
    # misleading extension.
    actual_fmt = _detect_format(data)
    ext = out_path.suffix.lower().lstrip(".")
    ext_fmt = "jpeg" if ext in ("jpg", "jpeg") else ext
    if actual_fmt and actual_fmt != ext_fmt:
        print(
            f"WARNING: {out_path} has extension .{ext} but the response bytes are actually "
            f"{actual_fmt} (Elixverse's 'auto' provider routing doesn't guarantee a fixed "
            "image format -- pin --model if you need a consistent one).",
            file=sys.stderr,
        )
    out_path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt", help="Prompt for the image")
    parser.add_argument("output_path", type=Path)
    parser.add_argument(
        "--identity-ref", type=Path, action="append", default=None, dest="identity_refs",
        help="Reference image to anchor IDENTITY. Repeatable to stack multiple images of the same subject.",
    )
    parser.add_argument("--identity-description", default=None, help="Text-only identity anchor, no image needed")
    parser.add_argument("--identity-strength", choices=STRENGTH_LEVELS, default="moderate")
    parser.add_argument(
        "--style-ref", type=Path, action="append", default=None, dest="style_refs",
        help="Reference image to anchor STYLE. Repeatable to stack multiple images into one unified style.",
    )
    parser.add_argument("--style-description", default=None, help="Text-only style anchor, no image needed")
    parser.add_argument("--style-strength", choices=STRENGTH_LEVELS, default="moderate")
    parser.add_argument(
        "--anchor-profile", type=Path, default=None,
        help="Path to a media-anchor-profile JSON file (see skills/media/media-anchor-profile/SKILL.md). "
        "Mutually exclusive with --identity-ref/--identity-description/--identity-strength/--style-ref/--style-description/--style-strength.",
    )
    parser.add_argument("--vision-model", default=None, help="Model used for the internal reference-image description step (default: admin/auto)")
    parser.add_argument("--model", default=None, help="Image-generation model (default: admin/auto)")
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="standard")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument(
        "--render-style", default="vivid",
        help="Elixverse's own image 'style' request field (e.g. vivid/natural) -- NOT the anchor --style-ref/--style-description above.",
    )
    parser.add_argument("--response-format", choices=("url", "b64_json"), default="b64_json")
    parser.add_argument("--api-key", default=None, help="Defaults to reading from the ELIXVERSE_API_KEY environment variable")
    args = parser.parse_args()

    anchor_flags_set = (
        args.identity_refs or args.identity_description or args.identity_strength != "moderate"
        or args.style_refs or args.style_description or args.style_strength != "moderate"
    )
    if args.anchor_profile and anchor_flags_set:
        parser.error(
            "--anchor-profile is mutually exclusive with --identity-ref/--identity-description/"
            "--identity-strength/--style-ref/--style-description/--style-strength"
        )

    api_key = resolve_api_key(args.api_key)

    if args.anchor_profile:
        profile_kwargs = _load_anchor_profile_kwargs(args.anchor_profile)
        identity_text = _resolve_anchor_text(
            "identity", profile_kwargs["identity_refs_bytes"], profile_kwargs["identity_description"],
            api_key, args.vision_model,
        )
        style_text = _resolve_anchor_text(
            "style", profile_kwargs["style_refs_bytes"], profile_kwargs["style_description"],
            api_key, args.vision_model,
        )
        identity_strength = profile_kwargs["identity_strength"]
        style_strength = profile_kwargs["style_strength"]
    else:
        identity_refs_bytes = [p.read_bytes() for p in args.identity_refs] if args.identity_refs else None
        style_refs_bytes = [p.read_bytes() for p in args.style_refs] if args.style_refs else None
        identity_text = _resolve_anchor_text("identity", identity_refs_bytes, args.identity_description, api_key, args.vision_model)
        style_text = _resolve_anchor_text("style", style_refs_bytes, args.style_description, api_key, args.vision_model)
        identity_strength = args.identity_strength
        style_strength = args.style_strength

    final_prompt = build_prompt(args.prompt, identity_text, identity_strength, style_text, style_strength)

    result = generate_images(
        final_prompt,
        api_key,
        model=args.model,
        size=args.size,
        quality=args.quality,
        n=args.n,
        style=args.render_style,
        response_format=args.response_format,
    )

    images = result.get("data", [])
    if not images:
        sys.exit(f"No images returned: {result}")

    stem, suffix = args.output_path.stem, args.output_path.suffix or ".png"
    for i, entry in enumerate(images):
        out_path = args.output_path if len(images) == 1 else args.output_path.with_name(f"{stem}_{i}{suffix}")
        _write_image(entry, out_path)
        note = f" (revised prompt: {entry['revised_prompt']!r})" if entry.get("revised_prompt") else ""
        print(f"OK: wrote {out_path}{note}")

    credit_cost = result.get("usage", {}).get("credit_cost")
    if credit_cost is not None:
        print(f"Credit cost: {credit_cost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
