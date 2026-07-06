# TradingAgents Docker日志获取工具 (PowerShell版本)

Write-Host "🚀 TradingAgents Docker日志获取工具" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# 查找容器
$ContainerNames = @("tradingagents-data-service", "tradingagents_data-service_1", "data-service", "tradingagents-cn-data-service-1")
$Container = $null

foreach ($name in $ContainerNames) {
    $result = docker ps --filter "name=$name" --format "{{.Names}}" 2>$null
    if ($result -and $result.Trim() -eq $name) {
        $Container = $name
        Write-Host "✅ 找到容器: $Container" -ForegroundColor Green
        break
    }
}

if (-not $Container) {
    Write-Host "❌ 未找到TradingAgents容器" -ForegroundColor Red
    Write-Host "📋 当前运行的容器:" -ForegroundColor Yellow
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    Write-Host ""
    $Container = Read-Host "请输入容器名称"
    if (-not $Container) {
        Write-Host "❌ 未提供容器名称，退出" -ForegroundColor Red
        exit 1
    }
}

# 创建时间戳
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host ""
Write-Host "📋 获取日志信息..." -ForegroundColor Cyan

# 1. 获取Docker标准日志
Write-Host "1️⃣ 获取Docker标准日志..." -ForegroundColor Yellow
$DockerLogFile = "docker_logs_$Timestamp.log"
docker logs $Container > $DockerLogFile 2>&1
Write-Host "✅ Docker日志已保存到: $DockerLogFile" -ForegroundColor Green

# 2. 查找容器内日志文件
Write-Host ""
Write-Host "2️⃣ 查找容器内日志文件..." -ForegroundColor Yellow
$LogFiles = docker exec $Container find /app -name "*.log" -type f 2>$null

if ($LogFiles) {
    Write-Host "📄 找到以下日志文件:" -ForegroundColor Cyan
    $LogFiles | ForEach-Object { Write-Host "   $_" }
    
    # 复制每个日志文件
    Write-Host ""
    Write-Host "3️⃣ 复制日志文件到本地..." -ForegroundColor Yellow
    $LogFiles | ForEach-Object {
        if ($_.Trim()) {
            $LogFile = $_.Trim()
            $FileName = Split-Path $LogFile -Leaf
            $LocalFile = "${FileName}_$Timestamp"
            
            Write-Host "📤 复制: $LogFile -> $LocalFile" -ForegroundColor Cyan
            $result = docker cp "${Container}:$LogFile" $LocalFile 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 成功复制: $LocalFile" -ForegroundColor Green
                
                # 显示文件信息
                if (Test-Path $LocalFile) {
                    $FileInfo = Get-Item $LocalFile
                    $Lines = (Get-Content $LocalFile | Measure-Object -Line).Lines
                    Write-Host "   📊 文件大小: $($FileInfo.Length) 字节, $Lines 行" -ForegroundColor Gray
                }
            } else {
                Write-Host "❌ 复制失败: $LogFile" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "⚠️ 未在容器中找到.log文件" -ForegroundColor Yellow
}

# 3. 获取容器内应用目录信息
Write-Host ""
Write-Host "4️⃣ 检查应用目录结构..." -ForegroundColor Yellow
Write-Host "📂 /app 目录内容:" -ForegroundColor Cyan
$AppDir = docker exec $Container ls -la /app/ 2>$null
if ($AppDir) {
    $AppDir | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "❌ 无法访问/app目录" -ForegroundColor Red
}

Write-Host ""
Write-Host "📂 查找所有可能的日志文件:" -ForegroundColor Cyan
$AllLogFiles = docker exec $Container find /app -name "*log*" -type f 2>$null
if ($AllLogFiles) {
    $AllLogFiles | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "❌ 未找到包含'log'的文件" -ForegroundColor Red
}

# 4. 检查环境变量和配置
Write-Host ""
Write-Host "5️⃣ 检查日志配置..." -ForegroundColor Yellow
Write-Host "🔧 环境变量:" -ForegroundColor Cyan
$EnvVars = docker exec $Container env 2>$null | Select-String -Pattern "log" -CaseSensitive:$false
if ($EnvVars) {
    $EnvVars | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "❌ 未找到日志相关环境变量" -ForegroundColor Red
}

# 5. 获取最近的应用输出
Write-Host ""
Write-Host "6️⃣ 获取最近的应用输出 (最后50行):" -ForegroundColor Yellow
Write-Host "==================================" -ForegroundColor Gray
docker logs --tail 50 $Container 2>&1 | ForEach-Object { Write-Host $_ -ForegroundColor White }
Write-Host "==================================" -ForegroundColor Gray

Write-Host ""
Write-Host "🎉 日志获取完成!" -ForegroundColor Green
Write-Host "📁 生成的文件:" -ForegroundColor Cyan
Get-ChildItem "*_$Timestamp*" 2>$null | ForEach-Object { 
    Write-Host "   📄 $($_.Name) ($($_.Length) 字节)" -ForegroundColor Gray 
}

Write-Host ""
Write-Host "💡 使用建议:" -ForegroundColor Yellow
Write-Host "   - 如果源码目录的tradingagents.log为空，说明日志可能输出到stdout" -ForegroundColor Gray
Write-Host "   - Docker标准日志包含了应用的所有输出" -ForegroundColor Gray
Write-Host "   - 检查应用的日志配置，确保日志写入到文件" -ForegroundColor Gray
Write-Host ""
Write-Host "📧 发送日志文件:" -ForegroundColor Cyan
Write-Host "   请将 $DockerLogFile 文件发送给开发者" -ForegroundColor Gray
if (Test-Path "tradingagents.log_$Timestamp") {
    Write-Host "   以及 tradingagents.log_$Timestamp 文件" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🔧 如果需要实时监控日志，请运行:" -ForegroundColor Yellow
Write-Host "   docker logs -f $Container" -ForegroundColor Gray
