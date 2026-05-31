# scan.ps1 — Run Trivy vulnerability scan against all service images
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TrivyConfig = Resolve-Path "$PSScriptRoot\..\security\trivy\trivy.yaml"
$Services    = @('matchmaking-api', 'worker')
$Failed      = $false

foreach ($svc in $Services) {
    Write-Host "==> Scanning game-backend-platform/${svc}:dev"
    trivy image --config $TrivyConfig "game-backend-platform/${svc}:dev"
    if ($LASTEXITCODE -ne 0) { $Failed = $true }
}

if ($Failed) {
    Write-Host ""
    Write-Error "One or more scans reported vulnerabilities."
    exit 1
}

Write-Host ""
Write-Host "All scans passed."
