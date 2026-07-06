# Project Registry — Session Memory

## 2026-06-21: GitHub Push & Role Labels

- **Pushed** to `https://github.com/SimplyICT/project-registry`
- **Fixed** JSON comma bug (missing comma before Wazuh SOC entry)
- **Added** Wazuh SOC + Project Registry to project list (10 projects total)
- **Added** `role` field to all projects (Frontend/Backend/Full Stack/etc.)
- **Updated** both `project-switch.sh` and `project-switch.ps1` to display role column
- **To update:** `git pull` in `~/project-registry` on laptop/desktop

## 2026-06-22: New Project Wizard

- **Built** `new-project.py` — Python stdlib server (port 61738) with web form to scaffold new projects
- **Creates** project folder, `.opencode/` with superpowers, AGENTS.md, git init, updates `registry.json`
- **Optional** "Register in Project Hub" checkbox — logs into hub (port 3010) and creates project there too
- **Path traversal** protected (rejects `..` segments)
- **Added** link to wizard in Project Hub top bar, plus help/devdocs sections
- **Committed** to both repos (registry + project-hub)

## 2026-07-06: Web-based Project Switcher + Terminal

- **Fixed** `project-switch.ps1` — now launches opencode in project dir instead of plain cmd window
- **Built** `web-switcher/switcher_server.py` — Python HTTP server on port 8765 (`.84:8765`) serving project cards from `registry.json`
- **Built** `web-switcher/terminal_server.py` — WebSocket PTY terminal server on port 8766 using `websockets` + `pty`
- **Built** `web-switcher/templates/index.html` — xterm.js frontend: click a project card to open a browser terminal directly in the project's directory
- **Terminal handles both servers:** local shell for .84 projects, SSH for .183 projects
- **Created systemd services:** `web-switcher.service` (HTTP) and `terminal-websocket.service` (WebSocket), both enabled and running
- **Firewall:** opened ports 8765 and 8766 on .84
