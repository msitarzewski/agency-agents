param(
    [int]$BackendPort = 8000,
    [int]$MongoPort = 27017,
    [int]$RedisPort = 6379,
    [int]$NginxPort = 80,
    [int]$TimeoutSeconds = 10,
    [int]$MaxAttempts = 100,
    [ValidateSet('json','kv')][string]$Output = 'kv'
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Probe-Port {
    param([int]$Port)
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        return $connection -ne $null
    } catch {
        return $false
    }
}

Write-Log "Starting port detection..."
Write-Log "Backend Port: $BackendPort"
Write-Log "MongoDB Port: $MongoPort"
Write-Log "Redis Port: $RedisPort"
Write-Log "Nginx Port: $NginxPort"

$result = @{
    Backend = $BackendPort
    Mongo = $MongoPort
    Redis = $RedisPort
    Nginx = $NginxPort
}

$jobs = @()
$jobs += Start-Job -ScriptBlock { param($p) Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue } -ArgumentList $BackendPort
$jobs += Start-Job -ScriptBlock { param($p) Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue } -ArgumentList $MongoPort
$jobs += Start-Job -ScriptBlock { param($p) Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue } -ArgumentList $RedisPort
$jobs += Start-Job -ScriptBlock { param($p) Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue } -ArgumentList $NginxPort

$timeout = (Get-Date).AddSeconds($TimeoutSeconds)
$completed = 0
while ((Get-Date) -lt $timeout -and $completed -lt 4) {
    $completed = ($jobs | Where-Object { $_.State -eq "Completed" }).Count
    Start-Sleep -Milliseconds 100
}

$portMap = @{ 0 = "Backend"; 1 = "Mongo"; 2 = "Redis"; 3 = "Nginx" }
$portValues = @($BackendPort, $MongoPort, $RedisPort, $NginxPort)

for ($i = 0; $i -lt 4; $i++) {
    $job = $jobs[$i]
    $portName = $portMap[$i]
    $port = $portValues[$i]
    
    if ($job.State -eq "Completed") {
        $output = Receive-Job -Job $job
        if ($output) {
            Write-Log "Port $port ($portName) is in use, finding alternative..."
            for ($newPort = $port + 1; $newPort -le 65535; $newPort++) {
                if (-not (Probe-Port $newPort)) {
                    $result[$portName] = $newPort
                    Write-Log "Found available port: $newPort for $portName"
                    break
                }
            }
        } else {
            Write-Log "Port $port ($portName) is available"
        }
    } else {
        Write-Log "Port detection timeout for $portName, using default: $port" "WARNING"
    }
    
    Remove-Job -Job $job -Force
}

if ($Output -eq 'json') {
    $result | ConvertTo-Json
} else {
    Write-Output "Backend=$($result.Backend)"
    Write-Output "Mongo=$($result.Mongo)"
    Write-Output "Redis=$($result.Redis)"
    Write-Output "Nginx=$($result.Nginx)"
}
