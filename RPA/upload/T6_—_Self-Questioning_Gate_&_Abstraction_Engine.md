# T6 — Self-Questioning Gate & Abstraction Engine

## Purpose
Add the pre-output intelligence check (self-questioning) and the long-term compression mechanism (abstraction). Together these make the system feel genuinely intelligent — it checks itself before responding, and it generalizes knowledge over time.

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/06a32f99-af97-44b5-99f3-1e701c3e02e5` — Component Architecture (SelfQuestioningGate, AbstractionEngine), Data Model (AbstractionNode)

## Scope

**In:**
- Implement `SelfQuestioningGate` (`rpa/learning/self_questioning.py`):
  - Before any output: query `GapDetector` for pattern completeness, query `EpisodicMemory` for known failures on this pattern, check for known edge cases
  - If gaps found: return a structured gap response instead of an answer (expose the gap, don't fake it)
  - If complete: pass through to action
- Implement `AbstractionEngine` (`rpa/learning/abstraction_engine.py`):
  - Scan LTM for clusters of similar patterns (structural similarity)
  - Form `AbstractionNode` from clusters (e.g., 20 loop examples → 1 `iteration_concept` node)
  - Link concrete patterns to abstraction via `IS_INSTANCE_OF` edge
  - Future patterns attach to abstraction node first, then specialize
  - Run as a background job (triggered after every N new patterns consolidated to LTM)
- Implement `AbstractionNode` as a `Node` extension (adds `concrete_pattern_ids`, `abstraction_label`, `coverage`, `validated`)

**Out:**
- UI display of self-questioning results (T10)
- Abstraction visualization in dashboard (T10)

## Acceptance Criteria
- A query for an incomplete pattern returns a gap response, not a fabricated answer
- A query for a pattern with known failures surfaces the failure history before responding
- After 20+ similar patterns are in LTM, `AbstractionEngine` forms at least one abstraction node
- Abstraction nodes are linked to their concrete instances via `IS_INSTANCE_OF` edges
- `SelfQuestioningGate` adds < 10ms overhead to response time (graph lookup, not generation)
- Unit tests cover: gap detection path, known failure path, clean pass-through path

## Dependencies
T4 and T5 must be complete.