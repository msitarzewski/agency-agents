$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "[INFO] Root: $root"

function Setup-PythonProject {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectPath,
        [Parameter(Mandatory = $true)]
        [string[]]$RequirementFiles
    )

    if (-not (Test-Path $ProjectPath)) {
        Write-Warning "[WARN] Project path not found: $ProjectPath"
        return
    }

    Push-Location $ProjectPath
    try {
        Write-Host "[INFO] Setting up: $ProjectPath"

        if (-not (Test-Path ".venv")) {
            Write-Host "[INFO] Creating virtual environment..."
            py -m venv .venv
        }

        $pythonExe = Join-Path ".venv" "Scripts\\python.exe"
        if (-not (Test-Path $pythonExe)) {
            throw "Python executable not found in venv: $pythonExe"
        }

        & $pythonExe -m pip install --upgrade pip

        foreach ($req in $RequirementFiles) {
            if (Test-Path $req) {
                Write-Host "[INFO] Installing requirements from $req"
                & $pythonExe -m pip install -r $req
            }
        }

        Write-Host "[OK] Setup finished: $ProjectPath"
    }
    finally {
        Pop-Location
    }
}

Setup-PythonProject -ProjectPath (Join-Path $root "unified-ai-system") -RequirementFiles @("requirements.txt", "requirements-agent-framework.txt")
Setup-PythonProject -ProjectPath (Join-Path $root "aios") -RequirementFiles @()

Write-Host ""
Write-Host "[DONE] Installation completed."
Write-Host "[NEXT] To run Supreme tests:"
Write-Host "  Set-Location \"$root\\unified-ai-system\""
Write-Host "  .\\.venv\\Scripts\\python.exe -m pytest tests/core/test_supreme_brainiac.py tests/core/test_api_server_supreme_endpoints.py -q"
