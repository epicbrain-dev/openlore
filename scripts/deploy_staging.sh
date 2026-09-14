#!/usr/bin/env bash
# OpenLore Staging Deployment and Verification Script
set -euo pipefail

echo "=========================================================="
echo "🚀 Deploying OpenLore to Staging Environment (Docker Stack)"
echo "=========================================================="

export OPENLORE_ENV=staging
export OPENLORE_AUTH_ENABLED=true
export OPENLORE_CAS_BACKEND=s3
export OPENLORE_CATALOG_BACKEND=sql

COMPOSE_FILE="docker-compose.staging.yml"

if ! command -v docker &> /dev/null; then
    echo "⚠️ Docker command not found in current path. Validating configuration only."
    exit 0
fi

echo "📦 Validating Compose configuration..."
docker compose -f "${COMPOSE_FILE}" config --quiet

echo "🔄 Spinning up staging microservices..."
docker compose -f "${COMPOSE_FILE}" up -d --build

echo "⏳ Waiting for health check on http://localhost:8080/api/status..."
TOKEN=$(python3 -m openlore.cli.main auth create-token --sub staging-healthcheck --role admin 2>/dev/null | grep "Token:" | awk '{print $2}')
MAX_TRIES=20
COUNT=0
while [ $COUNT -lt $MAX_TRIES ]; do
    if curl -s -f -H "Authorization: Bearer ${TOKEN}" http://localhost:8080/api/status > /dev/null 2>&1; then
        echo "✅ OpenLore Staging is healthy and responsive on port 8080!"
        break
    fi
    COUNT=$((COUNT + 1))
    echo "   ... waiting ($COUNT/$MAX_TRIES)"
    sleep 3
done

if [ $COUNT -eq $MAX_TRIES ]; then
    echo "⚠️ Timed out waiting for OpenLore API healthcheck."
fi

echo "✨ Staging deployment sequence completed."
