#!/bin/bash
# RPA Docker Login Script
# Run this once to authenticate with GitHub Container Registry

set -e

echo "=== RPA Docker Login ==="
echo ""
echo "This script will authenticate Docker with GitHub Container Registry."
echo "You need a GitHub Personal Access Token with 'read:packages' scope."
echo ""

# Check if already logged in
if docker pull ghcr.io/bbrngit/rpa-backend:latest &>/dev/null; then
    echo "✅ Already authenticated! You can pull images without logging in."
    exit 0
fi

# Prompt for token
echo "Enter your GitHub Personal Access Token (or press Enter to use saved token):"
read -s TOKEN

if [ -z "$TOKEN" ]; then
    # Try to use token from .env
    if [ -f ".env" ]; then
        TOKEN=$(grep GITHUB_TOKEN .env 2>/dev/null | cut -d'=' -f2)
    fi
fi

if [ -z "$TOKEN" ]; then
    echo ""
    echo "❌ No token provided. Create one at: https://github.com/settings/tokens/new"
    echo "   Required scopes: read:packages (and write:packages if you want to push)"
    exit 1
fi

# Login
echo ""
echo "Logging in to ghcr.io..."
echo "$TOKEN" | docker login ghcr.io -u BBRNGIT --password-stdin

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Login successful!"
    echo ""
    echo "Now run: docker compose pull && docker compose up -d"
else
    echo ""
    echo "❌ Login failed. Check your token."
    exit 1
fi
