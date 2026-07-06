# Docker镜像发布脚本 - 发布到Docker Hub
# 使用方法: .\scripts\publish-docker-images.ps1 -DockerHubUsername "your-username"

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername,

    [Parameter(Mandatory=$false)]
    [string]$Password,

    [Parameter(Mandatory=$false)]
    [string]$Version = "v1.0.1",

    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,

    [Parameter(Mandatory=$false)]
    [switch]$PushLatest = $true
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker镜像发布到Docker Hub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$BackendImageLocal = "tradingagents-backend:$Version"
$FrontendImageLocal = "tradingagents-frontend:$Version"
$BackendImageRemote = "$DockerHubUsername/tradingagents-backend"
$FrontendImageRemote = "$DockerHubUsername/tradingagents-frontend"

# 步骤1: 登录Docker Hub
Write-Host "步骤1: 登录Docker Hub..." -ForegroundColor Yellow
if ($Password) {
    echo $Password | docker login -u $DockerHubUsername --password-stdin
} else {
    docker login -u $DockerHubUsername
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 登录失败！请检查用户名和密码是否正确。" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 登录成功！" -ForegroundColor Green
Write-Host ""

# 步骤2: 构建镜像（如果需要）
if (-not $SkipBuild) {
    Write-Host "步骤2: 构建Docker镜像..." -ForegroundColor Yellow
    
    Write-Host "  构建后端镜像..." -ForegroundColor Cyan
    docker build -f Dockerfile.backend -t $BackendImageLocal .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 后端镜像构建失败！" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✅ 后端镜像构建成功！" -ForegroundColor Green
    
    Write-Host "  构建前端镜像..." -ForegroundColor Cyan
    docker build -f Dockerfile.frontend -t $FrontendImageLocal .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 前端镜像构建失败！" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✅ 前端镜像构建成功！" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "步骤2: 跳过构建（使用现有镜像）" -ForegroundColor Yellow
    Write-Host ""
}

# 步骤3: 标记镜像
Write-Host "步骤3: 标记镜像..." -ForegroundColor Yellow

Write-Host "  标记后端镜像: $BackendImageRemote`:$Version" -ForegroundColor Cyan
docker tag $BackendImageLocal "$BackendImageRemote`:$Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 后端镜像标记失败！" -ForegroundColor Red
    exit 1
}

if ($PushLatest) {
    Write-Host "  标记后端镜像: $BackendImageRemote`:latest" -ForegroundColor Cyan
    docker tag $BackendImageLocal "$BackendImageRemote`:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 后端镜像标记失败！" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  标记前端镜像: $FrontendImageRemote`:$Version" -ForegroundColor Cyan
docker tag $FrontendImageLocal "$FrontendImageRemote`:$Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 前端镜像标记失败！" -ForegroundColor Red
    exit 1
}

if ($PushLatest) {
    Write-Host "  标记前端镜像: $FrontendImageRemote`:latest" -ForegroundColor Cyan
    docker tag $FrontendImageLocal "$FrontendImageRemote`:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 前端镜像标记失败！" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ 镜像标记成功！" -ForegroundColor Green
Write-Host ""

# 步骤4: 推送镜像
Write-Host "步骤4: 推送镜像到GitHub Container Registry..." -ForegroundColor Yellow

Write-Host "  推送后端镜像: $BackendImageRemote`:$Version" -ForegroundColor Cyan
docker push "$BackendImageRemote`:$Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 后端镜像推送失败！" -ForegroundColor Red
    exit 1
}

if ($PushLatest) {
    Write-Host "  推送后端镜像: $BackendImageRemote`:latest" -ForegroundColor Cyan
    docker push "$BackendImageRemote`:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 后端镜像推送失败！" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  推送前端镜像: $FrontendImageRemote`:$Version" -ForegroundColor Cyan
docker push "$FrontendImageRemote`:$Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 前端镜像推送失败！" -ForegroundColor Red
    exit 1
}

if ($PushLatest) {
    Write-Host "  推送前端镜像: $FrontendImageRemote`:latest" -ForegroundColor Cyan
    docker push "$FrontendImageRemote`:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 前端镜像推送失败！" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ 镜像推送成功！" -ForegroundColor Green
Write-Host ""

# 完成
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 Docker镜像发布完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "已发布的镜像：" -ForegroundColor Yellow
Write-Host "  后端: $BackendImageRemote`:$Version" -ForegroundColor Cyan
if ($PushLatest) {
    Write-Host "  后端: $BackendImageRemote`:latest" -ForegroundColor Cyan
}
Write-Host "  前端: $FrontendImageRemote`:$Version" -ForegroundColor Cyan
if ($PushLatest) {
    Write-Host "  前端: $FrontendImageRemote`:latest" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "用户可以通过以下命令拉取镜像：" -ForegroundColor Yellow
Write-Host "  docker pull $BackendImageRemote`:latest" -ForegroundColor Cyan
Write-Host "  docker pull $FrontendImageRemote`:latest" -ForegroundColor Cyan
Write-Host ""
Write-Host "或使用docker-compose启动：" -ForegroundColor Yellow
Write-Host "  docker-compose -f docker-compose.hub.yml up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 访问 https://hub.docker.com/repositories/$DockerHubUsername" -ForegroundColor White
Write-Host "  2. 查看已发布的镜像" -ForegroundColor White
Write-Host "  3. 更新docker-compose.hub.yml中的镜像地址（替换YOUR_DOCKERHUB_USERNAME）" -ForegroundColor White
Write-Host ""

