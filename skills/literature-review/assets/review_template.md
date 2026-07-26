<!--
Literature review template. Copy this file, fill every bracketed placeholder,
delete this comment block before finalizing.
-->

# <Review Title>

## 1. Introduction

- **Research question(s)**: <state clearly; use PICO — Population, Intervention, Comparison, Outcome — for clinical/biomedical questions>
- **Review type**: <narrative | scoping | systematic | meta-analysis>
- **Scope**: <time period, geographic scope, study types included>

## 2. Search Strategy

### Search terms and databases

| Database | Date searched | Search terms | Results (raw) |
| --- | --- | --- | --- |
| <arXiv / PubMed / CrossRef / other> | <YYYY-MM-DD> | <terms used> | <count> |

Run via `scripts/search_literature.py "<query>" --sources arxiv pubmed crossref --output sources/search_results.md`.

### Inclusion / exclusion criteria

- **Include**: <date range, language, publication type, study design>
- **Exclude**: <explicit exclusion reasons>

### Screening flow

```
Initial search (combined, before dedup): n = <X>
├─ After deduplication:                  n = <Y>
├─ After title screening:                n = <Z>
├─ After abstract screening:              n = <A>
└─ Included in review:                    n = <B>
```

## 3. Results (organized by theme, NOT study-by-study)

### 3.1 Theme: <theme name>

<Synthesize findings ACROSS studies for this theme — compare, contrast, identify consensus and controversy. Do not summarize studies one at a time.>

### 3.2 Theme: <theme name>

<...>

## 4. Critical Analysis

- Methodological strengths/limitations observed across the included studies.
- Consistency and quality of the evidence overall.
- Known or suspected publication bias.

## 5. Discussion

- Interpretation of findings in the broader context of the field.
- Practical/research implications.
- Comparison with prior reviews, if any exist.

## 6. Limitations of This Review

<Search scope limitations, language/database restrictions, single- vs dual-reviewer screening, etc.>

## 7. Future Directions

<Specific, concrete gaps this review identified that future work should address.>

## 8. References

<Every entry MUST have been resolved via the `citation-management` skill (DOI/PMID/arXiv -> verified BibTeX) before being listed here — do not hand-type bibliographic details from memory.>
