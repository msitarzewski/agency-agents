#Requires -Version 5.1
<#
.SYNOPSIS
    Install The Agency agents into your local agentic tool(s) on Windows.

.DESCRIPTION
    Windows-native counterpart of install.sh. Reads converted files from
    integrations/ and copies them to the appropriate config directory for each
    tool. Run scripts/convert.sh (via WSL or Git Bash) first if integrations/
    is missing or stale.

.PARAMETER Tool
    Install only the specified tool. Valid values:
    claude-code, copilot, antigravity, gemini-cli, opencode, openclaw,
    cursor, aider, windsurf, qwen, all (default).

.PARAMETER Help
    Show this help message.

.EXAMPLE
    .\scripts\install.ps1
    .\scripts\install.ps1 -Tool claude-code
    .\scripts\install.ps1 -Tool cursor
#>

[CmdletBinding()]
param(
    [ValidateSet('claude-code','copilot','antigravity','gemini-cli','opencode',
                 'openclaw','cursor','aider','windsurf','qwen','all')]
    [string]$Tool = 'all',

    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot    = Split-Path -Parent $ScriptDir
$Integrations = Join-Path $RepoRoot 'integrations'

$AllTools = @(
    'claude-code','copilot','antigravity','gemini-cli','opencode',
    'openclaw','cursor','aider','windsurf','qwen'
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Ok    { param([string]$Msg) Write-Host "[OK]  $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "[!!]  $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "[ERR] $Msg" -ForegroundColor Red }
function Write-Header { param([string]$Msg) Write-Host "`n$Msg" -ForegroundColor White -NoNewline; Write-Host "" }

function Resolve-ToolPath {
    param([string]$Binary)
    $cmd = Get-Command $Binary -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

# ---------------------------------------------------------------------------
# Tool detection
# ---------------------------------------------------------------------------
function Test-ToolDetected {
    param([string]$ToolName)
    switch ($ToolName) {
        'claude-code'  { return ((Resolve-ToolPath 'claude') -or (Test-Path "$env:USERPROFILE\.claude")) }
        'copilot'      { return ((Resolve-ToolPath 'code') -or (Test-Path "$env:USERPROFILE\.github") -or (Test-Path "$env:USERPROFILE\.copilot")) }
        'antigravity'  { return (Test-Path "$env:USERPROFILE\.gemini\antigravity\skills") }
        'gemini-cli'   { return ((Resolve-ToolPath 'gemini') -or (Test-Path "$env:USERPROFILE\.gemini")) }
        'cursor'       { return ((Resolve-ToolPath 'cursor') -or (Test-Path "$env:USERPROFILE\.cursor")) }
        'opencode'     { return ((Resolve-ToolPath 'opencode') -or (Test-Path "$env:USERPROFILE\.config\opencode")) }
        'aider'        { return [bool](Resolve-ToolPath 'aider') }
        'openclaw'     { return ((Resolve-ToolPath 'openclaw') -or (Test-Path "$env:USERPROFILE\.openclaw")) }
        'windsurf'     { return ((Resolve-ToolPath 'windsurf') -or (Test-Path "$env:USERPROFILE\.codeium")) }
        'qwen'         { return ((Resolve-ToolPath 'qwen') -or (Test-Path "$env:USERPROFILE\.qwen")) }
        default        { return $false }
    }
}

# ---------------------------------------------------------------------------
# Installers
# ---------------------------------------------------------------------------
function Install-ClaudeCode {
    $dest = Join-Path $env:USERPROFILE '.claude\agents'
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    $count = 0
    $agentDirs = @('academic','design','engineering','game-development','marketing',
                   'paid-media','sales','product','project-management','testing',
                   'support','spatial-computing','specialized')
    foreach ($dir in $agentDirs) {
        $dirPath = Join-Path $RepoRoot $dir
        if (-not (Test-Path $dirPath)) { continue }
        Get-ChildItem -Path $dirPath -Filter '*.md' -File | ForEach-Object {
            $firstLine = Get-Content $_.FullName -TotalCount 1
            if ($firstLine -eq '---') {
                Copy-Item $_.FullName -Destination $dest -Force
                $count++
            }
        }
    }
    Write-Ok "Claude Code: $count agents -> $dest"
}

function Install-Copilot {
    $destGH  = Join-Path $env:USERPROFILE '.github\agents'
    $destCop = Join-Path $env:USERPROFILE '.copilot\agents'
    New-Item -ItemType Directory -Path $destGH -Force | Out-Null
    New-Item -ItemType Directory -Path $destCop -Force | Out-Null
    $count = 0
    $agentDirs = @('academic','design','engineering','game-development','marketing',
                   'paid-media','sales','product','project-management','testing',
                   'support','spatial-computing','specialized')
    foreach ($dir in $agentDirs) {
        $dirPath = Join-Path $RepoRoot $dir
        if (-not (Test-Path $dirPath)) { continue }
        Get-ChildItem -Path $dirPath -Filter '*.md' -File | ForEach-Object {
            $firstLine = Get-Content $_.FullName -TotalCount 1
            if ($firstLine -eq '---') {
                Copy-Item $_.FullName -Destination $destGH -Force
                Copy-Item $_.FullName -Destination $destCop -Force
                $count++
            }
        }
    }
    Write-Ok "Copilot: $count agents -> $destGH"
    Write-Ok "Copilot: $count agents -> $destCop"
}

function Install-Cursor {
    $src  = Join-Path $Integrations 'cursor\rules'
    $dest = Join-Path $PWD '.cursor\rules'
    if (-not (Test-Path $src)) { Write-Err "integrations/cursor missing. Run convert.sh first."; return }
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    $count = 0
    Get-ChildItem -Path $src -Filter '*.mdc' -File | ForEach-Object {
        Copy-Item $_.FullName -Destination $dest -Force
        $count++
    }
    Write-Ok "Cursor: $count rules -> $dest"
    Write-Warn "Cursor: project-scoped. Run from your project root to install there."
}

function Install-Aider {
    $src  = Join-Path $Integrations 'aider\CONVENTIONS.md'
    $dest = Join-Path $PWD 'CONVENTIONS.md'
    if (-not (Test-Path $src)) { Write-Err "integrations/aider/CONVENTIONS.md missing. Run convert.sh first."; return }
    if (Test-Path $dest) { Write-Warn "Aider: CONVENTIONS.md already exists at $dest (remove to reinstall)."; return }
    Copy-Item $src -Destination $dest -Force
    Write-Ok "Aider: installed -> $dest"
}

function Install-Windsurf {
    $src  = Join-Path $Integrations 'windsurf\.windsurfrules'
    $dest = Join-Path $PWD '.windsurfrules'
    if (-not (Test-Path $src)) { Write-Err "integrations/windsurf/.windsurfrules missing. Run convert.sh first."; return }
    if (Test-Path $dest) { Write-Warn "Windsurf: .windsurfrules already exists at $dest (remove to reinstall)."; return }
    Copy-Item $src -Destination $dest -Force
    Write-Ok "Windsurf: installed -> $dest"
}

function Install-Tool {
    param([string]$ToolName)
    switch ($ToolName) {
        'claude-code' { Install-ClaudeCode }
        'copilot'     { Install-Copilot }
        'cursor'      { Install-Cursor }
        'aider'       { Install-Aider }
        'windsurf'    { Install-Windsurf }
        default       { Write-Warn "$ToolName: PowerShell installer not yet implemented. Use install.sh via WSL or Git Bash." }
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

if (-not (Test-Path $Integrations)) {
    Write-Err "integrations/ not found. Run ./scripts/convert.sh first (via WSL or Git Bash)."
    exit 1
}

Write-Header "The Agency -- Installing agents (PowerShell)"
Write-Host "  Repo:     $RepoRoot"
Write-Host "  Platform: Windows (PowerShell $($PSVersionTable.PSVersion))"
Write-Host ""

$selectedTools = @()
if ($Tool -eq 'all') {
    foreach ($t in $AllTools) {
        if (Test-ToolDetected $t) {
            $selectedTools += $t
            Write-Host "  [*]  $t  detected" -ForegroundColor Green
        } else {
            Write-Host "  [ ]  $t  not found" -ForegroundColor DarkGray
        }
    }
} else {
    $selectedTools = @($Tool)
}

if ($selectedTools.Count -eq 0) {
    Write-Warn "No tools selected or detected. Nothing to install."
    Write-Host "  Tip: use -Tool <name> to force-install a specific tool."
    exit 0
}

Write-Host ""
$installed = 0
foreach ($t in $selectedTools) {
    Install-Tool $t
    $installed++
}

Write-Host ""
Write-Ok "Done! Installed $installed tool(s)."
Write-Host ""
