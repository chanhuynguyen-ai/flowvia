$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Install Docker Desktop with Linux containers, then try again."
}
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Start Docker Desktop before running Flowvia." }
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw "Compose configuration is invalid." }
Write-Host "Building Flowvia and waiting for healthy services..." -ForegroundColor Cyan
docker compose up -d --build --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) {
    docker compose logs --tail 60 api worker web
    throw "Flowvia startup failed. Review the service logs above."
}
docker compose ps
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect services." }
Write-Host "Web: http://localhost:3000" -ForegroundColor Green
Write-Host "API: http://localhost:8000/docs"
Write-Host "Owner: owner@flowvia.local / FlowviaOwner123!"
Write-Host "Choose Test workflow in Dry run mode, then review and approve the action."
