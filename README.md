# Scriptorium

Scriptorium is a system for **creating, quality-testing, security-auditing, and cataloging portable [Agent Skills](https://agentskills.io)** — the open `SKILL.md` standard that lets an agent's capabilities be packaged, shared, and run across any harness that supports the spec (~44 platforms as of mid-2026: Claude Code, Codex CLI, Kimi Code CLI, Grok Build, and others). It is not a chatbot, not a dedicated app, and not an agent harness of its own — it produces the skill *artifacts* other agents run, and never sits in the middle as an AI-calling service itself.

## Why this exists

Scriptorium's predecessor was **EduStation**, an agentic app built as "Claude Code for Vietnamese teachers." EduStation didn't fail on engineering — its core (agentic loop, tool dispatcher) had substantially landed. It stalled from **governance-before-traction**: 18 enforcement rules, a 5-tier compliance engine, and a fully vendored legal corpus, all built before a single real pilot with real teachers ever ran.

The pivot: stop building a dedicated harness — that layer is being commoditized fast across the whole industry — and build the layer nobody has actually solved yet: a disciplined pipeline for turning a real expert's tacit process into a portable, audited skill, verified across harnesses before anyone calls it "ready."

## How it works

Every skill goes through the same non-negotiable pipeline, in order: **research → elicit a real tacit process → `skill-creator` → quality evaluation (≥2 harnesses) → security audit (a separate stage) → scout/harvest existing prior art → license-compliance check → dedup/novelty check → registry**. An agent is never allowed to self-generate a skill from its own guess — real-world evaluation (SkillsBench) found self-generated skills perform "no benefit on average," while skills grounded in real elicited input average +16.2pp higher pass rates. `docs/templates/CLUSTER_SURVEY_TEMPLATE.md` is the standard tool for that elicitation step.

Two more disciplines run through every skill in this repo:

- **Grounding over confidence.** A claim without a real, citable source is a bug, not a style choice — the same reasoning `citation-management` applies to a BibTeX entry applies to `legal-citation-checker` refusing to guess a statute's in-effect status, and to `document-ai-structurer` never inventing a document's issuing date.
- **Deterministic-first.** Where a script can decide pass/fail, a script decides it — not a model's judgment call. Quality evaluation and security audit are always two separate gates, never merged into one review pass (a single-layer scanner has been shown to miss most serious attacks).

## What's in here

38 skills as of 2026-07-27: pipeline infrastructure (create/evaluate/audit/catalog/export a skill), general-purpose foundation tools (document structuring, PII masking, research discipline, translation, browser rendering, format bootstrapping), a Legal specializer network (contract review, citation/format checking, dossier tooling, disciplined legal web search), and an education audience-tier ladder (Teacher tier substantially staffed; Student tier has 1 skill plus a real research brief for what's next; University Student and a labeled Lecturer/Researcher tier don't exist yet). No skill has passed the quality-evaluation gate yet — none is "ready to use" in the strict sense defined here, even though several have already seen real use while being built. Full real status, verified against the registry (never from memory): `docs/STATUS.md`.

## Structure

- `docs/` — `MASTER_CONTEXT.md` (architecture + documentation convention), `STATUS.md` (real status), `DECISIONS_PENDING.md`, `specs/` (official specs), `templates/` (reusable operational templates), `archive/` (historical discussion/raw research).
- `skills/` — each skill is a subfolder containing a `SKILL.md` matching the agentskills.io 6-field spec (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`).
- `registry/` — the multi-axis identity backbone (domain, task-type, risk-tier, grounding, harness-compatibility). Schema: `registry/SCHEMA.md`. Data: `registry/skills.json`.
- `outside_research/` — living input gathered before a tier is built (owner-authored surveys, AI-assisted research briefs), kept verbatim, never a source of truth on its own. See `docs/MASTER_CONTEXT.md` §3-4.
- `outside_agy/` — reference material surveyed from external LegalTech skill/playbook models (Harvey AI, CoCounsel, Ironclad-inspired), used for comparison only, not copied.

## Non-negotiable principles

1. Stick to the agentskills.io open spec — never invent extra frontmatter fields.
2. Quality and security are two different gates — never merge into one review pass.
3. Never mark a skill harness-compatible based on a vendor claim — only direct verification counts.
4. Never let an agent self-generate a skill without input elicited from a real source.
5. One skill that runs well, audits clean, and gets real use beats ten skills sitting unused in the registry.

Start at [docs/README.md](docs/README.md) for the full navigation hub. Full strategic detail: `docs/specs/STRATEGY_SPEC.md`.
