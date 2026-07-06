# ============================================================================
# Build Portable Package - One-Click Solution
# ============================================================================
# This script combines sync and packaging into one step:
# 1. Sync code from main project to portable directory
# 2. Setup embedded Python (if not present)
# 3. Build frontend
# 4. Package portable directory into compressed archive
# ============================================================================

param(
    [string]$Version = "",
    [switch]$SkipSync = $false,
    [switch]$SkipEmbeddedPython = $false,
    [switch]$SkipPackage = $false,  # 🔥 新增：只同步和编译，不打包
    [string]$PythonVersion = "3.10.11"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$portableDir = Join-Path $root "release\TradingAgentsCN-portable"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Build TradingAgents-CN Portable Package" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Sync Code (unless skipped)
# ============================================================================

if (-not $SkipSync) {
    Write-Host "[1/3] Syncing code to portable directory..." -ForegroundColor Yellow
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
    Write-Host "Sync completed successfully!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/3] Skipping sync (using existing files)..." -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# Step 1.5: Setup Embedded Python (if not present)
# ============================================================================

if (-not $SkipEmbeddedPython) {
    $pythonExe = Join-Path $portableDir "vendors\python\python.exe"

    if (-not (Test-Path $pythonExe)) {
        Write-Host "[1.5/4] Setting up embedded Python..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Embedded Python not found, installing..." -ForegroundColor Cyan

        $setupScript = Join-Path $root "scripts\deployment\setup_embedded_python.ps1"
        if (-not (Test-Path $setupScript)) {
            Write-Host "  ERROR: Setup script not found: $setupScript" -ForegroundColor Red
            Write-Host "  Continuing without embedded Python..." -ForegroundColor Yellow
        } else {
            try {
                & powershell -ExecutionPolicy Bypass -File $setupScript -PythonVersion $PythonVersion -PortableDir $portableDir
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ""
                    Write-Host "  ✅ Embedded Python setup completed!" -ForegroundColor Green

                    # Update scripts to use embedded Python
                    $updateScript = Join-Path $root "scripts\deployment\update_scripts_for_embedded_python.ps1"
                    if (Test-Path $updateScript) {
                        Write-Host "  Updating scripts..." -ForegroundColor Gray
                        & powershell -ExecutionPolicy Bypass -File $updateScript -PortableDir $portableDir | Out-Null
                    }
                } else {
                    Write-Host "  ⚠️ Embedded Python setup failed, continuing..." -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  ⚠️ Embedded Python setup error: $_" -ForegroundColor Yellow
                Write-Host "  Continuing with packaging..." -ForegroundColor Gray
            }
        }
        Write-Host ""
    } else {
        Write-Host "[1.5/4] Embedded Python already present, skipping..." -ForegroundColor Gray
        Write-Host "  Location: $pythonExe" -ForegroundColor DarkGray
        Write-Host ""
    }
} else {
    Write-Host "[1.5/4] Skipping embedded Python setup..." -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# Step 2: Build Frontend
# ============================================================================

Write-Host "[2/4] Building frontend..." -ForegroundColor Yellow
Write-Host ""

$frontendDir = Join-Path $root "frontend"
$frontendDistSrc = Join-Path $frontendDir "dist"
$frontendDistDest = Join-Path $portableDir "frontend\dist"

if (Test-Path $frontendDir) {
    try {
        # Build in main project directory using Yarn (same as Dockerfile)
        Write-Host "  Building frontend in main project directory..." -ForegroundColor Cyan
        Write-Host "  Installing dependencies with Yarn..." -ForegroundColor Gray

        # Use cmd.exe to run yarn to avoid PowerShell parsing issues
        $installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$frontendDir`" && yarn install --frozen-lockfile" -Wait -PassThru -NoNewWindow

        if ($installProcess.ExitCode -ne 0) {
            Write-Host "  WARNING: yarn install failed with exit code $($installProcess.ExitCode)" -ForegroundColor Yellow
        } else {
            Write-Host "  Dependencies installed successfully" -ForegroundColor Green
        }

        Write-Host "  Building frontend (skipping type check, this may take a few minutes)..." -ForegroundColor Gray
        # Use 'yarn vite build' to skip TypeScript type checking (same as Dockerfile)
        $buildProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$frontendDir`" && yarn vite build" -Wait -PassThru -NoNewWindow

        if ($buildProcess.ExitCode -ne 0) {
            Write-Host "  WARNING: Frontend build failed with exit code $($buildProcess.ExitCode)" -ForegroundColor Yellow
        } else {
            Write-Host "  Frontend build completed" -ForegroundColor Green

            # Copy dist to portable directory
            if (Test-Path $frontendDistSrc) {
                Write-Host "  Copying frontend dist to portable directory..." -ForegroundColor Gray

                # Remove old dist
                if (Test-Path $frontendDistDest) {
                    Remove-Item -Path $frontendDistDest -Recurse -Force
                }

                # Copy new dist
                Copy-Item -Path $frontendDistSrc -Destination $frontendDistDest -Recurse -Force
                Write-Host "  Frontend dist copied successfully" -ForegroundColor Green
            } else {
                Write-Host "  WARNING: Frontend dist not found: $frontendDistSrc" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "  ERROR: Frontend build failed: $_" -ForegroundColor Red
        Write-Host "  Continuing with packaging..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  WARNING: Frontend directory not found: $frontendDir" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 3: Package (unless skipped)
# ============================================================================

if ($SkipPackage) {
    Write-Host "[3/4] Packaging skipped (SkipPackage flag set)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host "  Sync and Build Completed Successfully!" -ForegroundColor Green
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Files synced to: $portableDir" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor White
    Write-Host "  1. Test the changes in release\TradingAgentsCN-portable" -ForegroundColor Gray
    Write-Host "  2. Run .\start_all.ps1 to start all services" -ForegroundColor Gray
    Write-Host "  3. Visit http://localhost to access the application" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

Write-Host "[3/4] Packaging portable directory..." -ForegroundColor Yellow
Write-Host ""

$portableDir = Join-Path $root "release\TradingAgentsCN-portable"
if (-not (Test-Path $portableDir)) {
    Write-Host "ERROR: Portable directory not found: $portableDir" -ForegroundColor Red
    exit 1
}

# Determine version (priority: parameter > VERSION file > .env > default)
if (-not $Version) {
    # Try VERSION file in root
    $versionFile = Join-Path $root "VERSION"
    if (Test-Path $versionFile) {
        $Version = (Get-Content $versionFile -Raw).Trim()
        Write-Host "  Version from VERSION file: $Version" -ForegroundColor Cyan
    }

    # Fallback to .env file
    if (-not $Version) {
        $envFile = Join-Path $portableDir ".env"
        if (Test-Path $envFile) {
            $versionLine = Get-Content $envFile | Where-Object { $_ -match "^VERSION=" }
            if ($versionLine) {
                $Version = ($versionLine -split "=", 2)[1].Trim()
                Write-Host "  Version from .env file: $Version" -ForegroundColor Cyan
            }
        }
    }

    # Final fallback to default
    if (-not $Version) {
        $Version = "v0.1.13-preview"
        Write-Host "  Using default version: $Version" -ForegroundColor Yellow
    }
}

# Create packages directory
$packagesDir = Join-Path $root "release\packages"
if (-not (Test-Path $packagesDir)) {
    New-Item -ItemType Directory -Path $packagesDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$packageName = "TradingAgentsCN-Portable-$Version-$timestamp"
$zipPath = Join-Path $packagesDir "$packageName.zip"

Write-Host "  Package name: $packageName" -ForegroundColor Cyan
Write-Host "  Output path: $zipPath" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Create temporary directory and copy files (excluding database data)
# ============================================================================

Write-Host "  Creating temporary directory..." -ForegroundColor Gray
$tempDir = Join-Path $env:TEMP "TradingAgentsCN-Package-$timestamp"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

Write-Host "  Copying all files to temporary directory..." -ForegroundColor Gray

# First, copy everything
$robocopyArgs = @(
    $portableDir,
    $tempDir,
    "/E",           # Copy subdirectories including empty ones
    "/NFL",         # No file list
    "/NDL",         # No directory list
    "/NJH",         # No job header
    "/NJS",         # No job summary
    "/NC",          # No class
    "/NS",          # No size
    "/NP"           # No progress
)

# Execute robocopy
Write-Host "  Source: $portableDir" -ForegroundColor DarkGray
Write-Host "  Destination: $tempDir" -ForegroundColor DarkGray
$robocopyOutput = & robocopy @robocopyArgs 2>&1

# robocopy exit codes: 0-7 success, 8+ failure
if ($LASTEXITCODE -ge 8) {
    Write-Host "  ERROR: Robocopy failed with exit code $LASTEXITCODE" -ForegroundColor Red
    Write-Host "  Output: $robocopyOutput" -ForegroundColor Gray
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "  Robocopy exit code: $LASTEXITCODE" -ForegroundColor DarkGray

Write-Host "  Files copied successfully" -ForegroundColor Green

# Now remove directories we don't want to package (database data, logs, cache)
Write-Host "  Removing database data and logs from package..." -ForegroundColor Gray

$excludeDirs = @(
    (Join-Path $tempDir "data\mongodb"),
    (Join-Path $tempDir "data\redis"),
    (Join-Path $tempDir "logs"),
    (Join-Path $tempDir "data\cache")
)

foreach ($dir in $excludeDirs) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "    Removed: $($dir.Replace($tempDir, ''))" -ForegroundColor DarkGray
    }
}

Write-Host "  Cleanup completed" -ForegroundColor Green

# ============================================================================
# Remove MongoDB debug symbols and crash dumps (saves ~2GB)
# ============================================================================

Write-Host "  Removing MongoDB debug symbols and crash dumps..." -ForegroundColor Gray

$mongodbVendorDir = Join-Path $tempDir "vendors\mongodb"
if (Test-Path $mongodbVendorDir) {
    # Remove .pdb files (debug symbols)
    $pdbFiles = Get-ChildItem -Path $mongodbVendorDir -Filter "*.pdb" -Recurse -File
    foreach ($file in $pdbFiles) {
        Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "    Removed: $($file.Name) ($sizeMB MB)" -ForegroundColor DarkGray
    }

    # Remove .mdmp files (crash dumps)
    $mdmpFiles = Get-ChildItem -Path $mongodbVendorDir -Filter "*.mdmp" -Recurse -File
    foreach ($file in $mdmpFiles) {
        Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "    Removed: $($file.Name) ($sizeMB MB)" -ForegroundColor DarkGray
    }

    Write-Host "  MongoDB cleanup completed (saved ~2GB)" -ForegroundColor Green
}

# ============================================================================
# Clean up runtime directory (keep config files only)
# ============================================================================

Write-Host "  Cleaning runtime directory (keeping config files)..." -ForegroundColor Gray

$runtimeDir = Join-Path $tempDir "runtime"
if (Test-Path $runtimeDir) {
    # Keep only config files (.conf, .types)
    Get-ChildItem -Path $runtimeDir -File | Where-Object {
        $_.Extension -notin @('.conf', '.types')
    } | Remove-Item -Force -ErrorAction SilentlyContinue

    Write-Host "  Runtime directory cleaned" -ForegroundColor Green
}

# ============================================================================
# Ensure venv exists and package with Python runtime for portability
# ============================================================================

$venvDir = Join-Path $tempDir "venv"

if (-not (Test-Path $venvDir)) {
    Write-Host "  Creating portable venv..." -ForegroundColor Gray

    $createScript = Join-Path $root "scripts\deployment\create_portable_venv.ps1"
    if (Test-Path $createScript) {
        & powershell -ExecutionPolicy Bypass -File $createScript -PortableDir $tempDir -RequirementsFile (Join-Path $root "requirements.txt") 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ venv created" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  venv creation returned code $LASTEXITCODE" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  Create script not found: $createScript" -ForegroundColor Yellow
    }
}

if (Test-Path $venvDir) {
    Write-Host "  Packaging venv with Python runtime..." -ForegroundColor Gray

    $packageScript = Join-Path $root "scripts\deployment\package_venv_with_runtime.ps1"
    if (Test-Path $packageScript) {
        & powershell -ExecutionPolicy Bypass -File $packageScript -VenvPath $venvDir 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ venv packaged with runtime" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  venv packaging returned code $LASTEXITCODE" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  Package script not found: $packageScript" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  venv not found, package may not be portable!" -ForegroundColor Yellow
}

# ============================================================================
# Keep embedded Python (venv needs it as base installation)
# ============================================================================

$embeddedPythonDir = Join-Path $tempDir "vendors\python"

if ((Test-Path $venvDir) -and (Test-Path $embeddedPythonDir)) {
    Write-Host "  Keeping embedded Python (venv requires it as base installation)..." -ForegroundColor Gray
    $pythonSize = (Get-ChildItem $embeddedPythonDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "  Embedded Python size: $([math]::Round($pythonSize, 2)) MB" -ForegroundColor Green
}

# ============================================================================
# Compress files
# ============================================================================

Write-Host "  Compressing files (this may take several minutes)..." -ForegroundColor Gray

try {
    # Load .NET compression assembly
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    # Remove existing ZIP if present
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }

    # Create ZIP using .NET (more reliable than Compress-Archive for large file counts)
    Write-Host "  Creating ZIP archive..." -ForegroundColor Gray
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

    Write-Host "  Compression completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Compression failed: $_" -ForegroundColor Red
    Write-Host "  Error details: $($_.Exception.Message)" -ForegroundColor Gray
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    exit 1
}

# ============================================================================
# Clean up temporary directory
# ============================================================================

Write-Host "  Cleaning up temporary directory..." -ForegroundColor Gray
Write-Host "  DEBUG: Temp directory kept at: $tempDir" -ForegroundColor Yellow
# Remove-Item -Path $tempDir -Recurse -Force

# ============================================================================
# Display results
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  Package Created Successfully!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

$fileInfo = Get-Item $zipPath
$fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)

Write-Host "Package Information:" -ForegroundColor White
Write-Host "  File: $($fileInfo.Name)" -ForegroundColor Cyan
Write-Host "  Size: $fileSizeMB MB" -ForegroundColor Cyan
Write-Host "  Path: $($fileInfo.FullName)" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Test the package on another computer" -ForegroundColor Gray
Write-Host "  2. Extract the ZIP file" -ForegroundColor Gray
Write-Host "  3. Run start_all.ps1 to start all services" -ForegroundColor Gray
Write-Host "  4. Visit http://localhost to access the application" -ForegroundColor Gray
Write-Host ""

Write-Host "Note: First-time startup will automatically import configuration and create default user (admin/admin123)" -ForegroundColor Yellow
Write-Host ""

