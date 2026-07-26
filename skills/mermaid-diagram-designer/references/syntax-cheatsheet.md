# Mermaid — syntax cheatsheet by diagram type

Every Mermaid diagram is plain text, placed inside a ```` ```mermaid ```` code fence (markdown) or `<pre class="mermaid">` (HTML). The first line is always the diagram-type keyword.

## Flowchart — processes, decision flows

```
flowchart TD
    A[Start] --> B{Condition?}
    B -->|Yes| C[Process A]
    B -->|No| D[Process B]
    C --> E[End]
    D --> E
```

Direction: `TD`/`TB` (top-down), `LR` (left-right), `BT`, `RL`. Node shapes: `[rectangle]`, `(rounded)`, `{diamond = decision}`, `((circle))`, `[[subroutine]]`.

## Sequence diagram — interactions over time between multiple actors

```
sequenceDiagram
    participant User
    participant API
    User->>API: Send request
    API-->>User: Return response
    Note over API: Async processing
```

`->>` = synchronous call (solid arrow), `-->>` = reply (dashed arrow), `activate`/`deactivate` to draw a lifeline.

## Class diagram — relationships between classes/entities

```
classDiagram
    class Skill {
        +String name
        +String description
        +run()
    }
    Skill <|-- DomainSkill
    Skill *-- Metadata
```

`<|--` inheritance, `*--` composition, `o--` aggregation, `-->` association.

## State diagram — state machines

```
stateDiagram-v2
    [*] --> Draft
    Draft --> UnderReview: submit
    UnderReview --> Published: approve
    UnderReview --> Draft: reject
    Published --> [*]
```

## ER diagram — data models

```
erDiagram
    SKILL ||--o{ REGISTRY_ENTRY : has
    SKILL {
        string skill_id PK
        string version
    }
```

`||--o{` = one-to-many, `||--||` = one-to-one, `}o--o{` = many-to-many.

## Gantt — project timeline

```
gantt
    dateFormat YYYY-MM-DD
    section Phase 1
    Research :a1, 2026-07-01, 7d
    Design   :after a1, 5d
```

## Pie — simple proportions (NOT the primary tool for complex data charts)

```
pie title Skill distribution by domain
    "meta" : 8
    "general" : 3
```

For more complex quantitative data (multiple series, axes, interactivity), use a dedicated charting tool (matplotlib/Recharts/D3) — don't force Mermaid to do what it isn't strong at.

## Journey / Mindmap / Timeline — presenting experiences/branching ideas

```
journey
    title User journey
    section Discovery
      Find a skill: 5: User
      Read SKILL.md: 4: User
```

```
mindmap
  root((Scriptorium))
    Pipeline
      skill-creator
      quality-eval
    Registry
```

## Common syntax errors (caught in part by the `scripts/lint_mermaid.py` script)

- Missing diagram-type keyword on the first line.
- Unbalanced `[`, `(`, `{` brackets.
- An unclosed edge label (`|text|`).
- Mixing old `stateDiagram` syntax with `stateDiagram-v2` (use `-v2` for every new diagram, richer syntax).
