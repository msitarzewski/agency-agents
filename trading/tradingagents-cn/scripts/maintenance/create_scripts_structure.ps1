# PowerShell脚本：为TradingAgentsCN创建scripts目录结构

Write-Host "📁 创建TradingAgentsCN项目的scripts目录结构" -ForegroundColor Blue
Write-Host "=============================================" -ForegroundColor Blue

# 设置项目路径
$ProjectPath = "C:\code\TradingAgentsCN"
Set-Location $ProjectPath

Write-Host "📍 当前目录：$(Get-Location)" -ForegroundColor Yellow

# 定义目录结构
$ScriptsStructure = @{
    "scripts" = @{
        "setup" = @(
            "setup_environment.py",
            "install_dependencies.py", 
            "configure_apis.py",
            "setup_database.py"
        ),
        "validation" = @(
            "verify_gitignore.py",
            "check_dependencies.py",
            "validate_config.py",
            "test_api_connections.py"
        ),
        "maintenance" = @(
            "cleanup_cache.py",
            "backup_data.py",
            "update_dependencies.py",
            "sync_upstream.py"
        ),
        "development" = @(
            "code_analysis.py",
            "performance_benchmark.py",
            "generate_docs.py",
            "prepare_contribution.py"
        ),
        "deployment" = @(
            "deploy_web.py",
            "package_release.py",
            "docker_build.py"
        )
    }
}

# 创建目录结构
Write-Host "`n📁 创建目录结构..." -ForegroundColor Yellow

foreach ($mainDir in $ScriptsStructure.Keys) {
    # 创建主目录
    if (-not (Test-Path $mainDir)) {
        New-Item -ItemType Directory -Path $mainDir -Force | Out-Null
        Write-Host "✅ 创建目录: $mainDir" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ 目录已存在: $mainDir" -ForegroundColor Cyan
    }
    
    foreach ($subDir in $ScriptsStructure[$mainDir].Keys) {
        $subDirPath = Join-Path $mainDir $subDir
        
        if (-not (Test-Path $subDirPath)) {
            New-Item -ItemType Directory -Path $subDirPath -Force | Out-Null
            Write-Host "✅ 创建子目录: $subDirPath" -ForegroundColor Green
        } else {
            Write-Host "ℹ️ 子目录已存在: $subDirPath" -ForegroundColor Cyan
        }
        
        # 创建README文件
        $readmePath = Join-Path $subDirPath "README.md"
        if (-not (Test-Path $readmePath)) {
            $readmeContent = @"
# $subDir

## 目录说明

这个目录包含 $subDir 相关的脚本。

## 脚本列表

"@
            foreach ($script in $ScriptsStructure[$mainDir][$subDir]) {
                $readmeContent += "- ``$script`` - 脚本说明`n"
            }
            
            $readmeContent += @"

## 使用方法

```bash
# 进入项目根目录
cd C:\code\TradingAgentsCN

# 运行脚本
python scripts/$subDir/script_name.py
```

## 注意事项

- 确保在项目根目录下运行脚本
- 检查脚本的依赖要求
- 某些脚本可能需要管理员权限
"@
            
            Set-Content -Path $readmePath -Value $readmeContent -Encoding UTF8
            Write-Host "📝 创建README: $readmePath" -ForegroundColor Cyan
        }
    }
}

# 移动现有的验证脚本
Write-Host "`n📦 移动现有脚本..." -ForegroundColor Yellow

$ExistingScripts = @(
    @{ Source = "C:\code\verify_gitignore.py"; Target = "scripts\validation\verify_gitignore.py" },
    @{ Source = "C:\code\check_dependencies.py"; Target = "scripts\validation\check_dependencies.py" },
    @{ Source = "C:\code\smart_config.py"; Target = "scripts\setup\smart_config.py" },
    @{ Source = "C:\code\debug_integration.ps1"; Target = "scripts\development\debug_integration.ps1" },
    @{ Source = "C:\code\remove_contribution_from_git.ps1"; Target = "scripts\maintenance\remove_contribution_from_git.ps1" }
)

foreach ($script in $ExistingScripts) {
    if (Test-Path $script.Source) {
        $targetDir = Split-Path $script.Target -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        
        Copy-Item $script.Source $script.Target -Force
        Write-Host "✅ 移动脚本: $($script.Source) -> $($script.Target)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 脚本不存在: $($script.Source)" -ForegroundColor Yellow
    }
}

# 创建主README
$MainReadmePath = "scripts\README.md"
$MainReadmeContent = @"
# Scripts Directory

这个目录包含TradingAgentsCN项目的各种脚本工具。

## 目录结构

### 📦 setup/ - 安装和配置脚本
- 环境设置
- 依赖安装
- API配置
- 数据库设置

### 🔍 validation/ - 验证脚本
- Git配置验证
- 依赖检查
- 配置验证
- API连接测试

### 🔧 maintenance/ - 维护脚本
- 缓存清理
- 数据备份
- 依赖更新
- 上游同步

### 🛠️ development/ - 开发辅助脚本
- 代码分析
- 性能基准测试
- 文档生成
- 贡献准备

### 🚀 deployment/ - 部署脚本
- Web应用部署
- 发布打包
- Docker构建

## 使用原则

### 脚本分类
- **tests/** - 单元测试和集成测试（pytest运行）
- **scripts/** - 工具脚本和验证脚本（独立运行）
- **tools/** - 复杂的独立工具程序

### 命名规范
- 使用描述性的文件名
- Python脚本使用 `.py` 扩展名
- PowerShell脚本使用 `.ps1` 扩展名
- Bash脚本使用 `.sh` 扩展名

### 运行方式
```bash
# 从项目根目录运行
cd C:\code\TradingAgentsCN

# Python脚本
python scripts/validation/verify_gitignore.py

# PowerShell脚本
powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup.ps1
```

## 开发指南

### 添加新脚本
1. 确定脚本类型和目标目录
2. 创建脚本文件
3. 添加适当的文档注释
4. 更新相应目录的README
5. 测试脚本功能

### 脚本模板
每个脚本应包含：
- 文件头注释说明用途
- 使用方法说明
- 依赖要求
- 错误处理
- 日志输出

## 注意事项

- 所有脚本应该从项目根目录运行
- 检查脚本的依赖要求
- 某些脚本可能需要特殊权限
- 保持脚本的独立性和可重用性
"@

Set-Content -Path $MainReadmePath -Value $MainReadmeContent -Encoding UTF8
Write-Host "📝 创建主README: $MainReadmePath" -ForegroundColor Green

# 更新.gitignore（如果需要）
Write-Host "`n⚙️ 检查.gitignore配置..." -ForegroundColor Yellow

$GitignorePath = ".gitignore"
if (Test-Path $GitignorePath) {
    $gitignoreContent = Get-Content $GitignorePath -Raw
    
    # 检查是否需要添加scripts相关的忽略规则
    $scriptsIgnoreRules = @(
        "# Scripts临时文件",
        "scripts/**/*.log",
        "scripts/**/*.tmp",
        "scripts/**/temp/",
        "scripts/**/__pycache__/"
    )
    
    $needsUpdate = $false
    foreach ($rule in $scriptsIgnoreRules) {
        if ($gitignoreContent -notmatch [regex]::Escape($rule)) {
            $needsUpdate = $true
            break
        }
    }
    
    if ($needsUpdate) {
        Add-Content $GitignorePath "`n# Scripts临时文件和缓存"
        Add-Content $GitignorePath "scripts/**/*.log"
        Add-Content $GitignorePath "scripts/**/*.tmp" 
        Add-Content $GitignorePath "scripts/**/temp/"
        Add-Content $GitignorePath "scripts/**/__pycache__/"
        
        Write-Host "✅ 已更新.gitignore，添加scripts相关规则" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ .gitignore已包含scripts相关规则" -ForegroundColor Cyan
    }
}

# 显示最终结构
Write-Host "`n📊 最终目录结构：" -ForegroundColor Blue

if (Get-Command tree -ErrorAction SilentlyContinue) {
    tree scripts /F
} else {
    Get-ChildItem scripts -Recurse | ForEach-Object {
        $indent = "  " * ($_.FullName.Split('\').Count - (Get-Location).Path.Split('\').Count - 2)
        Write-Host "$indent$($_.Name)" -ForegroundColor Gray
    }
}

Write-Host "`n🎯 使用建议：" -ForegroundColor Blue
Write-Host "1. 验证脚本放在 scripts/validation/" -ForegroundColor White
Write-Host "2. 测试代码放在 tests/" -ForegroundColor White  
Write-Host "3. 工具脚本放在 scripts/对应分类/" -ForegroundColor White
Write-Host "4. 复杂工具可以考虑单独的 tools/ 目录" -ForegroundColor White

Write-Host "`n🎉 Scripts目录结构创建完成！" -ForegroundColor Green
