# 导出 MongoDB 配置数据（简化版）

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "导出 MongoDB 配置数据" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 配置
$containerName = "tradingagents-mongodb"
$dbName = "tradingagents"
$username = "admin"
$password = "tradingagents123"
$authDb = "admin"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$exportDir = "mongodb_config_export_$timestamp"

# 需要导出的集合
$collections = @(
    "system_configs",
    "users",
    "llm_providers",
    "market_categories",
    "user_tags",
    "datasource_groupings",
    "platform_configs",
    "user_configs",
    "model_catalog",
    "market_quotes",        # 实时行情数据
    "stock_basic_info"      # 股票基础信息
)

Write-Host "`n[1] 检查 MongoDB 容器..." -ForegroundColor Yellow
$container = docker ps --filter "name=$containerName" --format "{{.Names}}"
if (-not $container) {
    Write-Host "错误: MongoDB 容器未运行" -ForegroundColor Red
    exit 1
}
Write-Host "  容器正在运行: $container" -ForegroundColor Green

Write-Host "`n[2] 创建导出目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $exportDir -Force | Out-Null
Write-Host "  导出目录: $exportDir" -ForegroundColor Green

Write-Host "`n[3] 导出配置集合..." -ForegroundColor Yellow

$successCount = 0

foreach ($collection in $collections) {
    Write-Host "  导出: $collection" -ForegroundColor Cyan
    
    # 导出集合
    docker exec $containerName mongodump `
        -u $username -p $password --authenticationDatabase $authDb `
        -d $dbName -c $collection `
        -o /tmp/export 2>$null | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        # 从容器复制到本地
        docker cp "${containerName}:/tmp/export/$dbName/$collection.bson" "$exportDir/" 2>$null | Out-Null
        docker cp "${containerName}:/tmp/export/$dbName/$collection.metadata.json" "$exportDir/" 2>$null | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    成功" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "    复制失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "    导出失败或集合不存在" -ForegroundColor Yellow
    }
}

# 清理容器中的临时文件
docker exec $containerName rm -rf /tmp/export 2>$null | Out-Null

Write-Host "`n[4] 导出统计..." -ForegroundColor Yellow
Write-Host "  成功导出: $successCount 个集合" -ForegroundColor Green

Write-Host "`n[5] 创建导入脚本..." -ForegroundColor Yellow

# 创建导入脚本
$importScript = @'
# 导入 MongoDB 配置数据

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "导入 MongoDB 配置数据" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 配置（根据新服务器环境修改）
$containerName = "tradingagents-mongodb"
$dbName = "tradingagents"
$username = "admin"
$password = "tradingagents123"
$authDb = "admin"

Write-Host "`n[1] 检查 MongoDB 容器..." -ForegroundColor Yellow
$container = docker ps --filter "name=$containerName" --format "{{.Names}}"
if (-not $container) {
    Write-Host "错误: MongoDB 容器未运行" -ForegroundColor Red
    Write-Host "请先启动 MongoDB 容器" -ForegroundColor Yellow
    exit 1
}
Write-Host "  容器正在运行: $container" -ForegroundColor Green

Write-Host "`n[2] 复制文件到容器..." -ForegroundColor Yellow
docker cp . "${containerName}:/tmp/import/"
Write-Host "  文件已复制" -ForegroundColor Green

Write-Host "`n[3] 导入配置集合..." -ForegroundColor Yellow

$bsonFiles = Get-ChildItem -Filter "*.bson"
$successCount = 0

foreach ($file in $bsonFiles) {
    $collection = $file.BaseName
    Write-Host "  导入: $collection" -ForegroundColor Cyan
    
    docker exec $containerName mongorestore `
        -u $username -p $password --authenticationDatabase $authDb `
        -d $dbName -c $collection `
        --drop `
        /tmp/import/$($file.Name) 2>$null | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    成功" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "    失败" -ForegroundColor Red
    }
}

# 清理
docker exec $containerName rm -rf /tmp/import 2>$null | Out-Null

Write-Host "`n[4] 导入统计..." -ForegroundColor Yellow
Write-Host "  成功导入: $successCount 个集合" -ForegroundColor Green

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "导入完成！" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n后续步骤:" -ForegroundColor Yellow
Write-Host "  1. 重启后端服务: docker restart tradingagents-backend" -ForegroundColor Cyan
Write-Host "  2. 检查系统配置" -ForegroundColor Cyan
'@

$importScript | Out-File -FilePath "$exportDir/import_config.ps1" -Encoding UTF8

Write-Host "  导入脚本已创建: import_config.ps1" -ForegroundColor Green

Write-Host "`n[6] 创建 README..." -ForegroundColor Yellow

$readme = @"
# MongoDB 配置数据导出

导出时间: $timestamp

## 导出的集合

- system_configs (系统配置，包括 15 个 LLM 配置)
- users (用户数据)
- llm_providers (LLM 提供商)
- market_categories (市场分类)
- user_tags (用户标签)
- datasource_groupings (数据源分组)
- platform_configs (平台配置)
- user_configs (用户配置)
- model_catalog (模型目录)
- market_quotes (实时行情数据)
- stock_basic_info (股票基础信息)

## 使用方法

### 在新服务器上导入

1. 将整个导出目录复制到新服务器
2. 确保 MongoDB 容器正在运行
3. 在导出目录中运行:
   ``````powershell
   .\import_config.ps1
   ``````

## 注意事项

1. 导入前建议备份现有数据
2. 导入会覆盖同名集合
3. 用户密码保持原样（已加密）
4. API 密钥会一起导入
5. 导入后需要重启后端服务

## 验证导入

``````powershell
# 检查系统配置
docker exec tradingagents-mongodb mongo tradingagents -u admin -p tradingagents123 --authenticationDatabase admin --eval "db.system_configs.countDocuments()"

# 检查用户数量
docker exec tradingagents-mongodb mongo tradingagents -u admin -p tradingagents123 --authenticationDatabase admin --eval "db.users.countDocuments()"
``````
"@

$readme | Out-File -FilePath "$exportDir/README.md" -Encoding UTF8

Write-Host "  README 已创建" -ForegroundColor Green

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "导出完成！" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n导出目录: $exportDir" -ForegroundColor Cyan
Write-Host "`n导出的文件:" -ForegroundColor Yellow
Get-ChildItem $exportDir | ForEach-Object {
    $size = if ($_.Length -gt 1MB) { "{0:N2} MB" -f ($_.Length / 1MB) } else { "{0:N2} KB" -f ($_.Length / 1KB) }
    Write-Host "  - $($_.Name) ($size)" -ForegroundColor Cyan
}

Write-Host "`n后续步骤:" -ForegroundColor Yellow
Write-Host "  1. 将 '$exportDir' 目录复制到新服务器" -ForegroundColor Cyan
Write-Host "  2. 在新服务器上运行: .\import_config.ps1" -ForegroundColor Cyan
Write-Host "  3. 重启后端服务并验证配置" -ForegroundColor Cyan

Write-Host "`n提示:" -ForegroundColor Yellow
Write-Host "  - 导出包含 LLM API 密钥，请妥善保管" -ForegroundColor Yellow
Write-Host "  - 导入会覆盖新服务器上的同名集合" -ForegroundColor Yellow

