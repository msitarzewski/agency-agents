[CmdletBinding()]
param(
  [string]$Tool = "all",
  [string]$Out,
  [Alias("h")]
  [switch]$Help
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

$AgentDirs = @(
  "academic", "design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management",
  "testing", "support", "spatial-computing", "specialized"
)

$ValidTools = @("antigravity", "gemini-cli", "opencode", "cursor", "aider", "windsurf", "openclaw", "qwen", "all")
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$OutDir = if ($PSBoundParameters.ContainsKey("Out")) { $Out } else { Join-Path $RepoRoot "integrations" }
$Today = Get-Date -Format "yyyy-MM-dd"

$Script:AiderAccumulator = New-Object System.Text.StringBuilder
$Script:WindsurfAccumulator = New-Object System.Text.StringBuilder

function Get-Usage {
  return @"
convert.ps1 -- Convert agency agent .md files into tool-specific formats.

Reads all agent files from the standard category directories and outputs
converted files to integrations/<tool>/.

Usage:
  ./scripts/convert.ps1 [-Tool <name>] [-Out <dir>] [-Help]

Tools:
  antigravity  -- Antigravity skill files (~/.gemini/antigravity/skills/)
  gemini-cli   -- Gemini CLI extension (skills/ + gemini-extension.json)
  opencode     -- OpenCode agent files (.opencode/agents/*.md)
  cursor       -- Cursor rule files (.cursor/rules/*.mdc)
  aider        -- Single CONVENTIONS.md for Aider
  windsurf     -- Single .windsurfrules for Windsurf
  openclaw     -- OpenClaw SOUL.md files (openclaw_workspace/<agent>/SOUL.md)
  qwen         -- Qwen Code SubAgent files (~/.qwen/agents/*.md)
  all          -- All tools (default)
"@
}

function Write-Info {
  param([string]$Message)
  Write-Host "[OK]  $Message" -ForegroundColor Green
}

function Write-WarnMsg {
  param([string]$Message)
  Write-Host "[!!]  $Message" -ForegroundColor Yellow
}

function Write-ErrMsg {
  param([string]$Message)
  Write-Host "[ERR] $Message" -ForegroundColor Red
}

function Write-Header {
  param([string]$Message)
  Write-Host ""
  Write-Host $Message
}

function Ensure-Directory {
  param([string]$Path)

  if (-not (Test-Path -Path $Path -PathType Container)) {
    $null = New-Item -ItemType Directory -Path $Path -Force
  }
}

function Write-Utf8File {
  param(
    [string]$Path,
    [string]$Content
  )

  $parent = Split-Path -Parent $Path
  if (-not [string]::IsNullOrWhiteSpace($parent)) {
    Ensure-Directory -Path $parent
  }

  if (-not $Content.EndsWith("`n")) {
    $Content += "`n"
  }

  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Write-ToolArtifact {
  param(
    [string]$RelativePath,
    [string]$Content
  )

  $outPath = Join-Path $OutDir $RelativePath
  Write-Utf8File -Path $outPath -Content $Content
}

function Read-Utf8Lines {
  param([string]$Path)

  $utf8 = New-Object System.Text.UTF8Encoding($false)
  return [System.IO.File]::ReadAllLines($Path, $utf8)
}

function Join-Lines {
  param([string[]]$Lines)

  if ($null -eq $Lines -or $Lines.Count -eq 0) {
    return ""
  }

  return [string]::Join("`n", $Lines)
}

function Get-AgentRecord {
  param([string]$FilePath)

  $lines = Read-Utf8Lines -Path $FilePath
  if ($lines.Count -lt 3) {
    return $null
  }

  if ($lines[0] -ne "---") {
    return $null
  }

  $endFrontmatter = -1
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq "---") {
      $endFrontmatter = $i
      break
    }
  }

  if ($endFrontmatter -lt 1) {
    return $null
  }

  $frontmatterLines = @()
  if ($endFrontmatter -gt 1) {
    $frontmatterLines = $lines[1..($endFrontmatter - 1)]
  }

  $bodyLines = @()
  if ($endFrontmatter + 1 -le $lines.Count - 1) {
    $bodyLines = $lines[($endFrontmatter + 1)..($lines.Count - 1)]
  }

  $fields = @{}
  foreach ($line in $frontmatterLines) {
    if ($line -match '^\s*([A-Za-z0-9_-]+):\s*(.*)\s*$') {
      $key = $matches[1].ToLowerInvariant()
      if (-not $fields.ContainsKey($key)) {
        $fields[$key] = $matches[2].Trim()
      }
    }
  }

  $name = if ($fields.ContainsKey("name")) { $fields["name"] } else { "" }
  if ([string]::IsNullOrWhiteSpace($name)) {
    return $null
  }

  $description = if ($fields.ContainsKey("description")) { $fields["description"] } else { "" }
  $color = if ($fields.ContainsKey("color")) { $fields["color"] } else { "" }
  $tools = if ($fields.ContainsKey("tools")) { $fields["tools"] } else { "" }
  $emoji = if ($fields.ContainsKey("emoji")) { $fields["emoji"] } else { "" }
  $vibe = if ($fields.ContainsKey("vibe")) { $fields["vibe"] } else { "" }

  return [pscustomobject]@{
    Path = $FilePath
    Name = $name
    Description = $description
    Color = $color
    Tools = $tools
    Emoji = $emoji
    Vibe = $vibe
    BodyLines = $bodyLines
    Body = (Join-Lines -Lines $bodyLines)
  }
}

function Slugify {
  param([string]$Value)

  $slug = $Value.ToLowerInvariant()
  $slug = [regex]::Replace($slug, "[^a-z0-9]", "-")
  $slug = [regex]::Replace($slug, "-+", "-")
  $slug = $slug.Trim('-')
  return $slug
}

function Resolve-OpenCodeColor {
  param([string]$Color)

  $normalized = if ($null -eq $Color) { "" } else { $Color.Trim().ToLowerInvariant() }

  $namedMap = @{
    "cyan" = "#00FFFF"
    "blue" = "#3498DB"
    "green" = "#2ECC71"
    "red" = "#E74C3C"
    "purple" = "#9B59B6"
    "orange" = "#F39C12"
    "teal" = "#008080"
    "indigo" = "#6366F1"
    "pink" = "#E84393"
    "gold" = "#EAB308"
    "amber" = "#F59E0B"
    "neon-green" = "#10B981"
    "neon-cyan" = "#06B6D4"
    "metallic-blue" = "#3B82F6"
    "yellow" = "#EAB308"
    "violet" = "#8B5CF6"
    "rose" = "#F43F5E"
    "lime" = "#84CC16"
    "gray" = "#6B7280"
    "fuchsia" = "#D946EF"
  }

  $mapped = if ($namedMap.ContainsKey($normalized)) { $namedMap[$normalized] } else { $normalized }

  if ($mapped -match '^#[0-9a-fA-F]{6}$') {
    return ("#{0}" -f $mapped.Substring(1).ToUpperInvariant())
  }

  if ($mapped -match '^[0-9a-fA-F]{6}$') {
    return ("#{0}" -f $mapped.ToUpperInvariant())
  }

  return "#6B7280"
}

function Initialize-Accumulators {
  $Script:AiderAccumulator.Clear() | Out-Null
  $Script:WindsurfAccumulator.Clear() | Out-Null

  $aiderHeader = @"
# The Agency -- AI Agent Conventions
#
# This file provides Aider with the full roster of specialized AI agents from
# The Agency (https://github.com/msitarzewski/agency-agents).
#
# To activate an agent, reference it by name in your Aider session prompt, e.g.:
#   "Use the Frontend Developer agent to review this component."
#
# Generated by scripts/convert.ps1 -- do not edit manually.
"@

  $windsurfHeader = @"
# The Agency -- AI Agent Rules for Windsurf
#
# Full roster of specialized AI agents from The Agency.
# To activate an agent, reference it by name in your Windsurf conversation.
#
# Generated by scripts/convert.ps1 -- do not edit manually.
"@

  [void]$Script:AiderAccumulator.AppendLine($aiderHeader)
  [void]$Script:WindsurfAccumulator.AppendLine($windsurfHeader)
}

function Convert-Antigravity {
  param([pscustomobject]$Agent)

  $slug = "agency-$(Slugify -Value $Agent.Name)"
  $relativePath = Join-Path (Join-Path "antigravity" $slug) "SKILL.md"

  $content = @"
---
name: $slug
description: $($Agent.Description)
risk: low
source: community
date_added: '$Today'
---
$($Agent.Body)
"@

  Write-ToolArtifact -RelativePath $relativePath -Content $content
}

function Convert-GeminiCli {
  param([pscustomobject]$Agent)

  $slug = Slugify -Value $Agent.Name
  $relativePath = Join-Path (Join-Path (Join-Path "gemini-cli" "skills") $slug) "SKILL.md"

  $content = @"
---
name: $slug
description: $($Agent.Description)
---
$($Agent.Body)
"@

  Write-ToolArtifact -RelativePath $relativePath -Content $content
}

function Convert-OpenCode {
  param([pscustomobject]$Agent)

  $slug = Slugify -Value $Agent.Name
  $color = Resolve-OpenCodeColor -Color $Agent.Color
  $relativePath = Join-Path (Join-Path "opencode" "agents") "$slug.md"

  $content = @"
---
name: $($Agent.Name)
description: $($Agent.Description)
mode: subagent
color: '$color'
---
$($Agent.Body)
"@

  Write-ToolArtifact -RelativePath $relativePath -Content $content
}

function Convert-Cursor {
  param([pscustomobject]$Agent)

  $slug = Slugify -Value $Agent.Name
  $relativePath = Join-Path (Join-Path "cursor" "rules") "$slug.mdc"

  $content = @"
---
description: $($Agent.Description)
globs: ""
alwaysApply: false
---
$($Agent.Body)
"@

  Write-ToolArtifact -RelativePath $relativePath -Content $content
}

function Split-OpenClawBody {
  param([string[]]$BodyLines)

  $soul = New-Object System.Text.StringBuilder
  $agents = New-Object System.Text.StringBuilder
  $currentTarget = "agents"
  $currentSection = New-Object System.Collections.Generic.List[string]

  $flushSection = {
    if ($currentSection.Count -eq 0) {
      return
    }

    $sectionText = [string]::Join("`n", $currentSection) + "`n"
    if ($currentTarget -eq "soul") {
      [void]$soul.Append($sectionText)
    }
    else {
      [void]$agents.Append($sectionText)
    }

    $currentSection.Clear()
  }

  foreach ($line in $BodyLines) {
    if ($line -match '^##\s') {
      & $flushSection

      $headerLower = $line.ToLowerInvariant()
      if (
        $headerLower -match 'identity' -or
        $headerLower -match 'communication' -or
        $headerLower -match 'style' -or
        $headerLower -match 'critical.rule' -or
        $headerLower -match 'rules.you.must.follow'
      ) {
        $currentTarget = "soul"
      }
      else {
        $currentTarget = "agents"
      }
    }

    [void]$currentSection.Add($line)
  }

  & $flushSection

  return [pscustomobject]@{
    Soul = $soul.ToString()
    Agents = $agents.ToString()
  }
}

function Convert-OpenClaw {
  param([pscustomobject]$Agent)

  $slug = Slugify -Value $Agent.Name
  $outDir = Join-Path (Join-Path $OutDir "openclaw") $slug
  Ensure-Directory -Path $outDir

  $split = Split-OpenClawBody -BodyLines $Agent.BodyLines
  Write-Utf8File -Path (Join-Path $outDir "SOUL.md") -Content $split.Soul
  Write-Utf8File -Path (Join-Path $outDir "AGENTS.md") -Content $split.Agents

  $identity = ""
  if (-not [string]::IsNullOrWhiteSpace($Agent.Emoji) -and -not [string]::IsNullOrWhiteSpace($Agent.Vibe)) {
    $identity = @"
# $($Agent.Emoji) $($Agent.Name)
$($Agent.Vibe)
"@
  }
  else {
    $identity = @"
# $($Agent.Name)
$($Agent.Description)
"@
  }

  Write-Utf8File -Path (Join-Path $outDir "IDENTITY.md") -Content $identity
}

function Convert-Qwen {
  param([pscustomobject]$Agent)

  $slug = Slugify -Value $Agent.Name
  $relativePath = Join-Path (Join-Path "qwen" "agents") "$slug.md"

  if (-not [string]::IsNullOrWhiteSpace($Agent.Tools)) {
    $content = @"
---
name: $slug
description: $($Agent.Description)
tools: $($Agent.Tools)
---
$($Agent.Body)
"@
  }
  else {
    $content = @"
---
name: $slug
description: $($Agent.Description)
---
$($Agent.Body)
"@
  }

  Write-ToolArtifact -RelativePath $relativePath -Content $content
}

function Accumulate-Aider {
  param([pscustomobject]$Agent)

  $segment = @"

---

## $($Agent.Name)

> $($Agent.Description)

$($Agent.Body)
"@

  [void]$Script:AiderAccumulator.AppendLine($segment)
}

function Accumulate-Windsurf {
  param([pscustomobject]$Agent)

  $segment = @"

================================================================================
## $($Agent.Name)
$($Agent.Description)
================================================================================

$($Agent.Body)
"@

  [void]$Script:WindsurfAccumulator.AppendLine($segment)
}

function Get-AgentFilesInDir {
  param([string]$DirectoryPath)

  if (-not (Test-Path -Path $DirectoryPath -PathType Container)) {
    return @()
  }

  return Get-ChildItem -Path $DirectoryPath -Filter "*.md" -File -Recurse | Sort-Object -Property FullName
}

function Run-Conversions {
  param([string]$TargetTool)

  $count = 0

  foreach ($dir in $AgentDirs) {
    $dirPath = Join-Path $RepoRoot $dir
    $files = Get-AgentFilesInDir -DirectoryPath $dirPath

    foreach ($file in $files) {
      $agent = Get-AgentRecord -FilePath $file.FullName
      if ($null -eq $agent) {
        continue
      }

      switch ($TargetTool) {
        "antigravity" { Convert-Antigravity -Agent $agent; break }
        "gemini-cli" { Convert-GeminiCli -Agent $agent; break }
        "opencode" { Convert-OpenCode -Agent $agent; break }
        "cursor" { Convert-Cursor -Agent $agent; break }
        "openclaw" { Convert-OpenClaw -Agent $agent; break }
        "qwen" { Convert-Qwen -Agent $agent; break }
        "aider" { Accumulate-Aider -Agent $agent; break }
        "windsurf" { Accumulate-Windsurf -Agent $agent; break }
      }

      $count++
    }
  }

  return $count
}

function Write-GeminiManifest {
  $manifest = @'
{
  "name": "agency-agents",
  "version": "1.0.0"
}
'@
  Write-ToolArtifact -RelativePath (Join-Path "gemini-cli" "gemini-extension.json") -Content $manifest
}

function Write-SingleFileOutputs {
  Write-ToolArtifact -RelativePath (Join-Path "aider" "CONVENTIONS.md") -Content $Script:AiderAccumulator.ToString()
  Write-ToolArtifact -RelativePath (Join-Path "windsurf" ".windsurfrules") -Content $Script:WindsurfAccumulator.ToString()
}

if ($Help) {
  Write-Output (Get-Usage)
  exit 0
}

$Tool = $Tool.ToLowerInvariant()
if (-not ($ValidTools -contains $Tool)) {
  Write-ErrMsg "Unknown tool '$Tool'. Valid: $($ValidTools -join ' ')"
  exit 1
}

Initialize-Accumulators

Write-Header "The Agency -- Converting agents to tool-specific formats"
Write-Host ("  Repo:   {0}" -f $RepoRoot)
Write-Host ("  Output: {0}" -f $OutDir)
Write-Host ("  Tool:   {0}" -f $Tool)
Write-Host ("  Date:   {0}" -f $Today)

$toolsToRun = @()
if ($Tool -eq "all") {
  $toolsToRun = @("antigravity", "gemini-cli", "opencode", "cursor", "aider", "windsurf", "openclaw", "qwen")
}
else {
  $toolsToRun = @($Tool)
}

$total = 0
foreach ($targetTool in $toolsToRun) {
  Write-Header "Converting: $targetTool"
  $count = Run-Conversions -TargetTool $targetTool
  $total += [int]$count

  if ($targetTool -eq "gemini-cli") {
    Write-GeminiManifest
    Write-Info "Wrote gemini-extension.json"
  }

  Write-Info "Converted $count agents for $targetTool"
}

if ($Tool -eq "all" -or $Tool -eq "aider" -or $Tool -eq "windsurf") {
  Write-SingleFileOutputs
  Write-Info "Wrote integrations/aider/CONVENTIONS.md"
  Write-Info "Wrote integrations/windsurf/.windsurfrules"
}

Write-Host ""
Write-Info "Done. Total conversions: $total"
