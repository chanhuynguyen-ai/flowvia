$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python scripts/validate_blueprint.py

Push-Location apps/api
try {
    python -m pytest
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Backend and blueprint checks passed."
Write-Host "Frontend check (requires npm dependencies):"
Write-Host "  cd apps/web"
Write-Host "  npm install"
Write-Host "  npm run typecheck"
Write-Host "  npm run build"
