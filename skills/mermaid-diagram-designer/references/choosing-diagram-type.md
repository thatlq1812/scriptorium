# Choosing a diagram type by situation

| Described situation | Diagram type | Why |
| --- | --- | --- |
| "do A then B, branch if X" | `flowchart` | The clearest way to show decisions/branching |
| "system A calls system B, B replies, there's a time order" | `sequenceDiagram` | The only Mermaid type that shows a time axis across multiple actors |
| "this class/entity inherits/contains that class" | `classDiagram` | Standard UML notation for inheritance/composition relationships |
| "an object moves from one state to another on an event" | `stateDiagram-v2` | Don't use a flowchart to fake a state machine — it lacks transition/event semantics |
| "table A links to table B one-to-many" | `erDiagram` | Standard database relationship notation (crow's foot) |
| "this task runs from date X to Y, depends on an earlier task" | `gantt` | The only type with a real calendar time axis |
| "percentage split between a few groups" | `pie` | Simple, good for 3-6 slices; more than that gets hard to read, consider a bar chart in another tool |
| "user experience across steps, with a satisfaction level" | `journey` | Has a built-in emotion axis (score), which flowchart doesn't |
| "branching ideas with no fixed order/timeline" | `mindmap` | Free tree structure, not forced into a linear flow |
| "a sequence of events by time marker but not tasks with duration" | `timeline` | Lighter than gantt, doesn't need precise start/end dates |

## Quick decision rules

1. There's a **real time axis** (specific dates, duration) → `gantt` or `timeline`.
2. There are **multiple interacting actors** → `sequenceDiagram`.
3. There are **states + state-transition events** (not just sequential steps) → `stateDiagram-v2`.
4. There's a **static data structure/class relationship** (not a processing flow) → `classDiagram` or `erDiagram`.
5. Otherwise, default to `flowchart` — the most flexible, usable for most processes/decisions.

When unsure, ask the user which aspect they want to emphasize (time order? state? data relationships?) instead of guessing — picking the wrong diagram type makes the reader misunderstand the system's actual nature, which is more than just an aesthetic issue.
