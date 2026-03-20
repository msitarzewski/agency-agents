[CmdletBinding()]
param(
  [string[]]$Paths,
  [Alias("h")]
  [switch]$Help
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

$AgentDirs = @(
  "academic",
  "design",
  "engineering",
  "game-development",
  "marketing",
  "paid-media",
  "product",
  "project-management",
  "testing",
  "support",
  "spatial-computing",
  "specialized"
)

$RequiredFrontmatter = @("name", "description", "color")
$RecommendedSections = @("Identity", "Core Mission", "Critical Rules")

$Script:ErrorCount = 0
$Script:WarningCount = 0

function Get-Usage {
  return @"
lint-agents.ps1 -- Validates agent markdown files.

Checks:
  1. YAML frontmatter exists with name, description, color (ERROR)
  2. Recommended sections are present (WARN)
  3. Body has meaningful content (WARN)

Usage:
  ./scripts/lint-agents.ps1 [-Paths <file...>] [-Help]

Examples:
  ./scripts/lint-agents.ps1
  ./scripts/lint-agents.ps1 -Paths engineering\engineering-frontend-developer.md
"@
}

function Write-ErrorMsg {
  param([string]$Message)
  Write-Host $Message -ForegroundColor Red
}

function Write-WarnMsg {
  param([string]$Message)
  Write-Host $Message -ForegroundColor Yellow
}

function Read-Utf8Lines {
  param([string]$Path)

  $utf8 = New-Object System.Text.UTF8Encoding($false)
  return [System.IO.File]::ReadAllLines($Path, $utf8)
}

function Get-FirstLine {
  param([string]$FilePath)

  $lines = Read-Utf8Lines -Path $FilePath
  if ($lines.Count -eq 0) {
    return ""
  }

  return $lines[0]
}

function Get-FrontmatterLines {
  param([string]$FilePath)

  $lines = Read-Utf8Lines -Path $FilePath
  if ($lines.Count -lt 3) {
    return @()
  }

  if ($lines[0] -ne "---") {
    return @()
  }

  $endIndex = -1
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq "---") {
      $endIndex = $i
      break
    }
  }

  if ($endIndex -lt 1) {
    return @()
  }

  if ($endIndex -eq 1) {
    return @()
  }

  return $lines[1..($endIndex - 1)]
}

function Get-BodyLines {
  param([string]$FilePath)

  $lines = Read-Utf8Lines -Path $FilePath
  if ($lines.Count -lt 3) {
    return @()
  }

  if ($lines[0] -ne "---") {
    return @()
  }

  $endIndex = -1
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq "---") {
      $endIndex = $i
      break
    }
  }

  if ($endIndex -lt 1) {
    return @()
  }

  if ($endIndex -ge $lines.Count - 1) {
    return @()
  }

  return $lines[($endIndex + 1)..($lines.Count - 1)]
}

function Increment-Error {
  param([string]$Message)
  Write-ErrorMsg -Message $Message
  $Script:ErrorCount++
}

function Increment-Warn {
  param([string]$Message)
  Write-WarnMsg -Message $Message
  $Script:WarningCount++
}

function Test-FrontmatterHasField {
  param(
    [string[]]$FrontmatterLines,
    [string]$Field
  )

  foreach ($line in $FrontmatterLines) {
    if ($line -match ("^" + [regex]::Escape($Field) + ":")) {
      return $true
    }
  }

  return $false
}

function Count-Words {
  param([string[]]$BodyLines)

  if ($null -eq $BodyLines -or $BodyLines.Count -eq 0) {
    return 0
  }

  $text = [string]::Join(" ", $BodyLines)
  $matches = [regex]::Matches($text, "\S+")
  return $matches.Count
}

function Test-BodyHasSection {
  param(
    [string[]]$BodyLines,
    [string]$Section
  )

  foreach ($line in $BodyLines) {
    if ($line -match [regex]::Escape($Section)) {
      return $true
    }
  }

  return $false
}

function Lint-File {
  param([string]$FilePath)

  $firstLine = Get-FirstLine -FilePath $FilePath
  if ($firstLine -ne "---") {
    Increment-Error -Message "ERROR ${FilePath}: missing frontmatter opening ---"
    return
  }

  $frontmatterLines = Get-FrontmatterLines -FilePath $FilePath
  if ($frontmatterLines.Count -eq 0) {
    Increment-Error -Message "ERROR ${FilePath}: empty or malformed frontmatter"
    return
  }

  foreach ($field in $RequiredFrontmatter) {
    if (-not (Test-FrontmatterHasField -FrontmatterLines $frontmatterLines -Field $field)) {
      Increment-Error -Message "ERROR ${FilePath}: missing frontmatter field '$field'"
    }
  }

  $bodyLines = Get-BodyLines -FilePath $FilePath
  foreach ($section in $RecommendedSections) {
    if (-not (Test-BodyHasSection -BodyLines $bodyLines -Section $section)) {
      Increment-Warn -Message "WARN  ${FilePath}: missing recommended section '$section'"
    }
  }

  $wordCount = Count-Words -BodyLines $bodyLines
  if ($wordCount -lt 50) {
    Increment-Warn -Message "WARN  ${FilePath}: body seems very short (< 50 words)"
  }
}

function Get-DefaultFiles {
  param([string]$RepoRoot)

  $files = New-Object System.Collections.Generic.List[string]

  foreach ($dir in $AgentDirs) {
    $dirPath = Join-Path $RepoRoot $dir
    if (-not (Test-Path -Path $dirPath -PathType Container)) {
      continue
    }

    $entries = Get-ChildItem -Path $dirPath -Filter "*.md" -File -Recurse | Sort-Object -Property FullName
    foreach ($entry in $entries) {
      $files.Add($entry.FullName)
    }
  }

  return $files.ToArray()
}

if ($Help) {
  Write-Output (Get-Usage)
  exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

$filesToLint = @()
if ($PSBoundParameters.ContainsKey("Paths") -and $Paths.Count -gt 0) {
  foreach ($path in $Paths) {
    $resolved = $path
    if (-not [System.IO.Path]::IsPathRooted($resolved)) {
      $resolved = Join-Path (Get-Location).Path $resolved
    }

    if (-not (Test-Path -Path $resolved -PathType Leaf)) {
      Increment-Error -Message "ERROR ${path}: file not found"
      continue
    }

    $filesToLint += (Resolve-Path -Path $resolved).Path
  }
}
else {
  $filesToLint = Get-DefaultFiles -RepoRoot $RepoRoot
}

if ($filesToLint.Count -eq 0) {
  Write-Host "No agent files found."
  exit 1
}

Write-Host ("Linting {0} agent files..." -f $filesToLint.Count)
Write-Host ""

foreach ($file in $filesToLint) {
  Lint-File -FilePath $file
}

Write-Host ""
Write-Host ("Results: {0} error(s), {1} warning(s) in {2} files." -f $Script:ErrorCount, $Script:WarningCount, $filesToLint.Count)

if ($Script:ErrorCount -gt 0) {
  Write-Host "FAILED: fix the errors above before merging."
  exit 1
}

Write-Host "PASSED"
exit 0
