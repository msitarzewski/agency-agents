# Docker环境初始化脚本 - TradingAgents-CN v1.0.0-preview (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TradingAgents-CN Docker 初始化" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查.env文件
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  未找到.env文件，从.env.example复制..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env文件创建成功" -ForegroundColor Green
    Write-Host "⚠️  请编辑.env文件，配置你的API密钥" -ForegroundColor Yellow
    exit 1
}

# 检查必需的环境变量
Write-Host ""
Write-Host "检查环境变量..."

$envContent = Get-Content ".env" -Raw
$requiredVars = @("DEEPSEEK_API_KEY", "JWT_SECRET")
$missingVars = @()

foreach ($var in $requiredVars) {
    if ($envContent -match "$var=(.+)") {
        $value = $matches[1].Trim()
        if ([string]::IsNullOrEmpty($value) -or $value -like "*your_*_here*") {
            $missingVars += $var
        }
    } else {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ 缺少必需的环境变量:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host "请编辑.env文件，配置这些变量" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ 环境变量检查通过" -ForegroundColor Green

# 创建必需的目录
Write-Host ""
Write-Host "创建必需的目录..."

$directories = @(
    "logs",
    "data\cache",
    "data\exports",
    "data\reports",
    "data\progress",
    "config"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ 创建目录: $dir" -ForegroundColor Green
    }
}

# 停止现有容器
Write-Host ""
Write-Host "停止现有容器..."
docker-compose down 2>$null

# 拉取最新镜像
Write-Host ""
Write-Host "拉取Docker镜像..."
docker-compose pull

# 构建自定义镜像
Write-Host ""
Write-Host "构建应用镜像..."
docker-compose build

# 启动数据库服务
Write-Host ""
Write-Host "启动数据库服务..."
docker-compose up -d mongodb redis

# 等待数据库就绪
Write-Host ""
Write-Host "等待数据库就绪..."
Start-Sleep -Seconds 10

# 检查MongoDB
Write-Host "检查MongoDB..."
$maxAttempts = 30
$attempt = 0
$mongoReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $result = docker-compose exec -T mongodb mongo --eval "db.adminCommand('ping')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ MongoDB就绪" -ForegroundColor Green
            $mongoReady = $true
            break
        }
    } catch {}
    
    $attempt++
    Write-Host "等待MongoDB启动... ($attempt/$maxAttempts)"
    Start-Sleep -Seconds 2
}

if (-not $mongoReady) {
    Write-Host "❌ MongoDB启动超时" -ForegroundColor Red
    exit 1
}

# 检查Redis
Write-Host "检查Redis..."
$attempt = 0
$redisReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $result = docker-compose exec -T redis redis-cli ping 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Redis就绪" -ForegroundColor Green
            $redisReady = $true
            break
        }
    } catch {}
    
    $attempt++
    Write-Host "等待Redis启动... ($attempt/$maxAttempts)"
    Start-Sleep -Seconds 2
}

if (-not $redisReady) {
    Write-Host "❌ Redis启动超时" -ForegroundColor Red
    exit 1
}

# 初始化数据库
Write-Host ""
Write-Host "初始化数据库..."
docker-compose exec -T mongodb mongo tradingagents /docker-entrypoint-initdb.d/mongo-init.js

# 启动应用服务
Write-Host ""
Write-Host "启动应用服务..."
docker-compose up -d

# 等待应用就绪
Write-Host ""
Write-Host "等待应用就绪..."
Start-Sleep -Seconds 15

# 检查后端服务
Write-Host "检查后端服务..."
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ 后端服务就绪" -ForegroundColor Green
            $backendReady = $true
            break
        }
    } catch {}
    
    $attempt++
    Write-Host "等待后端服务启动... ($attempt/$maxAttempts)"
    Start-Sleep -Seconds 2
}

if (-not $backendReady) {
    Write-Host "⚠️  后端服务启动超时，请检查日志" -ForegroundColor Yellow
}

# 检查前端服务
Write-Host "检查前端服务..."
$attempt = 0
$frontendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ 前端服务就绪" -ForegroundColor Green
            $frontendReady = $true
            break
        }
    } catch {}
    
    $attempt++
    Write-Host "等待前端服务启动... ($attempt/$maxAttempts)"
    Start-Sleep -Seconds 2
}

if (-not $frontendReady) {
    Write-Host "⚠️  前端服务启动超时，请检查日志" -ForegroundColor Yellow
}

# 显示服务状态
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
docker-compose ps

# 显示访问信息
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ 初始化完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:"
Write-Host "  前端界面: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  后端API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API文档:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "默认账号:"
Write-Host "  用户名: admin"
Write-Host "  密码: admin123"
Write-Host ""
Write-Host "⚠️  重要: 请在首次登录后立即修改密码！" -ForegroundColor Yellow
Write-Host ""
Write-Host "常用命令:"
Write-Host "  查看日志: docker-compose logs -f"
Write-Host "  停止服务: docker-compose down"
Write-Host "  重启服务: docker-compose restart"
Write-Host "  查看状态: docker-compose ps"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan

