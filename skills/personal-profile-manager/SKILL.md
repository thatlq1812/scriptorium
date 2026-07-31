---
name: personal-profile-manager
description: Local-only personal profile store and behavior-adaptation proposal generator for non-tech users. `init_profile.py` scaffolds a local `personal/profile.json` (identity, organization, tax ID, contact, plus an optional org_profile issuing-organization/letterhead section) from a bundled template; `validate_profile.py` checks required sections/fields, including org_profile's cross-field checks (signatory-to-department reference integrity, no duplicate ids); `autofill.py` resolves a caller-declared field_map against the profile, refusing to invent unresolved values; `propose_style_update.py` turns a feedback log into a PROPOSED instruction-update block, never auto-applied. Use when a user wants to stop re-typing identity/org details into every form/contract, wants tone/register to adapt to feedback, or needs an org's letterhead identity stored separately from personal contact details. Do NOT auto-apply a style change without human review, and do NOT use as a secrets store — plain local JSON only.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse, pathlib, re) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-08-01).
metadata:
  domain: general
  task_type: coordination
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner direction 2026-07-29 (docs/ROADMAP.md 'New planned roadmap items', UPGRADE_PLAN_20260729.md Item 1), grounded in the owner's real non-tech-user pilot need (repeating identity/org details across forms, dossiers, contracts, lesson plans) rather than an invented feature. Field schema (identity/organization/contact) cross-checked against what legal-form-filler/office-doc-creator/lesson-plan-builder's own input schemas actually ask for, not designed from scratch. Local-config-file convention (single JSON, separate from credentials) lightly grounded against AWS CLI's config/credentials split and cookiecutter's variables-file pattern (public convention survey, not a cloned dependency -- deliberately kept stdlib-only rather than adopting a templating engine). v0.2.0's org_profile section ported (schema shape and validation logic, rewritten clean, not copied) from the owner's own real prior production system, D:/elix/archive/platform_archive/modules/document/v6/co_quan_profile/schemas.py (CoQuanProfileCreate/Update, DonViEntry, ChucDanhEntry) -- a real 'issuing organization' profile schema used to render Vietnamese administrative documents under NĐ 30/2020/NĐ-CP, including its quyền-hạn signing-authority prefix table cross-checked against D:/elix/archive/platform_archive/modules/document/v6/config/law_constants.py's QUYEN_HAN_PREFIXES."
  version: 0.2.0
  changelog_0_2_0: "Added an OPTIONAL org_profile top-level section to the profile schema -- the profile-as-ISSUING-ORGANIZATION identity (org name, parent org, abbreviation, locality, logo, address/contact, a department list, a signatory-title list) for letterhead-style document generation, distinct from the existing individual-person organization/contact fields. init_profile.py: new --with-org-profile flag merges the bundled assets/org_profile_template.json's org_profile section into the scaffold (whole-file overwrite semantics unchanged, same --force protection). validate_profile.py: new org_profile validation (only runs when the section is present) -- required name/abbreviation/locality, abbreviation format check (2-16 upper-case Latin letters + Đ), and 2 cross-field integrity checks ported from the source schema: every signatory's department_id (if set) must resolve to a real entry in org_profile.departments (dangling-reference check), and no duplicate department or signatory ids/codes. default_signing_authority is REQUIRED per signatory entry (never silently defaulted to 'none' the way the source schema does) -- this skill's existing 'never fabricate a value' discipline applied to the ported schema. Zero new dependencies (json/re/pathlib/argparse, all stdlib already in use), zero network, zero subprocess/eval."
  changelog_0_1_1: "Doc-only: documented and verified real chaining into legal-form-filler's fill_form.py -- autofill.py's output already matches that skill's form_data.json shape with zero conversion needed (docs/DECISIONS_PENDING.md resolved item 9). No script change."
  grounding: not_applicable
  object_type: ["profile", "form", "organization", "letterhead"]
---

# personal-profile-manager

Two independent halves: a local personal-data profile store with a generic auto-fill engine, and a writing-style feedback-to-proposal pipeline. Both are local-only, no network calls, no AI backend.

## Why this skill, and why this scope

A recurring real cost for non-tech users (teachers, lawyers, other professionals) working with Scriptorium-produced skills is re-typing the same identity/organization/contact details into every form, dossier, contract, or lesson plan a downstream skill asks for. Rather than have each downstream skill invent its own profile-storage convention, this is one shared local store plus a generic field-mapping engine -- same "generic engine, caller supplies the specifics" shape as `legal-form-filler` (which never hardcodes a checklist/template, only validates against one the caller supplies).

The behavior-adaptation half is a separate, smaller capability bundled here because it's the same underlying idea (adapting to *this user specifically*) but is NOT the same mechanism -- it never writes to system instructions directly. A script proposing a change to CLAUDE.md/AGENTS.md and applying it silently would be the same ungated-generator failure mode the v0.2.0 hardening round found and fixed in `hypothesis-generation`/`peer-review` (STATUS.md's hardening-round notes) -- so this only ever proposes, printed for a human/agent to review and insert manually.

## Run

### Profile store

```bash
python scripts/init_profile.py personal/profile.json
python scripts/validate_profile.py personal/profile.json
```

`init_profile.py` scaffolds from `assets/profile_template.json`, refuses to overwrite an existing file without `--force`. `validate_profile.py` checks the 3 required sections (`identity`, `organization`, `contact`) each have their minimum required field non-empty -- exit 0 = valid, 1 = named violations, 2 = malformed/missing file.

Recommended location: `personal/profile.json` at the repo root -- `.gitignore` already excludes `/personal` by default (see "Privacy" below).

### org_profile -- issuing-organization / letterhead identity (optional, v0.2.0)

`identity`/`organization`/`contact` describe the profile's owner as an individual person (their own name, their own employer, their own contact details). `org_profile` is a separate, OPTIONAL top-level section for when the profile needs to represent an ISSUING ORGANIZATION -- the entity that appears on a letterhead or signs a document in its own institutional capacity, e.g. a school, a law office, a government unit. It lives in the same `profile.json` (not a separate file) because it is still a per-user local profile store, and a single non-tech user (e.g. a Hiệu trưởng/school principal) is exactly the case that needs both halves at once: their own personal identity AND the organization they issue documents on behalf of.

```bash
python scripts/init_profile.py personal/profile.json --with-org-profile
python scripts/validate_profile.py personal/profile.json
```

`--with-org-profile` merges `assets/org_profile_template.json`'s `org_profile` section into the scaffold at creation time (same whole-file `--force` overwrite protection as the base scaffold -- this is not a partial merge into an existing file). Schema:

```json
{
  "org_profile": {
    "name": "Trường THPT Chu Văn An",
    "parent_org_name": "Sở Giáo dục và Đào tạo Hà Nội",
    "abbreviation": "THPTCVA",
    "locality": "Hà Nội",
    "logo": null,
    "address": "10 Thụy Khuê, Tây Hồ, Hà Nội",
    "contact_phone": "+84243456789",
    "contact_email": "vanphong@thptcva.edu.vn",
    "departments": [
      { "id": "van_phong", "name": "Văn phòng", "abbreviation": "VP" }
    ],
    "signatory_roles": [
      {
        "id": "hieu_truong", "code": "hieu_truong",
        "label_full": "Hiệu trưởng", "label_short": "HT",
        "default_signing_authority": "none", "department_id": null
      }
    ]
  }
}
```

- `name`, `abbreviation`, `locality` are required. `abbreviation` (org- and department-level) must be 2-16 upper-case Latin letters plus the single Vietnamese letter "Đ" (`^[A-ZĐ]{2,16}$`) -- ported from the real NĐ 30/2020 viết-tắt convention this section is grounded in (mixed-case/accented forms break Số/ký hiệu rendering in the source system).
- `departments` (đơn vị / phòng ban): each entry needs a unique `id`, `name`, `abbreviation`. Duplicate `id`s across the list are rejected.
- `signatory_roles` (chức danh): each entry needs a unique `id`, a `code` (snake_case, 2-32 chars), `label_full`, `label_short`, and a REQUIRED `default_signing_authority` -- one of `"none"`, `"TM."` (thay mặt/on behalf of), `"KT."` (ký thay/signed for), `"TL."` (thừa lệnh/by order of), `"TUQ."` (thừa uỷ quyền/by authorization), `"Q."` (quyền/acting) -- the 5 real quyền-hạn prefixes NĐ 30/2020 Mục IV.7 recognises, rendered literally at ô 7a of a Vietnamese administrative document. This field is deliberately NOT defaulted to `"none"` the way the source production schema does -- following this skill's own "never silently fabricate a value" discipline, every signatory entry must state its authority explicitly. An optional `department_id`, if set, must reference an `id` that actually exists in `departments` (a dangling-reference check) -- e.g. "Chánh Văn phòng" pinned to the "Văn phòng" department.
- Duplicate `id`s and duplicate `code`s within `signatory_roles` are both rejected.

`validate_profile.py` only runs the `org_profile` checks when the section is present -- a profile without it validates exactly as before (fully backward compatible with pre-0.2.0 profiles).

**Chains into `light-logo-arranger` and `latex-project-bootstrap`'s vnnd30 mode (documented intent, not wired -- see below)**: `org_profile.logo` is a path/URL a caller could feed as `light-logo-arranger/scripts/compute_anchor.py`'s logo dimensions/placement input for letterhead layout; `org_profile.name`/`locality`/`departments`/`signatory_roles[].label_full`/`default_signing_authority` map naturally onto `latex-project-bootstrap`'s vnnd30 `render_nd30_document.py` content JSON (`ten_co_quan`, `dia_danh_ngay`, `nguoi_ky.quyen_han`/`chuc_vu_ho_ten_nguoi_ky`) for signature-block rendering. Neither downstream skill has been wired or field-mapped to this section yet -- that integration work is out of scope here (other parallel work this session touches those skills) and belongs in each target skill's own `SKILL.md` once done, per this project's composability-discipline convention.

### Auto-fill

```bash
python scripts/autofill.py personal/profile.json field_map.json -o filled.json
```

`field_map.json` is always caller-supplied (start from `assets/field_map_template.json`) -- a flat `{ "target_field_name": "section.field" }` mapping from a downstream skill's own field names to a dotted path in `profile.json`. A path that doesn't resolve (typo, or the profile genuinely has no such field) is reported by name on stderr and left OUT of the output, never invented -- exit 0 = every mapped field resolved, 1 = at least one unresolved (still writes what did resolve if `-o` given; the caller must check the unresolved list before trusting the output), 2 = malformed input.

**Chains into `legal-form-filler` for real** (2026-07-29, `docs/DECISIONS_PENDING.md` resolved item 9): `autofill.py -o filled.json`'s output is already the exact flat `{field_name: value}` shape `legal-form-filler/scripts/fill_form.py` expects as its `form_data.json` argument -- no conversion script needed, pipe the output straight in:

```bash
python scripts/autofill.py personal/profile.json field_map.json -o filled.json
python skills/legal-form-filler/scripts/fill_form.py <form_template.json> filled.json
```

`fill_form.py` already tolerates extra keys in `filled.json` that a specific form doesn't declare (reports them as unmatched, doesn't fail) -- so one `profile.json`/`field_map.json` pair covering many possible fields can feed different forms without re-running `autofill.py` per form. Field VALUE format (e.g. date format) is not cross-checked between the two skills -- `personal-profile-manager` stores whatever format the profile was written in, `fill_form.py` only checks presence, not format; a real form needing a specific date format still needs that normalized by the caller.

### Behavior/style adaptation proposal

```bash
python scripts/propose_style_update.py feedback_log.json -o proposal.md
```

`feedback_log.json` (start from `assets/feedback_log_template.json`) is a list of `{date, category, feedback_text}` entries. Groups by category and prints (and optionally writes) a Markdown block explicitly marked as a **proposal**, never auto-applied to any file. Exit 0 = proposal generated, 1 = no valid entries, 2 = malformed input.

## What this skill does NOT do

- Does not auto-apply anything to `CLAUDE.md`/`AGENTS.md`/a harness system prompt -- `propose_style_update.py` only ever prints/writes a standalone proposal file for a human or the calling agent to review and manually insert.
- Does not do fuzzy/semantic field matching in `autofill.py` -- a `field_map` entry naming a path that doesn't exist in the profile is reported unresolved, same "never guess a match" discipline as `legal-form-filler`.
- Is not a secrets/credentials store -- `profile.json` is a plain local JSON file, appropriate for identity/org/contact metadata, not passwords/API keys/private keys.
- Does not decide WHICH downstream skill's fields map to which profile fields -- that mapping is always caller-declared via `field_map.json`, never hard-coded for a specific target skill.
- Does not sync/back up the profile anywhere -- purely local; a user wanting version history must opt in themselves (see "Privacy" below).
- `org_profile` does not render anything (no letterhead PDF/DOCX, no logo placement) -- it is data storage + structural/cross-field validation only. Actually placing a logo is `light-logo-arranger`'s job; actually rendering a signature block onto a document is `latex-project-bootstrap`'s vnnd30 mode's job. Neither is wired to this section yet (see "Chains into" note above).
- Does not validate `org_profile.logo` as a real, existing file/URL -- it is stored and format-checked as a string (or left `null`), never dereferenced or fetched (no network calls, ever).

## Privacy

`.gitignore` at the repo root excludes `/personal` by default -- a `profile.json` under `personal/` never gets committed even in a repo the user later makes public. A `personal/README.md` (create alongside the first real profile) should explain this and note that users on a genuinely private repository can remove the ignore rule if they want their profile under version control.

## Verified

`init_profile.py`: fresh scaffold from template succeeded; re-running without `--force` against an existing file correctly refused (exit 1); `--force` correctly overwrote. `validate_profile.py`: the bundled template passed clean; a profile missing the `contact` section entirely was correctly refused, naming the missing section; a profile with `identity.full_name` present but empty-string was correctly refused, naming the exact field; malformed JSON correctly refused (exit 2). `autofill.py`: the bundled `field_map_template.json` against the bundled `profile_template.json` resolved all 8 fields correctly (verified value-by-value); a field_map with one path pointing at a nonexistent profile key ("identity.middle_name") was correctly reported unresolved while the other 7 still resolved and were written to output; a field_map path pointing at a nested object instead of a leaf value (e.g. `"identity"` alone) was correctly treated as unresolved, not silently serialized as a JSON object. `propose_style_update.py`: the bundled `feedback_log_template.json` (2 entries, 2 categories) produced a correctly-grouped Markdown proposal with the explicit non-auto-apply warning banner; an entries list missing a required field on one entry was correctly refused (exit 2, naming the entry index) rather than silently skipping just that entry; an empty `entries: []` list was correctly refused (exit 2). **`legal-form-filler` chaining (2026-07-29)**: `autofill.py`'s real output (from the bundled profile/field_map) piped directly into `legal-form-filler/scripts/fill_form.py` with zero conversion -- correctly identified the 6 extra fields the form didn't declare as unmatched (not an error) and correctly reported all required fields filled, exit 0. First real end-to-end downstream usage of this skill's output by another skill.

**`org_profile` (v0.2.0, 2026-08-01)**: `init_profile.py --with-org-profile` scaffolded a real profile from the bundled `org_profile_template.json` (2 departments -- Văn phòng/VP, Tổ chuyên môn/TCM -- and 3 signatory roles -- Hiệu trưởng, Phó Hiệu trưởng, Chánh Văn phòng with a real `department_id` reference into "Văn phòng") and `validate_profile.py` passed it clean (exit 0). Re-running `init_profile.py` without `--force` against the same path correctly refused (exit 1, unchanged base behavior); `--force --with-org-profile` correctly overwrote. Base scaffold without `--with-org-profile` still validates clean with no `org_profile` key present, confirming backward compatibility with pre-0.2.0 profiles. 3 deliberately broken `org_profile` cases, each correctly caught by `validate_profile.py` (exit 1, exact violation named):
- (a) a signatory (`chanh_van_phong`) with `department_id: "phong_khong_ton_tai"` (a department id not present in `departments`) -- refused: `org_profile.signatory_roles[2] (id='chanh_van_phong'): department_id 'phong_khong_ton_tai' does not reference an existing entry in org_profile.departments`.
- (b) both departments given `id: "van_phong"` -- refused: `org_profile.departments: duplicate department id(s): ['van_phong']`.
- (c) the `pho_hieu_truong` signatory entry with `default_signing_authority` omitted entirely -- refused: `org_profile.signatory_roles[1]: required field 'default_signing_authority' is missing -- must be explicitly one of ['KT.', 'Q.', 'TL.', 'TM.', 'TUQ.', 'none']`.

## Known limitations (v0.2.0)

- `validate_profile.py`'s required-field check for `identity`/`organization`/`contact` is deliberately minimal (one anchor field per section, e.g. `identity.full_name`) -- it does not enforce every field in the template exists or is well-formed (no date-format or tax-ID-format validation). `org_profile`'s checks are stricter (full required-field + cross-field-reference validation) since it was ported from a real production schema that already enforced that rigor; the individual-person sections were not retroactively tightened to match -- that stays a future-version candidate if real use shows the need.
- `autofill.py` only resolves scalar (string/number/bool) leaf values -- a `field_map` path pointing at a nested object or list is treated as unresolved rather than serialized, since a downstream form field is assumed to want a single value, not a structure. This means `autofill.py` cannot currently resolve `org_profile.departments`/`org_profile.signatory_roles` as a whole (they're lists) -- a caller needing a specific signatory's `label_full` or `default_signing_authority` must address it by a dotted path into a specific array index (e.g. `org_profile.signatory_roles.0.label_full` is NOT supported -- `_resolve_path` only walks dict keys, not list indices). Not fixed in this version; documented as a real gap for whoever wires the `light-logo-arranger`/`latex-project-bootstrap` chain.
- Verified chained into `legal-form-filler` for real (2026-07-29, see "Verified" above) -- other candidate downstream skills (`lesson-plan-builder`, `project-workspace-initializer`'s `PROJECT.md`, and `org_profile`'s own `light-logo-arranger`/`latex-project-bootstrap` chains) haven't been wired/verified yet.
- No profile-migration/versioning story yet if the schema in `assets/profile_template.json`/`assets/org_profile_template.json` changes later -- an existing `personal/profile.json` from an older template version isn't automatically upgraded.
- `org_profile.chu_ky_so_provider`/digital-signature-provider config from the source production schema was deliberately NOT ported -- out of scope for a local profile store (that's live CA/PKI integration state, not identity/letterhead data), and would be the kind of external-service integration principle 8 in `CLAUDE.md` rules out for Scriptorium anyway.
