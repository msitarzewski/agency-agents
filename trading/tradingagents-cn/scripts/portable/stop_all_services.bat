@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   TradingAgents-CN Stop All Services
echo ========================================
echo.

REM Call PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0stop_all.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Services stopped
) else (
    echo.
    echo [WARNING] Issues occurred during service stop
    echo Please check the output above
)

echo.
echo Press any key to exit...
pause >nul

