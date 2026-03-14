<#
.SYNOPSIS
Convert agency agent .md files into tool-specific formats.

.DESCRIPTION
Reads all agent files from the standard category directories and outputs
converted files to integrations/<tool>/. Run this to regenerate all
integration files after adding or modifying agents.

.PARAMETER Tool
The target tool to convert for (e.g., antigravity, gemini-cli, opencode, cursor, aider, windsurf, openclaw, qwen, all)

.PARAMETER Out
The output directory. Defaults to <repo-root>/integrations.
#>

param(
    [string]$Tool = "all",
    [string]$Out = ""
)

$ErrorActionPreference = 'Stop'

# --- Colour helpers ---
function Write-Info([string]$Message) { Write-Host "[OK]  $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "[!!]  $Message" -ForegroundColor Yellow }
function Write-ErrorMsg([string]$Message) { Write-Host "[ERR] $Message" -ForegroundColor Red }
function Write-Header([string]$Message) { Write-Host "`n$Message" -ForegroundColor Cyan }

# --- Paths ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) { $ScriptDir = $PWD.Path }
$RepoRoot = Split-Path -Parent $ScriptDir
if ([string]::IsNullOrWhiteSpace($Out)) {
    $OutDir = Join-Path $RepoRoot "integrations"
} else {
    $OutDir = $Out
}
$Today = (Get-Date).ToString("yyyy-MM-dd")

$AgentDirs = @(
    "design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management",
    "testing", "support", "spatial-computing", "specialized"
)

# --- File writing helpers ---
function Set-Utf8Content {
    param([string]$Path, [string]$Content)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Content + "`n", $utf8NoBom)
}

function Append-Utf8Content {
    param([string]$Path, [string]$Content)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::AppendAllText($Path, $Content + "`n", $utf8NoBom)
}

# --- Frontmatter helpers ---

function Get-Frontmatter {
    param([string]$FilePath)
    $lines = [System.IO.File]::ReadAllLines($FilePath)
    $fm = @{}
    $inFm = $false
    $fmCount = 0
    foreach ($line in $lines) {
        if ($line -eq '---') {
            $fmCount++
            if ($fmCount -eq 2) { break }
            $inFm = $true
            continue
        }
        if ($inFm -and $line -match "^([^:]+):\s*(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim()
            if ($val -match "^'(.*)'$") { $val = $Matches[1] }
            elseif ($val -match '^"(.*)"$') { $val = $Matches[1] }
            $fm[$key] = $val
        }
    }
    return $fm
}

function Get-Body {
    param([string]$FilePath)
    $lines = [System.IO.File]::ReadAllLines($FilePath)
    $body = New-Object System.Collections.Generic.List[string]
    $fm = 0
    foreach ($line in $lines) {
        if ($line -eq '---') {
            $fm++
            if ($fm -eq 1 -or $fm -eq 2) { continue }
        }
        if ($fm -ge 2) {
            $body.Add($line)
        }
    }
    return $body -join "`n"
}

function Convert-Slugify {
    param([string]$Text)
    $Text = $Text.ToLower()
    $Text = $Text -replace '[^a-z0-9]', '-'
    $Text = $Text -replace '-+', '-'
    $Text = $Text -replace '^-', ''
    $Text = $Text -replace '-$', ''
    return $Text
}

function Resolve-OpenCodeColor {
    param([string]$Color)
    if ([string]::IsNullOrWhiteSpace($Color)) { return "#6B7280" }
    $c = $Color.Trim().ToLower()
    $mapped = switch ($c) {
        "cyan" { "#00FFFF" }
        "blue" { "#3498DB" }
        "green" { "#2ECC71" }
        "red" { "#E74C3C" }
        "purple" { "#9B59B6" }
        "orange" { "#F39C12" }
        "teal" { "#008080" }
        "indigo" { "#6366F1" }
        "pink" { "#E84393" }
        "gold" { "#EAB308" }
        "amber" { "#F59E0B" }
        "neon-green" { "#10B981" }
        "neon-cyan" { "#06B6D4" }
        "metallic-blue" { "#3B82F6" }
        "yellow" { "#EAB308" }
        "violet" { "#8B5CF6" }
        "rose" { "#F43F5E" }
        "lime" { "#84CC16" }
        "gray" { "#6B7280" }
        "fuchsia" { "#D946EF" }
        default { $c }
    }
    if ($mapped -match "^#[0-9a-fA-F]{6}$") { return $mapped.ToUpper() }
    if ($mapped -match "^[0-9a-fA-F]{6}$") { return "#" + $mapped.ToUpper() }
    return "#6B7280"
}

function Convert-OpenClaw {
    param([hashtable]$Fm, [string]$Body, [string]$Slug)
    $outPath = Join-Path $OutDir "openclaw\$Slug"
    New-Item -ItemType Directory -Force -Path $outPath | Out-Null
    
    $soulContent = New-Object System.Text.StringBuilder
    $agentsContent = New-Object System.Text.StringBuilder
    $currentTarget = "agents"
    $currentSection = ""
    
    $lines = $Body -split "\r?\n"
    foreach ($line in $lines) {
        if ($line -match "^##\s") {
            if (![string]::IsNullOrEmpty($currentSection)) {
                if ($currentTarget -eq "soul") { [void]$soulContent.Append($currentSection) }
                else { [void]$agentsContent.Append($currentSection) }
            }
            $currentSection = ""
            
            $headerLower = $line.ToLower()
            if ($headerLower -match "identity" -or
                $headerLower -match "communication" -or
                $headerLower -match "style" -or
                $headerLower -match "critical rule" -or
                $headerLower -match "rules you must follow") {
                $currentTarget = "soul"
            } else {
                $currentTarget = "agents"
            }
        }
        $currentSection += "$line`n"
    }
    if (![string]::IsNullOrEmpty($currentSection)) {
        if ($currentTarget -eq "soul") { [void]$soulContent.Append($currentSection) }
        else { [void]$agentsContent.Append($currentSection) }
    }
    
    Set-Utf8Content -Path (Join-Path $outPath "SOUL.md") -Content $soulContent.ToString().TrimEnd()
    Set-Utf8Content -Path (Join-Path $outPath "AGENTS.md") -Content $agentsContent.ToString().TrimEnd()
    
    $emoji = $Fm["emoji"]
    $vibe = $Fm["vibe"]
    $name = $Fm["name"]
    $desc = $Fm["description"]
    
    if ($emoji -and $vibe) {
        $identity = "# $emoji $name`n$vibe"
    } else {
        $identity = "# $name`n$desc"
    }
    Set-Utf8Content -Path (Join-Path $outPath "IDENTITY.md") -Content $identity
}

# --- Main loop ---

$ValidTools = @("antigravity", "gemini-cli", "opencode", "cursor", "aider", "windsurf", "openclaw", "qwen", "all")
if ($ValidTools -notcontains $Tool) {
    Write-ErrorMsg "Unknown tool '$Tool'. Valid: $($ValidTools -join ' ')"
    exit 1
}

Write-Header "The Agency -- Converting agents to tool-specific formats"
Write-Host "  Repo:   $RepoRoot"
Write-Host "  Output: $OutDir"
Write-Host "  Tool:   $Tool"
Write-Host "  Date:   $Today"

$ToolsToRun = if ($Tool -eq "all") {
    @("antigravity", "gemini-cli", "opencode", "cursor", "aider", "windsurf", "openclaw", "qwen")
} else {
    @($Tool)
}

$AiderTmp = [System.IO.Path]::GetTempFileName()
$WindsurfTmp = [System.IO.Path]::GetTempFileName()

try {
    $AiderHeader = @"
# The Agency — AI Agent Conventions
#
# This file provides Aider with the full roster of specialized AI agents from
# The Agency (https://github.com/msitarzewski/agency-agents).
#
# To activate an agent, reference it by name in your Aider session prompt, e.g.:
#   "Use the Frontend Developer agent to review this component."
#
# Generated by scripts/convert.ps1 — do not edit manually.

"@
    Set-Utf8Content -Path $AiderTmp -Content $AiderHeader

    $WindsurfHeader = @"
# The Agency — AI Agent Rules for Windsurf
#
# Full roster of specialized AI agents from The Agency.
# To activate an agent, reference it by name in your Windsurf conversation.
#
# Generated by scripts/convert.ps1 — do not edit manually.

"@
    Set-Utf8Content -Path $WindsurfTmp -Content $WindsurfHeader

    $Total = 0

    foreach ($t in $ToolsToRun) {
        Write-Header "Converting: $t"
        $count = 0

        foreach ($dir in $AgentDirs) {
            $dirPath = Join-Path $RepoRoot $dir
            if (-not (Test-Path $dirPath)) { continue }

            $files = Get-ChildItem -Path $dirPath -Filter "*.md" -File | Sort-Object Name
            foreach ($file in $files) {
                $firstLine = Get-Content $file.FullName -TotalCount 1
                if ($firstLine -ne "---") { continue }

                $fm = Get-Frontmatter -FilePath $file.FullName
                if (-not $fm["name"]) { continue }

                $body = Get-Body -FilePath $file.FullName
                $slug = Convert-Slugify -Text $fm["name"]

                switch ($t) {
                    "antigravity" {
                        $outPath = Join-Path $OutDir "antigravity\agency-$slug"
                        New-Item -ItemType Directory -Force -Path $outPath | Out-Null
                        $content = @"
---
name: agency-$slug
description: $($fm['description'])
risk: low
source: community
date_added: '$Today'
---
$body
"@
                        Set-Utf8Content -Path (Join-Path $outPath "SKILL.md") -Content $content
                    }
                    "gemini-cli" {
                        $outPath = Join-Path $OutDir "gemini-cli\skills\$slug"
                        New-Item -ItemType Directory -Force -Path $outPath | Out-Null
                        $content = @"
---
name: $slug
description: $($fm['description'])
---
$body
"@
                        Set-Utf8Content -Path (Join-Path $outPath "SKILL.md") -Content $content
                    }
                    "opencode" {
                        $outPath = Join-Path $OutDir "opencode\agents"
                        New-Item -ItemType Directory -Force -Path $outPath | Out-Null
                        $color = Resolve-OpenCodeColor -Color $fm["color"]
                        $content = @"
---
name: $($fm['name'])
description: $($fm['description'])
mode: subagent
color: '$color'
---
$body
"@
                        Set-Utf8Content -Path (Join-Path $outPath "$slug.md") -Content $content
                    }
                    "cursor" {
                        $outPath = Join-Path $OutDir "cursor\rules"
                        New-Item -ItemType Directory -Force -Path $outPath | Out-Null
                        $content = @"
---
description: $($fm['description'])
globs: ""
alwaysApply: false
---
$body
"@
                        Set-Utf8Content -Path (Join-Path $outPath "$slug.mdc") -Content $content
                    }
                    "openclaw" {
                        Convert-OpenClaw -Fm $fm -Body $body -Slug $slug
                    }
                    "qwen" {
                        $outPath = Join-Path $OutDir "qwen\agents"
                        New-Item -ItemType Directory -Force -Path $outPath | Out-Null
                        if ($fm["tools"]) {
                            $content = @"
---
name: $slug
description: $($fm['description'])
tools: $($fm['tools'])
---
$body
"@
                        } else {
                            $content = @"
---
name: $slug
description: $($fm['description'])
---
$body
"@
                        }
                        Set-Utf8Content -Path (Join-Path $outPath "$slug.md") -Content $content
                    }
                    "aider" {
                        $content = @"

---

## $($fm['name'])

> $($fm['description'])

$body
"@
                        Append-Utf8Content -Path $AiderTmp -Content $content
                    }
                    "windsurf" {
                        $content = @"

================================================================================
## $($fm['name'])
$($fm['description'])
================================================================================

$body
"@
                        Append-Utf8Content -Path $WindsurfTmp -Content $content
                    }
                }
                $count++
            }
        }
        $Total += $count

        if ($t -eq "gemini-cli") {
            $geminiCliDir = Join-Path $OutDir "gemini-cli"
            New-Item -ItemType Directory -Force -Path $geminiCliDir | Out-Null
            $geminiExtJson = @"
{
  "name": "agency-agents",
  "version": "1.0.0"
}
"@
            Set-Utf8Content -Path (Join-Path $geminiCliDir "gemini-extension.json") -Content $geminiExtJson
            Write-Info "Wrote gemini-extension.json"
        }

        Write-Info "Converted $count agents for $t"
    }

    if ($Tool -eq "all" -or $Tool -eq "aider" -or $Tool -eq "windsurf") {
        if ($Tool -eq "all" -or $Tool -eq "aider") {
            $aiderDir = Join-Path $OutDir "aider"
            New-Item -ItemType Directory -Force -Path $aiderDir | Out-Null
            Copy-Item -Path $AiderTmp -Destination (Join-Path $aiderDir "CONVENTIONS.md") -Force
            Write-Info "Wrote integrations/aider/CONVENTIONS.md"
        }
        if ($Tool -eq "all" -or $Tool -eq "windsurf") {
            $windsurfDir = Join-Path $OutDir "windsurf"
            New-Item -ItemType Directory -Force -Path $windsurfDir | Out-Null
            Copy-Item -Path $WindsurfTmp -Destination (Join-Path $windsurfDir ".windsurfrules") -Force
            Write-Info "Wrote integrations/windsurf/.windsurfrules"
        }
    }

    Write-Host ""
    Write-Info "Done. Total conversions: $Total"

} finally {
    if (Test-Path $AiderTmp) { Remove-Item $AiderTmp -Force }
    if (Test-Path $WindsurfTmp) { Remove-Item $WindsurfTmp -Force }
}
