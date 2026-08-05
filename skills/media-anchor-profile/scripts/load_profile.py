#!/usr/bin/env python3
"""Loads and validates an anchor-profile JSON file, resolving its reference
images to bytes, ready for a generator skill (image-generator-gemini,
video-generator-gemini, poster-generator) to consume. Validates first --
raises ValueError with the full error list rather than partially loading a
broken profile.

Importable:
    from load_profile import load_anchor_profile
    profile = load_anchor_profile(Path("hero.json"))
    # profile["identity"]["reference_image_bytes"] -> list[bytes]
    # profile["identity"]["description"] -> str | None
    # profile["identity"]["strength"] -> "strict" | "moderate" | "loose"
    # profile["style"] -> same shape, or None if not declared
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_profile import ANCHOR_KEYS, validate_anchor_profile  # noqa: E402


def _resolve_block(block: dict, base_dir: Path) -> dict:
    reference_images = block.get("reference_images") or []
    resolved_bytes = []
    for ref in reference_images:
        ref_path = (base_dir / ref) if not Path(ref).is_absolute() else Path(ref)
        resolved_bytes.append(ref_path.read_bytes())
    return {
        "description": block.get("description"),
        "reference_image_bytes": resolved_bytes,
        "strength": block.get("strength", "moderate"),
    }


def load_anchor_profile(profile_path: Path) -> dict:
    profile_path = Path(profile_path)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    base_dir = profile_path.parent

    errors = validate_anchor_profile(profile, base_dir=base_dir)
    if errors:
        raise ValueError(f"Invalid anchor profile {profile_path}:\n" + "\n".join(f"  - {e}" for e in errors))

    result = {"profile_id": profile["profile_id"]}
    for key in ANCHOR_KEYS:
        result[key] = _resolve_block(profile[key], base_dir) if key in profile else None
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_path", type=Path)
    args = parser.parse_args()

    loaded = load_anchor_profile(args.profile_path)
    for key in ANCHOR_KEYS:
        block = loaded.get(key)
        if block is None:
            print(f"{key}: (not declared)")
        else:
            print(
                f"{key}: strength={block['strength']}, "
                f"{len(block['reference_image_bytes'])} reference image(s), "
                f"description={'set' if block['description'] else 'none'}"
            )
