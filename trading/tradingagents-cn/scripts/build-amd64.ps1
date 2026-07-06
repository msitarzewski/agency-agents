# TradingAgents-CN AMD64 (x86_64) 架构 Docker 镜像构建脚本 (PowerShell)
# 适用于：Intel/AMD 处理器的 PC、服务器

param(
    [string]$Version = "v1.0.0-preview",
    [string]$Registry = ""  # 留空表示本地构建，设置为 Docker Hub 用户名可推送到远程
)

# 镜像名称
$BackendImage = "tradingagents-backend"
$FrontendImage = "tradingagents-frontend"

# 目标架构
$Platform = "linux/amd64"
$ArchSuffix = "amd64"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "TradingAgents-CN AMD64 镜像构建" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "版本: $Version" -ForegroundColor Green
Write-Host "架构: $Platform" -ForegroundColor Green
Write-Host "适用: Intel/AMD 处理器 (x86_64)" -ForegroundColor Green
if ($Registry) {
    Write-Host "仓库: $Registry" -ForegroundColor Green
} else {
    Write-Host "仓库: 本地构建（不推送）" -ForegroundColor Yellow
}
Write-Host ""

# 检查 Docker 是否安装
try {
    $null = docker --version
    Write-Host "✅ Docker 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未安装" -ForegroundColor Red
    exit 1
}

# 检查 Docker Buildx 是否可用
try {
    $null = docker buildx version
    Write-Host "✅ Docker Buildx 可用" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Buildx 未安装或不可用" -ForegroundColor Red
    Write-Host "请升级到 Docker 19.03+ 或安装 Buildx 插件" -ForegroundColor Yellow
    exit 1
}

# 创建或使用 buildx builder
Write-Host ""
Write-Host "配置 Docker Buildx..." -ForegroundColor Blue
$BuilderName = "tradingagents-builder-amd64"

$builderExists = docker buildx inspect $BuilderName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Builder '$BuilderName' 已存在" -ForegroundColor Green
} else {
    Write-Host "创建新的 Builder '$BuilderName'..." -ForegroundColor Yellow
    docker buildx create --name $BuilderName --use --platform $Platform
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Builder 创建失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Builder 创建成功" -ForegroundColor Green
}

# 使用指定的 builder
docker buildx use $BuilderName

# 启动 builder（如果未运行）
docker buildx inspect --bootstrap

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "开始构建镜像" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# 构建后端镜像
Write-Host ""
Write-Host "📦 构建后端镜像 (AMD64)..." -ForegroundColor Yellow
$BackendTag = "${BackendImage}:${Version}-${ArchSuffix}"
if ($Registry) {
    $BackendTag = "${Registry}/${BackendTag}"
}

$BuildArgs = @(
    "buildx", "build",
    "--platform", $Platform,
    "-f", "Dockerfile.backend",
    "-t", $BackendTag
)

if ($Registry) {
    # 推送到远程仓库
    $BuildArgs += "--push"
    Write-Host "将推送到: $BackendTag" -ForegroundColor Yellow
} else {
    # 本地构建并加载
    $BuildArgs += "--load"
    Write-Host "本地构建: $BackendTag" -ForegroundColor Yellow
}

# 同时打上不带架构后缀的标签（方便本地使用）
$BackendTagSimple = "${BackendImage}:${Version}"
if ($Registry) {
    $BackendTagSimple = "${Registry}/${BackendTagSimple}"
}
$BuildArgs += "-t", $BackendTagSimple

$BuildArgs += "."

Write-Host "构建命令: docker $($BuildArgs -join ' ')" -ForegroundColor Blue
& docker $BuildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 后端镜像构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 后端镜像构建成功" -ForegroundColor Green

# 构建前端镜像
Write-Host ""
Write-Host "📦 构建前端镜像 (AMD64)..." -ForegroundColor Yellow
$FrontendTag = "${FrontendImage}:${Version}-${ArchSuffix}"
if ($Registry) {
    $FrontendTag = "${Registry}/${FrontendTag}"
}

$BuildArgs = @(
    "buildx", "build",
    "--platform", $Platform,
    "-f", "Dockerfile.frontend",
    "-t", $FrontendTag
)

if ($Registry) {
    # 推送到远程仓库
    $BuildArgs += "--push"
    Write-Host "将推送到: $FrontendTag" -ForegroundColor Yellow
} else {
    # 本地构建并加载
    $BuildArgs += "--load"
    Write-Host "本地构建: $FrontendTag" -ForegroundColor Yellow
}

# 同时打上不带架构后缀的标签（方便本地使用）
$FrontendTagSimple = "${FrontendImage}:${Version}"
if ($Registry) {
    $FrontendTagSimple = "${Registry}/${FrontendTagSimple}"
}
$BuildArgs += "-t", $FrontendTagSimple

$BuildArgs += "."

Write-Host "构建命令: docker $($BuildArgs -join ' ')" -ForegroundColor Blue
& docker $BuildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 前端镜像构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 前端镜像构建成功" -ForegroundColor Green

# 构建完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "✅ AMD64 镜像构建完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

if ($Registry) {
    Write-Host "镜像已推送到远程仓库:" -ForegroundColor Green
    Write-Host "  - $BackendTag"
    Write-Host "  - $BackendTagSimple"
    Write-Host "  - $FrontendTag"
    Write-Host "  - $FrontendTagSimple"
    Write-Host ""
    Write-Host "使用方法:" -ForegroundColor Yellow
    Write-Host "  docker pull $BackendTag"
    Write-Host "  docker pull $FrontendTag"
} else {
    Write-Host "镜像已构建到本地:" -ForegroundColor Green
    Write-Host "  - $BackendTag"
    Write-Host "  - $BackendTagSimple"
    Write-Host "  - $FrontendTag"
    Write-Host "  - $FrontendTagSimple"
    Write-Host ""
    Write-Host "使用方法:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.v1.0.0.yml up -d"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "💡 提示" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "1. 推送到 Docker Hub:" -ForegroundColor Yellow
Write-Host "   .\scripts\build-amd64.ps1 -Registry your-dockerhub-username -Version v1.0.0"
Write-Host ""
Write-Host "2. 本地构建:" -ForegroundColor Yellow
Write-Host "   .\scripts\build-amd64.ps1"
Write-Host ""
Write-Host "3. 查看镜像:" -ForegroundColor Yellow
Write-Host "   docker images | Select-String tradingagents"
Write-Host ""
Write-Host "4. 构建其他架构:" -ForegroundColor Yellow
Write-Host "   ARM64: .\scripts\build-arm64.ps1"
Write-Host ""

