#!/bin/bash
#
# RPA - One-Command Startup Script
# ================================
# Just run: ./start.sh
#
# This script handles everything:
# - Checks dependencies
# - Logs into Docker
# - Pulls images
# - Starts RPA
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
USER="bbrngit"
IMAGES="rpa-backend rpa-frontend rpa-sandbox"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    RPA Quick Start                         ║${NC}"
echo -e "${BLUE}║              Recursive Pattern Agent                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# =============================================================================
# Step 1: Check Docker
# =============================================================================
echo -e "${YELLOW}[1/6] Checking Docker...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo ""
    echo "Install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo "Then run this script again."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo ""
    echo "Open Docker Desktop and wait for it to start."
    echo "Then run this script again."
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# =============================================================================
# Step 2: Setup Environment File
# =============================================================================
echo -e "${YELLOW}[2/6] Setting up environment...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from .env.example${NC}"
    else
        # Create minimal .env
        cat > .env << 'EOF'
SECRET_KEY=rpa-production-secret-change-me
ALLOWED_ORIGINS=http://localhost,http://localhost:80
SANDBOX_TIMEOUT=10
LOG_LEVEL=INFO
ENVIRONMENT=production
HUGGINGFACE_TOKEN=
EOF
        echo -e "${GREEN}✅ Created .env file${NC}"
    fi
else
    echo -e "${GREEN}✅ .env already exists${NC}"
fi

# =============================================================================
# Step 3: Docker Login
# =============================================================================
echo -e "${YELLOW}[3/6] Authenticating with GitHub Container Registry...${NC}"

# Check if we can pull without login (images might be public)
if docker pull ${REGISTRY}/${USER}/rpa-backend:latest &> /dev/null; then
    echo -e "${GREEN}✅ Already authenticated (images accessible)${NC}"
else
    # Need to login
    TOKEN=""

    # Try to get token from .env
    if [ -f ".env" ]; then
        TOKEN=$(grep -E "^GITHUB_TOKEN=" .env 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    fi

    # Try to get from environment variable
    if [ -z "$TOKEN" ]; then
        TOKEN="${GITHUB_TOKEN:-}"
    fi

    # If still no token, prompt user
    if [ -z "$TOKEN" ]; then
        echo ""
        echo -e "${YELLOW}GitHub authentication required to pull Docker images.${NC}"
        echo ""
        echo "You need a GitHub Personal Access Token with 'read:packages' scope."
        echo "Create one at: https://github.com/settings/tokens/new"
        echo ""
        echo -n "Enter your GitHub token (input hidden): "
        read -s TOKEN
        echo ""

        if [ -z "$TOKEN" ]; then
            echo -e "${RED}❌ No token provided. Cannot continue.${NC}"
            exit 1
        fi
    fi

    # Login
    echo "$TOKEN" | docker login ${REGISTRY} -u ${USER} --password-stdin 2> /dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Logged in to GitHub Container Registry${NC}"
    else
        echo -e "${RED}❌ Login failed. Check your token.${NC}"
        echo ""
        echo "Your token needs 'read:packages' scope."
        echo "Create one at: https://github.com/settings/tokens/new"
        exit 1
    fi
fi

# =============================================================================
# Step 4: Pull Docker Images
# =============================================================================
echo -e "${YELLOW}[4/6] Pulling Docker images (this may take a few minutes)...${NC}"

for IMAGE in $IMAGES; do
    echo -n "  Pulling ${IMAGE}... "
    if docker pull ${REGISTRY}/${USER}/${IMAGE}:latest &> /dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        echo -e "${RED}Failed to pull ${IMAGE}${NC}"
        exit 1
    fi
done

# =============================================================================
# Step 5: Start Services
# =============================================================================
echo -e "${YELLOW}[5/6] Starting RPA services...${NC}"

# Stop any existing containers
docker compose down &> /dev/null || true

# Start services
docker compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start services${NC}"
    echo ""
    echo "Check logs with: docker compose logs"
    exit 1
fi

echo -e "${GREEN}✅ Services started${NC}"

# =============================================================================
# Step 6: Wait for Health Checks
# =============================================================================
echo -e "${YELLOW}[6/6] Waiting for services to be ready...${NC}"

MAX_WAIT=60
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost/api/status &> /dev/null; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo -n "."
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠ Backend health check timed out (may still be starting)${NC}"
fi

# =============================================================================
# Done!
# =============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  🎉 RPA is Running!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Web UI:${NC}    http://localhost"
echo -e "  ${BLUE}API:${NC}       http://localhost/api/status"
echo ""
echo "Commands:"
echo "  View logs:    docker compose logs -f"
echo "  Stop:         docker compose down"
echo "  Restart:      docker compose restart"
echo "  Status:       docker compose ps"
echo ""

# Try to open browser
if command -v open &> /dev/null; then
    sleep 2
    open http://localhost 2>/dev/null || true
fi
