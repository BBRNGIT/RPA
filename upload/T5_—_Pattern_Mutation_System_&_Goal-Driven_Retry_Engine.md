# T5 — Pattern Mutation System & Goal-Driven Retry Engine

## Purpose
When a pattern fails, the system doesn't just log it — it versions the pattern, links the failure to a fix, and retries with the mutated version. This is the core of the self-improvement loop.

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/06a32f99-af97-44b5-99f3-1e701c3e02e5` — Data Model (PatternVersion, RetrySession), Component Architecture (PatternMutator, RetryEngine)

## Scope

**In:**
- Implement `PatternVersion` data structure
- Implement `PatternMutator` (`rpa/learning/pattern_mutator.py`):
  - On INVALID `OutcomeSignal`: create new `PatternVersion`, link failure → fix, mark old version `is_deprecated = True`
  - Integrates with existing `ErrorClassifier` to classify the failure type before mutating
  - Integrates with existing `ErrorCorrector` to determine the fix
- Implement `RetryEngine` (`rpa/learning/retry_engine.py`):
  - Goal → Attempt → `OutcomeEvaluator` → if INVALID: `PatternMutator` → Retry
  - Hard cap: max 5 retry attempts (enforced by existing `LoopDetector`)
  - Final status: `SUCCESS` | `GAP_IDENTIFIED` | `MAX_RETRIES`
  - Stores full `RetrySession` in `EpisodicMemory`
- Expose `/api/retry` endpoint stub (wired in T9)

**Out:**
- Self-questioning gate (T6)
- UI display of retry sessions (T10)

## Acceptance Criteria
- A failing pattern produces a new `PatternVersion` with `reason` and `created_by` fields populated
- Old pattern version is marked `is_deprecated = True`
- `RetrySession` is stored in `EpisodicMemory` with all attempts logged
- Retry loop stops at max 5 attempts — no infinite loops
- `GAP_IDENTIFIED` status is returned when the error cannot be classified/fixed
- Unit tests cover: single retry success, max retry exhaustion, gap identification

## Dependencies
T4 must be complete (`OutcomeSignal` and `OutcomeEvaluator` must exist).