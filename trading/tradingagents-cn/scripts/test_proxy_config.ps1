# 测试代理配置脚本
# 验证 NO_PROXY 配置是否正确加载

Write-Host "🧪 测试代理配置..." -ForegroundColor Green
Write-Host ""

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "❌ 虚拟环境不存在，请先运行: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# 测试 1：检查 .env 文件中的配置
Write-Host "📋 测试 1: 检查 .env 文件中的配置" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    if ($envContent -match 'NO_PROXY=(.+)') {
        $noProxy = $matches[1].Trim()
        Write-Host "✅ .env 文件中找到 NO_PROXY 配置:" -ForegroundColor Green
        Write-Host "   $noProxy" -ForegroundColor Gray
    } else {
        Write-Host "❌ .env 文件中未找到 NO_PROXY 配置" -ForegroundColor Red
        exit 1
    }
    
    if ($envContent -match 'HTTP_PROXY=(.+)') {
        $httpProxy = $matches[1].Trim()
        Write-Host "✅ .env 文件中找到 HTTP_PROXY 配置:" -ForegroundColor Green
        Write-Host "   $httpProxy" -ForegroundColor Gray
    }
    
    if ($envContent -match 'HTTPS_PROXY=(.+)') {
        $httpsProxy = $matches[1].Trim()
        Write-Host "✅ .env 文件中找到 HTTPS_PROXY 配置:" -ForegroundColor Green
        Write-Host "   $httpsProxy" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ .env 文件不存在" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 测试 2：检查 Settings 是否正确加载配置
Write-Host "📋 测试 2: 检查 Settings 是否正确加载配置" -ForegroundColor Cyan
Write-Host ""

$testScript = @"
from app.core.config import settings
import os

print('Settings 配置:')
print(f'  HTTP_PROXY: {settings.HTTP_PROXY}')
print(f'  HTTPS_PROXY: {settings.HTTPS_PROXY}')
print(f'  NO_PROXY: {settings.NO_PROXY}')
print()
print('环境变量:')
print(f'  HTTP_PROXY: {os.environ.get("HTTP_PROXY", "(未设置)")}')
print(f'  HTTPS_PROXY: {os.environ.get("HTTPS_PROXY", "(未设置)")}')
print(f'  NO_PROXY: {os.environ.get("NO_PROXY", "(未设置)")}')
"@

python -c $testScript

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Settings 加载失败" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 测试 3：测试 AKShare 连接
Write-Host "📋 测试 3: 测试 AKShare 连接" -ForegroundColor Cyan
Write-Host ""

$akshareTest = @"
import akshare as ak
try:
    df = ak.stock_zh_a_spot_em()
    print(f'✅ AKShare 连接成功，获取到 {len(df)} 条股票数据')
    print()
    print('前 5 条数据:')
    print(df.head())
except Exception as e:
    print(f'❌ AKShare 连接失败: {e}')
    exit(1)
"@

python -c $akshareTest

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ AKShare 连接失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 可能的原因:" -ForegroundColor Yellow
    Write-Host "   1. NO_PROXY 配置未生效（Windows 可能不支持通配符）" -ForegroundColor Yellow
    Write-Host "   2. 代理服务器配置错误" -ForegroundColor Yellow
    Write-Host "   3. 网络连接问题" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔧 解决方案:" -ForegroundColor Yellow
    Write-Host "   1. 尝试使用完整域名（不使用通配符）:" -ForegroundColor Yellow
    Write-Host "      NO_PROXY=localhost,127.0.0.1,82.push2.eastmoney.com,push2.eastmoney.com" -ForegroundColor Gray
    Write-Host "   2. 在代理软件中配置规则（Clash/V2Ray）" -ForegroundColor Yellow
    Write-Host "   3. 临时禁用代理测试:" -ForegroundColor Yellow
    Write-Host "      `$env:HTTP_PROXY=`"`"; `$env:HTTPS_PROXY=`"`"" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "🎉 所有测试通过！代理配置正确。" -ForegroundColor Green
Write-Host ""
Write-Host "现在可以启动后端了:" -ForegroundColor Cyan
Write-Host "  python -m app" -ForegroundColor Gray
Write-Host "或使用启动脚本:" -ForegroundColor Cyan
Write-Host "  .\scripts\start_backend_with_proxy.ps1" -ForegroundColor Gray

