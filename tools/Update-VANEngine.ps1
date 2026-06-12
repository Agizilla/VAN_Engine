# Update-VANEngine.ps1
param(
    [string]$Root = $PSScriptRoot
)

$files = @{
    "VAN_Engine.csproj" = @'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
</Project>
'@
    
    "Core/VANEngineBrain.cs" = @'
using System;
namespace VAN_Engine.Core;
public class VANEngineBrain { }
'@
    
    "Services/BrainBridge.cs" = @'
using System.Net.Http;
using System.Text;
using System.Text.Json;
namespace VAN_Engine.WinForms.Services;
public class BrainBridge { }
'@
}

Write-Host "Creating files in $Root..." -ForegroundColor Cyan

foreach ($file in $files.Keys) {
    $fullPath = Join-Path $Root $file
    $dir = Split-Path $fullPath -Parent
    if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -Path $fullPath -Value $files[$file] -Encoding UTF8
    Write-Host "  Created: $file" -ForegroundColor Green
}

Write-Host "`nDone!" -ForegroundColor Cyan