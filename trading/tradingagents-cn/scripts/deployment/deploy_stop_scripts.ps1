<#
Deploy Stop Scripts to Portable Release

This script copies the stop service scripts to the portable release directory.
#>

[CmdletBinding()]
param(
    [string]$PortableDir = "release\TradingAgentsCN-portable"
)

$ErrorActionPreference = 'Stop'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploy Stop Scripts to Portable" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$root = Get-Location

# Check if portable directory exists
$portablePath = Join-Path $root $PortableDir
if (-not (Test-Path $portablePath)) {
    Write-Host "[ERROR] Portable directory not found: $portablePath" -ForegroundColor Red
    Write-Host "Please build the portable version first." -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] Portable directory: $portablePath" -ForegroundColor Cyan
Write-Host ""

# Define files to copy
$filesToCopy = @(
    @{
        Source = "scripts\portable\stop_all.ps1"
        Dest = "stop_all.ps1"
        Description = "PowerShell stop script"
    },
    @{
        Source = "scripts\portable\stop_all_services.bat"
        Dest = "stop_all_services.bat"
        Description = "Batch file wrapper"
    },
    @{
        Source = "docs\deployment\stop-services-guide.md"
        Dest = "stop_services_guide.md"
        Description = "Stop services guide"
    }
)

$successCount = 0
$failCount = 0

foreach ($file in $filesToCopy) {
    $sourcePath = Join-Path $root $file.Source
    $destPath = Join-Path $portablePath $file.Dest
    
    Write-Host "[COPY] $($file.Description)" -ForegroundColor Yellow
    Write-Host "  From: $sourcePath" -ForegroundColor Gray
    Write-Host "  To:   $destPath" -ForegroundColor Gray
    
    if (-not (Test-Path $sourcePath)) {
        Write-Host "  [ERROR] Source file not found!" -ForegroundColor Red
        $failCount++
        continue
    }
    
    try {
        Copy-Item -Path $sourcePath -Destination $destPath -Force
        Write-Host "  [OK] Copied successfully" -ForegroundColor Green
        $successCount++
    } catch {
        Write-Host "  [ERROR] Failed to copy: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total files: $($filesToCopy.Count)" -ForegroundColor Cyan
Write-Host "Success: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "[OK] All files deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Users can now stop services by:" -ForegroundColor Cyan
    Write-Host "  1. Double-click: stop_all_services.bat" -ForegroundColor Yellow
    Write-Host "  2. Or run: .\stop_all.ps1" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Note: You may want to create Chinese filename shortcuts:" -ForegroundColor Yellow
    Write-Host "  - stop_all_services.bat -> 停止所有服务.bat" -ForegroundColor Gray
    Write-Host "  - stop_services_guide.md -> 停止服务说明.md" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[WARNING] Some files failed to deploy!" -ForegroundColor Yellow
    exit 1
}

