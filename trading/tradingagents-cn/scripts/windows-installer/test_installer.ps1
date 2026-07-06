param(
    [string]$InstallerPath,
    [string]$TestDir = "C:\TradingAgentsCN_Test"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

Write-Log "=========================================="
Write-Log "TradingAgentsCN Installer Test"
Write-Log "=========================================="

if (-not $InstallerPath) {
    $root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    $InstallerPath = Join-Path $root "scripts\windows-installer\nsis\TradingAgentsCNSetup-1.0.0.exe"
}

Write-Log "Installer Path: $InstallerPath"

if (-not (Test-Path $InstallerPath)) {
    Write-Log "Installer not found: $InstallerPath" "ERROR"
    exit 1
}

Write-Log "Installer found"

$fileSize = (Get-Item $InstallerPath).Length / 1MB
Write-Log "Installer Size: $([Math]::Round($fileSize, 2)) MB"

Write-Log ""
Write-Log "Checking NSIS installation..."
$nsisPath = $null
$candidates = @()
if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles 'NSIS') }
$pf86 = ${env:ProgramFiles(x86)}
if ($pf86) { $candidates += (Join-Path $pf86 'NSIS') }

foreach ($p in $candidates) {
    $exe = Join-Path $p 'makensis.exe'
    if (Test-Path -LiteralPath $exe) {
        $nsisPath = $p
        Write-Log "Found NSIS: $nsisPath"
        break
    }
}

if (-not $nsisPath) {
    Write-Log "NSIS not installed, cannot verify installer contents" "WARNING"
} else {
    Write-Log "NSIS installed, full testing available"
}

Write-Log ""
Write-Log "Checking portable version..."
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$portableDir = Join-Path $root "release\portable"

if (Test-Path $portableDir) {
    Write-Log "Portable version directory exists: $portableDir"
    
    $requiredDirs = @("app", "scripts\installer", "runtime", "logs", "data")
    foreach ($dir in $requiredDirs) {
        $fullPath = Join-Path $portableDir $dir
        if (Test-Path $fullPath) {
            Write-Log "OK: $dir directory exists"
        } else {
            Write-Log "MISSING: $dir directory" "WARNING"
        }
    }
    
    $requiredFiles = @(".env.example", "runtime\nginx.conf")
    foreach ($file in $requiredFiles) {
        $fullPath = Join-Path $portableDir $file
        if (Test-Path $fullPath) {
            Write-Log "OK: $file file exists"
        } else {
            Write-Log "MISSING: $file file" "WARNING"
        }
    }
} else {
    Write-Log "Portable version directory not found: $portableDir" "WARNING"
}

Write-Log ""
Write-Log "=========================================="
Write-Log "Test Completed"
Write-Log "=========================================="
Write-Log "Recommendations:"
Write-Log "1. Run installer for full installation test"
Write-Log "2. Verify all services start correctly"
Write-Log "3. Check Web UI accessibility"
Write-Log "4. Test uninstall functionality"
