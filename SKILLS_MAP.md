# Scriptorium — Skills Map

Generated from `registry/skills.json` (63 skills, 2026-08-01). Clusters follow the audience-tier/domain grouping documented in `docs/STATUS.md` and `docs/specs/STRATEGY_SPEC.md` §5 — not invented for this diagram. Regenerate by hand whenever the registry count changes; this file is a snapshot, not a source of truth (`registry/skills.json` always wins if they diverge).

Split into one diagram per layer instead of one giant flowchart — a single 62-node/10-subgraph graph doesn't render reliably in most Mermaid viewers. Each layer diagram below is self-contained (its own `skill-creator` note: linted independently). Edges that cross layers (e.g. `document-ai-structurer` feeding a Legal-tier skill) are listed as text under **Cross-layer dependencies**, not forced into a single-layer diagram.

## Layer 0 — Overview (10 clusters, 63 skills)

```mermaid
flowchart TB
  Pipeline["Pipeline & Meta (8)"]
  Foundation["Foundation & Document/Research Tools (20)"]
  LightDesign["Light Design (4)"]
  Legal["Legal Specializer Network (6)"]
  Teacher["Teacher Tier (7)"]
  Student["Student / Learner Tier (7)"]
  Parent["Parent / Guardian Tier (3)"]
  TA["TA / Graduate Tier (3)"]
  Lecturer["Lecturer / Researcher Tier (2)"]
  Lifelong["Lifelong Learner Tier (3)"]

  Pipeline -->|shared venv bootstrap| Foundation
  Foundation -->|document-ai-structurer, personal-profile-manager| Legal
  Foundation -->|office-doc-creator delegate| Teacher
  Student -->|study-plan-builder feeds| Lifelong
```

## Layer 1 — Pipeline & Meta (8)

The 9-step bootstrap pipeline (`CLAUDE.md`) plus the shared-venv dependency almost every scripted skill sits on.

```mermaid
flowchart LR
  skill_creator["skill-creator"]
  quality_eval["quality-eval"]
  security_audit["security-audit"]
  scout_harvester["scout-harvester"]
  license_compliance_check["license-compliance-check"]
  dedup_novelty_check["dedup-novelty-check"]
  registry_db[("registry/skills.json")]
  skill_exporter["skill-exporter"]
  python_env_bootstrap["python-env-bootstrap"]

  skill_creator --> quality_eval --> security_audit --> scout_harvester --> license_compliance_check --> dedup_novelty_check --> registry_db --> skill_exporter
```

## Layer 2 — Foundation & Document/Research Tools (20)

General-capability skills not tied to one audience: document structuring, citation/research discipline, document-generation engines.

```mermaid
flowchart TB
  document_ai_structurer["document-ai-structurer"]
  pii_masking["pii-masking"]
  personal_profile_manager["personal-profile-manager"]
  project_workspace_initializer["project-workspace-initializer"]
  deep_research["deep-research"]
  literature_review["literature-review"]
  citation_management["citation-management"]
  hypothesis_generation["hypothesis-generation"]
  peer_review["peer-review"]
  exploratory_data_analysis["exploratory-data-analysis"]
  translator_en_vi["translator-en-vi"]
  latex_project_bootstrap["latex-project-bootstrap"]
  typst_bootstrap["typst-bootstrap"]
  xelatex_bootstrap["xelatex-bootstrap"]
  pandoc_bootstrap["pandoc-bootstrap"]
  image_generator_gemini["image-generator-gemini"]
  office_doc_creator["office-doc-creator"]
  mermaid_diagram_designer["mermaid-diagram-designer"]
  browser_web_renderer["browser-web-renderer"]
  slide_deck_composer["slide-deck-composer"]

  citation_management --> literature_review
  typst_bootstrap --> latex_project_bootstrap
  xelatex_bootstrap --> latex_project_bootstrap
  pandoc_bootstrap --> latex_project_bootstrap
```

## Layer 3 — Light Design (4)

Deterministic SVG/layout linting only — deliberately not expanded into general image generation or a Figma-class tool (`CLAUDE.md` scope discipline).

```mermaid
flowchart LR
  svg_poster_builder["svg-poster-builder"]
  brand_identity_linter["brand-identity-linter"]
  slogan_copy_linter["slogan-copy-linter"]
  light_logo_arranger["light-logo-arranger"]
```

## Layer 4 — Legal Specializer Network (6)

The first niche-specializer network, all 6 elicited from a real junior-lawyer survey.

```mermaid
flowchart TB
  contract_consistency_linter["contract-consistency-linter"]
  legal_research_brief["legal-research-brief"]
  legal_citation_checker["legal-citation-checker"]
  contract_risk_log["contract-risk-log"]
  legal_form_filler["legal-form-filler"]
  legal_web_search["legal-web-search"]
```

## Layer 5 — Teacher Tier (7)

```mermaid
flowchart TB
  lesson_plan_builder["lesson-plan-builder"]
  assessment_builder["assessment-builder"]
  grading_and_feedback["grading-and-feedback"]
  competency_rubric_builder["competency-rubric-builder"]
  classroom_materials_builder["classroom-materials-builder"]
  grade_book_builder["grade-book-builder"]
  parent_communication["parent-communication"]
```

## Layer 6 — Student / Learner Tier (7)

`group-work-coordinator` sits here for audience-tier placement but is tagged `domain: general` in the registry (deliberate exception, `docs/DECISIONS_PENDING.md` resolved item 7 — RACI matrices aren't education-specific).

```mermaid
flowchart TB
  study_plan_builder["study-plan-builder"]
  exam_ready_scaffold["exam-ready-scaffold"]
  reading_note_structurer["reading-note-structurer"]
  socratic_concept_helper["socratic-concept-helper (PAUSED)"]
  essay_structure_scaffold["essay-structure-scaffold"]
  academic_source_finder["academic-source-finder"]
  group_work_coordinator["group-work-coordinator"]

  classDef paused stroke-dasharray: 5 5,fill:#eee,color:#888
  class socratic_concept_helper paused
```

## Layer 7 — Parent / Guardian Tier (3)

```mermaid
flowchart LR
  parent_school_communicator["parent-school-communicator"]
  home_study_environment_guide["home-study-environment-guide"]
  student_progress_tracker["student-progress-tracker"]
```

## Layer 8 — TA / Graduate Tier (3)

```mermaid
flowchart LR
  ta_grading_rubric_linter["ta-grading-rubric-linter"]
  lab_practicum_guide["lab-practicum-guide"]
  dissertation_proposal_scaffold["dissertation-proposal-scaffold"]
```

## Layer 9 — Lecturer / Researcher Tier (2)

```mermaid
flowchart LR
  academic_grant_proposal["academic-grant-proposal"]
  manuscript_journal_formatter["manuscript-journal-formatter"]
```

## Layer 10 — Lifelong Learner Tier (3)

```mermaid
flowchart LR
  upskilling_roadmap_builder["upskilling-roadmap-builder"]
  certification_exam_prep["certification-exam-prep"]
  knowledge_gap_analyzer["knowledge-gap-analyzer"]

  knowledge_gap_analyzer -.->|from_gap_analysis.py| upskilling_roadmap_builder
```

## Cross-layer dependencies

Real dependencies that cross a layer boundary — not drawable inside a single-layer diagram above, listed here instead of forced in:

| From (layer) | To (layer) | Relationship |
| --- | --- | --- |
| `python-env-bootstrap` (L1) | `document-ai-structurer`, `office-doc-creator`, `image-generator-gemini`, `browser-web-renderer`, `slide-deck-composer` (L2) | shared-venv bootstrap dependency (`registry/skills.json` `dependencies`) |
| `document-ai-structurer` (L2) | `legal-citation-checker`, `legal-form-filler` (L4) | registry `dependencies` field |
| `personal-profile-manager` (L2) | `legal-form-filler` (L4) | `autofill.py` output = `fill_form.py`'s `form_data.json` shape, documented chain |
| `office-doc-creator` (L2) | `assessment-builder` (L5) | DOCX render delegate |
| `study-plan-builder` (L6) | `upskilling-roadmap-builder` (L10) | registry `dependencies` field |

## Reading this map

- `socratic-concept-helper` (Layer 6) is drawn dashed/greyed — registered but `operational_status: paused`, excluded from `skill-exporter` bundles.
- `slide-deck-composer` (Layer 2, added 2026-08-01) is BYOT (Bring Your Own Template) — never bundles a template file itself; composes with `image-generator-gemini` (picture-placeholder fill) and `personal-profile-manager`'s `org_profile` (title-slide identity), documented within-layer, not drawn as an edge.
- Linted with `skills/mermaid-diagram-designer/scripts/lint_mermaid.py` (structural check only, not a real render) — each layer's fenced block extracted and linted independently.
