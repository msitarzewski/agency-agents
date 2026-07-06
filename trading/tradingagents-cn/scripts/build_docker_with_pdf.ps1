# Docker 镜像构建脚本（包含 PDF 导出支持）- PowerShell 版本
# 用于构建支持 PDF 导出的 TradingAgents-CN Docker 镜像

param(
    [switch]$Build,
    [switch]$Test,
    [switch]$Compose,
    [switch]$NoCache,
    [switch]$Help
)

# 颜色定义
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 检查 Docker 是否安装
function Test-Docker {
    try {
        $null = docker --version
        Write-Success "Docker 已安装"
        return $true
    }
    catch {
        Write-Error "Docker 未安装，请先安装 Docker Desktop"
        return $false
    }
}

# 检查 Docker Compose 是否安装
function Test-DockerCompose {
    try {
        $null = docker-compose --version
        Write-Success "Docker Compose 已安装"
        return $true
    }
    catch {
        try {
            $null = docker compose version
            Write-Success "Docker Compose (V2) 已安装"
            return $true
        }
        catch {
            Write-Warning "Docker Compose 未安装"
            return $false
        }
    }
}

# 构建后端镜像
function Build-Backend {
    Write-Info "开始构建后端镜像（包含 PDF 导出支持）..."
    
    # 获取架构
    $arch = $env:PROCESSOR_ARCHITECTURE
    if ($arch -eq "AMD64") {
        $platform = "linux/amd64"
    }
    elseif ($arch -eq "ARM64") {
        $platform = "linux/arm64"
    }
    else {
        Write-Error "不支持的架构: $arch"
        exit 1
    }
    
    Write-Info "目标平台: $platform"
    
    # 构建参数
    $buildArgs = @(
        "build",
        "--platform", $platform,
        "-f", "Dockerfile.backend",
        "-t", "tradingagents-backend:latest",
        "-t", "tradingagents-backend:pdf-support"
    )
    
    if ($NoCache) {
        $buildArgs += "--no-cache"
    }
    
    $buildArgs += "."
    
    # 构建镜像
    Write-Info "执行构建命令..."
    & docker $buildArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "后端镜像构建成功"
        return $true
    }
    else {
        Write-Error "后端镜像构建失败"
        return $false
    }
}

# 测试 PDF 导出功能
function Test-PdfExport {
    Write-Info "测试 PDF 导出功能..."
    
    # 启动临时容器
    Write-Info "启动测试容器..."
    docker run --rm -d `
        --name tradingagents-pdf-test `
        -p 8000:8000 `
        tradingagents-backend:latest
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "容器启动失败"
        return $false
    }
    
    # 等待容器启动
    Write-Info "等待容器启动..."
    Start-Sleep -Seconds 10
    
    # 检查 PDF 工具是否可用
    Write-Info "检查 PDF 工具..."
    
    # 检查 WeasyPrint
    Write-Info "检查 WeasyPrint..."
    $weasyPrintCheck = @"
import sys
try:
    import weasyprint
    print('✅ WeasyPrint 已安装')
    try:
        weasyprint.HTML(string='<html><body>test</body></html>').write_pdf()
        print('✅ WeasyPrint 可用')
        sys.exit(0)
    except Exception as e:
        print(f'❌ WeasyPrint 不可用: {e}')
        sys.exit(1)
except ImportError:
    print('❌ WeasyPrint 未安装')
    sys.exit(1)
"@
    
    docker exec tradingagents-pdf-test python -c $weasyPrintCheck
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "WeasyPrint 检测失败"
    }
    
    # 检查 pdfkit
    Write-Info "检查 pdfkit..."
    $pdfkitCheck = @"
import sys
try:
    import pdfkit
    print('✅ pdfkit 已安装')
    try:
        pdfkit.configuration()
        print('✅ pdfkit + wkhtmltopdf 可用')
        sys.exit(0)
    except Exception as e:
        print(f'❌ pdfkit 不可用: {e}')
        sys.exit(1)
except ImportError:
    print('❌ pdfkit 未安装')
    sys.exit(1)
"@
    
    docker exec tradingagents-pdf-test python -c $pdfkitCheck
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "pdfkit 检测失败"
    }
    
    # 检查 Pandoc
    Write-Info "检查 Pandoc..."
    docker exec tradingagents-pdf-test pandoc --version
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Pandoc 检测失败"
    }
    
    # 检查 wkhtmltopdf
    Write-Info "检查 wkhtmltopdf..."
    docker exec tradingagents-pdf-test wkhtmltopdf --version
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "wkhtmltopdf 检测失败"
    }
    
    # 停止测试容器
    Write-Info "停止测试容器..."
    docker stop tradingagents-pdf-test
    
    Write-Success "PDF 导出功能测试完成"
    return $true
}

# 使用 docker-compose 启动服务
function Start-WithCompose {
    Write-Info "使用 docker-compose 启动服务..."
    
    if (Test-Path "docker-compose.yml") {
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Success "服务已启动"
            Write-Info "查看日志: docker-compose logs -f backend"
            return $true
        }
        else {
            Write-Error "服务启动失败"
            return $false
        }
    }
    else {
        Write-Error "docker-compose.yml 文件不存在"
        return $false
    }
}

# 显示使用说明
function Show-Usage {
    Write-Host @"

TradingAgents-CN Docker 构建脚本（PDF 导出支持）

用法:
    .\scripts\build_docker_with_pdf.ps1 [选项]

选项:
    -Build          仅构建镜像
    -Test           构建并测试 PDF 导出功能
    -Compose        使用 docker-compose 启动服务
    -NoCache        构建时不使用缓存
    -Help           显示此帮助信息

示例:
    # 构建镜像
    .\scripts\build_docker_with_pdf.ps1 -Build

    # 构建并测试
    .\scripts\build_docker_with_pdf.ps1 -Test

    # 使用 docker-compose 启动
    .\scripts\build_docker_with_pdf.ps1 -Compose

    # 不使用缓存构建
    .\scripts\build_docker_with_pdf.ps1 -Build -NoCache

"@ -ForegroundColor Green
}

# 主函数
function Main {
    # 显示帮助
    if ($Help) {
        Show-Usage
        exit 0
    }
    
    # 检查 Docker
    if (-not (Test-Docker)) {
        exit 1
    }
    
    # 构建镜像
    if ($Build -or $Test -or $Compose) {
        if (-not (Build-Backend)) {
            exit 1
        }
    }
    
    # 测试 PDF 导出
    if ($Test) {
        if (-not (Test-PdfExport)) {
            exit 1
        }
    }
    
    # 使用 docker-compose 启动
    if ($Compose) {
        if (Test-DockerCompose) {
            if (-not (Start-WithCompose)) {
                exit 1
            }
        }
        else {
            Write-Error "Docker Compose 不可用"
            exit 1
        }
    }
    
    # 如果没有指定任何选项，显示帮助
    if (-not ($Build -or $Test -or $Compose)) {
        Show-Usage
        exit 0
    }
    
    Write-Success "所有操作完成！"
    
    # 显示下一步提示
    Write-Host @"

下一步:
1. 测试 PDF 导出功能:
   docker run --rm -p 8000:8000 tradingagents-backend:latest

2. 查看容器日志:
   docker logs -f <container_id>

3. 进入容器调试:
   docker exec -it <container_id> bash

4. 使用 docker-compose 启动完整服务:
   docker-compose up -d

"@ -ForegroundColor Green
}

# 运行主函数
Main

