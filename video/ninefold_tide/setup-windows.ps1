# Full toolbox. Safe dry run unless -Install is explicitly supplied.
# From repository root:
#   powershell -ExecutionPolicy Bypass -File video/ninefold_tide/setup-windows.ps1
#   powershell -ExecutionPolicy Bypass -File video/ninefold_tide/setup-windows.ps1 -Install
param([switch]$Install)
$ErrorActionPreference = "Stop"
$packages = @(
  @{ id="Python.Python.3.11"; role="Production Python 3.11" },
  @{ id="KDE.Krita"; role="Hand-drawn art and set painting" },
  @{ id="DWANGO.OpenToonz"; role="Traditional 2D acting and keyframe animation" },
  @{ id="BlenderFoundation.Blender"; role="3D staging and bridge/ferry camera layouts" },
  @{ id="GodotEngine.GodotEngine"; role="Reused 2D rig and scene test tools" },
  @{ id="Audacity.Audacity"; role="Human dialogue and sound recording" },
  @{ id="KDE.Kdenlive"; role="Human-edited timeline, look and sound review" },
  @{ id="Gyan.FFmpeg"; role="Final media encoding and inspection" }
)
Write-Host "The Ninefold Tide: COMPLETE no-paid-credits Windows production toolbox"
Write-Host "DRY RUN by default. -Install consents to the one-time software downloads."
Write-Host "These downloads can be large; use an affordable connection and re-use cached installers."
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  throw "Windows Package Manager is needed. Install the Microsoft App Installer first."
}
foreach ($p in $packages) {
  $args = @("install", "--exact", "--id", $p.id, "--accept-package-agreements", "--accept-source-agreements")
  Write-Host ("{0}: {1}" -f $p.role, $p.id)
  if ($Install) {
    & winget @args
    if ($LASTEXITCODE -ne 0) { throw "Could not install $($p.id); check available version, disk and network" }
  } else {
    Write-Host ("Would run: winget " + ($args -join " "))
  }
}

# One pinned official GitHub release, not arbitrary executable discovery.
$releaseApi = "https://api.github.com/repos/DanielSWolf/rhubarb-lip-sync/releases/tags/v1.14.0"
$toolRoot = Join-Path $env:LOCALAPPDATA "NinefoldTideTools"
$rhubarbDir = Join-Path $toolRoot "rhubarb"
$rhubarbExe = Join-Path $rhubarbDir "rhubarb.exe"
Write-Host "Rhubarb Lip Sync: $releaseApi"
if ($Install -and -not (Test-Path $rhubarbExe)) {
  New-Item -ItemType Directory -Force -Path $toolRoot | Out-Null
  $release = Invoke-RestMethod -Uri $releaseApi -Headers @{"Accept"="application/vnd.github+json"; "User-Agent"="Ninefold-Tide-Production"}
  $asset = $release.assets | Where-Object { $_.name -match '(?i)windows.*\.zip$' } | Select-Object -First 1
  if (-not $asset) { throw "No official Windows ZIP in pinned Rhubarb release; see the upstream releases page." }
  $zip = Join-Path $toolRoot $asset.name
  if (-not (Test-Path $zip)) { Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip }
  $digest = (Get-FileHash -Algorithm SHA256 -Path $zip).Hash.ToLowerInvariant()
  if ($asset.digest -and $asset.digest -match '^sha256:([a-fA-F0-9]{64})$') {
    if ($digest -ne $Matches[1].ToLowerInvariant()) { throw "Rhubarb archive checksum mismatch" }
  }
  $extract = Join-Path $toolRoot "rhubarb-unpack"
  Expand-Archive -Path $zip -DestinationPath $extract -Force
  $found = Get-ChildItem -Path $extract -Recurse -Filter rhubarb.exe | Select-Object -First 1
  if (-not $found) { throw "Official Rhubarb archive did not contain rhubarb.exe" }
  New-Item -ItemType Directory -Force -Path $rhubarbDir | Out-Null
  Copy-Item (Join-Path $found.DirectoryName "*") $rhubarbDir -Recurse -Force
  Set-Content -Path (Join-Path $rhubarbDir "archive-sha256.txt") -Value $digest
}
if (-not $Install) { Write-Host "Would install pinned official Rhubarb Lip Sync v1.14.0" }
if ($Install -and (Test-Path $rhubarbExe)) {
  $prior = [Environment]::GetEnvironmentVariable("PATH", "User")
  if (($prior -split ";") -notcontains $rhubarbDir) {
    [Environment]::SetEnvironmentVariable("PATH", "$prior;$rhubarbDir", "User")
  }
}

# Install only the local inference engine, never a synthetic voice model by default.
# Final voice choice requires full human-directed auditions and commercial-rights review.
$piperVenv = Join-Path $toolRoot "piper-venv"
Write-Host "Piper offline voice audition engine: $piperVenv"
if ($Install) {
  New-Item -ItemType Directory -Force -Path $toolRoot | Out-Null
  if (-not (Test-Path (Join-Path $piperVenv "Scripts\python.exe"))) {
    & py -3.11 -m venv $piperVenv
    if ($LASTEXITCODE -ne 0) { throw "Unable to initialize Piper Python 3.11 environment" }
  }
  $pythonExe = Join-Path $piperVenv "Scripts\python.exe"
  & $pythonExe -m pip show piper-tts *> $null
  if ($LASTEXITCODE -ne 0) {
    & $pythonExe -m pip install piper-tts
    if ($LASTEXITCODE -ne 0) { throw "Piper install failed" }
  }
} else {
  Write-Host "Would install Piper TTS engine to local private virtual environment (no voice download)"
}
Write-Host "IMPORTANT: Software installation alone is not an animation quality pass."
Write-Host "Run a NEW PowerShell terminal, then:"
Write-Host "  python video/ninefold_tide/pipeline.py doctor"
Write-Host "  python video/ninefold_tide/pipeline.py init"
Write-Host "  python -m unittest discover -s video/ninefold_tide/tests -v"
Write-Host "The first VIEWER-FACING film remains locked until full-quality art, acting and audio pass."
