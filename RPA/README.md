# RPA - Quick Start

## One Command Setup

```bash
./start.sh
```

That's it. The script handles:
- ✅ Docker check
- ✅ GitHub authentication
- ✅ Image download
- ✅ Service startup
- ✅ Opens browser

## Other Commands

| Command | Description |
|---------|-------------|
| `./start.sh` | Start RPA |
| `./stop.sh` | Stop RPA |
| `./update.sh` | Update to latest version |
| `docker compose logs -f` | View logs |
| `docker compose ps` | Check status |

## First Time Setup

On first run, you'll need a GitHub token with `read:packages` scope.

1. Go to: https://github.com/settings/tokens/new
2. Name it "RPA Docker"
3. Select scope: `read:packages`
4. Click "Generate token"
5. Copy the token
6. Paste when prompted by `./start.sh`

## Requirements

- Docker Desktop installed and running
- macOS / Linux / Windows WSL2

## Troubleshooting

**Docker not running:**
```
Open Docker Desktop, wait for it to start, then run ./start.sh again
```

**Login failed:**
```
Make sure your token has 'read:packages' scope
Create new token: https://github.com/settings/tokens/new
```

**Port 80 in use:**
```
sudo lsof -i :80  # Find what's using port 80
docker compose down  # Stop any existing RPA
./start.sh  # Start fresh
```
