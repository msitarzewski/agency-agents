param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$DestDir = (Join-Path $HOME ".gemini/antigravity/skills"),
    [switch]$DryRun
)

if ($DryRun) {
    Write-Host "--- DRY RUN MODE ACTIVE ---" -ForegroundColor Yellow
}


$IntegrationsDir = Join-Path $RepoRoot "integrations\antigravity"
$Today = Get-Date -Format "yyyy-MM-dd"

$AgentDirs = @(
    "academic", "design", "engineering", "game-development", "marketing", 
    "paid-media", "sales", "product", "project-management", 
    "testing", "support", "spatial-computing", "specialized", "strategy"
)

if ($IntegrationsDir -and -not (Test-Path $IntegrationsDir)) {
    if ($DryRun) { Write-Host "[DryRun] Would create directory: $IntegrationsDir" }
    else { New-Item -ItemType Directory -Path $IntegrationsDir -Force | Out-Null }
}

if ($DestDir -and -not (Test-Path $DestDir)) {
    if ($DryRun) { Write-Host "[DryRun] Would create directory: $DestDir" }
    else { New-Item -ItemType Directory -Path $DestDir -Force | Out-Null }
}


function Slugify($Name) {
    $Slug = $Name.ToLower() -replace '[^a-z0-9]', '-'
    $Slug = $Slug -replace '-+', '-'
    $Slug = $Slug.Trim('-')
    return "agency-$Slug"
}

$Count = 0

foreach ($Dir in $AgentDirs) {
    $DirPath = Join-Path $RepoRoot $Dir
    if (-not (Test-Path $DirPath)) { continue }

    $Files = Get-ChildItem -Path $DirPath -Filter "*.md"
    foreach ($File in $Files) {
        $Content = Get-Content -Path $File.FullName -Raw
        if ($Content -match "^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$") {
            $FrontMatter = $Matches[1]
            $Body = $Matches[2]

            $Name = ""
            $Description = ""

            if ($FrontMatter -match "name:\s*(.*)") { $Name = $Matches[1].Trim() }
            if ($FrontMatter -match "description:\s*(.*)") { $Description = $Matches[1].Trim() }

            if ($Name -eq "") { continue }

            $Slug = Slugify $Name
            $SkillDir = Join-Path $IntegrationsDir $Slug
            if (-not (Test-Path $SkillDir)) {
                if ($DryRun) { Write-Host "[DryRun] Would create directory: $SkillDir" }
                else { New-Item -ItemType Directory -Path $SkillDir -Force | Out-Null }
            }

            $NewContent = @"
---
name: $Slug
description: $Description
risk: low
source: community
date_added: '$Today'
---
$Body
"@
            $OutFile = Join-Path $SkillDir "SKILL.md"
            
            if ($DryRun) {
                Write-Host "[DryRun] Would write converted skill to: $OutFile"
            }
            else {
                Set-Content -Path $OutFile -Value $NewContent -Encoding utf8
            }

            # Install to Antigravity skills dir
            $InstallDir = Join-Path $DestDir $Slug
            if (-not (Test-Path $InstallDir)) {
                if ($DryRun) { Write-Host "[DryRun] Would create directory: $InstallDir" }
                else { New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null }
            }
            
            if ($DryRun) {
                Write-Host "[DryRun] Would copy skill to installation path: $(Join-Path $InstallDir "SKILL.md")"
            }
            else {
                Copy-Item -Path $OutFile -Destination (Join-Path $InstallDir "SKILL.md") -Force
            }


            $Count++
        }
    }
}

if ($DryRun) {
    Write-Host "Dry run complete. Found $Count agents to convert."
}
else {
    Write-Host "Successfully converted and installed $Count agents as Antigravity skills."
    Write-Host "Skills installed to: $DestDir"
}

