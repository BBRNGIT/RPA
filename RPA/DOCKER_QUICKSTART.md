# RPA Quick Start - Run Locally with Docker

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- Internet connection (to pull images)

## One-Time Setup

### Step 1: Open Terminal/Command Prompt

**Windows**: PowerShell or Command Prompt  
**Mac**: Terminal  
**Linux**: Terminal

### Step 2: Clone the Repository

```bash
git clone https://github.com/BBRNGIT/RPA.git
cd RPA
```

### Step 3: Configure Environment

```bash
# Copy example config
cp .env.example .env

# (Optional) Edit with your settings
# nano .env  # or use any text editor
```

### Step 4: Run

```bash
# Pull and start everything
docker-compose pull
docker-compose up
```

### Step 5: Open in Browser

```
http://localhost
```

---

## Common Commands

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Update to latest version
docker-compose pull && docker-compose up -d

# Restart
docker-compose restart
```

---

## Troubleshooting

### Port 80 already in use

Edit `docker-compose.yml` and change:
```yaml
ports:
  - "8080:80"  # Changed from 80:80
```
Then access via `http://localhost:8080`

### Docker not found

Make sure Docker Desktop is running (check system tray/menu bar)

### Permission denied

On Linux/Mac, you may need:
```bash
sudo docker-compose up
```

---

## What's Running

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 80 | Web UI (Nginx + Next.js) |
| Backend | 8000 | FastAPI REST + WebSocket |
| Sandbox | - | Isolated Python executor (no network) |

---

## Data Storage

All data is stored in Docker volumes:
- `rpa-data` - LTM patterns
- `rpa-memory` - Memory state

To backup:
```bash
docker run --rm -v rpa-data:/data -v $(pwd):/backup alpine tar czf /backup/rpa-data-backup.tar.gz /data
```

---

## Need Help?

1. Check logs: `docker-compose logs -f`
2. Restart: `docker-compose restart`
3. Full reset: `docker-compose down -v && docker-compose up`
