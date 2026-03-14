# lint-agents.ps1 -- Validates agent markdown files.
#
# Usage: .\scripts\lint-agents.ps1 [file ...]
#   If no files given, scans all agent directories.

param (
    [string[]]$Files
)

$AgentDirs = @(
    "design", "engineering", "game-development", "marketing", "paid-media", "sales", "product", "project-management",
    "testing", "support", "spatial-computing", "specialized"
)

$RequiredFrontmatter = @("name", "description", "color")
$RecommendedSections = @("Identity", "Core Mission", "Critical Rules")

$Errors = 0
$Warnings = 0

function Lint-File {
    param([string]$FilePath)
    $Content = Get-Content $FilePath -Raw
    $Lines = $Content -split "`r?`n"
    
    # 1. Check frontmatter delimiters
    if ($Lines[0] -ne "---") {
        Write-Host "ERROR $($FilePath): missing frontmatter opening ---" -ForegroundColor Red
        $script:Errors++
        return
    }
    
    $FrontmatterEnd = -1
    for ($i = 1; $i -lt $Lines.Length; $i++) {
        if ($Lines[$i] -eq "---") {
            $FrontmatterEnd = $i
            break
        }
    }
    
    if ($FrontmatterEnd -eq -1) {
        Write-Host "ERROR $($FilePath): unclosed frontmatter" -ForegroundColor Red
        $script:Errors++
        return
    }
    
    $Frontmatter = ($Lines[1..($FrontmatterEnd - 1)] -join "`n")
    $Body = ($Lines[($FrontmatterEnd + 1)..($Lines.Length - 1)] -join "`n")
    
    # 2. Check required frontmatter fields
    foreach ($Field in $RequiredFrontmatter) {
        if ($Frontmatter -notmatch "(?m)^$($Field):") {
            Write-Host "ERROR $($FilePath): missing frontmatter field '$($Field)'" -ForegroundColor Red
            $script:Errors++
        }
    }
    
    # 3. Check recommended sections (warn only)
    foreach ($Section in $RecommendedSections) {
        if ($Body -notmatch "(?i)$($Section)") {
            Write-Host "WARN  $($FilePath): missing recommended section '$($Section)'" -ForegroundColor Yellow
            $script:Warnings++
        }
    }
    
    # 4. Check file has meaningful content
    $WordCount = ($Body -split "\s+").Length
    if ($WordCount -lt 50) {
        Write-Host "WARN  $($FilePath): body seems very short ($($WordCount) words)" -ForegroundColor Yellow
        $script:Warnings++
    }
}

$RepoRoot = Resolve-Path "$PSScriptRoot\.."

if (-not $Files) {
    $Files = @()
    foreach ($Dir in $AgentDirs) {
        $Path = Join-Path $RepoRoot $Dir
        if (Test-Path $Path) {
            $Files += (Get-ChildItem -Path $Path -Filter "*.md" -File -Recurse).FullName
        }
    }
}

Write-Host "Linting $($Files.Count) agent files..."

foreach ($F in $Files) {
    Lint-File $F
}

Write-Host "`nResults: $Errors error(s), $Warnings warning(s) in $($Files.Count) files."

if ($Errors -gt 0) {
    Write-Host "FAILED: fix the errors above before merging." -ForegroundColor Red
    exit 1
} else {
    Write-Host "PASSED" -ForegroundColor Green
    exit 0
}
