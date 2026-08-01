"""
Template-slide classification: bucket the caller-supplied template's
real slides into title / content / closing so the compiler knows which
real slide to clone for each output slide.

Ported near-verbatim (pure, no I/O) from:
D:/elix/archive/platform_archive/modules/presentation/pptx/slide_classifier.py
"""
from __future__ import annotations

_INSTRUCTION_MARKERS: tuple[str, ...] = (
    "alternative resources", "fonts used", "to view this template",
    "editable presentation theme", "sister projects", "freepik",
    "flaticon", "storyset", "videvo", "wepik", "thanks slide",
    "infographic resources", "slidesgo | blog", "slidesgo |  blog",
    "credits and acknowledgements",
)

_TITLE_KEYWORDS: tuple[str, ...] = ("title", "cover", "intro", "opening")
_CLOSING_KEYWORDS: tuple[str, ...] = (
    "end", "thank", "thanks", "closing", "credit", "credits",
    "goodbye", "farewell", "outro", "final",
)

# Real bug found in self-test round 2 against an actual Slidesgo
# template ("Business Plan_ Minimalist Aesthetics"): its slide 1 is a
# vendor "About this template" instruction page written in Portuguese
# ("Conteudo deste modelo" / "Isto e o que voce vai encontrar nesse
# modelo de Slidesgo: ..."), which _INSTRUCTION_MARKERS never catches
# because every marker is an English phrase. The slide slipped into
# the "content" pool, got picked as a clone source, and its Portuguese
# instructional paragraph leaked into real output -- and because that
# paragraph happens to name "slidesgo", shape_roles.is_watermark_text
# also flagged it as an immutable watermark, so compile_deck.py's own
# stale-text cleanup sweep was blocked from clearing it (watermarks are
# deliberately protected from scrubbing so legitimate attribution
# credits survive). Two failures compounding: language-specific
# markers miss non-English instruction pages, AND the watermark
# protection (correct for a genuine short footer credit) had no length
# ceiling, so it also shielded a full paragraph.
#
# Fix: language-independent structural signal. A legitimate footer/
# attribution watermark line naming one of these vendor brands is
# always short (a few words). A whole PARAGRAPH mentioning one of them
# is instructional content, in any language -- flag the slide
# regardless of which language wrote the surrounding sentence.
_BRAND_WATERMARK_WORDS: tuple[str, ...] = (
    "slidesgo", "freepik", "flaticon", "storyset", "wepik",
)
_INSTRUCTION_PARAGRAPH_MIN_CHARS = 40


def is_instruction_slide(slide) -> bool:
    """Detect vendor "About this template"/credits/resources pages that
    must never be cloned for real content."""
    try:
        text_chunks: list[str] = []
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            txt = (shape.text_frame.text or "").lower()
            if txt:
                text_chunks.append(txt)
                if len(txt) > _INSTRUCTION_PARAGRAPH_MIN_CHARS and any(
                    b in txt for b in _BRAND_WATERMARK_WORDS
                ):
                    return True
            try:
                if shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            ct = (cell.text or "").lower()
                            if ct:
                                text_chunks.append(ct)
            except Exception:
                pass
        joined = " | ".join(text_chunks)
        if not joined:
            return False
        hits = sum(1 for m in _INSTRUCTION_MARKERS if m in joined)
        return hits >= 2
    except Exception:
        return False


def classify_template_slides(prs, original_count: int) -> dict[str, list[int]]:
    """Classify each original template slide into title/content/closing."""
    title_idx: list[int] = []
    content_idx: list[int] = []
    closing_idx: list[int] = []

    for i in range(original_count):
        try:
            slide = prs.slides[i]
            layout_name = (slide.slide_layout.name or "").lower()
        except Exception:
            layout_name = ""

        try:
            if is_instruction_slide(prs.slides[i]):
                continue
        except Exception:
            pass

        is_title = any(kw in layout_name for kw in _TITLE_KEYWORDS)
        is_closing = any(kw in layout_name for kw in _CLOSING_KEYWORDS)

        if is_title and not title_idx:
            title_idx.append(i)
        elif is_closing:
            closing_idx.append(i)
        else:
            content_idx.append(i)

    if not title_idx and original_count > 0:
        if content_idx and content_idx[0] == 0:
            title_idx.append(content_idx.pop(0))

    if not closing_idx and len(content_idx) >= 2:
        last_idx = content_idx[-1]
        try:
            last_slide = prs.slides[last_idx]
            total_chars = 0
            for shape in last_slide.shapes:
                if shape.has_text_frame:
                    total_chars += len(shape.text_frame.text or "")
            if total_chars < 80:
                closing_idx.append(content_idx.pop(-1))
        except Exception:
            pass

    return {"title": title_idx, "content": content_idx, "closing": closing_idx}
