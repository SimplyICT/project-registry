#!/usr/bin/env bash
set -euo pipefail

REGISTRY_DIR="$(cd "$(dirname "$0")" && pwd)"
REGISTRY_FILE="$REGISTRY_DIR/registry.json"
REGISTRY_REPO_DIR="$REGISTRY_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
AUTOSAVE_INTERVAL=600

cleanup() {
  local exit_code=$?
  if [[ -n "${PROJECT_DIR:-}" && -n "${HAS_GIT:-}" && "${HAS_MEMORY:-}" == "true" ]]; then
    echo -e "${GREEN}Saving memory...${NC}"
    git -C "$PROJECT_DIR" add .opencode/memory.md 2>/dev/null || true
    git -C "$PROJECT_DIR" commit -m "auto-save memory $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || true
    git -C "$PROJECT_DIR" push 2>/dev/null || true
    echo -e "${GREEN}Memory saved.${NC}"
  fi
  kill ${AUTOSAVE_PID:-} 2>/dev/null || true
  git -C "$REGISTRY_REPO_DIR" pull --ff-only 2>/dev/null || true
  exit "$exit_code"
}
trap cleanup EXIT

AUTOSAVE_LOOP() {
  while true; do
    sleep "$AUTOSAVE_INTERVAL"
    if [[ -n "${PROJECT_DIR:-}" && -n "${HAS_GIT:-}" && "${HAS_MEMORY:-}" == "true" ]]; then
      git -C "$PROJECT_DIR" add .opencode/memory.md 2>/dev/null || true
      git -C "$PROJECT_DIR" commit -m "auto-save memory $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || true
      git -C "$PROJECT_DIR" push 2>/dev/null || true
    fi
  done
}

list_projects() {
  python3 -c "
import json, sys
with open('$REGISTRY_FILE') as f:
  data = json.load(f)
for i, p in enumerate(data['projects'], 1):
  git_flag = 'git' if p.get('hasGit') else '--'
  role = p.get('role', '')
  print(f'{i:2}. {p["name"]:22s} {role:30s} [{p["server"]:9s}] {git_flag}')
"
}

get_project() {
  local index=$1
  python3 -c "
import json, sys
with open('$REGISTRY_FILE') as f:
  data = json.load(f)
p = data['projects'][$index]
print(json.dumps(p))
"
}

check_deps() {
  if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: python3 is required${NC}"
    exit 1
  fi
  if ! command -v code &>/dev/null; then
    echo -e "${RED}Error: 'code' command not found (VS Code CLI)${NC}"
    echo "Install VS Code and add 'code' to PATH"
    exit 1
  fi
}

main() {
  check_deps

  echo -e "${CYAN}Pulling latest registry...${NC}"
  git -C "$REGISTRY_REPO_DIR" pull --ff-only 2>/dev/null || true

  while true; do
    clear
    echo -e "${CYAN}===== Project Switcher =====${NC}"
    echo ""
    list_projects
    echo ""
    echo -e "${YELLOW}  q. Quit${NC}"
    echo ""
    read -rp "Select project: " choice

    if [[ "$choice" == "q" ]]; then
      exit 0
    fi

    if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
      continue
    fi

    PROJECT_JSON=$(get_project $((choice - 1)) 2>/dev/null) || continue

    PROJECT_NAME=$(echo "$PROJECT_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['name'])")
    PROJECT_DIR=$(echo "$PROJECT_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['path'])")
    PROJECT_SSH=$(echo "$PROJECT_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['ssh'])")
    HAS_GIT=$(echo "$PROJECT_JSON" | python3 -c "import json,sys; print(str(json.load(sys.stdin).get('hasGit', False)).lower())")
    HAS_MEMORY=$(echo "$PROJECT_JSON" | python3 -c "import json,sys; print(str(json.load(sys.stdin).get('hasMemory', False)).lower())")

    if [[ "$HAS_GIT" == "true" ]]; then
      echo -e "${GREEN}Pulling latest from $PROJECT_NAME...${NC}"
      git -C "$PROJECT_DIR" pull --ff-only 2>/dev/null || true
    fi

    AUTOSAVE_PID=""
    if [[ "$HAS_GIT" == "true" && "$HAS_MEMORY" == "true" ]]; then
      AUTOSAVE_LOOP &
      AUTOSAVE_PID=$!
    fi

    URI="vscode-remote://ssh-remote+${PROJECT_SSH}${PROJECT_DIR}"
    echo -e "${GREEN}Opening $PROJECT_NAME in VS Code...${NC}"
    code --new-window --folder-uri "$URI"
    echo -e "${GREEN}VS Code closed.${NC}"
    break
  done
}

main "$@"
