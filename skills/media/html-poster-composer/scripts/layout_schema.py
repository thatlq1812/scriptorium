"""Zone-layout schema + validator -- SAME contract as the superseded
svg-poster-builder (canvas presets, 6-type zone taxonomy, 40%-text-coverage
rule). Copied rather than cross-imported: svg-poster-builder is deprecated
(superseded_by: html-poster-composer in the registry), and this project's
own convention (media-anchor-profile, poster-generator) is to import a
LIVE, still-maintained sibling skill's validator, never a deprecated one --
a deprecated skill can be removed later without warning to a dependent.

Grounding unchanged from svg-poster-builder v0.3.0: zone taxonomy and
full-bleed/no-overflow discipline from a real production A1-poster
pipeline's component-type schema; canvas presets are the real public ISO
216 standard; MAX_TEXT_COVERAGE_PCT=40.0 ported from design_rules.py
(10 Canva + 149 Slidesgo templates / 7,854 slides).
"""
from __future__ import annotations

CANVAS_PRESETS_MM = {
    "A1": (594, 841),
    "A4": (210, 297),
    # 1920x1080 landscape at the fixed 96 CSS-px/inch conversion this module
    # already uses everywhere else -- round-trips exactly back to 1920x1080
    # via _mm_to_px(), not an approximation. General-purpose (any video-frame
    # card/overlay need, e.g. video-assembly-composer's intro/outro cards and
    # watermark_image), not tied to one caller.
    "VIDEO_HD": (508.0, 285.75),
    # 1080x1080px at the same fixed 96 CSS-px/inch conversion -- the real
    # standard square social-post size (Facebook/Instagram feed posts).
    # Round-trips exactly back to 1080x1080 via _mm_to_px(), same derivation
    # as VIDEO_HD. A real, previously-missing gap: a caller drafting a social
    # announcement poster had only A1/A4 (print) or a 16:9 video frame to
    # choose from, neither of which matches how these posts actually get
    # published. General-purpose, not tied to one caller.
    "SQUARE": (285.75, 285.75),
}

ZONE_TYPES = {
    "hero_image", "content_scene", "vignette", "decorative_element",
    "background_canvas", "typography_frame",
}

ZONE_DEFAULT_FILL = {
    "hero_image": "#E8C97A",
    "content_scene": "#B8D8BA",
    "vignette": "#F2B6A0",
    "decorative_element": "#D9C7F0",
    "background_canvas": "#F5E6C8",
    "typography_frame": "#FFFFFF",
}

REQUIRED_ZONE_KEYS = {"id", "type", "w_pct", "h_pct"}  # x_pct/y_pct come either declared directly or resolved from relative_to+anchor
POSITION_KEYS = {"x_pct", "y_pct"}
RELATIVE_KEYS = {"relative_to", "anchor"}

# Same 7-value vocabulary as light-logo-arranger's compute_anchor.py, for a
# consistent anchor naming convention across this registry -- but a
# different semantic: light-logo-arranger anchors INSIDE a canvas with an
# INWARD margin; this anchors a zone OUTSIDE another zone's edge/corner with
# an OUTWARD (or negative -> intentionally overlapping) gap, elicited
# directly from a real satellite-icon-cluster layout
# (D:/elix/projects/temp_project_20260728/design/signboard/layout.md's
# "icon rải lệch tầng trên/dưới quanh tên món" pattern) and a real explicit
# instruction to allow deliberate overlap
# (D:/elix/projects/temp_project_20260728/PROJECT.md phase-3: "cho nó tràn
# ra một chút thì tốt" -- let it spill out a bit, that's good).
RELATIVE_ANCHORS = {
    "top-left", "top-right", "top-center",
    "bottom-left", "bottom-right", "bottom-center",
    "center",
}

MAX_TEXT_COVERAGE_PCT = 40.0


def _anchor_target_point(ref: dict, anchor: str) -> tuple[float, float]:
    rx, ry, rw, rh = ref["x_pct"], ref["y_pct"], ref["w_pct"], ref["h_pct"]
    return {
        "top-left": (rx, ry),
        "top-right": (rx + rw, ry),
        "top-center": (rx + rw / 2, ry),
        "bottom-left": (rx, ry + rh),
        "bottom-right": (rx + rw, ry + rh),
        "bottom-center": (rx + rw / 2, ry + rh),
        "center": (rx + rw / 2, ry + rh / 2),
    }[anchor]


def _resolve_relative_xy(ref: dict, anchor: str, gap_pct: float, w_pct: float, h_pct: float) -> tuple[float, float]:
    tx, ty = _anchor_target_point(ref, anchor)
    if anchor == "top-left":
        return tx - gap_pct - w_pct, ty - gap_pct - h_pct
    if anchor == "top-right":
        return tx + gap_pct, ty - gap_pct - h_pct
    if anchor == "top-center":
        return tx - w_pct / 2, ty - gap_pct - h_pct
    if anchor == "bottom-left":
        return tx - gap_pct - w_pct, ty + gap_pct
    if anchor == "bottom-right":
        return tx + gap_pct, ty + gap_pct
    if anchor == "bottom-center":
        return tx - w_pct / 2, ty + gap_pct
    if anchor == "center":
        return tx - w_pct / 2, ty - h_pct / 2
    raise ValueError(f"unknown anchor {anchor!r}")  # unreachable, caller validates first


def resolve_zone_positions(layout: dict) -> tuple[list[dict], list[str]]:
    """Returns (resolved_zones, errors). Every returned zone dict has a real
    numeric x_pct/y_pct -- either the caller's own declared value, or one
    computed from relative_to+anchor(+gap_pct, default 0) against an
    EARLIER zone in the same list (forward/self/circular references refused
    -- deterministic single-pass resolution, no dependency-graph solver).
    Non-position keys (id/type/w_pct/h_pct/fill/text_label/...) pass through
    unchanged. Does not itself run the geometric/overflow/coverage checks --
    call validate_layout() with the result for that."""
    zones = layout.get("zones")
    if not isinstance(zones, list):
        return [], []  # validate_layout's own check reports this; nothing to resolve

    resolved: list[dict] = []
    resolved_by_id: dict[str, dict] = {}
    errors: list[str] = []

    for i, zone in enumerate(zones):
        if not isinstance(zone, dict) or "id" not in zone:
            resolved.append(zone if isinstance(zone, dict) else {})
            continue
        zid = zone["id"]
        has_position = POSITION_KEYS.issubset(zone)
        has_relative = "relative_to" in zone or "anchor" in zone

        if has_position and has_relative:
            errors.append(f"zones[{i}] ('{zid}'): declares both x_pct/y_pct AND relative_to/anchor -- use exactly one positioning mode")
            resolved.append(dict(zone))
            continue

        if has_position:
            resolved.append(dict(zone))
            resolved_by_id[zid] = resolved[-1]
            continue

        if has_relative:
            if not RELATIVE_KEYS.issubset(zone):
                errors.append(f"zones[{i}] ('{zid}'): relative positioning requires BOTH 'relative_to' and 'anchor'")
                resolved.append(dict(zone))
                continue
            ref_id = zone["relative_to"]
            anchor = zone["anchor"]
            gap_pct = zone.get("gap_pct", 0)
            if anchor not in RELATIVE_ANCHORS:
                errors.append(f"zones[{i}] ('{zid}'): 'anchor' must be one of {sorted(RELATIVE_ANCHORS)}, got {anchor!r}")
                resolved.append(dict(zone))
                continue
            if not isinstance(gap_pct, (int, float)):
                errors.append(f"zones[{i}] ('{zid}'): 'gap_pct' must be a number, got {gap_pct!r}")
                resolved.append(dict(zone))
                continue
            if ref_id == zid:
                errors.append(f"zones[{i}] ('{zid}'): 'relative_to' cannot reference itself")
                resolved.append(dict(zone))
                continue
            ref = resolved_by_id.get(ref_id)
            if ref is None:
                errors.append(f"zones[{i}] ('{zid}'): 'relative_to' references '{ref_id}', which must be an earlier zone in the list with an already-resolved position (not found, not yet declared, or itself unresolved)")
                resolved.append(dict(zone))
                continue
            w_pct, h_pct = zone.get("w_pct"), zone.get("h_pct")
            if not isinstance(w_pct, (int, float)) or not isinstance(h_pct, (int, float)):
                errors.append(f"zones[{i}] ('{zid}'): relative positioning still requires numeric 'w_pct'/'h_pct'")
                resolved.append(dict(zone))
                continue
            x_pct, y_pct = _resolve_relative_xy(ref, anchor, gap_pct, w_pct, h_pct)
            new_zone = dict(zone)
            new_zone["x_pct"] = x_pct
            new_zone["y_pct"] = y_pct
            resolved.append(new_zone)
            resolved_by_id[zid] = new_zone
            continue

        errors.append(f"zones[{i}] ('{zid}'): must declare either x_pct/y_pct or relative_to/anchor")
        resolved.append(dict(zone))

    return resolved, errors


def validate_layout(layout: dict) -> list[str]:
    errors: list[str] = []

    canvas = layout.get("canvas")
    if not isinstance(canvas, dict) or "preset" not in canvas:
        errors.append("missing 'canvas.preset'")
    elif canvas["preset"] not in CANVAS_PRESETS_MM:
        errors.append(f"unknown canvas.preset {canvas['preset']!r}, expected one of {sorted(CANVAS_PRESETS_MM)}")

    zones = layout.get("zones")
    if not isinstance(zones, list) or not zones:
        errors.append("'zones' must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for i, zone in enumerate(zones):
        if not isinstance(zone, dict) or not REQUIRED_ZONE_KEYS.issubset(zone) or not POSITION_KEYS.issubset(zone):
            errors.append(f"zones[{i}]: missing one of required keys {sorted(REQUIRED_ZONE_KEYS | POSITION_KEYS)} (call resolve_zone_positions() first if using relative_to/anchor)")
            continue
        zid = zone["id"]
        if zid in seen_ids:
            errors.append(f"zones[{i}]: duplicate zone id '{zid}'")
        seen_ids.add(zid)

        if zone["type"] not in ZONE_TYPES:
            errors.append(f"zones[{i}] ('{zid}'): unknown type {zone['type']!r}, expected one of {sorted(ZONE_TYPES)}")

        for key in ("x_pct", "y_pct", "w_pct", "h_pct"):
            val = zone[key]
            if not isinstance(val, (int, float)) or not (0 <= val <= 100):
                errors.append(f"zones[{i}] ('{zid}'): '{key}' must be a number in [0, 100], got {val!r}")

        if all(isinstance(zone[k], (int, float)) for k in ("x_pct", "w_pct")) and zone["x_pct"] + zone["w_pct"] > 100:
            errors.append(f"zones[{i}] ('{zid}'): x_pct + w_pct = {zone['x_pct'] + zone['w_pct']} exceeds canvas width (100)")
        if all(isinstance(zone[k], (int, float)) for k in ("y_pct", "h_pct")) and zone["y_pct"] + zone["h_pct"] > 100:
            errors.append(f"zones[{i}] ('{zid}'): y_pct + h_pct = {zone['y_pct'] + zone['h_pct']} exceeds canvas height (100)")

        if zone["type"] == "typography_frame" and not zone.get("text_label"):
            errors.append(f"zones[{i}] ('{zid}'): typography_frame zones must declare a non-empty 'text_label' (interior placeholder text)")

    total_text_coverage_pct = 0.0
    for zone in zones:
        if not isinstance(zone, dict) or zone.get("type") != "typography_frame":
            continue
        w_val, h_val = zone.get("w_pct"), zone.get("h_pct")
        if isinstance(w_val, (int, float)) and isinstance(h_val, (int, float)):
            total_text_coverage_pct += (w_val * h_val) / 100.0
    if total_text_coverage_pct > MAX_TEXT_COVERAGE_PCT:
        errors.append(
            f"zones: typography_frame zones cover {total_text_coverage_pct:.1f}% of the canvas, "
            f"exceeds max text coverage of {MAX_TEXT_COVERAGE_PCT}% (design_rules.py "
            "CONTENT_DENSITY['max_text_coverage_pct'], derived from 10 Canva + 149 Slidesgo "
            "templates / 7,854 slides)"
        )

    return errors
