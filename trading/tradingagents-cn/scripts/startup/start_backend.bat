@echo off
REM TradingAgents-CN Backend Launcher for Windows
REM 快速启动脚本

echo 🚀 TradingAgents-CN Backend Launcher
echo ==================================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM 检查app目录是否存在
if not exist "app" (
    echo ❌ app directory not found
    pause
    exit /b 1
)

echo ✅ Environment check passed
echo 🔄 Starting backend server...
echo --------------------------------------------------

REM 启动后端服务
python -m app

if errorlevel 1 (
    echo ❌ Failed to start server
    pause
    exit /b 1
)

echo 🛑 Server stopped
pause
