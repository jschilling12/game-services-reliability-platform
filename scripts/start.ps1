# start.ps1 — Bring up the full local stack
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ComposeFile = Resolve-Path "$PSScriptRoot\..\infra\compose\docker-compose.yml"

docker compose -f $ComposeFile up -d

Write-Host ""
Write-Host "Stack is up:"
Write-Host "  Gateway     -> http://localhost:80"
Write-Host "  Prometheus  -> http://localhost:9090"
Write-Host "  Grafana     -> http://localhost:3000  (admin / see .env)"
Write-Host "  Jaeger UI   -> http://localhost:16686"
