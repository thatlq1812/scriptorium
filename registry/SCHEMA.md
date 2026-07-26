# Registry Schema

The registry is Scriptorium's identity backbone: every skill that goes through the bootstrap pipeline must have an entry in `registry/skills.json` before it's considered "internally released." The registry uses multi-axis tags, not a single rigid category — a skill can carry multiple tags on the same axis, and on multiple axes at once.

Decision reference: `docs/specs/STRATEGY_SPEC.md` §3 (step 9) and §4.

## Five tag axes (4 mandatory + 1 optional)

- **domain** — the industry/profession axis. Reference SkillsMP's occupation groups directly instead of inventing a taxonomy from scratch. Two special values: `meta` for skills that operate Scriptorium itself (skill-creator, quality-eval, security-audit...); `general` for pure task-type skills, equally useful across every domain (e.g. document-ai-structurer — document conversion isn't tied to any domain).
- **task-type** — the task-category axis, cutting across every domain: `research`, `document-conversion`, `drafting`, `review-qa`, `coordination`.
- **risk-tier** — inherits the spirit of EduStation's N1-N5, reapplied as output/liability risk level: `N1` (low, e.g. lookup/format conversion) up to `N5` (high, e.g. contract drafting/law review — mandatory human gate).
- **grounding** (mandatory, added 2026-07-26) — whether the skill's output must be traceable to a verifiable source, the strongest available signal against hallucination and directly tied to the citation-grounding principle in `docs/specs/STRATEGY_SPEC.md` §5.2. Exactly one value:
  - `required` — the skill is broken/dangerous without grounding; every factual claim in its output must trace to a real source (e.g. `citation-management`, `literature-review`, `dedup-novelty-check`, `license-compliance-check`, future legal statute-lookup skills).
  - `optional` — grounding improves reliability but the skill's core function doesn't inherently require an external source (e.g. `mermaid-diagram-designer` renders whatever syntax it's given, `translator-en-vi` is grounded in the input text itself by construction).
  - `not_applicable` — the skill doesn't produce factual claims at all (e.g. `skill-creator`, `python-env-bootstrap`, `security-audit`, `office-doc-creator` — pure scaffolding/formatting/infrastructure tools).
  - Adapted from a 3-axis suggestion (`outside_research/research_01_comment_01.md` §6) that also proposed "forbidden" as a grounding value; dropped here — no skill in this registry has a case where citing a source would itself be wrong, so a 3rd value would sit unused.
- **harness-compatibility** — the list of harnesses **verified to run clean, for real**, never inferred from a vendor showcase. A value is only added after direct testing (see `docs/archive/pre-spec-2026-07-26/handoff.md` point 5).

## One optional tag axis

- **object-type** (optional, added 2026-07-26) — the document/artifact type a skill operates on (e.g. `contract`, `email`, `report`, `manuscript`, `bibliography`, `dataset`, `diagram`, `spreadsheet`). Free-form vocabulary, grows organically like `domain` — no fixed enum. Left empty (`[]`) for skills that aren't tied to one artifact type (e.g. `skill-creator`, `security-audit`, `translator-en-vi` which translates any text). Exists to support filtering by "what kind of document does this act on," a dimension `domain`/`task-type` don't capture on their own (adapted from `outside_research/research_01_comment_01.md` §6).

## Required fields of an entry

| Field | Type | Note |
|---|---|---|
| `skill_id` | string | Root identifier, immutable, matches the folder name under `skills/`. |
| `version` | string (semver) | Bump when the SKILL.md content changes meaningfully. |
| `source` | object | `{ "type": "self-authored" \| "harvested", "repo_url"?: string, "commit"?: string, "adapted_from"?: { "repo_url", "path", "license", "cleared_by" } }`. If `harvested`, `repo_url` + `commit` are required. `adapted_from` is used when `type = self-authored` but a specific pattern/idea was borrowed from an outside source that already passed license-compliance-check (not a wholesale harvest) — still must pass the check before being recorded. |
| `license` | string | SPDX identifier (`MIT`, `Apache-2.0`, ...). Must pass license-compliance-check if `source.type = harvested` OR `source.adapted_from` has a value. |
| `tags.domain` | string[] | ≥1 value. |
| `tags.task_type` | string[] | ≥1 value. |
| `tags.risk_tier` | string | Exactly 1 value, N1-N5. |
| `tags.grounding` | string | Exactly 1 value: `required` \| `optional` \| `not_applicable`. Mandatory since 2026-07-26 — see "Five tag axes" above. |
| `tags.harness_compatibility` | string[] | May be empty if quality-eval hasn't run yet; never inferred. |
| `tags.object_type` | string[] | Optional, may be `[]`. Free-form document/artifact-type vocabulary — see "One optional tag axis" above. |
| `quality_score` | object \| null | Result from the quality-eval loop (pipeline step 4). `null` if it hasn't run yet. |
| `security_audit` | object | `{ "status": "pending" \| "passed" \| "failed", "date": string \| null }`. No skill is considered ready to use while `status != "passed"`. |
| `dependencies` | string[] | Scripts/tools bundled with the skill (if any). |
| `elicited_from` | string | The tacit-knowledge source elicited before the skill was created — must be non-empty, per the "no self-generated-only" principle (`docs/specs/STRATEGY_SPEC.md` §7 point 4). |
| `license_debt` | object \| null | `null` if license is fully cleared. If the skill uses a pattern/code from a source with unclear or restricted license (bootstrap phase, `docs/specs/STRATEGY_SPEC.md` §7 point 5): `{ "source": string, "reason": string, "remediation_plan": string, "acknowledged_by": "owner", "date": string }`. NEVER use this field for a source with an explicit contractual clause banning redistribution (e.g. Anthropic's docx/pdf/pptx/xlsx) — that category stays absolutely BLOCKED, not debt-eligible. A skill with `license_debt != null` may not be distributed/published outside the internal repo. |

## Dedup/novelty-check principle

Before starting skill-creator on a new candidate, query `registry/skills.json` by relevant `tags`. If an existing skill already covers ≥80% of the new candidate's scope, prefer extending/versioning that skill over creating a parallel entry.

## License debt ledger

Every skill with `license_debt != null` must appear in the table in `docs/STATUS.md` — for a full review before the system leaves the bootstrap phase (before Phase 2, the legal vertical, `docs/specs/STRATEGY_SPEC.md` §7 point 5).
