"""
Experiment: replace every real image embedded in a compiled deck with a
random PIL-generated placeholder, at the zip/media level -- doesn't
touch any shape XML (position/crop/effects survive untouched), doesn't
need to walk grouped shapes to find <p:pic> elements.

Usage: python swap_images.py <input.pptx> <output.pptx>
"""
import random
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

PALETTES = [
    ((239, 108, 0), (255, 183, 77)),
    ((21, 101, 192), (100, 181, 246)),
    ((46, 125, 50), (129, 199, 132)),
    ((123, 31, 162), (206, 147, 216)),
    ((0, 121, 107), (77, 208, 225)),
]


def random_placeholder(width_px: int, height_px: int) -> bytes:
    c1, c2 = random.choice(PALETTES)
    img = Image.new("RGB", (width_px, height_px), c1)
    draw = ImageDraw.Draw(img)
    # A few random translucent-looking shapes so it's visibly "generated",
    # not a blank rectangle.
    for _ in range(6):
        x0 = random.randint(0, width_px)
        y0 = random.randint(0, height_px)
        r = random.randint(min(width_px, height_px) // 8, min(width_px, height_px) // 3)
        draw.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=c2)
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main(src: Path, dst: Path) -> None:
    with zipfile.ZipFile(src, "r") as zin:
        names = zin.namelist()
        media_names = [n for n in names if n.startswith("ppt/media/") and re.search(r"\.(png|jpg|jpeg|gif)$", n, re.I)]

        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                data = zin.read(name)
                if name in media_names:
                    try:
                        orig = Image.open(zipfile.ZipFile(src).open(name))
                        w, h = orig.size
                    except Exception:
                        w, h = 800, 600
                    data = random_placeholder(w, h)
                    # Force .png regardless of original extension isn't
                    # safe (name must match content-type/relationship) --
                    # PNG bytes work fine under a .jpg/.jpeg name for
                    # PowerPoint/LibreOffice's purposes in practice, but
                    # to stay honest we re-encode as the original format
                    # when it's a JPEG.
                    if re.search(r"\.jpe?g$", name, re.I):
                        import io
                        rgb = Image.open(io.BytesIO(data)).convert("RGB")
                        buf = io.BytesIO()
                        rgb.save(buf, format="JPEG", quality=70)
                        data = buf.getvalue()
                zout.writestr(name, data)

    print(f"Replaced {len(media_names)} embedded image(s): {media_names}")
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
