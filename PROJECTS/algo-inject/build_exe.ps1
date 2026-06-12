$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $ProjectDir "..\..\ClawDia\.venv"
$Python = Join-Path $Venv "Scripts\python.exe"

Write-Host "=== Installing dependencies ==="
& $Python -m pip install pyperclip win10toast pyinstaller -q

Write-Host "=== Building algo-inject.exe ==="
& $Python -m PyInstaller --onefile --noconsole `
    --add-data "Algorithm.txt;." `
    --name "algo-inject" `
    --distpath "$ProjectDir\dist" `
    --workpath "$ProjectDir\build" `
    --specpath "$ProjectDir" `
    "$ProjectDir\algo_inject.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Build OK: $ProjectDir\dist\algo-inject.exe ==="
    Remove-Item "$ProjectDir\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$ProjectDir\algo-inject.spec" -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "=== BUILD FAILED ==="
    exit 1
}
