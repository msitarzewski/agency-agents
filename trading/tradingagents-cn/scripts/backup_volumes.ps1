# Backup TradingAgents-CN Docker Volumes
# This script backs up MongoDB and Redis data volumes

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $ProjectRoot "backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupPath = Join-Path $BackupDir $Timestamp

Write-Host "[INFO] Creating backup directory: $BackupPath" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null

$Volumes = @(
    @{
        Name = "tradingagents_mongodb_data"
        Container = "tradingagents-mongodb"
        BackupFile = "mongodb_backup.tar"
        Description = "MongoDB Data"
    },
    @{
        Name = "tradingagents_redis_data"
        Container = "tradingagents-redis"
        BackupFile = "redis_backup.tar"
        Description = "Redis Data"
    }
)

Write-Host ""
Write-Host "[INFO] Checking container status..." -ForegroundColor Cyan

$RunningContainers = docker ps --format "{{.Names}}"
$AllContainers = docker ps -a --format "{{.Names}}"

foreach ($Volume in $Volumes) {
    $ContainerName = $Volume.Container

    if ($AllContainers -notcontains $ContainerName) {
        Write-Host "[WARN] Container $ContainerName does not exist, skipping" -ForegroundColor Yellow
        continue
    }

    $IsRunning = $RunningContainers -contains $ContainerName

    if (-not $IsRunning) {
        Write-Host "[WARN] Container $ContainerName is not running, starting..." -ForegroundColor Yellow
        docker start $ContainerName | Out-Null
        Start-Sleep -Seconds 3
    }
}

Write-Host ""
Write-Host "[INFO] Starting backup..." -ForegroundColor Green
Write-Host ""

foreach ($Volume in $Volumes) {
    $VolumeName = $Volume.Name
    $ContainerName = $Volume.Container
    $BackupFile = Join-Path $BackupPath $Volume.BackupFile
    $Description = $Volume.Description

    Write-Host "[INFO] Backing up $Description ($VolumeName)..." -ForegroundColor Cyan

    try {
        $VolumeExists = docker volume ls --format "{{.Name}}" | Select-String -Pattern "^$VolumeName$"

        if (-not $VolumeExists) {
            Write-Host "  [WARN] Volume $VolumeName does not exist, skipping" -ForegroundColor Yellow
            continue
        }

        Write-Host "  [INFO] Creating backup..." -ForegroundColor Gray

        docker run --rm `
            -v ${VolumeName}:/data `
            -v ${BackupPath}:/backup `
            alpine `
            tar czf /backup/$($Volume.BackupFile) -C /data .

        if ($LASTEXITCODE -eq 0) {
            $FileSize = (Get-Item $BackupFile).Length / 1MB
            Write-Host "  [OK] Backup successful: $BackupFile ($([math]::Round($FileSize, 2)) MB)" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Backup failed" -ForegroundColor Red
        }

    } catch {
        Write-Host "  [ERROR] Backup failed: $_" -ForegroundColor Red
    }

    Write-Host ""
}

$Metadata = @{
    timestamp = $Timestamp
    date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    volumes = $Volumes | ForEach-Object {
        @{
            name = $_.Name
            container = $_.Container
            backup_file = $_.BackupFile
            description = $_.Description
        }
    }
    docker_version = (docker version --format "{{.Server.Version}}")
    host = $env:COMPUTERNAME
}

$MetadataFile = Join-Path $BackupPath "metadata.json"
$Metadata | ConvertTo-Json -Depth 10 | Out-File -FilePath $MetadataFile -Encoding UTF8

Write-Host "[INFO] Metadata saved: $MetadataFile" -ForegroundColor Cyan
Write-Host ""

Write-Host "======================================================================" -ForegroundColor Green
Write-Host "[OK] Backup completed!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Backup location: $BackupPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Backup files:" -ForegroundColor Cyan

Get-ChildItem -Path $BackupPath | ForEach-Object {
    $Size = if ($_.Length -gt 1MB) {
        "$([math]::Round($_.Length / 1MB, 2)) MB"
    } elseif ($_.Length -gt 1KB) {
        "$([math]::Round($_.Length / 1KB, 2)) KB"
    } else {
        "$($_.Length) B"
    }
    Write-Host "  - $($_.Name) ($Size)" -ForegroundColor White
}

Write-Host ""
Write-Host "[INFO] Tips:" -ForegroundColor Yellow
Write-Host "  - Use restore_volumes.ps1 to restore backup" -ForegroundColor Gray
Write-Host "  - Backup files can be used to recover data volumes" -ForegroundColor Gray
Write-Host ""

