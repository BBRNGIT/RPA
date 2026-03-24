#!/bin/bash
#
# RPA Deployment Script
# 
# Pulls latest Docker images from GHCR and restarts containers.
# Can be run on a production server or locally.
#
# Usage:
#   ./deploy.sh              # Deploy latest
#   ./deploy.sh v1.2.3       # Deploy specific version
#
# Prerequisites:
#   - Docker installed
#   - docker-compose.yml in the same directory
#   - .env file with configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
IMAGE_PREFIX="bbrngit/rpa"
VERSION="${1:-latest}"
COMPOSE_FILE="docker-compose.yml"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  RPA Deployment - v${VERSION}${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

# Check docker-compose.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: $COMPOSE_FILE not found${NC}"
    echo "Please run this script from the RPA directory"
    exit 1
fi

# Create .env from .env.example if not exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env with your configuration${NC}"
    else
        echo -e "${YELLOW}Warning: No .env file found, using defaults${NC}"
    fi
fi

# Pull latest images
echo -e "${GREEN}Pulling Docker images...${NC}"
echo ""

for SERVICE in backend frontend sandbox; do
    IMAGE="${REGISTRY}/${IMAGE_PREFIX}-${SERVICE}:${VERSION}"
    echo -e "  ${BLUE}Pulling ${IMAGE}...${NC}"
    docker pull "$IMAGE"
done

echo ""
echo -e "${GREEN}Images pulled successfully!${NC}"
echo ""

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

# Start containers
echo -e "${GREEN}Starting containers...${NC}"
docker-compose up -d || docker compose up -d

# Wait for health checks
echo ""
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Show status
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null

echo ""
echo -e "Access the application:"
echo -e "  ${BLUE}Web UI:${NC}     http://localhost"
echo -e "  ${BLUE}API Docs:${NC}   http://localhost:8000/docs"
echo -e "  ${BLUE}WebSocket:${NC}  ws://localhost:8000/ws"
echo ""
echo -e "Useful commands:"
echo -e "  ${YELLOW}View logs:${NC}    docker-compose logs -f"
echo -e "  ${YELLOW}Stop:${NC}         docker-compose down"
echo -e "  ${YELLOW}Restart:${NC}      docker-compose restart"
echo ""
