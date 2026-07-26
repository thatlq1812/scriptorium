# Scriptorium

Start at [docs/README.md](docs/README.md) — navigation hub into the architecture, real status, and strategy spec.

## Structure

- `docs/` — `MASTER_CONTEXT.md` (architecture + documentation convention), `STATUS.md` (real status), `DECISIONS_PENDING.md`, `specs/` (official specs), `archive/` (historical discussion/raw research).
- `skills/` — each skill is a subfolder containing a `SKILL.md` matching the agentskills.io 6-field spec (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`).
- `registry/` — the multi-axis identity backbone (domain, task-type, risk-tier, harness-compatibility). Schema: `registry/SCHEMA.md`. Data: `registry/skills.json`.

## Bootstrap pipeline (in progress)

Research → Elicit tacit process → **skill-creator** → Quality evaluation (≥2 harnesses) → Security audit (separate stage) → Skill scout/harvester → License-compliance check → Dedup/novelty-check → Registry.

Order is not negotiable. Never let an agent self-generate a skill without input elicited from a real source — SkillsBench measured self-generated skills as "no benefit on average."

## Non-negotiable principles

1. Stick to the agentskills.io open spec — never invent extra frontmatter fields.
2. Quality and security are two different gates — never merge into one review pass.
3. Never mark a skill harness-compatible based on a vendor claim — only direct verification counts.
4. One skill that runs well, audits clean, and gets real use beats ten skills sitting unused in the registry.

Full detail: `docs/specs/STRATEGY_SPEC.md`.
