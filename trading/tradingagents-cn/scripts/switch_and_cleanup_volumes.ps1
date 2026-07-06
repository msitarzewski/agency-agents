# 切换到统一数据卷并清理旧数据卷
#
# 这个脚本会：
# 1. 停止当前容器
# 2. 切换到统一的数据卷（tradingagents_mongodb_data 和 tradingagents_redis_data）
# 3. 重新启动容器
# 4. 清理未使用的旧数据卷

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🔄 切换到统一数据卷并清理旧数据卷" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

# 1. 检查当前容器状态
Write-Host "`n1️⃣ 检查当前容器状态..." -ForegroundColor Yellow

$mongoContainer = docker ps -a --filter "name=tradingagents-mongodb" --format "{{.Names}}"
$redisContainer = docker ps -a --filter "name=tradingagents-redis" --format "{{.Names}}"

if ($mongoContainer) {
    Write-Host "  ✅ MongoDB 容器: $mongoContainer" -ForegroundColor Green
    $mongoVolume = docker inspect $mongoContainer -f '{{range .Mounts}}{{if eq .Destination "/data/db"}}{{.Name}}{{end}}{{end}}'
    Write-Host "    当前数据卷: $mongoVolume" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠️  MongoDB 容器不存在" -ForegroundColor Yellow
}

if ($redisContainer) {
    Write-Host "  ✅ Redis 容器: $redisContainer" -ForegroundColor Green
    $redisVolume = docker inspect $redisContainer -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}'
    Write-Host "    当前数据卷: $redisVolume" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠️  Redis 容器不存在" -ForegroundColor Yellow
}

# 2. 询问是否继续
Write-Host "`n2️⃣ 准备切换到统一数据卷..." -ForegroundColor Yellow
Write-Host "  目标 MongoDB 数据卷: tradingagents_mongodb_data" -ForegroundColor Cyan
Write-Host "  目标 Redis 数据卷: tradingagents_redis_data" -ForegroundColor Cyan

$confirm = Read-Host "`n是否继续？(yes/no)"

if ($confirm -ne "yes") {
    Write-Host "`n❌ 已取消操作" -ForegroundColor Red
    exit 0
}

# 3. 停止并删除容器
Write-Host "`n3️⃣ 停止并删除容器..." -ForegroundColor Yellow

if ($mongoContainer) {
    Write-Host "  停止 MongoDB 容器..." -ForegroundColor Yellow
    docker stop $mongoContainer 2>$null
    docker rm $mongoContainer 2>$null
    Write-Host "  ✅ MongoDB 容器已删除" -ForegroundColor Green
}

if ($redisContainer) {
    Write-Host "  停止 Redis 容器..." -ForegroundColor Yellow
    docker stop $redisContainer 2>$null
    docker rm $redisContainer 2>$null
    Write-Host "  ✅ Redis 容器已删除" -ForegroundColor Green
}

# 4. 检查网络
Write-Host "`n4️⃣ 检查 Docker 网络..." -ForegroundColor Yellow

$network = docker network ls --filter name=tradingagents-network --format "{{.Name}}"
if (-not $network) {
    Write-Host "  创建网络..." -ForegroundColor Yellow
    docker network create tradingagents-network
    Write-Host "  ✅ 网络已创建" -ForegroundColor Green
} else {
    Write-Host "  ✅ 网络已存在: $network" -ForegroundColor Green
}

# 5. 启动 MongoDB 容器（使用统一数据卷）
Write-Host "`n5️⃣ 启动 MongoDB 容器..." -ForegroundColor Yellow

docker run -d `
  --name tradingagents-mongodb `
  --network tradingagents-network `
  -p 27017:27017 `
  -v tradingagents_mongodb_data:/data/db `
  -v ${PWD}/scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro `
  -e MONGO_INITDB_ROOT_USERNAME=admin `
  -e MONGO_INITDB_ROOT_PASSWORD=tradingagents123 `
  -e MONGO_INITDB_DATABASE=tradingagents `
  -e TZ="Asia/Shanghai" `
  --restart unless-stopped `
  mongo:4.4

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ MongoDB 容器已启动" -ForegroundColor Green
} else {
    Write-Host "  ❌ MongoDB 容器启动失败" -ForegroundColor Red
    exit 1
}

# 6. 启动 Redis 容器（使用统一数据卷）
Write-Host "`n6️⃣ 启动 Redis 容器..." -ForegroundColor Yellow

docker run -d `
  --name tradingagents-redis `
  --network tradingagents-network `
  -p 6379:6379 `
  -v tradingagents_redis_data:/data `
  -e TZ="Asia/Shanghai" `
  --restart unless-stopped `
  redis:7-alpine redis-server --appendonly yes --requirepass tradingagents123

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Redis 容器已启动" -ForegroundColor Green
} else {
    Write-Host "  ❌ Redis 容器启动失败" -ForegroundColor Red
    exit 1
}

# 7. 等待容器启动
Write-Host "`n7️⃣ 等待容器启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 8. 验证数据卷挂载
Write-Host "`n8️⃣ 验证数据卷挂载..." -ForegroundColor Yellow

$mongoVolume = docker inspect tradingagents-mongodb -f '{{range .Mounts}}{{if eq .Destination "/data/db"}}{{.Name}}{{end}}{{end}}'
$redisVolume = docker inspect tradingagents-redis -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}'

Write-Host "  MongoDB 数据卷: $mongoVolume" -ForegroundColor Cyan
Write-Host "  Redis 数据卷: $redisVolume" -ForegroundColor Cyan

if ($mongoVolume -eq "tradingagents_mongodb_data" -and $redisVolume -eq "tradingagents_redis_data") {
    Write-Host "  ✅ 数据卷挂载正确" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  数据卷挂载可能不正确" -ForegroundColor Yellow
}

# 9. 验证 MongoDB 数据
Write-Host "`n9️⃣ 验证 MongoDB 数据..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

Write-Host "  正在查询数据库..." -ForegroundColor Cyan
$dbCheck = docker exec tradingagents-mongodb mongo tradingagents -u admin -p tradingagents123 --authenticationDatabase admin --quiet --eval "db.system_configs.countDocuments()" 2>$null

if ($dbCheck) {
    Write-Host "  ✅ 数据库连接成功" -ForegroundColor Green
    Write-Host "  system_configs 集合文档数: $dbCheck" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠️  无法连接数据库或验证数据" -ForegroundColor Yellow
}

# 10. 清理旧数据卷
Write-Host "`n🔟 清理旧数据卷..." -ForegroundColor Yellow

$volumesToDelete = @(
    "tradingagents_mongodb_data_v1",
    "tradingagents_redis_data_v1",
    "tradingagents-cn_tradingagents_mongodb_data_v1",
    "tradingagents-cn_tradingagents_redis_data_v1"
)

Write-Host "  准备删除以下数据卷:" -ForegroundColor Yellow
foreach ($vol in $volumesToDelete) {
    Write-Host "    - $vol" -ForegroundColor Yellow
}

$confirmDelete = Read-Host "`n是否删除这些旧数据卷？(yes/no)"

if ($confirmDelete -eq "yes") {
    foreach ($vol in $volumesToDelete) {
        Write-Host "  删除: $vol" -ForegroundColor Yellow
        docker volume rm $vol 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ 已删除" -ForegroundColor Green
        } else {
            Write-Host "    ⚠️  删除失败或不存在" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ❌ 已跳过删除旧数据卷" -ForegroundColor Yellow
}

# 11. 清理匿名数据卷
Write-Host "`n1️⃣1️⃣ 清理匿名数据卷..." -ForegroundColor Yellow

$anonymousVolumes = docker volume ls -qf "dangling=true"

if ($anonymousVolumes) {
    $anonymousCount = ($anonymousVolumes | Measure-Object).Count
    Write-Host "  发现 $anonymousCount 个匿名数据卷" -ForegroundColor Yellow
    
    $confirmAnonymous = Read-Host "是否删除所有匿名数据卷？(yes/no)"
    
    if ($confirmAnonymous -eq "yes") {
        docker volume prune -f
        Write-Host "  ✅ 匿名数据卷已清理" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 已跳过删除匿名数据卷" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✅ 没有匿名数据卷需要清理" -ForegroundColor Green
}

# 12. 显示最终状态
Write-Host "`n1️⃣2️⃣ 最终状态..." -ForegroundColor Yellow

Write-Host "`n  容器状态:" -ForegroundColor Cyan
docker ps --filter "name=tradingagents" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n  数据卷列表:" -ForegroundColor Cyan
docker volume ls --filter "name=tradingagents"

Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "✅ 切换和清理操作完成！" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan

Write-Host "`n📝 后续步骤:" -ForegroundColor Yellow
Write-Host "  1. 检查容器状态: docker ps" -ForegroundColor Cyan
Write-Host "  2. 检查 MongoDB 数据: docker exec tradingagents-mongodb mongo tradingagents -u admin -p tradingagents123 --authenticationDatabase admin" -ForegroundColor Cyan
Write-Host "  3. 重启后端服务（如果需要）: docker restart tradingagents-backend" -ForegroundColor Cyan

