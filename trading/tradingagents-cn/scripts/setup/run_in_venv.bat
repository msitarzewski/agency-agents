@echo off
REM 在虚拟环境中运行Python脚本的通用脚本

if "%1"=="" (
    echo 用法: run_in_venv.bat ^<python_script^> [参数...]
    echo 示例: run_in_venv.bat scripts\setup\initialize_system.py
    pause
    exit /b 1
)

echo 🐍 在虚拟环境中运行: %*
echo ================================

REM 检查虚拟环境
if not exist "env\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在: env\Scripts\activate.bat
    echo 💡 请先创建虚拟环境:
    echo    python -m venv env
    pause
    exit /b 1
)

REM 激活虚拟环境并运行脚本
call env\Scripts\activate.bat && python %*

echo.
echo 🎯 脚本执行完成
pause
