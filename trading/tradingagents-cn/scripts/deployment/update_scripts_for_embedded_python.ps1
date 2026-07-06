# ============================================================================
# Update Scripts for Embedded Python
# ============================================================================
# This script updates all startup scripts to use embedded Python
# instead of venv or system Python
# ============================================================================

param(
    [string]$PortableDir = ""
)

$ErrorActionPreference = "Stop"

# Determine portable directory
if (-not $PortableDir) {
    $root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $PortableDir = Join-Path $root "release\TradingAgentsCN-portable"
}

if (-not (Test-Path $PortableDir)) {
    Write-Host "ERROR: Portable directory not found: $PortableDir" -ForegroundColor Red
    exit 1
}

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Update Scripts for Embedded Python" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Define Python Path Pattern Replacement
# ============================================================================

$oldPattern1 = @'
$pythonExe = Join-Path $root 'venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
    $pythonExe = 'python'
}
'@

$newPattern1 = @'
$pythonExe = Join-Path $root 'vendors\python\python.exe'
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Embedded Python not found: $pythonExe" -ForegroundColor Red
    Write-Host "Please run setup_embedded_python.ps1 first" -ForegroundColor Yellow
    exit 1
}
'@

# ============================================================================
# Find and Update Scripts
# ============================================================================

$scriptsToUpdate = @(
    "start_all.ps1",
    "start_services_clean.ps1",
    "stop_all.ps1"
)

$updatedCount = 0
$skippedCount = 0

foreach ($scriptName in $scriptsToUpdate) {
    $scriptPath = Join-Path $PortableDir $scriptName
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "⚠️ Script not found: $scriptName" -ForegroundColor Yellow
        $skippedCount++
        continue
    }
    
    Write-Host "Processing: $scriptName" -ForegroundColor Cyan
    
    # Read content
    $content = Get-Content $scriptPath -Raw
    
    # Check if already updated
    if ($content -match "vendors\\python\\python\.exe") {
        Write-Host "  ✅ Already using embedded Python" -ForegroundColor Green
        $skippedCount++
        continue
    }
    
    # Check if needs update
    if ($content -match "venv\\Scripts\\python\.exe") {
        Write-Host "  🔧 Updating Python path..." -ForegroundColor Yellow
        
        # Replace pattern
        $newContent = $content -replace [regex]::Escape($oldPattern1), $newPattern1
        
        # Also replace any standalone venv references
        $newContent = $newContent -replace "venv\\Scripts\\python\.exe", "vendors\python\python.exe"
        
        # Backup original
        $backupPath = "$scriptPath.bak"
        Copy-Item -Path $scriptPath -Destination $backupPath -Force
        Write-Host "  📦 Backup created: $scriptName.bak" -ForegroundColor Gray
        
        # Write updated content
        Set-Content -Path $scriptPath -Value $newContent -Encoding UTF8
        Write-Host "  ✅ Updated successfully" -ForegroundColor Green
        $updatedCount++
    } else {
        Write-Host "  ℹ️ No venv references found" -ForegroundColor Gray
        $skippedCount++
    }
    
    Write-Host ""
}

# ============================================================================
# Update installer scripts (source)
# ============================================================================

Write-Host "Updating source scripts in scripts/installer..." -ForegroundColor Cyan
Write-Host ""

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$installerDir = Join-Path $root "scripts\installer"

if (Test-Path $installerDir) {
    $installerScripts = Get-ChildItem -Path $installerDir -Filter "*.ps1"
    
    foreach ($script in $installerScripts) {
        Write-Host "Processing: scripts\installer\$($script.Name)" -ForegroundColor Cyan
        
        $content = Get-Content $script.FullName -Raw
        
        # Check if already updated
        if ($content -match "vendors\\python\\python\.exe") {
            Write-Host "  ✅ Already using embedded Python" -ForegroundColor Green
            continue
        }
        
        # Check if needs update
        if ($content -match "venv\\Scripts\\python\.exe") {
            Write-Host "  🔧 Updating Python path..." -ForegroundColor Yellow
            
            # Replace pattern
            $newContent = $content -replace [regex]::Escape($oldPattern1), $newPattern1
            $newContent = $newContent -replace "venv\\Scripts\\python\.exe", "vendors\python\python.exe"
            
            # Backup
            $backupPath = "$($script.FullName).bak"
            Copy-Item -Path $script.FullName -Destination $backupPath -Force
            Write-Host "  📦 Backup created: $($script.Name).bak" -ForegroundColor Gray
            
            # Write
            Set-Content -Path $script.FullName -Value $newContent -Encoding UTF8
            Write-Host "  ✅ Updated successfully" -ForegroundColor Green
            $updatedCount++
        } else {
            Write-Host "  ℹ️ No venv references found" -ForegroundColor Gray
        }
        
        Write-Host ""
    }
}

# ============================================================================
# Remove venv directory
# ============================================================================

Write-Host "Checking for old venv directory..." -ForegroundColor Cyan
$venvDir = Join-Path $PortableDir "venv"

if (Test-Path $venvDir) {
    Write-Host "  Found venv directory: $venvDir" -ForegroundColor Yellow
    Write-Host "  Size: $((Get-ChildItem $venvDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB) MB" -ForegroundColor Gray
    
    $response = Read-Host "  Do you want to remove it? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "  Removing venv directory..." -ForegroundColor Yellow
        try {
            Remove-Item -Path $venvDir -Recurse -Force
            Write-Host "  ✅ venv directory removed" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Failed to remove venv: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ℹ️ Keeping venv directory" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✅ No venv directory found" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Summary
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  ✅ Script Update Completed!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  Scripts updated: $updatedCount" -ForegroundColor Gray
Write-Host "  Scripts skipped: $skippedCount" -ForegroundColor Gray
Write-Host ""

if ($updatedCount -gt 0) {
    Write-Host "💡 Backup files (.bak) have been created for all updated scripts" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "🧪 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the portable version:" -ForegroundColor Gray
Write-Host "     cd $PortableDir" -ForegroundColor Gray
Write-Host "     powershell -ExecutionPolicy Bypass -File .\start_all.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. If everything works, rebuild the package:" -ForegroundColor Gray
Write-Host "     powershell -ExecutionPolicy Bypass -File scripts\deployment\build_portable_package.ps1 -SkipSync" -ForegroundColor Gray
Write-Host ""

