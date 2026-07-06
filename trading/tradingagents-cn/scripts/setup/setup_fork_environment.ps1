# PowerShell脚本：配置TradingAgents Fork环境
# 用法：在C:\code目录下运行此脚本

Write-Host "🚀 配置TradingAgents Fork环境" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

# 检查目录结构
if (-not (Test-Path "TradingAgents")) {
    Write-Host "❌ 错误：未找到TradingAgents目录" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "TradingAgentsCN")) {
    Write-Host "❌ 错误：未找到TradingAgentsCN目录" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 目录结构检查通过" -ForegroundColor Green

# 进入TradingAgents目录
Set-Location TradingAgents

Write-Host "📍 当前目录：$(Get-Location)" -ForegroundColor Yellow

try {
    # 1. 检查当前远程仓库配置
    Write-Host "🔍 检查当前远程仓库配置..." -ForegroundColor Yellow
    git remote -v

    # 2. 添加上游仓库（如果还没有添加）
    Write-Host "🔗 添加上游仓库..." -ForegroundColor Yellow
    $remotes = git remote
    if ($remotes -notcontains "upstream") {
        git remote add upstream https://github.com/TauricResearch/TradingAgents.git
        Write-Host "✅ 已添加上游仓库" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ 上游仓库已存在" -ForegroundColor Cyan
    }

    # 3. 获取最新代码
    Write-Host "📡 获取最新代码..." -ForegroundColor Yellow
    git fetch upstream
    git fetch origin

    # 4. 检查当前分支
    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "📋 当前分支：$currentBranch" -ForegroundColor Cyan

    # 5. 确保main分支是最新的
    Write-Host "🔄 同步main分支..." -ForegroundColor Yellow
    git checkout main
    git merge upstream/main
    git push origin main

    # 6. 创建功能分支
    Write-Host "🌿 创建功能分支..." -ForegroundColor Yellow
    $branchName = "feature/intelligent-caching"
    $branches = git branch
    if ($branches -notmatch $branchName) {
        git checkout -b $branchName
        git push -u origin $branchName
        Write-Host "✅ 已创建并推送分支：$branchName" -ForegroundColor Green
    } else {
        git checkout $branchName
        Write-Host "ℹ️ 分支已存在，已切换到：$branchName" -ForegroundColor Cyan
    }

    # 7. 显示最终状态
    Write-Host "📊 最终配置状态：" -ForegroundColor Blue
    Write-Host "远程仓库：" -ForegroundColor Yellow
    git remote -v
    Write-Host "当前分支：" -ForegroundColor Yellow
    git rev-parse --abbrev-ref HEAD
    Write-Host "分支列表：" -ForegroundColor Yellow
    git branch -a

    Write-Host "🎉 Fork环境配置完成！" -ForegroundColor Green
}
catch {
    Write-Host "❌ 配置过程中出现错误：$($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Blue
Write-Host "1. 从TradingAgentsCN复制改进代码" -ForegroundColor White
Write-Host "2. 清理中文内容" -ForegroundColor White
Write-Host "3. 编写测试和文档" -ForegroundColor White
Write-Host "4. 提交Pull Request" -ForegroundColor White
