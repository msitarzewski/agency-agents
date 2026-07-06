# ============================================================================
# Setup Embedded Python for Portable Version
# ============================================================================
# This script downloads and configures an embedded Python distribution
# to make the portable version truly independent from system Python
# ============================================================================

param(
    [string]$PythonVersion = "3.10.11",
    [string]$PortableDir = ""
)

$ErrorActionPreference = "Stop"

# Determine portable directory
if (-not $PortableDir) {
    $root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $PortableDir = Join-Path $root "release\TradingAgentsCN-portable"
}

if (-not (Test-Path $PortableDir)) {
    Write-Host "ERROR: Portable directory not found: $PortableDir" -ForegroundColor Red
    exit 1
}

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Setup Embedded Python $PythonVersion" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$pythonDir = Join-Path $PortableDir "vendors\python"
$tempDir = $env:TEMP

# ============================================================================
# Step 1: Download Embedded Python
# ============================================================================

Write-Host "[1/6] Downloading Python $PythonVersion embedded distribution..." -ForegroundColor Yellow
Write-Host ""

$pythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$pythonZip = Join-Path $tempDir "python-$PythonVersion-embed-amd64.zip"

Write-Host "  URL: $pythonUrl" -ForegroundColor Gray
Write-Host "  Downloading to: $pythonZip" -ForegroundColor Gray

try {
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing
    Write-Host "  ✅ Download completed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Download failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 2: Extract Python
# ============================================================================

Write-Host "[2/6] Extracting Python..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  Target directory: $pythonDir" -ForegroundColor Gray

# Remove old Python directory if exists
if (Test-Path $pythonDir) {
    Write-Host "  Removing old Python directory..." -ForegroundColor Gray
    Remove-Item -Path $pythonDir -Recurse -Force
}

# Create directory
New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null

# Extract
try {
    Expand-Archive -Path $pythonZip -DestinationPath $pythonDir -Force
    Write-Host "  ✅ Extraction completed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Extraction failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 3: Configure Python (Enable site-packages)
# ============================================================================

Write-Host "[3/6] Configuring Python..." -ForegroundColor Yellow
Write-Host ""

# Find and modify ._pth file
$pthFile = Get-ChildItem -Path $pythonDir -Filter "python*._pth" | Select-Object -First 1

if (-not $pthFile) {
    Write-Host "  ❌ Python ._pth file not found" -ForegroundColor Red
    exit 1
}

Write-Host "  Modifying: $($pthFile.Name)" -ForegroundColor Gray

try {
    # Read current content
    $content = Get-Content $pthFile.FullName
    
    # Uncomment 'import site' line
    $content = $content -replace "^#import site", "import site"
    
    # Add Lib\site-packages if not present
    if ($content -notcontains ".\Lib\site-packages") {
        $content += ".\Lib\site-packages"
    }
    
    # Write back
    Set-Content -Path $pthFile.FullName -Value $content -Encoding ASCII
    
    Write-Host "  ✅ Configuration completed" -ForegroundColor Green
    Write-Host "  Content:" -ForegroundColor Gray
    Get-Content $pthFile.FullName | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
} catch {
    Write-Host "  ❌ Configuration failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 4: Install pip
# ============================================================================

Write-Host "[4/6] Installing pip..." -ForegroundColor Yellow
Write-Host ""

$getPipUrls = @(
    "https://bootstrap.pypa.io/get-pip.py",
    "https://mirrors.aliyun.com/pypi/get-pip.py",
    "https://pypi.tuna.tsinghua.edu.cn/get-pip.py"
)
$getPipPath = Join-Path $pythonDir "get-pip.py"
$pythonExe = Join-Path $pythonDir "python.exe"

Write-Host "  Downloading get-pip.py..." -ForegroundColor Gray

$downloaded = $false
foreach ($url in $getPipUrls) {
    try {
        Write-Host "    Trying: $url" -ForegroundColor DarkGray
        Invoke-WebRequest -Uri $url -OutFile $getPipPath -UseBasicParsing -TimeoutSec 30
        Write-Host "  ✅ get-pip.py downloaded" -ForegroundColor Green
        $downloaded = $true
        break
    } catch {
        Write-Host "    ⚠️ Failed: $_" -ForegroundColor DarkGray
    }
}

if (-not $downloaded) {
    Write-Host "  ❌ All download attempts failed" -ForegroundColor Red
    Write-Host "  Please manually download get-pip.py and place it in:" -ForegroundColor Yellow
    Write-Host "    $getPipPath" -ForegroundColor Gray
    exit 1
}

Write-Host "  Installing pip (this may take a minute)..." -ForegroundColor Gray
$pipOutput = & $pythonExe $getPipPath 2>&1 | Out-String

# Check if pip module is available (ignore warnings about PATH)
$pipCheck = & $pythonExe -m pip --version 2>&1 | Out-String
if ($pipCheck -match "pip \d+\.\d+") {
    Write-Host "  ✅ pip installed successfully" -ForegroundColor Green
    Write-Host "    Version: $($Matches[0])" -ForegroundColor DarkGray
} else {
    Write-Host "  ⚠️ pip installation may have issues" -ForegroundColor Yellow
    Write-Host "  Output: $pipOutput" -ForegroundColor Gray
    Write-Host "  Attempting to continue..." -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Step 5: Install Dependencies
# ============================================================================

Write-Host "[5/6] Installing project dependencies..." -ForegroundColor Yellow
Write-Host ""

$requirementsFile = Join-Path $PortableDir "requirements.txt"

if (-not (Test-Path $requirementsFile)) {
    Write-Host "  ⚠️ requirements.txt not found: $requirementsFile" -ForegroundColor Yellow
    Write-Host "  Skipping dependency installation" -ForegroundColor Gray
} else {
    Write-Host "  Requirements file: $requirementsFile" -ForegroundColor Gray
    Write-Host "  Installing dependencies (this may take 5-10 minutes)..." -ForegroundColor Gray
    Write-Host ""

    # Try multiple pip mirrors
    $pipMirrors = @(
        @{Name="Default"; Args=@("-r", $requirementsFile, "--no-warn-script-location")},
        @{Name="Aliyun"; Args=@("-r", $requirementsFile, "--no-warn-script-location", "-i", "https://mirrors.aliyun.com/pypi/simple/", "--trusted-host", "mirrors.aliyun.com")},
        @{Name="Tsinghua"; Args=@("-r", $requirementsFile, "--no-warn-script-location", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn")}
    )

    $installed = $false
    foreach ($mirror in $pipMirrors) {
        Write-Host "  Trying $($mirror.Name) mirror..." -ForegroundColor Gray
        try {
            & $pythonExe -m pip install @($mirror.Args)

            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "  ✅ All dependencies installed successfully using $($mirror.Name) mirror" -ForegroundColor Green
                $installed = $true
                break
            } else {
                Write-Host "  ⚠️ $($mirror.Name) mirror failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ⚠️ $($mirror.Name) mirror error: $_" -ForegroundColor Yellow
        }
    }

    if (-not $installed) {
        Write-Host ""
        Write-Host "  ❌ All mirrors failed to install dependencies" -ForegroundColor Red
        Write-Host "  You may need to install manually:" -ForegroundColor Yellow
        Write-Host "    cd $pythonDir" -ForegroundColor Gray
        Write-Host "    .\python.exe -m pip install -r $requirementsFile" -ForegroundColor Gray
        exit 1
    }
}

Write-Host ""

# ============================================================================
# Step 6: Verify Installation
# ============================================================================

Write-Host "[6/6] Verifying installation..." -ForegroundColor Yellow
Write-Host ""

# Check Python version
Write-Host "  Checking Python version..." -ForegroundColor Gray
$pythonVersionOutput = & $pythonExe --version 2>&1
Write-Host "    $pythonVersionOutput" -ForegroundColor Cyan

# Check pip version
Write-Host "  Checking pip version..." -ForegroundColor Gray
$pipVersionOutput = & $pythonExe -m pip --version 2>&1
Write-Host "    $pipVersionOutput" -ForegroundColor Cyan

# List installed packages
Write-Host "  Checking installed packages..." -ForegroundColor Gray
$packageCount = (& $pythonExe -m pip list 2>&1 | Measure-Object -Line).Lines - 2
Write-Host "    Installed packages: $packageCount" -ForegroundColor Cyan

# Test import of key packages
Write-Host "  Testing key imports..." -ForegroundColor Gray
$testImports = @("fastapi", "uvicorn", "pymongo", "redis", "langchain")
$importSuccess = 0
$importFailed = 0

foreach ($pkg in $testImports) {
    $testResult = & $pythonExe -c "import $pkg" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ $pkg" -ForegroundColor Green
        $importSuccess++
    } else {
        Write-Host "    ❌ $pkg" -ForegroundColor Red
        $importFailed++
    }
}

Write-Host ""

# ============================================================================
# Summary
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  ✅ Embedded Python Setup Completed!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  Python Version: $pythonVersionOutput" -ForegroundColor Gray
Write-Host "  Python Location: $pythonDir" -ForegroundColor Gray
Write-Host "  Installed Packages: $packageCount" -ForegroundColor Gray
Write-Host "  Import Tests: $importSuccess passed, $importFailed failed" -ForegroundColor Gray
Write-Host ""

if ($importFailed -gt 0) {
    Write-Host "⚠️ Warning: Some imports failed. Please check the installation." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Update start scripts to use vendors\python\python.exe" -ForegroundColor Gray
Write-Host "  2. Remove the old venv directory" -ForegroundColor Gray
Write-Host "  3. Test the portable version" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 To update scripts automatically, run:" -ForegroundColor Yellow
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\deployment\update_scripts_for_embedded_python.ps1" -ForegroundColor Cyan
Write-Host ""

