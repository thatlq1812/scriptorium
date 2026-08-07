# Scriptorium

Scriptorium is a system for **creating, quality-testing, security-auditing, and cataloging portable [Agent Skills](https://agentskills.io)** — the open `SKILL.md` standard that lets an agent's capabilities be packaged and run across any harness that supports the spec (~44 platforms as of mid-2026: Claude Code, Codex CLI, Kimi Code CLI, Grok Build, and others). It is not a chatbot, not a dedicated app, and not an agent harness of its own — it produces the skill *artifacts* other agents run, and never sits in the middle as an AI-calling service itself. The registry is built to that open format for cross-harness compatibility, but its content is proprietary — distributed commercially, not published to the public agentskills.io ecosystem.

## Why this exists

Scriptorium was born from a fundamental strategic realization: dedicated agent harnesses, custom desktop apps, and standalone chatbots are being commoditized fast across the AI industry. Building complex application governance and custom UI harnesses before establishing a disciplined pipeline for portable skill artifacts creates governance-before-traction friction.

The pivot: stop building a dedicated harness — that layer is being commoditized fast across the whole industry — and build the layer nobody has actually solved yet: a disciplined pipeline for turning a real expert's tacit process into a portable, audited skill, verified across harnesses before anyone calls it "ready."

## How it works

Every skill goes through the same non-negotiable pipeline, in order: **research → elicit a real tacit process → `skill-creator` → quality evaluation (≥2 harnesses) → security audit (a separate stage) → scout/harvest existing prior art → license-compliance check → dedup/novelty check → registry**. An agent is never allowed to self-generate a skill from its own guess — real-world evaluation (SkillsBench) found self-generated skills perform "no benefit on average," while skills grounded in real elicited input average +16.2pp higher pass rates. `docs/templates/CLUSTER_SURVEY_TEMPLATE.md` is the standard tool for that elicitation step.

Two more disciplines run through every skill in this repo:

- **Grounding over confidence.** A claim without a real, citable source is a bug, not a style choice — the same reasoning `citation-management` applies to a BibTeX entry applies to `legal-citation-checker` refusing to guess a statute's in-effect status, and to `document-ai-structurer` never inventing a document's issuing date.
- **Deterministic-first.** Where a script can decide pass/fail, a script decides it — not a model's judgment call. Quality evaluation and security audit are always two separate gates, never merged into one review pass (a single-layer scanner has been shown to miss most serious attacks).

## What's in here

73 skills as of 2026-08-08: pipeline infrastructure (create/evaluate/audit/catalog/export a skill, now including a "Document Distillation Mode" for turning a book/manual into an on-demand-reference skill, plus `scriptorium-updater` for keeping a tester's local skill copies synced against this repo without re-exporting a bundle each time), general-purpose foundation tools (document structuring, PII masking, research discipline, translation, browser rendering, format bootstrapping, personal-profile/workspace scaffolding + a personal color-palette/style-sample library, a deterministic Light Design cluster for signage/logos, a real HTML/CSS+headless-browser `html-poster-composer` for posters/banners/multi-page batches/circular seals — supersedes the earlier SVG/Pillow `svg-poster-builder`/`poster-generator`, both marked `operational_status: superseded` not deleted — and a clone-and-inject `slide-deck-composer` for real .pptx decks from a caller-supplied template), a GenVid media cluster (Gemini-backed image/video/audio generation with identity/style anchor profiles, ffmpeg-based assembly), a Legal specializer network (contract review, citation/format checking, dossier tooling, disciplined legal web search), and a merged Student/Learner audience tier spanning K12 through university, plus substantially-staffed Teacher, Parent/Guardian, TA/Graduate, Lecturer/Researcher, and Lifelong Learner tiers. Formal stage-4 quality evaluation is scoped (not blanket-deferred): exempt for foundation/general-capability skills, required only for niche-specializer skills elicited from a real expert source or skills ingesting uncontrolled external input — see `registry/SCHEMA.md`'s `quality_score` field. One skill (`socratic-concept-helper`) is deliberately paused pending a real student/teacher survey rather than treated as production-ready. Full real status, verified against the registry (never from memory): `docs/STATUS.md`.

## Structure

- `docs/` — `MASTER_CONTEXT.md` (architecture + documentation convention), `STATUS.md` (real status), `DECISIONS_PENDING.md`, `specs/` (official specs), `templates/` (reusable operational templates), `guides/` (non-technical end-user documentation), `archive/` (historical discussion/raw research).
- `skills/` — each skill is a subfolder containing a `SKILL.md` matching the agentskills.io 6-field spec (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`).
- `registry/` — the multi-axis identity backbone (domain, task-type, risk-tier, grounding, harness-compatibility). Schema: `registry/SCHEMA.md`. Data: `registry/skills.json`.
- `outside_research/` — living input gathered before a tier is built (owner-authored surveys, AI-assisted research briefs), kept verbatim, never a source of truth on its own. See `docs/MASTER_CONTEXT.md` §3-4.
- `outside_agy/` — reference material surveyed from external LegalTech skill/playbook models (Harvey AI, CoCounsel, Ironclad-inspired), used for comparison only, not copied.

Completed execution plans (e.g. the 2026-07-29 upgrade round that grew the registry 39→62 skills) move to `docs/archive/` once every checklist item is done — see `CLAUDE.md`'s read order.

## Non-negotiable principles

1. Stick to the agentskills.io open spec — never invent extra frontmatter fields.
2. Quality and security are two different gates — never merge into one review pass.
3. Never mark a skill harness-compatible based on a vendor claim — only direct verification counts.
4. Never let an agent self-generate a skill without input elicited from a real source.
5. One skill that runs well, audits clean, and gets real use beats ten skills sitting unused in the registry.

Start at [docs/README.md](docs/README.md) for the full navigation hub. Full strategic detail: `docs/specs/STRATEGY_SPEC.md`.
