<#
.SYNOPSIS
install.ps1 -- Install The Agency agents into your local agentic tool(s).

.DESCRIPTION
Reads converted files from integrations/ and copies them to the appropriate
config directory for each tool. Run scripts/convert.ps1 first if integrations/
is missing or stale.

.PARAMETER Tool
Install only the specified tool.

.PARAMETER Interactive
Show interactive selector.

.PARAMETER NoInteractive
Skip interactive selector, install all detected tools.
#>

param (
    [string]$Tool = "all",
    [switch]$Interactive,
    [switch]$NoInteractive
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Integrations = Join-Path $RepoRoot "integrations"

$AllTools = @("claude-code", "copilot", "antigravity", "gemini-cli", "opencode", "openclaw", "cursor", "aider", "windsurf", "qwen")

# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------
function Write-Ok { param([string]$msg) Write-Host "[OK]  $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg) Write-Host "[!!]  $msg" -ForegroundColor Yellow }
function Write-Err { param([string]$msg) Write-Host "[ERR] $msg" -ForegroundColor Red }
function Write-Header { param([string]$msg) Write-Host "`n$msg" -ForegroundColor Cyan }
function Write-Dim { param([string]$msg) Write-Host "$msg" -ForegroundColor DarkGray }

function Draw-Box {
    param([string]$text)
    $inner = 48
    $line = "-" * $inner
    Write-Host "  +$line+"
    # Strip basic ansi escapes for length calculation if any (though PowerShell coloring is typically done via Write-Host)
    $visibleLength = ($text -replace "`e\[\d+m", "").Length
    $pad = $inner - 2 - $visibleLength
    if ($pad -lt 0) { $pad = 0 }
    $padStr = " " * $pad
    Write-Host "  | $text$padStr |"
    Write-Host "  +$line+"
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
if (-not (Test-Path $Integrations)) {
    Write-Err "integrations/ not found. Run ./scripts/convert.ps1 first."
    exit 1
}

# ---------------------------------------------------------------------------
# Tool detection
# ---------------------------------------------------------------------------
function Detect-ClaudeCode { Test-Path (Join-Path $env:USERPROFILE ".claude") }
function Detect-Copilot { (Get-Command code -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE ".github")) }
function Detect-Antigravity { Test-Path (Join-Path $env:USERPROFILE ".gemini/antigravity/skills") }
function Detect-GeminiCli { (Get-Command gemini -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE ".gemini")) }
function Detect-OpenCode { (Get-Command opencode -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE ".config/opencode")) }
function Detect-OpenClaw { (Get-Command openclaw -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE ".openclaw")) }
function Detect-Cursor { (Get-Command cursor -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE ".cursor")) }
function Detect-Aider { (Get-Command aider -ErrorAction SilentlyContinue) }
function Detect-Windsurf { (Get-Command windsurf -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE ".codeium")) }
function Detect-Qwen { (Get-Command qwen -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $env:USERPROFILE ".qwen")) }

function Get-IsDetected {
    param([string]$t)
    switch ($t) {
        "claude-code" { return (Detect-ClaudeCode) }
        "copilot"     { return (Detect-Copilot) }
        "antigravity" { return (Detect-Antigravity) }
        "gemini-cli"  { return (Detect-GeminiCli) }
        "opencode"    { return (Detect-OpenCode) }
        "openclaw"    { return (Detect-OpenClaw) }
        "cursor"      { return (Detect-Cursor) }
        "aider"       { return (Detect-Aider) }
        "windsurf"    { return (Detect-Windsurf) }
        "qwen"        { return (Detect-Qwen) }
        default       { return $false }
    }
}

function Get-ToolLabel {
    param([string]$t)
    switch ($t) {
        "claude-code" { return "Claude Code".PadRight(14) + "  (claude.ai/code)" }
        "copilot"     { return "Copilot".PadRight(14) + "  (~/.github/agents)" }
        "antigravity" { return "Antigravity".PadRight(14) + "  (~/.gemini/antigravity)" }
        "gemini-cli"  { return "Gemini CLI".PadRight(14) + "  (gemini extension)" }
        "opencode"    { return "OpenCode".PadRight(14) + "  (opencode.ai)" }
        "openclaw"    { return "OpenClaw".PadRight(14) + "  (~/.openclaw)" }
        "cursor"      { return "Cursor".PadRight(14) + "  (.cursor/rules)" }
        "aider"       { return "Aider".PadRight(14) + "  (CONVENTIONS.md)" }
        "windsurf"    { return "Windsurf".PadRight(14) + "  (.windsurfrules)" }
        "qwen"        { return "Qwen Code".PadRight(14) + "  (~/.qwen/agents)" }
    }
}

# ---------------------------------------------------------------------------
# Installers
# ---------------------------------------------------------------------------

function Install-ClaudeCode {
    $dest = Join-Path $env:USERPROFILE ".claude/agents"
    $count = 0
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    $dirs = @("design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management", "testing", "support", "spatial-computing", "specialized")
    foreach ($dir in $dirs) {
        $dirPath = Join-Path $RepoRoot $dir
        if (Test-Path $dirPath) {
            Get-ChildItem -Path $dirPath -Filter "*.md" -Recurse | ForEach-Object {
                $firstLine = Get-Content $_.FullName -TotalCount 1
                if ($firstLine -eq "---") {
                    Copy-Item -Path $_.FullName -Destination $dest -Force
                    $count++
                }
            }
        }
    }
    Write-Ok "Claude Code: $count agents -> $dest"
}

function Install-Copilot {
    $dest = Join-Path $env:USERPROFILE ".github/agents"
    $count = 0
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    $dirs = @("design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management", "testing", "support", "spatial-computing", "specialized")
    foreach ($dir in $dirs) {
        $dirPath = Join-Path $RepoRoot $dir
        if (Test-Path $dirPath) {
            Get-ChildItem -Path $dirPath -Filter "*.md" -Recurse | ForEach-Object {
                $firstLine = Get-Content $_.FullName -TotalCount 1
                if ($firstLine -eq "---") {
                    Copy-Item -Path $_.FullName -Destination $dest -Force
                    $count++
                }
            }
        }
    }
    Write-Ok "Copilot: $count agents -> $dest"
}

function Install-Antigravity {
    $src = Join-Path $Integrations "antigravity"
    $dest = Join-Path $env:USERPROFILE ".gemini/antigravity/skills"
    $count = 0
    if (-not (Test-Path $src)) { Write-Err "integrations/antigravity missing. Run convert.ps1 first."; return }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    
    Get-ChildItem -Path $src -Directory | ForEach-Object {
        $name = $_.Name
        $targetDir = Join-Path $dest $name
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        $skillSrc = Join-Path $_.FullName "SKILL.md"
        if (Test-Path $skillSrc) {
            Copy-Item -Path $skillSrc -Destination (Join-Path $targetDir "SKILL.md") -Force
            $count++
        }
    }
    Write-Ok "Antigravity: $count skills -> $dest"
}

function Install-GeminiCli {
    $src = Join-Path $Integrations "gemini-cli"
    $dest = Join-Path $env:USERPROFILE ".gemini/extensions/agency-agents"
    $count = 0
    
    if (-not (Test-Path $src)) { Write-Err "integrations/gemini-cli missing. Run convert.ps1 first."; return }
    
    $manifest = Join-Path $src "gemini-extension.json"
    $skillsDir = Join-Path $src "skills"
    
    if (-not (Test-Path $manifest)) { Write-Err "integrations/gemini-cli/gemini-extension.json missing."; return }
    if (-not (Test-Path $skillsDir)) { Write-Err "integrations/gemini-cli/skills missing."; return }
    
    New-Item -ItemType Directory -Force -Path (Join-Path $dest "skills") | Out-Null
    Copy-Item -Path $manifest -Destination (Join-Path $dest "gemini-extension.json") -Force
    
    Get-ChildItem -Path $skillsDir -Directory | ForEach-Object {
        $name = $_.Name
        $targetDir = Join-Path $dest "skills/$name"
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        $skillSrc = Join-Path $_.FullName "SKILL.md"
        if (Test-Path $skillSrc) {
            Copy-Item -Path $skillSrc -Destination (Join-Path $targetDir "SKILL.md") -Force
            $count++
        }
    }
    Write-Ok "Gemini CLI: $count skills -> $dest"
}

function Install-OpenCode {
    $src = Join-Path $Integrations "opencode/agents"
    $dest = Join-Path (Get-Location).Path ".opencode/agents"
    $count = 0
    if (-not (Test-Path $src)) { Write-Err "integrations/opencode missing. Run convert.ps1 first."; return }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    
    Get-ChildItem -Path $src -Filter "*.md" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $dest -Force
        $count++
    }
    Write-Ok "OpenCode: $count agents -> $dest"
    Write-Warn "OpenCode: project-scoped. Run from your project root to install there."
}

function Install-OpenClaw {
    $src = Join-Path $Integrations "openclaw"
    $dest = Join-Path $env:USERPROFILE ".openclaw/agency-agents"
    $count = 0
    if (-not (Test-Path $src)) { Write-Err "integrations/openclaw missing. Run convert.ps1 first."; return }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    
    Get-ChildItem -Path $src -Directory | ForEach-Object {
        $name = $_.Name
        $targetDir = Join-Path $dest $name
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        
        $files = @("SOUL.md", "AGENTS.md", "IDENTITY.md")
        foreach ($f in $files) {
            $fPath = Join-Path $_.FullName $f
            if (Test-Path $fPath) {
                Copy-Item -Path $fPath -Destination (Join-Path $targetDir $f) -Force
            }
        }
        
        if (Get-Command openclaw -ErrorAction SilentlyContinue) {
            try {
                openclaw agents add $name --workspace "$targetDir" --non-interactive 2>$null
            } catch {}
        }
        $count++
    }
    Write-Ok "OpenClaw: $count workspaces -> $dest"
    if (Get-Command openclaw -ErrorAction SilentlyContinue) {
        Write-Warn "OpenClaw: run 'openclaw gateway restart' to activate new agents"
    }
}

function Install-Cursor {
    $src = Join-Path $Integrations "cursor/rules"
    $dest = Join-Path (Get-Location).Path ".cursor/rules"
    $count = 0
    if (-not (Test-Path $src)) { Write-Err "integrations/cursor missing. Run convert.ps1 first."; return }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    
    Get-ChildItem -Path $src -Filter "*.mdc" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $dest -Force
        $count++
    }
    Write-Ok "Cursor: $count rules -> $dest"
    Write-Warn "Cursor: project-scoped. Run from your project root to install there."
}

function Install-Aider {
    $src = Join-Path $Integrations "aider/CONVENTIONS.md"
    $dest = Join-Path (Get-Location).Path "CONVENTIONS.md"
    if (-not (Test-Path $src)) { Write-Err "integrations/aider/CONVENTIONS.md missing. Run convert.ps1 first."; return }
    if (Test-Path $dest) {
        Write-Warn "Aider: CONVENTIONS.md already exists at $dest (remove to reinstall)."
        return
    }
    Copy-Item -Path $src -Destination $dest -Force
    Write-Ok "Aider: installed -> $dest"
    Write-Warn "Aider: project-scoped. Run from your project root to install there."
}

function Install-Windsurf {
    $src = Join-Path $Integrations "windsurf/.windsurfrules"
    $dest = Join-Path (Get-Location).Path ".windsurfrules"
    if (-not (Test-Path $src)) { Write-Err "integrations/windsurf/.windsurfrules missing. Run convert.ps1 first."; return }
    if (Test-Path $dest) {
        Write-Warn "Windsurf: .windsurfrules already exists at $dest (remove to reinstall)."
        return
    }
    Copy-Item -Path $src -Destination $dest -Force
    Write-Ok "Windsurf: installed -> $dest"
    Write-Warn "Windsurf: project-scoped. Run from your project root to install there."
}

function Install-Qwen {
    $src = Join-Path $Integrations "qwen/agents"
    $dest = Join-Path (Get-Location).Path ".qwen/agents"
    $count = 0
    if (-not (Test-Path $src)) { Write-Err "integrations/qwen missing. Run convert.ps1 first."; return }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    
    Get-ChildItem -Path $src -Filter "*.md" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $dest -Force
        $count++
    }
    Write-Ok "Qwen Code: installed $count agents to $dest"
    Write-Warn "Qwen Code: project-scoped. Run from your project root to install there."
    Write-Warn "Tip: Run '/agents manage' in Qwen Code to refresh, or restart session"
}

function Install-Tool {
    param([string]$t)
    switch ($t) {
        "claude-code" { Install-ClaudeCode }
        "copilot"     { Install-Copilot }
        "antigravity" { Install-Antigravity }
        "gemini-cli"  { Install-GeminiCli }
        "opencode"    { Install-OpenCode }
        "openclaw"    { Install-OpenClaw }
        "cursor"      { Install-Cursor }
        "aider"       { Install-Aider }
        "windsurf"    { Install-Windsurf }
        "qwen"        { Install-Qwen }
    }
}

# ---------------------------------------------------------------------------
# Interactive selector
# ---------------------------------------------------------------------------
function Show-InteractiveSelect {
    $selected = @()
    $detectedMap = @()

    foreach ($t in $AllTools) {
        if (Get-IsDetected $t) {
            $selected += 1
            $detectedMap += 1
        } else {
            $selected += 0
            $detectedMap += 0
        }
    }

    $numTools = $AllTools.Count

    while ($true) {
        Clear-Host
        Write-Host ""
        Draw-Box "  The Agency -- Tool Installer"
        Write-Host ""
        Write-Host "  System scan:  [*] = detected on this machine" -ForegroundColor DarkGray
        Write-Host ""

        for ($i = 0; $i -lt $numTools; $i++) {
            $t = $AllTools[$i]
            $num = $i + 1
            $label = Get-ToolLabel $t
            $dot = if ($detectedMap[$i] -eq 1) { "[*]" } else { "[ ]" }
            $chk = if ($selected[$i] -eq 1) { "[x]" } else { "[ ]" }
            
            $dotColor = if ($detectedMap[$i] -eq 1) { "Green" } else { "DarkGray" }
            $chkColor = if ($selected[$i] -eq 1) { "Green" } else { "DarkGray" }
            
            Write-Host -NoNewline "  "
            Write-Host -NoNewline $chk -ForegroundColor $chkColor
            Write-Host -NoNewline "  $num)  "
            Write-Host -NoNewline $dot -ForegroundColor $dotColor
            Write-Host "  $label"
        }

        Write-Host ""
        Write-Host "  ------------------------------------------------"
        Write-Host "  [1-$numTools] toggle   [a] all   [n] none   [d] detected" -ForegroundColor Cyan
        Write-Host "  [Enter] install   [q] quit" -ForegroundColor Green
        Write-Host ""
        $input = Read-Host "  >> "

        if ($input -match "^[qQ]$") {
            Write-Host ""
            Write-Ok "Aborted."
            exit 0
        } elseif ($input -match "^[aA]$") {
            for ($j = 0; $j -lt $numTools; $j++) { $selected[$j] = 1 }
        } elseif ($input -match "^[nN]$") {
            for ($j = 0; $j -lt $numTools; $j++) { $selected[$j] = 0 }
        } elseif ($input -match "^[dD]$") {
            for ($j = 0; $j -lt $numTools; $j++) { $selected[$j] = $detectedMap[$j] }
        } elseif ([string]::IsNullOrWhiteSpace($input)) {
            $any = $false
            foreach ($s in $selected) { if ($s -eq 1) { $any = $true; break } }
            if ($any) {
                break
            } else {
                Write-Host "  Nothing selected -- pick a tool or press q to quit." -ForegroundColor Yellow
                Start-Sleep -Seconds 1
            }
        } else {
            $toggled = $false
            $parts = $input -split "\s+"
            foreach ($num in $parts) {
                if ($num -match "^\d+$") {
                    $idx = [int]$num - 1
                    if ($idx -ge 0 -and $idx -lt $numTools) {
                        $selected[$idx] = if ($selected[$idx] -eq 1) { 0 } else { 1 }
                        $toggled = $true
                    }
                }
            }
            if (-not $toggled) {
                Write-Host "  Invalid. Enter a number 1-$numTools, or a command." -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        }
    }

    $global:SELECTED_TOOLS = @()
    for ($i = 0; $i -lt $numTools; $i++) {
        if ($selected[$i] -eq 1) {
            $global:SELECTED_TOOLS += $AllTools[$i]
        }
    }
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
$useInteractive = $false

if ($Interactive) {
    $useInteractive = $true
} elseif ($NoInteractive) {
    $useInteractive = $false
} elseif ($Tool -eq "all" -and [Environment]::UserInteractive) {
    $useInteractive = $true
}

if ($Tool -ne "all") {
    if ($AllTools -notcontains $Tool) {
        Write-Err "Unknown tool '$Tool'. Valid: $($AllTools -join ', ')"
        exit 1
    }
}

$global:SELECTED_TOOLS = @()

if ($useInteractive) {
    Show-InteractiveSelect
} elseif ($Tool -ne "all") {
    $global:SELECTED_TOOLS += $Tool
} else {
    Write-Header "The Agency -- Scanning for installed tools..."
    Write-Host ""
    foreach ($t in $AllTools) {
        if (Get-IsDetected $t) {
            $global:SELECTED_TOOLS += $t
            $label = Get-ToolLabel $t
            Write-Host -NoNewline "  "
            Write-Host -NoNewline "[*]" -ForegroundColor Green
            Write-Host -NoNewline "  $label  "
            Write-Host "detected" -ForegroundColor DarkGray
        } else {
            $label = Get-ToolLabel $t
            Write-Host -NoNewline "  "
            Write-Host -NoNewline "[ ]" -ForegroundColor DarkGray
            Write-Host -NoNewline "  $label  "
            Write-Host "not found" -ForegroundColor DarkGray
        }
    }
}

if ($global:SELECTED_TOOLS.Count -eq 0) {
    Write-Warn "No tools selected or detected. Nothing to install."
    Write-Host ""
    Write-Dim "  Tip: use -Tool <name> to force-install a specific tool."
    Write-Dim "  Available: $($AllTools -join ' ')"
    exit 0
}

Write-Host ""
Write-Header "The Agency -- Installing agents"
Write-Host "  Repo:       $RepoRoot"
Write-Host "  Installing: $($global:SELECTED_TOOLS -join ' ')"
Write-Host ""

$installed = 0
foreach ($t in $global:SELECTED_TOOLS) {
    Install-Tool $t
    $installed++
}

Write-Host ""
Draw-Box "  Done!  Installed $installed tool(s)."
Write-Host ""
Write-Dim "  Run ./scripts/convert.ps1 to regenerate after adding or editing agents."
Write-Host ""