# stop.ps1 — Tear down the local stack
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ComposeFile = Resolve-Path "$PSScriptRoot\..\infra\compose\docker-compose.yml"

docker compose -f $ComposeFile down -v
Write-Host "Stack stopped and volumes removed."
