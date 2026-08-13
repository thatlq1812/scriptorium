# Common pitfalls when translating EN ↔ VI

## Verb tense

Vietnamese doesn't conjugate verbs by tense through inflection — it uses time adverbs/aspect markers (đã/đang/sẽ/rồi/từng). When translating EN→VI, don't add "đã/sẽ" to EVERY sentence just because English has tense — only add it when the timing needs clarifying and context isn't already clear enough (Vietnamese typically drops these when the context already implies it). When translating VI→EN, you must infer the correct tense from context since Vietnamese doesn't always mark it explicitly — read the timing carefully before choosing a tense.

## Classifiers

Vietnamese requires a classifier word (cái, con, chiếc, quả, việc...) before a countable noun in many contexts — English has no equivalent concept. When translating EN→VI, never drop the classifier just because the original has nothing corresponding to it ("a skill" → "một skill," not "một cái skill" nor dropping "một" entirely — choose the classifier based on the noun's nature; abstract nouns/technical loanword concepts usually need no classifier).

## Personal pronouns

Vietnamese has no neutral "I/you" — the choice depends on the relationship/rank (tôi/mình/em/anh/chị/bạn...). When translating technical documentation with no clear relationship context (like a README, SKILL.md), default to "bạn" (the reader) and avoid a first-person subject where possible (use a subjectless active sentence or a light passive, matching common Vietnamese technical-writing register).

## False friends / idioms that don't translate literally

An English idiom translated literally is often completely wrong in figurative meaning ("break a leg" ≠ "gãy chân"). Always check: does the phrase have a figurative meaning different from the literal meaning of its component words — if so, find an idiom/expression equivalent in FUNCTION (same communicative purpose) in the target language, don't translate word-by-word.

## Technical loanwords

Don't force-Vietnamize technical terms already established in their original form within the Vietnamese-speaking community (API, skill, prompt, token, agent, repo, commit...) — a forced translation ("kỹ năng" for "skill" in the Agent Skills context) causes confusion because the term already has its own established technical meaning, distinct from the everyday meaning of the equivalent Vietnamese word.

## Mandatory self-check after translating

Once translated, read the translation back independently of the source (don't look at them side by side) — if you need to go back and read the source to understand what the translation is saying, the translation isn't natural yet. This self-check step is mandatory, not optional.
