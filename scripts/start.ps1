$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Flowvia Local Development" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker CLI was not found." -ForegroundColor Red
    exit 1
}

docker info *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Engine is not running." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path ".env")) {
    if (-not (Test-Path ".env.example")) {
        Write-Host "ERROR: .env.example was not found." -ForegroundColor Red
        exit 1
    }

    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example." -ForegroundColor Green
}

Write-Host "Validating docker-compose.yml..." -ForegroundColor Yellow

docker compose config --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: docker-compose.yml is invalid." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Compose configuration: OK" -ForegroundColor Green

Write-Host ""
Write-Host "Building and starting Flowvia..." -ForegroundColor Yellow

docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Docker Compose failed to start Flowvia." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Waiting for services..." -ForegroundColor Yellow

Start-Sleep -Seconds 3

docker compose ps

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Unable to inspect Flowvia services." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host " Flowvia local environment started" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Web:       http://localhost:3000"
Write-Host "API docs:  http://localhost:8000/docs"
Write-Host "Health:    http://localhost:8000/health"
Write-Host "Ready:     http://localhost:8000/ready"
Write-Host "MinIO:     http://localhost:9001"
Write-Host ""