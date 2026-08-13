# skill-creator templates — gold reference skeletons

Two complete skeletons `skill-creator` copies from when authoring a new skill, instead of writing `SKILL.md` from a blank file each time. These are REFERENCE TEMPLATES — copy, fill, delete every `<!-- -->` comment block, never ship a template's comments in a real skill.

| Template | Use it for |
| --- | --- |
| [`standalone_skill/`](standalone_skill/) | A skill a user/agent invokes directly to produce a deliverable (a converted file, a generated asset, a draft). Mirrors `document-ai-structurer`, `office-doc-creator`, `image-generator-gemini`. |
| [`dependency_skill/`](dependency_skill/) | Infrastructure other skills lean on — not invoked directly for a deliverable. Mirrors `toolchain-bootstrap`, `license-compliance-check`, `dedup-novelty-check`. |

Adapted from the gold-template pattern in `prior project templates` (the owner's prior project) — kept the principle (copy-a-skeleton-with-marked-slots instead of writing from scratch, ★ REQUIRED / ◆ CHOOSE comment legend), dropped the harness-specific machinery (prior system's `use_skill`/`script_exec`/tier-based CI enforcement are tied to their own orchestrator, not portable to the agentskills.io spec Scriptorium targets).

## Deciding standalone vs dependency

Ask: is this skill something a user/agent reaches for directly to get a deliverable, or is it something ANOTHER skill calls to do its job? If the honest answer is "both," lean standalone — a dependency skill that also happens to be independently useful is fine, but a standalone-framed skill that's really just infrastructure confuses triggering (per skill-creator's own trigger-eval guidance).

## Using a template

```bash
python skills/meta/skill-creator/scripts/scaffold_skill.py <skill_id> --template standalone_skill --domain <domain>
# or: --template dependency_skill
```

Copies the chosen template into `skills/<skill_id>/`, substitutes `<skill_id>` in `SKILL.md`, and leaves every other `<...>` slot for the agent to fill by hand (the tool only automates the folder/name mechanics, not the actual authoring — that still requires elicited input + research, per skill-creator's precondition).
