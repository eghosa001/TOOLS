# Ninefold Tide Windows 11 setup. Nothing is installed without -Install.
# Run in PowerShell from the repository: 
#   powershell -ExecutionPolicy Bypass -File video/ninefold_tide/setup-windows.ps1
#   powershell -ExecutionPolicy Bypass -File video/ninefold_tide/setup-windows.ps1 -Install
param([switch]$Install, [switch]$Optional)
$ErrorActionPreference = "Stop"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Error "Windows Package Manager (winget) is missing. Install App Installer from Microsoft Store."
  exit 2
}
$packages = @(
  @{ id="KDE.Krita"; title="Krita, hand-drawn production art" },
  @{ id="DWANGO.OpenToonz"; version="1.8.0"; title="OpenToonz, stable 2D animation" },
  @{ id="Audacity.Audacity"; title="Audacity, recording and sound" },
  @{ id="KDE.Kdenlive"; title="Kdenlive, shot-by-shot human edit" },
  @{ id="Gyan.FFmpeg"; title="FFmpeg / FFprobe, approved master export" }
)
if ($Optional) {
  $packages += @{ id="BlenderFoundation.Blender"; title="Blender, optional 3D sets" }
  $packages += @{ id="GodotEngine.GodotEngine"; title="Godot, optional 2D rigs" }
}
foreach ($package in $packages) {
  $name = $package.id
  $args = @("install", "--exact", "--id", $name, "--accept-package-agreements", "--accept-source-agreements")
  if ($package.ContainsKey("version")) {
    $args += @("--version", $package.version)
  }
  Write-Host ("Tool: {0} ({1})" -f $package.title, $name)
  if ($Install) {
    & winget @args
    if ($LASTEXITCODE -ne 0) { throw "winget installation failed for $name" }
  } else {
    Write-Host ("DRY RUN only. Would invoke: winget " + ($args -join " "))
  }
}
Write-Host "Open a fresh terminal after installation, then run:"
Write-Host "python video/ninefold_tide/pipeline.py doctor"
Write-Host "python video/ninefold_tide/pipeline.py init"
Write-Host "Review the official source if the pinned OpenToonz version is unavailable: https://opentoonz.github.io/e/"
Write-Host "Rhubarb/Piper remain optional, unapproved audio helpers. No voice models are downloaded automatically."
