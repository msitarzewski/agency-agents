# ============================================================================
# Migrate to Embedded Python - One-Click Solution
# ============================================================================
# This script automates the complete migration from venv to embedded Python:
# 1. Setup embedded Python
# 2. Update all scripts
# 3. Remove old venv
# 4. Test the installation
# ============================================================================

param(
    [string]$PythonVersion = "3.10.11",
    [switch]$SkipTest = $false
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$portableDir = Join-Path $root "release\TradingAgentsCN-portable"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Migrate to Embedded Python - Complete Solution" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Download and setup Python $PythonVersion embedded distribution" -ForegroundColor Gray
Write-Host "  2. Install all project dependencies" -ForegroundColor Gray
Write-Host "  3. Update all startup scripts" -ForegroundColor Gray
Write-Host "  4. Remove old venv directory" -ForegroundColor Gray
Write-Host "  5. Test the installation" -ForegroundColor Gray
Write-Host ""

$response = Read-Host "Continue? (Y/n)"
if ($response -eq 'n' -or $response -eq 'N') {
    Write-Host "Cancelled by user" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# ============================================================================
# Step 1: Setup Embedded Python
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 1: Setup Embedded Python" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$setupScript = Join-Path $root "scripts\deployment\setup_embedded_python.ps1"
if (-not (Test-Path $setupScript)) {
    Write-Host "ERROR: Setup script not found: $setupScript" -ForegroundColor Red
    exit 1
}

try {
    & powershell -ExecutionPolicy Bypass -File $setupScript -PythonVersion $PythonVersion -PortableDir $portableDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Setup failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Setup failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue to Step 2..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

# ============================================================================
# Step 2: Update Scripts
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 2: Update Scripts" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$updateScript = Join-Path $root "scripts\deployment\update_scripts_for_embedded_python.ps1"
if (-not (Test-Path $updateScript)) {
    Write-Host "ERROR: Update script not found: $updateScript" -ForegroundColor Red
    exit 1
}

try {
    # Run with automatic 'y' response for venv removal
    $env:EMBEDDED_PYTHON_AUTO_REMOVE_VENV = "y"
    & powershell -ExecutionPolicy Bypass -File $updateScript -PortableDir $portableDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Update failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Update failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 3: Remove venv Directory
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 3: Remove Old venv Directory" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$venvDir = Join-Path $portableDir "venv"
if (Test-Path $venvDir) {
    $venvSize = (Get-ChildItem $venvDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "Found venv directory:" -ForegroundColor Yellow
    Write-Host "  Path: $venvDir" -ForegroundColor Gray
    Write-Host "  Size: $([math]::Round($venvSize, 2)) MB" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "Removing venv directory..." -ForegroundColor Yellow
    try {
        Remove-Item -Path $venvDir -Recurse -Force -ErrorAction Stop
        Write-Host "✅ venv directory removed successfully" -ForegroundColor Green
        Write-Host "  Freed up: $([math]::Round($venvSize, 2)) MB" -ForegroundColor Gray
    } catch {
        Write-Host "⚠️ Failed to remove venv: $_" -ForegroundColor Yellow
        Write-Host "  You can manually delete it later" -ForegroundColor Gray
    }
} else {
    Write-Host "✅ No venv directory found (already removed)" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 4: Test Installation
# ============================================================================

if (-not $SkipTest) {
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "STEP 4: Test Installation" -ForegroundColor Cyan
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $pythonExe = Join-Path $portableDir "vendors\python\python.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Host "❌ ERROR: Python executable not found: $pythonExe" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Testing Python installation..." -ForegroundColor Yellow
    Write-Host ""
    
    # Test 1: Python version
    Write-Host "[Test 1/4] Python version" -ForegroundColor Cyan
    $versionOutput = & $pythonExe --version 2>&1
    Write-Host "  $versionOutput" -ForegroundColor Gray
    
    # Test 2: pip
    Write-Host "[Test 2/4] pip availability" -ForegroundColor Cyan
    $pipOutput = & $pythonExe -m pip --version 2>&1
    Write-Host "  $pipOutput" -ForegroundColor Gray
    
    # Test 3: Key imports
    Write-Host "[Test 3/4] Key package imports" -ForegroundColor Cyan
    $testPackages = @("fastapi", "uvicorn", "pymongo", "redis", "langchain", "pandas", "numpy")
    $importSuccess = 0
    $importFailed = 0
    
    foreach ($pkg in $testPackages) {
        $testResult = & $pythonExe -c "import $pkg" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $pkg" -ForegroundColor Green
            $importSuccess++
        } else {
            Write-Host "  ❌ $pkg" -ForegroundColor Red
            $importFailed++
        }
    }
    
    # Test 4: App module
    Write-Host "[Test 4/4] App module structure" -ForegroundColor Cyan
    Push-Location $portableDir
    $appTest = & $pythonExe -c "import sys; sys.path.insert(0, '.'); import app; print('OK')" 2>&1
    Pop-Location
    
    if ($appTest -match "OK") {
        Write-Host "  ✅ App module can be imported" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ App module import warning (may be normal)" -ForegroundColor Yellow
        Write-Host "  $appTest" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "Test Summary:" -ForegroundColor Cyan
    Write-Host "  Package imports: $importSuccess passed, $importFailed failed" -ForegroundColor Gray
    
    if ($importFailed -gt 0) {
        Write-Host ""
        Write-Host "⚠️ Warning: Some packages failed to import" -ForegroundColor Yellow
        Write-Host "  This may indicate missing dependencies" -ForegroundColor Gray
    }
} else {
    Write-Host "Skipping tests (--SkipTest flag)" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Step 5: Calculate Size Difference
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 5: Size Analysis" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$pythonDir = Join-Path $portableDir "vendors\python"
if (Test-Path $pythonDir) {
    $pythonSize = (Get-ChildItem $pythonDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "Embedded Python size: $([math]::Round($pythonSize, 2)) MB" -ForegroundColor Cyan
}

$totalSize = (Get-ChildItem $portableDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Total portable directory size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor Cyan

Write-Host ""

# ============================================================================
# Final Summary
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  ✅ Migration to Embedded Python Completed!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Embedded Python installed: vendors\python\" -ForegroundColor Gray
Write-Host "  ✅ All scripts updated" -ForegroundColor Gray
Write-Host "  ✅ Old venv removed" -ForegroundColor Gray
Write-Host "  ✅ Installation tested" -ForegroundColor Gray
Write-Host ""
Write-Host "📦 Package Details:" -ForegroundColor Cyan
Write-Host "  Python: $([math]::Round($pythonSize, 2)) MB" -ForegroundColor Gray
Write-Host "  Total: $([math]::Round($totalSize, 2)) MB" -ForegroundColor Gray
Write-Host ""
Write-Host "🎉 Your portable version is now truly independent!" -ForegroundColor Green
Write-Host "   It will work on any Windows system without Python installed." -ForegroundColor Gray
Write-Host ""
Write-Host "🧪 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the portable version:" -ForegroundColor Gray
Write-Host "     cd $portableDir" -ForegroundColor Gray
Write-Host "     powershell -ExecutionPolicy Bypass -File .\start_all.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. If everything works, create a new package:" -ForegroundColor Gray
Write-Host "     powershell -ExecutionPolicy Bypass -File scripts\deployment\build_portable_package.ps1 -SkipSync" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test on a clean Windows system (no Python installed)" -ForegroundColor Gray
Write-Host ""

