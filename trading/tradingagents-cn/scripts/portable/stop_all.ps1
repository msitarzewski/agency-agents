<#
TradingAgents-CN Stop All Services Script

Features:
1. Stop all TradingAgents-CN related processes
2. Support graceful stop via PID file
3. Support force stop all related processes
4. Clean up temporary files and PID files

Usage:
  .\stop_all.ps1              # Normal stop (try PID file first, then force stop)
  .\stop_all.ps1 -Force       # Force stop all related processes
  .\stop_all.ps1 -OnlyPid     # Only use PID file to stop
#>

[CmdletBinding()]
param(
    [switch]$Force,      # Force stop all related processes
    [switch]$OnlyPid,    # Only use PID file to stop
    [switch]$Quiet       # Quiet mode, reduce output
)

$ErrorActionPreference = 'Continue'

function Write-Info {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor Cyan
    }
}

function Write-Success {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor Green
    }
}

function Write-Warning {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor Yellow
    }
}

function Write-Error {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Stop-ProcessByPid {
    param(
        [int]$ProcessId,
        [string]$Name = "Process"
    )
    
    try {
        $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Info "  Stopping $Name (PID: $ProcessId)..."
            Stop-Process -Id $ProcessId -Force -ErrorAction Stop
            Start-Sleep -Milliseconds 500
            
            # Verify process stopped
            $stillRunning = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
            if ($stillRunning) {
                Write-Warning "  Process $ProcessId still running, force terminating..."
                Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
            } else {
                Write-Success "  [OK] $Name stopped"
            }
            return $true
        } else {
            Write-Info "  Process $ProcessId not found or already stopped"
            return $false
        }
    } catch {
        Write-Warning "  Failed to stop process $ProcessId : $($_.Exception.Message)"
        return $false
    }
}

function Stop-ProcessByName {
    param(
        [string]$ProcessName,
        [string]$DisplayName = ""
    )
    
    if ($DisplayName -eq "") {
        $DisplayName = $ProcessName
    }
    
    try {
        $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
        if ($processes) {
            $count = ($processes | Measure-Object).Count
            Write-Info "  Found $count $DisplayName process(es), stopping..."
            
            foreach ($proc in $processes) {
                try {
                    Write-Info "    Stopping $DisplayName (PID: $($proc.Id))..."
                    Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                } catch {
                    Write-Warning "    Failed to stop process $($proc.Id): $($_.Exception.Message)"
                }
            }
            
            Start-Sleep -Seconds 1
            
            # Verify no remaining processes
            $remaining = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
            if ($remaining) {
                Write-Warning "  Still $((($remaining | Measure-Object).Count)) $DisplayName process(es) running"
                return $false
            } else {
                Write-Success "  [OK] All $DisplayName processes stopped"
                return $true
            }
        } else {
            Write-Info "  No $DisplayName processes found"
            return $true
        }
    } catch {
        Write-Warning "  Failed to stop $DisplayName processes: $($_.Exception.Message)"
        return $false
    }
}

function Stop-NginxGracefully {
    param([string]$NginxExe)
    
    if (Test-Path $NginxExe) {
        Write-Info "  Trying graceful Nginx shutdown..."
        try {
            $nginxDir = Split-Path -Parent $NginxExe
            Push-Location $nginxDir
            & $NginxExe -s quit
            Pop-Location
            Start-Sleep -Seconds 1
            Write-Success "  [OK] Nginx graceful shutdown command sent"
            return $true
        } catch {
            Write-Warning "  Nginx graceful shutdown failed: $($_.Exception.Message)"
            return $false
        }
    }
    return $false
}

# ============================================
# Main Program
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TradingAgents-CN Stop All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$root = Get-Location
$pidFile = Join-Path $root 'runtime\pids.json'
$stoppedCount = 0
$failedCount = 0

# ============================================
# Step 1: Stop services using PID file (graceful stop)
# ============================================

if (-not $Force) {
    Write-Info "Step 1: Trying to stop services using PID file..."
    
    if (Test-Path $pidFile) {
        try {
            $pids = Get-Content $pidFile -Raw | ConvertFrom-Json
            
            # Stop Nginx
            if ($pids.nginx) {
                Write-Info "Stopping Nginx..."
                
                # Try graceful stop first
                $nginxExe = Get-ChildItem -Path (Join-Path $root 'vendors\nginx') -Recurse -Filter 'nginx.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
                $graceful = Stop-NginxGracefully -NginxExe $nginxExe
                
                if (-not $graceful) {
                    if (Stop-ProcessByPid -ProcessId $pids.nginx -Name "Nginx") {
                        $stoppedCount++
                    } else {
                        $failedCount++
                    }
                } else {
                    $stoppedCount++
                }
            }
            
            # Stop Backend
            if ($pids.backend) {
                Write-Info "Stopping Backend (FastAPI)..."
                if (Stop-ProcessByPid -ProcessId $pids.backend -Name "Backend") {
                    $stoppedCount++
                } else {
                    $failedCount++
                }
            }
            
            # Stop Redis
            if ($pids.redis) {
                Write-Info "Stopping Redis..."
                if (Stop-ProcessByPid -ProcessId $pids.redis -Name "Redis") {
                    $stoppedCount++
                } else {
                    $failedCount++
                }
            }
            
            # Stop MongoDB
            if ($pids.mongodb) {
                Write-Info "Stopping MongoDB..."
                if (Stop-ProcessByPid -ProcessId $pids.mongodb -Name "MongoDB") {
                    $stoppedCount++
                } else {
                    $failedCount++
                }
            }
            
            Write-Success "`n[OK] PID file processed (Success: $stoppedCount, Failed: $failedCount)"
            
        } catch {
            Write-Warning "Failed to read or process PID file: $($_.Exception.Message)"
        }
    } else {
        Write-Warning "PID file not found: $pidFile"
    }
}

# ============================================
# Step 2: Force stop all related processes (fallback)
# ============================================

if ($Force -or (-not $OnlyPid)) {
    Write-Host ""
    Write-Info "Step 2: Force stopping all related processes..."
    
    # Define processes to stop
    $processesToStop = @(
        @{Name = "nginx"; Display = "Nginx"},
        @{Name = "python"; Display = "Python (Backend)"},
        @{Name = "pythonw"; Display = "Python (Background)"},
        @{Name = "redis-server"; Display = "Redis"},
        @{Name = "mongod"; Display = "MongoDB"}
    )
    
    foreach ($proc in $processesToStop) {
        Stop-ProcessByName -ProcessName $proc.Name -DisplayName $proc.Display | Out-Null
    }
    
    Write-Success "`n[OK] Force stop completed"
}

# ============================================
# Cleanup
# ============================================

Write-Host ""
Write-Info "Step 3: Cleaning up temporary files..."

# Remove PID file
if (Test-Path $pidFile) {
    try {
        Remove-Item $pidFile -Force -ErrorAction Stop
        Write-Success "  [OK] PID file removed"
    } catch {
        Write-Warning "  Failed to remove PID file: $($_.Exception.Message)"
    }
}

# Clean Nginx PID file
$nginxPidFile = Join-Path $root 'logs\nginx.pid'
if (Test-Path $nginxPidFile) {
    try {
        Remove-Item $nginxPidFile -Force -ErrorAction Stop
        Write-Success "  [OK] Nginx PID file removed"
    } catch {
        Write-Warning "  Failed to remove Nginx PID file: $($_.Exception.Message)"
    }
}

# Clean temporary directories (optional)
$tempDirs = @(
    'temp\client_body_temp',
    'temp\proxy_temp',
    'temp\fastcgi_temp',
    'temp\uwsgi_temp',
    'temp\scgi_temp'
)

foreach ($dir in $tempDirs) {
    $fullPath = Join-Path $root $dir
    if (Test-Path $fullPath) {
        try {
            Get-ChildItem -Path $fullPath -File | Remove-Item -Force -ErrorAction SilentlyContinue
        } catch {
            # Ignore cleanup errors
        }
    }
}

Write-Success "  [OK] Temporary files cleaned up"

# ============================================
# Final Verification
# ============================================

Write-Host ""
Write-Info "Step 4: Verifying service status..."

$stillRunning = @()

# Check if services are still running
$checkProcesses = @("nginx", "python", "pythonw", "redis-server", "mongod")
foreach ($procName in $checkProcesses) {
    $procs = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($procs) {
        $count = ($procs | Measure-Object).Count
        $stillRunning += "$procName ($count process(es))"
    }
}

if ($stillRunning.Count -gt 0) {
    Write-Warning "`nWARNING: The following services are still running:"
    foreach ($item in $stillRunning) {
        Write-Warning "  - $item"
    }
    Write-Host ""
    Write-Warning "Suggestions:"
    Write-Warning "  1. Run again: .\stop_all.ps1 -Force"
    Write-Warning "  2. Or manually terminate these processes in Task Manager"
} else {
    Write-Success "`n[OK] All services stopped successfully!"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stop Services Completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

