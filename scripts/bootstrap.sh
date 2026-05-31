#!/usr/bin/env bash
# bootstrap.sh — First-time environment setup
set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/../infra/compose" && pwd)"

echo "==> Checking required tools..."
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found"; exit 1; }
docker compose version >/dev/null 2>&1 || {
  echo "ERROR: Docker Compose plugin not available. Install or update Docker Desktop and try again."
  exit 1
}

echo "==> Copying .env.example -> .env (if not present)..."
if [[ ! -f "$COMPOSE_DIR/.env" ]]; then
  cp "$COMPOSE_DIR/.env.example" "$COMPOSE_DIR/.env"
  echo "    Created $COMPOSE_DIR/.env — edit it before starting services."
fi

echo "==> Building all images..."
pushd "$COMPOSE_DIR" >/dev/null
docker compose -f compose.yml -f compose.dev.yml build
popd >/dev/null

echo ""
echo "Bootstrap complete. Run 'scripts/start.sh' to bring up the stack."
