<#
Downloads Windows portable binaries (zip) for nginx, MongoDB, and Redis
into a target directory for packaging. Intended for maintainers at build time.

Note: End users are NOT required to run this script. The assembled release
will already include these binaries.

Usage:
  powershell -ExecutionPolicy Bypass -File scripts/deployment/get_vendors.ps1 -TargetDir ./vendors
#>

[CmdletBinding()]
param(
  [string]$TargetDir = "vendors",
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$path) { if (-not (Test-Path -LiteralPath $path)) { New-Item -ItemType Directory -Path $path | Out-Null } }

function Download-And-Extract {
  param(
    [string]$Name,
    [string]$Url,
    [string]$OutDir,
    [string]$ExpectedExe,
    [string]$SubDirHint
  )
  Write-Host "Downloading $Name from $Url" -ForegroundColor Cyan
  $zipPath = Join-Path $OutDir "$Name.zip"
  if ((Test-Path -LiteralPath $zipPath) -and -not $Force) {
    Write-Host "Zip already exists: $zipPath (use -Force to re-download)" -ForegroundColor Yellow
  } else {
    try {
      Invoke-WebRequest -Uri $Url -OutFile $zipPath -UseBasicParsing
    } catch {
      Write-Host "Failed to download ${Name}: $($_.Exception.Message)" -ForegroundColor Red
      return $false
    }
  }

  $extractDir = Join-Path $OutDir "tmp_$Name"
  if (Test-Path -LiteralPath $extractDir) { Remove-Item -Recurse -Force -LiteralPath $extractDir }
  Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force

  # Find the folder containing the expected exe
  $exePath = Get-ChildItem -LiteralPath $extractDir -Recurse -Filter $ExpectedExe -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $exePath) {
    Write-Host "Could not locate $ExpectedExe inside $Name archive" -ForegroundColor Red
    return $false
  }

  # Normalize to component directory name
  $componentDir = Join-Path $OutDir $Name
  if (Test-Path -LiteralPath $componentDir) { Remove-Item -Recurse -Force -LiteralPath $componentDir }
  New-Item -ItemType Directory -Path $componentDir | Out-Null

  # Move extracted contents under normalized directory
  Get-ChildItem -LiteralPath $extractDir | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination $componentDir
  }
  Remove-Item -Recurse -Force -LiteralPath $extractDir

  Write-Host "$Name staged at: $componentDir" -ForegroundColor Green
  return $true
}

$root = (Resolve-Path ".").Path
$absTarget = if ([System.IO.Path]::IsPathRooted($TargetDir)) { $TargetDir } else { Join-Path $root $TargetDir }
Ensure-Dir $absTarget

# nginx: Windows zip (mainline recommended)
$nginxUrl = "https://nginx.org/download/nginx-1.29.3.zip"
Download-And-Extract -Name 'nginx' -Url $nginxUrl -OutDir $absTarget -ExpectedExe 'nginx.exe' | Out-Null

# MongoDB: Windows x64 archive (Community)
$mongoUrl = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.13.zip"
Download-And-Extract -Name 'mongodb' -Url $mongoUrl -OutDir $absTarget -ExpectedExe 'mongod.exe' | Out-Null

# Redis: Windows builds are not official upstream; commonly from GitHub releases
# This download may fail in environments blocking GitHub. If so, place a redis zip
# under install/vendors and use stage_local_vendors.ps1.
$redisUrl = "https://github.com/tporadowski/redis/releases/download/v7.2.4/redis-7.2.4.zip"
try {
  Download-And-Extract -Name 'redis' -Url $redisUrl -OutDir $absTarget -ExpectedExe 'redis-server.exe' | Out-Null
} catch {
  Write-Host "Redis download failed or blocked. Please place a redis*.zip under install/vendors and use stage_local_vendors.ps1" -ForegroundColor Yellow
}

Write-Host "Vendor downloads completed (where possible)." -ForegroundColor Green