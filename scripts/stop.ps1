# stop.ps1 — Tear down the local stack
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ComposeDir = Resolve-Path "$PSScriptRoot\..\infra\compose"

Push-Location $ComposeDir
try {
    docker compose -f compose.yml -f compose.dev.yml down -v
}
finally {
    Pop-Location
}
Write-Host "Stack stopped and volumes removed."
