#!/bin/bash
#
# RPA - Update Script
# ===================
# Run: ./update.sh
#
# Pulls latest images and restarts
#

set -e

echo "Updating RPA..."

# Pull latest images
echo "Pulling latest images..."
docker compose pull

# Restart with new images
echo "Restarting services..."
docker compose down
docker compose up -d

echo "✅ RPA updated and running"
docker compose ps
