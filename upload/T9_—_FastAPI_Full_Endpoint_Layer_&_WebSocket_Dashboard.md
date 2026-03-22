# T9 — FastAPI Full Endpoint Layer & WebSocket Dashboard

## Purpose
Wire all backend components into a complete, production-ready API with a hard user/dev boundary enforced at the API layer. End users get a clean, minimal public API. Dev/team get a full-featured protected API. Same FastAPI app, two route groups.

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/06a32f99-af97-44b5-99f3-1e701c3e02e5` — API Specification, Web Interface Request Flow

## Scope

**In:**
- Complete `rpa/api/rest_server.py` with two route groups:

**Public routes (`/api/*`) — no auth, end-user facing:**

| Method | Path | Wires To |
|---|---|---|
| `POST` | `/api/chat` | `Orchestrator` → `SelfQuestioningGate` → agent → `OutcomeEvaluator` (self-assessment only, silent) |
| `GET` | `/api/badges/current` | `BadgeManager` — returns current capability level label only |

**Dev routes (`/dev/*`) — auth required, dev/team only:**

| Method | Path | Wires To |
|---|---|---|
| `POST` | `/dev/chat` | Full dev chat with slash command parsing + code execution |
| `POST` | `/dev/chat/{msg_id}/rate` | `OutcomeEvaluator` (explicit user rating source) |
| `POST` | `/dev/train` | `train.py` pipeline (async, streams progress via WebSocket) |
| `GET` | `/dev/status` | Memory stats, training status, IQ score, badge count |
| `GET` | `/dev/gaps` | `GapDetector.detect_all_gaps()` |
| `POST` | `/dev/gaps/{gap_id}/answer` | `AnswerIntegrator` |
| `GET` | `/dev/patterns/{id}` | LTM node detail with full `evolution` block |
| `POST` | `/dev/exam/{track}/{level}` | `ExamEngine` |
| `GET` | `/dev/badges` | `BadgeManager` — full list with scores, timestamps, version tags |
| `GET` | `/dev/iq` | `IQCalculator` current score |
| `POST` | `/dev/iq/mode` | `IQCalculator` mode switch |
| `WS` | `/dev/ws/dashboard` | Live stream: `OutcomeSignal` events, training progress, memory stats |

- Complete `rpa/api/websocket_server.py`:
  - Broadcasts `OutcomeSignal` events in real time as they are produced
  - Broadcasts training progress (patterns learned, validation pass/fail) during `/api/train` runs
  - Broadcasts memory stats every 30 seconds
- CORS configured for the frontend domain
- All endpoints return structured JSON with consistent error format

**Out:**
- Frontend UI (T10)

## Acceptance Criteria
- `POST /api/chat` works without authentication and returns `{answer, reasoning, pattern_used}`
- `GET /api/badges/current` returns only the current badge label (no scores, no history)
- All `/dev/*` endpoints return 401 without valid dev credentials
- All `/dev/*` endpoints work correctly with valid dev credentials
- Silent learning: every `POST /api/chat` call produces an `OutcomeSignal` via self-assessment — no user action required
- WebSocket at `/dev/ws/dashboard` streams events in real time
- Training runs triggered via `/dev/train` stream progress via WebSocket
- All endpoints handle errors gracefully (no 500s on bad input)
- Integration tests cover: public chat flow, dev auth gate, silent outcome signal generation

## Dependencies
T4, T5, T6, T7, T8 must all be complete.
