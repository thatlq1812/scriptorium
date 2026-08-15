#!/usr/bin/env python3
"""Check caller-declared expense-claim and budget-vs-actual records against
2 real conventions: an international expense-report field set PLUS a real
Vietnamese-specific "Giay de nghi thanh toan" (payment-request) requirement
international sources don't cover (amount stated in words, a travel-
authorization prerequisite for cong tac phi claims, invoice tax-code
presence); and a standard budget-vs-actual variance-arithmetic convention.
Stdlib only (json, argparse, datetime), local, deterministic -- no
AI/network call of any kind.

SCOPE LIMIT (read before use): this checks STRUCTURE and ARITHMETIC only.
It does not verify a receipt/invoice is genuine, does not verify VAS
(Vietnamese Accounting Standards) legal compliance beyond the 2 checkable
conventions named above (grounded via secondary sources, not a primary
legal-text read -- see references/research_11_business_admin_sop_budget/
research_brief.json's own gaps note), and does not decide whether a
variance is acceptable -- only whether it was explained per the caller's
own declared materiality threshold.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_budget_expense.py <record.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

EXPENSE_CATEGORIES = {"travel", "meals", "accommodation", "office_supplies", "other"}


class RecordError(Exception):
    pass


def parse_iso_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be an ISO date string 'YYYY-MM-DD', got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordError(f"{field} is not a real calendar date: {value!r} ({exc})") from exc


def require_nonempty_text(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required and must be non-empty text")


def validate_expense_claims(claims: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(claims, list):
        return ["expense_claims must be a list"]

    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            errors.append(f"expense_claims[{i}] must be an object")
            continue
        p = f"expense_claims[{i}]"

        try:
            parse_iso_date(c.get("date"), f"{p}.date")
        except RecordError as exc:
            errors.append(str(exc))

        require_nonempty_text(c.get("requester_name"), f"{p}.requester_name", errors)
        require_nonempty_text(c.get("requesting_department"), f"{p}.requesting_department", errors)
        require_nonempty_text(c.get("vendor"), f"{p}.vendor", errors)
        require_nonempty_text(c.get("business_purpose"), f"{p}.business_purpose", errors)
        require_nonempty_text(c.get("currency"), f"{p}.currency", errors)

        category = c.get("category")
        if category not in EXPENSE_CATEGORIES:
            errors.append(f"{p}.category must be one of {sorted(EXPENSE_CATEGORIES)}, got {category!r}")

        amount = c.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
            errors.append(f"{p}.amount must be a positive number, got {amount!r}")

        # Vietnamese "Giay de nghi thanh toan" convention: amount must be
        # declared in words, not just numerals (references/research_11...).
        require_nonempty_text(c.get("amount_in_words"), f"{p}.amount_in_words", errors)

        docs_count = c.get("supporting_documents_count")
        if not isinstance(docs_count, int) or isinstance(docs_count, bool) or docs_count < 0:
            errors.append(f"{p}.supporting_documents_count must be a non-negative integer, got {docs_count!r}")
        elif docs_count == 0:
            errors.append(f"{p}.supporting_documents_count is 0 -- a claim with zero attached original documents (chung tu goc) cannot be processed")

        if c.get("invoice_has_company_tax_code") is not True:
            errors.append(
                f"{p}.invoice_has_company_tax_code must be true -- a claim's invoice must bear the "
                "company's own name and tax code (ma so thue) to be treated as a deductible business cost"
            )

        if category == "travel":
            require_nonempty_text(
                c.get("travel_authorization_ref"), f"{p}.travel_authorization_ref "
                "(required for travel/cong tac phi claims -- a prerequisite Quyet dinh/Cong van cu di cong tac "
                "reference, filed before the claim)", errors
            )

    return errors


def validate_budget_lines(lines: object, threshold_pct: float | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(lines, list):
        return ["budget_lines must be a list"]

    for i, ln in enumerate(lines):
        if not isinstance(ln, dict):
            errors.append(f"budget_lines[{i}] must be an object")
            continue
        p = f"budget_lines[{i}]"

        require_nonempty_text(ln.get("line_item"), f"{p}.line_item", errors)
        require_nonempty_text(ln.get("assumption_note"), f"{p}.assumption_note", errors)

        budgeted = ln.get("budgeted_amount")
        actual = ln.get("actual_amount")
        variance = ln.get("variance")
        variance_pct = ln.get("variance_pct")

        for field, val in (("budgeted_amount", budgeted), ("actual_amount", actual)):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                errors.append(f"{p}.{field} must be a number, got {val!r}")

        if not (isinstance(budgeted, (int, float)) and not isinstance(budgeted, bool)) or \
           not (isinstance(actual, (int, float)) and not isinstance(actual, bool)):
            continue  # can't compute derived checks without valid numbers

        expected_variance = actual - budgeted
        if not isinstance(variance, (int, float)) or isinstance(variance, bool):
            errors.append(f"{p}.variance must be a number, got {variance!r}")
        elif abs(variance - expected_variance) > 1e-6:
            errors.append(f"{p}.variance is {variance!r} but actual_amount - budgeted_amount = {expected_variance!r}")

        if budgeted == 0:
            if variance_pct is not None:
                errors.append(f"{p}.variance_pct should be null/omitted when budgeted_amount is 0 (percentage is undefined)")
            pct_for_threshold = None
        else:
            expected_pct = (expected_variance / budgeted) * 100
            if not isinstance(variance_pct, (int, float)) or isinstance(variance_pct, bool):
                errors.append(f"{p}.variance_pct must be a number, got {variance_pct!r}")
                pct_for_threshold = None
            elif abs(variance_pct - expected_pct) > 0.01:
                errors.append(f"{p}.variance_pct is {variance_pct!r} but the computed value is {expected_pct:.2f}")
                pct_for_threshold = variance_pct
            else:
                pct_for_threshold = variance_pct

        if threshold_pct is not None and pct_for_threshold is not None and abs(pct_for_threshold) > threshold_pct:
            explanation = ln.get("variance_explanation")
            if not isinstance(explanation, str) or not explanation.strip():
                errors.append(
                    f"{p}: variance {pct_for_threshold:.2f}% exceeds the declared materiality threshold "
                    f"({threshold_pct}%) -- variance_explanation is required once a line crosses the "
                    "materiality threshold, per standard budget-variance-review practice"
                )

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    threshold = record.get("materiality_threshold_pct")
    if threshold is not None and (not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or threshold < 0):
        errors.append(f"materiality_threshold_pct must be a non-negative number or omitted, got {threshold!r}")
        threshold = None

    if "expense_claims" in record:
        errors.extend(validate_expense_claims(record.get("expense_claims")))
    if "budget_lines" in record:
        errors.extend(validate_budget_lines(record.get("budget_lines"), threshold))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a budget/expense record JSON file (see assets/budget_expense_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or not ("expense_claims" in data or "budget_lines" in data):
        print("MALFORMED: input must be a JSON object with at least one of 'expense_claims' or 'budget_lines'", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks expense-claim STRUCTURE (international field set + the Vietnamese amount-in-words/"
        "travel-authorization/invoice-tax-code convention) and budget-variance ARITHMETIC only -- it does not "
        "verify receipts are genuine, does not constitute VAS legal-compliance verification, and does not "
        "judge whether a variance is acceptable, only whether it was explained.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    n_claims = len(data.get("expense_claims", []) or [])
    n_lines = len(data.get("budget_lines", []) or [])
    print(f"OK: {n_claims} expense claim(s), {n_lines} budget line(s), no issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
