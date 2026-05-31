# bootstrap.ps1 - First-time environment setup
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ComposeDir = Resolve-Path "$PSScriptRoot\..\infra\compose"

Write-Host "==> Checking required tools..."
foreach ($cmd in @('docker', 'docker-compose')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "ERROR: '$cmd' not found. Install Docker Desktop and try again."
        exit 1
    }
}

Write-Host "==> Copying .env.example -> .env (if not present)..."
$envFile = Join-Path $ComposeDir '.env'
$envExample = Join-Path $ComposeDir '.env.example'
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "    Created $envFile - edit it before starting services."
}

Write-Host "==> Building all images..."
docker compose -f (Join-Path $ComposeDir 'docker-compose.yml') build

Write-Host ""
Write-Host "Bootstrap complete. Run 'scripts\start.ps1' to bring up the stack."