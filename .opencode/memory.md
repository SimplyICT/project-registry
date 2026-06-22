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
