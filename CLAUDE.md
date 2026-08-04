# CLAUDE.md — Mandatory System Context

> [!IMPORTANT]
> **Read this file first — before touching any code, building any skill, or executing any roadmap item.** This applies to every agent (Claude Code, Codex CLI, Kimi, Amp, any other harness) working in this repository. It is the single authoritative entry point for system rules, pipeline order, and non-negotiable constraints.

## What this repository is

Scriptorium creates, quality-tests, security-audits, and catalogs portable **Agent Skills** (the open `SKILL.md` standard at agentskills.io, ~44 adopter platforms). It is **not** an app, chatbot, or agent harness — it produces skill *artifacts* that run on whatever harness/model the consuming agent already has. Scriptorium itself never calls an AI API (see "Non-negotiable principles" below).

Skills are built to that open `SKILL.md` format for cross-harness technical compatibility only — the registry itself (`skills/`, `registry/skills.json`) is proprietary, not published to the public agentskills.io showcase/community. Distribution is commercial: whole skills or curated packs, exported via `skill-exporter`, sold retail — never given away as an open contribution. (Owner decision, 2026-08-02.)

**Read in this order before doing any non-trivial work:**
1. This file (`CLAUDE.md`) — you are here ✓
2. `registry/SCHEMA.md` — registry field definitions and `quality_score` interpretation
3. `docs/MASTER_CONTEXT.md` — architecture, scope, documentation conventions
4. `docs/STATUS.md` — real skill status (verify against `registry/skills.json`)
5. `docs/specs/STRATEGY_SPEC.md` — source of truth for pipeline, taxonomy, and strategy principles
6. `docs/ROADMAP.md` — skill-expansion backlog
7. `docs/DECISIONS_PENDING.md` — decisions awaiting owner confirmation (check before assuming anything is unresolved)
8. `SKILLS_MAP.md` (repo root) — Mermaid overview of the full registry by cluster and real cross-skill dependency; a snapshot, regenerate by hand when the registry count changes, `registry/skills.json` always wins if they diverge

Completed execution plans move to `docs/archive/<name>-<date>/` once every checklist item is done (e.g. `docs/archive/upgrade-plan-2026-07-29/`) — check there for prior rounds' full reasoning before assuming a past decision wasn't documented.

## Repo structure

```
scriptorium/
├── SKILLS_MAP.md               # Mermaid overview of the registry (snapshot, regenerate by hand)
├── docs/
│   ├── MASTER_CONTEXT.md      # architecture, scope, documentation convention
│   ├── STATUS.md               # real status, must be verifiable against registry/skills.json
│   ├── DECISIONS_PENDING.md    # decisions awaiting owner confirmation
│   ├── ROADMAP.md              # skill-expansion backlog
│   ├── specs/STRATEGY_SPEC.md  # source of truth for strategy/pipeline/taxonomy
│   ├── templates/              # e.g. CLUSTER_SURVEY_TEMPLATE.md (elicitation before skill-creator)
│   └── archive/                # history, not current state (original language kept verbatim); completed execution plans (e.g. UPGRADE_PLAN_*.md) live here once fully checked off
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

A skill is "officially ready" only after it clears stage 5 (security audit) and, *if applicable*, stage 4 (quality eval). **Stage 4 does not apply to every skill (owner decision, 2026-07-29)** — it's scoped, via each registry entry's `quality_score.stage4_required`, to (a) niche-specializer skills elicited from a real expert source, and (b) skills that ingest uncontrolled external input (arbitrary documents, web content, third-party repos, external API responses). Foundation/infrastructure and general-capability skills grounded in public sources are exempt by design, not just deferred — see `registry/SCHEMA.md`'s `quality_score` field for the exact rule and `docs/STATUS.md` for the current per-skill classification. **For the ~14 skills where `stage4_required: true`, running stage 4 is still deliberately not yet scheduled — do not run it without asking first.** This is a hold on the formal multi-harness scoring gate, not a statement about implementation quality: every skill in this repo has been tested against real and adversarial inputs, with real bugs found and fixed; security audit has passed for all skills. "Not yet through stage 4" means the formal QA scoring run hasn't been scheduled — it does not mean the skill is broken or ungrounded.

Before starting a new skill, query `registry/skills.json` by domain/task_type/object_type — if an existing skill already covers ≥80% of scope, extend/version it instead of creating a parallel entry.

### Scouting a brand-new skill type before `skill-creator` runs

Standing practice (owner directive, first applied 2026-07-29 and generalized here so it survives beyond any one execution plan): *"Search và clone các repo tiêu biểu cho cùng một chủ đề và tham khảo trước khi tạo kiểu skill đó."* Applies to any genuinely new skill type — not a version bump of an existing skill.

1. Search for 2-4 representative real-world repos/projects on the same topic (`WebSearch`, or `scout-harvester`'s `github_scout.py` for GitHub specifically).
2. Shallow-clone the most relevant 1-3 into `outside_research/references/<topic>/` via `scout-harvester`'s `clone_candidate.py` (never inside `skills/`, never committed as a dependency — reference-only).
3. Run `license-compliance-check` on anything whose patterns/code might get adapted (not just wholesale-copied) — per principle 5 below, harvesting/adapting goes through this gate before `skill-creator`.
4. Record what was found/adapted/rejected in the new skill's own `SKILL.md` (`metadata.elicited_from` or an explicit "Reference material" note) — so a later session can see the grounding without re-deriving it.
5. Only then run `skill-creator`, following the elicitation tier that applies (principle 4 below: infra/bootstrap → no interview needed; general-capability → public-source grounding sufficient; niche specializer → mandatory real elicitation source).

## Non-negotiable principles

1. Stick to the agentskills.io 6-field spec (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) — never invent extra top-level frontmatter fields; project-specific fields always live inside `metadata`.
2. Quality evaluation and security audit are two different gates — never merge into one review pass.
3. Never mark a skill harness-compatible from a vendor/showcase claim — only direct verification counts.
4. **Elicitation requirements vary by knowledge tier** — apply the right bar for each, not a single binary rule:
   - **Infrastructure / bootstrap skills** (e.g. `python-env-bootstrap`, `xelatex-bootstrap`, `skill-creator`): grounded from open specs, public toolchain docs, and direct testing. No expert interview needed.
   - **General-capability skills** (e.g. education, research, study-planning, writing): the knowledge is publicly documented in books, curriculum standards, pedagogy literature, and established best practices. Public-source grounding is sufficient — no expert interview needed before `skill-creator` runs.
   - **Niche specializer skills** (e.g. Vietnamese legal workflows, niche industry procedures, domain-specific tacit processes): the knowledge is NOT publicly findable — it lives in experts' heads, un-written workflows, or locally-specific regulation. A real elicitation source is **mandatory** before `skill-creator` runs: an expert interview, a real prior deployed system, a real practitioner survey, or direct owner instruction confirming the tacit process. `outside_research/`'s brainstormed skill lists are ideation, not elicitation, for this tier.
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
- Composability discipline (2026-07-29, scoped 2026-08-02): when a new skill's output shape genuinely matches an existing skill's input shape (or vice versa), document it explicitly in both `SKILL.md`s — a "Chains into `<skill>`" note with a real, verified example (see `personal-profile-manager`/`legal-form-filler` or `knowledge-gap-analyzer`/`upskilling-roadmap-builder` for the pattern). This isn't optional polish for a pipeline that isn't self-evident from the two skills' own descriptions/schemas: a consuming agent reading one `SKILL.md` in isolation has no way to know a real pipeline exists unless the skill itself says so, and a generic "minimize tool calls" instinct in a downstream agent's own system prompt can otherwise suppress exactly the multi-skill chaining this project is built to enable (`skill-exporter`'s exported `MANIFEST.md` also carries this reminder for real bundles, but don't rely on that alone — the cross-reference belongs in the skill itself). **Scoped by a real cold-agent test (2026-08-02)**: a fresh `general-purpose` agent, given no cross-reference note and no hint either skill existed, was handed a task needing both `svg-poster-builder` (poster zone composition) and `light-logo-arranger` (logo-anchor placement with exclusion-zone collision refusal) — it independently found and correctly ran both real scripts, chaining them without being told to. So this discipline is mandatory when the chain genuinely isn't inferable from the two `SKILL.md`s alone (distant-sounding skill names, a registry large enough that discovery cost is real, or a multi-step pipeline with real stakes — see the legal cluster's verified chains for the pattern that still needs it) — not a blanket requirement for every pair of skills within a small, closely-related cluster whose own descriptions already make the connection obvious. Re-test this judgment call if the registry grows an order of magnitude past its current size (discovery cost rises with registry size, this finding was verified at 63 skills, not at hundreds).

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
