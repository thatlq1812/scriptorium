#!/usr/bin/env python3
"""Export a Vietnamese administrative-document content JSON (same schema and
validation as render_nd30_document.py) to DOCX via Pandoc, using
assets/reference-vn-nd30.docx as the --reference-doc so the exported file
keeps Times New Roman/black text instead of Pandoc's stock Aptos font +
blue/teal heading colors (see build_reference_docx.py for how that template
was built, adapted from a real fix in a sibling project, D:/elix/praxis_csc).

Deliberately does NOT feed the .tex file to pandoc -- pandoc's LaTeX reader
does not expand custom macros (\\ndCoQuan, \\ndSoKyHieu, ...) the way a real
TeX engine does, so it would either fail or silently drop content. Instead
this renders the SAME validated content straight to Markdown (a format
pandoc's writer handles natively and predictably), then converts that.

Exit codes: 0 = exported, 1 = validation errors found (nothing written),
2 = malformed input / missing prerequisite (pandoc not found, reference
template missing).

Usage:
    python export_nd30_docx.py <content.json> <output.docx>
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_nd30_document import ContentError, validate  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DOCX = SKILL_ROOT / "assets" / "reference-vn-nd30.docx"


def markdown_escape(text: str) -> str:
    if not isinstance(text, str):
        raise ContentError(f"expected a string, got {type(text).__name__}: {text!r}")
    for ch in ("\\", "*", "_", "|", "<", ">", "#"):
        text = text.replace(ch, "\\" + ch)
    return text


DOC_KIEU_WITH_TEN_LOAI = {"quyet_dinh_truc_tiep": "QUYẾT ĐỊNH", "nghi_quyet": "NGHỊ QUYẾT"}


def build_markdown(content: dict) -> str:
    doc_kieu = content["doc_kieu"]
    esc = markdown_escape

    if doc_kieu == "bien_ban":
        return _build_markdown_bien_ban(content)

    co_quan_left = esc(content["co_quan_ban_hanh"])
    if content.get("co_quan_chu_quan"):
        co_quan_left = f"{esc(content['co_quan_chu_quan'])}<br>**{co_quan_left}**"
    else:
        co_quan_left = f"**{co_quan_left}**"

    # No year in số/ký hiệu -- every doc_kieu here is a "văn bản hành chính cá
    # biệt" (Mẫu 1.1-1.9's real templates), not a normative law document like
    # Nghị định (which does use "<so>/<nam>/<loai>-<coquan>", a different rule
    # legal-citation-checker validates for CITATIONS, not authoring here).
    so_hieu_display = f"{content['so']}/{content['ky_hieu']}"
    left_cell = f"{co_quan_left}<br><br>Số: {esc(so_hieu_display)}"
    if doc_kieu == "cong_van":
        left_cell += f"<br>V/v {esc(content['trich_yeu_cong_van'])}"

    right_cell = (
        "**CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**<br>**Độc lập - Tự do - Hạnh phúc**<br><br>"
        f"*{esc(content['dia_danh'])}, ngày {content['ngay']} tháng {content['thang']} năm {content['nam']}*"
    )

    lines: list[str] = [
        f"| {left_cell} | {right_cell} |",
        "| --- | --- |",
        "",
    ]

    if doc_kieu == "cong_van":
        lines.append("**Kính gửi:**")
        lines.extend(f"- {esc(x)};" for x in content["kinh_gui"])
        lines.append("")
        lines.extend(esc(p) for p in content["noi_dung_doan"])

    elif doc_kieu in ("quyet_dinh_truc_tiep", "nghi_quyet"):
        ten_loai = DOC_KIEU_WITH_TEN_LOAI[doc_kieu]
        lines += [f"**{ten_loai}**", f"**{esc(content['trich_yeu'])}**", "", "**THẨM QUYỀN BAN HÀNH**", ""]
        lines.extend(f"*Căn cứ {esc(cc)};*" for cc in content["can_cu"])
        if content.get("theo_de_nghi"):
            lines.append(f"*Theo đề nghị của {esc(content['theo_de_nghi'])}.*")
        if doc_kieu == "quyet_dinh_truc_tiep":
            lines += ["", "**QUYẾT ĐỊNH:**", ""]
            for d in content["dieu_list"]:
                lines.append(f"**Điều {d['so']}.** {esc(d['noi_dung'])}")
        else:
            lines += ["", "**QUYẾT NGHỊ:**", ""]
            lines.extend(esc(p) for p in content["noi_dung_doan"])

    elif doc_kieu == "van_ban_ten_loai":
        lines += [f"**{esc(content['ten_loai']['hien_thi'])}**", f"**{esc(content['trich_yeu'])}**", ""]
        lines.extend(esc(p) for p in content["noi_dung_doan"])

    elif doc_kieu == "cong_dien":
        lines += [f"**CÔNG ĐIỆN**", f"**{esc(content['trich_yeu'])}**", ""]
        lines.append(f"{esc(content['nguoi_dung_dau'])} điện:")
        lines.extend(f"- {esc(x)};" for x in content["nguoi_nhan_dien"])
        lines.append("")
        lines.extend(esc(p) for p in content["noi_dung_doan"])

    elif doc_kieu == "giay_moi":
        lines += [f"**GIẤY MỜI**", f"**{esc(content['trich_yeu'])}**", ""]
        lines.append(f"{esc(content['co_quan_ban_hanh'])} trân trọng kính mời: {esc(content['nguoi_duoc_moi'])}")
        lines.append("")
        lines.append(f"Tới dự {esc(content['noi_dung_cuoc_hop'])}")
        lines.append("")
        lines.append(f"Chủ trì: {esc(content['chu_tri'])}")
        lines.append("")
        lines.append(f"Thời gian: {esc(content['thoi_gian'])}")
        lines.append("")
        lines.append(f"Địa điểm: {esc(content['dia_diem'])}")
        if content.get("luu_y"):
            lines.append("")
            lines.append(esc(content["luu_y"]))

    else:
        raise ContentError(
            f"build_markdown: doc_kieu {doc_kieu!r} passed validate() but has no Markdown-rendering "
            f"branch here -- refusing rather than silently emitting a header/footer-only DOCX with no body content"
        )

    nguoi_ky = content["nguoi_ky"]
    quyen_han = nguoi_ky.get("quyen_han", "")
    chuc_vu = nguoi_ky["chuc_vu"]
    if nguoi_ky.get("tap_the"):
        signer_line = f"**{esc(quyen_han)} {esc(nguoi_ky['tap_the'])}**<br>**{esc(chuc_vu)}**"
    elif quyen_han:
        signer_line = f"**{esc(quyen_han)} {esc(chuc_vu)}**"
    else:
        signer_line = f"**{esc(chuc_vu)}**"
    noi_nhan_lines = "<br>".join(f"- {esc(x)};" for x in content["noi_nhan"])

    lines += [
        "",
        f"| **Nơi nhận:**<br>{noi_nhan_lines} | {signer_line}<br><br><br>{esc(nguoi_ky['ho_ten'])} |",
        "| --- | --- |",
    ]
    return "\n".join(lines) + "\n"


def _build_markdown_bien_ban(content: dict) -> str:
    esc = markdown_escape
    co_quan_left = esc(content["co_quan_ban_hanh"])
    if content.get("co_quan_chu_quan"):
        co_quan_left = f"{esc(content['co_quan_chu_quan'])}<br>**{co_quan_left}**"
    else:
        co_quan_left = f"**{co_quan_left}**"
    so_hieu_display = f"{content['so']}/{content['ky_hieu']}"
    ket_thuc = content["thoi_gian_ket_thuc"]

    lines = [
        f"| {co_quan_left}<br><br>Số: {esc(so_hieu_display)} | **CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**<br>**Độc lập - Tự do - Hạnh phúc** |",
        "| --- | --- |",
        "",
        "**BIÊN BẢN**",
        f"**{esc(content['trich_yeu'])}**",
        "",
        f"Thời gian bắt đầu: {esc(content['thoi_gian_bat_dau'])}",
        "",
        f"Địa điểm: {esc(content['dia_diem'])}",
        "",
        f"Thành phần tham dự: {esc(content['thanh_phan_tham_du'])}",
        "",
        f"Chủ trì (chủ toạ): {esc(content['chu_tri'])}",
        "",
        f"Thư ký (người ghi biên bản): {esc(content['thu_ky'])}",
        "",
    ]
    lines.extend(esc(p) for p in content["noi_dung_doan"])
    lines += [
        "",
        f"Cuộc họp (hội nghị, hội thảo) kết thúc vào {ket_thuc['gio']} giờ, "
        f"ngày {ket_thuc['ngay']} tháng {ket_thuc['thang']} năm {ket_thuc['nam']}./.",
        "",
        f"| **THƯ KÝ**<br><br><br>{esc(content['thu_ky_ho_ten'])} | **CHỦ TỌA**<br><br><br>{esc(content['chu_toa_ho_ten'])} |",
        "| --- | --- |",
        "",
        "**Nơi nhận:**<br>" + "<br>".join(f"- {esc(x)};" for x in content["noi_nhan"]),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("content", type=Path)
    parser.add_argument("output_docx", type=Path)
    args = parser.parse_args()

    if shutil.which("pandoc") is None:
        print("MALFORMED: pandoc not found on PATH (see pandoc-bootstrap).", file=sys.stderr)
        return 2
    if not REFERENCE_DOCX.exists():
        print(f"MALFORMED: {REFERENCE_DOCX} not found (run build_reference_docx.py once).", file=sys.stderr)
        return 2

    try:
        content = json.loads(args.content.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    if not isinstance(content, dict):
        print("MALFORMED: content JSON must be an object", file=sys.stderr)
        return 2

    try:
        errors = validate(content)
    except ContentError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s). Nothing written.")
        for e in errors:
            print(f"  - {e}")
        return 1

    try:
        markdown = build_markdown(content)
    except ContentError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    args.output_docx.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "docx", f"--reference-doc={REFERENCE_DOCX}", "-o", str(args.output_docx)],
        input=markdown, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        print(f"EXPORT FAILED: {result.stderr}", file=sys.stderr)
        return 1

    print(f"OK: exported {args.output_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
