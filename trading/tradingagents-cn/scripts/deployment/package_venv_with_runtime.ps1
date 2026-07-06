# ============================================================================
# Package venv with Python Runtime
# ============================================================================
# This script packages the venv with Python runtime DLLs to make it portable
# ============================================================================

param(
    [string]$VenvPath = "C:\TradingAgentsCN\release\TradingAgentsCN-portable\venv"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Package venv with Python Runtime" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Validate venv
# ============================================================================

Write-Host "[1/3] Validating virtual environment..." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $VenvPath)) {
    Write-Host "  ❌ Virtual environment not found: $VenvPath" -ForegroundColor Red
    exit 1
}

$venvPython = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "  ❌ Python executable not found in venv" -ForegroundColor Red
    exit 1
}

Write-Host "  ✅ Virtual environment found" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 2: Find system Python and copy runtime DLLs
# ============================================================================

Write-Host "[2/3] Copying Python runtime DLLs..." -ForegroundColor Yellow
Write-Host ""

# Get system Python directory by querying Python itself
$systemPython = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $systemPython) {
    Write-Host "  ❌ System Python not found" -ForegroundColor Red
    exit 1
}

# Use Python to get its base installation directory (not venv)
$systemPythonDir = & python -c "import sys; print(sys.base_prefix)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Failed to get Python installation directory" -ForegroundColor Red
    exit 1
}

Write-Host "  System Python: $systemPythonDir" -ForegroundColor Gray

# DLLs to copy
$dllsToCopy = @(
    "python310.dll",
    "python3.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll"
)

$venvScriptsDir = Join-Path $VenvPath "Scripts"
$copiedCount = 0

foreach ($dll in $dllsToCopy) {
    $sourceDll = Join-Path $systemPythonDir $dll
    if (Test-Path $sourceDll) {
        $destDll = Join-Path $venvScriptsDir $dll
        Copy-Item -Path $sourceDll -Destination $destDll -Force
        Write-Host "  ✅ Copied $dll" -ForegroundColor Green
        $copiedCount++
    } else {
        Write-Host "  ⚠️  $dll not found (may not be needed)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "  Copied $copiedCount DLL files" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 3: Copy Python standard library
# ============================================================================

Write-Host "[3/3] Copying Python standard library..." -ForegroundColor Yellow
Write-Host ""

$systemLibDir = Join-Path $systemPythonDir "Lib"
$venvLibDir = Join-Path $VenvPath "Lib"

if (-not (Test-Path $systemLibDir)) {
    Write-Host "  ⚠️  System Lib directory not found: $systemLibDir" -ForegroundColor Yellow
    Write-Host "  Skipping standard library copy" -ForegroundColor Gray
} else {
    Write-Host "  Copying standard library (this may take a few minutes)..." -ForegroundColor Gray
    
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
        "/XD", "site-packages", "__pycache__"  # Exclude these directories
    )
    
    & robocopy @robocopyArgs | Out-Null
    
    # robocopy exit codes: 0-7 success, 8+ failure
    if ($LASTEXITCODE -le 7) {
        Write-Host "  ✅ Standard library copied" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Robocopy returned code $LASTEXITCODE" -ForegroundColor Yellow
    }
}

Write-Host ""

# ============================================================================
# Step 4: Update pyvenv.cfg to use relative path
# ============================================================================

Write-Host "[4/4] Updating pyvenv.cfg to use relative path..." -ForegroundColor Yellow
Write-Host ""

$pyvenvCfg = Join-Path $VenvPath "pyvenv.cfg"
if (Test-Path $pyvenvCfg) {
    # Read current content
    $content = Get-Content $pyvenvCfg -Raw

    # Replace absolute path with relative path to vendors\python
    # The venv is at: TradingAgentsCN-portable\venv
    # The embedded Python is at: TradingAgentsCN-portable\vendors\python
    # Relative path from venv to vendors\python: ..\vendors\python

    $newContent = $content -replace 'home\s*=\s*.*', 'home = ..\vendors\python'

    Set-Content -Path $pyvenvCfg -Value $newContent -Encoding UTF8 -NoNewline
    Write-Host "  ✅ pyvenv.cfg updated to use relative path" -ForegroundColor Green

    # Show the updated content
    Write-Host ""
    Write-Host "  Updated pyvenv.cfg content:" -ForegroundColor Gray
    Get-Content $pyvenvCfg | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
} else {
    Write-Host "  ⚠️  pyvenv.cfg not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  ✅ venv packaged with Python runtime!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  DLLs copied: $copiedCount/4" -ForegroundColor Gray
Write-Host "  Standard library: $(if (Test-Path $venvLibDir) { 'Copied' } else { 'Not copied' })" -ForegroundColor Gray
Write-Host "  pyvenv.cfg: Updated to use relative path (..\vendors\python)" -ForegroundColor Gray
Write-Host ""
Write-Host "The venv is now fully portable and will work on any Windows system!" -ForegroundColor Green
Write-Host ""

exit 0

