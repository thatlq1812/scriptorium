"""Base64 self-hosted @font-face embedding -- real pattern elicited from
D:/elix/projects/temp_project_20260728/design/shared/fonts_embed.css (a real
production signboard/logo/banner project, 2026-07-28/29): ONE complete font
file base64-embedded per family/weight, inlined into a <style> block, no
external font request at render time (guarantees identical output regardless
of what fonts happen to be installed on the machine that renders it).

Deliberately does NOT attempt an automated Vietnamese-glyph-coverage check.
Tried this for real during this skill's own build (a cmap-based check against
the real project's own "-vn" subset font) and found it produces a FALSE
refusal on a font this project already uses successfully in production --
Vietnamese web-font subsets commonly rely on OpenType GSUB mark-positioning
(base letter + combining accent) rather than one dedicated glyph per
precomposed character, which a naive cmap-membership check gets wrong. The
real elicitation source itself never ran an automated check either -- it
embedded ONE known-complete font file per family and verified by rendering a
real sample and looking at it (render_preview.py + human visual review), the
same discipline this project's own vision-critique-loop finding already
established as the correct division of labor between deterministic checks
and real visual judgment. See SKILL.md "Known limitations".
"""
from __future__ import annotations

import base64
from pathlib import Path

FONT_MIME_BY_EXT = {
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def validate_fonts(fonts: dict, base_dir: Path) -> list[str]:
    """fonts: {family_name: font_file_path}. Checks each path exists, has a
    recognized font extension, and is actually parseable as a font (via
    fontTools -- catches a corrupt/renamed-non-font file loudly rather than
    embedding garbage and getting an inscrutable browser failure later)."""
    errors: list[str] = []
    if not isinstance(fonts, dict):
        return ["'fonts' must be an object of {family_name: font_file_path}"]

    for family, font_path in fonts.items():
        if not isinstance(family, str) or not family.strip():
            errors.append(f"fonts: empty/invalid family name {family!r}")
            continue
        if not isinstance(font_path, str) or not font_path.strip():
            errors.append(f"fonts['{family}']: path must be a non-empty string")
            continue
        resolved = Path(font_path) if Path(font_path).is_absolute() else base_dir / font_path
        ext = resolved.suffix.lower()
        if ext not in FONT_MIME_BY_EXT:
            errors.append(f"fonts['{family}']: unrecognized font extension {ext!r} ({resolved}), expected one of {sorted(FONT_MIME_BY_EXT)}")
            continue
        if not resolved.is_file():
            errors.append(f"fonts['{family}']: font file not found: {resolved}")
            continue
        try:
            from fontTools.ttLib import TTFont
            TTFont(str(resolved), lazy=True)
        except Exception as e:
            errors.append(f"fonts['{family}']: {resolved} is not a valid/parseable font file ({e})")

    return errors


def build_font_face_css(fonts: dict, base_dir: Path) -> str:
    """Assumes validate_fonts() already passed. Returns one @font-face block
    per declared family, base64-embedding the real font bytes."""
    blocks = []
    for family, font_path in fonts.items():
        resolved = Path(font_path) if Path(font_path).is_absolute() else base_dir / font_path
        ext = resolved.suffix.lower()
        mime = FONT_MIME_BY_EXT[ext]
        b64 = base64.b64encode(resolved.read_bytes()).decode("ascii")
        fmt = {"ttf": "truetype", "otf": "opentype", "woff": "woff", "woff2": "woff2"}[ext.lstrip(".")]
        blocks.append(
            f"@font-face {{ font-family: '{family}'; "
            f"src: url(data:{mime};base64,{b64}) format('{fmt}'); "
            f"font-display: block; }}"
        )
    return "\n".join(blocks)
