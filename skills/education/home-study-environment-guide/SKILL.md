---
name: home-study-environment-guide
description: Checks a parent/guardian's home study-environment setup (dedicated study space, daily routine, screen-time policy) for structural completeness, and prints non-blocking advisory comparisons against real, named public guidance (AAP screen-time recommendations, National Sleep Foundation sleep-duration ranges) when the caller supplies a child's age and/or sleep schedule. Use when a parent wants to check their home study setup covers the basics before relying on it, or wants a mechanical sanity-check against published age-band guidance. Do NOT use this to prescribe a study plan or curriculum (that's study-plan-builder), to enforce any number as a mandatory rule (every advisory is a warning, never a hard block), or as authority on a specific child's individual needs -- it restates cited public reference ranges, it does not replace a pediatrician's or teacher's judgment.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, argparse) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "General-capability tier per CLAUDE.md principle 4 -- public-source grounding, no expert interview needed. Grounded in 3 real, named, currently-live public sources, each verified via live web search on 2026-07-29 (not recalled from training-data memory alone): (1) American Academy of Pediatrics (AAP), 'Media and Young Minds' (Pediatrics, 2016, publications.aap.org/pediatrics/article/138/5/e20162591) and the AAP's own 2026 updated screen-time guidance (aap.org Center of Excellence on Social Media and Youth Mental Health; healthychildren.org Family Media Use Plan) -- confirmed live: avoid screen use other than video-chatting under 18 months; at most about 1 hour/day of high-quality content for ages 2-5; the AAP's 2026 update explicitly moved away from a single fixed-hours number for ages 6+ toward an individualized family media-use plan emphasizing quality/context/not displacing sleep, physical activity, or family time, and toward device-free bedrooms and mealtimes -- this skill does NOT invent a replacement fixed-hours number for ages 6+, matching that source's own explicit stance. (2) National Sleep Foundation, 'How Much Sleep Do Babies and Kids Need' (sleepfoundation.org / thensf.org) -- confirmed live age-banded sleep-duration ranges (0-3mo 14-17h, 4-11mo 12-15h, 1-2y 11-14h, 3-5y 10-13h, 6-13y 9-11h, 14-17y 8-10h), used verbatim as NSF_SLEEP_BANDS in scripts/validate_home_study_environment.py. (3) The general 'dedicated space + consistent routine + minimized distraction' shape for a home study environment is a widely-documented convention across public parenting/education-support literature (e.g. school-district and library 'homework help for parents' guidance), not attributed to one single named source -- kept as a structural-completeness check only (no invented numeric threshold attached to it), the same discipline grade-book-builder applies to its own weight/banding inputs. Every numeric value used in an advisory (never a hard-blocking check) traces to source (1) or (2) above; nothing was invented."
  version: 0.1.0
  grounding: required
  object_type: ["checklist"]
---

# home-study-environment-guide

Checks a parent/guardian's home study-environment setup -- dedicated space, daily routine, screen-time policy -- for structural completeness, then prints non-blocking advisories comparing the declared setup against real, named, cited public guidance when the caller supplies a child's age and/or sleep schedule.

## Why this skill, and why this scope

A recurring parent-tier need distinct from anything a teacher-facing skill covers: does the physical/behavioral setup around a child's home study time have the basics in place. This is deliberately split into two layers, mirroring `grade-book-builder`'s own discipline about invented numbers:

1. **Structural completeness** (hard-blocking): does the record actually declare a study space, a routine, and a screen-time policy, with no field left unanswered. This layer has no numeric judgment at all -- it is pure presence/type checking, same shape as `parent-communication`/`legal-form-filler`.
2. **Advisory comparison against cited public guidance** (never blocking): if the caller also supplies a child's age and/or a sleep schedule, the script compares the declared screen-time/sleep numbers against real, named, currently-live public sources -- printed as a warning, never a failure. A family's setup does not become "invalid" because it differs from a published reference range; the advisory exists so a parent notices the gap, not so the script overrides their judgment.

## Grounding: exact sources, verified live 2026-07-29

Every numeric value this script uses in an advisory was verified via live web search on 2026-07-29, not recalled from memory alone, per this project's grounding discipline (no factual claim without a real, citable source):

- **American Academy of Pediatrics (AAP)**, "Media and Young Minds" (*Pediatrics*, 2016, `publications.aap.org/pediatrics/article/138/5/e20162591`) and the AAP's own 2026 updated screen-time guidance (`aap.org` Center of Excellence on Social Media and Youth Mental Health; `healthychildren.org` Family Media Use Plan):
  - Avoid screen use other than video-chatting for children **under 18 months**.
  - At most **about 1 hour/day of high-quality content for ages 2-5**.
  - For ages 6+, the AAP's 2026 update **explicitly moved away from a single fixed-hours number**, toward an individualized family media-use plan emphasizing content quality/context and not letting screens displace sleep, physical activity, or family time -- and toward **device-free bedrooms and mealtimes**. This skill does not invent a replacement fixed-hours number for 6+ -- no screen-hours advisory fires above age 5, matching the source's own current stance.
- **National Sleep Foundation**, "How Much Sleep Do Babies and Kids Need" (`sleepfoundation.org` / `thensf.org`): age-banded recommended sleep-duration ranges (0-3 months 14-17h, 4-11 months 12-15h, 1-2 years 11-14h, 3-5 years 10-13h, 6-13 years 9-11h, 14-17 years 8-10h) -- used verbatim in `NSF_SLEEP_BANDS`.
- The general "dedicated space + consistent routine + minimized distraction" shape is a widely-documented convention across public parenting/education-support literature, not attributed to one named source -- kept as a structural-completeness check only, with no numeric threshold invented for it.

## How to run

```bash
python scripts/validate_home_study_environment.py <record.json>
```

Start from `assets/home_study_environment_template.json`. Required structure:

| Field | Meaning |
| --- | --- |
| `child_name` | Non-empty string. |
| `child_age_years` | Optional number. If omitted, only age-independent checks run (no invented default age). |
| `study_space.location`, `.has_dedicated_desk_or_table`, `.distraction_controls` | Where the child studies, whether there's a dedicated surface, and a non-empty list of concrete distraction controls in place. |
| `routine.study_schedule` | Free text describing when study happens. `regular_bedtime`/`regular_wake_time` optional, 24h `HH:MM` if given. |
| `screen_time_policy.study_block_device_free`, `.device_free_bedroom`, `.device_free_mealtime` | Required booleans. `recreational_screen_hours_per_day` optional non-negative number. |

Exit 0 = structurally complete (advisories, if any, print above the VALID line -- non-blocking reference comparisons, not failures). Exit 1 = at least one structural error (missing/wrong-type required field, malformed `HH:MM` time). Exit 2 = file not readable or malformed JSON.

## What this skill does NOT do

- **Does not prescribe a study plan, curriculum, or subject-specific schedule** -- that's `study-plan-builder`. This only checks the environment/routine setup around study time, not what's being studied.
- **Does not enforce any advisory number as a rule.** Every age/sleep comparison is a WARNING printed for the parent to read, never a validation failure -- a family's actual circumstances vary, and this script has no authority to declare a setup "wrong" for differing from a reference range.
- **Does not invent a screen-time number for ages 6+.** The AAP's own 2026 guidance deliberately dropped a single fixed-hours rule for that age range in favor of an individualized plan -- this skill does not fabricate a replacement number to fill that gap.
- **Does not call any LLM/AI API** -- pure stdlib structural + arithmetic checking, no network of any kind at runtime (the grounding sources above were verified once during authoring, not fetched live on every run).
- **Is not medical, developmental, or educational advice** for an individual child -- it restates published reference ranges; a parent with a specific concern should consult their child's pediatrician or teacher, not treat this script's output as a diagnosis.

## Verified

A complete record (age 8, full study_space/routine/screen_time_policy, bedtime 21:30/wake 06:30 -> 9.0h, within the NSF 6-13y band of 9-11h, recreational_screen_hours_per_day 1.0) validated with zero errors and zero advisories. A record missing `study_space.distraction_controls` entirely correctly refused (exit 1, naming the field). A record with `screen_time_policy.study_block_device_free` given as the string `"yes"` instead of a boolean correctly refused (exit 1, naming the type mismatch). An age-1 (child_age_years=1.0, under 18 months) record with `recreational_screen_hours_per_day: 2.0` correctly produced an AAP-cited advisory (exit 0, 1 warning) without blocking. An age-4 record with `recreational_screen_hours_per_day: 3.0` (exceeding the AAP-cited ~1h/day for ages 2-5) correctly produced the matching advisory. An age-10 record with `recreational_screen_hours_per_day: 6.0` correctly produced NO screen-hours advisory (exit 0, 0 warnings on that axis) -- confirming ages 6+ deliberately has no invented fixed-hours threshold, matching the AAP's own 2026 stance. A record with `device_free_bedroom: false` and `device_free_mealtime: false` correctly produced both AAP-cited advisories. A record with `regular_bedtime: "23:30"` and `regular_wake_time: "05:30"` for a 7-year-old (computed 6.0h, below the NSF 6-13y band of 9-11h) correctly produced the sleep-duration advisory naming the actual computed hours and the cited band. A record with `regular_bedtime: "25:99"` (invalid time) correctly refused (exit 1, naming the malformed value). A record with `child_age_years: -3` correctly refused (exit 1). Malformed JSON correctly refused (exit 2).

## Known limitations (v0.1.0)

- Age is a single scalar (`child_age_years`); no support for validating multiple children in one record -- run once per child.
- The screen-time advisory bands only cover the AAP-cited under-18-months and 2-5-years ranges; per the AAP's own 2026 guidance, no numeric advisory fires for ages 6+ (see "Grounding" above) -- this is a deliberate absence, not an oversight, but it does mean a parent of an older child gets no screen-hours advisory from this script at all, only the device-free-bedroom/mealtime and structural checks.
- The sleep-duration advisory assumes a single nightly sleep window computed from `regular_bedtime`/`regular_wake_time` -- it does not account for daytime naps (relevant for the youngest NSF bands, where total recommended sleep includes naps), so a young child's advisory may under-count actual total sleep if naps aren't reflected in the record.
- `distraction_controls` and the general space/routine shape are checked for presence only, not content -- the script cannot judge whether a listed distraction control is actually effective, only that something concrete was declared.
- Public guidance changes over time (the AAP's own 2026 update is itself a revision of its 2016 position) -- the citations above were verified live on 2026-07-29; a future maintainer should re-verify before trusting these numbers years later.
