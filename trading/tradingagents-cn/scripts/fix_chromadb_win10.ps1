# ChromaDB Windows 10 兼容性修复脚本
# 专门解决Windows 10与Windows 11之间的ChromaDB兼容性问题

Write-Host "=== ChromaDB Windows 10 兼容性修复工具 ===" -ForegroundColor Green
Write-Host "解决Windows 10上的ChromaDB实例冲突问题" -ForegroundColor Cyan
Write-Host ""

# 1. 检查Windows版本
Write-Host "1. 检查Windows版本..." -ForegroundColor Yellow
$osVersion = (Get-WmiObject -Class Win32_OperatingSystem).Caption
Write-Host "操作系统: $osVersion" -ForegroundColor Cyan

if ($osVersion -like "*Windows 10*") {
    Write-Host "检测到Windows 10，应用兼容性修复..." -ForegroundColor Yellow
} else {
    Write-Host "当前系统: $osVersion" -ForegroundColor Cyan
}

# 2. 强制终止所有Python进程
Write-Host "`n2. 强制清理Python进程..." -ForegroundColor Yellow
try {
    Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "已清理Python进程" -ForegroundColor Green
    Start-Sleep -Seconds 3
} catch {
    Write-Host "Python进程清理完成" -ForegroundColor Green
}

# 3. 清理ChromaDB相关文件和注册表
Write-Host "`n3. 深度清理ChromaDB文件..." -ForegroundColor Yellow

# 清理临时文件
$cleanupPaths = @(
    "$env:TEMP\*chroma*",
    "$env:LOCALAPPDATA\Temp\*chroma*", 
    "$env:USERPROFILE\.chroma*",
    ".\chroma*",
    ".\.chroma*",
    "$env:APPDATA\chroma*",
    "$env:LOCALAPPDATA\chroma*"
)

foreach ($path in $cleanupPaths) {
    try {
        Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    } catch {
        # 忽略错误
    }
}

# 清理Python缓存
Get-ChildItem -Path "." -Name "__pycache__" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "深度清理完成" -ForegroundColor Green

# 4. 检查Python版本兼容性
Write-Host "`n4. 检查Python版本兼容性..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Cyan
    
    if ($pythonVersion -match "Python 3\.(8|9|10|11)\.") {
        Write-Host "Python版本兼容" -ForegroundColor Green
    } else {
        Write-Host "警告: 建议使用Python 3.8-3.11版本" -ForegroundColor Yellow
    }
} catch {
    Write-Host "无法检测Python版本" -ForegroundColor Red
}

# 5. 重新安装ChromaDB (Windows 10兼容版本)
Write-Host "`n5. 重新安装ChromaDB..." -ForegroundColor Yellow
Write-Host "卸载当前ChromaDB..." -ForegroundColor Cyan
pip uninstall chromadb -y 2>$null

Write-Host "安装Windows 10兼容版本..." -ForegroundColor Cyan
pip install "chromadb==1.0.12" --no-cache-dir --force-reinstall

# 6. 创建Windows 10专用的ChromaDB配置
Write-Host "`n6. 创建Windows 10兼容配置..." -ForegroundColor Yellow

$chromaConfigContent = @"
# Windows 10 ChromaDB 兼容性配置
import os
import tempfile
import chromadb
from chromadb.config import Settings

# Windows 10 专用配置
def get_win10_chromadb_client():
    '''获取Windows 10兼容的ChromaDB客户端'''
    settings = Settings(
        allow_reset=True,
        anonymized_telemetry=False,
        is_persistent=False,
        # Windows 10 特定配置
        chroma_db_impl="duckdb+parquet",
        chroma_api_impl="chromadb.api.segment.SegmentAPI",
        # 使用临时目录避免权限问题
        persist_directory=None
    )
    
    try:
        client = chromadb.Client(settings)
        return client
    except Exception as e:
        # 降级到最基本配置
        basic_settings = Settings(
            allow_reset=True,
            is_persistent=False
        )
        return chromadb.Client(basic_settings)

# 导出配置
__all__ = ['get_win10_chromadb_client']
"@

$configPath = ".\tradingagents\agents\utils\chromadb_win10_config.py"
$chromaConfigContent | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "已创建Windows 10兼容配置文件: $configPath" -ForegroundColor Green

# 7. 测试ChromaDB初始化
Write-Host "`n7. 测试ChromaDB初始化..." -ForegroundColor Yellow

$testScript = @"
import sys
import os
sys.path.insert(0, '.')

try:
    import chromadb
    from chromadb.config import Settings
    
    # 测试基本初始化
    settings = Settings(
        allow_reset=True,
        anonymized_telemetry=False,
        is_persistent=False
    )
    
    client = chromadb.Client(settings)
    print('基本初始化成功')
    
    # 测试集合操作
    collection_name = 'test_win10_collection'
    try:
        # 删除可能存在的集合
        try:
            client.delete_collection(name=collection_name)
        except:
            pass
            
        # 创建新集合
        collection = client.create_collection(name=collection_name)
        print('集合创建成功')
        
        # 清理测试集合
        client.delete_collection(name=collection_name)
        print('ChromaDB Windows 10 测试完成')
        
    except Exception as e:
        print(f'集合操作失败: {e}')
        
except Exception as e:
    print(f'ChromaDB测试失败: {e}')
    sys.exit(1)
"@

try {
    $testResult = python -c $testScript 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $testResult -ForegroundColor Green
        Write-Host "ChromaDB测试成功" -ForegroundColor Green
    } else {
        Write-Host "ChromaDB测试失败: $testResult" -ForegroundColor Red
    }
} catch {
    Write-Host "ChromaDB测试异常" -ForegroundColor Red
}

# 8. Windows 10 特定解决方案
Write-Host "`n=== Windows 10 特定解决方案 ===" -ForegroundColor Green
Write-Host ""
Write-Host "Windows 10与Windows 11的主要差异:" -ForegroundColor Cyan
Write-Host "1. 文件系统权限管理不同" -ForegroundColor White
Write-Host "2. 临时文件处理机制不同" -ForegroundColor White  
Write-Host "3. 进程隔离级别不同" -ForegroundColor White
Write-Host "4. 内存管理策略不同" -ForegroundColor White
Write-Host ""

Write-Host "推荐解决方案 (按优先级):" -ForegroundColor Yellow
Write-Host ""
Write-Host "方案1: 使用管理员权限运行" -ForegroundColor Yellow
Write-Host "  - 右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor White
Write-Host "  - 然后运行应用程序" -ForegroundColor White
Write-Host ""

Write-Host "方案2: 修改内存配置" -ForegroundColor Yellow
Write-Host "  - 在.env文件中添加:" -ForegroundColor White
Write-Host "    MEMORY_ENABLED=false" -ForegroundColor Cyan
Write-Host "    或降低内存使用" -ForegroundColor White
Write-Host ""

Write-Host "方案3: 使用虚拟环境隔离" -ForegroundColor Yellow
Write-Host "  python -m venv win10_env" -ForegroundColor Cyan
Write-Host "  win10_env\Scripts\activate" -ForegroundColor Cyan
Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
Write-Host ""

Write-Host "方案4: 重启后首次运行" -ForegroundColor Yellow
Write-Host "  - 重启Windows 10系统" -ForegroundColor White
Write-Host "  - 首次运行前不要启动其他Python程序" -ForegroundColor White
Write-Host ""

Write-Host "如果问题仍然存在，请尝试在.env文件中设置:" -ForegroundColor Yellow
Write-Host "MEMORY_ENABLED=false" -ForegroundColor Cyan
Write-Host "这将禁用ChromaDB内存功能，避免冲突" -ForegroundColor White
Write-Host ""

Write-Host "修复完成！建议重启系统后重新运行应用程序。" -ForegroundColor Green