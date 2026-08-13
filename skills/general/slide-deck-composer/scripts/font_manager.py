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


def _run_level_font(shape) -> str | None:
    """The shape's OWN currently-set explicit font, read directly off
    its first run that has one -- the single most authoritative signal
    for "what does this specific shape actually render as," when it
    exists. `run.font.name` is None when a run has no explicit
    `<a:latin>` (pure inheritance), which is the common case -- this
    returns None in that case rather than guessing."""
    try:
        tf = shape.text_frame
    except Exception:
        return None
    try:
        for p in tf.paragraphs:
            for r in p.runs:
                if r.text and r.text.strip() and r.font.name:
                    return r.font.name
    except Exception:
        pass
    return None


def _lvl1_defrpr_latin(element) -> str | None:
    """`<a:lstStyle>/<a:lvl1pPr>/<a:defRPr>/<a:latin typeface="...">`
    off a given element (a placeholder shape's own element, or a
    `<p:titleStyle>`/`<p:bodyStyle>`/`<p:otherStyle>` element) -- the
    real place Slidesgo/Google-Slides templates were found (v0.6.0
    cold-agent-test follow-up) to declare a placeholder's actual
    display font, separate from and NOT visible via the theme's
    fontScheme (`theme1.xml`'s majorFont/minorFont) alone."""
    ns_a = OOXML_NS["a"]
    node = element.find(f".//{{{ns_a}}}lvl1pPr/{{{ns_a}}}defRPr/{{{ns_a}}}latin")
    if node is None:
        return None
    typeface = node.get("typeface")
    return typeface or None


def resolve_effective_font(shape, slide) -> str | None:
    """Best-effort resolution of a shape's REAL effective font, beyond
    the theme's fontScheme alone.

    Real bug found via a cold-agent usability test (2026-08-02,
    friction #2 in this skill's own SKILL.md changelog): `--vietnamese`
    only ever checked/applied the theme's majorFont/minorFont, but a
    real Slidesgo template (`Vintage Recipe Book by Slidesgo.pptx`,
    confirmed by direct XML inspection) declares its actual title font
    ("Libre Baskerville") and subtitle font ("Roboto") on the SLIDE
    LAYOUT's placeholder `<a:lstStyle>/<a:lvl1pPr>/<a:defRPr>/<a:latin>`
    -- while `theme1.xml` itself just says "Arial" for both slots. The
    old code would report "Arial" (theme) as the effective font (safe),
    when the template's real rendered font is something the theme
    scheme never mentions at all -- a genuine blind spot, not a false
    positive on a font that was actually checked.

    Resolution order, each tier only consulted if the previous found
    nothing (never all three at once -- most specific signal wins):
    1. The shape's own explicit run-level font (`_run_level_font`) --
       most authoritative when present, since it's literally what
       this exact shape is already rendering.
    2. The matching placeholder (by `placeholder_format.idx`) on
       `slide.slide_layout`'s own `<a:lstStyle>` default run props.
    3. The slide master's `<p:txStyles>` (`titleStyle` for a
       TITLE/CENTER_TITLE placeholder, `bodyStyle` for BODY/OBJECT/
       SUBTITLE, `otherStyle` for anything else / non-placeholder).

    Returns None (not a guess) if none of the three has an explicit
    font -- the caller falls back to the theme scheme, same as before
    this function existed. This is a best-effort real-world fix, not a
    full OOXML style-cascade resolver (doesn't walk per-paragraph
    `lvl2pPr..lvl9pPr`, doesn't reconcile a layout placeholder that
    itself only partially overrides the master) -- documented as such
    in SKILL.md rather than overclaiming full cascade correctness.
    """
    own = _run_level_font(shape)
    if own:
        return own

    is_placeholder = False
    ph_idx = None
    ph_type = None
    try:
        pf = shape.placeholder_format
        if pf is not None and pf.type is not None:
            is_placeholder = True
            ph_idx = pf.idx
            ph_type = str(pf.type).split(".")[-1].rstrip("'").split(" ")[0]
    except (ValueError, AttributeError, TypeError):
        pass

    if is_placeholder and ph_idx is not None:
        try:
            for layout_ph in slide.slide_layout.placeholders:
                if layout_ph.placeholder_format.idx == ph_idx:
                    found = _lvl1_defrpr_latin(layout_ph._element)
                    if found:
                        return found
                    break
        except Exception:
            pass

    try:
        master_element = slide.slide_layout.slide_master.element
        ns_p = OOXML_NS["p"]
        style_tag = "titleStyle" if ph_type in ("TITLE", "CENTER_TITLE") else (
            "bodyStyle" if ph_type in ("BODY", "OBJECT", "SUBTITLE", "CONTENT") else "otherStyle"
        )
        tx_styles = master_element.find(f".//{{{ns_p}}}txStyles/{{{ns_p}}}{style_tag}")
        if tx_styles is not None:
            found = _lvl1_defrpr_latin(tx_styles)
            if found:
                return found
    except Exception:
        pass

    return None


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
