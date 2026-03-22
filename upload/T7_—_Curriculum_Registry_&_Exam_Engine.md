# T7 — Curriculum Registry & Exam Engine

## Purpose
Define the standardized curriculum tracks and build the engine that runs the AI through real-world exams. This is what transforms the system from "knows things" to "certified to know things at a measurable level."

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/06a32f99-af97-44b5-99f3-1e701c3e02e5` — Data Model (CurriculumTrack, ExamSession), Component Architecture (ExamEngine, CurriculumRegistry)

## Scope

**In:**
- Implement `CurriculumRegistry` (`rpa/assessment/curriculum_registry.py`):
  - Stores all `CurriculumTrack` definitions as JSON config files in `curriculum/tracks/`
  - Initial tracks: English (Kindergarten, Grade 1, Grade 2), Python (Junior, Mid, Senior), Physics (Year 1), Finance (CFA L1 concepts)
  - Each level maps to: an HF dataset + subset, a pass threshold (e.g., 0.8), and a `badge_id`
- Implement `ExamEngine` (`rpa/assessment/exam_engine.py`):
  - Loads questions from HF datasets (MMLU, HumanEval, SQuAD, OpenBookQA) via existing `DatasetLoader`
  - Supports manually curated questions (JSON files in `curriculum/exams/<track>/<level>.json`)
  - Submits each question to the RPA via `AgentInterface`
  - Scores answers against expected (exact match for code, keyword match for text)
  - Produces `ExamSession` record stored in `EpisodicMemory`
  - Triggered via `/api/exam/{track}/{level}` endpoint (wired in T9)

**Out:**
- Badge awarding (T8)
- IQ calculation (T8)
- UI display of exam results (T10)

## Acceptance Criteria
- `CurriculumRegistry` loads all track definitions from `curriculum/tracks/` on startup
- `ExamEngine` can run an exam for any defined track/level
- Exam questions are sourced from HF datasets (streaming, no full download required)
- Manual question override files in `curriculum/exams/` are loaded and merged with HF questions
- `ExamSession` is stored in `EpisodicMemory` with per-question detail (question, expected, AI answer, is_correct)
- Pass/fail determination uses the configured `pass_threshold` per level
- Unit tests cover: HF dataset loading, manual question loading, scoring, pass/fail determination

## Dependencies
None — can run in parallel with T4/T5/T6.