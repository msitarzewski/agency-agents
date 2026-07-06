# AKShare 请求频率限制测试脚本
# 自动加载 .env 配置并运行测试

Write-Host "🚀 AKShare 请求频率限制测试" -ForegroundColor Green
Write-Host ""

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "❌ 虚拟环境不存在，请先运行: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# 加载 .env 文件中的代理配置
Write-Host "🔧 加载代理配置..." -ForegroundColor Cyan

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    # 提取 HTTP_PROXY
    if ($envContent -match 'HTTP_PROXY=(.+)') {
        $httpProxy = $matches[1].Trim()
        if ($httpProxy -and $httpProxy -ne '""' -and $httpProxy -ne "''") {
            $env:HTTP_PROXY = $httpProxy
            Write-Host "   HTTP_PROXY: $httpProxy" -ForegroundColor Gray
        }
    }
    
    # 提取 HTTPS_PROXY
    if ($envContent -match 'HTTPS_PROXY=(.+)') {
        $httpsProxy = $matches[1].Trim()
        if ($httpsProxy -and $httpsProxy -ne '""' -and $httpsProxy -ne "''") {
            $env:HTTPS_PROXY = $httpsProxy
            Write-Host "   HTTPS_PROXY: $httpsProxy" -ForegroundColor Gray
        }
    }
    
    # 提取 NO_PROXY
    if ($envContent -match 'NO_PROXY=(.+)') {
        $noProxy = $matches[1].Trim()
        if ($noProxy) {
            $env:NO_PROXY = $noProxy
            Write-Host "   NO_PROXY: $noProxy" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "⚠️  .env 文件不存在，使用系统环境变量" -ForegroundColor Yellow
}

Write-Host ""

# 运行测试
Write-Host "🧪 启动测试程序..." -ForegroundColor Green
Write-Host ""

python scripts\test_akshare_rate_limit.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 测试失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ 测试完成" -ForegroundColor Green

