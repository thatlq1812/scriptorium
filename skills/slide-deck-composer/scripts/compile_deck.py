#!/usr/bin/env python3
"""
slide-deck-composer entry point: clone a caller-supplied real .pptx
template's slides and inject caller-supplied content into them,
preserving the template's own design (fonts, colors, layout geometry,
decorative elements) instead of drawing generic geometric slides from
scratch.

Architecture: see SKILL.md "Architecture decision" section. This is
the "clone-and-inject" pipeline -- NOT a from-scratch layout builder.

Usage:
    python compile_deck.py <template.pptx> <content.json> <output.pptx>
        [--heading-font "Montserrat"] [--body-font "Open Sans"]
        [--vietnamese]

content.json shape:
    {
      "slides": [
        {"layout": "title", "markdown": "# Deck Title\\nA subtitle line"},
        {"layout": "standard", "markdown": "## Slide heading\\n- bullet one\\n- bullet two"},
        {"layout": "two_column", "markdown": "## Compare\\n### Left\\n- a\\n### Right\\n- b"},
        {"layout": "image", "markdown": "## Caption title\\nCaption text"},
        {"layout": "quote", "markdown": "# A standalone statement"},
        {"layout": "section", "markdown": "## Section N\\nSection subtitle"}
      ]
    }

``layout`` must be one of the 6 keys in constants.LAYOUT_NAME_MAP --
see SKILL.md "Known limitations" for the ~14 layout types NOT built in
this pass (refused with a clear error, never silently downgraded).

Exit codes: 0 = success, 2 = malformed/invalid input (refuse loudly,
never guess), 3 = template structurally unusable (e.g. zero slides).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation

import constants as C
import text_utils
import rich_text
import shape_roles
import slide_classifier
import slide_duplicator
import font_manager
import font_engine
import font_vietnamese
import font_size_balance

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

_DEFAULT_TITLE_PT = 28.0
_DEFAULT_BODY_PT = 16.0


class ComposerError(Exception):
    """Raised for any refuse-loudly condition (never guess, never silently drop)."""


def load_content_spec(path: Path) -> list[dict]:
    if not path.is_file():
        raise ComposerError(f"content file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ComposerError(f"malformed JSON in {path}: {e}") from e
    if not isinstance(data, dict) or "slides" not in data:
        raise ComposerError("content JSON must be an object with a 'slides' array")
    slides = data["slides"]
    if not isinstance(slides, list) or not slides:
        raise ComposerError("content.slides must be a non-empty array")
    for i, item in enumerate(slides):
        if not isinstance(item, dict) or "layout" not in item or "markdown" not in item:
            raise ComposerError(f"slides[{i}] must be an object with 'layout' and 'markdown' keys")
        if item["layout"] not in C.LAYOUT_NAME_MAP:
            raise ComposerError(
                f"slides[{i}].layout={item['layout']!r} is not implemented. "
                f"Supported: {sorted(C.LAYOUT_NAME_MAP)}. See SKILL.md 'Known limitations' "
                f"for the layout types not yet built -- refusing rather than silently "
                f"downgrading to a layout you didn't ask for."
            )
    return slides


# Minimum structurally-required body/content shapes for each layout,
# used to pick a STRUCTURALLY COMPATIBLE source slide from the template
# instead of blind round-robin. Bug found in self-test round 1 (see
# SKILL.md changelog): blind round-robin cloned a "standard" bullets
# request onto a two-column template slide (and vice versa), which (a)
# left the unused second placeholder's ORIGINAL DEMO TEXT visible in
# the output ("Right demo point" leaking into a real deck) and (b)
# silently dropped real caller content that had nowhere structurally
# compatible to go (a two-column right-side list vanishing entirely).
# Fixed two ways: this structural pre-filter, AND a post-injection
# sweep (see ``_clear_unused_text_shapes``) that blanks any leftover
# non-decorative text shape not actually used for this slide's content,
# so stale template demo text can never survive into real output even
# when a perfect structural match isn't available.
_MIN_BODY_REQUIRED: dict[str, int] = {
    C.LAYOUT_TITLE: 0,
    C.LAYOUT_STD: 1,
    C.LAYOUT_2COL: 2,
    C.LAYOUT_IMG: 1,
    C.LAYOUT_QUOTE: 0,
    C.LAYOUT_SECTION: 1,
}


def _title_and_body_counts(prs, slide_idx: int) -> tuple[bool, int]:
    title, bodies = shape_roles.find_title_and_body(
        prs.slides[slide_idx].shapes, prs.slide_width, prs.slide_height
    )
    return title is not None, len(bodies)


def _fits(prs, slide_idx: int, min_body: int) -> bool:
    """A candidate source slide is usable only when it has BOTH a
    scorable title shape AND enough body candidates. Real bug found in
    self-test round 3 against an actual Slidesgo template ("Elegant
    Black & White Style"): its closing slide is a pure full-bleed
    picture ("BLANK" layout, a single Picture shape, zero text frames)
    -- min_body=0 for a "quote" layout let it through the old filter
    (which only checked body count), so the quote's whole title text
    silently had nowhere to go and vanished from the output. A
    has_title check was missing entirely; fixed here."""
    has_title, body_count = _title_and_body_counts(prs, slide_idx)
    return has_title and body_count >= min_body


def pick_source_slide_index(
    prs,
    layout_type: str,
    position: int,
    total: int,
    classification: dict[str, list[int]],
    original_count: int,
    layout_round_robin: dict[str, int],
) -> tuple[int, bool]:
    """Pick a structurally-compatible template slide to clone for this
    output slide. Returns (source_slide_idx, structural_match)."""
    title_pool = classification.get("title", [])
    content_pool = classification.get("content", [])
    closing_pool = classification.get("closing", [])
    all_pool = title_pool + content_pool + closing_pool
    if not all_pool:
        all_pool = list(range(original_count))

    min_body = _MIN_BODY_REQUIRED.get(layout_type, 0)

    if layout_type == C.LAYOUT_TITLE:
        candidates = [i for i in (title_pool or content_pool or all_pool) if _fits(prs, i, 0)]
        if candidates:
            return candidates[0], True
        # No title-pool slide has a scorable title shape (rare, but a
        # picture-only cover slide is possible) -- fall through to the
        # general search below instead of guaranteeing a content-loss.
        title_pool = []

    # Only reuse a "closing" slide (typically minimal/single-message,
    # e.g. "Thank you") for layouts that themselves need at most a
    # title -- and only when that slide actually HAS a title-capable
    # shape (see _fits docstring for the real bug this guards against).
    if position == total - 1 and closing_pool and min_body == 0:
        closing_candidates = [i for i in closing_pool if _fits(prs, i, min_body)]
        if closing_candidates:
            return closing_candidates[0], True

    search_pool = content_pool or all_pool
    matching = [i for i in search_pool if _fits(prs, i, min_body)]
    if not matching:
        matching = [i for i in all_pool if _fits(prs, i, min_body)]

    if matching:
        counter = layout_round_robin.get(layout_type, 0)
        layout_round_robin[layout_type] = counter + 1
        return matching[counter % len(matching)], True

    # No structurally-compatible slide anywhere in the template: fall
    # back to the richest available slide rather than crashing the
    # whole compile over one slide, but report the mismatch (never
    # silently pretend the content fit).
    best = max(search_pool, key=lambda i: _title_and_body_counts(prs, i)[1])
    return best, False


def _clear_shape_text(shape) -> None:
    """Blank a shape's text down to a single empty paragraph, XML-level
    (matches the wipe pattern used when python-pptx add_slide() first
    injects placeholder demo text from the layout)."""
    tf = shape.text_frame
    txBody = tf._txBody
    for p in list(txBody.findall(f"{C.NS_A}p")):
        txBody.remove(p)
    from lxml import etree
    empty_p = etree.SubElement(txBody, f"{C.NS_A}p")
    etree.SubElement(empty_p, f"{C.NS_A}endParaRPr")


def _clear_unused_text_shapes(all_infos: list[dict], used_shape_ids: set[int]) -> int:
    """Blank any non-decorative, non-watermark text shape on the cloned
    slide that was NOT assigned a role for this slide's content, so
    the template's own original demo/instruction text never leaks into
    real output. Returns the number of shapes cleared."""
    cleared = 0
    for info in all_infos:
        if info["is_decorative"] or info["is_watermark"]:
            continue
        if id(info["shape"]._element) in used_shape_ids:
            continue
        if info["text"]:
            _clear_shape_text(info["shape"])
            cleared += 1
    return cleared


def _resolve_font_name(
    requested: str | None,
    theme_fallback: str,
    vietnamese: bool,
    role_label: str,
    log: list[dict],
) -> str | None:
    """Resolve the font name to actually WRITE onto runs.

    Returns None when no explicit override is warranted (leave the
    template's own inherited font alone -- the default, most-common
    path). Returns a concrete font name when the caller requested a
    swap, or when --vietnamese forced a substitution because the
    effective font lacks confirmed Vietnamese support.
    """
    effective = requested or theme_fallback
    if not effective:
        return requested  # nothing to check against; honor caller's raw request or None

    if not vietnamese:
        return requested  # only override runs when caller explicitly requested a font swap

    check = font_vietnamese.check_font_vietnamese_safety(effective)
    if check.status == "unknown":
        raise ComposerError(
            f"--vietnamese requested but the {role_label} font '{effective}' has unknown "
            f"Vietnamese glyph coverage: {check.reason}"
        )
    resolved = check.substitute if check.status == "substitute" else check.font_name
    log.append({
        "role": role_label, "requested_or_theme": effective,
        "status": check.status, "resolved": resolved,
    })
    return resolved


def _inject_single_line(
    shape, text: str, *, font_name: str | None, font_size_pt: float, bold: bool = False,
) -> None:
    tf = shape.text_frame
    while len(tf.paragraphs) > 1:
        tf._txBody.remove(tf.paragraphs[-1]._p)
    p = tf.paragraphs[0]
    runs = rich_text.parse_inline_formatting(text_utils.clean_markdown_formatting(text))
    rich_text.apply_runs_to_paragraph(
        p, runs, base_font_name=font_name, base_font_size_pt=font_size_pt, base_bold=bold,
    )
    text_utils.enable_autofit(tf)
    text_utils.set_text_wrap(tf)


def _inject_bullets(
    shape, bullets: list[str], *, font_name: str | None, font_size_pt: float,
) -> None:
    tf = shape.text_frame
    while len(tf.paragraphs) > 1:
        tf._txBody.remove(tf.paragraphs[-1]._p)
    if not bullets:
        bullets = [""]
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        clean = text_utils.clean_markdown_formatting(bullet)
        runs = rich_text.parse_inline_formatting(clean)
        rich_text.apply_runs_to_paragraph(p, runs, base_font_name=font_name, base_font_size_pt=font_size_pt)
    text_utils.enable_autofit(tf)
    text_utils.set_text_wrap(tf)


def compile_deck(
    template_path: Path,
    content_path: Path,
    output_path: Path,
    heading_font: str | None,
    body_font: str | None,
    vietnamese: bool,
) -> dict:
    slides_spec = load_content_spec(content_path)

    if not template_path.is_file():
        raise ComposerError(f"template file not found: {template_path}")
    prs = Presentation(str(template_path))

    original_count = len(prs.slides)
    if original_count == 0:
        raise ComposerError("template has zero slides -- nothing to clone from")

    classification = slide_classifier.classify_template_slides(prs, original_count)

    theme = font_manager.FontManager(prs).get_theme_fonts()
    font_log: list[dict] = []
    resolved_heading_font = _resolve_font_name(heading_font, theme.major_font, vietnamese, "heading", font_log)
    resolved_body_font = _resolve_font_name(body_font, theme.minor_font, vietnamese, "body", font_log)

    if heading_font or body_font:
        applied_heading = resolved_heading_font or theme.major_font
        applied_body = resolved_body_font or theme.minor_font
        if applied_heading and applied_body:
            font_engine.set_theme_fonts(prs, applied_heading, applied_body)

    total = len(slides_spec)
    slide_plan: list[dict] = []
    size_decisions: list[dict] = []
    layout_round_robin: dict[str, int] = {}

    for position, item in enumerate(slides_spec):
        layout_type = C.LAYOUT_NAME_MAP[item["layout"]]
        source_idx, structural_match = pick_source_slide_index(
            prs, layout_type, position, total, classification, original_count, layout_round_robin,
        )
        source_slide = prs.slides[source_idx]
        new_slide = slide_duplicator.duplicate_slide(prs, source_slide)

        content = text_utils.parse_slide_content(layout_type, item["markdown"])

        # Captured once, before any injection, so (a) role scoring sees
        # the template's real original text/geometry and (b) the later
        # stale-text cleanup sweep knows what every shape looked like
        # before this slide's content touched it.
        all_text_infos = shape_roles.collect_text_shapes(new_slide.shapes, prs.slide_width, prs.slide_height)
        title_info, body_infos = shape_roles.find_title_and_body(
            new_slide.shapes, prs.slide_width, prs.slide_height
        )
        used_shape_ids: set[int] = set()
        if title_info is not None:
            used_shape_ids.add(id(title_info["shape"]._element))

        record = {
            "position": position, "layout": item["layout"], "source_slide_idx": source_idx,
            "structural_match": structural_match,
            "title_shape_found": title_info is not None, "body_shapes_found": len(body_infos),
        }
        slide_plan.append(record)

        def _size_for(info, new_text: str, role: str) -> float:
            base_pt = info["font_size_pt"] or (_DEFAULT_TITLE_PT if role == "title" else _DEFAULT_BODY_PT)
            decision = font_size_balance.compute_balanced_font_size(
                original_char_count=info["char_count"],
                new_char_count=len(new_text),
                original_pt=base_pt,
                role=role,
            )
            if decision.applied:
                size_decisions.append({
                    "position": position, "role": role,
                    "original_chars": decision.original_char_count,
                    "new_chars": decision.new_char_count,
                    "ratio": round(decision.ratio, 2),
                    "steps": decision.steps,
                    "original_pt": decision.original_pt,
                    "balanced_pt": decision.balanced_pt,
                })
            return decision.balanced_pt

        if layout_type == C.LAYOUT_TITLE:
            if title_info is not None:
                pt = _size_for(title_info, content.title, "title")
                _inject_single_line(title_info["shape"], content.title, font_name=resolved_heading_font, font_size_pt=pt)
            if content.subtitle and body_infos:
                sub_info = body_infos[0]
                pt = _size_for(sub_info, content.subtitle, "body")
                _inject_single_line(sub_info["shape"], content.subtitle, font_name=resolved_body_font, font_size_pt=pt)
                used_shape_ids.add(id(sub_info["shape"]._element))

        elif layout_type == C.LAYOUT_STD:
            if title_info is not None:
                pt = _size_for(title_info, content.title, "title")
                _inject_single_line(title_info["shape"], content.title, font_name=resolved_heading_font, font_size_pt=pt)
            if body_infos:
                body_info = body_infos[0]
                joined = "\n".join(content.bullets)
                pt = _size_for(body_info, joined, "body")
                _inject_bullets(body_info["shape"], content.bullets, font_name=resolved_body_font, font_size_pt=pt)
                used_shape_ids.add(id(body_info["shape"]._element))

        elif layout_type == C.LAYOUT_2COL:
            if title_info is not None:
                pt = _size_for(title_info, content.title, "title")
                _inject_single_line(title_info["shape"], content.title, font_name=resolved_heading_font, font_size_pt=pt)
            cols = sorted(body_infos[:2], key=lambda i: i["left_pct"])
            if len(cols) >= 1 and content.left_column:
                pt = _size_for(cols[0], "\n".join(content.left_column), "body")
                _inject_bullets(cols[0]["shape"], content.left_column, font_name=resolved_body_font, font_size_pt=pt)
                used_shape_ids.add(id(cols[0]["shape"]._element))
            if len(cols) >= 2 and content.right_column:
                pt = _size_for(cols[1], "\n".join(content.right_column), "body")
                _inject_bullets(cols[1]["shape"], content.right_column, font_name=resolved_body_font, font_size_pt=pt)
                used_shape_ids.add(id(cols[1]["shape"]._element))

        elif layout_type == C.LAYOUT_IMG:
            # v1 does NOT replace the template's own picture -- see
            # SKILL.md "Known limitations": image content injection is
            # text-only in this pass.
            if title_info is not None:
                pt = _size_for(title_info, content.title, "title")
                _inject_single_line(title_info["shape"], content.title, font_name=resolved_heading_font, font_size_pt=pt)
            if body_infos and content.caption:
                cap_info = body_infos[0]
                pt = _size_for(cap_info, content.caption, "body")
                _inject_single_line(cap_info["shape"], content.caption, font_name=resolved_body_font, font_size_pt=pt)
                used_shape_ids.add(id(cap_info["shape"]._element))

        elif layout_type == C.LAYOUT_QUOTE:
            if title_info is not None:
                pt = _size_for(title_info, content.title, "title")
                _inject_single_line(title_info["shape"], content.title, font_name=resolved_heading_font, font_size_pt=pt)

        elif layout_type == C.LAYOUT_SECTION:
            if title_info is not None:
                pt = _size_for(title_info, content.title, "title")
                _inject_single_line(title_info["shape"], content.title, font_name=resolved_heading_font, font_size_pt=pt)
            # Real bug found in self-test round 1: markdown with a single
            # "## Heading\nplain text line" (no second heading) parses
            # via text_utils' standard-slide path, which routes an
            # unheaded body line into ``bullets``, not ``subtitle`` (only
            # an explicit H1+H2 pair populates ``subtitle`` -- see
            # _parse_standard_slide). LAYOUT_SECTION only checked
            # ``content.subtitle``, so that line silently vanished from
            # the output. Fixed: fall back to the bullets when no
            # explicit subtitle was parsed.
            subtitle_text = content.subtitle or " ".join(content.bullets)
            if subtitle_text and body_infos:
                sub_info = body_infos[0]
                pt = _size_for(sub_info, subtitle_text, "body")
                _inject_single_line(sub_info["shape"], subtitle_text, font_name=resolved_body_font, font_size_pt=pt)
                used_shape_ids.add(id(sub_info["shape"]._element))

        record["stale_text_shapes_cleared"] = _clear_unused_text_shapes(all_text_infos, used_shape_ids)

    slide_duplicator.strip_template_slides(prs, original_count)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))

    return {
        "output": str(output_path),
        "slides_generated": len(slides_spec),
        "template_classification": classification,
        "theme_fonts": {"major": theme.major_font, "minor": theme.minor_font},
        "font_resolution_log": font_log,
        "slide_plan": slide_plan,
        "font_size_balancing_applied": size_decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Clone a real .pptx template and inject content.")
    parser.add_argument("template", type=Path, help="Caller-supplied .pptx template file")
    parser.add_argument("content", type=Path, help="content.json (see module docstring for shape)")
    parser.add_argument("output", type=Path, help="Output .pptx path")
    parser.add_argument("--heading-font", default=None, help="Override template's heading/title font")
    parser.add_argument("--body-font", default=None, help="Override template's body font")
    parser.add_argument(
        "--vietnamese", action="store_true",
        help="Require Vietnamese-diacritic-safe fonts; substitutes or refuses loudly if unresolvable",
    )
    args = parser.parse_args()

    try:
        result = compile_deck(
            args.template, args.content, args.output,
            args.heading_font, args.body_font, args.vietnamese,
        )
    except ComposerError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - top-level CLI boundary, report and exit non-zero
        print(f"ERROR: unexpected failure: {e}", file=sys.stderr)
        return 3

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
