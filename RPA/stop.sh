#!/bin/bash
#
# RPA - Stop Script
# =================
# Run: ./stop.sh
#

echo "Stopping RPA..."
docker compose down
echo "✅ RPA stopped"
