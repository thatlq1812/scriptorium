"""
Visual effects for already-inserted picture shapes (rounded corners,
border, shadow). Standalone utility, not wired into compile_deck.py's
v1 pipeline (v1 does not insert/replace images -- see SKILL.md "Known
limitations"). Kept for a future round or for a caller that inserts its
own picture (e.g. via gemini-generator) and wants template-grade
finishing touches applied afterward.

Ported near-verbatim (pure XML mutation, no I/O) from:
D:/elix/archive/platform_archive/modules/presentation/pptx/image_formatter.py
"""
from __future__ import annotations

import logging

from lxml import etree
from pptx.oxml.ns import qn

logger = logging.getLogger("slide_deck_composer")


def format_image_shape(
    picture,
    rounded_corners: bool = False,
    corner_radius: int = 16667,
    border_color: str | None = None,
    border_width_pt: float = 1.0,
    shadow: bool = False,
    shadow_blur_pt: float = 4.0,
    shadow_distance_pt: float = 3.0,
    shadow_opacity: int = 40,
) -> None:
    try:
        sp = picture._element
        spPr = sp.find(qn("p:spPr"))
        if spPr is None:
            spPr = sp.find(qn("pic:spPr"))
        if spPr is None:
            for child in sp:
                if child.tag.endswith("}spPr"):
                    spPr = child
                    break
        if spPr is None:
            logger.warning("Cannot find spPr on image shape")
            return

        if rounded_corners:
            _apply_rounded_corners(spPr, corner_radius)
        if border_color:
            _apply_border(spPr, border_color, border_width_pt)
        if shadow:
            _apply_shadow(spPr, shadow_blur_pt, shadow_distance_pt, shadow_opacity)
    except Exception as e:
        logger.warning("Failed to format image shape: %s", e)


def _apply_rounded_corners(spPr, corner_radius: int) -> None:
    prstGeom = spPr.find(qn("a:prstGeom"))
    if prstGeom is not None:
        spPr.remove(prstGeom)
    new_geom = etree.SubElement(spPr, qn("a:prstGeom"))
    new_geom.set("prst", "roundRect")
    avLst = etree.SubElement(new_geom, qn("a:avLst"))
    gd = etree.SubElement(avLst, qn("a:gd"))
    gd.set("name", "adj")
    gd.set("fmla", "val %d" % corner_radius)


def _apply_border(spPr, color: str, width_pt: float) -> None:
    existing_ln = spPr.find(qn("a:ln"))
    if existing_ln is not None:
        spPr.remove(existing_ln)
    ln = etree.SubElement(spPr, qn("a:ln"))
    ln.set("w", str(int(width_pt * 12700)))
    solidFill = etree.SubElement(ln, qn("a:solidFill"))
    srgbClr = etree.SubElement(solidFill, qn("a:srgbClr"))
    srgbClr.set("val", color)


def _apply_shadow(spPr, blur_pt: float, distance_pt: float, opacity: int) -> None:
    existing_eff = spPr.find(qn("a:effectLst"))
    if existing_eff is not None:
        spPr.remove(existing_eff)
    effectLst = etree.SubElement(spPr, qn("a:effectLst"))
    outerShdw = etree.SubElement(effectLst, qn("a:outerShdw"))
    outerShdw.set("blurRad", str(int(blur_pt * 12700)))
    outerShdw.set("dist", str(int(distance_pt * 12700)))
    outerShdw.set("dir", "5400000")
    outerShdw.set("rotWithShape", "0")
    srgbClr = etree.SubElement(outerShdw, qn("a:srgbClr"))
    srgbClr.set("val", "000000")
    alpha = etree.SubElement(srgbClr, qn("a:alpha"))
    alpha.set("val", str(opacity * 1000))
