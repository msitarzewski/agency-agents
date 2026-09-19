param(
    [string[]]$TargetDirs = @(
        "$env:USERPROFILE\.github\agents",
        "$env:USERPROFILE\.copilot\agents"
    )
)

$mapFile = Join-Path $PSScriptRoot "agent-names-zh.json"
$map = Get-Content $mapFile -Raw -Encoding UTF8 | ConvertFrom-Json

$totalUpdated = 0
foreach ($dir in $TargetDirs) {
    if (-not (Test-Path $dir)) { Write-Warning "Skip (not found): $dir"; continue }
    $files = Get-ChildItem "$dir\*.md" -ErrorAction SilentlyContinue
    $updated = 0
    foreach ($f in $files) {
        $raw = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
        if (-not $raw.StartsWith("---")) { continue }
        $endIdx = $raw.IndexOf("---", 3)
        if ($endIdx -lt 0) { continue }
        $yaml = $raw.Substring(3, $endIdx - 3)
        if (-not ($yaml -match "(?m)^name:\s*(.+)$")) { continue }
        $currentName = $Matches[1].Trim()
        $entry = $map.$currentName
        if (-not $entry) { continue }
        $newYaml = $yaml -replace "(?m)^name:\s*.+$", "name: $($entry.name)"
        if ($newYaml -match "(?m)^description:") {
            $newYaml = $newYaml -replace "(?m)^description:\s*.+$", "description: $($entry.description)"
        }
        $newContent = "---" + $newYaml + "---" + $raw.Substring($endIdx + 3)
        [System.IO.File]::WriteAllText($f.FullName, $newContent, [System.Text.Encoding]::UTF8)
        $updated++
    }
    Write-Host "OK: $updated agents localized -> $dir"
    $totalUpdated += $updated
}
Write-Host "Total: $totalUpdated agent files updated."
Write-Host "Reload VS Code window (Ctrl+Shift+P -> Reload Window) to apply."