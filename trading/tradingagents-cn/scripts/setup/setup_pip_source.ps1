# PowerShell脚本：配置pip源为清华大学镜像

Write-Host "🔧 配置pip源为清华大学镜像" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

# 获取用户主目录
$UserHome = $env:USERPROFILE
$PipConfigDir = Join-Path $UserHome "pip"
$PipConfigFile = Join-Path $PipConfigDir "pip.ini"

Write-Host "📁 pip配置目录: $PipConfigDir" -ForegroundColor Yellow
Write-Host "📄 配置文件: $PipConfigFile" -ForegroundColor Yellow

# 创建pip配置目录
if (-not (Test-Path $PipConfigDir)) {
    New-Item -ItemType Directory -Path $PipConfigDir -Force | Out-Null
    Write-Host "✅ 配置目录已创建" -ForegroundColor Green
} else {
    Write-Host "ℹ️ 配置目录已存在" -ForegroundColor Cyan
}

# pip配置内容
$PipConfig = @"
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
"@

# 写入配置文件
try {
    Set-Content -Path $PipConfigFile -Value $PipConfig -Encoding UTF8
    Write-Host "✅ pip配置已保存" -ForegroundColor Green
} catch {
    Write-Host "❌ 配置保存失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 显示配置内容
Write-Host "`n📊 当前pip配置:" -ForegroundColor Yellow
Get-Content $PipConfigFile | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

# 测试pip配置
Write-Host "`n🧪 测试pip配置..." -ForegroundColor Yellow
try {
    $pipConfig = python -m pip config list 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ pip配置测试成功" -ForegroundColor Green
    } else {
        Write-Host "⚠️ pip配置测试失败" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ 无法测试pip配置" -ForegroundColor Yellow
}

# 升级pip
Write-Host "`n📦 升级pip..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ pip升级成功" -ForegroundColor Green
    } else {
        Write-Host "⚠️ pip升级失败" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ pip升级异常" -ForegroundColor Red
}

# 安装数据库包
Write-Host "`n📥 安装数据库相关包..." -ForegroundColor Yellow

$packages = @("pymongo", "redis")

foreach ($package in $packages) {
    Write-Host "📦 安装 $package..." -ForegroundColor Cyan
    try {
        python -m pip install $package
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $package 安装成功" -ForegroundColor Green
        } else {
            Write-Host "❌ $package 安装失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $package 安装异常: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🎉 pip源配置完成!" -ForegroundColor Green
Write-Host "`n💡 使用说明:" -ForegroundColor Blue
Write-Host "1. 配置已永久生效，以后安装包会自动使用清华镜像" -ForegroundColor White
Write-Host "2. 如需临时使用其他源:" -ForegroundColor White
Write-Host "   pip install -i https://pypi.douban.com/simple/ package_name" -ForegroundColor Gray
Write-Host "3. 如需恢复默认源，删除配置文件:" -ForegroundColor White
Write-Host "   del `"$PipConfigFile`"" -ForegroundColor Gray

Write-Host "`n🎯 下一步:" -ForegroundColor Blue
Write-Host "1. 运行系统初始化: python scripts\setup\initialize_system.py" -ForegroundColor White
Write-Host "2. 检查系统状态: python scripts\validation\check_system_status.py" -ForegroundColor White

Write-Host "`nPress any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
