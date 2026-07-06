# Switch to Production Environment
# This script stops test containers and starts production containers

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Switch to Production Environment" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Stop test containers
Write-Host "[INFO] Stopping test containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.hub.test.yml down

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Failed to stop test containers (may not be running)" -ForegroundColor Yellow
}

Write-Host ""

# Start production containers
Write-Host "[INFO] Starting production containers..." -ForegroundColor Green
docker-compose -f docker-compose.hub.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start production containers" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "[OK] Production environment started!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Production containers:" -ForegroundColor Cyan
Write-Host "  - tradingagents-mongodb" -ForegroundColor White
Write-Host "  - tradingagents-redis" -ForegroundColor White
Write-Host "  - tradingagents-backend" -ForegroundColor White
Write-Host "  - tradingagents-frontend" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Production data volumes:" -ForegroundColor Cyan
Write-Host "  - tradingagents_mongodb_data" -ForegroundColor White
Write-Host "  - tradingagents_redis_data" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Access URLs:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Check logs:" -ForegroundColor Yellow
Write-Host "  docker logs -f tradingagents-backend" -ForegroundColor Gray
Write-Host ""

