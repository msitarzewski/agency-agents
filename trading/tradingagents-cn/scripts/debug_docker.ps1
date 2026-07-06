# Docker容器排查脚本
# 使用方法: .\scripts\debug_docker.ps1

Write-Host "=== Docker容器排查工具 ===" -ForegroundColor Green

# 1. 检查Docker服务状态
Write-Host "`n1. 检查Docker服务状态:" -ForegroundColor Yellow
try {
    docker version
    Write-Host "✅ Docker服务正常运行" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker服务未运行或有问题" -ForegroundColor Red
    exit 1
}

# 2. 检查容器状态
Write-Host "`n2. 检查容器状态:" -ForegroundColor Yellow
docker-compose ps -a

# 3. 检查网络状态
Write-Host "`n3. 检查Docker网络:" -ForegroundColor Yellow
docker network ls | Select-String "tradingagents"

# 4. 检查数据卷状态
Write-Host "`n4. 检查数据卷:" -ForegroundColor Yellow
docker volume ls | Select-String "tradingagents"

# 5. 检查端口占用
Write-Host "`n5. 检查端口占用:" -ForegroundColor Yellow
$ports = @(8501, 27017, 6379, 8081, 8082)
foreach ($port in $ports) {
    $result = netstat -an | Select-String ":$port "
    if ($result) {
        Write-Host "端口 $port 被占用: $result" -ForegroundColor Yellow
    } else {
        Write-Host "端口 $port 空闲" -ForegroundColor Green
    }
}

# 6. 检查磁盘空间
Write-Host "`n6. 检查磁盘空间:" -ForegroundColor Yellow
docker system df

Write-Host "`n=== 排查完成 ===" -ForegroundColor Green
Write-Host "如需查看详细日志，请运行:" -ForegroundColor Cyan
Write-Host "docker-compose logs [服务名]" -ForegroundColor Cyan
Write-Host "例如: docker-compose logs web" -ForegroundColor Cyan