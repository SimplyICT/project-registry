# New Project Wizard — Design Spec

## Purpose
A web-based tool in the project-registry that guides creating a new project: collects project details via form, creates the folder structure, sets up opencode with superpowers, and updates `registry.json`.

## Architecture
- **Server:** Python stdlib `http.server` — single-file `new-project.py` in the registry root
- **Port:** 61738 (next after brainstorming port 61737)
- **No dependencies** beyond Python 3 stdlib
- Runs on the server machine where project-registry lives

## Form Fields
| Field | Type | Notes |
|-------|------|-------|
| Project name | text (required) | Auto-generates kebab-case path |
| Role | text (optional) | Free-text description |
| Server | dropdown | `server-a (208.87.135.84)`, `server-b (208.87.135.183)`, or custom |
| SSH address | text | Pre-filled from server selection, editable |
| Path | text | Pre-filled from name as `/home/aiagent/<name>` |
| Has Git | checkbox | Default on |
| Has Memory | checkbox | Default on |

## Backend Actions (POST /create)
1. Validate inputs (name required, path doesn't exist, etc.)
2. Create project directory at the specified path
3. Create `.opencode/` with:
   - `package.json` — `{ "dependencies": { "@opencode-ai/plugin": "1.17.9" } }`
   - `.gitignore` — node_modules, package.json, package-lock.json, bun.lock
   - `memory.md` — project template with creation date
   - `AGENTS.md` — basic stub
   - `opencode.json` — `{ "plugin": ["superpowers@latest"] }` (installed via `npm install` in the `.opencode/` dir)
   - Skills directory created; populated by the superpowers plugin on first opencode run
4. Run `npm install` in the `.opencode/` directory
5. `git init` if Has Git is checked
6. Append entry to `registry.json`
7. Return success summary with details of what was created

## UI
- Clean HTML form with styled fields
- Real-time output log showing each action as it runs
- Error messages inline (path exists, invalid name, etc.)
- Summary card on success with next steps

## File Structure
```
project-registry/
  new-project.py          # Server: form + API handler
  docs/superpowers/specs/ # This spec
  registry.json           # Updated on each project creation
```

## Error Handling
- If path already exists, show error (don't overwrite)
- If npm install fails, still complete the rest (warn user)
- If git init fails, still complete (warn user)
- All errors shown inline; partial success still adds to registry
