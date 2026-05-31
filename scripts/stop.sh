#!/usr/bin/env bash
# stop.sh — Tear down the local stack
set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/../infra/compose" && pwd)"

pushd "$COMPOSE_DIR" >/dev/null
docker compose -f compose.yml -f compose.dev.yml down -v
popd >/dev/null
echo "Stack stopped and volumes removed."
