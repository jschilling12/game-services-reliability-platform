# bootstrap.ps1 - First-time environment setup
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ComposeDir = Resolve-Path "$PSScriptRoot\..\infra\compose"

Write-Host "==> Checking required tools..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: 'docker' not found. Install Docker Desktop and try again."
    exit 1
}

docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Docker Compose plugin not available. Install or update Docker Desktop and try again."
    exit 1
}

Write-Host "==> Copying .env.example -> .env (if not present)..."
$envFile = Join-Path $ComposeDir '.env'
$envExample = Join-Path $ComposeDir '.env.example'
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "    Created $envFile - edit it before starting services."
}

Write-Host "==> Building all images..."
Push-Location $ComposeDir
try {
    docker compose -f compose.yml -f compose.dev.yml build
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Bootstrap complete. Run 'scripts\start.ps1' to bring up the stack."
