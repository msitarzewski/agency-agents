<#
TradingAgents-CN Windows Portable Stopper
Stops MongoDB, Redis, backend, optional Nginx based on runtime\pids.json.
Encoding-safe version: ASCII-only output.
#>

$ErrorActionPreference = 'Stop'

function Stop-ByPid {
    param([int]$ProcessId, [string]$Name)
    try {
        Write-Host "Stopping $Name (PID $ProcessId) ..."
        Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        Write-Host "$Name stopped"
    } catch {
        Write-Host "Failed to stop $Name by PID; it may have exited already"
    }
}

$root = (Get-Location).Path
$pidFile = Join-Path $root 'runtime\pids.json'

if (Test-Path -LiteralPath $pidFile) {
    $content = Get-Content -LiteralPath $pidFile -Raw
    $pids = $null
    try { $pids = $content | ConvertFrom-Json } catch {}
    if ($pids -ne $null) {
        if ($pids.mongodb) { Stop-ByPid -ProcessId ([int]$pids.mongodb) -Name 'MongoDB' }
        if ($pids.redis) { Stop-ByPid -ProcessId ([int]$pids.redis) -Name 'Redis' }
        if ($pids.backend) { Stop-ByPid -ProcessId ([int]$pids.backend) -Name 'Backend' }
        if ($pids.nginx) { Stop-ByPid -ProcessId ([int]$pids.nginx) -Name 'Nginx' }
    }
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "PID file removed"
} else {
    Write-Host "PID file not found; trying to stop by process name"
    Get-Process -Name 'mongod' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name 'redis-server' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name 'python' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name 'nginx' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

Write-Host "All stop operations completed"