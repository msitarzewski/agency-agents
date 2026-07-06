@echo off
chcp 65001 >nul

echo ========================================
echo TradingAgents Docker Services (Alt Ports)
echo ========================================

echo Checking Docker...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker not running
    pause
    exit /b 1
)

echo Cleaning up existing containers...
docker stop tradingagents-mongodb tradingagents-redis tradingagents-redis-commander 2>nul
docker rm tradingagents-mongodb tradingagents-redis tradingagents-redis-commander 2>nul

echo Starting MongoDB on port 27018...
docker run -d --name tradingagents-mongodb -p 27018:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=tradingagents123 -e MONGO_INITDB_DATABASE=tradingagents -v tradingagents_mongodb_data:/data/db --restart unless-stopped mongo:4.4

echo Starting Redis on port 6380...
docker run -d --name tradingagents-redis -p 6380:6379 -v tradingagents_redis_data:/data --restart unless-stopped redis:latest redis-server --appendonly yes --requirepass tradingagents123

echo Waiting 10 seconds for services to start...
timeout /t 10 /nobreak >nul

echo Starting Redis Commander on port 8082...
docker run -d --name tradingagents-redis-commander -p 8082:8081 -e REDIS_HOSTS=local:tradingagents-redis:6379:0:tradingagents123 --link tradingagents-redis:redis --restart unless-stopped rediscommander/redis-commander:latest

echo.
echo Service Status:
docker ps --filter "name=tradingagents-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo ========================================
echo Services Started with Alternative Ports!
echo ========================================
echo MongoDB: localhost:27018
echo Redis: localhost:6380  
echo Redis Commander: http://localhost:8082
echo.
echo Username: admin
echo Password: tradingagents123
echo.
echo Next Steps:
echo 1. Update .env file with new ports:
echo    MONGODB_PORT=27018
echo    REDIS_PORT=6380
echo 2. Run database initialization:
echo    python scripts/init_database.py
echo 3. Start web application:
echo    python start_web.py
echo.

pause
