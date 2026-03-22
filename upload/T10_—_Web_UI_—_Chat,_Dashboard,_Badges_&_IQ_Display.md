# T10 — Web UI — Chat, Dashboard, Badges & IQ Display

## Purpose
Build two distinct frontend surfaces in one React app: a clean, minimal end-user chat interface (public) and a full-featured dev interface (auth-protected). End users never see training controls, dashboards, or internal metrics. Dev/team get the full Open WebUI-style experience.

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/06a32f99-af97-44b5-99f3-1e701c3e02e5` — Frontend UI Wireframes, Web Interface Components
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/cd3bab32-c888-4927-9881-3c95943b5269` — Workstream 3

## Scope

**In — End-User Interface (`/app/*`, public, no auth):**
- Clean, minimal dark chat interface — no sidebar tabs, no dashboard, no training controls
- Message input: free-form natural language only — no slash commands, no code execution UI
- AI response with collapsible reasoning panel (pattern used, why selected, known limitations)
- Current AI capability badge displayed in header (e.g., "🎓 Certified: Junior Python") — read-only
- Session history in sidebar (past conversations only)
- No rating buttons, no gap queue, no internal metrics visible
- Connects to public API only: `POST /api/chat`, `GET /api/badges/current`

**In — Dev Interface (`/dev/*`, auth-protected):**
- Full Open WebUI-style layout: dark sidebar + central chat + top nav (Chat / Dashboard / Gaps)
- Sidebar: session history, full badge shelf with scores and version tags, "New Chat" button
- Chat panel: free-form text, code blocks, slash commands (`/train`, `/assess`, `/gaps`, `/retry`, `/exam`)
- AI response with outcome badge (✅ VALID / ❌ INVALID / ⚠ GAP) + rating buttons
- Collapsible reasoning panel: pattern used, why selected, version history, known gaps
- Dashboard panel: memory stats, training status, intelligence metrics, IQ score + mode switcher, live outcome feed (WebSocket)
- Gaps panel: knowledge gap list with inline answer input
- Connects to dev API: all `/dev/*` endpoints
- Login gate: simple credential check before accessing `/dev/*` routes

**Out:**
- Mobile responsiveness (desktop-first)
- Multi-user auth system (single dev credential for now)

## Acceptance Criteria
- `https://yourdomain.com/app` loads the clean end-user chat interface with no training controls visible
- `https://yourdomain.com/dev` redirects to login if unauthenticated
- After dev login, full dashboard, gaps panel, slash commands, and rating buttons are accessible
- End-user chat calls `POST /api/chat` and displays response with collapsible reasoning
- Dev chat calls `POST /dev/chat` and supports slash commands
- Badge header in end-user UI shows current capability level from `GET /api/badges/current`
- Dashboard updates in real time via WebSocket at `/dev/ws/dashboard`
- IQ mode switcher calls `/dev/iq/mode` and immediately updates displayed score
- No dev-only UI element (dashboard, gaps, slash commands, rating buttons) is reachable from `/app/*` routes

## Dependencies
T9 must be complete (all API endpoints must exist). T2 must be complete (server must be live for production deploy).
