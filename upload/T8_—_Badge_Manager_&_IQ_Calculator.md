# T8 — Badge Manager & IQ Calculator

## Purpose
Award badges when the AI passes curriculum level exams, and compute the IQ score in the active mode. Badges are the dev milestone markers; IQ is the quantified intelligence metric shown to users.

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/06a32f99-af97-44b5-99f3-1e701c3e02e5` — Data Model (Badge, IQScore), Component Architecture (BadgeManager, IQCalculator)

## Scope

**In:**
- Implement `BadgeManager` (`rpa/assessment/badge_manager.py`):
  - On `ExamSession` pass: create `Badge` record with `badge_id`, `track_id`, `level_id`, `earned_at`, `exam_score`, `patterns_at_time`, `version_tag`
  - Store badge in `EpisodicMemory` and a persistent `badges.json` file
  - Expose badge list via `/api/badges` (wired in T9)
  - `version_tag` format: `v{major}.{minor}-{track}-{level}` (e.g., `v0.3-english-kg`)
- Implement `IQCalculator` (`rpa/assessment/iq_calculator.py`):
  - Three switchable modes (set via `/api/iq/mode`):
    - `exam_based`: score = weighted average of exam pass rates across all tracks
    - `composite`: score = weighted combination of exam pass rate + patterns learned + retry resolution rate + abstraction depth + breadth score
    - `percentile`: score = AI's exam performance vs. human baseline for that level (baseline stored in `curriculum/baselines/`)
  - Recomputes `IQScore` after every exam session and after every N new patterns
  - Stores `IQScore` history in `EpisodicMemory`

**Out:**
- UI display of badges and IQ (T10)

## Acceptance Criteria
- Passing an exam awards a badge with correct `version_tag` and `patterns_at_time`
- Badges persist across container restarts (stored in named volume)
- `IQCalculator` produces a valid score in all three modes
- Switching IQ mode via `/api/iq/mode` immediately recomputes the score
- IQ score history is queryable (last N scores with timestamps)
- Unit tests cover: badge creation, all three IQ modes, mode switching

## Dependencies
T7 must be complete (`ExamSession` must exist).