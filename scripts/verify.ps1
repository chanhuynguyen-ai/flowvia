# Run start.ps1 first. Tests use their own SQLite file, never the demo database.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
docker compose exec -T api python -m pytest -o addopts= -q
if ($LASTEXITCODE -ne 0) { throw "Backend verification failed." }
docker compose exec -T api alembic check
if ($LASTEXITCODE -ne 0) { throw "Migration metadata differs from the running database." }
docker compose build web
if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck/build failed." }
Write-Host "Backend tests, migration metadata and frontend build passed." -ForegroundColor Green
Write-Host "Complete the browser and live-provider acceptance steps in docs/11_LITE_RUNTIME.md."
