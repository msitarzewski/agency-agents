<#
TradingAgents-CN Windows Portable Setup
This script initializes a portable environment (.env, directories) for Windows.
Encoding-safe version: ASCII-only output, no emoji or non-ASCII symbols.
#>

[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [string]$AppHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$AppDebug,
    [switch]$ServeFrontend,
    [string]$FrontendStatic = "frontend\dist",
    [switch]$EnableNginx,
    [switch]$AutoOpenBrowser,
    [string]$MongoHost = "127.0.0.1",
    [int]$MongoPort = 27017,
    [string]$MongoDb = "tradingagents",
    [string]$RedisHost = "127.0.0.1",
    [int]$RedisPort = 6379,
    [int]$NginxPort = 80
)

$ErrorActionPreference = 'Stop'

function New-SecureSecret {
    param([int]$Length = 32)
    $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    $bytes = New-Object byte[] ($Length)
    $rng.GetBytes($bytes)
    [Convert]::ToBase64String($bytes).TrimEnd('=')
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
}

function Set-EnvLine {
    param(
        [string]$File,
        [string]$Key,
        [string]$Value
    )
    # Append-only in ASCII to avoid rewriting entire file and breaking comments/encoding
    Add-Content -Path $File -Value "$Key=$Value" -Encoding ASCII
}

Write-Host "TradingAgents-CN Windows Setup"
Write-Host "Initializing environment and configuration..."

$root = (Get-Location).Path
$envFile = Join-Path $root '.env'
$envExample = Join-Path $root '.env.example'

# Copy template env if exists
if (Test-Path -LiteralPath $envExample -PathType Leaf) {
    if (-not (Test-Path -LiteralPath $envFile)) {
        Copy-Item -LiteralPath $envExample -Destination $envFile
        Write-Host ".env created from .env.example"
    } else {
        Write-Host ".env already exists; will append/update keys"
    }
} else {
    if (-not (Test-Path -LiteralPath $envFile)) {
        New-Item -ItemType File -Path $envFile | Out-Null
        Write-Host ".env created (empty)"
    }
}

# Initialize directories
Ensure-Dir (Join-Path $root 'data')
Ensure-Dir (Join-Path $root 'data\mongodb')
Ensure-Dir (Join-Path $root 'data\mongodb\db')
Ensure-Dir (Join-Path $root 'data\redis')
Ensure-Dir (Join-Path $root 'data\redis\data')
Ensure-Dir (Join-Path $root 'runtime')
Ensure-Dir (Join-Path $root 'logs')

if (-not $NonInteractive) {
    Write-Host "Non-interactive options can be provided via parameters."
}

$jwt = New-SecureSecret 48
$csrf = New-SecureSecret 48

# Append core env keys (ASCII-only)
Set-EnvLine -File $envFile -Key 'JWT_SECRET' -Value $jwt
Set-EnvLine -File $envFile -Key 'CSRF_SECRET' -Value $csrf
Set-EnvLine -File $envFile -Key 'HOST' -Value $AppHost
Set-EnvLine -File $envFile -Key 'PORT' -Value $Port
Set-EnvLine -File $envFile -Key 'DEBUG' -Value ([string]([bool]$AppDebug))

# Frontend serving
if ($ServeFrontend -or -not $NonInteractive) {
    Set-EnvLine -File $envFile -Key 'SERVE_FRONTEND' -Value 'true'
    Set-EnvLine -File $envFile -Key 'FRONTEND_STATIC' -Value $FrontendStatic
} else {
    Set-EnvLine -File $envFile -Key 'SERVE_FRONTEND' -Value 'false'
}

# Browser auto-open
if ($AutoOpenBrowser -or -not $NonInteractive) {
    Set-EnvLine -File $envFile -Key 'AUTO_OPEN_BROWSER' -Value 'true'
} else {
    Set-EnvLine -File $envFile -Key 'AUTO_OPEN_BROWSER' -Value 'false'
}

# Mongo / Redis
Set-EnvLine -File $envFile -Key 'MONGODB_HOST' -Value $MongoHost
Set-EnvLine -File $envFile -Key 'MONGODB_PORT' -Value $MongoPort
Set-EnvLine -File $envFile -Key 'MONGODB_DATABASE' -Value $MongoDb
Set-EnvLine -File $envFile -Key 'REDIS_HOST' -Value $RedisHost
Set-EnvLine -File $envFile -Key 'REDIS_PORT' -Value $RedisPort
if ($EnableNginx) { Set-EnvLine -File $envFile -Key 'NGINX_PORT' -Value $NginxPort }

Write-Host "Setup completed. You can run start_all.ps1 to start services."
Write-Host "If you need Nginx/MongoDB/Redis, place binaries under vendors/."