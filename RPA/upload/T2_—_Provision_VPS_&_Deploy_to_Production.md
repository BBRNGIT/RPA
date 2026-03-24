# T2 — Provision VPS & Deploy to Production

## Purpose
Get the system live on a public URL. Since development happens directly online (pushing to GitHub), the server only needs Docker installed — it pulls pre-built images from GHCR (built by GitHub Actions in T3). No Python, no source code, no build tools needed on the server.

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/85700796-5df9-4395-b084-666c2f4f810f` — Steps 2–5, 7–8

## Scope

**In:**
- Provision a VPS (minimum: Ubuntu 22.04, 2 vCPU, 4GB RAM, 20GB SSD — Hetzner CX22 recommended at ~€4/mo)
- Install **Docker and Docker Compose only** — no Python, no Node, no build tools
- Create a non-root deploy user with Docker group access
- Open firewall ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Copy `docker-compose.yml` and `.env` to `/opt/rpa/` on the server (no full repo clone needed)
- Create `.env` file on server with all production secrets (not committed to git)
- Run `deploy.sh` — pulls images from GHCR and starts containers
- Nginx is handled **inside the `rpa-frontend` container** (configured in T1) — no host-level Nginx needed
- Issue SSL certificate via Certbot (runs as a one-time command on the server, certificate stored in a Docker volume)
- Point domain DNS A record to server IP
- Configure UptimeRobot (free tier) to ping `GET /api/status` every 5 minutes

**Out:**
- No source code on the server (images come from GHCR)
- No Python on the server
- No CI/CD automation (that's T3)
- No intelligence engine features (those are T4–T6)

## Acceptance Criteria
- `https://yourdomain.com` loads the web UI with valid SSL
- `https://yourdomain.com/api/docs` loads FastAPI Swagger UI
- `https://yourdomain.com/api/status` returns HTTP 200
- WebSocket dashboard feed connects at `wss://yourdomain.com/ws/dashboard`
- UptimeRobot monitoring is active and alerting on failure
- LTM data persists across container restarts on the server

## Dependencies
T1 must be complete.
