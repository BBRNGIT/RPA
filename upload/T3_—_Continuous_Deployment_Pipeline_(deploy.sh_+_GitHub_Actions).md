# T3 — Continuous Deployment Pipeline (deploy.sh + GitHub Actions)

## Purpose
Enable zero-friction deployment: merging to `main` automatically builds Docker images, pushes them to GitHub Container Registry (GHCR), and deploys to production. GitHub owns the entire build and image storage pipeline. The production server only needs Docker — it pulls pre-built, tested images from GHCR and runs them. Development continues on feature branches; production stays current.

## Spec Reference
`spec:14489e66-b1b1-4ea2-90bd-6a90ffb7e529/85700796-5df9-4395-b084-666c2f4f810f` — Step 6

## Scope

**In:**

**Step 1 — GitHub Actions CI/CD workflow** (`.github/workflows/deploy.yml`):
  - Triggers on push to `main`
  - Runs `pytest` — blocks deployment if tests fail
  - Logs into GHCR using `GITHUB_TOKEN` (no PAT needed for public repo)
  - Builds all three Docker images using `docker/build-push-action`:
    - `ghcr.io/bbrngit/rpa-backend:latest`
    - `ghcr.io/bbrngit/rpa-frontend:latest`
    - `ghcr.io/bbrngit/rpa-sandbox:latest`
  - Pushes all images to GHCR
  - SSH's into the production server and runs `deploy.sh`

**Step 2 — `deploy.sh`** (on the production server, committed to repo):
  - `docker pull ghcr.io/bbrngit/rpa-backend:latest`
  - `docker pull ghcr.io/bbrngit/rpa-frontend:latest`
  - `docker pull ghcr.io/bbrngit/rpa-sandbox:latest`
  - `docker-compose up -d` (uses pre-pulled images — no build on server)

**Step 3 — `docker-compose.yml`** updated to reference GHCR images by tag (not build from source), so the server never needs the source code or Python installed

**Step 4 — GitHub secrets** configured:
  - `SSH_PRIVATE_KEY` — deploy key for the production server
  - `SERVER_IP` — production server address
  - `ALLOWED_ORIGINS` — CORS domain for the frontend

**Step 5 — GHCR image visibility** set to public (free, no auth needed to pull)

**Out:**
- No staging environment
- No rollback automation (manual rollback via `git checkout <tag>` + `deploy.sh`)

## Acceptance Criteria
- Merging a PR to `main` triggers the GitHub Actions workflow automatically
- Workflow runs `pytest` — failed tests block the build and deploy steps
- All three Docker images are built by GitHub Actions and pushed to `ghcr.io/bbrngit/rpa-*`
- Images are publicly visible on GHCR (no auth needed to pull)
- Production server pulls images from GHCR and restarts containers via `deploy.sh`
- Production is updated within 5 minutes of merge to `main`
- The production server has **no Python installed** — only Docker. The container is the environment.
- `deploy.sh` can be run manually on the server for emergency deploys (just pulls latest images and restarts)
- Rolling back is possible by pulling a specific image tag: `ghcr.io/bbrngit/rpa-backend:v0.2` + `docker-compose up -d`

## Dependencies
T2 must be complete (server must exist).
