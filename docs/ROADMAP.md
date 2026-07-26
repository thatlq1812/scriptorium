# Roadmap — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude | First version — recorded the skill-expansion backlog the owner laid out (`important.md`); owner delegated full ordering authority. |
| 1.1.0 | 2026-07-26 | Claude | Completed backlog items 1-5 in the same session: 8 new skills (`dedup-novelty-check`, `mermaid-diagram-designer`, `translator-en-vi`, `latex-project-bootstrap`, + item-5 scouting). Recorded deep-scout results from the 2 large repos. |
| 1.2.0 | 2026-07-26 | Claude | Translated to English per owner directive (whole system except `docs/archive/` and outside-reference material). |

---

## Background

Owner supplied 4 external sources, all license-verified clean (`docs/STATUS.md` — no debt needed for these):

| Repo | Stars | License | Note |
| --- | --- | --- | --- |
| `google-gemini/gemini-cli` | 106,186 | Apache-2.0 | CLI agent, referenced for architecture patterns, not a direct skill source |
| `K-Dense-AI/scientific-agent-skills` | 31,783 | MIT | 148 real scientific skills in `skills/` |
| `VoltAgent/awesome-agent-skills` | 28,962 | MIT | A curated list linking to 1000+ other skills — used as an INDEX for further discovery, doesn't contain skills itself |
| `mermaid-js/mermaid` | 89,421 | MIT | Diagram syntax, source for `mermaid-diagram-designer` |

A "Top 10 Agent Skills repos" blog post the owner pasted had **unverifiable figures** (e.g. "Matt Pocock Skills 130k+ stars" — the real repo tops out at 59 stars; "Superpowers" has no matching repo findable on GitHub) — **not used as a source**, only direct verification via `gh api`/`gh search` counts, as done for the 4 repos above.

The image the owner sent (`1785053923858_...jpg`) is an org-chart-style diagram of 42 skills from a different commercial product (grouped by department: Dev/Design/Marketing/Social/Finance/Small-business/Legal) — used as **structural inspiration for future domain expansion**, content not copied.

## Principle applied to every new skill from now on (owner, 2026-07-26)

A skill with only a `SKILL.md` does NOT meet the bar. A quality skill needs enough supporting files (`scripts/`, `references/`, `assets/` as appropriate) that "looking it over tells you what it'll do and makes you actually want to use it" — not pure text describing intent.

## Backlog (execution order chosen by Claude)

| # | Item | Ordering rationale | Status |
| --- | --- | --- | --- |
| 1 | `dedup-novelty-check` (stage 8) | Rule already existed in `registry/SCHEMA.md`; finish staffing the pipeline skeleton (9/9 stages with an operating skill) before expanding sideways | **Done** — `skills/dedup-novelty-check/` |
| 2 | `mermaid-diagram-designer` | MIT, clear architecture (text syntax → diagram), testable immediately without a long elicit | **Done** — `skills/mermaid-diagram-designer/` |
| 3 | `translator-en-vi` | No external repo scouting needed — elicited directly from the owner on translation quality control (terminology, register), other languages later | **Done** — `skills/translator-en-vi/` |
| 4 | LaTeX/research skill(s) from `D:\elix\researches` | Needed deeper reading of the real structure (`textbooks/document_engineering/`, `docs/methodology/idea_to_book_series.md`, `elix-textbook.cls`) to elicit the actual process instead of guessing — more time than the 3 items above | **Done** — `skills/latex-project-bootstrap/` (generic scaffold, didn't copy the project-specific `.cls`) |
| 5 | Deep-scout `scientific-agent-skills` (148 skills) + browse the `awesome-agent-skills` catalog (1000+ entries) | Largest volume of work — best done after having 3-4 high-quality sample skills to calibrate against, to avoid mass-harvesting then discovering a standard mismatch that requires redoing everything | **Scouting done, harvesting not yet done** — see "Item 5 scout results" below |
| 6 (optional) | Image-generation skill (using the user's own API key) | Owner marked optional, referencing `D:/elix/platform/scripts`, `D:/UNI/S9_SP26/MLN131/project` | **Done, expanded into a designer toolkit** — `skills/image-generator-gemini/`, grounded in a full survey of both referenced projects. Verified for real via actual API calls (owner-authorized test key). |

## Item 5 scout results (2026-07-26)

**`K-Dense-AI/scientific-agent-skills`** (148 real skills in `skills/`, MIT, verified via `gh api`): broad coverage — domain-specific scientific tooling (`biopython`, `scanpy`, `rdkit`, `qiskit`, `pymatgen`...), statistical analysis (`statsmodels`, `pymc`, `scikit-survival`), scientific writing/presentation (`scientific-writing`, `scientific-slides`, `literature-review`, `peer-review`, `citation-management`), and a few skills that **overlap with what Scriptorium already has** (`docx`, `pptx`, `xlsx`, `pdf`, `markitdown`, `latex-posters` — run `dedup-novelty-check` before harvesting any of these; high odds of overlap with the existing `office-doc-creator`/`document-ai-structurer`). Candidates worth harvesting first (no overlap, high value, low narrow-domain coupling): `citation-management`, `literature-review`, `experimental-design`, `statistical-power`, `exploratory-data-analysis`.

**`VoltAgent/awesome-agent-skills`** (curated link list, MIT): structured by Official/Core/by-programming-language (.NET/Java/Python/Rust/TypeScript)/NVIDIA-tooling/Community. Has a "Skill Quality Standards" table (third-person description + specific keywords, progressive disclosure <500 lines, **no hard-coded absolute paths**, scoped tools instead of `"tools": ["*"]`) — matches most of the principles Scriptorium already set independently, confirming the direction is aligned with community standards. One thing to self-check: audit Scriptorium's existing scripts for any hard-coded absolute path (`check_dedup.py` uses `Path(__file__).resolve().parents[2]` — relative, safe; need to check the remaining scripts too).

Haven't harvested any specific skill from these two sources yet — waiting on owner priority confirmation before proceeding (see end of session).

## Long-term direction (owner confirmed it's sound)

General-purpose skill clusters first → skills by audience (students, university students, teachers, professors) → explosion by industry. Matches the principle already in `docs/specs/STRATEGY_SPEC.md` §5 (the legal vertical is the first pilot, not the only one).

## More flexible repo structure (owner confirmed)

Not everything has to live inside `skills/`. Free to add directories at root (`scripts/`, a shared `venv`...) if convenient — treat Scriptorium like a normal project, not a rigid mold containing only `skills/`.
