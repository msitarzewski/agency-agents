@echo off
REM TradingAgents Docker Compose启动脚本
REM 使用Docker Compose管理所有服务

echo ========================================
echo TradingAgents Docker Compose启动脚本
echo ========================================

REM 检查Docker Compose是否可用
echo 检查Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安装或不可用
    echo 请安装Docker Desktop或Docker Compose
    pause
    exit /b 1
)
echo ✅ Docker Compose可用

echo.
echo 🚀 启动TradingAgents服务栈...

REM 启动核心服务 (MongoDB, Redis, Redis Commander)
echo 📊 启动核心数据库服务...
docker-compose up -d mongodb redis redis-commander

if %errorlevel% equ 0 (
    echo ✅ 核心服务启动成功
) else (
    echo ❌ 核心服务启动失败
    pause
    exit /b 1
)

REM 等待服务启动
echo ⏳ 等待服务启动和健康检查...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 📋 检查服务状态...
docker-compose ps

echo.
echo 🔍 等待健康检查完成...
:healthcheck_loop
docker-compose ps --filter "health=healthy" | findstr "tradingagents" >nul
if %errorlevel% neq 0 (
    echo ⏳ 等待服务健康检查...
    timeout /t 5 /nobreak >nul
    goto healthcheck_loop
)

echo ✅ 所有服务健康检查通过

echo.
echo 📊 服务访问信息:
echo ========================================
echo 🗄️ MongoDB:
echo    - 连接地址: mongodb://admin:tradingagents123@localhost:27017/tradingagents
echo    - 端口: 27017
echo    - 用户名: admin
echo    - 密码: tradingagents123
echo.
echo 📦 Redis:
echo    - 连接地址: redis://localhost:6379
echo    - 端口: 6379
echo    - 密码: tradingagents123
echo.
echo 🖥️ 管理界面:
echo    - Redis Commander: http://localhost:8081
echo    - Mongo Express: http://localhost:8082 (可选，需要启动)
echo.

REM 询问是否启动管理界面
set /p start_management="是否启动Mongo Express管理界面? (y/N): "
if /i "%start_management%"=="y" (
    echo 🖥️ 启动Mongo Express...
    docker-compose --profile management up -d mongo-express
    if %errorlevel% equ 0 (
        echo ✅ Mongo Express启动成功: http://localhost:8082
        echo    用户名: admin, 密码: tradingagents123
    ) else (
        echo ❌ Mongo Express启动失败
    )
)

echo.
echo 💡 管理命令:
echo ========================================
echo 查看日志: docker-compose logs [服务名]
echo 停止服务: docker-compose down
echo 重启服务: docker-compose restart [服务名]
echo 查看状态: docker-compose ps
echo 进入容器: docker-compose exec [服务名] bash
echo.
echo 🔧 数据库初始化:
echo 运行初始化脚本: python scripts/init_database.py
echo.
echo 🌐 启动Web应用:
echo python start_web.py
echo.

echo ========================================
echo 🎉 TradingAgents服务栈启动完成！
echo ========================================

pause
