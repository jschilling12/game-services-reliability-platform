#!/usr/bin/env bash
# scan.sh — Run Trivy vulnerability scan against all service images
set -euo pipefail

SERVICES=(matchmaking-api worker)
TRIVY_CONFIG="$(cd "$(dirname "$0")/../security/trivy" && pwd)/trivy.yaml"
FAILED=0

for svc in "${SERVICES[@]}"; do
  echo "==> Scanning game-backend-platform/${svc}:dev"
  trivy image \
    --config "$TRIVY_CONFIG" \
    "game-backend-platform/${svc}:dev" || FAILED=1
done

if [[ $FAILED -ne 0 ]]; then
  echo ""
  echo "One or more scans reported vulnerabilities."
  exit 1
fi

echo ""
echo "All scans passed."
