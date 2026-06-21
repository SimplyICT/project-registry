# Project Registry Setup

## Prerequisites (Windows)
- [VS Code](https://code.visualstudio.com/)
- [VS Code Remote SSH extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)
- [PowerShell](https://github.com/PowerShell/PowerShell) (Windows comes with it)
- [Git for Windows](https://git-scm.com/download/win)
- SSH key configured for both servers

## Clone the registry
```bash
cd ~
git clone https://github.com/SimplyICT/project-registry.git
```

## Run the switcher
```powershell
cd ~/project-registry
.\project-switch.ps1
```

## First-time SSH config
Make sure `~/.ssh/config` has entries for your servers:
```
Host server-a
    HostName 208.87.135.84
    User user

Host server-b
    HostName <server-b-ip>
    User user
```

## To update the registry (add/change projects)
1. Edit `registry.json`
2. Commit and push:
```bash
git add registry.json
git commit -m "feat: update project list"
git push
```
3. On each machine, the switcher auto-pulls on open.
