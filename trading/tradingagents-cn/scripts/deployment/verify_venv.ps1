# ============================================================================
# Verify Virtual Environment
# ============================================================================
# This script verifies that the virtual environment is complete and functional
# ============================================================================

param(
    [string]$VenvPath = "release\TradingAgentsCN-portable\venv"
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Verify Virtual Environment" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path $VenvPath)) {
    Write-Host "❌ Virtual environment not found: $VenvPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Virtual environment found: $VenvPath" -ForegroundColor Green
Write-Host ""

# Check Python executable
$pythonExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Python executable not found: $pythonExe" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python executable found" -ForegroundColor Green

# Get Python version
$pythonVersion = & $pythonExe --version 2>&1
Write-Host "  Version: $pythonVersion" -ForegroundColor Gray
Write-Host ""

# Check pip
$pipExe = Join-Path $VenvPath "Scripts\pip.exe"
if (-not (Test-Path $pipExe)) {
    Write-Host "❌ Pip executable not found: $pipExe" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Pip found" -ForegroundColor Green

# Get pip version
$pipVersion = & $pipExe --version 2>&1
Write-Host "  Version: $pipVersion" -ForegroundColor Gray
Write-Host ""

# Check critical packages
Write-Host "Checking critical packages..." -ForegroundColor Yellow
Write-Host ""

$criticalPackages = @(
    "pymongo",
    "redis", 
    "fastapi",
    "uvicorn",
    "pandas",
    "pywin32",
    "pydantic",
    "motor",
    "akshare"
)

$allOk = $true
foreach ($pkg in $criticalPackages) {
    $result = & $pipExe show $pkg 2>&1
    if ($LASTEXITCODE -eq 0) {
        # Extract version
        $version = ($result | Select-String "Version:").ToString().Split(":")[1].Trim()
        Write-Host "  ✅ $pkg ($version)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $pkg - NOT FOUND" -ForegroundColor Red
        $allOk = $false
    }
}

Write-Host ""

# Count total packages
Write-Host "Counting installed packages..." -ForegroundColor Yellow
$packageList = & $pipExe list 2>&1
$packageCount = ($packageList | Select-String "^[a-zA-Z]").Count
Write-Host "  Total packages: $packageCount" -ForegroundColor Gray
Write-Host ""

# Test import
Write-Host "Testing Python imports..." -ForegroundColor Yellow
Write-Host ""

$testScript = @"
import sys
try:
    import pymongo
    print('✅ pymongo OK')
except ImportError as e:
    print(f'❌ pymongo FAILED: {e}')
    sys.exit(1)

try:
    import redis
    print('✅ redis OK')
except ImportError as e:
    print(f'❌ redis FAILED: {e}')
    sys.exit(1)

try:
    import fastapi
    print('✅ fastapi OK')
except ImportError as e:
    print(f'❌ fastapi FAILED: {e}')
    sys.exit(1)

try:
    import win32api
    print('✅ pywin32 OK')
except ImportError as e:
    print(f'❌ pywin32 FAILED: {e}')
    sys.exit(1)

print('✅ All imports successful')
"@

$testScriptPath = Join-Path $env:TEMP "test_imports.py"
Set-Content -Path $testScriptPath -Value $testScript -Encoding UTF8

$importResult = & $pythonExe $testScriptPath 2>&1
Write-Host $importResult

Remove-Item -Path $testScriptPath -Force

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Import test failed" -ForegroundColor Red
    $allOk = $false
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan

if ($allOk) {
    Write-Host "  ✅ Virtual Environment is COMPLETE and FUNCTIONAL" -ForegroundColor Green
    Write-Host "============================================================================" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "  ❌ Virtual Environment has MISSING PACKAGES" -ForegroundColor Red
    Write-Host "============================================================================" -ForegroundColor Cyan
    exit 1
}

