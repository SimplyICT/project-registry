#!/usr/bin/env bash
set -euo pipefail

REGISTRY_DIR="$(cd "$(dirname "$0")" && pwd)"
REGISTRY_FILE="$REGISTRY_DIR/registry.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

list_projects() {
  python3 -c "
import json, sys
with open('$REGISTRY_FILE') as f:
  data = json.load(f)
for i, p in enumerate(data['projects'], 1):
  git_flag = 'git' if p.get('hasGit') else '--'
  role = p.get('role', '')
  print(f'{i:2}. {p[\"name\"]:22s} {role:30s} [{p[\"server\"]:9s}] {git_flag}')
"
}

get_project_info() {
  local index=$1
  python3 -c "
import json, sys
with open('$REGISTRY_FILE') as f:
  data = json.load(f)
p = data['projects'][$index]
print(p['path'])
print(p['name'])
print(p.get('ssh', ''))
"
}

main() {
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

    PROJECT_INFO=$(get_project_info $((choice - 1)) 2>/dev/null) || continue
    PROJECT_PATH=$(echo "$PROJECT_INFO" | sed -n '1p')
    PROJECT_NAME=$(echo "$PROJECT_INFO" | sed -n '2p')
    PROJECT_SSH=$(echo "$PROJECT_INFO" | sed -n '3p')

    echo -e "${GREEN}Switching to $PROJECT_NAME on $PROJECT_SSH...${NC}"
    ssh -t "$PROJECT_SSH" "cd '$PROJECT_PATH' && exec opencode"
    break
  done
}

main "$@"
