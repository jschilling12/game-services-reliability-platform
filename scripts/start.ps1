# start.ps1 — Bring up the full local stack
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ComposeDir = Resolve-Path "$PSScriptRoot\..\infra\compose"

Push-Location $ComposeDir
try {
    docker compose -f compose.yml -f compose.dev.yml up -d
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Stack is up:"
Write-Host "  Gateway     -> http://localhost:80"
Write-Host "  Prometheus  -> http://localhost:9090"
Write-Host "  Grafana     -> http://localhost:3000  (admin / see .env)"
Write-Host "  Jaeger UI   -> http://localhost:16686"
