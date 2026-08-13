<!--
EDA report scaffold. Copy this file, fill every bracketed placeholder,
delete this comment block before finalizing. Never paste raw cell values,
row content, or direct identifiers into this document — aggregate stats
and column/field names only.
-->

# EDA Report: <dataset name>

**Analysis date**: <YYYY-MM-DD>
**Source file (basename only, no full path)**: <filename>
**Tool + command used**: `python scripts/eda_analyzer.py <file> --root <root>`

## 1. Data dictionary

| Field | Meaning | Unit | Allowed range/categories | Provenance |
| --- | --- | --- | --- | --- |
| <field> | <what it measures> | <unit> | <range> | <where it came from> |

## 2. Observational structure

- **Observational unit**: <row = what?>
- **Subject/sample/replicate hierarchy**: <e.g. multiple rows per subject?>
- **Treatment/control, pairing, blocking, batch/site/instrument**: <describe>
- **Time/spatial structure**: <describe, if any>

## 3. Scanned scope

- Rows/records scanned: <N> (truncated: <yes/no, cap applied>)
- Columns/fields scanned: <N>

## 4. Missingness

| Field | Missing % | Plausible mechanism (MCAR/MAR/MNAR, or explicit code) |
| --- | --- | --- |
| <field> | <%> | <hypothesis, not a claim> |

Missing, structural absence, non-detect/below-LOQ, and true zero are kept
distinct — state which applies to each field with a nonzero "missing" count.

## 5. Distribution and outliers

For each numeric field of interest: report mean/SD alongside median/IQR/MAD,
and state the IQR-fence outlier count. An IQR-fence flag is a diagnostic, not
a deletion rule — no row has been removed from the raw data.

| Field | Mean | Median | SD | IQR | Outlier count (IQR fence) |
| --- | --- | --- | --- | --- | --- |
| <field> | <x> | <x> | <x> | <x> | <n> |

## 6. Train/validation/test boundary (if applicable)

- Split column/unit used: <field, and whether split by subject/time/group>
- Confirm: were any transformations/imputers/scalers fit using training data only? <yes/no>

## 7. Pre-specified vs. exploratory

- Questions defined BEFORE this EDA: <list>
- Patterns noticed DURING this EDA (label explicitly as exploratory, not confirmatory): <list>

## 8. Limitations

<Scan-scope limitations, format-specific caveats (see SKILL.md's capability
matrix), anything this tool could not automatically check.>

## 9. Next steps

<What confirmatory analysis, if any, would be needed — and what pre-registration
or multiple-comparison correction (e.g. Benjamini-Hochberg FDR) it would require.>
