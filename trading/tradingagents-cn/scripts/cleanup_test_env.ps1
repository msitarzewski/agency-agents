# Cleanup Test Environment
# This script removes test containers, volumes, and directories

param(
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Red
Write-Host "WARNING: Cleanup Test Environment" -ForegroundColor Red
Write-Host "======================================================================" -ForegroundColor Red
Write-Host ""
Write-Host "[WARN] This will remove:" -ForegroundColor Yellow
Write-Host "  - Test containers (tradingagents-*-test)" -ForegroundColor White
Write-Host "  - Test data volumes (tradingagents_test_*)" -ForegroundColor White
Write-Host "  - Test directories (logs-test/, config-test/, data-test/)" -ForegroundColor White
Write-Host ""

if (-not $Force) {
    $Confirmation = Read-Host "Confirm cleanup? (yes/no)"
    if ($Confirmation -ne "yes") {
        Write-Host "[INFO] Cleanup cancelled" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "[INFO] Starting cleanup..." -ForegroundColor Green
Write-Host ""

# Stop and remove test containers
Write-Host "[INFO] Stopping and removing test containers..." -ForegroundColor Cyan
docker-compose -f docker-compose.hub.test.yml down -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Test containers removed" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Failed to remove test containers" -ForegroundColor Yellow
}

Write-Host ""

# Remove test directories
Write-Host "[INFO] Removing test directories..." -ForegroundColor Cyan

$TestDirs = @("logs-test", "config-test", "data-test")

foreach ($Dir in $TestDirs) {
    if (Test-Path $Dir) {
        Write-Host "  Removing: $Dir" -ForegroundColor Gray
        Remove-Item -Path $Dir -Recurse -Force
        Write-Host "  [OK] Removed: $Dir" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] Directory does not exist: $Dir" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "[OK] Test environment cleaned up!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Remaining volumes:" -ForegroundColor Cyan
docker volume ls --format "table {{.Name}}\t{{.Driver}}" | Select-String "tradingagents"
Write-Host ""

