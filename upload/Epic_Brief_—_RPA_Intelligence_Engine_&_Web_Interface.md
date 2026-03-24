# Epic Brief — RPA Intelligence Engine & Web Interface

## Summary

The RPA (Recursive Pattern Architecture) system currently learns patterns from curated datasets and stores them in a graph-based memory (STM → LTM). It can execute code in a sandbox, detect knowledge gaps, and coordinate multiple agents. However, it operates as a **static knowledge store** — it knows things, but it does not get better at knowing things over time. This Epic upgrades the system into a **closed-loop, self-improving organism** by adding a continuous feedback and learning engine, and exposes the full system through a modern web interface for direct human interaction.

## Context & Problem

### Two distinct user groups

**Dev/Team (internal):** The developer and team who train the RPA, run curriculum pipelines, monitor learning, trigger exams, view the dashboard, and iterate on the system's knowledge. All training, curriculum management, exam triggering, gap analysis, and system monitoring features are **exclusively for this group**.

**End users (public):** Millions of everyday users who interact with the AI through a clean conversational interface. They see only the AI's responses. They have no visibility into training pipelines, curriculum tracks, exam results, gap queues, or internal metrics. The AI learns from their natural interactions — but this happens silently in the background, not through explicit training controls.

### Where in the system

Two gaps exist simultaneously:

**Gap 1 — No closed learning loop.** After a pattern is learned and used, nothing happens. Errors are logged but patterns are never mutated. There is no outcome evaluation, no reinforcement signal, no self-questioning before output, and no goal-driven retry. The system cannot improve itself between training runs.

**Gap 2 — No human interface.** Interaction requires running Python scripts directly. There is no way to query the AI conversationally, submit code for execution, trigger training runs, or observe the system's internal state in real time.

**Gap 3 — No user/dev separation.** There is no distinction between what a developer sees (training controls, curriculum, dashboard, gaps) and what an end user sees (just the AI). This boundary must be designed in from the start.

### Current pain

- Patterns that fail are stored as-is — no versioning, no deprecation, no fix linkage
- The system has no mechanism to ask "have I seen this fail before?" before responding
- Errors from sandbox execution are classified but never fed back to mutate the originating pattern
- Memory is a database, not a learning organism — no usage frequency, no evolution trail
- The only way to interact with the system is via Python REPL or CLI

## Scope

### Workstream 0 — Production Deployment *(immediate)*

Deploy the current Phase 8 full-stack build from GitHub (`BBRNGIT/RPA`) to production while development continues in parallel. The system is already functional — training pipeline, sandbox execution, multi-agent coordination, and the web UI demo are all present. Deployment is Docker-first using the existing `docker-compose.yml`.

### Workstream 1 — Closed-Loop Intelligence Engine *(first)*

Add the missing feedback and self-improvement layer:


| Component                | Purpose                                                                             |
| ------------------------ | ----------------------------------------------------------------------------------- |
| Outcome Evaluator        | Classify every action result: ✅ Valid / ❌ Invalid / ⚠ Gap                           |
| Pattern Mutator          | Version, fix, and deprecate patterns on failure                                     |
| Reinforcement Tracker    | Deterministic link strength: reinforce on success, decay on disuse, flag on failure |
| Self-Questioning Gate    | Pre-output check: complete pattern? known failure? known edge case?                 |
| Goal-Driven Retry Engine | Attempt → Sandbox → Error → Classify → Mutate → Retry loop                          |
| Memory Evolution         | LTM patterns gain: origin, versions, failures, fixes, usage frequency               |
| Abstraction Compression  | Cluster similar patterns into generalized abstraction nodes                         |


Feedback sources: sandbox execution result + user explicit rating + RPA's own `SelfAssessmentEngine` (all three).

### Workstream 2 — Standardized Curriculum, Exams & IQ Scoring *(parallel with engine)*

The curriculum certifies what the AI has learned as usable in the real world — it does not constrain learning. Data continues flowing through the normal pipeline (Hugging Face → DatasetLoader → LTM). Periodically, the AI sits standardized exams mapped to curriculum levels.


| Component             | Purpose                                                                                                                                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Curriculum Tracks     | Domain-specific level ladders: English (Kindergarten → Grade N), Python (Junior → Senior), Finance (CFA L1 concepts), Physics (Year 1...)                                                                        |
| Exam Engine           | Runs standardized exams per track/level using HF datasets (MMLU, HumanEval, SQuAD, OpenBookQA) + manually curated questions                                                                                      |
| IQ Score              | Composite, switchable metric: exam pass rate + patterns learned + retry cycles resolved + abstraction nodes formed. Dev can switch between IQ modes.                                                             |
| Badge / Certification | Lightweight milestone marker — when the AI passes a curriculum level exam, it earns a badge. Badges are dev milestones / versioning points. Displayed in the UI to communicate current AI capabilities to users. |


### Workstream 3 — Web Interface *(after engine is stable)*

Two distinct interface surfaces — same codebase, different access levels:

**End-User Interface (public):**

| Element | Description |
| --- | --- |
| Layout | Clean chat interface — no training controls, no dashboard, no internal metrics |
| Chat input | Free-form natural language only — no slash commands, no code execution controls |
| Reasoning panel | Collapsible below each response — pattern used, why selected, known limitations |
| Badge display | Shows current AI capability level (e.g., "Certified: Junior Python") — read-only, no exam controls |
| Learning | AI learns silently from natural interaction — no explicit feedback buttons visible to users |

**Dev/Team Interface (protected, same deployment):**

| Element | Description |
| --- | --- |
| Layout | Full Open WebUI-style layout — sidebar, chat, dashboard, gaps tab |
| Chat input | Free-form text, code blocks, slash commands (`/train`, `/assess`, `/gaps`, `/retry`, `/exam`) |
| Dashboard | Memory stats + training status + intelligence metrics + IQ score + badges |
| Training controls | Trigger training runs, view curriculum tracks, run exams, answer gap inquiries |
| Access control | Protected by dev credentials — not accessible to end users |


> **Note on working history:** The existing `EpisodicMemory` already fulfills the persistent history role — it logs all events (training runs, exam attempts, pattern mutations) with timestamps and session IDs. No duplication needed. The chat UI surfaces relevant history contextually at session start.

## User / Dev Boundary — Non-Negotiable Rules

| Rule | Detail |
|---|---|
| Training is dev-only | End users never see `/train`, dataset controls, curriculum tracks, or exam triggers |
| Dashboard is dev-only | Memory stats, consolidation rates, gap queues, IQ mode switching — dev interface only |
| Silent learning from users | The AI improves from natural user interactions via the feedback pipeline — but this is invisible to users |
| Badges are informational for users | Users see the AI's current capability level (badge name) — they cannot trigger exams or see scores |
| Slash commands are dev-only | `/train`, `/assess`, `/gaps`, `/retry`, `/exam` are never exposed in the end-user interface |
| One deployment, two surfaces | Both interfaces run from the same Docker stack — access is separated by authentication, not separate deployments |

## Guiding Principle

The system must be treated as a **recursive intelligent organism**. Every building block — feedback, mutation, reinforcement, self-questioning, retry, abstraction, memory evolution — must be present. No heuristics pretending to be reasoning. If the system doesn't know → it exposes the gap.
