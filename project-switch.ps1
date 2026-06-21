#!/usr/bin/env pwsh

$RegistryPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$RegistryFile = Join-Path $RegistryPath "registry.json"
$Global:Timer = $null
$Global:CurrentProject = $null

# Verify VS Code CLI is available
if (-not (Get-Command "code" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: 'code' command not found (VS Code CLI). Add VS Code to PATH." -ForegroundColor Red
    exit 1
}

function Cleanup {
    if ($Global:Timer) {
        $Global:Timer.Stop()
        $Global:Timer.Dispose()
    }
    if ($Global:CurrentProject -and $Global:CurrentProject.hasGit -and $Global:CurrentProject.hasMemory) {
        Write-Host "Saving memory..." -ForegroundColor Green
        Push-Location $Global:CurrentProject.path
        & git add ".opencode/memory.md" 2>$null
        & git commit -m "auto-save memory $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>$null
        & git push 2>$null
        Pop-Location
        Write-Host "Memory saved." -ForegroundColor Green
    }
    & git -C $RegistryPath pull --ff-only 2>$null
}

function Show-Menu($projects) {
    Clear-Host
    Write-Host "===== Project Switcher =====" -ForegroundColor Cyan
    Write-Host ""
    for ($i = 0; $i -lt $projects.Count; $i++) {
        $p = $projects[$i]
        $gitFlag = if ($p.hasGit) { "git" } else { "--" }
        Write-Host ("{0,2}. {1,-25} [{2,-9}] {3}" -f ($i+1), $p.name, $p.server, $gitFlag)
    }
    Write-Host ""
    Write-Host "  q. Quit" -ForegroundColor Yellow
    Write-Host ""
}

function Open-Project($project) {
    $Global:CurrentProject = $project

    # Pull registry
    Write-Host "Pulling latest registry..." -ForegroundColor Cyan
    & git -C $RegistryPath pull --ff-only 2>$null

    # Pull project repo
    if ($project.hasGit) {
        Write-Host "Pulling latest from $($project.name)..." -ForegroundColor Green
        Push-Location $project.path
        & git pull --ff-only 2>$null
        Pop-Location
    }

    # Start auto-save timer
    if ($project.hasGit -and $project.hasMemory) {
        $Global:Timer = New-Object System.Timers.Timer
        $Global:Timer.Interval = 600000
        $Global:Timer.AutoReset = $true
        Register-ObjectEvent -InputObject $Global:Timer -EventName Elapsed -MessageData $project -Action {
            $proj = $Event.MessageData
            Push-Location $proj.path
            & git add ".opencode/memory.md" 2>$null
            & git commit -m "auto-save memory $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>$null
            & git push 2>$null
            Pop-Location
        } | Out-Null
        $Global:Timer.Start()
    }

    # Launch VS Code via SSH Remote
    $uri = "vscode-remote://ssh-remote+$($project.ssh)$($project.path)"
    Write-Host "Opening $($project.name) in VS Code..." -ForegroundColor Green
    $process = Start-Process -FilePath "code" -ArgumentList "--new-window", "--folder-uri", "`"$uri`"" -PassThru -WindowStyle Normal
    $process.WaitForExit()

    # Cleanup runs on exit
    Cleanup
}

# Main
try {
    $registry = Get-Content $RegistryFile -Raw | ConvertFrom-Json
    $projects = $registry.projects

    do {
        Show-Menu $projects
        $choice = Read-Host "Select project"

        if ($choice -eq 'q') { break }

        $index = 0
        if ([int]::TryParse($choice, [ref]$index)) {
            $index -= 1
        }
        if ($index -ge 0 -and $index -lt $projects.Count) {
            Open-Project $projects[$index]
            break
        }
    } while ($true)
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Cleanup
    exit 1
}
