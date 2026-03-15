# install.ps1 -- Install The Agency agents into your local agentic tool(s).
#
# Reads converted files from integrations/ and copies them to the appropriate
# config directory for each tool. Run scripts/convert.ps1 first if integrations/
# is missing or stale.
#
# Usage:
#   .\scripts\install.ps1 [-Tool <name>] [-Interactive] [-NoInteractive] [-Help]

param (
    [string]$Tool = "all",
    [switch]$Interactive,
    [switch]$NoInteractive,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\scripts\install.ps1 [-Tool <name>] [-Interactive] [-NoInteractive] [-Help]"
    Write-Host ""
    Write-Host "Tools: claude-code, copilot, antigravity, gemini-cli, opencode, openclaw, cursor, aider, windsurf, qwen"
    exit 0
}

$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$Integrations = Join-Path $RepoRoot "integrations"

if (-not (Test-Path $Integrations)) {
    Write-Error "integrations/ not found. Run .\scripts\convert.ps1 first."
    exit 1
}

$AllTools = @("claude-code", "copilot", "antigravity", "gemini-cli", "opencode", "openclaw", "cursor", "aider", "windsurf", "qwen")

# --- Detection ---

function Test-Detected {
    param($T)
    $UserHome = $env:USERPROFILE
    switch ($T) {
        "claude-code" { return Test-Path (Join-Path $UserHome ".claude") }
        "copilot"     { return (Get-Command "code" -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $UserHome ".github")) -or (Test-Path (Join-Path $UserHome ".copilot")) }
        "antigravity" { return Test-Path (Join-Path $UserHome ".gemini\antigravity\skills") }
        "gemini-cli"  { return (Get-Command "gemini" -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $UserHome ".gemini")) }
        "cursor"      { return (Get-Command "cursor" -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $UserHome ".cursor")) }
        "opencode"    { return (Get-Command "opencode" -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $UserHome ".config\opencode")) }
        "aider"        { return [bool](Get-Command "aider" -ErrorAction SilentlyContinue) }
        "openclaw"    { return (Get-Command "openclaw" -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $UserHome ".openclaw")) }
        "windsurf"    { return (Get-Command "windsurf" -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $UserHome ".codeium")) }
        "qwen"         { return (Get-Command "qwen" -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $UserHome ".qwen")) }
    }
    return $false
}

# --- Installers ---

function Install-ClaudeCode {
    $Dest = Join-Path $env:USERPROFILE ".claude\agents"
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force }
    $Count = 0
    $AgentDirs = @("design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management", "testing", "support", "spatial-computing", "specialized")
    foreach ($Dir in $AgentDirs) {
        $Path = Join-Path $RepoRoot $Dir
        if (Test-Path $Path) {
            $Files = Get-ChildItem -Path $Path -Filter "*.md" -File
            foreach ($F in $Files) {
                if ((Get-Content $F.FullName -TotalCount 1 -Encoding UTF8).StartsWith("---")) {
                    Copy-Item $F.FullName $Dest -Force
                    $Count++
                }
            }
        }
    }
    Write-Host "[OK]  Claude Code: $Count agents -> $Dest"
}

function Install-Copilot {
    $DestGithub = Join-Path $env:USERPROFILE ".github\agents"
    $DestCopilot = Join-Path $env:USERPROFILE ".copilot\agents"
    if (-not (Test-Path $DestGithub)) { New-Item -ItemType Directory -Path $DestGithub -Force }
    if (-not (Test-Path $DestCopilot)) { New-Item -ItemType Directory -Path $DestCopilot -Force }
    $Count = 0
    $AgentDirs = @("design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management", "testing", "support", "spatial-computing", "specialized")
    foreach ($Dir in $AgentDirs) {
        $Path = Join-Path $RepoRoot $Dir
        if (Test-Path $Path) {
            $Files = Get-ChildItem -Path $Path -Filter "*.md" -File
            foreach ($F in $Files) {
                if ((Get-Content $F.FullName -TotalCount 1 -Encoding UTF8).StartsWith("---")) {
                    Copy-Item $F.FullName $DestGithub -Force
                    Copy-Item $F.FullName $DestCopilot -Force
                    $Count++
                }
            }
        }
    }
    Write-Host "[OK]  Copilot: $Count agents -> $DestGithub"
}

function Install-Antigravity {
    $Src = Join-Path $Integrations "antigravity"
    $Dest = Join-Path $env:USERPROFILE ".gemini\antigravity\skills"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/antigravity missing."; return }
    $Dirs = Get-ChildItem -Path $Src -Directory
    foreach ($D in $Dirs) {
        $Target = Join-Path $Dest $D.Name
        if (-not (Test-Path $Target)) { New-Item -ItemType Directory -Path $Target -Force }
        Copy-Item (Join-Path $D.FullName "SKILL.md") $Target -Force
    }
    Write-Host "[OK]  Antigravity: $($Dirs.Count) skills -> $Dest"
}

function Install-GeminiCLI {
    $Src = Join-Path $Integrations "gemini-cli"
    $Dest = Join-Path $env:USERPROFILE ".gemini\extensions\agency-agents"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/gemini-cli missing."; return }
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force }
    Copy-Item (Join-Path $Src "gemini-extension.json") $Dest -Force
    $SkillsSrc = Join-Path $Src "skills"
    $SkillsDest = Join-Path $Dest "skills"
    if (-not (Test-Path $SkillsDest)) { New-Item -ItemType Directory -Path $SkillsDest -Force }
    $Dirs = Get-ChildItem -Path $SkillsSrc -Directory
    foreach ($D in $Dirs) {
        $Target = Join-Path $SkillsDest $D.Name
        if (-not (Test-Path $Target)) { New-Item -ItemType Directory -Path $Target -Force }
        Copy-Item (Join-Path $D.FullName "SKILL.md") $Target -Force
    }
    Write-Host "[OK]  Gemini CLI: $($Dirs.Count) skills -> $Dest"
}

function Install-OpenCode {
    $Src = Join-Path $Integrations "opencode\agents"
    $Dest = Join-Path $PWD ".opencode\agents"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/opencode missing."; return }
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force }
    Copy-Item (Join-Path $Src "*.md") $Dest -Force
    Write-Host "[OK]  OpenCode: agents -> $Dest"
}

function Install-Cursor {
    $Src = Join-Path $Integrations "cursor\rules"
    $Dest = Join-Path $PWD ".cursor\rules"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/cursor missing."; return }
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force }
    Copy-Item (Join-Path $Src "*.mdc") $Dest -Force
    Write-Host "[OK]  Cursor: rules -> $Dest"
}

function Install-Aider {
    $Src = Join-Path $Integrations "aider\CONVENTIONS.md"
    $Dest = Join-Path $PWD "CONVENTIONS.md"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/aider missing."; return }
    Copy-Item $Src $Dest -Force
    Write-Host "[OK]  Aider: CONVENTIONS.md -> $Dest"
}

function Install-Windsurf {
    $Src = Join-Path $Integrations "windsurf\.windsurfrules"
    $Dest = Join-Path $PWD ".windsurfrules"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/windsurf missing."; return }
    Copy-Item $Src $Dest -Force
    Write-Host "[OK]  Windsurf: .windsurfrules -> $Dest"
}

function Install-OpenClaw {
    $Src = Join-Path $Integrations "openclaw"
    $Dest = Join-Path $env:USERPROFILE ".openclaw\agency-agents"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/openclaw missing."; return }
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force }
    $Dirs = Get-ChildItem -Path $Src -Directory
    foreach ($D in $Dirs) {
        $Target = Join-Path $Dest $D.Name
        if (-not (Test-Path $Target)) { New-Item -ItemType Directory -Path $Target -Force }
        Copy-Item (Join-Path $D.FullName "*.md") $Target -Force
    }
    Write-Host "[OK]  OpenClaw: $($Dirs.Count) workspaces -> $Dest"
}

function Install-Qwen {
    $Src = Join-Path $Integrations "qwen\agents"
    $Dest = Join-Path $PWD ".qwen\agents"
    if (-not (Test-Path $Src)) { Write-Warning "integrations/qwen missing."; return }
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force }
    Copy-Item (Join-Path $Src "*.md") $Dest -Force
    Write-Host "[OK]  Qwen Code: agents -> $Dest"
}

# --- Main Interaction ---

$SelectedTools = @()

if ($Interactive -or (-not $NoInteractive -and $Tool -eq "all")) {
    Write-Host "`n  The Agency -- Tool Installer (PowerShell)"
    Write-Host "  ------------------------------------------------"
    Write-Host "  Detected tools (marked with *):"
    
    $TempList = @()
    for ($i = 0; $i -lt $AllTools.Length; $i++) {
        $T = $AllTools[$i]
        $Detected = Test-Detected $T
        $Mark = if ($Detected) { "*" } else { " " }
        Write-Host "  $($i + 1)) [$Mark] $T"
        $TempList += [PSCustomObject]@{ Id = $i + 1; Name = $T; Detected = $Detected }
    }
    
    Write-Host "`n  Enter numbers separated by space (e.g. 1 3 7), 'all', or 'q' to quit."
    $Input = Read-Host "  >> "
    
    if ($Input -eq "all") { $SelectedTools = $AllTools }
    elseif ($Input -eq "q") { exit 0 }
    else {
        $Indices = $Input -split "\s+"
        foreach ($Idx in $Indices) {
            if ($Idx -as [int] -and $Idx -ge 1 -and $Idx -le $AllTools.Length) {
                $SelectedTools += $AllTools[$Idx - 1]
            }
        }
    }
} elseif ($Tool -ne "all") {
    $SelectedTools = @($Tool)
} else {
    # Non-interactive, auto-detect
    foreach ($T in $AllTools) {
        if (Test-Detected $T) { $SelectedTools += $T }
    }
}

if ($SelectedTools.Count -eq 0) {
    Write-Warning "No tools selected or detected. Use -Tool <name> to force install."
    exit 0
}

Write-Host "`nInstalling tools: $($SelectedTools -join ', ')"

foreach ($T in $SelectedTools) {
    switch ($T) {
        "claude-code" { Install-ClaudeCode }
        "copilot"     { Install-Copilot }
        "antigravity" { Install-Antigravity }
        "gemini-cli"  { Install-GeminiCLI }
        "opencode"    { Install-OpenCode }
        "cursor"      { Install-Cursor }
        "aider"        { Install-Aider }
        "windsurf"    { Install-Windsurf }
        "openclaw"    { Install-OpenClaw }
        "qwen"         { Install-Qwen }
    }
}

Write-Host "`n  Done! Installed $($SelectedTools.Count) tool(s).`n"
