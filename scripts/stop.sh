#!/usr/bin/env bash
# stop.sh — Tear down the local stack
set -euo pipefail

COMPOSE_FILE="$(cd "$(dirname "$0")/../infra/compose" && pwd)/docker-compose.yml"

docker compose -f "$COMPOSE_FILE" down -v
echo "Stack stopped and volumes removed."
