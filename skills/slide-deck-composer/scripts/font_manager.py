"""
Read-only theme font extraction.

Ported near-verbatim (pure, read-only) from:
D:/elix/archive/platform_archive/modules/presentation/pptx/font_manager.py
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from lxml import etree

from constants import OOXML_NS

logger = logging.getLogger("slide_deck_composer")


@dataclass(frozen=True)
class ThemeFonts:
    major_font: str = ""
    minor_font: str = ""
    major_ea: str = ""
    minor_ea: str = ""
    scheme_colors: dict[str, str] = field(default_factory=dict)


class FontManager:
    """Read-only accessor for a template's theme font information."""

    def __init__(self, prs):
        self._prs = prs
        self._theme_fonts: ThemeFonts | None = None

    def get_theme_fonts(self) -> ThemeFonts:
        if self._theme_fonts is not None:
            return self._theme_fonts
        self._theme_fonts = self._extract_theme_fonts()
        return self._theme_fonts

    def _extract_theme_fonts(self) -> ThemeFonts:
        try:
            slide_master = self._prs.slide_masters[0]
        except (IndexError, AttributeError):
            logger.warning("No Slide Master found; returning empty ThemeFonts")
            return ThemeFonts()

        theme_element = self._get_theme_element(slide_master)
        if theme_element is None:
            logger.warning("Theme XML not accessible; returning empty ThemeFonts")
            return ThemeFonts()

        major_font, major_ea = self._parse_font_scheme(theme_element, "majorFont")
        minor_font, minor_ea = self._parse_font_scheme(theme_element, "minorFont")
        scheme_colors = self._parse_color_scheme(theme_element)

        return ThemeFonts(
            major_font=major_font, minor_font=minor_font,
            major_ea=major_ea, minor_ea=minor_ea, scheme_colors=scheme_colors,
        )

    @staticmethod
    def _get_theme_element(slide_master):
        try:
            theme_part = slide_master.part.theme_part
            if theme_part is not None:
                return theme_part._element
        except AttributeError:
            pass
        try:
            for rel in slide_master.part.rels.values():
                if "theme" in rel.reltype.lower():
                    target = rel.target_part
                    if hasattr(target, "_element") and target._element is not None:
                        return target._element
                    if hasattr(target, "blob"):
                        return etree.fromstring(target.blob)
        except Exception:
            pass
        try:
            ns_a = OOXML_NS["a"]
            theme = slide_master.element.find(f".//{{{ns_a}}}theme")
            if theme is not None:
                return theme
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_font_scheme(theme_element, font_role: str) -> tuple[str, str]:
        ns_a = OOXML_NS["a"]
        font_node = theme_element.find(f".//{{{ns_a}}}fontScheme/{{{ns_a}}}{font_role}/{{{ns_a}}}latin")
        latin = font_node.get("typeface", "") if font_node is not None else ""
        ea_node = theme_element.find(f".//{{{ns_a}}}fontScheme/{{{ns_a}}}{font_role}/{{{ns_a}}}ea")
        ea = ea_node.get("typeface", "") if ea_node is not None else ""
        return latin, ea

    @staticmethod
    def _parse_color_scheme(theme_element) -> dict[str, str]:
        ns_a = OOXML_NS["a"]
        colors: dict[str, str] = {}
        clr_scheme = theme_element.find(f".//{{{ns_a}}}clrScheme")
        if clr_scheme is None:
            return colors
        for child in clr_scheme:
            tag_name = etree.QName(child).localname
            srgb = child.find(f"{{{ns_a}}}srgbClr")
            if srgb is not None:
                colors[tag_name] = srgb.get("val", "")
                continue
            sys_clr = child.find(f"{{{ns_a}}}sysClr")
            if sys_clr is not None:
                colors[tag_name] = sys_clr.get("lastClr", sys_clr.get("val", ""))
        return colors
