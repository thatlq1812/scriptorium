#!/usr/bin/env python3
"""Validate a Vietnamese administrative-document content JSON against
Nghị định 30/2020/NĐ-CP's real formatting rules, then render it into a
self-contained Typst (.typ) file using vnnd30.typ's functions (see
references/nd30-2020-formatting.md for the grounding table this enforces).

Never invents content -- every field must be supplied by the caller. This
script only refuses loudly when something doesn't match a known NĐ 30/2020
convention (a malformed số/ký hiệu, an unrecognized tên loại, a missing
required field), and otherwise mechanically maps validated content onto the
correct function with the correct font/size/style already baked into
vnnd30.typ -- no Typst knowledge required from the caller.

Engine (v0.4.0): Typst, not XeLaTeX. This mode was originally built on
XeLaTeX/MiKTeX; switched to Typst after comparing against a sibling
project (D:/elix/praxis_csc) that made the identical switch for its own
document export, for the same reason -- a full LaTeX distribution is
~5GB and not realistically portable to an arbitrary target machine, while
Typst is a single ~50MB static binary (see skills/typst-bootstrap). The
book/report scaffold mode elsewhere in this skill stays on XeLaTeX
deliberately -- see SKILL.md "Engine per mode" for why.

Supported doc_kieu: "cong_van", "quyet_dinh_truc_tiep", "van_ban_ten_loai",
"nghi_quyet", "bien_ban", "cong_dien" (Mẫu 1.6), "giay_moi" (Mẫu 1.7).

Density presets (v0.5.0, --density): "tiet_kiem_giay", "tieu_chuan",
"trang_trong" -- an optional knob bundling margin + Quốc hiệu/Tiêu ngữ/
Địa danh/body font size + first-line indent + line spacing into ONE named
choice, ported from a real prior production system's DENSITY_PRESETS table
(see SKILL.md metadata.elicited_from). Omitting --density leaves every
default byte-identical to pre-v0.5.0 behavior.

Số/ký hiệu convention: every doc_kieu this skill covers is a "văn bản hành
chính cá biệt" (an individual administrative act -- a specific decision/
notice/report), which per Mẫu 1.1-1.9's real templates uses
"<so>/<loai_vt>-<co_quan_vt>" with NO year embedded. Only a "văn bản quy
phạm pháp luật" (a law-making normative document, e.g. Nghị định itself --
"30/2020/NĐ-CP") uses the with-year convention `legal-citation-checker`
validates for CITATIONS to such laws -- that convention does not apply
here, to any doc_kieu this script authors.

Exit codes: 0 = rendered (and compiled, if --compile), 1 = validation
errors found (nothing written), 2 = malformed input / missing prerequisite.

Usage:
    python render_nd30_document.py <content.json> <output_dir> [--compile]
        [--margin-top MM] [--margin-bottom MM] [--margin-left MM] [--margin-right MM]
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
TYP_LIB_PATH = SKILL_ROOT / "assets" / "vnnd30.typ"
ABBR_PATH = SKILL_ROOT / "references" / "loai_van_ban_viet_tat.json"
SHARED_TYPST_DIR = REPO_ROOT / ".tools" / "typst"

_SEGMENT = r"[A-ZĐ][A-Za-zĐđ]*"  # e.g. "QĐ", "BGDĐT", "GDTrH" (mixed-case agency abbreviations are real)
SO_HIEU_RE = re.compile(rf"^\d{{1,6}}/{_SEGMENT}(-{_SEGMENT})*$")
QUYEN_HAN_VALUES = {"", "TM.", "Q.", "KT.", "TL.", "TUQ."}
DOC_KIEU_VALUES = {
    "cong_van", "quyet_dinh_truc_tiep", "van_ban_ten_loai", "nghi_quyet", "bien_ban",
    "cong_dien", "giay_moi",
}
DOC_KIEU_WITH_TEN_LOAI = {"quyet_dinh_truc_tiep": "QUYẾT ĐỊNH", "nghi_quyet": "NGHỊ QUYẾT"}

# NĐ 30/2020 Phụ lục I Mục I.3 permitted ranges (mm). A caller may override
# the concrete default within these ranges via --margin-*, never outside them.
MARGIN_RANGES_MM = {
    "top": (20, 25), "bottom": (20, 25), "left": (30, 35), "right": (15, 20),
}

# v0.5.0: named density presets (--density), an optional knob bundling
# margin + font-size + indent + line-spacing into one choice. Font-size/
# indent/line-spacing live in assets/vnnd30.typ's nd-density-presets (Typst
# reads its own copy); margins are validated/applied here in Python (single
# source of truth for the legal-range check already enforced by
# MARGIN_RANGES_MM). Both tables' concrete numbers are ported from the same
# real prior production system's DENSITY_PRESETS table (see SKILL.md
# metadata.elicited_from, v0.5.0 entry) and stay within MARGIN_RANGES_MM.
DENSITY_PRESET_VALUES = {"tiet_kiem_giay", "tieu_chuan", "trang_trong"}
DENSITY_PRESET_MARGINS_MM = {
    "tiet_kiem_giay": {"top": 20, "bottom": 20, "left": 30, "right": 20},
    "tieu_chuan": {"top": 20, "bottom": 20, "left": 30, "right": 20},
    "trang_trong": {"top": 25, "bottom": 25, "left": 35, "right": 20},
}


class ContentError(Exception):
    pass


def typst_escape(text: str) -> str:
    """Escape a value for use inside a Typst double-quoted string literal.
    Typst's string escaping is much narrower than LaTeX's -- only a literal
    backslash or double-quote needs escaping inside `"..."`; every other
    character (including `#`, `*`, `_`, `-`) is inert as long as it stays
    inside the quotes rather than being interpreted as markup."""
    if not isinstance(text, str):
        raise ContentError(f"expected a string, got {type(text).__name__}: {text!r}")
    return text.replace("\\", "\\\\").replace('"', '\\"')


def find_typst() -> str | None:
    binary_name = "typst.exe" if platform.system() == "Windows" else "typst"
    shared = SHARED_TYPST_DIR / binary_name
    if shared.is_file():
        return str(shared)
    return shutil.which("typst")


def load_abbreviations() -> dict[str, str]:
    data = json.loads(ABBR_PATH.read_text(encoding="utf-8"))
    return dict(data["van_ban_hanh_chinh"])


def _canonical_key(hien_thi: str, abbrevs: dict[str, str]) -> str | None:
    for key in abbrevs:
        if key.strip().lower() == hien_thi.strip().lower():
            return key
    return None


def _validate_nguoi_ky(nguoi_ky, errors: list[str], prefix: str = "nguoi_ky") -> None:
    if not isinstance(nguoi_ky, dict):
        errors.append(f"{prefix} must be an object with quyen_han/chuc_vu/ho_ten")
        return
    quyen_han = nguoi_ky.get("quyen_han", "")
    if quyen_han not in QUYEN_HAN_VALUES:
        errors.append(f"{prefix}.quyen_han must be one of {sorted(QUYEN_HAN_VALUES)}, got {quyen_han!r}")
    if not nguoi_ky.get("chuc_vu"):
        errors.append(f"{prefix}.chuc_vu is required")
    if not nguoi_ky.get("ho_ten"):
        errors.append(f"{prefix}.ho_ten is required")
    tap_the = nguoi_ky.get("tap_the")
    if tap_the is not None and not quyen_han:
        errors.append(f"{prefix}.tap_the (collective-body signature, e.g. 'ỦY BAN NHÂN DÂN') requires a non-empty quyen_han (e.g. 'TM.')")


def validate(content: dict) -> list[str]:
    errors: list[str] = []

    doc_kieu = content.get("doc_kieu")
    if doc_kieu not in DOC_KIEU_VALUES:
        errors.append(f"doc_kieu must be one of {sorted(DOC_KIEU_VALUES)}, got {doc_kieu!r}")
        return errors  # can't validate the rest without knowing the shape

    if doc_kieu == "bien_ban":
        return _validate_bien_ban(content)

    for field in ("co_quan_ban_hanh", "dia_danh", "so", "ngay", "thang", "nam", "noi_nhan", "nguoi_ky"):
        if field not in content:
            errors.append(f"missing required field: {field!r}")
    if errors:
        return errors

    ngay, thang, nam = content["ngay"], content["thang"], content["nam"]
    if not (isinstance(ngay, int) and 1 <= ngay <= 31):
        errors.append(f"ngay must be an integer 1-31, got {ngay!r}")
    if not (isinstance(thang, int) and 1 <= thang <= 12):
        errors.append(f"thang must be an integer 1-12, got {thang!r}")
    if not (isinstance(nam, int) and 1000 <= nam <= 9999):
        errors.append(f"nam must be a 4-digit integer, got {nam!r}")

    so = content["so"]
    ky_hieu = content.get("ky_hieu")
    if not ky_hieu:
        errors.append("ky_hieu is required (e.g. 'QĐ-UBND' or 'SNV-VP' -- no year, see module docstring)")
    elif not isinstance(so, int) or so < 1:
        errors.append(f"so must be a positive integer, got {so!r}")
    elif not SO_HIEU_RE.match(f"{so}/{ky_hieu}"):
        errors.append(
            f"so/ky_hieu {so}/{ky_hieu!r} doesn't match the văn-bản-cá-biệt numbering convention "
            f"'<so>/<loai_vt-hoac-coquan_vt>-<don_vi_vt>' (no year), e.g. '45/SNV-VP' or '12/QĐ-UBND'"
        )

    _validate_nguoi_ky(content["nguoi_ky"], errors)

    noi_nhan = content["noi_nhan"]
    if not isinstance(noi_nhan, list) or not noi_nhan or not all(isinstance(x, str) and x.strip() for x in noi_nhan):
        errors.append("noi_nhan must be a non-empty list of non-empty strings")

    if doc_kieu == "cong_van":
        if not content.get("trich_yeu_cong_van"):
            errors.append("cong_van requires trich_yeu_cong_van (the 'V/v ...' line)")
        if not content.get("kinh_gui") or not isinstance(content["kinh_gui"], list):
            errors.append("cong_van requires a non-empty kinh_gui list")
        if not content.get("noi_dung_doan"):
            errors.append("cong_van requires a non-empty noi_dung_doan list")

    elif doc_kieu in ("quyet_dinh_truc_tiep", "nghi_quyet"):
        if not content.get("trich_yeu"):
            errors.append(f"{doc_kieu} requires trich_yeu")
        if not content.get("can_cu") or not isinstance(content["can_cu"], list):
            errors.append(f"{doc_kieu} requires a non-empty can_cu list")
        if doc_kieu == "quyet_dinh_truc_tiep":
            dieu_list = content.get("dieu_list")
            if not dieu_list or not isinstance(dieu_list, list):
                errors.append("quyet_dinh_truc_tiep requires a non-empty dieu_list")
            else:
                for i, d in enumerate(dieu_list):
                    if not isinstance(d, dict) or not d.get("so") or not d.get("noi_dung"):
                        errors.append(f"dieu_list[{i}] must be an object with 'so' and 'noi_dung'")
        else:  # nghi_quyet: free-form content after "QUYẾT NGHỊ:", no Điều enumeration in the real mẫu
            if not content.get("noi_dung_doan"):
                errors.append("nghi_quyet requires a non-empty noi_dung_doan list")

    elif doc_kieu == "van_ban_ten_loai":
        ten_loai = content.get("ten_loai")
        if not isinstance(ten_loai, dict) or not ten_loai.get("hien_thi") or not ten_loai.get("viet_tat"):
            errors.append("van_ban_ten_loai requires ten_loai: {hien_thi, viet_tat}")
        else:
            abbrevs = load_abbreviations()
            match = abbrevs.get(_canonical_key(ten_loai["hien_thi"], abbrevs))
            if match is None or match != ten_loai["viet_tat"]:
                errors.append(
                    f"ten_loai {ten_loai!r} doesn't match a known Phụ lục III entry "
                    f"(see references/loai_van_ban_viet_tat.json) -- do not invent a new abbreviation"
                )
        if not content.get("trich_yeu"):
            errors.append("van_ban_ten_loai requires trich_yeu")
        if not content.get("noi_dung_doan"):
            errors.append("van_ban_ten_loai requires a non-empty noi_dung_doan list")

    elif doc_kieu == "cong_dien":
        # Mẫu 1.6 (Phụ lục III Mục II, trang 10 của PDF gốc): trích yếu +
        # "<người đứng đầu> điện:" + danh sách nơi nhận điện + nội dung điện.
        if not content.get("trich_yeu"):
            errors.append("cong_dien requires trich_yeu")
        if not content.get("nguoi_dung_dau"):
            errors.append("cong_dien requires nguoi_dung_dau (chú thích 6 của mẫu thật: tên cơ quan/chức danh người đứng đầu ban hành điện)")
        if not content.get("nguoi_nhan_dien") or not isinstance(content["nguoi_nhan_dien"], list):
            errors.append("cong_dien requires a non-empty nguoi_nhan_dien list (chú thích 7: tên cơ quan/tổ chức nhận điện)")
        if not content.get("noi_dung_doan"):
            errors.append("cong_dien requires a non-empty noi_dung_doan list")

    elif doc_kieu == "giay_moi":
        # Mẫu 1.7 (Phụ lục III Mục II, trang 11 của PDF gốc): trích yếu (tên
        # cuộc họp) + người được mời + nội dung cuộc họp + chủ trì/thời
        # gian/địa điểm; "các vấn đề cần lưu ý" (chú thích 8) is optional.
        if not content.get("trich_yeu"):
            errors.append("giay_moi requires trich_yeu (chú thích 5 của mẫu thật: trích yếu nội dung cuộc họp)")
        if not content.get("nguoi_duoc_moi"):
            errors.append("giay_moi requires nguoi_duoc_moi (chú thích 6: tên cơ quan/họ tên, chức vụ, đơn vị công tác của người được mời)")
        if not content.get("noi_dung_cuoc_hop"):
            errors.append("giay_moi requires noi_dung_cuoc_hop (chú thích 7: tên/nội dung cuộc họp, hội thảo, hội nghị)")
        if not content.get("chu_tri"):
            errors.append("giay_moi requires chu_tri")
        if not content.get("thoi_gian"):
            errors.append("giay_moi requires thoi_gian")
        if not content.get("dia_diem"):
            errors.append("giay_moi requires dia_diem")

    return errors


def _validate_bien_ban(content: dict) -> list[str]:
    """Mẫu 1.9 has a structurally different shape from every other doc_kieu:
    no dia_danh/quốc hiệu date line in the header (the date lives in
    thoi_gian_ket_thuc instead), and a 2-column THƯ KÝ/CHỦ TỌA signature
    footer instead of Nơi nhận + quyền hạn-chức vụ."""
    errors: list[str] = []
    for field in ("co_quan_ban_hanh", "so", "ky_hieu", "trich_yeu", "thoi_gian_bat_dau",
                  "dia_diem", "thanh_phan_tham_du", "chu_tri", "thu_ky", "noi_dung_doan",
                  "thoi_gian_ket_thuc", "thu_ky_ho_ten", "chu_toa_ho_ten", "noi_nhan"):
        if field not in content or (isinstance(content[field], (str, list)) and not content[field]):
            errors.append(f"bien_ban: missing/empty required field: {field!r}")
    if errors:
        return errors

    so, ky_hieu = content["so"], content["ky_hieu"]
    if not isinstance(so, int) or so < 1 or not SO_HIEU_RE.match(f"{so}/{ky_hieu}"):
        errors.append(f"bien_ban: so/ky_hieu {so}/{ky_hieu!r} doesn't match '<so>/<loai_vt>-<co_quan_vt>', e.g. '12/BB-VP'")

    ket_thuc = content["thoi_gian_ket_thuc"]
    if not isinstance(ket_thuc, dict) or not all(k in ket_thuc for k in ("gio", "ngay", "thang", "nam")):
        errors.append("bien_ban: thoi_gian_ket_thuc must be an object with gio/ngay/thang/nam")

    if not isinstance(content["noi_dung_doan"], list):
        errors.append("bien_ban: noi_dung_doan must be a list")

    noi_nhan = content["noi_nhan"]
    if not isinstance(noi_nhan, list) or not all(isinstance(x, str) and x.strip() for x in noi_nhan):
        errors.append("bien_ban: noi_nhan must be a list of non-empty strings")

    return errors


def _typ_str(text: str) -> str:
    """Wrap an already-escaped value in Typst double quotes."""
    return f'"{typst_escape(text)}"'


def _typ_list(items: list[str]) -> str:
    return "(" + ", ".join(_typ_str(x) for x in items) + ("," if len(items) == 1 else "") + ")"


def build_typst(content: dict, margins: dict[str, int] | None = None, density: str | None = None) -> str:
    doc_kieu = content["doc_kieu"]
    margins = margins or {}
    setup_arg_list = [f"margin-{k}: {v}mm" for k, v in margins.items()]
    if density is not None:
        setup_arg_list.append(f'density: "{density}"')
    setup_args = ", ".join(setup_arg_list)
    setup_call = f'#show: nd-setup.with({setup_args})' if setup_args else "#show: nd-setup"

    parts: list[str] = [
        '#import "vnnd30.typ": *',
        setup_call,
        "",
    ]

    if doc_kieu == "bien_ban":
        return _build_typst_bien_ban(content, parts)

    so_hieu_display = f"{content['so']}/{content['ky_hieu']}"
    left_col: list[str] = [
        f"#nd-coquan({_typ_str(content.get('co_quan_chu_quan') or '')}, {_typ_str(content['co_quan_ban_hanh'])})",
        f"#nd-sokyhieu({_typ_str(so_hieu_display)})",
    ]
    if doc_kieu == "cong_van":
        left_col.append(f"#nd-trichyeu-congvan({_typ_str(content['trich_yeu_cong_van'])})")
    right_col = [
        "#nd-quochieu-tieungu()",
        f"#nd-diadanhngay({_typ_str(content['dia_danh'])}, {content['ngay']}, {content['thang']}, {content['nam']})",
    ]
    parts.append(
        "#nd-2col(\n  [" + "\n  ".join(left_col) + "],\n  [\n  " + "\n  ".join(right_col) + "\n  ],\n)"
    )

    if doc_kieu == "cong_van":
        parts.append(f"#nd-kinhgui({_typ_list(content['kinh_gui'])})")
        parts.append(f"#nd-noidung({_typ_list(content['noi_dung_doan'])})")

    elif doc_kieu in ("quyet_dinh_truc_tiep", "nghi_quyet"):
        ten_loai = DOC_KIEU_WITH_TEN_LOAI[doc_kieu]
        parts.append(f'#nd-tenloai-trichyeu("{ten_loai}", {_typ_str(content["trich_yeu"])})')
        parts.append("#nd-thamquyenbanhanh()")
        for cc in content["can_cu"]:
            parts.append(f'Căn cứ {typst_escape(cc)};\\')
        if content.get("theo_de_nghi"):
            parts.append(f'Theo đề nghị của {typst_escape(content["theo_de_nghi"])}.')
        parts.append("")
        if doc_kieu == "quyet_dinh_truc_tiep":
            parts.append("*QUYẾT ĐỊNH:*")
            parts.append("")
            for d in content["dieu_list"]:
                parts.append(f'#nd-dieu("{d["so"]}", [{typst_escape(d["noi_dung"])}])')
        else:  # nghi_quyet
            parts.append("*QUYẾT NGHỊ:*")
            parts.append("")
            parts.append(f"#nd-noidung({_typ_list(content['noi_dung_doan'])})")

    elif doc_kieu == "van_ban_ten_loai":
        parts.append(f'#nd-tenloai-trichyeu({_typ_str(content["ten_loai"]["hien_thi"])}, {_typ_str(content["trich_yeu"])})')
        parts.append(f"#nd-noidung({_typ_list(content['noi_dung_doan'])})")

    elif doc_kieu == "cong_dien":
        parts.append(f'#nd-tenloai-trichyeu("CÔNG ĐIỆN", {_typ_str(content["trich_yeu"])})')
        parts.append(f"#nd-dien({_typ_str(content['nguoi_dung_dau'])}, {_typ_list(content['nguoi_nhan_dien'])})")
        parts.append(f"#nd-noidung({_typ_list(content['noi_dung_doan'])})")

    elif doc_kieu == "giay_moi":
        parts.append(f'#nd-tenloai-trichyeu("GIẤY MỜI", {_typ_str(content["trich_yeu"])})')
        giaymoi_args = (
            f"{_typ_str(content['co_quan_ban_hanh'])}, {_typ_str(content['nguoi_duoc_moi'])}, "
            f"{_typ_str(content['noi_dung_cuoc_hop'])}, {_typ_str(content['chu_tri'])}, "
            f"{_typ_str(content['thoi_gian'])}, {_typ_str(content['dia_diem'])}"
        )
        if content.get("luu_y"):
            giaymoi_args += f", luu-y: {_typ_str(content['luu_y'])}"
        parts.append(f"#nd-giaymoi-noidung({giaymoi_args})")

    nguoi_ky = content["nguoi_ky"]
    parts.append("")
    if nguoi_ky.get("tap_the"):
        signer_call = (
            f'nd-nguoiky-tapthe({_typ_str(nguoi_ky["quyen_han"])}, {_typ_str(nguoi_ky["tap_the"])}, '
            f'{_typ_str(nguoi_ky["chuc_vu"])}, {_typ_str(nguoi_ky["ho_ten"])})'
        )
    else:
        signer_call = (
            f'nd-nguoiky({_typ_str(nguoi_ky.get("quyen_han", ""))}, {_typ_str(nguoi_ky["chuc_vu"])}, '
            f'{_typ_str(nguoi_ky["ho_ten"])})'
        )
    parts.append(f"#nd-2col(\n  nd-noinhan({_typ_list(content['noi_nhan'])}),\n  {signer_call},\n)")
    return "\n".join(parts) + "\n"


def _build_typst_bien_ban(content: dict, parts: list[str]) -> str:
    ket_thuc = content["thoi_gian_ket_thuc"]
    so_hieu_display = f"{content['so']}/{content['ky_hieu']}"
    parts.append(
        "#nd-2col(\n  nd-coquan(" + _typ_str(content.get("co_quan_chu_quan") or "") + ", "
        + _typ_str(content["co_quan_ban_hanh"]) + "),\n  nd-quochieu-tieungu(),\n)"
    )
    parts.append(f"#nd-sokyhieu({_typ_str(so_hieu_display)})")
    parts.append(f'#nd-tenloai-trichyeu("BIÊN BẢN", {_typ_str(content["trich_yeu"])})')
    parts.append(
        f'#nd-bienban-info({_typ_str(content["thoi_gian_bat_dau"])}, {_typ_str(content["dia_diem"])}, '
        f'{_typ_str(content["thanh_phan_tham_du"])}, {_typ_str(content["chu_tri"])}, {_typ_str(content["thu_ky"])})'
    )
    parts.append(f"#nd-noidung({_typ_list(content['noi_dung_doan'])})")
    parts.append(
        f'Cuộc họp (hội nghị, hội thảo) kết thúc vào {ket_thuc["gio"]} giờ, '
        f'ngày {ket_thuc["ngay"]} tháng {ket_thuc["thang"]} năm {ket_thuc["nam"]}./.'
    )
    parts.append("")
    parts.append(f'#nd-bienban-chuky({_typ_str(content["thu_ky_ho_ten"])}, {_typ_str(content["chu_toa_ho_ten"])})')
    parts.append(f"#nd-noinhan({_typ_list(content['noi_nhan'])})")
    return "\n".join(parts) + "\n"


def _parse_margins(args: argparse.Namespace) -> dict[str, int]:
    # Start from the density preset's margins (if --density was given) --
    # an explicit --margin-* always wins over the preset for that one side,
    # since it's the more specific, manually-chosen value.
    margins: dict[str, int] = dict(DENSITY_PRESET_MARGINS_MM[args.density]) if args.density else {}
    for side in ("top", "bottom", "left", "right"):
        value = getattr(args, f"margin_{side}")
        if value is None:
            continue
        lo, hi = MARGIN_RANGES_MM[side]
        if not (lo <= value <= hi):
            raise ContentError(f"--margin-{side} must be within NĐ 30/2020's permitted range {lo}-{hi}mm, got {value}mm")
        margins[side] = value
    return margins


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("content", type=Path, help="Path to a content JSON file")
    parser.add_argument("output_dir", type=Path, help="Directory to write main.typ + vnnd30.typ into")
    parser.add_argument("--compile", action="store_true", help="Also run typst compile if it's available")
    parser.add_argument("--margin-top", type=int, default=None, help="mm, must be within 20-25")
    parser.add_argument("--margin-bottom", type=int, default=None, help="mm, must be within 20-25")
    parser.add_argument("--margin-left", type=int, default=None, help="mm, must be within 30-35")
    parser.add_argument("--margin-right", type=int, default=None, help="mm, must be within 15-20")
    parser.add_argument(
        "--density", choices=sorted(DENSITY_PRESET_VALUES), default=None,
        help="optional named preset bundling margin+font-size+indent+line-spacing; omit to keep pre-v0.5.0 defaults",
    )
    args = parser.parse_args()

    try:
        content = json.loads(args.content.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    if not isinstance(content, dict):
        print("MALFORMED: content JSON must be an object", file=sys.stderr)
        return 2

    try:
        margins = _parse_margins(args)
    except ContentError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
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
        typ_source = build_typst(content, margins, args.density)
    except ContentError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "main.typ").write_text(typ_source, encoding="utf-8", newline="\n")
    shutil.copy(TYP_LIB_PATH, args.output_dir / "vnnd30.typ")
    print(f"OK: wrote {args.output_dir / 'main.typ'} (+ vnnd30.typ)")

    if args.compile:
        typst_bin = find_typst()
        if typst_bin is None:
            print("COMPILE SKIPPED: typst not found (see typst-bootstrap).", file=sys.stderr)
            return 0
        result = subprocess.run(
            [typst_bin, "compile", "main.typ", "main.pdf"],
            cwd=args.output_dir, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode != 0:
            print("COMPILE FAILED:", file=sys.stderr)
            print(result.stderr[-3000:], file=sys.stderr)
            return 1
        print(f"OK: compiled {args.output_dir / 'main.pdf'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
