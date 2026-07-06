# TradingAgents-CN Services Starter (Clean English Version)
# Start MongoDB and Redis services without Chinese characters

param(
    [switch]$SkipMongoDB,
    [switch]$SkipRedis
)

$root = $PSScriptRoot
$envPath = Join-Path $root '.env'
function Load-Env($path) {
    $map = @{}
    if (Test-Path -LiteralPath $path) {
        foreach ($line in Get-Content -LiteralPath $path) {
            if ($line -match '^\s*#') { continue }
            if ($line -match '^\s*$') { continue }
            $idx = $line.IndexOf('=')
            if ($idx -gt 0) {
                $key = $line.Substring(0, $idx).Trim()
                $val = $line.Substring($idx + 1).Trim()
                $map[$key] = $val
            }
        }
    }
    return $map
}

$envMap = Load-Env $envPath
$mongoPort = if ($envMap.ContainsKey('MONGODB_PORT')) { [int]$envMap['MONGODB_PORT'] } else { 27017 }
$redisPort = if ($envMap.ContainsKey('REDIS_PORT')) { [int]$envMap['REDIS_PORT'] } else { 6379 }
$mongoExe = Join-Path $root 'vendors\mongodb\mongodb-win32-x86_64-windows-8.0.13\bin\mongod.exe'
$redisExe = Join-Path $root 'vendors\redis\Redis-8.2.2-Windows-x64-msys2\redis-server.exe'
$mongoData = Join-Path $root 'data\mongodb\db'
$redisData = Join-Path $root 'data\redis\data'

function Ensure-Dir($path) {
    if (-not (Test-Path -LiteralPath $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

function Check-Port($Port, $ServiceName) {
    Write-Host "  Checking port $Port..." -ForegroundColor Gray
    $portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Host "  WARNING: Port $Port is already in use!" -ForegroundColor Yellow
        foreach ($conn in $portInUse) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "    Process: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Gray

                # Check if it's the same service
                $shouldStop = $false
                if ($ServiceName -eq "MongoDB" -and $process.ProcessName -eq "mongod") {
                    $shouldStop = $true
                } elseif ($ServiceName -eq "Redis" -and $process.ProcessName -eq "redis-server") {
                    $shouldStop = $true
                }

                if ($shouldStop) {
                    Write-Host "  Stopping existing $ServiceName process (PID: $($process.Id))..." -ForegroundColor Yellow
                    try {
                        Stop-Process -Id $process.Id -Force -ErrorAction Stop
                        Start-Sleep -Seconds 2
                        Write-Host "  Existing $ServiceName process stopped" -ForegroundColor Green
                    } catch {
                        Write-Host "  ERROR: Failed to stop process: $_" -ForegroundColor Red
                        return $false
                    }
                } else {
                    Write-Host "  ERROR: Port $Port is occupied by another application" -ForegroundColor Red
                    return $false
                }
            }
        }
    }
    return $true
}

function Start-Proc($FilePath, $Arguments, $Name, $WaitSeconds = 3, $WorkingDirectory = $null) {
    Write-Host "Starting $Name..."
    Write-Host "  Command: $FilePath $Arguments"
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $FilePath
        $psi.Arguments = $Arguments
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true

        # Set working directory if provided
        if ($WorkingDirectory) {
            $psi.WorkingDirectory = $WorkingDirectory
            Write-Host "  Working Directory: $WorkingDirectory"
        }

        $process = [System.Diagnostics.Process]::Start($psi)
        Write-Host "  Process started, waiting $WaitSeconds seconds..."
        Start-Sleep -Seconds $WaitSeconds

        if ($process.HasExited) {
            Write-Host "Failed to start $Name (process exited)"
            $stdout = $process.StandardOutput.ReadToEnd()
            $stderr = $process.StandardError.ReadToEnd()
            if ($stdout) { Write-Host "  STDOUT: $stdout" }
            if ($stderr) { Write-Host "  STDERR: $stderr" }
            return $null
        } else {
            Write-Host "$Name started with PID: $($process.Id)"
            return $process
        }
    } catch {
        Write-Host "Error starting $Name`: $_"
        return $null
    }
}

# Start MongoDB
if (-not $SkipMongoDB -and (Test-Path -LiteralPath $mongoExe)) {
    if (-not (Check-Port -Port $mongoPort -ServiceName "MongoDB")) {
        Write-Host "ERROR: Cannot start MongoDB - port 27017 is not available" -ForegroundColor Red
        exit 1
    }

    Ensure-Dir $mongoData

    # Check if MongoDB is already initialized
    $initMarker = Join-Path $mongoData '.mongo_initialized'
    if (-not (Test-Path $initMarker)) {
        Write-Host "Initializing MongoDB for first time..."
        
        # Start MongoDB without auth first
        Write-Host "Starting MongoDB-Init..."
        $mongoArgs = "--dbpath `"$mongoData`" --bind_ip 127.0.0.1 --port $mongoPort"

        try {
            # Start MongoDB in background without redirecting output
            $mongoProc = Start-Process -FilePath $mongoExe -ArgumentList $mongoArgs -WindowStyle Hidden -PassThru
            Write-Host "  MongoDB-Init started with PID: $($mongoProc.Id)"

            # Wait longer for MongoDB to be ready
            Write-Host "Waiting for MongoDB to be ready..."
            Start-Sleep -Seconds 15

            # Create admin user using Python script
            Write-Host "Creating MongoDB admin user..."
            $pythonExe = Join-Path $root 'venv\Scripts\python.exe'
            if (-not (Test-Path $pythonExe)) {
                Write-Host "  ERROR: Python virtual environment not found at: $pythonExe" -ForegroundColor Red
                Write-Host "  Please ensure the portable package is complete and extracted correctly." -ForegroundColor Yellow
                return $false
            }

            # Test Python first
            Write-Host "  Testing Python: $pythonExe" -ForegroundColor Gray
            try {
                $pythonTest = & $pythonExe --version 2>&1
                Write-Host "  Python version: $pythonTest" -ForegroundColor Gray
            } catch {
                Write-Host "  ERROR: Python failed to run: $_" -ForegroundColor Red
                Write-Host "  Exception details: $($_.Exception.Message)" -ForegroundColor Red
                return $false
            }

            $initScript = Join-Path $root 'scripts\init_mongodb_user.py'
            if (Test-Path $initScript) {
                try {
                    Write-Host "  Running: $pythonExe $initScript 127.0.0.1 27017 admin ***" -ForegroundColor Gray
                    $output = & $pythonExe $initScript 127.0.0.1 27017 admin tradingagents123 2>&1

                    # Print all output
                    if ($output) {
                        $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                    }

                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  MongoDB admin user initialized successfully" -ForegroundColor Green
                        # Note: Configuration import is handled by start_all.ps1
                    } else {
                        Write-Host "  Warning: MongoDB user initialization returned exit code $LASTEXITCODE" -ForegroundColor Yellow
                        Write-Host "  This may be normal if the user already exists." -ForegroundColor Gray
                    }
                } catch {
                    Write-Host "  Warning: Failed to initialize MongoDB user: $_" -ForegroundColor Yellow
                    Write-Host "  Exception details: $($_.Exception.Message)" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  Warning: MongoDB init script not found at $initScript" -ForegroundColor Yellow
            }

            # Stop MongoDB
            Write-Host "Stopping MongoDB-Init..."
            try {
                $mongoProc.Kill()
                $mongoProc.WaitForExit(5000)
                Write-Host "  MongoDB-Init stopped"
            } catch {
                Write-Host "  Warning: Failed to stop MongoDB init process"
            }

            # Mark as initialized
            Set-Content -Path $initMarker -Value (Get-Date) -Encoding UTF8
            Write-Host "MongoDB initialization completed"
        } catch {
            Write-Host "Error during MongoDB initialization: $_"
        }
    }
    
    # Start MongoDB with auth
    $mongoArgs = "--dbpath `"$mongoData`" --bind_ip 127.0.0.1 --port $mongoPort --auth"
    $mongoProc = Start-Proc -FilePath $mongoExe -Arguments $mongoArgs -Name 'MongoDB'
} else {
    Write-Host "MongoDB skipped or binary not found"
}

# Start Redis
if (-not $SkipRedis -and (Test-Path -LiteralPath $redisExe)) {
    if (-not (Check-Port -Port $redisPort -ServiceName "Redis")) {
        Write-Host "ERROR: Cannot start Redis - port 6379 is not available" -ForegroundColor Red
        exit 1
    }

    # Ensure Redis data directory exists
    Ensure-Dir $redisData
    Ensure-Dir (Join-Path $root 'runtime')

    $redisConf = Join-Path $root 'runtime\redis.conf'

    # Create Redis config with proper path format
    # Redis on Windows needs forward slashes or escaped backslashes
    $redisDataUnix = $redisData -replace '\\', '/'
    $conf = @(
        "bind 127.0.0.1",
        "port $redisPort",
        "dir $redisDataUnix",
        "requirepass tradingagents123",
        "appendonly yes",
        "save 900 1",
        "save 300 10",
        "save 60 10000"
    )
    # Use UTF8 without BOM to avoid Redis parsing errors
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($redisConf, ($conf -join "`n"), $utf8NoBom)

    # Redis needs more time to initialize, wait 5 seconds
    # Use relative path with WorkingDirectory to avoid Cygwin path issues
    $redisConfRelative = "runtime\redis.conf"
    $redisProc = Start-Proc -FilePath $redisExe -Arguments "`"$redisConfRelative`"" -Name 'Redis' -WaitSeconds 5 -WorkingDirectory $root
} else {
    Write-Host "Redis skipped or binary not found"
}

Write-Host "Services startup completed."
Write-Host "MongoDB should be available at: 127.0.0.1:27017"
Write-Host "Redis should be available at: 127.0.0.1:6379"
