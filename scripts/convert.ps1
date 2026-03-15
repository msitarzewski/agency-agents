# convert.ps1 — Convert agency agent .md files into tool-specific formats.
#
# Reads all agent files from the standard category directories and outputs
# converted files to integrations/<tool>/. Run this to regenerate all
# integration files after adding or modifying agents.
#
# Usage:
#   .\scripts\convert.ps1 [-Tool <name>] [-Out <dir>] [-Help]

param (
    [string]$Tool = "all",
    [string]$Out,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\scripts\convert.ps1 [-Tool <name>] [-Out <dir>] [-Help]"
    Write-Host ""
    Write-Host "Tools: antigravity, gemini-cli, opencode, cursor, aider, windsurf, openclaw, qwen, all (default)"
    exit 0
}

$RepoRoot = Resolve-Path "$PSScriptRoot\.."
if (-not $Out) {
    $OutDir = Join-Path $RepoRoot "integrations"
} else {
    $OutDir = Resolve-Path $Out
}

$Today = Get-Date -Format "yyyy-MM-dd"

$AgentDirs = @(
    "design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management",
    "testing", "support", "spatial-computing", "specialized"
)

# --- Helpers ---

function Get-Field {
    param([string]$Field, [string]$Content)
    if ($Content -match "(?ms)^---`r?`n(.*?)^---") {
        $Frontmatter = $Matches[1]
        if ($Frontmatter -match "(?m)^$($Field):\s*(.*)") {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Get-Body {
    param([string]$Content)
    $Parts = $Content -split "(?m)^---`r?`n"
    if ($Parts.Length -ge 3) {
        return ($Parts[2..($Parts.Length-1)] -join "---`r`n").Trim()
    }
    return $null
}

function Slugify {
    param([string]$Name)
    $S = $Name.ToLower()
    $S = $S -replace '[^a-z0-9]', '-'
    $S = $S -replace '-+', '-'
    return $S.Trim('-')
}

function Resolve-OpenCode-Color {
    param([string]$C)
    $C = $C.Trim().ToLower()
    $Map = @{
        "cyan"           = "#00FFFF"
        "blue"           = "#3498DB"
        "green"          = "#2ECC71"
        "red"            = "#E74C3C"
        "purple"         = "#9B59B6"
        "orange"         = "#F39C12"
        "teal"           = "#008080"
        "indigo"         = "#6366F1"
        "pink"           = "#E84393"
        "gold"           = "#EAB308"
        "amber"          = "#F59E0B"
        "neon-green"     = "#10B981"
        "neon-cyan"      = "#06B6D4"
        "metallic-blue"  = "#3B82F6"
        "yellow"         = "#EAB308"
        "violet"         = "#8B5CF6"
        "rose"           = "#F43F5E"
        "lime"           = "#84CC16"
        "gray"           = "#6B7280"
        "fuchsia"        = "#D946EF"
    }
    if ($Map.ContainsKey($C)) { return $Map[$C] }
    if ($C -match "^#?[0-9a-f]{6}$") {
        if (-not $C.StartsWith("#")) { return "#" + $C.ToUpper() }
        return $C.ToUpper()
    }
    return "#6B7280"
}

# --- Converters ---

function Convert-Antigravity {
    param($File, $Content)
    $Name = Get-Field "name" $Content
    $Description = Get-Field "description" $Content
    $Slug = "agency-" + (Slugify $Name)
    $Body = Get-Body $Content
    
    $TargetDir = Join-Path $OutDir "antigravity\$Slug"
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }
    
    $OutFile = Join-Path $TargetDir "SKILL.md"
    $Header = @"
---
name: $Slug
description: $Description
risk: low
source: community
date_added: '$Today'
---
"@
    $FullContent = $Header + "`r`n" + $Body
    [System.IO.File]::WriteAllText($OutFile, $FullContent, (New-Object System.Text.UTF8Encoding $false))
}

function Convert-GeminiCLI {
    param($File, $Content)
    $Name = Get-Field "name" $Content
    $Description = Get-Field "description" $Content
    $Slug = Slugify $Name
    $Body = Get-Body $Content
    
    $TargetDir = Join-Path $OutDir "gemini-cli\skills\$Slug"
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }
    
    $OutFile = Join-Path $TargetDir "SKILL.md"
    $Header = @"
---
name: $Slug
description: $Description
---
"@
    $FullContent = $Header + "`r`n" + $Body
    [System.IO.File]::WriteAllText($OutFile, $FullContent, (New-Object System.Text.UTF8Encoding $false))
}

function Convert-OpenCode {
    param($File, $Content)
    $Name = Get-Field "name" $Content
    $Description = Get-Field "description" $Content
    $Color = Resolve-OpenCode-Color (Get-Field "color" $Content)
    $Slug = Slugify $Name
    $Body = Get-Body $Content
    
    $TargetDir = Join-Path $OutDir "opencode\agents"
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }
    
    $OutFile = Join-Path $TargetDir "$Slug.md"
    $Header = @"
---
name: $Name
description: $Description
mode: subagent
color: '$Color'
---
"@
    $FullContent = $Header + "`r`n" + $Body
    [System.IO.File]::WriteAllText($OutFile, $FullContent, (New-Object System.Text.UTF8Encoding $false))
}

function Convert-Cursor {
    param($File, $Content)
    $Name = Get-Field "name" $Content
    $Description = Get-Field "description" $Content
    $Slug = Slugify $Name
    $Body = Get-Body $Content
    
    $TargetDir = Join-Path $OutDir "cursor\rules"
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }
    
    $OutFile = Join-Path $TargetDir "$Slug.mdc"
    $Header = @"
---
description: $Description
globs: ""
alwaysApply: false
---
"@
    $FullContent = $Header + "`r`n" + $Body
    [System.IO.File]::WriteAllText($OutFile, $FullContent, (New-Object System.Text.UTF8Encoding $false))
}

function Convert-OpenClaw {
    param($File, $Content)
    $Name = Get-Field "name" $Content
    $Description = Get-Field "description" $Content
    $Slug = Slugify $Name
    $Body = Get-Body $Content
    
    $TargetDir = Join-Path $OutDir "openclaw\$Slug"
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }
    
    $SoulContent = ""
    $AgentsContent = ""
    $CurrentTarget = "agents"
    
    $Lines = $Body -split "`r?`n"
    foreach ($Line in $Lines) {
        if ($Line -match "^##\s") {
            $H = $Line.ToLower()
            if ($H -match "identity" -or $H -match "communication" -or $H -match "style" -or $H -match "critical rule" -or $H -match "rules you must follow") {
                $CurrentTarget = "soul"
            } else {
                $CurrentTarget = "agents"
            }
        }
        if ($CurrentTarget -eq "soul") { $SoulContent += $Line + "`r`n" }
        else { $AgentsContent += $Line + "`r`n" }
    }
    
    [System.IO.File]::WriteAllText((Join-Path $TargetDir "SOUL.md"), $SoulContent, (New-Object System.Text.UTF8Encoding $false))
    [System.IO.File]::WriteAllText((Join-Path $TargetDir "AGENTS.md"), $AgentsContent, (New-Object System.Text.UTF8Encoding $false))
    
    $Emoji = Get-Field "emoji" $Content
    $Vibe = Get-Field "vibe" $Content
    
    if ($Emoji -and $Vibe) {
        [System.IO.File]::WriteAllText((Join-Path $TargetDir "IDENTITY.md"), "# $Emoji $Name`r`n$Vibe", (New-Object System.Text.UTF8Encoding $false))
    } else {
        [System.IO.File]::WriteAllText((Join-Path $TargetDir "IDENTITY.md"), "# $Name`r`n$Description", (New-Object System.Text.UTF8Encoding $false))
    }
}

function Convert-Qwen {
    param($File, $Content)
    $Name = Get-Field "name" $Content
    $Description = Get-Field "description" $Content
    $Tools = Get-Field "tools" $Content
    $Slug = Slugify $Name
    $Body = Get-Body $Content
    
    $TargetDir = Join-Path $OutDir "qwen\agents"
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }
    
    $OutFile = Join-Path $TargetDir "$Slug.md"
    if ($Tools) {
        $Header = @"
---
name: $Slug
description: $Description
tools: $Tools
---
"@
    } else {
        $Header = @"
---
name: $Slug
description: $Description
---
"@
    }
    $FullContent = $Header + "`r`n" + $Body
    [System.IO.File]::WriteAllText($OutFile, $FullContent, (New-Object System.Text.UTF8Encoding $false))
}

# --- Main ---

Write-Host "`nThe Agency -- Converting agents to tool-specific formats (PowerShell)"
Write-Host "  Repo:   $RepoRoot"
Write-Host "  Output: $OutDir"
Write-Host "  Tool:   $Tool"
Write-Host "  Date:   $Today"

$AiderHeader = "# The Agency - AI Agent Conventions`r`n#`r`n# Generated by scripts/convert.ps1 - do not edit manually.`r`n`r`n"
$AiderContent = $AiderHeader
$WindsurfHeader = "# The Agency - AI Agent Rules for Windsurf`r`n#`r`n# Generated by scripts/convert.ps1 - do not edit manually.`r`n`r`n"
$WindsurfContent = $WindsurfHeader

$Total = 0
$ToolsToRun = if ($Tool -eq "all") { @("antigravity", "gemini-cli", "opencode", "cursor", "aider", "windsurf", "openclaw", "qwen") } else { @($Tool) }

foreach ($T in $ToolsToRun) {
    Write-Host "`nConverting: $T"
    $Count = 0
    foreach ($Dir in $AgentDirs) {
        $Path = Join-Path $RepoRoot $Dir
        if (-not (Test-Path $Path)) { continue }
        
        $Files = Get-ChildItem -Path $Path -Filter "*.md" -File
        foreach ($F in $Files) {
            $Content = Get-Content -Path $F.FullName -Raw -Encoding UTF8
            if (-not $Content.StartsWith("---")) { continue }
            
            $Name = Get-Field "name" $Content
            if (-not $Name) { continue }
            
            switch ($T) {
                "antigravity" { Convert-Antigravity $F $Content }
                "gemini-cli"  { Convert-GeminiCLI $F $Content }
                "opencode"    { Convert-OpenCode $F $Content }
                "cursor"      { Convert-Cursor $F $Content }
                "openclaw"    { Convert-OpenClaw $F $Content }
                "qwen"        { Convert-Qwen $F $Content }
                "aider" {
                    $Desc = Get-Field "description" $Content
                    $Body = Get-Body $Content
                    $AiderContent += "`r`n---`r`n`r`n## $Name`r`n`r`n> $Desc`r`n`r`n$Body`r`n"
                }
                "windsurf" {
                    $Desc = Get-Field "description" $Content
                    $Body = Get-Body $Content
                    $WindsurfContent += "`r`n================================================================================`r`n## $Name`r`n$Desc`r`n================================================================================`r`n`r`n$Body`r`n"
                }
            }
            $Count++
        }
    }
    
    if ($T -eq "gemini-cli") {
        $ManifestDir = Join-Path $OutDir "gemini-cli"
        if (-not (Test-Path $ManifestDir)) { New-Item -ItemType Directory -Path $ManifestDir -Force }
        [System.IO.File]::WriteAllText((Join-Path $ManifestDir "gemini-extension.json"), '{"name": "agency-agents", "version": "1.0.0"}', (New-Object System.Text.UTF8Encoding $false))
    }
    
    if ($T -eq "aider") {
        $AiderDir = Join-Path $OutDir "aider"
        if (-not (Test-Path $AiderDir)) { New-Item -ItemType Directory -Path $AiderDir -Force }
        [System.IO.File]::WriteAllText((Join-Path $AiderDir "CONVENTIONS.md"), $AiderContent, (New-Object System.Text.UTF8Encoding $false))
    }

    if ($T -eq "windsurf") {
        $WindsurfDir = Join-Path $OutDir "windsurf"
        if (-not (Test-Path $WindsurfDir)) { New-Item -ItemType Directory -Path $WindsurfDir -Force }
        [System.IO.File]::WriteAllText((Join-Path $WindsurfDir ".windsurfrules"), $WindsurfContent, (New-Object System.Text.UTF8Encoding $false))
    }

    Write-Host "  Converted $Count agents for $T"
    $Total += $Count
}

Write-Host "`nDone. Total conversions: $Total"
