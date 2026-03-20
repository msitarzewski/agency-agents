[CmdletBinding()]
param(
  [string]$Tool = "all",
  [switch]$Interactive,
  [Alias("no-interactive")]
  [switch]$NoInteractive,
  [Alias("h")]
  [switch]$Help
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

$AllTools = @("claude-code", "copilot", "antigravity", "gemini-cli", "opencode", "openclaw", "cursor", "aider", "windsurf", "qwen")
$AgentDirs = @(
  "academic", "design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management",
  "testing", "support", "spatial-computing", "specialized"
)

function Get-Usage {
  return @"
install.ps1 -- Install The Agency agents into your local agentic tool(s).

Reads converted files from integrations/ and copies them to the appropriate
config directory for each tool.

Usage:
  ./scripts/install.ps1 [-Tool <name>] [-Interactive] [-NoInteractive] [-Help]

Tools:
  claude-code  -- Copy agents to ~/.claude/agents/
  copilot      -- Copy agents to ~/.github/agents/ and ~/.copilot/agents/
  antigravity  -- Copy skills to ~/.gemini/antigravity/skills/
  gemini-cli   -- Install extension to ~/.gemini/extensions/agency-agents/
  opencode     -- Copy agents to .opencode/agents/ in current directory
  cursor       -- Copy rules to .cursor/rules/ in current directory
  aider        -- Copy CONVENTIONS.md to current directory
  windsurf     -- Copy .windsurfrules to current directory
  openclaw     -- Copy workspaces to ~/.openclaw/agency-agents/
  qwen         -- Copy SubAgents to .qwen/agents/ in current directory
  all          -- Install for all detected tools (default)
"@
}

function Write-Ok {
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

function Test-CommandAvailable {
  param([string]$Name)
  return $null -ne (Get-Command -Name $Name -ErrorAction SilentlyContinue)
}

function Get-ToolLabel {
  param([string]$ToolName)

  switch ($ToolName) {
    "claude-code" { return "Claude Code    (~/.claude/agents)" }
    "copilot" { return "Copilot        (~/.github + ~/.copilot)" }
    "antigravity" { return "Antigravity    (~/.gemini/antigravity)" }
    "gemini-cli" { return "Gemini CLI     (~/.gemini/extensions)" }
    "opencode" { return "OpenCode       (.opencode/agents)" }
    "openclaw" { return "OpenClaw       (~/.openclaw)" }
    "cursor" { return "Cursor         (.cursor/rules)" }
    "aider" { return "Aider          (CONVENTIONS.md)" }
    "windsurf" { return "Windsurf       (.windsurfrules)" }
    "qwen" { return "Qwen Code      (.qwen/agents)" }
    default { return $ToolName }
  }
}

function Test-ToolDetected {
  param([string]$ToolName)

  switch ($ToolName) {
    "claude-code" { return (Test-Path -Path (Join-Path $HOME ".claude") -PathType Container) }
    "copilot" {
      return (Test-CommandAvailable "code") -or
        (Test-Path -Path (Join-Path $HOME ".github") -PathType Container) -or
        (Test-Path -Path (Join-Path $HOME ".copilot") -PathType Container)
    }
    "antigravity" {
      $path = Join-Path (Join-Path (Join-Path $HOME ".gemini") "antigravity") "skills"
      return (Test-Path -Path $path -PathType Container)
    }
    "gemini-cli" { return (Test-CommandAvailable "gemini") -or (Test-Path -Path (Join-Path $HOME ".gemini") -PathType Container) }
    "opencode" { return (Test-CommandAvailable "opencode") -or (Test-Path -Path (Join-Path (Join-Path $HOME ".config") "opencode") -PathType Container) }
    "openclaw" { return (Test-CommandAvailable "openclaw") -or (Test-Path -Path (Join-Path $HOME ".openclaw") -PathType Container) }
    "cursor" { return (Test-CommandAvailable "cursor") -or (Test-Path -Path (Join-Path $HOME ".cursor") -PathType Container) }
    "aider" { return (Test-CommandAvailable "aider") }
    "windsurf" { return (Test-CommandAvailable "windsurf") -or (Test-Path -Path (Join-Path $HOME ".codeium") -PathType Container) }
    "qwen" { return (Test-CommandAvailable "qwen") -or (Test-Path -Path (Join-Path $HOME ".qwen") -PathType Container) }
    default { return $false }
  }
}

function Ensure-Directory {
  param([string]$Path)

  if (-not (Test-Path -Path $Path -PathType Container)) {
    $null = New-Item -ItemType Directory -Path $Path -Force
  }
}

function Copy-FlatFiles {
  param(
    [string]$Source,
    [string]$Filter,
    [string]$Destination
  )

  Ensure-Directory -Path $Destination

  $count = 0
  $files = Get-ChildItem -Path $Source -Filter $Filter -File | Sort-Object -Property Name
  foreach ($file in $files) {
    Copy-Item -Path $file.FullName -Destination $Destination -Force
    $count++
  }

  return $count
}

function Install-SingleProjectFile {
  param(
    [string]$Source,
    [string]$MissingMessage,
    [string]$Destination,
    [string]$ExistsWarning,
    [string]$SuccessMessage,
    [string]$ScopeWarning
  )

  if (-not (Test-Path -Path $Source -PathType Leaf)) {
    throw $MissingMessage
  }

  if (Test-Path -Path $Destination -PathType Leaf) {
    Write-WarnMsg $ExistsWarning
    return
  }

  Copy-Item -Path $Source -Destination $Destination -Force
  Write-Ok $SuccessMessage
  Write-WarnMsg $ScopeWarning
}

function Read-Utf8FirstLine {
  param([string]$Path)

  $utf8 = New-Object System.Text.UTF8Encoding($false)
  $reader = [System.IO.StreamReader]::new($Path, $utf8)
  try {
    return $reader.ReadLine()
  }
  finally {
    $reader.Dispose()
  }
}

function Get-AgentFiles {
  param([string]$RepoRoot)

  $result = New-Object System.Collections.Generic.List[string]

  foreach ($dir in $AgentDirs) {
    $dirPath = Join-Path $RepoRoot $dir
    if (-not (Test-Path -Path $dirPath -PathType Container)) {
      continue
    }

    $files = Get-ChildItem -Path $dirPath -Filter "*.md" -File -Recurse | Sort-Object -Property FullName
    foreach ($file in $files) {
      $firstLine = Read-Utf8FirstLine -Path $file.FullName
      if ($firstLine -eq "---") {
        $result.Add($file.FullName)
      }
    }
  }

  return $result.ToArray()
}

function Copy-AgentMarkdown {
  param(
    [string]$RepoRoot,
    [string]$Destination
  )

  Ensure-Directory -Path $Destination
  $count = 0
  $files = Get-AgentFiles -RepoRoot $RepoRoot

  foreach ($file in $files) {
    Copy-Item -Path $file -Destination $Destination -Force
    $count++
  }

  return $count
}

function Select-ToolsInteractive {
  param([string[]]$Tools)

  $selected = @{}
  $detected = @{}

  foreach ($toolName in $Tools) {
    $isDetected = Test-ToolDetected -ToolName $toolName
    $selected[$toolName] = $isDetected
    $detected[$toolName] = $isDetected
  }

  while ($true) {
    Write-Host ""
    Write-Host "The Agency -- Tool Installer"
    Write-Host "System scan: [*] = detected on this machine"
    Write-Host ""

    for ($i = 0; $i -lt $Tools.Count; $i++) {
      $toolName = $Tools[$i]
      $checked = if ($selected[$toolName]) { "[x]" } else { "[ ]" }
      $scan = if ($detected[$toolName]) { "[*]" } else { "[ ]" }
      $label = Get-ToolLabel -ToolName $toolName
      Write-Host ("  {0} {1,2}) {2} {3}" -f $checked, ($i + 1), $scan, $label)
    }

    Write-Host ""
    Write-Host ("  [1-{0}] toggle   [a] all   [n] none   [d] detected" -f $Tools.Count)
    Write-Host "  [Enter] install   [q] quit"
    $selectionInput = Read-Host ">>"
    $selectionInput = $selectionInput.Trim()

    if ($selectionInput -eq "") {
      $hasAny = $false
      foreach ($toolName in $Tools) {
        if ($selected[$toolName]) {
          $hasAny = $true
          break
        }
      }

      if ($hasAny) {
        break
      }

      Write-WarnMsg "Nothing selected -- pick a tool or press q to quit."
      continue
    }

    switch -Regex ($selectionInput.ToLowerInvariant()) {
      "^q$" {
        Write-Host ""
        Write-Ok "Aborted."
        exit 0
      }
      "^a$" {
        foreach ($toolName in $Tools) {
          $selected[$toolName] = $true
        }
        continue
      }
      "^n$" {
        foreach ($toolName in $Tools) {
          $selected[$toolName] = $false
        }
        continue
      }
      "^d$" {
        foreach ($toolName in $Tools) {
          $selected[$toolName] = $detected[$toolName]
        }
        continue
      }
      default {
        $tokens = $selectionInput -split "[ ,\t]+" | Where-Object { $_ -ne "" }
        $toggled = $false

        foreach ($token in $tokens) {
          $num = 0
          if ([int]::TryParse($token, [ref]$num)) {
            $idx = $num - 1
            if ($idx -ge 0 -and $idx -lt $Tools.Count) {
              $targetTool = $Tools[$idx]
              $selected[$targetTool] = -not $selected[$targetTool]
              $toggled = $true
            }
          }
        }

        if (-not $toggled) {
          Write-ErrMsg ("Invalid input. Enter a number 1-{0}, or a command." -f $Tools.Count)
        }
      }
    }
  }

  $chosen = New-Object System.Collections.Generic.List[string]
  foreach ($toolName in $Tools) {
    if ($selected[$toolName]) {
      $chosen.Add($toolName)
    }
  }

  return $chosen.ToArray()
}

function Install-ClaudeCode {
  param([string]$RepoRoot)

  $dest = Join-Path (Join-Path $HOME ".claude") "agents"
  $count = Copy-AgentMarkdown -RepoRoot $RepoRoot -Destination $dest
  Write-Ok "Claude Code: $count agents -> $dest"
}

function Install-Copilot {
  param([string]$RepoRoot)

  $destGithub = Join-Path (Join-Path $HOME ".github") "agents"
  $destCopilot = Join-Path (Join-Path $HOME ".copilot") "agents"

  $count = Copy-AgentMarkdown -RepoRoot $RepoRoot -Destination $destGithub
  Ensure-Directory -Path $destCopilot
  $files = Get-AgentFiles -RepoRoot $RepoRoot
  foreach ($file in $files) {
    Copy-Item -Path $file -Destination $destCopilot -Force
  }

  Write-Ok "Copilot: $count agents -> $destGithub"
  Write-Ok "Copilot: $count agents -> $destCopilot"
}

function Install-Antigravity {
  param([string]$Integrations)

  $src = Join-Path $Integrations "antigravity"
  if (-not (Test-Path -Path $src -PathType Container)) {
    throw "integrations/antigravity missing. Run convert.sh or convert.ps1 first."
  }

  $dest = Join-Path (Join-Path (Join-Path $HOME ".gemini") "antigravity") "skills"
  Ensure-Directory -Path $dest

  $count = 0
  $folders = Get-ChildItem -Path $src -Directory | Sort-Object -Property Name
  foreach ($folder in $folders) {
    $target = Join-Path $dest $folder.Name
    Ensure-Directory -Path $target

    $skillPath = Join-Path $folder.FullName "SKILL.md"
    if (-not (Test-Path -Path $skillPath -PathType Leaf)) {
      throw "Missing expected file: $skillPath"
    }

    Copy-Item -Path $skillPath -Destination (Join-Path $target "SKILL.md") -Force
    $count++
  }

  Write-Ok "Antigravity: $count skills -> $dest"
}

function Install-GeminiCli {
  param([string]$Integrations)

  $src = Join-Path $Integrations "gemini-cli"
  if (-not (Test-Path -Path $src -PathType Container)) {
    throw "integrations/gemini-cli missing. Run convert.sh or convert.ps1 first."
  }

  $dest = Join-Path (Join-Path (Join-Path $HOME ".gemini") "extensions") "agency-agents"
  Ensure-Directory -Path (Join-Path $dest "skills")

  $manifest = Join-Path $src "gemini-extension.json"
  if (-not (Test-Path -Path $manifest -PathType Leaf)) {
    throw "Missing expected file: $manifest"
  }
  Copy-Item -Path $manifest -Destination (Join-Path $dest "gemini-extension.json") -Force

  $skillsRoot = Join-Path $src "skills"
  if (-not (Test-Path -Path $skillsRoot -PathType Container)) {
    throw "Missing expected directory: $skillsRoot"
  }

  $count = 0
  $skillDirs = Get-ChildItem -Path $skillsRoot -Directory | Sort-Object -Property Name
  foreach ($skillDir in $skillDirs) {
    $target = Join-Path (Join-Path $dest "skills") $skillDir.Name
    Ensure-Directory -Path $target

    $skillPath = Join-Path $skillDir.FullName "SKILL.md"
    if (-not (Test-Path -Path $skillPath -PathType Leaf)) {
      throw "Missing expected file: $skillPath"
    }

    Copy-Item -Path $skillPath -Destination (Join-Path $target "SKILL.md") -Force
    $count++
  }

  Write-Ok "Gemini CLI: $count skills -> $dest"
}

function Install-OpenCode {
  param([string]$Integrations)

  $src = Join-Path (Join-Path $Integrations "opencode") "agents"
  if (-not (Test-Path -Path $src -PathType Container)) {
    throw "integrations/opencode missing. Run convert.sh or convert.ps1 first."
  }

  $dest = Join-Path (Get-Location).Path ".opencode\agents"
  $count = Copy-FlatFiles -Source $src -Filter "*.md" -Destination $dest

  Write-Ok "OpenCode: $count agents -> $dest"
  Write-WarnMsg "OpenCode: project-scoped. Run from your project root to install there."
}

function Install-OpenClaw {
  param([string]$Integrations)

  $src = Join-Path $Integrations "openclaw"
  if (-not (Test-Path -Path $src -PathType Container)) {
    throw "integrations/openclaw missing. Run convert.sh or convert.ps1 first."
  }

  $dest = Join-Path (Join-Path $HOME ".openclaw") "agency-agents"
  Ensure-Directory -Path $dest

  $count = 0
  $openclawInstalled = Test-CommandAvailable -Name "openclaw"
  $dirs = Get-ChildItem -Path $src -Directory | Sort-Object -Property Name

  foreach ($dir in $dirs) {
    $workspace = Join-Path $dest $dir.Name
    Ensure-Directory -Path $workspace

    foreach ($name in @("SOUL.md", "AGENTS.md", "IDENTITY.md")) {
      $from = Join-Path $dir.FullName $name
      if (-not (Test-Path -Path $from -PathType Leaf)) {
        throw "Missing expected file: $from"
      }
      Copy-Item -Path $from -Destination (Join-Path $workspace $name) -Force
    }

    if ($openclawInstalled) {
      try {
        & openclaw agents add $dir.Name --workspace $workspace --non-interactive | Out-Null
      }
      catch {
      }
    }

    $count++
  }

  Write-Ok "OpenClaw: $count workspaces -> $dest"
  if ($openclawInstalled) {
    Write-WarnMsg "OpenClaw: run 'openclaw gateway restart' to activate new agents"
  }
}

function Install-Cursor {
  param([string]$Integrations)

  $src = Join-Path (Join-Path $Integrations "cursor") "rules"
  if (-not (Test-Path -Path $src -PathType Container)) {
    throw "integrations/cursor missing. Run convert.sh or convert.ps1 first."
  }

  $dest = Join-Path (Get-Location).Path ".cursor\rules"
  $count = Copy-FlatFiles -Source $src -Filter "*.mdc" -Destination $dest

  Write-Ok "Cursor: $count rules -> $dest"
  Write-WarnMsg "Cursor: project-scoped. Run from your project root to install there."
}

function Install-Aider {
  param([string]$Integrations)

  $src = Join-Path (Join-Path $Integrations "aider") "CONVENTIONS.md"
  $dest = Join-Path (Get-Location).Path "CONVENTIONS.md"
  Install-SingleProjectFile `
    -Source $src `
    -MissingMessage "integrations/aider/CONVENTIONS.md missing. Run convert.sh or convert.ps1 first." `
    -Destination $dest `
    -ExistsWarning "Aider: CONVENTIONS.md already exists at $dest (remove to reinstall)." `
    -SuccessMessage "Aider: installed -> $dest" `
    -ScopeWarning "Aider: project-scoped. Run from your project root to install there."
}

function Install-Windsurf {
  param([string]$Integrations)

  $src = Join-Path (Join-Path $Integrations "windsurf") ".windsurfrules"
  $dest = Join-Path (Get-Location).Path ".windsurfrules"
  Install-SingleProjectFile `
    -Source $src `
    -MissingMessage "integrations/windsurf/.windsurfrules missing. Run convert.sh or convert.ps1 first." `
    -Destination $dest `
    -ExistsWarning "Windsurf: .windsurfrules already exists at $dest (remove to reinstall)." `
    -SuccessMessage "Windsurf: installed -> $dest" `
    -ScopeWarning "Windsurf: project-scoped. Run from your project root to install there."
}

function Install-Qwen {
  param([string]$Integrations)

  $src = Join-Path (Join-Path $Integrations "qwen") "agents"
  if (-not (Test-Path -Path $src -PathType Container)) {
    throw "integrations/qwen missing. Run convert.sh or convert.ps1 first."
  }

  $dest = Join-Path (Get-Location).Path ".qwen\agents"
  $count = Copy-FlatFiles -Source $src -Filter "*.md" -Destination $dest

  Write-Ok "Qwen Code: installed $count agents to $dest"
  Write-WarnMsg "Qwen Code: project-scoped. Run from your project root to install there."
  Write-WarnMsg "Tip: Run '/agents manage' in Qwen Code to refresh, or restart session"
}

function Install-Tool {
  param(
    [string]$ToolName,
    [string]$RepoRoot,
    [string]$Integrations
  )

  switch ($ToolName) {
    "claude-code" { Install-ClaudeCode -RepoRoot $RepoRoot; return }
    "copilot" { Install-Copilot -RepoRoot $RepoRoot; return }
    "antigravity" { Install-Antigravity -Integrations $Integrations; return }
    "gemini-cli" { Install-GeminiCli -Integrations $Integrations; return }
    "opencode" { Install-OpenCode -Integrations $Integrations; return }
    "openclaw" { Install-OpenClaw -Integrations $Integrations; return }
    "cursor" { Install-Cursor -Integrations $Integrations; return }
    "aider" { Install-Aider -Integrations $Integrations; return }
    "windsurf" { Install-Windsurf -Integrations $Integrations; return }
    "qwen" { Install-Qwen -Integrations $Integrations; return }
    default { throw "Unknown tool '$ToolName'" }
  }
}

if ($Help) {
  Write-Output (Get-Usage)
  exit 0
}

if ($Interactive -and $NoInteractive) {
  Write-ErrMsg "Choose either -Interactive or -NoInteractive, not both."
  exit 1
}

$Tool = $Tool.ToLowerInvariant()
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Integrations = Join-Path $RepoRoot "integrations"

if (-not (Test-Path -Path $Integrations -PathType Container)) {
  Write-ErrMsg "integrations/ not found. Run ./scripts/convert.sh or ./scripts/convert.ps1 first."
  exit 1
}

if ($Tool -ne "all" -and -not ($AllTools -contains $Tool)) {
  Write-ErrMsg "Unknown tool '$Tool'. Valid: $($AllTools -join ' ')"
  exit 1
}

$interactiveMode = "auto"
if ($Interactive) {
  $interactiveMode = "yes"
}
elseif ($NoInteractive) {
  $interactiveMode = "no"
}

$useInteractive = $false
$canPrompt = [Environment]::UserInteractive -and -not [Console]::IsInputRedirected -and -not [Console]::IsOutputRedirected

if ($interactiveMode -eq "yes") {
  $useInteractive = $true
}
elseif ($interactiveMode -eq "auto" -and $Tool -eq "all" -and $canPrompt) {
  $useInteractive = $true
}

$selectedTools = New-Object System.Collections.Generic.List[string]

if ($useInteractive) {
  $choices = Select-ToolsInteractive -Tools $AllTools
  foreach ($choice in $choices) {
    $selectedTools.Add($choice)
  }
}
elseif ($Tool -ne "all") {
  $selectedTools.Add($Tool)
}
else {
  Write-Header "The Agency -- Scanning for installed tools..."
  Write-Host ""

  foreach ($toolName in $AllTools) {
    $detected = Test-ToolDetected -ToolName $toolName
    if ($detected) {
      $selectedTools.Add($toolName)
      Write-Host ("  [*]  {0}  detected" -f (Get-ToolLabel -ToolName $toolName))
    }
    else {
      Write-Host ("  [ ]  {0}  not found" -f (Get-ToolLabel -ToolName $toolName))
    }
  }
}

if ($selectedTools.Count -eq 0) {
  Write-WarnMsg "No tools selected or detected. Nothing to install."
  Write-Host ""
  Write-Host "Tip: use -Tool <name> to force-install a specific tool."
  Write-Host "Available: $($AllTools -join ' ')"
  exit 0
}

Write-Header "The Agency -- Installing agents"
Write-Host ("  Repo:       {0}" -f $RepoRoot)
Write-Host ("  Installing: {0}" -f ($selectedTools -join " "))
Write-Host ""

$installed = 0
foreach ($toolName in $selectedTools) {
  try {
    Install-Tool -ToolName $toolName -RepoRoot $RepoRoot -Integrations $Integrations
    $installed++
  }
  catch {
    Write-ErrMsg "$toolName install failed: $($_.Exception.Message)"
    exit 1
  }
}

Write-Host ""
Write-Ok "Done! Installed $installed tool(s)."
Write-Host ""
Write-Host "Run ./scripts/convert.sh (or .\scripts\convert.ps1) to regenerate after adding or editing agents."
Write-Host ""
