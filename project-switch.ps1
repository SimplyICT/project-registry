#!/usr/bin/env pwsh
# Project Switcher - PowerShell version for Windows
# Usage: ~/projects/project-registry/project-switch.ps1

$RegistryPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$RegistryFile = Join-Path $RegistryPath "registry.json"
$LocalBase = Join-Path $env:USERPROFILE "projects"

New-Item -ItemType Directory -Force -Path $LocalBase | Out-Null

# Self-update
Set-Location $RegistryPath
git pull --ff-only 2>$null

function Sync-Project($name, $github, $localPath) {
    if (-not $github) {
        Write-Host "No GitHub URL for $name - skipping" -ForegroundColor Yellow
        return
    }
    if (Test-Path (Join-Path $localPath ".git")) {
        Write-Host "Pulling $name..." -ForegroundColor Green
        Set-Location $localPath
        git pull --ff-only
    } else {
        Write-Host "Cloning $name..." -ForegroundColor Green
        git clone $github $localPath
    }
}

while ($true) {
    Clear-Host
    Write-Host "===== Project Switcher ====="

    $registry = Get-Content $RegistryFile -Raw | ConvertFrom-Json
    $projects = $registry.projects

    for ($i = 0; $i -lt $projects.Count; $i++) {
        $p = $projects[$i]
        $repo = Split-Path -Leaf $p.path
        $local = Join-Path $LocalBase $repo
        $status = if (Test-Path (Join-Path $local ".git")) { "✓" } else { " " }
        $role = if ($p.role) { " - $($p.role)" } else { "" }
        Write-Host ("{0,2}.[{1}] {2}{3}" -f ($i + 1), $status, $p.name, $role)
    }

    $choice = Read-Host "#"

    if ($choice -eq 'q') { break }

    if ($choice -eq 'a') {
        foreach ($p in $projects) {
            $repo = Split-Path -Leaf $p.path
            $local = Join-Path $LocalBase $repo
            Sync-Project $p.name $p.github $local
        }
        Read-Host "done, press enter..."
        continue
    }

    $index = 0
    if ([int]::TryParse($choice, [ref]$index)) {
        $index -= 1
        if ($index -ge 0 -and $index -lt $projects.Count) {
            $p = $projects[$index]
            $repo = Split-Path -Leaf $p.path
            $local = Join-Path $LocalBase $repo
            Sync-Project $p.name $p.github $local
            Set-Location $local
            cmd /c "start" "cmd" "/K" "cd /d $local"
            Read-Host "back, press enter..."
        }
    } else {
        Read-Host "invalid, press enter..."
    }
}
