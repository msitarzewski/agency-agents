# ============================================================================
# Create Portable Virtual Environment
# ============================================================================
# This script creates a truly portable Python virtual environment by:
# 1. Creating a fresh venv in the portable directory
# 2. Installing all dependencies
# 3. Making the venv relocatable (removing hardcoded paths)
# ============================================================================

param(
    [string]$PortableDir = "C:\TradingAgentsCN\release\TradingAgentsCN-portable",
    [string]$RequirementsFile = "C:\TradingAgentsCN\requirements.txt"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Create Portable Virtual Environment" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Validate inputs
# ============================================================================

Write-Host "[1/5] Validating inputs..." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $PortableDir)) {
    Write-Host "  ❌ Portable directory not found: $PortableDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $RequirementsFile)) {
    Write-Host "  ❌ Requirements file not found: $RequirementsFile" -ForegroundColor Red
    exit 1
}

# Check Python availability
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Host "  ❌ Python not found in PATH" -ForegroundColor Red
    exit 1
}

$pythonVersion = & python --version 2>&1
Write-Host "  ✅ Found Python: $pythonVersion" -ForegroundColor Green
Write-Host "  Location: $pythonExe" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 2: Remove old venv if exists
# ============================================================================

Write-Host "[2/5] Cleaning old virtual environment..." -ForegroundColor Yellow
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
# Step 3: Create new virtual environment
# ============================================================================

Write-Host "[3/5] Creating new virtual environment..." -ForegroundColor Yellow
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
# Step 4: Install dependencies
# ============================================================================

Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
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
Write-Host "  This will install all packages from requirements.txt" -ForegroundColor Gray
Write-Host ""

# Try multiple mirrors
$pipMirrors = @(
    @{Name="Default"; Args=@("-r", $RequirementsFile, "--no-warn-script-location")},
    @{Name="Aliyun"; Args=@("-r", $RequirementsFile, "--no-warn-script-location", "-i", "https://mirrors.aliyun.com/pypi/simple/", "--trusted-host", "mirrors.aliyun.com")},
    @{Name="Tsinghua"; Args=@("-r", $RequirementsFile, "--no-warn-script-location", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn")}
)

$installed = $false
foreach ($mirror in $pipMirrors) {
    Write-Host "  Trying $($mirror.Name) mirror..." -ForegroundColor Gray

    # Show installation progress
    & $venvPip install @($mirror.Args) 2>&1 | ForEach-Object {
        if ($_ -match "Successfully installed" -or $_ -match "Requirement already satisfied") {
            Write-Host "    $_" -ForegroundColor DarkGray
        }
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  ✅ All dependencies installed successfully using $($mirror.Name) mirror" -ForegroundColor Green
        $installed = $true
        break
    } else {
        Write-Host "  ⚠️ $($mirror.Name) mirror failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
    }
}

if (-not $installed) {
    Write-Host ""
    Write-Host "  ❌ All mirrors failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Verify critical packages are installed
Write-Host ""
Write-Host "  Verifying critical packages..." -ForegroundColor Gray
$criticalPackages = @("pymongo", "redis", "fastapi", "uvicorn", "pandas", "pywin32")
$missingPackages = @()

foreach ($pkg in $criticalPackages) {
    $checkResult = & $venvPip show $pkg 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $pkg
        Write-Host "    ❌ $pkg - NOT FOUND" -ForegroundColor Red
    } else {
        Write-Host "    ✅ $pkg - OK" -ForegroundColor Green
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "  ❌ Critical packages missing: $($missingPackages -join ', ')" -ForegroundColor Red
    Write-Host "  Attempting to install missing packages..." -ForegroundColor Yellow

    foreach ($pkg in $missingPackages) {
        Write-Host "    Installing $pkg..." -ForegroundColor Gray
        & $venvPip install $pkg --no-warn-script-location
    }
}

Write-Host ""

# ============================================================================
# Step 5: Make venv relocatable
# ============================================================================

Write-Host "[5/5] Making virtual environment relocatable..." -ForegroundColor Yellow
Write-Host ""

# Modify activation scripts to use relative paths
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "  Updating Activate.ps1..." -ForegroundColor Gray
    
    $content = Get-Content $activateScript -Raw
    
    # Replace absolute path with relative path detection
    $newContent = $content -replace 'VIRTUAL_ENV\s*=\s*"[^"]*"', 'VIRTUAL_ENV = Split-Path -Parent $PSScriptRoot'
    
    Set-Content -Path $activateScript -Value $newContent -Encoding UTF8
    Write-Host "  ✅ Activate.ps1 updated" -ForegroundColor Green
}

# Note: With --copies option, the venv is already more portable
# The 'home' path in pyvenv.cfg is still needed for Python to work
Write-Host "  ✅ Virtual environment is portable (using --copies)" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Step 6: Test the installation
# ============================================================================

Write-Host "[6/6] Testing installation..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  Testing Python..." -ForegroundColor Gray
$testOutput = & $venvPython --version 2>&1
Write-Host "    $testOutput" -ForegroundColor DarkGray

Write-Host "  Testing pip..." -ForegroundColor Gray
$testOutput = & $venvPip --version 2>&1
Write-Host "    $testOutput" -ForegroundColor DarkGray

Write-Host "  Testing key packages..." -ForegroundColor Gray
$packages = @("fastapi", "uvicorn", "pymongo", "redis", "pandas")
foreach ($pkg in $packages) {
    $testOutput = & $venvPython -c "import $pkg; print('$pkg OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ $testOutput" -ForegroundColor DarkGreen
    } else {
        Write-Host "    ⚠️ $pkg failed to import" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  ✅ Portable Virtual Environment Created Successfully!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $venvDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: This venv uses --copies option, making it more portable." -ForegroundColor Gray
Write-Host "However, it still requires Python to be installed on the target system." -ForegroundColor Gray
Write-Host ""

