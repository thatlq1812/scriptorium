#!/usr/bin/env python3
"""Analyze one or more reference images via Elixverse's vision-capable
/chat/completions and return a text description -- either STYLE (palette/
lighting/rendering technique) or IDENTITY (subject-identifying features).
This is the same logic generate_image.py calls internally for
--identity-ref/--style-ref; this CLI is for inspecting the description
directly, or preparing an anchor description offline (e.g. to paste into a
media-anchor-profile JSON's "description" field). BYOK: uses the user's own
ELIXVERSE_API_KEY (or --api-key), not a key Scriptorium holds or manages.

Usage:
    python analyze_reference.py style.png --kind style
    python analyze_reference.py face1.png face2.png --kind identity
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from elixverse_client import describe_images, resolve_api_key


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image_paths", type=Path, nargs="+")
    parser.add_argument("--kind", choices=("style", "identity"), required=True)
    parser.add_argument("--model", default=None, help="Vision model to use (default: admin/auto)")
    parser.add_argument("--api-key", default=None, help="Defaults to reading from the ELIXVERSE_API_KEY environment variable")
    args = parser.parse_args()

    missing = [p for p in args.image_paths if not p.exists()]
    if missing:
        sys.exit(f"Not found: {', '.join(str(p) for p in missing)}")

    api_key = resolve_api_key(args.api_key)
    description = describe_images(
        [p.read_bytes() for p in args.image_paths], args.kind, api_key, args.model
    )
    print(description)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
