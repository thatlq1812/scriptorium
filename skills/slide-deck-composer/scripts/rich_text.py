"""
Inline Markdown formatting -> python-pptx paragraph runs.

Ported near-verbatim (pure, no I/O) from:
D:/elix/archive/platform_archive/modules/presentation/pptx/rich_text.py
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pptx.util import Pt
from pptx.dml.color import RGBColor


@dataclass
class TextRun:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: str | None = None


_INLINE_PATTERN = re.compile(
    r"(\*\*\*(.+?)\*\*\*)"
    r"|(\*\*(.+?)\*\*)"
    r"|(\*(.+?)\*)"
    r"|(`(.+?)`)"
    r"|(\[(.+?)\]\((.+?)\))",
    re.DOTALL,
)


def parse_inline_formatting(text: str) -> list[TextRun]:
    if not text:
        return [TextRun(text="")]
    runs: list[TextRun] = []
    last_end = 0
    for match in _INLINE_PATTERN.finditer(text):
        start = match.start()
        if start > last_end:
            plain = text[last_end:start]
            if plain:
                runs.append(TextRun(text=plain))
        if match.group(2) is not None:
            runs.append(TextRun(text=match.group(2), bold=True, italic=True))
        elif match.group(4) is not None:
            runs.append(TextRun(text=match.group(4), bold=True))
        elif match.group(6) is not None:
            runs.append(TextRun(text=match.group(6), italic=True))
        elif match.group(8) is not None:
            runs.append(TextRun(text=match.group(8), code=True))
        elif match.group(10) is not None:
            runs.append(TextRun(text=match.group(10), link=match.group(11)))
        last_end = match.end()
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            runs.append(TextRun(text=remaining))
    if not runs:
        runs.append(TextRun(text=text))
    return runs


def apply_runs_to_paragraph(
    paragraph,
    runs: list[TextRun],
    base_font_name: str | None = None,
    base_font_size_pt: float | None = None,
    base_bold: bool = False,
    code_font: str = "Consolas",
) -> None:
    """Apply TextRun list to a python-pptx paragraph (clears existing runs)."""
    paragraph.clear()
    for text_run in runs:
        if not text_run.text:
            continue
        run = paragraph.add_run()
        run.text = text_run.text
        if base_font_name:
            run.font.name = base_font_name
        if base_font_size_pt is not None:
            run.font.size = Pt(base_font_size_pt)
        if text_run.bold or base_bold:
            run.font.bold = True
        if text_run.italic:
            run.font.italic = True
        if text_run.code:
            run.font.name = code_font
            if base_font_size_pt is not None:
                run.font.size = Pt(max(8, base_font_size_pt - 2))
            run.font.color.rgb = RGBColor(0x4A, 0x4A, 0x4A)
        if text_run.link:
            try:
                run.hyperlink.address = text_run.link
                run.font.color.rgb = RGBColor(0x05, 0x63, 0xC1)
                run.font.underline = True
            except Exception:
                pass
