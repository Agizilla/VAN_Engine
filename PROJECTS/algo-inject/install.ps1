# Install algo-inject context menu entry
# Run as Administrator: right-click PowerShell → Run as Administrator
# Then: .\install.ps1

$ExePath = "$PSScriptRoot\dist\algo-inject.exe"

if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: $ExePath not found. Run build_exe.ps1 first." -ForegroundColor Red
    exit 1
}

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Must run as Administrator. Right-click PowerShell → Run as Administrator" -ForegroundColor Red
    exit 1
}

$RegPath = "HKCU:\Software\Classes\*\shell\AlgoInject"
$CmdPath = "HKCU:\Software\Classes\*\shell\AlgoInject\command"

# Create context menu entry
New-Item -Path $RegPath -Force | Out-Null
Set-ItemProperty -Path $RegPath -Name "(Default)" -Value "Inject Algorithm"
Set-ItemProperty -Path $RegPath -Name "Icon" -Value "$ExePath,0"

New-Item -Path $CmdPath -Force | Out-Null
Set-ItemProperty -Path $CmdPath -Name "(Default)" -Value "`"$ExePath`""

Write-Host "✓ Context menu entry installed." -ForegroundColor Green
Write-Host "  Right-click any file → 'Inject Algorithm' to run." -ForegroundColor Green
Write-Host "  (Make sure you copy the prompt text to clipboard first.)" -ForegroundColor Yellow
