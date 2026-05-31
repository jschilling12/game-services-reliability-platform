#!/usr/bin/env bash
# start.sh — Bring up the full local stack
set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/../infra/compose" && pwd)"

pushd "$COMPOSE_DIR" >/dev/null
docker compose -f compose.yml -f compose.dev.yml up -d
popd >/dev/null

echo ""
echo "Stack is up:"
echo "  Gateway     -> http://localhost:80"
echo "  Prometheus  -> http://localhost:9090"
echo "  Grafana     -> http://localhost:3000  (admin / see .env)"
echo "  Jaeger UI   -> http://localhost:16686"
