# Switch to Test Environment
# This script stops production containers and starts test containers

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Switch to Test Environment" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Stop production containers
Write-Host "[INFO] Stopping production containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.hub.yml down

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Failed to stop production containers (may not be running)" -ForegroundColor Yellow
}

Write-Host ""

# Start test containers
Write-Host "[INFO] Starting test containers..." -ForegroundColor Green
docker-compose -f docker-compose.hub.test.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start test containers" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "[OK] Test environment started!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Test containers:" -ForegroundColor Cyan
Write-Host "  - tradingagents-mongodb-test" -ForegroundColor White
Write-Host "  - tradingagents-redis-test" -ForegroundColor White
Write-Host "  - tradingagents-backend-test" -ForegroundColor White
Write-Host "  - tradingagents-frontend-test" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Test data volumes:" -ForegroundColor Cyan
Write-Host "  - tradingagents_test_mongodb_data" -ForegroundColor White
Write-Host "  - tradingagents_test_redis_data" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Test directories:" -ForegroundColor Cyan
Write-Host "  - logs-test/" -ForegroundColor White
Write-Host "  - config-test/" -ForegroundColor White
Write-Host "  - data-test/" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Access URLs:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Check logs:" -ForegroundColor Yellow
Write-Host "  docker logs -f tradingagents-backend-test" -ForegroundColor Gray
Write-Host ""
Write-Host "[INFO] Switch back to production:" -ForegroundColor Yellow
Write-Host "  .\scripts\switch_to_prod_env.ps1" -ForegroundColor Gray
Write-Host ""

