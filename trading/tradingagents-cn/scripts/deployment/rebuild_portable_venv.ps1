# ============================================================================
# Rebuild Portable Virtual Environment - Simple Solution
# ============================================================================
# This script rebuilds the virtual environment in the portable directory
# using the system Python, making it more portable with --copies option.
# ============================================================================

param(
    [string]$PortableDir = "C:\TradingAgentsCN\release\TradingAgentsCN-portable"
)

$ErrorActionPreference = "Stop"
$root = "C:\TradingAgentsCN"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Rebuild Portable Virtual Environment" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will recreate the virtual environment with --copies option" -ForegroundColor Gray
Write-Host "making it more portable (but still requires Python on target system)." -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 1: Run the venv creation script
# ============================================================================

Write-Host "[1/2] Creating portable virtual environment..." -ForegroundColor Yellow
Write-Host ""

$createScript = Join-Path $root "scripts\deployment\create_portable_venv.ps1"
$requirementsFile = Join-Path $root "requirements.txt"

if (-not (Test-Path $createScript)) {
    Write-Host "  ❌ Script not found: $createScript" -ForegroundColor Red
    exit 1
}

try {
    & powershell -ExecutionPolicy Bypass -File $createScript -PortableDir $PortableDir -RequirementsFile $requirementsFile
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  ❌ Virtual environment creation failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "  ❌ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 2: Display summary
# ============================================================================

Write-Host "[2/2] Summary" -ForegroundColor Yellow
Write-Host ""

$venvDir = Join-Path $PortableDir "venv"
$venvSize = (Get-ChildItem -Path $venvDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Host "  Virtual Environment:" -ForegroundColor Cyan
Write-Host "    Location: $venvDir" -ForegroundColor Gray
Write-Host "    Size: $([math]::Round($venvSize, 2)) MB" -ForegroundColor Gray
Write-Host ""

Write-Host "  ✅ Portable venv rebuilt successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  Next Steps" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Test the portable version:" -ForegroundColor Cyan
Write-Host "   cd $PortableDir" -ForegroundColor Gray
Write-Host "   powershell -ExecutionPolicy Bypass -File .\start_all.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Package for distribution:" -ForegroundColor Cyan
Write-Host "   powershell -ExecutionPolicy Bypass -File scripts\deployment\build_portable_package.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: The target system still needs Python 3.10+ installed." -ForegroundColor Yellow
Write-Host "For a truly standalone version, use the embedded Python approach." -ForegroundColor Yellow
Write-Host ""

