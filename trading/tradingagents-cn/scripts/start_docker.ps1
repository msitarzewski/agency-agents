# TradingAgents Docker 启动脚本 (PowerShell版本)
# 自动创建必要目录并启动Docker容器

Write-Host "🚀 TradingAgents Docker 启动" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

# 检查Docker是否运行
try {
    docker info | Out-Null
    Write-Host "✅ Docker运行正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker未运行，请先启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 检查docker-compose是否可用
try {
    docker-compose --version | Out-Null
    Write-Host "✅ docker-compose可用" -ForegroundColor Green
} catch {
    Write-Host "❌ docker-compose未安装或不可用" -ForegroundColor Red
    exit 1
}

# 创建logs目录
Write-Host ""
Write-Host "📁 创建logs目录..." -ForegroundColor Yellow
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "✅ logs目录已创建" -ForegroundColor Green
} else {
    Write-Host "📁 logs目录已存在" -ForegroundColor Gray
}

# 创建.gitkeep文件
$gitkeepFile = "logs\.gitkeep"
if (-not (Test-Path $gitkeepFile)) {
    New-Item -ItemType File -Path $gitkeepFile -Force | Out-Null
    Write-Host "✅ 创建.gitkeep文件" -ForegroundColor Green
}

# 检查.env文件
Write-Host ""
Write-Host "🔧 检查配置文件..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️ .env文件不存在" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "📋 已复制.env.example到.env" -ForegroundColor Green
        Write-Host "✅ 请编辑.env文件配置API密钥" -ForegroundColor Cyan
    } else {
        Write-Host "❌ .env.example文件也不存在" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ .env文件存在" -ForegroundColor Green
}

# 显示当前配置
Write-Host ""
Write-Host "📋 当前配置:" -ForegroundColor Cyan
Write-Host "   项目目录: $(Get-Location)" -ForegroundColor Gray
Write-Host "   日志目录: $(Join-Path (Get-Location) 'logs')" -ForegroundColor Gray
Write-Host "   配置文件: .env" -ForegroundColor Gray

# 启动Docker容器
Write-Host ""
Write-Host "🐳 启动Docker容器..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker容器启动成功" -ForegroundColor Green
} else {
    Write-Host "❌ Docker容器启动失败" -ForegroundColor Red
    exit 1
}

# 检查启动状态
Write-Host ""
Write-Host "📊 检查容器状态..." -ForegroundColor Yellow
docker-compose ps

# 等待服务启动
Write-Host ""
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查Web服务
Write-Host ""
Write-Host "🌐 检查Web服务..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Web服务正常运行" -ForegroundColor Green
        Write-Host "🌐 访问地址: http://localhost:8501" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️ Web服务可能还在启动中..." -ForegroundColor Yellow
    Write-Host "💡 请稍等片刻后访问: http://localhost:8501" -ForegroundColor Cyan
}

# 显示日志信息
Write-Host ""
Write-Host "📋 日志信息:" -ForegroundColor Cyan
Write-Host "   日志目录: .\logs\" -ForegroundColor Gray
Write-Host "   实时查看: Get-Content logs\tradingagents.log -Wait" -ForegroundColor Gray
Write-Host "   Docker日志: docker-compose logs -f web" -ForegroundColor Gray

# 检查是否有日志文件生成
Write-Host ""
Write-Host "📄 检查日志文件..." -ForegroundColor Yellow
$logFiles = Get-ChildItem "logs\*.log" -ErrorAction SilentlyContinue
if ($logFiles) {
    Write-Host "✅ 找到日志文件:" -ForegroundColor Green
    foreach ($file in $logFiles) {
        $size = [math]::Round($file.Length / 1KB, 2)
        Write-Host "   📄 $($file.Name) ($size KB)" -ForegroundColor Gray
    }
} else {
    Write-Host "⏳ 日志文件还未生成，请稍等..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "💡 常用命令:" -ForegroundColor Yellow
Write-Host "   查看状态: docker-compose ps" -ForegroundColor Gray
Write-Host "   查看日志: docker-compose logs -f web" -ForegroundColor Gray
Write-Host "   查看应用日志: Get-Content logs\tradingagents.log -Wait" -ForegroundColor Gray
Write-Host "   停止服务: docker-compose down" -ForegroundColor Gray
Write-Host "   重启服务: docker-compose restart web" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 Web界面: http://localhost:8501" -ForegroundColor Cyan
Write-Host "🗄️ MongoDB管理: http://localhost:8082 (可选)" -ForegroundColor Cyan
Write-Host "🔧 Redis管理: http://localhost:8081" -ForegroundColor Cyan
