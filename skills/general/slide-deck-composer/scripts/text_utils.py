"""
Markdown slide-content parsing.

Ported and trimmed from the real, pure content-parsing layer at
D:/elix/archive/platform_archive/modules/presentation/pptx/text_utils.py
(929 lines) - kept: parse_slide_content, the per-layout parsers, the
character-limit heuristic truncation, clean_markdown_formatting,
strip_leading_bullet_marker, enable_autofit. Dropped (out of scope for
this skill): the v2 JSON-metadata-block parsing (layout_id /
structured_slots / template_slide_idx / visual_needs - those are
Elixverse AI-orchestration fields, not part of this skill's plain
markdown+layout-name contract), auto-pagination splitting (v1 does not
auto-split overflowing content into extra slides - see SKILL.md "Known
limitations").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from lxml import etree

from constants import CHAR_LIMITS, MAX_BULLETS_PER_SLIDE, MAX_BULLETS_PER_COLUMN, NS_A

_HEADING_H1 = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_HEADING_H2 = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_HEADING_H3 = re.compile(r"^###\s+(.+)$", re.MULTILINE)
_BULLET = re.compile(r"^\s*[-*+]\s+(.+)$", re.MULTILINE)
_IMAGE_REF = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_SPEAKER_NOTES = re.compile(
    r"<!--\s*Speaker\s*Notes?:\s*(.*?)-->", re.DOTALL | re.IGNORECASE
)
_NOTES_SEPARATOR = re.compile(r"^---+\s*$", re.MULTILINE)
_LEADING_BULLET_MARKER = re.compile(r"^\s*(?:[-*+\u2022\u2013\u2014]|\d+[.)])\s+")


@dataclass
class ParsedSlideContent:
    title: str = ""
    subtitle: str = ""
    bullets: list[str] = field(default_factory=list)
    left_column: list[str] = field(default_factory=list)
    right_column: list[str] = field(default_factory=list)
    left_header: str = ""
    right_header: str = ""
    speaker_notes: str = ""
    image_ref: str | None = None
    caption: str = ""


def parse_slide_content(layout_type: str, raw_content: str) -> ParsedSlideContent:
    """Parse raw Markdown content for a single slide into structured fields."""
    result = ParsedSlideContent()
    if not raw_content or not raw_content.strip():
        return result

    notes_match = _SPEAKER_NOTES.search(raw_content)
    if notes_match:
        result.speaker_notes = notes_match.group(1).strip()
        raw_content = _SPEAKER_NOTES.sub("", raw_content)

    separator_match = _NOTES_SEPARATOR.search(raw_content)
    if separator_match and not result.speaker_notes:
        parts = _NOTES_SEPARATOR.split(raw_content, maxsplit=1)
        raw_content = parts[0]
        if len(parts) > 1:
            result.speaker_notes = parts[1].strip()

    img_match = _IMAGE_REF.search(raw_content)
    if img_match:
        result.image_ref = img_match.group(2)
        raw_content = _IMAGE_REF.sub("", raw_content)

    if layout_type == "LAYOUT_TITLE":
        _parse_title_slide(raw_content, result)
    elif layout_type == "LAYOUT_QUOTE":
        _parse_center_slide(raw_content, result)
    elif layout_type == "LAYOUT_2COL":
        _parse_two_column_slide(raw_content, result)
    elif layout_type == "LAYOUT_IMG":
        _parse_standard_slide(raw_content, result)
        result.caption = " ".join(result.bullets) if result.bullets else result.subtitle
    else:
        # LAYOUT_STD, LAYOUT_SECTION
        _parse_standard_slide(raw_content, result)

    _apply_char_limits(result)
    return result


def _parse_title_slide(content: str, result: ParsedSlideContent) -> None:
    h1 = _HEADING_H1.search(content)
    if h1:
        result.title = h1.group(1).strip()
        after_h1 = content[h1.end():].strip()
        h2_after = _HEADING_H2.search(after_h1)
        if h2_after:
            result.subtitle = h2_after.group(1).strip()
        else:
            lines = [
                s.strip() for s in after_h1.splitlines()
                if s.strip() and not s.strip().startswith("#")
                and not re.match(r"^\s*[-*+]\s+", s.strip())
            ]
            result.subtitle = " ".join(lines)
    else:
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        if lines:
            result.title = lines[0]
            if len(lines) > 1:
                result.subtitle = " ".join(lines[1:])


def _parse_center_slide(content: str, result: ParsedSlideContent) -> None:
    h1 = _HEADING_H1.search(content)
    h2 = _HEADING_H2.search(content)
    if h1:
        result.title = h1.group(1).strip()
    elif h2:
        result.title = h2.group(1).strip()
    else:
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        result.title = " ".join(lines)
    result.bullets = [m.group(1).strip() for m in _BULLET.finditer(content)]


def _parse_standard_slide(content: str, result: ParsedSlideContent) -> None:
    h1 = _HEADING_H1.search(content)
    h2 = _HEADING_H2.search(content)
    if h1:
        result.title = h1.group(1).strip()
        if h2 and h2.start() > h1.end():
            result.subtitle = h2.group(1).strip()
    elif h2:
        result.title = h2.group(1).strip()
    else:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not re.match(r"^\s*[-*+]\s+", stripped):
                result.title = stripped
                break

    result.bullets = [m.group(1).strip() for m in _BULLET.finditer(content)]
    if not result.bullets:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and stripped != result.title:
                result.bullets.append(stripped)
    result.bullets = result.bullets[:MAX_BULLETS_PER_SLIDE]


def _parse_two_column_slide(content: str, result: ParsedSlideContent) -> None:
    h1 = _HEADING_H1.search(content)
    h2 = _HEADING_H2.search(content)
    if h1:
        result.title = h1.group(1).strip()
    elif h2:
        result.title = h2.group(1).strip()

    h3_splits = _HEADING_H3.split(content)
    left_found = False
    right_found = False
    i = 1
    while i < len(h3_splits) - 1:
        heading_raw = h3_splits[i].strip()
        heading = heading_raw.lower()
        body = h3_splits[i + 1]
        bullets = [m.group(1).strip() for m in _BULLET.finditer(body)]

        if not left_found and heading in ("left", "col 1", "column 1"):
            result.left_column = bullets[:MAX_BULLETS_PER_COLUMN]
            result.left_header = heading_raw
            left_found = True
        elif not right_found and heading in ("right", "col 2", "column 2"):
            result.right_column = bullets[:MAX_BULLETS_PER_COLUMN]
            result.right_header = heading_raw
            right_found = True
        elif not left_found:
            result.left_column = bullets[:MAX_BULLETS_PER_COLUMN]
            result.left_header = heading_raw
            left_found = True
        elif not right_found:
            result.right_column = bullets[:MAX_BULLETS_PER_COLUMN]
            result.right_header = heading_raw
            right_found = True
        i += 2

    if not result.left_column and not result.right_column:
        all_bullets = [m.group(1).strip() for m in _BULLET.finditer(content)]
        mid = len(all_bullets) // 2
        result.left_column = all_bullets[:mid][:MAX_BULLETS_PER_COLUMN]
        result.right_column = all_bullets[mid:][:MAX_BULLETS_PER_COLUMN]


def truncate_text(text: str, limit: int, suffix: str = "...") -> str:
    if not text or len(text) <= limit:
        return text
    cutoff = limit - len(suffix)
    if cutoff <= 0:
        return text[:limit]
    truncated = text[:cutoff].rsplit(" ", 1)[0]
    return truncated + suffix


def _apply_char_limits(content: ParsedSlideContent) -> None:
    content.title = truncate_text(content.title, CHAR_LIMITS["title"]["hard"])
    content.subtitle = truncate_text(content.subtitle, CHAR_LIMITS["subtitle"]["hard"])
    content.speaker_notes = truncate_text(content.speaker_notes, CHAR_LIMITS["speaker_notes"]["hard"])
    content.bullets = [truncate_text(b, CHAR_LIMITS["bullet_point"]["hard"]) for b in content.bullets]
    content.left_column = [truncate_text(b, CHAR_LIMITS["bullet_point"]["hard"]) for b in content.left_column]
    content.right_column = [truncate_text(b, CHAR_LIMITS["bullet_point"]["hard"]) for b in content.right_column]


def strip_leading_bullet_marker(text: str) -> str:
    if not text:
        return text
    return _LEADING_BULLET_MARKER.sub("", text, count=1)


def clean_markdown_formatting(text: str) -> str:
    """Strip a leading list-marker prefix and stray HTML comments,
    leaving the real Markdown emphasis/link/code syntax untouched for
    `rich_text.parse_inline_formatting` to actually render as styled
    runs (bold/italic/code/hyperlink).

    Real, significant bug found via a real dogfooding round (v0.8.2,
    2026-08-03): every caller of this function immediately pipes its
    output through `rich_text.parse_inline_formatting`, the real
    run-based formatter that turns `**bold**`/`*italic*`/`` `code` ``/
    `[text](url)` into actually-styled PowerPoint runs -- but this
    function used to run FIRST and, via bare regex substitution
    (`\\*{1,3}(.+?)\\*{1,3}` -> plain text, `_{1,3}(.+?)_{1,3}` ->
    plain text, `` `(.+?)` `` -> plain text, `[text](url)` -> just
    `text`, discarding the url entirely), silently stripped every one
    of those markers down to plain text BEFORE `parse_inline_formatting`
    ever got a chance to see them. Net effect, confirmed both by direct
    testing and by rendering real compiled output: Markdown bold,
    italic, code, and hyperlink formatting had never actually rendered
    as styled text in any output this skill has ever produced --
    `**bold**` silently became plain unstyled "bold", not because
    `parse_inline_formatting` was broken (it works correctly on its
    own, verified directly), but because this function destroyed the
    markers first. The bug that actually surfaced this round was even
    more damaging for plain content: a v3 legal-briefing deck's real
    content included literal Python filenames with underscores
    ("validate_legal_brief.py") -- the underscore-stripping regex
    matched ANY pair of underscores anywhere in the string (not just
    genuine emphasis pairs) and deleted them outright, corrupting
    "validate_legal_brief.py" into "validatelegalbrief.py" with no
    error, no warning; confirmed by rendering the compiled output.
    Fixed by removing every regex this function shared responsibility
    for with `parse_inline_formatting` -- there was no real formatting
    behavior being preserved by running both, only corruption risk.
    Only `strip_leading_bullet_marker` (a leading "- "/"* " list marker,
    a different concern `parse_inline_formatting` doesn't touch) and
    HTML-comment removal (likewise outside `parse_inline_formatting`'s
    scope) remain here.
    """
    if not text:
        return ""
    text = strip_leading_bullet_marker(text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text.strip()


def enable_autofit(text_frame) -> None:
    """Enable OOXML normAutofit on a python-pptx TextFrame (PowerPoint/
    Google Slides shrink text automatically on overflow at open-time)."""
    try:
        body_pr = text_frame._txBody.find(f"{NS_A}bodyPr")
        if body_pr is None:
            return
        for tag_name in ("normAutofit", "spAutoFit", "noAutofit"):
            existing = body_pr.find(f"{NS_A}{tag_name}")
            if existing is not None:
                body_pr.remove(existing)
        etree.SubElement(body_pr, f"{NS_A}normAutofit")
    except Exception:
        pass


def set_text_wrap(text_frame, wrap: bool = True) -> None:
    try:
        body_pr = text_frame._txBody.find(f"{NS_A}bodyPr")
        if body_pr is not None:
            body_pr.set("wrap", "square" if wrap else "none")
    except Exception:
        pass
