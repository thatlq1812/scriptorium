# Status — Scriptorium

| Last Updated | Status |
| --- | --- |
| 2026-07-26 | 13 skills written. All have passed `security-audit` (all `passed`), none have a `quality_score` yet (stage 4 hasn't run on any skill) — so no skill is officially "ready to use" yet, even though several have already seen real use this session. See `docs/ROADMAP.md` for the running expansion backlog. Everything below is verified directly against `registry/skills.json` + `skills/`. |

## Existing skills

| skill_id | version | risk_tier | quality_score | security_audit | Ready to use? |
| --- | --- | --- | --- | --- | --- |
| `skill-creator` | 0.3.0 | N2 | `null` | `passed` | **Not yet official** — added 2 gold templates (standalone/dependency) + `scripts/scaffold_skill.py`, adapted from EduStation's `_templates/` pattern, smoke-tested (both templates scaffold correctly, invalid names rejected). Security-audit clean, hasn't passed stage 4. |
| `document-ai-structurer` | 0.1.1 | N1 | `null` | `passed` | **Not yet official** — real PDF smoke test OK, security-audit clean (Docling's external fetch is declared), hasn't passed stage 4. |
| `python-env-bootstrap` | 0.2.0 | N1 | `null` | `passed` (accepted risk, noted) | **Not yet official** — verified working correctly on Windows/PowerShell. Security-audit flagged a blind-trust pattern (`curl\|sh`/`irm\|iex` from astral.sh) as acceptable risk (reputable, declared source), hasn't passed stage 4. |
| `license-compliance-check` | 0.2.0 | N2 | `null` | `passed` | **Not yet official** — verified running for real against anthropics/skills, security-audit clean, hasn't passed stage 4. |
| `quality-eval` | 0.1.0 | N2 | `null` | `passed` | **Not yet official** — design complete (v0.1.0), not yet applied to any real skill, security-audit clean (no script yet). |
| `security-audit` | 0.1.0 | N2 | `null` | `passed` (self-audit) | **Not yet official** — already applied for real to the 5 skills above (self-audit), hasn't passed stage 4. |
| `scout-harvester` | 0.2.0 | N1 | `null` | `passed` | **Not yet official** — distilled from 3 real runs this session (Docling, uv, anthropics/skills). Added `scripts/github_scout.py` + `scripts/pypi_license_check.py`, tested for real (reproduced prior manual findings for mermaid-js/mermaid + 3 PyPI packages). Hasn't passed stage 4. |
| `office-doc-creator` | 0.1.1 | N1 | `null` | `passed` | **Not yet official** — real smoke test across all 3 formats (docx/xlsx/pptx), verified by reading content back including correct Vietnamese diacritics. Uses python-docx/python-pptx/openpyxl (MIT, verified directly), doesn't touch Anthropic's locked skill. Hasn't passed stage 4. |
| `dedup-novelty-check` | 0.1.0 | N1 | `null` | `passed` | **Not yet official** — real overlap-scoring script (stdlib, no dependency), tested both a flagged case and a safe case against the real registry. Hasn't passed stage 4. |
| `mermaid-diagram-designer` | 0.1.0 | N1 | `null` | `passed` | **Not yet official** — 2 reference files + lint script (stdlib), tested both a valid and an invalid diagram. Hasn't passed stage 4. |
| `translator-en-vi` | 0.1.0 | N2 | `null` | `passed` | **Not yet official** — elicited from the owner (no fixed glossary, flexible register), 2 reference files. Hasn't passed stage 4. |
| `latex-project-bootstrap` | 0.1.0 | N1 | `null` | `passed` | **Not yet official** — grounded in the owner's real LaTeX project. Real 4-pass build smoke test (xelatex→biber→xelatex→xelatex), 5-page PDF with correctly-rendered Vietnamese diacritics. Hasn't passed stage 4. |
| `image-generator-gemini` | 0.3.0 | N2 | `null` | `passed` | **Not yet official** — expanded into a full designer toolkit (owner request): added batch auto-anchor, vision-analysis (image→text style), PDF-page-extraction (no AI needed). All 4 capabilities verified for REAL via actual API calls/renders (owner-authorized test key, lightweight model). Grounded in a full survey of `D:/elix/platform/scripts/gen/` (9 scripts) + `D:/UNI/S9_SP26/MLN131/project`. Hasn't passed stage 4. |
| `citation-management` | 0.1.0 | N1 | `null` | `passed` | **Not yet official** — first harvested skill (from K-Dense-AI/scientific-agent-skills, MIT). DOI/PMID/arXiv → BibTeX via free CrossRef/PubMed/arXiv APIs, no AI backend. Verified real: 3 real lookups correct (AlphaFold DOI, a PMID, an arXiv ID) + 1 correct failure case. Hasn't passed stage 4. |

Source: `registry/skills.json`. If the numbers here differ from `registry/skills.json`, the registry wins — this file may be stale.

## Pipeline stage — which have an operating skill, which don't

| Stage | Operating skill | Status |
| --- | --- | --- |
| 1. Research | — | No skill yet; done manually many times (owner + Claude) |
| 2. Elicit tacit process | — | No skill yet; done manually for each existing skill |
| 3. skill-creator | `skills/skill-creator/SKILL.md` | Yes |
| 4. Quality evaluation | `skills/quality-eval/SKILL.md` | Yes — design complete, not yet applied to any real skill |
| 5. Security audit | `skills/security-audit/SKILL.md` | Yes — already applied for real to 5 skills (self-audit) |
| 6. Scout/harvester | `skills/scout-harvester/SKILL.md` | Yes |
| 7. License-compliance check | `skills/license-compliance-check/SKILL.md` | Yes |
| 8. Dedup/novelty-check | `skills/dedup-novelty-check/SKILL.md` | Yes |
| 9. Registry | `registry/SCHEMA.md` + `registry/skills.json` | Yes, 13 entries |

The pipeline skeleton (stages 3-9) is now fully staffed, 7/7 skills operating. Only gap: stages 1/2 (Research, Elicit tacit process) — not yet skill-ified, still done well manually; unclear whether skill-ifying them is even necessary.

## License debt ledger

Empty — no skill currently has `license_debt != null`. This table must be fully reviewed before the system leaves the bootstrap phase (before Phase 2, the legal vertical). See `docs/specs/STRATEGY_SPEC.md` §7 point 5, `registry/SCHEMA.md`.

| skill_id | Source | Reason for debt | Remediation plan | Date |
| --- | --- | --- | --- | --- |

## Infrastructure

- Git repo: initialized 2026-07-26, no remote yet.
- AI backend: none, by design — Scriptorium does not integrate Elixverse or any AI API (`docs/specs/STRATEGY_SPEC.md` §2, §6).
- Shared Python venv: `<repo_root>/.venv`, managed by `python-env-bootstrap`, gitignored. Currently holds dependencies for `document-ai-structurer`, `office-doc-creator`, `image-generator-gemini`.
