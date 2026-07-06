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

# Main loop
while ($true) {
    Clear-Host
    Write-Host "========== Project Switcher ==========" -ForegroundColor Cyan
    Write-Host ""

    $registry = Get-Content $RegistryFile -Raw | ConvertFrom-Json
    $projects = $registry.projects

    for ($i = 0; $i -lt $projects.Count; $i++) {
        $p = $projects[$i]
        $repo = Split-Path -Leaf $p.path
        $local = Join-Path $LocalBase $repo
        $status = if (Test-Path (Join-Path $local ".git")) { "✓" } else { " " }
        $role = if ($p.role) { $p.role } else { "" }
        Write-Host ("{0,2}. [{1}] {2}" -f ($i + 1), $status, $p.name)
        if ($role) { Write-Host ("     {0}" -f $role) }
    }

    Write-Host ""
    Write-Host "  a. Pull ALL projects" -ForegroundColor Yellow
    Write-Host "  q. Quit" -ForegroundColor Yellow
    Write-Host ""
    $choice = Read-Host "Select project"

    if ($choice -eq 'q') { Write-Host "Bye!"; break }

    if ($choice -eq 'a') {
        Write-Host "Syncing all projects..."
        foreach ($p in $projects) {
            $repo = Split-Path -Leaf $p.path
            $local = Join-Path $LocalBase $repo
            Sync-Project $p.name $p.github $local
        }
        Read-Host "All done. Press Enter..."
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
            Write-Host ""
            Write-Host "Opening $($p.name)..." -ForegroundColor Green
            Set-Location $local
            cmd /c "start" "cmd" "/K" "cd /d $local"
            Read-Host "Press Enter to return to switcher..."
        }
    } else {
        Read-Host "Invalid choice. Press Enter..."
    }
}
