---
name: budget-expense-tracker
description: A completeness/arithmetic CHECKER, not a bookkeeping system. Validates caller-declared expense-claim records against an international expense-report field set (date/vendor/category/amount/purpose) PLUS a real Vietnamese-specific "Giấy đề nghị thanh toán" requirement international tools miss (amount stated in words, a travel-authorization reference required for công tác phí claims, invoice must bear the company's tax code); and validates budget-vs-actual variance records' arithmetic (variance = actual - budgeted, variance_pct correctly computed), requiring a variance_explanation once a line crosses a caller-declared materiality threshold. Use before submitting an expense claim for approval, or before circulating a budget-variance report, to catch missing fields or arithmetic errors. Do NOT use this to judge whether a variance is acceptable or whether spending was a good decision -- it checks structure/arithmetic only.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: business
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from a deep-research pass (references/research_11_business_admin_sop_budget/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15) covering both international and Vietnamese-language sources, per thatlq1812's explicit direction to search Vietnamese sources too, not just English. International expense-report shape (date/vendor/category/amount/purpose) corroborated across 2 sources (SAP Concur, Ramp); budget-vs-actual variance shape (budgeted/actual/variance/variance_pct + assumption/explanation notes) corroborated across 2 sources (Tipalti, AccountingDepartment.com). The genuinely differentiating finding came from the Vietnamese-language search specifically: real Vietnamese business practice (HoaTieu.vn, ThuVienPhapLuat.vn, AZTAX) requires a 'Giấy đề nghị thanh toán' to state the amount in words as well as numerals, and a công tác phí (business-travel) claim requires a prerequisite travel-authorization document (Quyết định/Công văn cử đi công tác) plus an invoice bearing the company's own tax code -- none of which the international sources mention, making this skill's grounding genuinely Vietnam-differentiated, not a generic international tool with Vietnamese labels. Companion to sop-structure-validator and meeting-action-tracker (same domain, same structural/arithmetic-validator-not-generator shape)."
  version: 0.1.0
  grounding: required
  object_type: ["expense-claim", "budget-line"]
---

# budget-expense-tracker

Validates the *structure* of an expense claim and the *arithmetic* of a budget-variance line. Does not judge spending decisions, and is not a bookkeeping or accounting system.

## Why this skill, and why this scope

`meeting-action-tracker`'s research (`references/research_07_business_administrator/research_brief.json`) identified "budget/expense-tracking templates" as part of the Business Administrator cluster's real, non-duplicated gap. A follow-up research pass (`references/research_11_business_admin_sop_budget/research_brief.json`) deliberately searched Vietnamese-language sources as well as English ones, and found a real Vietnam-specific requirement no international expense tool already covers: the amount-in-words convention and the travel-authorization prerequisite for `công tác phí` claims. This skill checks exactly those checkable structural/arithmetic facts, mirroring `meeting-action-tracker`/`sop-structure-validator`'s validator-not-generator shape.

## What this skill checks

1. **Expense claims** (`expense_claims`, each entry): a real `date`; non-empty `requester_name`/`requesting_department`/`vendor`/`business_purpose`/`currency`; `category` in `travel`/`meals`/`accommodation`/`office_supplies`/`other`; a positive `amount`; non-empty `amount_in_words` (the Vietnamese numeral-plus-words convention); `supporting_documents_count` ≥ 1 (a claim with zero attached original documents can't be processed); `invoice_has_company_tax_code` must be `true`; and, only for `category: "travel"`, a non-empty `travel_authorization_ref`.
2. **Budget lines** (`budget_lines`, each entry): non-empty `line_item` and `assumption_note`; `variance` must equal `actual_amount - budgeted_amount`; `variance_pct` must equal the correctly computed percentage (or be omitted when `budgeted_amount` is 0, since the percentage is undefined); if a top-level `materiality_threshold_pct` is given and a line's variance exceeds it, `variance_explanation` becomes required.

## Run

```bash
python scripts/validate_budget_expense.py <record.json>
```

Start from `assets/budget_expense_template.json`. At least one of `expense_claims`/`budget_lines` is required; either may be an empty list (`[]`, meaning "checked, none this period") or omitted entirely if not applicable to this run. `materiality_threshold_pct` is optional -- omit it if you don't want the `variance_explanation`-required check applied. Exit 0 = no issues, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Does not verify a receipt or invoice is genuine -- it checks that required fields are declared, not that the underlying document is real.
- Does not constitute Vietnamese Accounting Standards (VAS) legal-compliance verification -- the amount-in-words/travel-authorization/tax-code checks are grounded in real Vietnamese business-document practice found via secondary sources (HoaTieu.vn/ThuVienPhapLuat.vn/AZTAX explainer sites), not a direct read of the underlying Thông Tư/Nghị định text (flagged as an open gap in `references/research_11_business_admin_sop_budget/research_brief.json`) -- unlike `vn-ad-compliance-checker`'s primary-source-PDF-verified grounding.
- Does not decide whether a budget variance is acceptable, only whether it crossed the caller's own declared threshold and, if so, whether an explanation was provided.
- Does not do any bookkeeping, ledger reconciliation, or tax calculation -- pure structural/arithmetic checking on caller-declared records.
- Does not call any LLM/AI API -- pure stdlib checking.

## Verified

The bundled template (2 expense claims incl. 1 travel claim with authorization ref, 2 budget lines incl. 1 within threshold and 1 with an explanation) passes clean. A deliberately broken record (unparseable date, empty requester name, invalid category, negative amount, empty amount-in-words, 0 supporting documents, `invoice_has_company_tax_code: false`, a travel claim missing its authorization ref, a wrong `variance` value, and a threshold-crossing line missing its required `variance_explanation`) correctly caught all 10 issues in one run. A zero-`budgeted_amount` edge case correctly required no `variance_pct` and passed. An empty `expense_claims: []` list correctly passed (distinct from `sop-structure-validator`'s required-non-empty lists -- an expense/budget run can legitimately have nothing to report). A record with neither `expense_claims` nor `budget_lines` and malformed JSON both correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- The 3 Vietnam-specific checks (amount-in-words, travel-authorization-prerequisite, invoice-tax-code) are grounded in secondary sources, not a direct primary-legal-text read -- a future version should verify against the actual VAS Thông Tư/Nghị định text before this skill's grounding is upgraded to the same confidence level as `vn-ad-compliance-checker`.
- Does not check that `amount_in_words` actually matches the numeral `amount` (e.g. catching "một triệu đồng" declared for an `amount` of 2,000,000) -- only that the field is non-empty. Reliable numeral-to-Vietnamese-words cross-validation would need a real number-to-Vietnamese-text converter, not yet built.
- `materiality_threshold_pct` is a single flat percentage applied to every budget line -- does not support per-category or per-line-item differentiated thresholds.
- Only verified against hand-authored fixtures this session, not yet exercised against a real organization's actual expense/budget records.
