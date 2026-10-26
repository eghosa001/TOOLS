# Download MIT-licensed YouTube research projects into the current Windows user's app-data folder.
# This script does NOT run the downloaded code, grant YouTube access, or register an MCP connection.
param(
    [string]$Destination = (Join-Path $env:LOCALAPPDATA "TOOLS-YouTube-Research")
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required. Install Git for Windows before running this script."
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

$projects = @(
    @{ Name = "youtube-niche-finder"; Url = "https://github.com/pandich93/youtube-niche-finder.git" },
    @{ Name = "youtube-marketing-skills"; Url = "https://github.com/adityaarsharma/youtube-marketing-skills.git" }
)

foreach ($project in $projects) {
    $target = Join-Path $Destination $project.Name
    if (Test-Path (Join-Path $target ".git")) {
        Write-Host "Already present: $target (skipping; not overwriting or updating)"
        continue
    }
    if (Test-Path $target) {
        throw "Destination already exists but is not a Git clone: $target. Review it manually."
    }

    Write-Host "Cloning $($project.Name) ..."
    & git clone --depth 1 $project.Url $target
    if ($LASTEXITCODE -ne 0) {
        throw "Clone failed for $($project.Name); check network and Git configuration."
    }
}

Write-Host ""
Write-Host "Open-source project sources are saved under $Destination"
Write-Host "NEXT: Follow .agents/skills/youtube-growth-research/SETUP.md to configure Google API credentials and start the tools."
Write-Host "No MCP connection, Docker service or Google authorization has been configured by this script."
