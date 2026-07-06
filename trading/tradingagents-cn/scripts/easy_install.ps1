# TradingAgents-CN 一键安装脚本 (Windows PowerShell)
# 功能：自动检测环境、安装依赖、配置API密钥、启动应用

param(
    [switch]$Reconfigure,  # 重新配置
    [switch]$SkipInstall,  # 跳过安装，仅配置
    [switch]$Minimal       # 最小化安装（无数据库）
)

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "✅ $Message" "Green" }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ️  $Message" "Cyan" }
function Write-Warning { param([string]$Message) Write-ColorOutput "⚠️  $Message" "Yellow" }
function Write-Error { param([string]$Message) Write-ColorOutput "❌ $Message" "Red" }
function Write-Step { param([string]$Message) Write-ColorOutput "`n🔹 $Message" "Magenta" }

# 显示欢迎信息
function Show-Welcome {
    Clear-Host
    Write-ColorOutput @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚀 TradingAgents-CN 一键安装向导                         ║
║                                                              ║
║     让AI驱动的股票分析触手可及                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ "Cyan"
    Write-Host ""
}

# 检查Python版本
function Test-PythonVersion {
    Write-Step "检查Python环境..."
    
    try {
        $pythonVersion = python --version 2>&1
        Write-Info "发现Python: $pythonVersion"
        
        # 提取版本号
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -ge 3 -and $minor -ge 10) {
                Write-Success "Python版本符合要求 (需要3.10+)"
                return $true
            }
        }
        
        Write-Error "Python版本过低，需要3.10或更高版本"
        Write-Info "请访问 https://www.python.org/downloads/ 下载最新版本"
        return $false
    }
    catch {
        Write-Error "未找到Python，请先安装Python 3.10+"
        Write-Info "下载地址: https://www.python.org/downloads/"
        return $false
    }
}

# 检查网络连接
function Test-NetworkConnection {
    Write-Step "检查网络连接..."
    
    $testUrls = @(
        "https://pypi.org",
        "https://api.deepseek.com",
        "https://dashscope.aliyun.com"
    )
    
    $connected = $false
    foreach ($url in $testUrls) {
        try {
            $response = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                $connected = $true
                break
            }
        }
        catch {
            continue
        }
    }
    
    if ($connected) {
        Write-Success "网络连接正常"
        return $true
    }
    else {
        Write-Warning "网络连接可能存在问题，但将继续安装"
        return $true  # 不阻止安装
    }
}

# 创建虚拟环境
function New-VirtualEnvironment {
    Write-Step "创建Python虚拟环境..."
    
    if (Test-Path ".venv") {
        Write-Info "虚拟环境已存在"
        return $true
    }
    
    try {
        python -m venv .venv
        Write-Success "虚拟环境创建成功"
        return $true
    }
    catch {
        Write-Error "虚拟环境创建失败: $_"
        return $false
    }
}

# 激活虚拟环境
function Enable-VirtualEnvironment {
    Write-Info "激活虚拟环境..."
    
    $activateScript = ".\.venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Success "虚拟环境已激活"
        return $true
    }
    else {
        Write-Error "找不到激活脚本"
        return $false
    }
}

# 升级pip
function Update-Pip {
    Write-Step "升级pip..."
    
    try {
        python -m pip install --upgrade pip --quiet
        Write-Success "pip升级完成"
        return $true
    }
    catch {
        Write-Warning "pip升级失败，但将继续安装"
        return $true
    }
}

# 安装依赖
function Install-Dependencies {
    Write-Step "安装项目依赖..."
    Write-Info "这可能需要几分钟时间，请耐心等待..."
    
    try {
        # 使用国内镜像加速
        $mirrors = @(
            "https://mirrors.aliyun.com/pypi/simple",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://pypi.org/simple"
        )
        
        foreach ($mirror in $mirrors) {
            Write-Info "尝试使用镜像: $mirror"
            try {
                pip install -e . -i $mirror --quiet
                Write-Success "依赖安装成功"
                return $true
            }
            catch {
                Write-Warning "镜像 $mirror 安装失败，尝试下一个..."
                continue
            }
        }
        
        Write-Error "所有镜像都安装失败"
        return $false
    }
    catch {
        Write-Error "依赖安装失败: $_"
        return $false
    }
}

# 选择LLM提供商
function Select-LLMProvider {
    Write-Step "选择大语言模型提供商..."
    Write-Host ""
    Write-Host "请选择您要使用的LLM提供商（至少选择一个）：" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. DeepSeek V3      - 推荐 ⭐ (性价比最高，中文优化)"
    Write-Host "2. 通义千问         - 推荐 ⭐ (国产稳定，响应快)"
    Write-Host "3. Google Gemini    - 推荐 ⭐ (免费额度大，能力强)"
    Write-Host "4. OpenAI GPT       - 可选 (通用能力强，成本较高)"
    Write-Host "5. 跳过配置         - 稍后手动配置"
    Write-Host ""
    
    $choice = Read-Host "请输入选项 (1-5)"
    
    switch ($choice) {
        "1" { return @{Provider="DeepSeek"; Key="DEEPSEEK_API_KEY"; Url="https://platform.deepseek.com/"} }
        "2" { return @{Provider="通义千问"; Key="DASHSCOPE_API_KEY"; Url="https://dashscope.aliyun.com/"} }
        "3" { return @{Provider="Google Gemini"; Key="GOOGLE_API_KEY"; Url="https://aistudio.google.com/"} }
        "4" { return @{Provider="OpenAI"; Key="OPENAI_API_KEY"; Url="https://platform.openai.com/"} }
        "5" { return $null }
        default {
            Write-Warning "无效选项，默认选择DeepSeek"
            return @{Provider="DeepSeek"; Key="DEEPSEEK_API_KEY"; Url="https://platform.deepseek.com/"}
        }
    }
}

# 配置API密钥
function Set-APIKey {
    param($ProviderInfo)
    
    if ($null -eq $ProviderInfo) {
        Write-Info "跳过API密钥配置"
        return $null
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  配置 $($ProviderInfo.Provider) API密钥" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 获取API密钥步骤：" -ForegroundColor Green
    Write-Host "   1. 访问: $($ProviderInfo.Url)"
    Write-Host "   2. 注册/登录账号"
    Write-Host "   3. 创建API密钥"
    Write-Host "   4. 复制密钥并粘贴到下方"
    Write-Host ""
    
    $apiKey = Read-Host "请输入API密钥 (或按Enter跳过)"
    
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Warning "未配置API密钥，稍后可手动配置"
        return $null
    }
    
    return @{Key=$ProviderInfo.Key; Value=$apiKey}
}

# 生成.env文件
function New-EnvFile {
    param($ApiKeyConfig, $MinimalMode)
    
    Write-Step "生成配置文件..."
    
    $envContent = @"
# TradingAgents-CN 配置文件
# 由一键安装脚本自动生成
# 生成时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# ==================== LLM配置 ====================
"@
    
    if ($null -ne $ApiKeyConfig) {
        $envContent += "`n$($ApiKeyConfig.Key)=$($ApiKeyConfig.Value)"
    }
    else {
        $envContent += @"

# 请手动配置至少一个LLM提供商的API密钥：
# DEEPSEEK_API_KEY=sk-your-key-here
# DASHSCOPE_API_KEY=sk-your-key-here
# GOOGLE_API_KEY=AIzaSy-your-key-here
"@
    }
    
    $envContent += @"


# ==================== 数据库配置 ====================
"@
    
    if ($MinimalMode) {
        $envContent += @"

# 极简模式：使用文件存储，无需数据库
MONGODB_ENABLED=false
REDIS_ENABLED=false
"@
    }
    else {
        $envContent += @"

# 标准模式：启用数据库（需要Docker或手动安装）
MONGODB_ENABLED=false
REDIS_ENABLED=false
# 如需启用，请设置为true并确保数据库服务运行
"@
    }
    
    $envContent += @"


# ==================== 可选配置 ====================
# 数据源（可选）
# TUSHARE_TOKEN=your-token-here
# FINNHUB_API_KEY=your-key-here

# 日志级别
TRADINGAGENTS_LOG_LEVEL=INFO

# 应用端口
STREAMLIT_PORT=8501
"@
    
    try {
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "配置文件已生成: .env"
        return $true
    }
    catch {
        Write-Error "配置文件生成失败: $_"
        return $false
    }
}

# 启动应用
function Start-Application {
    Write-Step "启动应用..."
    
    Write-Info "正在启动Web界面..."
    Write-Info "浏览器将自动打开 http://localhost:8501"
    Write-Host ""
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Green"
    Write-ColorOutput "  🎉 安装完成！应用正在启动..." "Green"
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Green"
    Write-Host ""
    Write-Info "按 Ctrl+C 停止应用"
    Write-Host ""
    
    try {
        python start_web.py
    }
    catch {
        Write-Error "应用启动失败: $_"
        Write-Info "请尝试手动启动: python start_web.py"
    }
}

# 主函数
function Main {
    Show-Welcome
    
    # 检查环境
    if (-not (Test-PythonVersion)) { exit 1 }
    Test-NetworkConnection | Out-Null
    
    # 安装依赖
    if (-not $SkipInstall) {
        if (-not (New-VirtualEnvironment)) { exit 1 }
        if (-not (Enable-VirtualEnvironment)) { exit 1 }
        if (-not (Update-Pip)) { exit 1 }
        if (-not (Install-Dependencies)) { exit 1 }
    }
    
    # 配置API密钥
    if ($Reconfigure -or -not (Test-Path ".env")) {
        $providerInfo = Select-LLMProvider
        $apiKeyConfig = Set-APIKey -ProviderInfo $providerInfo
        $minimalMode = $Minimal -or -not (Get-Command docker -ErrorAction SilentlyContinue)
        
        if (-not (New-EnvFile -ApiKeyConfig $apiKeyConfig -MinimalMode $minimalMode)) {
            exit 1
        }
    }
    else {
        Write-Info "配置文件已存在，跳过配置步骤"
        Write-Info "如需重新配置，请运行: .\scripts\easy_install.ps1 -Reconfigure"
    }
    
    # 启动应用
    Start-Application
}

# 运行主函数
Main

