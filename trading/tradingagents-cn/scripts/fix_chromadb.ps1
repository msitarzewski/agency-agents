# ChromaDB 问题诊断和修复脚本 (Windows PowerShell版本)
# 用于解决 "Configuration error: An instance of Chroma already exists for ephemeral with different settings" 错误

Write-Host "=== ChromaDB 问题诊断和修复工具 ===" -ForegroundColor Green
Write-Host "适用环境: Windows PowerShell" -ForegroundColor Cyan
Write-Host ""

# 1. 检查Python进程中的ChromaDB实例
Write-Host "1. 检查Python进程..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "发现Python进程:" -ForegroundColor Red
    $pythonProcesses | Format-Table -Property Id, ProcessName, StartTime -AutoSize
    
    $choice = Read-Host "是否终止所有Python进程? (y/N)"
    if ($choice -eq "y" -or $choice -eq "Y") {
        $pythonProcesses | Stop-Process -Force
        Write-Host "✅ 已终止所有Python进程" -ForegroundColor Green
        Start-Sleep -Seconds 2
    }
} else {
    Write-Host "✅ 未发现Python进程" -ForegroundColor Green
}

# 2. 清理ChromaDB临时文件和缓存
Write-Host "`n2. 清理ChromaDB临时文件..." -ForegroundColor Yellow

# 清理用户临时目录中的ChromaDB文件
$tempPaths = @(
    "$env:TEMP\chroma*",
    "$env:LOCALAPPDATA\Temp\chroma*",
    "$env:USERPROFILE\.chroma*",
    ".\chroma*",
    ".\.chroma*"
)

$cleanedFiles = 0
foreach ($path in $tempPaths) {
    $items = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
    if ($items) {
        Write-Host "清理: $path" -ForegroundColor Cyan
        try {
            Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
            $cleanedFiles += $items.Count
        } catch {
            Write-Host "⚠️ 无法删除: $path" -ForegroundColor Yellow
        }
    }
}

if ($cleanedFiles -gt 0) {
    Write-Host "✅ 已清理 $cleanedFiles 个ChromaDB临时文件" -ForegroundColor Green
} else {
    Write-Host "✅ 未发现ChromaDB临时文件" -ForegroundColor Green
}

# 3. 清理Python缓存
Write-Host "`n3. 清理Python缓存..." -ForegroundColor Yellow
$pycachePaths = @(
    ".\__pycache__",
    ".\tradingagents\__pycache__",
    ".\tradingagents\agents\__pycache__",
    ".\tradingagents\agents\utils\__pycache__"
)

$cleanedCache = 0
foreach ($path in $pycachePaths) {
    if (Test-Path $path) {
        try {
            Remove-Item -Path $path -Recurse -Force
            $cleanedCache++
            Write-Host "清理: $path" -ForegroundColor Cyan
        } catch {
            Write-Host "⚠️ 无法删除: $path" -ForegroundColor Yellow
        }
    }
}

if ($cleanedCache -gt 0) {
    Write-Host "✅ 已清理 $cleanedCache 个Python缓存目录" -ForegroundColor Green
} else {
    Write-Host "✅ 未发现Python缓存目录" -ForegroundColor Green
}

# 4. 检查ChromaDB版本兼容性
Write-Host "`n4. 检查ChromaDB版本..." -ForegroundColor Yellow
try {
    $chromaVersion = python -c "import chromadb; print(chromadb.__version__)" 2>$null
    if ($chromaVersion) {
        Write-Host "ChromaDB版本: $chromaVersion" -ForegroundColor Cyan
        
        # 检查是否为推荐版本
        if ($chromaVersion -match "^1\.0\.") {
            Write-Host "✅ ChromaDB版本兼容" -ForegroundColor Green
        } else {
            Write-Host "⚠️ 建议使用ChromaDB 1.0.x版本" -ForegroundColor Yellow
            $upgrade = Read-Host "是否升级ChromaDB? (y/N)"
            if ($upgrade -eq "y" -or $upgrade -eq "Y") {
                Write-Host "升级ChromaDB..." -ForegroundColor Cyan
                pip install --upgrade "chromadb>=1.0.12"
            }
        }
    } else {
        Write-Host "❌ 无法检测ChromaDB版本" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ ChromaDB检查失败" -ForegroundColor Red
}

# 5. 检查环境变量冲突
Write-Host "`n5. 检查环境变量..." -ForegroundColor Yellow
$chromaEnvVars = @(
    "CHROMA_HOST",
    "CHROMA_PORT", 
    "CHROMA_DB_IMPL",
    "CHROMA_API_IMPL",
    "CHROMA_TELEMETRY"
)

$foundEnvVars = @()
foreach ($var in $chromaEnvVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ($value) {
        $foundEnvVars += "$var=$value"
    }
}

if ($foundEnvVars.Count -gt 0) {
    Write-Host "发现ChromaDB环境变量:" -ForegroundColor Yellow
    $foundEnvVars | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }
    Write-Host "⚠️ 这些环境变量可能导致配置冲突" -ForegroundColor Yellow
} else {
    Write-Host "✅ 未发现ChromaDB环境变量冲突" -ForegroundColor Green
}

# 6. 测试ChromaDB初始化
Write-Host "`n6. 测试ChromaDB初始化..." -ForegroundColor Yellow
$testScript = @"
import chromadb
from chromadb.config import Settings
import sys

try:
    # 测试基本初始化
    client = chromadb.Client()
    print("✅ 基本初始化成功")
    
    # 测试项目配置
    settings = Settings(
        allow_reset=True,
        anonymized_telemetry=False,
        is_persistent=False
    )
    client2 = chromadb.Client(settings)
    print("✅ 项目配置初始化成功")
    
    # 测试集合创建
    collection = client2.create_collection(name="test_collection")
    print("✅ 集合创建成功")
    
    # 清理测试
    client2.delete_collection(name="test_collection")
    print("✅ ChromaDB测试完成")
    
except Exception as e:
    print(f"❌ ChromaDB测试失败: {e}")
    sys.exit(1)
"@

try {
    $testResult = python -c $testScript 2>&1
    Write-Host $testResult -ForegroundColor Green
} catch {
    Write-Host "❌ ChromaDB测试失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# 7. 提供解决方案建议
Write-Host "`n=== 解决方案建议 ===" -ForegroundColor Green
Write-Host "如果问题仍然存在，请尝试以下方案:" -ForegroundColor Cyan
Write-Host ""
Write-Host "方案1: 重启系统" -ForegroundColor Yellow
Write-Host "  - 完全清理内存中的ChromaDB实例"
Write-Host ""
Write-Host "方案2: 使用虚拟环境" -ForegroundColor Yellow
Write-Host "  python -m venv fresh_env"
Write-Host "  fresh_env\Scripts\activate"
Write-Host "  pip install -r requirements.txt"
Write-Host ""
Write-Host "方案3: 重新安装ChromaDB" -ForegroundColor Yellow
Write-Host "  pip uninstall chromadb -y"
Write-Host "  pip install chromadb==1.0.12"
Write-Host ""
Write-Host "方案4: 检查Python版本兼容性" -ForegroundColor Yellow
Write-Host "  - 确保使用Python 3.8-3.11"
Write-Host "  - 避免使用Python 3.12+"
Write-Host ""

Write-Host "🔧 修复完成！请重新运行应用程序。" -ForegroundColor Green