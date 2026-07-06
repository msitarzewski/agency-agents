#!/usr/bin/env pwsh
<#
.SYNOPSIS
    清理 TradingAgents-CN Docker 数据卷

.DESCRIPTION
    此脚本用于清理 MongoDB 和 Redis 数据卷，创建全新的数据卷
    用于测试从零开始部署的场景

.PARAMETER Force
    跳过确认提示，直接清理

.EXAMPLE
    .\scripts\clean_volumes.ps1
    .\scripts\clean_volumes.ps1 -Force
#>

param(
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# 设置错误处理
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Red
Write-Host "⚠️  警告：此操作将删除所有数据卷和容器！" -ForegroundColor Red
Write-Host "=" * 70 -ForegroundColor Red
Write-Host ""
Write-Host "📦 将要删除的数据卷:" -ForegroundColor Yellow
Write-Host "   - tradingagents_mongodb_data (MongoDB 数据)" -ForegroundColor White
Write-Host "   - tradingagents_redis_data (Redis 数据)" -ForegroundColor White
Write-Host ""
Write-Host "🗑️  将要删除的容器:" -ForegroundColor Yellow
Write-Host "   - tradingagents-mongodb" -ForegroundColor White
Write-Host "   - tradingagents-redis" -ForegroundColor White
Write-Host "   - tradingagents-backend" -ForegroundColor White
Write-Host "   - tradingagents-frontend" -ForegroundColor White
Write-Host "   - tradingagents-nginx (如果存在)" -ForegroundColor White
Write-Host ""

if (-not $Force) {
    $Confirmation = Read-Host "确认清理？(yes/no)"
    if ($Confirmation -ne "yes") {
        Write-Host "❌ 已取消清理" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "🧹 开始清理..." -ForegroundColor Green
Write-Host ""

# 容器列表
$Containers = @(
    "tradingagents-nginx",
    "tradingagents-frontend",
    "tradingagents-backend",
    "tradingagents-redis",
    "tradingagents-mongodb"
)

# 数据卷列表
$Volumes = @(
    "tradingagents_mongodb_data",
    "tradingagents_redis_data"
)

# 停止并删除容器
Write-Host "🛑 停止并删除容器..." -ForegroundColor Cyan
foreach ($Container in $Containers) {
    $ContainerExists = docker ps -a --format "{{.Names}}" | Select-String -Pattern "^$Container$"
    
    if ($ContainerExists) {
        Write-Host "   删除容器: $Container" -ForegroundColor Gray
        
        # 停止容器
        $IsRunning = docker ps --format "{{.Names}}" | Select-String -Pattern "^$Container$"
        if ($IsRunning) {
            docker stop $Container 2>$null | Out-Null
        }
        
        # 删除容器
        docker rm $Container 2>$null | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ 已删除: $Container" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  删除失败: $Container" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⏭️  容器不存在，跳过: $Container" -ForegroundColor Gray
    }
}

Write-Host ""

# 删除数据卷
Write-Host "🗑️  删除数据卷..." -ForegroundColor Cyan
foreach ($Volume in $Volumes) {
    $VolumeExists = docker volume ls --format "{{.Name}}" | Select-String -Pattern "^$Volume$"
    
    if ($VolumeExists) {
        Write-Host "   删除数据卷: $Volume" -ForegroundColor Gray
        docker volume rm $Volume 2>$null | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ 已删除: $Volume" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  删除失败: $Volume (可能被其他容器使用)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⏭️  数据卷不存在，跳过: $Volume" -ForegroundColor Gray
    }
}

Write-Host ""

# 创建新数据卷
Write-Host "📁 创建新数据卷..." -ForegroundColor Cyan
foreach ($Volume in $Volumes) {
    Write-Host "   创建数据卷: $Volume" -ForegroundColor Gray
    docker volume create $Volume | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ 已创建: $Volume" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 创建失败: $Volume" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "✅ 清理完成！" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "📦 新数据卷已创建:" -ForegroundColor Cyan

docker volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" | Select-String "tradingagents"

Write-Host ""
Write-Host "💡 下一步:" -ForegroundColor Yellow
Write-Host "   1. 使用 docker-compose 启动服务" -ForegroundColor Gray
Write-Host "   2. 等待服务初始化完成" -ForegroundColor Gray
Write-Host "   3. 访问前端页面测试功能" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 启动命令示例:" -ForegroundColor Cyan
Write-Host "   docker-compose -f docker-compose.hub.yml up -d" -ForegroundColor White
Write-Host ""

