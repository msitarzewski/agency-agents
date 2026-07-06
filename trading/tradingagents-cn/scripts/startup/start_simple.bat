@echo off
REM TradingAgents-CN 简化启动脚本 (Windows)
REM 用于日常快速启动应用

echo.
echo ========================================
echo   TradingAgents-CN 快速启动
echo ========================================
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在
    echo.
    echo 请先运行安装脚本:
    echo   powershell -ExecutionPolicy Bypass -File scripts\easy_install.ps1
    echo.
    pause
    exit /b 1
)

REM 激活虚拟环境
echo [1/3] 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 检查配置文件
if not exist ".env" (
    echo [警告] 配置文件不存在
    echo.
    echo 请先运行安装脚本或手动创建 .env 文件
    echo.
    pause
    exit /b 1
)

REM 启动应用
echo [2/3] 启动Web应用...
echo.
echo ========================================
echo   应用正在启动...
echo   浏览器将自动打开 http://localhost:8501
echo ========================================
echo.
echo 按 Ctrl+C 停止应用
echo.

python start_web.py

echo.
echo [3/3] 应用已停止
pause

