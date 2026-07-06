@echo off
chcp 65001 >nul
REM TradingAgents Docker服务启动脚本
REM 启动MongoDB、Redis和Redis Commander

echo ========================================
echo TradingAgents Docker Service Startup
echo ========================================

REM 检查Docker是否运行
echo Checking Docker service status...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running or not installed
    echo Please start Docker Desktop first
    pause
    exit /b 1
)
echo [OK] Docker service is running

echo.
echo Starting database services...

REM 启动MongoDB
echo Starting MongoDB...
docker run -d ^
    --name tradingagents-mongodb ^
    -p 27017:27017 ^
    -e MONGO_INITDB_ROOT_USERNAME=admin ^
    -e MONGO_INITDB_ROOT_PASSWORD=tradingagents123 ^
    -e MONGO_INITDB_DATABASE=tradingagents ^
    -v mongodb_data:/data/db ^
    --restart unless-stopped ^
    mongo:4.4

if %errorlevel% equ 0 (
    echo [OK] MongoDB started successfully - Port: 27017
) else (
    echo [WARN] MongoDB may already be running or failed to start
)

REM 启动Redis
echo Starting Redis...
docker run -d ^
    --name tradingagents-redis ^
    -p 6379:6379 ^
    -v redis_data:/data ^
    --restart unless-stopped ^
    redis:latest redis-server --appendonly yes --requirepass tradingagents123

if %errorlevel% equ 0 (
    echo [OK] Redis started successfully - Port: 6379
) else (
    echo [WARN] Redis may already be running or failed to start
)

REM 等待服务启动
echo Waiting for services to start...
timeout /t 5 /nobreak >nul

REM 启动Redis Commander (可选的Redis管理界面)
echo Starting Redis Commander...
docker run -d ^
    --name tradingagents-redis-commander ^
    -p 8081:8081 ^
    -e REDIS_HOSTS=local:tradingagents-redis:6379:0:tradingagents123 ^
    --link tradingagents-redis:redis ^
    --restart unless-stopped ^
    rediscommander/redis-commander:latest

if %errorlevel% equ 0 (
    echo [OK] Redis Commander started - Access: http://localhost:8081
) else (
    echo [WARN] Redis Commander may already be running or failed to start
)

echo.
echo Checking service status...
docker ps --filter "name=tradingagents-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo ========================================
echo Docker services startup completed!
echo ========================================
echo.
echo MongoDB:
echo    - Connection: mongodb://admin:tradingagents123@localhost:27017/tradingagents
echo    - Port: 27017
echo    - Username: admin
echo    - Password: tradingagents123
echo.
echo Redis:
echo    - Connection: redis://localhost:6379
echo    - Port: 6379
echo    - Password: tradingagents123
echo.
echo Redis Commander:
echo    - Web Interface: http://localhost:8081
echo.
echo Tips:
echo    - Use stop_docker_services.bat to stop all services
echo    - Use docker logs [container_name] to view logs
echo    - Data will be persisted in Docker volumes
echo.

pause
