---
name: academic-grant-proposal
description: Validates that a grant-proposal JSON record has all 5 required sections (specific aims, significance, approach/methodology, timeline, budget justification) present and non-empty, and that every budget-justification narrative references a real, caller-declared budget line item (and every declared budget line item is justified) -- catching a missing section or a budget justification that doesn't tie back to the actual budget request before submission. Use after drafting a grant proposal to check structural completeness and proposal-to-budget consistency. Do NOT use this to judge scientific/research merit, to check funder-specific formatting (page limits, font, margins), or to guarantee compliance with a specific funder's submission portal -- it is a structural/consistency validator only.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean on Claude Code (2026-07-29); see "Verified" section below for exact test-case detail.
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "The 5-section structural core (specific_aims, significance, approach, timeline, budget_justification) is grounded in two real, publicly documented funder guides: NIH's SF424 (R&R) Application Guide, which requires Specific Aims, Significance, and Approach as separate required attachments for an R01-type research narrative (https://grants.nih.gov/grants/how-to-apply-application-guide.html), and NSF's Proposal & Award Policies & Procedures Guide (PAPPG), which requires a Project Description covering the proposed work's goals/approach and a mandatory, itemized Budget Justification tied to the Budget (https://www.nsf.gov/policies/pappg). The budget-justification-must-trace-to-a-real-line-item check applies the same grounding discipline this repo's legal-research-brief already applies to factual/statutory claims (every assertion must cite a real, caller-declared source) -- here applied to grant structure instead of legal fact."
  version: 0.1.0
  grounding: required
  object_type: ["grant-proposal", "budget"]
---

# academic-grant-proposal

Validates that a grant-proposal JSON record is structurally complete and internally consistent with its declared budget. Never drafts, scores, or judges the scientific merit of a proposal -- this is a structural/consistency checker, not a writing tool or a reviewer.

## Why this skill, and why this scope

Checked against `citation-management` and `peer-review` (this repo's existing general-tier research cluster) before building: neither covers this. `citation-management`'s own "What this skill does NOT do" section is explicit that it "doesn't validate citation STYLE consistency across a whole bibliography" and it only resolves DOI/PMID/arXiv identifiers into BibTeX -- it has no notion of a grant proposal's section structure or a budget table at all. `peer-review` validates a manuscript-review workflow's intake/confidentiality gate and a claim-evidence matrix for an already-authored manuscript being reviewed by someone else -- it has no budget concept and doesn't apply to a proposal being drafted by its own author. This is a real, unaddressed gap: a grant proposal is rejected as often for a missing/boilerplate required section or an unjustified budget line as for weak science, and both are mechanically checkable before a human reviewer ever reads it.

## The 5 required sections this skill encodes

Grounded in NIH's SF424 (R&R) Application Guide and NSF's PAPPG (see `metadata.elicited_from`):

| Section | Requirement |
| --- | --- |
| `specific_aims` | Non-empty narrative -- what the project will accomplish |
| `significance` | Non-empty narrative -- why the problem matters, what gap it fills |
| `approach` | Non-empty narrative -- methodology/how the aims will be achieved |
| `timeline` | Non-empty list of `{milestone, period}` objects |
| `budget_justification` | Non-empty list of `{line_item_id, narrative}` objects, each `line_item_id` must exist in the declared budget, and every declared budget line item must have at least one justification entry |

## Run

```bash
python scripts/validate_grant_proposal.py <budget.json> <proposal.json> [--render proposal.md]
```

Start from `assets/budget_template.json` (declare every budget line item: `id`, `category`, positive `amount`) and `assets/proposal_template.json`. Exit 0 = all 5 sections present/non-empty and budget justification is fully consistent with the declared budget (every justification references a real line item, every line item is justified), 1 = errors found (each naming the exact field/index and reason), 2 = malformed input. `--render` only writes when validation passes, and refuses to overwrite an existing file unless `--force` is passed.

## What this skill does NOT do

- Doesn't judge scientific/research merit, novelty, or feasibility -- that is a human reviewer's job, not a mechanical check.
- Doesn't check funder-specific formatting rules (page limits, font size, margins, required forms/attachments beyond the 5 sections encoded here) -- funder submission portals (NIH eRA Commons, NSF Research.gov) enforce their own rules; this skill checks structural completeness and budget consistency only, a subset any funder would additionally require.
- Doesn't verify that a budget `amount` is reasonable, within a funder's cost cap, or correctly categorized per that funder's specific budget category taxonomy -- only that amounts are positive numbers and every line item is both declared and justified.
- Doesn't call any LLM/AI API -- pure stdlib structural/reference validation.
- Doesn't check citation formatting inside the proposal narrative -- see `manuscript-journal-formatter` for that (a distinct, unrelated document type).

## Verified

Ran for real (2026-07-29, Python 3.12.13, this machine's system interpreter -- stdlib only, no venv needed):

1. **Valid case**: 3-item budget (`personnel-pi`, `equipment-microscope`, `travel-conference`) with a proposal justifying all 3 and all 5 sections filled -- exit 0, `--render` produced a correct Markdown file with per-item dollar amounts and narratives inlined.
2. **Broken -- empty section + fabricated budget reference**: `approach` set to `""` and one `budget_justification` entry referencing `equipment-electron-microscope` (not in the budget) -- correctly caught both as separate errors, plus flagged the 2 real budget items left unjustified by the truncated justification list (3 errors total), exit 1.
3. **Malformed input**: `budget.json` with a trailing comma (invalid JSON) -- correctly refused with `MALFORMED: cannot read budget file: Expecting value: line 4 column 3 (char 97)`, exit 2.
4. **Unjustified budget line items**: valid 3-item budget, proposal justifies only 1 of the 3 -- correctly caught the 2 unjustified items (`equipment-microscope`, `travel-conference`) by exact id, exit 1.

## Known limitations (v0.1.0)

- Consistency checking is purely by line-item **id**, not by amount or content -- a justification narrative that cites a real `line_item_id` but describes an unrelated cost will still pass. A human must still read the narrative against the category to confirm it actually makes sense.
- No page-length, word-count, or reading-level check on any narrative field -- only non-emptiness is enforced. A one-word "approach" value passes structurally even though no real funder would accept it; this skill checks presence, not adequacy.
- No cross-check between `timeline` periods and `budget_justification` (e.g. personnel costs concentrated in a period with no corresponding milestone) -- each section is validated independently.
- Currency/unit is not modeled -- `amount` is treated as a bare positive number; multi-currency budgets are not distinguished or converted.
