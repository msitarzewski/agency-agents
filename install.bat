@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%install.ps1"
if %errorlevel% neq 0 (
  echo Installation failed.
  exit /b %errorlevel%
)

echo Installation completed.
exit /b 0
