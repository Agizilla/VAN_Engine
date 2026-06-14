# Install Algo context menu entries
# Run as Administrator: right-click PowerShell → Run as Administrator
# Then: .\install.ps1

$ExePath = "$PSScriptRoot\dist\algo.exe"

if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: $ExePath not found. Run build_exe.ps1 first." -ForegroundColor Red
    exit 1
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Must run as Administrator. Right-click PowerShell → Run as Administrator" -ForegroundColor Red
    exit 1
}

function Add-MenuEntry {
    param($Path, $Name, $Command, $Icon)
    $regPath = "HKCU:\Software\Classes\$Path\shell\$Name"
    $cmdPath = "$regPath\command"
    New-Item -Path $regPath -Force | Out-Null
    Set-ItemProperty -Path $regPath -Name "(Default)" -Value $Name
    if ($Icon) { Set-ItemProperty -Path $regPath -Name "Icon" -Value $Icon }
    New-Item -Path $cmdPath -Force | Out-Null
    Set-ItemProperty -Path $cmdPath -Name "(Default)" -Value $Command
    Write-Host "  ✓ $Name" -ForegroundColor Green
}

# ── 1. File context: Inject Algorithm ────────────────────────────────────────
Add-MenuEntry -Path "*" -Name "Inject Algorithm" -Command "`"$ExePath`" inject" -Icon "$ExePath,0"

# ── 2. .pyp file context ─────────────────────────────────────────────────────
Add-MenuEntry -Path ".pyp" -Name "Send to Clawdia (SAAS)" -Command "`"$ExePath`" pyp-send `"%1`"" -Icon "$ExePath,0"
Add-MenuEntry -Path ".pyp" -Name "Create Master Prompt" -Command "`"$ExePath`" prompt `"%1`" --copy" -Icon "$ExePath,0"

# ── 3. Folder context: Clawdia Tools (cascading submenu) ─────────────────────
$toolsPath = "HKCU:\Software\Classes\Directory\shell\ClawdiaTools"
New-Item -Path $toolsPath -Force | Out-Null
Set-ItemProperty -Path $toolsPath -Name "(Default)" -Value "Clawdia Tools"
Set-ItemProperty -Path $toolsPath -Name "Icon" -Value "$ExePath,0"
Set-ItemProperty -Path $toolsPath -Name "SubCommands" -Value ""
New-Item -Path "$toolsPath\shell" -Force | Out-Null

$folderTools = @(
    @{Name="Folder Stats"; Cmd="`"$ExePath`" stats `"%V`" --copy"},
    @{Name="Generate .pyp"; Cmd="`"$ExePath`" pyp `"%V`" --copy"},
    @{Name="Send to SAAS"; Cmd="`"$ExePath`" pyp-send `"%V`""},
    @{Name="Master Prompt from Folder"; Cmd="`"$ExePath`" pyp `"%V`" --copy"}
)

$i = 0
foreach ($tool in $folderTools) {
    $i++
    $key = "{0:D2}_{1}" -f $i, $tool.Name
    $subPath = "$toolsPath\shell\$key"
    $cmdPath = "$subPath\command"
    New-Item -Path $subPath -Force | Out-Null
    Set-ItemProperty -Path $subPath -Name "(Default)" -Value $tool.Name
    New-Item -Path $cmdPath -Force | Out-Null
    Set-ItemProperty -Path $cmdPath -Name "(Default)" -Value $tool.Cmd
    Write-Host "  ✓ Folder: $($tool.Name)" -ForegroundColor Green
}

# ── 4. Send To: Clawdia (folder → pyp → SAAS) ───────────────────────────────
$sendToPath = [Environment]::GetFolderPath("SendTo")
$shortcutPath = Join-Path $sendToPath "Clawdia (Send to SAAS).url"
@"
[InternetShortcut]
URL=file:///$ExePath
"@ | Out-File -FilePath $shortcutPath -Encoding default

Write-Host ""
Write-Host "✓ All context menu entries installed." -ForegroundColor Green
Write-Host ""
Write-Host "  File right-click  → Inject Algorithm" -ForegroundColor Cyan
Write-Host "  .pyp right-click  → Send to Clawdia / Create Master Prompt" -ForegroundColor Cyan
Write-Host "  Folder right-click → Clawdia Tools (Stats / .pyp / SAAS)" -ForegroundColor Cyan
Write-Host "  Send To menu      → Clawdia (Send to SAAS)" -ForegroundColor Cyan
