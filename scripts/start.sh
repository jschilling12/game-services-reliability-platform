#!/usr/bin/env bash
# start.sh — Bring up the full local stack
set -euo pipefail

COMPOSE_FILE="$(cd "$(dirname "$0")/../infra/compose" && pwd)/docker-compose.yml"

docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "Stack is up:"
echo "  Gateway     -> http://localhost:80"
echo "  Prometheus  -> http://localhost:9090"
echo "  Grafana     -> http://localhost:3000  (admin / see .env)"
echo "  Jaeger UI   -> http://localhost:16686"
