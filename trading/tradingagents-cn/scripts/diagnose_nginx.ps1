# Nginx 启动问题诊断脚本

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Nginx 启动问题诊断" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查端口占用
Write-Host "[1/5] 检查端口 80 占用情况..." -ForegroundColor Yellow
Write-Host ""

$port80 = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
if ($port80) {
    Write-Host "  ❌ 端口 80 已被占用！" -ForegroundColor Red
    Write-Host ""
    foreach ($conn in $port80) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  进程名称: $($process.ProcessName)" -ForegroundColor Yellow
            Write-Host "  进程 ID:  $($process.Id)" -ForegroundColor Yellow
            Write-Host "  进程路径: $($process.Path)" -ForegroundColor Yellow
            Write-Host ""
        }
    }
    Write-Host "  💡 解决方法：" -ForegroundColor Cyan
    Write-Host "     1. 停止占用端口的程序" -ForegroundColor White
    Write-Host "     2. 或者修改 Nginx 配置使用其他端口（如 8080）" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "  ✅ 端口 80 未被占用" -ForegroundColor Green
    Write-Host ""
}

# 2. 检查 Nginx 配置文件
Write-Host "[2/5] 检查 Nginx 配置文件..." -ForegroundColor Yellow
Write-Host ""

$nginxConf = "vendors\nginx\conf\nginx.conf"
if (Test-Path $nginxConf) {
    Write-Host "  ✅ 配置文件存在: $nginxConf" -ForegroundColor Green
    
    # 测试配置文件语法
    $nginxExe = "vendors\nginx\nginx.exe"
    if (Test-Path $nginxExe) {
        Write-Host "  🔍 测试配置文件语法..." -ForegroundColor Cyan
        $testResult = & $nginxExe -t -c "$PWD\$nginxConf" 2>&1
        Write-Host "  $testResult" -ForegroundColor Gray
    }
} else {
    Write-Host "  ❌ 配置文件不存在: $nginxConf" -ForegroundColor Red
}
Write-Host ""

# 3. 检查 Nginx 日志
Write-Host "[3/5] 检查 Nginx 错误日志..." -ForegroundColor Yellow
Write-Host ""

$errorLog = "logs\nginx_error.log"
if (Test-Path $errorLog) {
    Write-Host "  📄 最近的错误日志（最后 20 行）：" -ForegroundColor Cyan
    Write-Host ""
    Get-Content $errorLog -Tail 20 | ForEach-Object {
        if ($_ -match "error|failed|cannot") {
            Write-Host "  $_" -ForegroundColor Red
        } else {
            Write-Host "  $_" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ⚠️ 错误日志文件不存在" -ForegroundColor Yellow
}
Write-Host ""

# 4. 检查 Nginx 进程
Write-Host "[4/5] 检查 Nginx 进程..." -ForegroundColor Yellow
Write-Host ""

$nginxProcesses = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcesses) {
    Write-Host "  ✅ 发现 Nginx 进程：" -ForegroundColor Green
    foreach ($proc in $nginxProcesses) {
        Write-Host "  PID: $($proc.Id), 启动时间: $($proc.StartTime)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️ 没有运行中的 Nginx 进程" -ForegroundColor Yellow
}
Write-Host ""

# 5. 检查临时文件和锁文件
Write-Host "[5/5] 检查临时文件和锁文件..." -ForegroundColor Yellow
Write-Host ""

$tempFiles = @(
    "vendors\nginx\logs\nginx.pid",
    "vendors\nginx\temp\*"
)

$foundTempFiles = $false
foreach ($pattern in $tempFiles) {
    $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    if ($files) {
        $foundTempFiles = $true
        foreach ($file in $files) {
            Write-Host "  发现临时文件: $($file.FullName)" -ForegroundColor Yellow
        }
    }
}

if ($foundTempFiles) {
    Write-Host ""
    Write-Host "  💡 建议：清理这些临时文件可能有助于解决问题" -ForegroundColor Cyan
} else {
    Write-Host "  ✅ 没有发现遗留的临时文件" -ForegroundColor Green
}
Write-Host ""

# 6. 检查 Windows 服务
Write-Host "[6/6] 检查可能冲突的 Windows 服务..." -ForegroundColor Yellow
Write-Host ""

$conflictServices = @(
    "W3SVC",  # IIS
    "WAS"     # Windows Process Activation Service
)

foreach ($serviceName in $conflictServices) {
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq "Running") {
            Write-Host "  ⚠️ $($service.DisplayName) 正在运行" -ForegroundColor Yellow
            Write-Host "     服务名: $serviceName" -ForegroundColor Gray
            Write-Host "     状态: $($service.Status)" -ForegroundColor Gray
            Write-Host "     💡 此服务可能占用 80 端口，建议停止" -ForegroundColor Cyan
            Write-Host ""
        }
    }
}

# 总结
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  诊断完成" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 常见解决方法：" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 如果端口 80 被占用：" -ForegroundColor White
Write-Host "   - 停止占用端口的程序" -ForegroundColor Gray
Write-Host "   - 或修改 Nginx 配置使用其他端口" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 如果配置文件有问题：" -ForegroundColor White
Write-Host "   - 检查路径是否正确（使用绝对路径）" -ForegroundColor Gray
Write-Host "   - 检查语法是否正确" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 如果有临时文件冲突：" -ForegroundColor White
Write-Host "   - 清理 vendors\nginx\logs\nginx.pid" -ForegroundColor Gray
Write-Host "   - 清理 vendors\nginx\temp\ 目录" -ForegroundColor Gray
Write-Host ""
Write-Host "4. 如果需要管理员权限：" -ForegroundColor White
Write-Host "   - 右键点击 start_all.ps1" -ForegroundColor Gray
Write-Host "   - 选择「以管理员身份运行」" -ForegroundColor Gray
Write-Host ""

