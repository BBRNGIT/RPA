# T1 — Finalize Docker Compose & Dockerfiles in Repo

## Purpose

Ensure the repo contains complete, correct Docker configuration for all three services. Since development happens directly online (pushing to GitHub), this work is done in the repo itself — not verified locally. GitHub Actions (T3) will be the first real build test.

## Spec Reference

spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/85700796-5df9-4395-b084-666c2f4f810f — Step 1

## Scope

**In:**

- Audit the repo for `docker-compose.yml` — create or complete it if missing
- Define all three services: `rpa-backend` (FastAPI), `rpa-frontend` (Nginx + React), `rpa-sandbox` (network-isolated Python executor)
- `rpa-backend` Dockerfile: installs all Python dependencies from `requirements.txt`, copies `rpa/` and `curriculum/` source
- `rpa-frontend` Dockerfile: builds the React app (`npm run build`) and serves the static output via Nginx
- `rpa-sandbox` Dockerfile: minimal Python image with `network_mode: none` — no internet access
- `docker-compose.yml` (production mode): references GHCR image tags (`ghcr.io/bbrngit/rpa-*:latest`) — does NOT build from source on the server
- `docker-compose.build.yml` (build mode): used by GitHub Actions to build images from source
- Named Docker volumes for `data/` (LTM graph + EpisodicMemory) — persists across container restarts
- `restart: unless-stopped` on all services
- `.env.example` committed to repo with all required variables: `HUGGINGFACE_TOKEN`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `LTM_DATA_PATH`, `SANDBOX_TIMEOUT`
- Nginx config file for the frontend container: reverse-proxies `/api/` and `/ws/` to `rpa-backend:8000`

**Out:**

- No local `docker-compose up` verification (dev is online)
- No server provisioning (T2)
- No CI/CD pipeline (T3)

## Acceptance Criteria

- `docker-compose.yml` and `docker-compose.build.yml` exist at repo root
- All three Dockerfiles exist (`docker/backend/Dockerfile`, `docker/frontend/Dockerfile`, `docker/sandbox/Dockerfile`)
- `rpa-backend` Dockerfile correctly installs from `requirements.txt`
- `rpa-frontend` Dockerfile correctly builds the React app and serves via Nginx
- `rpa-sandbox` Dockerfile has no network access configured
- Nginx config correctly proxies `/api/` and `/ws/` to the backend
- `.env.example` is committed with all required variable names
- Named volume for `data/` is defined in `docker-compose.yml`
- GitHub Actions (T3) can use these files to build and push images successfully

## Dependencies

None — this is the starting point.