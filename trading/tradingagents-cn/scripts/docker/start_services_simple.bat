@echo off
chcp 65001 >nul

echo ========================================
echo TradingAgents Docker Services
echo ========================================

echo Checking Docker...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker not running
    pause
    exit /b 1
)

echo Starting MongoDB...
docker run -d --name tradingagents-mongodb -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=tradingagents123 -e MONGO_INITDB_DATABASE=tradingagents -v mongodb_data:/data/db --restart unless-stopped mongo:4.4

echo Starting Redis...
docker run -d --name tradingagents-redis -p 6379:6379 -v redis_data:/data --restart unless-stopped redis:latest redis-server --appendonly yes --requirepass tradingagents123

echo Waiting 5 seconds...
timeout /t 5 /nobreak >nul

echo Starting Redis Commander...
docker run -d --name tradingagents-redis-commander -p 8081:8081 -e REDIS_HOSTS=local:tradingagents-redis:6379:0:tradingagents123 --link tradingagents-redis:redis --restart unless-stopped rediscommander/redis-commander:latest

echo.
echo Service Status:
docker ps --filter "name=tradingagents-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo ========================================
echo Services Started!
echo ========================================
echo MongoDB: localhost:27017
echo Redis: localhost:6379  
echo Redis Commander: http://localhost:8081
echo.
echo Username: admin
echo Password: tradingagents123
echo.

pause
