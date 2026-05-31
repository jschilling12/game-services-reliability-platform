#!/usr/bin/env bash
# bootstrap.sh — First-time environment setup
set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/../infra/compose" && pwd)"

echo "==> Checking required tools..."
for cmd in docker docker-compose; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: $cmd not found"; exit 1; }
done

echo "==> Copying .env.example -> .env (if not present)..."
if [[ ! -f "$COMPOSE_DIR/.env" ]]; then
  cp "$COMPOSE_DIR/.env.example" "$COMPOSE_DIR/.env"
  echo "    Created $COMPOSE_DIR/.env — edit it before starting services."
fi

echo "==> Building all images..."
docker compose -f "$COMPOSE_DIR/docker-compose.yml" build

echo ""
echo "Bootstrap complete. Run 'scripts/start.sh' to bring up the stack."
