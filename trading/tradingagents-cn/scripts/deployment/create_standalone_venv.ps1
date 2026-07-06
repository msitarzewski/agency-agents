# ============================================================================
# Create Standalone Virtual Environment
# ============================================================================
# This script creates a truly standalone Python environment by:
# 1. Creating a venv with --copies option
# 2. Copying Python runtime DLLs and standard library
# 3. Modifying pyvenv.cfg to be relocatable
# ============================================================================

param(
    [string]$PortableDir = "C:\TradingAgentsCN\release\TradingAgentsCN-portable",
    [string]$RequirementsFile = "C:\TradingAgentsCN\requirements.txt"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Create Standalone Virtual Environment" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Validate inputs
# ============================================================================

Write-Host "[1/7] Validating inputs..." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $PortableDir)) {
    Write-Host "  ❌ Portable directory not found: $PortableDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $RequirementsFile)) {
    Write-Host "  ❌ Requirements file not found: $RequirementsFile" -ForegroundColor Red
    exit 1
}

# Get system Python info
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Host "  ❌ Python not found in PATH" -ForegroundColor Red
    exit 1
}

$pythonVersion = & python --version 2>&1
$pythonDir = Split-Path -Parent $pythonExe

Write-Host "  ✅ Found Python: $pythonVersion" -ForegroundColor Green
Write-Host "  Location: $pythonDir" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 2: Remove old venv if exists
# ============================================================================

Write-Host "[2/7] Cleaning old virtual environment..." -ForegroundColor Yellow
Write-Host ""

$venvDir = Join-Path $PortableDir "venv"
if (Test-Path $venvDir) {
    Write-Host "  Removing old venv directory..." -ForegroundColor Gray
    Remove-Item -Path $venvDir -Recurse -Force
    Write-Host "  ✅ Old venv removed" -ForegroundColor Green
} else {
    Write-Host "  ✅ No old venv found" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# Step 3: Create new virtual environment with --copies
# ============================================================================

Write-Host "[3/7] Creating new virtual environment..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  Creating venv with --copies option..." -ForegroundColor Gray
& python -m venv $venvDir --copies

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "  ✅ Virtual environment created" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 4: Copy Python runtime files
# ============================================================================

Write-Host "[4/7] Copying Python runtime files..." -ForegroundColor Yellow
Write-Host ""

# Copy DLLs from system Python to venv
$dllsToCopy = @(
    "python310.dll",
    "python3.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll"
)

$venvScriptsDir = Join-Path $venvDir "Scripts"

foreach ($dll in $dllsToCopy) {
    $sourceDll = Join-Path $pythonDir $dll
    if (Test-Path $sourceDll) {
        $destDll = Join-Path $venvScriptsDir $dll
        if (-not (Test-Path $destDll)) {
            Copy-Item -Path $sourceDll -Destination $destDll -Force
            Write-Host "  ✅ Copied $dll" -ForegroundColor Green
        } else {
            Write-Host "  ⏭️  $dll already exists" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠️  $dll not found in system Python" -ForegroundColor Yellow
    }
}

# Copy standard library (Lib folder)
$systemLibDir = Join-Path $pythonDir "Lib"
$venvLibDir = Join-Path $venvDir "Lib"

Write-Host ""
Write-Host "  Copying Python standard library..." -ForegroundColor Gray
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

# Use robocopy for efficient copying
$robocopyArgs = @(
    $systemLibDir,
    $venvLibDir,
    "/E",           # Copy subdirectories including empty ones
    "/NFL",         # No file list
    "/NDL",         # No directory list
    "/NJH",         # No job header
    "/NJS",         # No job summary
    "/NC",          # No class
    "/NS",          # No size
    "/NP",          # No progress
    "/XD", "site-packages"  # Exclude site-packages (already in venv)
)

& robocopy @robocopyArgs | Out-Null

# robocopy exit codes: 0-7 success, 8+ failure
if ($LASTEXITCODE -ge 8) {
    Write-Host "  ⚠️  Robocopy returned code $LASTEXITCODE (may not be critical)" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ Standard library copied" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 5: Modify pyvenv.cfg to be relocatable
# ============================================================================

Write-Host "[5/7] Making virtual environment relocatable..." -ForegroundColor Yellow
Write-Host ""

$pyvenvCfg = Join-Path $venvDir "pyvenv.cfg"
if (Test-Path $pyvenvCfg) {
    $content = Get-Content $pyvenvCfg
    $newContent = @()
    
    foreach ($line in $content) {
        if ($line -match "^home\s*=") {
            # Comment out the home line
            $newContent += "# $line (commented for portability)"
            Write-Host "  ✅ Commented out 'home' path" -ForegroundColor Green
        } else {
            $newContent += $line
        }
    }
    
    Set-Content -Path $pyvenvCfg -Value $newContent -Encoding ASCII
    Write-Host "  ✅ pyvenv.cfg updated" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  pyvenv.cfg not found" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 6: Install dependencies
# ============================================================================

Write-Host "[6/7] Installing dependencies..." -ForegroundColor Yellow
Write-Host ""

$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "  ❌ Virtual environment Python not found: $venvPython" -ForegroundColor Red
    exit 1
}

Write-Host "  Upgrading pip..." -ForegroundColor Gray
& $venvPython -m pip install --upgrade pip --quiet

Write-Host "  Installing project dependencies (this may take 5-10 minutes)..." -ForegroundColor Gray
Write-Host ""

# Try multiple mirrors
$pipMirrors = @(
    @{Name="Aliyun"; Args=@("-r", $RequirementsFile, "--no-warn-script-location", "-i", "https://mirrors.aliyun.com/pypi/simple/", "--trusted-host", "mirrors.aliyun.com")},
    @{Name="Tsinghua"; Args=@("-r", $RequirementsFile, "--no-warn-script-location", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn")},
    @{Name="Default"; Args=@("-r", $RequirementsFile, "--no-warn-script-location")}
)

$installed = $false
foreach ($mirror in $pipMirrors) {
    Write-Host "  Trying $($mirror.Name) mirror..." -ForegroundColor Gray
    
    & $venvPip install @($mirror.Args) 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ All dependencies installed using $($mirror.Name) mirror" -ForegroundColor Green
        $installed = $true
        break
    } else {
        Write-Host "  ⚠️  $($mirror.Name) mirror failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
    }
}

if (-not $installed) {
    Write-Host ""
    Write-Host "  ❌ All mirrors failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 7: Verify installation
# ============================================================================

Write-Host "[7/7] Verifying installation..." -ForegroundColor Yellow
Write-Host ""

# Test Python
$testVersion = & $venvPython --version 2>&1
Write-Host "  Python: $testVersion" -ForegroundColor Gray

# Test pip
$testPip = & $venvPip --version 2>&1
Write-Host "  Pip: $testPip" -ForegroundColor Gray

# Test critical imports
$testScript = @"
import sys
packages = ['pymongo', 'redis', 'fastapi', 'uvicorn', 'pandas']
failed = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} OK')
    except ImportError as e:
        print(f'❌ {pkg} FAILED: {e}')
        failed.append(pkg)
        sys.exit(1)
"@

$testScriptPath = Join-Path $env:TEMP "test_standalone_venv.py"
Set-Content -Path $testScriptPath -Value $testScript -Encoding UTF8

Write-Host ""
& $venvPython $testScriptPath

Remove-Item -Path $testScriptPath -Force

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ❌ Import test failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  ✅ Standalone Virtual Environment Created Successfully!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Location: $venvDir" -ForegroundColor Gray
Write-Host ""
Write-Host "This environment should work on systems without Python installed." -ForegroundColor Gray
Write-Host ""

exit 0

