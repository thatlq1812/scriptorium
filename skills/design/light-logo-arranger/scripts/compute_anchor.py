#!/usr/bin/env python3
"""Deterministic icon/logo anchor-position calculator.

Given a canvas size, a logo/icon size, a named anchor point, and a margin,
computes the (x, y) top-left placement in the canvas's own units (mm, px --
whatever the caller's units are, this script is unit-agnostic). Refuses if
the resulting placement overlaps any caller-declared exclusion zone, rather
than silently placing over something else (e.g. a background_canvas element
declared by svg-poster-builder, or another logo already anchored).

Anchor-then-exclude is the same "chain from a fixed reference point" idea a
real production layout pipeline uses for its own component chaining (master
anchor -> group anchor -> component), simplified here to single fixed-point
anchoring against named canvas corners/edges/center, per
UPGRADE_PLAN_20260729.md Item 4.

Usage:
    python compute_anchor.py <placement.json>

Exit 0 = placement computed and printed, 1 = placement overlaps a declared
exclusion zone, 2 = malformed input.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_ANCHORS = {
    "top-left", "top-right", "top-center",
    "bottom-left", "bottom-right", "bottom-center",
    "center",
}

REQUIRED_KEYS = {"canvas_w", "canvas_h", "logo_w", "logo_h", "anchor", "margin"}


def _compute_xy(canvas_w: float, canvas_h: float, logo_w: float, logo_h: float, anchor: str, margin: float) -> tuple[float, float]:
    if anchor == "top-left":
        return margin, margin
    if anchor == "top-right":
        return canvas_w - logo_w - margin, margin
    if anchor == "top-center":
        return (canvas_w - logo_w) / 2, margin
    if anchor == "bottom-left":
        return margin, canvas_h - logo_h - margin
    if anchor == "bottom-right":
        return canvas_w - logo_w - margin, canvas_h - logo_h - margin
    if anchor == "bottom-center":
        return (canvas_w - logo_w) / 2, canvas_h - logo_h - margin
    if anchor == "center":
        return (canvas_w - logo_w) / 2, (canvas_h - logo_h) / 2
    raise ValueError(f"unknown anchor {anchor!r}")


def _rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python compute_anchor.py <placement.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or not REQUIRED_KEYS.issubset(data):
        print(f"ERROR: placement.json must be an object with keys {sorted(REQUIRED_KEYS)}", file=sys.stderr)
        return 2

    for key in ("canvas_w", "canvas_h", "logo_w", "logo_h", "margin"):
        if not isinstance(data[key], (int, float)) or data[key] < 0:
            print(f"ERROR: '{key}' must be a non-negative number, got {data[key]!r}", file=sys.stderr)
            return 2

    if data["anchor"] not in VALID_ANCHORS:
        print(f"ERROR: 'anchor' must be one of {sorted(VALID_ANCHORS)}, got {data['anchor']!r}", file=sys.stderr)
        return 2

    if data["logo_w"] > data["canvas_w"] or data["logo_h"] > data["canvas_h"]:
        print("ERROR: logo dimensions exceed canvas dimensions.", file=sys.stderr)
        return 2

    x, y = _compute_xy(data["canvas_w"], data["canvas_h"], data["logo_w"], data["logo_h"], data["anchor"], data["margin"])

    if x < 0 or y < 0 or x + data["logo_w"] > data["canvas_w"] or y + data["logo_h"] > data["canvas_h"]:
        print(
            f"ERROR: computed placement (x={x:.2f}, y={y:.2f}) with margin={data['margin']} "
            f"pushes the logo outside the canvas -- reduce margin or logo size.",
            file=sys.stderr,
        )
        return 1

    exclusion_zones = data.get("exclusion_zones", [])
    for i, zone in enumerate(exclusion_zones):
        if not isinstance(zone, dict) or not {"x", "y", "w", "h"}.issubset(zone):
            print(f"ERROR: exclusion_zones[{i}] must have x/y/w/h", file=sys.stderr)
            return 2
        if _rects_overlap(x, y, data["logo_w"], data["logo_h"], zone["x"], zone["y"], zone["w"], zone["h"]):
            print(
                f"REFUSED: placement (x={x:.2f}, y={y:.2f}, w={data['logo_w']}, h={data['logo_h']}) "
                f"overlaps exclusion_zones[{i}] ({zone})",
                file=sys.stderr,
            )
            return 1

    print(f"x={x:.2f}")
    print(f"y={y:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
