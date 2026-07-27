# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Scriptorium creates, quality-tests, security-audits, and catalogs portable **Agent Skills** (the open `SKILL.md` standard at agentskills.io, ~44 adopter platforms). It is **not** an app, chatbot, or agent harness — it produces skill *artifacts* that run on whatever harness/model the consuming agent already has. Scriptorium itself never calls an AI API (see "Non-negotiable principles" below).

Read in this order before doing any non-trivial work: `docs/MASTER_CONTEXT.md` → `docs/STATUS.md` → `docs/DECISIONS_PENDING.md` → `docs/specs/STRATEGY_SPEC.md` → `docs/ROADMAP.md`.

## Repo structure

```
scriptorium/
├── docs/
│   ├── MASTER_CONTEXT.md      # architecture, scope, documentation convention
│   ├── STATUS.md               # real status, must be verifiable against registry/skills.json
│   ├── DECISIONS_PENDING.md    # decisions awaiting owner confirmation
│   ├── ROADMAP.md              # skill-expansion backlog
│   ├── specs/STRATEGY_SPEC.md  # source of truth for strategy/pipeline/taxonomy
│   ├── templates/              # e.g. CLUSTER_SURVEY_TEMPLATE.md (elicitation before skill-creator)
│   └── archive/                # history, not current state (original language kept verbatim)
├── outside_research/           # living input (owner surveys, external AI research) — ideation only, not elicited input on its own
├── outside_agy/                # external LegalTech reference material — comparison only, never copied
├── skills/<skill_id>/SKILL.md  # each skill is its own subfolder, 6-field agentskills.io spec
├── registry/
│   ├── SCHEMA.md                # multi-axis registry schema
│   └── skills.json              # registry data — the single source of truth for skill status
└── .venv/                      # SHARED Python venv for every Python-dependent skill (gitignored, never committed)
```

When docs conflict: `skills/` + `registry/` beat every doc. Within docs, `specs/` beats `archive/`. `STATUS.md` must match `registry/skills.json` — if they diverge, fix `STATUS.md`.

## The 9-step bootstrap pipeline (order not negotiable)

research → elicit tacit process from a real source → `skill-creator` → quality evaluation (≥2 harnesses) → security audit (separate stage, never merged with quality eval) → scout/harvester (existing prior art) → license-compliance check → dedup/novelty-check → registry entry.

A skill is never "ready to use" until it clears stage 4 (quality eval) *and* stage 5 (security audit) — regardless of how much real use it's already seen while being built. **Running stage 4 on any skill is deliberately deferred by owner decision** — don't run it in a session without asking first.

Before starting a new skill, query `registry/skills.json` by domain/task_type/object_type — if an existing skill already covers ≥80% of scope, extend/version it instead of creating a parallel entry.

## Non-negotiable principles

1. Stick to the agentskills.io 6-field spec (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) — never invent extra top-level frontmatter fields; project-specific fields always live inside `metadata`.
2. Quality evaluation and security audit are two different gates — never merge into one review pass.
3. Never mark a skill harness-compatible from a vendor/showcase claim — only direct verification counts.
4. Never let an agent self-generate a skill without input elicited from a real source (owner, real survey, or a real prior deployed system). `outside_research/`'s brainstormed skill lists are ideation, not elicitation, on their own.
5. Harvesting from an outside source goes through license-compliance-check before skill-creator. Controlled "license debt" is permitted during bootstrap (tag via `registry/SCHEMA.md`'s `license_debt` field, never distribute externally while in debt) — **except** sources with an explicit no-redistribution clause (e.g. Anthropic's docx/pdf/pptx/xlsx skills), which stay hard-BLOCKED, never debt-eligible.
6. One skill that runs well, audits clean, and gets real use beats ten unused skills in the registry.
7. Never commit a venv or binary environment into git. A Python skill declares `requirements.txt`; it installs into the ONE shared root `.venv` via `python-env-bootstrap`, never its own venv.
8. Scriptorium never integrates an AI backend/API (not even the owner's own Elixverse platform) — skills are pure artifacts run by the consuming agent's own backend. Don't add one, even for something that seems like it needs it (e.g. "deep research" skills are protocols the calling agent executes with its own tools, not Scriptorium holding a provider key).
9. The whole system must be in English, except `docs/archive/` (historical, original language) and content brought in purely for outside reference (`outside_agy/`, `outside_research/`).

## Registry (`registry/skills.json`, schema in `registry/SCHEMA.md`)

Every skill needs an entry with 4 mandatory tag axes + 1 optional:
- `domain` — reference SkillsMP's occupation groups; `meta` for skills operating Scriptorium itself, `general` for domain-agnostic task-type skills.
- `task_type` — `research` / `document-conversion` / `drafting` / `review-qa` / `coordination`.
- `risk_tier` — exactly one, `N1` (low) to `N5` (high, mandatory human gate).
- `grounding` — exactly one: `required` (every factual claim must trace to a real source) / `optional` / `not_applicable` (pure scaffolding/formatting tools).
- `object_type` (optional) — free-form artifact type the skill acts on (`contract`, `email`, ...); `[]` if not tied to one.

Other required fields: `elicited_from` (must be non-empty — the real tacit-knowledge source), `security_audit.status` (no skill is "ready" while `!= "passed"`), `license_debt` (null unless deliberately debt-tagged per principle 5 above), `dependencies` (bundled scripts/tools another skill needs, e.g. `python-env-bootstrap`).

## Working with skills

- Each `skills/<skill_id>/SKILL.md` frontmatter follows the agentskills.io spec exactly — see any existing skill (e.g. `skills/legal-citation-checker/SKILL.md`) for the shape, including how `metadata.elicited_from` documents grounding and how the body documents "What this skill does NOT do" / "Known limitations" sections. Follow this documentation shape for new skills — it's how every skill in this repo self-documents scope boundaries.
- Scripts are stdlib-first; a skill only reaches for a real dependency (`docling`, `python-docx`, `playwright`, ...) when the task genuinely needs it, and always through the shared venv (see below), never a private one.
- Deterministic-first: where a script can decide pass/fail mechanically, a script decides it — not a model's judgment call. Several skills follow a "2-step-review" shape: a script proposes candidate structure/matches (explicitly labeled unverified), the reviewing agent checks it, then a second script mechanically applies the reviewed result.
- Grounding discipline: a factual claim without a real, citable source is treated as a bug. Skills refuse loudly (non-zero exit, clear stderr message) rather than silently guessing, dropping data, or fabricating a plausible-looking value — this is the single most consistently enforced behavior across the codebase (see `docs/STATUS.md`'s v0.2.0 hardening-round notes for concrete examples of the failure mode being guarded against).

## Running a Python skill

There is **one shared venv at the repo root** (`.venv/`, gitignored) — never create a per-skill venv. Bootstrap/extend it via `python-env-bootstrap`:

```bash
# Real Unix/macOS shell:
bash skills/python-env-bootstrap/scripts/bootstrap.sh skills/<target_skill>/requirements.txt [python_version]

# Windows — ALWAYS run via real PowerShell, never Git Bash/MSYS2:
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\<target_skill>\requirements.txt [-PyVersion 3.12]
```

**Windows-specific bug (confirmed):** running the bootstrap (or anything invoking `uv`) inside Git Bash/MSYS2 makes `uv` misdetect the platform via MSYS2's Linux-like `uname` and download an unusable Linux Python build. On this Windows box, always invoke `uv`-based scripts through the PowerShell tool, not the Bash tool.

Once bootstrapped, run a skill's script through the shared venv's interpreter, e.g. `.venv\Scripts\python.exe skills\<skill_id>\scripts\<script>.py ...` (Windows) or `.venv/bin/python skills/<skill_id>/scripts/<script>.py ...` (Unix).

## No test suite / build / lint commands

There is no repo-wide build, lint, or test runner — each skill is verified individually by actually running its scripts against real and adversarial fixtures (see each `SKILL.md`'s own "Run" section and `docs/STATUS.md` for what was verified and how). When adding or changing a skill, verify it the same way: run it for real against a valid case and at least one deliberately broken case, and record what was verified in the `SKILL.md` and `docs/STATUS.md` — don't claim a skill works without having actually executed it.
