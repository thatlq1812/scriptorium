#!/usr/bin/env python3
"""Check a caller-declared online-ad/campaign record against 3 mechanically-
checkable rule sets from Vietnam's Nghị định 342/2025/NĐ-CP (detailing the
amended Luật Quảng cáo, effective 2026-02-15) -- Điều 17 (closeable-ad
wait-time/close-button rules), Điều 18 (violation-removal SLA), and Điều 19
(online-ad-service-business record-retention/reporting/notification rules),
plus a Điều 3 special-product-category router. Stdlib only (json, argparse,
datetime), local, deterministic -- no AI/network call of any kind.

CRITICAL SCOPE LIMIT (read before use): this script checks the STRUCTURAL/
NUMERIC rules that are honestly deterministic from a caller-declared record.
It does NOT verify a special product category's substantive ad-content
requirements (Điều 4-12 each set specific required disclosures per category,
e.g. mandatory warning text for cosmetics/food) -- it only flags that a
declared product_category is one of Điều 3's 11 regulated categories and
that Điều 4-12 applies, the same "route, don't verify" honesty this
project's legal-citation-checker already applies to Điều-existence checks.
It does NOT constitute legal advice, and does NOT check enforcement/penalty
amounts (a separate decree). A special-category ad should still get real
legal/compliance review before publishing.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_ad_compliance.py <ad_record.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

AD_TYPES = {"static_image", "video"}

# Điều 3 -- the exact 11 special product/service categories, each with its
# own additional content rules in Điều 4 through Điều 12.
SPECIAL_CATEGORIES = {
    "my_pham": "mỹ phẩm (Điều 4)",
    "thuc_pham": "thực phẩm (Điều 5)",
    "sua_dinh_duong_tre_nho": "sữa/sản phẩm dinh dưỡng trẻ nhỏ (Điều 6)",
    "hoa_chat_che_pham_diet_con_trung_khuan": "hóa chất/chế phẩm diệt côn trùng, diệt khuẩn (Điều 7)",
    "thiet_bi_y_te": "thiết bị y tế (Điều 8)",
    "kham_chua_benh": "dịch vụ khám bệnh, chữa bệnh (Điều 9)",
    "thuoc_bvtv_thu_y_thuc_an_chan_nuoi": "thuốc bảo vệ thực vật/thú y/thức ăn chăn nuôi-thủy sản (Điều 10)",
    "phan_bon": "phân bón (Điều 11a)",
    "giong_cay_trong": "giống cây trồng (Điều 11b)",
    "thuoc": "thuốc (Điều 12a)",
    "do_uong_co_con": "đồ uống có cồn (rượu/bia, Điều 12b)",
}


class RecordError(Exception):
    pass


def parse_date_field(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be an ISO date string 'YYYY-MM-DD', got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordError(f"{field} is not a real calendar date: {value!r} ({exc})") from exc


def validate_ad(ad: object) -> tuple[list[str], list[str]]:
    """Điều 17 (closeable-ad rules) + Điều 3 special-category routing."""
    errors: list[str] = []
    notes: list[str] = []
    if not isinstance(ad, dict):
        return ["ad must be an object"], notes

    ad_type = ad.get("ad_type")
    if ad_type not in AD_TYPES:
        errors.append(f"ad.ad_type must be one of {sorted(AD_TYPES)}, got {ad_type!r}")

    if ad.get("close_single_interaction") is not True:
        errors.append(
            "ad.close_single_interaction must be true -- Điều 17 khoản 2 requires the close control to work "
            "with exactly one interaction, and forbids fake or hard-to-identify close icons"
        )

    if ad.get("close_icon_fake_or_ambiguous") is not False:
        errors.append(
            "ad.close_icon_fake_or_ambiguous must be false -- Điều 17 khoản 2 explicitly bans fake or "
            "hard-to-distinguish close icons"
        )

    wait = ad.get("wait_time_seconds")
    if not isinstance(wait, (int, float)) or isinstance(wait, bool) or wait < 0:
        errors.append(f"ad.wait_time_seconds must be a non-negative number, got {wait!r}")
    elif ad_type == "static_image" and wait != 0:
        errors.append(
            f"ad.wait_time_seconds is {wait!r} but Điều 17 khoản 3 requires NO mandatory wait time "
            "(0 seconds) before a static-image ad can be closed"
        )
    elif ad_type == "video" and wait > 5:
        errors.append(
            f"ad.wait_time_seconds is {wait!r} but Điều 17 khoản 3 caps the wait time for video/moving-image "
            "ads at a MAXIMUM of 5 seconds before the close control must be available"
        )

    if ad.get("report_mechanism_present") is not True:
        errors.append(
            "ad.report_mechanism_present must be true -- Điều 17 khoản 4 requires a visible icon plus "
            "instructions for users to report violating ad content"
        )

    category = ad.get("product_category")
    if category is not None and category != "general":
        if category not in SPECIAL_CATEGORIES:
            errors.append(
                f"ad.product_category {category!r} is not recognized -- use 'general' or one of "
                f"{sorted(SPECIAL_CATEGORIES)}"
            )
        else:
            notes.append(
                f"ROUTED (not verified): product_category={category!r} is a Điều 3 special category "
                f"({SPECIAL_CATEGORIES[category]}) -- Điều 4-12 sets additional content-disclosure "
                "requirements this script does NOT check the substantive content of. Get real legal/"
                "compliance review before publishing this ad."
            )

    return errors, notes


def validate_ad_service_business(block: object) -> list[str]:
    """Điều 19 -- online-ad-service-business notification/retention/reporting rules."""
    if block is None:
        return []
    errors: list[str] = []
    if not isinstance(block, dict):
        return ["ad_service_business must be an object if present"]

    if block.get("contact_info_notified") is not True:
        errors.append(
            "ad_service_business.contact_info_notified must be true -- Điều 19 khoản 1 requires notifying "
            "contact info to the Ministry of Culture, Sports and Tourism before starting online-ad-service "
            "business in Vietnam"
        )

    last_display_raw = block.get("last_ad_display_date")
    retention_raw = block.get("retention_until")
    try:
        last_display = parse_date_field(last_display_raw, "ad_service_business.last_ad_display_date")
        retention_until = parse_date_field(retention_raw, "ad_service_business.retention_until")
        try:
            required_until = last_display.replace(year=last_display.year + 3)
        except ValueError:
            # Feb 29 on a non-leap target year -- fall back to Feb 28, same convention
            # most retention/expiry calendaring uses for this edge case.
            required_until = last_display.replace(year=last_display.year + 3, day=28)
        if retention_until < required_until:
            errors.append(
                f"ad_service_business.retention_until {retention_raw!r} is earlier than "
                f"{required_until.isoformat()!r} -- Điều 19 khoản 2 requires retaining advertising-activity "
                "records for 3 years from the date the ad was last displayed"
            )
    except RecordError as exc:
        errors.append(str(exc))

    report_raw = block.get("annual_report_filed_date")
    if report_raw is not None:
        try:
            report_date = parse_date_field(report_raw, "ad_service_business.annual_report_filed_date")
            if (report_date.month, report_date.day) > (11, 25):
                errors.append(
                    f"ad_service_business.annual_report_filed_date {report_raw!r} is after November 25 -- "
                    "Điều 19 khoản 3 requires the annual online-ad-service activity report no later than "
                    "November 25 each year"
                )
        except RecordError as exc:
            errors.append(str(exc))

    return errors


def validate_takedown_request(block: object) -> list[str]:
    """Điều 18 -- 24-hour violation-removal SLA."""
    if block is None:
        return []
    errors: list[str] = []
    if not isinstance(block, dict):
        return ["takedown_request must be an object if present"]

    received_raw = block.get("request_received_at")
    removed_raw = block.get("removed_at")
    if not isinstance(received_raw, str) or not isinstance(removed_raw, str):
        return ["takedown_request.request_received_at and .removed_at must both be ISO datetime strings"]

    try:
        received = datetime.fromisoformat(received_raw)
        removed = datetime.fromisoformat(removed_raw)
    except ValueError as exc:
        return [f"takedown_request has an unparseable ISO datetime: {exc}"]

    if (received.tzinfo is None) != (removed.tzinfo is None):
        return [
            "takedown_request.request_received_at and .removed_at must both carry a timezone offset, or "
            "both omit one -- mixing an offset-aware and a naive ISO datetime can't be compared safely"
        ]

    if removed < received:
        errors.append("takedown_request.removed_at is earlier than .request_received_at -- not possible")
    else:
        hours = (removed - received).total_seconds() / 3600
        if hours > 24:
            errors.append(
                f"takedown_request: {hours:.1f} hours elapsed between request and removal -- Điều 18 khoản 2 "
                "requires blocking/removal within 24 hours of a valid request (no later than 24 hours even "
                "for national-security violations, khoản 2)"
            )

    return errors


def validate(record: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    ad_errors, ad_notes = validate_ad(record.get("ad"))
    errors.extend(ad_errors)
    notes.extend(ad_notes)

    errors.extend(validate_ad_service_business(record.get("ad_service_business")))
    errors.extend(validate_takedown_request(record.get("takedown_request")))

    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to an ad-compliance record JSON file (see assets/ad_record_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or "ad" not in data:
        print("MALFORMED: input must be a JSON object with at least an 'ad' key", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks Điều 17 (close-button/wait-time), Điều 18 (24h takedown SLA, only if "
        "takedown_request is given), and Điều 19 (retention/reporting/notification, only if "
        "ad_service_business is given) of Nghị định 342/2025/NĐ-CP mechanically. It does NOT verify a "
        "special product category's substantive ad-content requirements (Điều 4-12), does NOT constitute "
        "legal advice, and does NOT check enforcement/penalty amounts. Get real legal/compliance review "
        "for any special-category ad before publishing.",
        file=sys.stderr,
    )

    try:
        errors, notes = validate(data)
    except RecordError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    for note in notes:
        print(note, file=sys.stderr)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: no flagged issues against Điều 17/18/19 of Nghị định 342/2025/NĐ-CP.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
