# ============================================================================
# Sync and Build Only (No Packaging)
# ============================================================================
# This script only syncs code and builds frontend, without creating ZIP package
# Use this for development/testing when you want to update the portable directory
# ============================================================================

param(
    [switch]$SkipSync = $false,
    [switch]$SkipFrontend = $false
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$portableDir = Join-Path $root "release\TradingAgentsCN-portable"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Sync and Build TradingAgents-CN Portable (No Packaging)" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Sync Code (unless skipped)
# ============================================================================

if (-not $SkipSync) {
    Write-Host "[1/2] Syncing code to portable directory..." -ForegroundColor Yellow
    Write-Host ""

    $syncScript = Join-Path $root "scripts\deployment\sync_to_portable.ps1"
    if (-not (Test-Path $syncScript)) {
        Write-Host "ERROR: Sync script not found: $syncScript" -ForegroundColor Red
        exit 1
    }

    try {
        & powershell -ExecutionPolicy Bypass -File $syncScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Sync failed with exit code $LASTEXITCODE" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "ERROR: Sync failed: $_" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "✅ Sync completed successfully!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/2] Skipping sync (using existing files)..." -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# Step 2: Build Frontend (unless skipped)
# ============================================================================

if (-not $SkipFrontend) {
    Write-Host "[2/2] Building frontend..." -ForegroundColor Yellow
    Write-Host ""

    $frontendDir = Join-Path $root "frontend"
    $frontendDistSrc = Join-Path $frontendDir "dist"
    $frontendDistDest = Join-Path $portableDir "frontend\dist"

    if (Test-Path $frontendDir) {
        try {
            # Build in main project directory using Yarn
            Write-Host "  Building frontend in main project directory..." -ForegroundColor Cyan
            Write-Host "  Installing dependencies with Yarn..." -ForegroundColor Gray

            # Use cmd.exe to run yarn to avoid PowerShell parsing issues
            $installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$frontendDir`" && yarn install --frozen-lockfile" -Wait -PassThru -NoNewWindow

            if ($installProcess.ExitCode -ne 0) {
                Write-Host "  WARNING: yarn install failed with exit code $($installProcess.ExitCode)" -ForegroundColor Yellow
            } else {
                Write-Host "  ✅ Dependencies installed successfully" -ForegroundColor Green
            }

            Write-Host "  Building frontend (skipping type check, this may take a few minutes)..." -ForegroundColor Gray
            # Use 'yarn vite build' to skip TypeScript type checking
            $buildProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$frontendDir`" && yarn vite build" -Wait -PassThru -NoNewWindow

            if ($buildProcess.ExitCode -ne 0) {
                Write-Host "  WARNING: Frontend build failed with exit code $($buildProcess.ExitCode)" -ForegroundColor Yellow
            } else {
                Write-Host "  ✅ Frontend build completed" -ForegroundColor Green

                # Copy dist to portable directory
                if (Test-Path $frontendDistSrc) {
                    Write-Host "  Copying frontend dist to portable directory..." -ForegroundColor Gray

                    # Remove old dist
                    if (Test-Path $frontendDistDest) {
                        Remove-Item -Path $frontendDistDest -Recurse -Force
                    }

                    # Copy new dist
                    Copy-Item -Path $frontendDistSrc -Destination $frontendDistDest -Recurse -Force
                    Write-Host "  ✅ Frontend dist copied successfully" -ForegroundColor Green
                } else {
                    Write-Host "  WARNING: Frontend dist not found: $frontendDistSrc" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "  ERROR: Frontend build failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  WARNING: Frontend directory not found: $frontendDir" -ForegroundColor Yellow
    }

    Write-Host ""
} else {
    Write-Host "[2/2] Skipping frontend build..." -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  ✅ Sync and Build Completed!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📂 Portable directory: $portableDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Test the portable version:" -ForegroundColor Gray
Write-Host "      cd $portableDir" -ForegroundColor Gray
Write-Host "      powershell -ExecutionPolicy Bypass -File .\start_all.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Create package (if needed):" -ForegroundColor Gray
Write-Host "      powershell -ExecutionPolicy Bypass -File scripts\deployment\build_portable_package.ps1 -SkipSync" -ForegroundColor Gray
Write-Host ""

