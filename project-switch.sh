#!/bin/bash
# Project Switcher - run on Ubuntu or Git Bash (Windows)
# Usage: ~/projects/project-registry/project-switch.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REGISTRY_FILE="$SCRIPT_DIR/registry.json"
LOCAL_BASE="$HOME/projects"
TEMP_FILE=$(mktemp)

mkdir -p "$LOCAL_BASE"

cd "$SCRIPT_DIR" && git pull --ff-only 2>/dev/null

python3 - "$REGISTRY_FILE" "$LOCAL_BASE" > "$TEMP_FILE" << 'PYEOF'
import json, os, sys
with open(sys.argv[1]) as f:
    reg = json.load(f)
base = os.path.expanduser(sys.argv[2])
for p in reg['projects']:
    name = p['name']
    role = p.get('role', '')
    github = p.get('github', '')
    local = os.path.join(base, os.path.basename(p['path']))
    cloned = 'yes' if os.path.isdir(os.path.join(local, '.git')) else 'no'
    print(f"{name}|{role}|{github}|{local}|{cloned}")
PYEOF

sync_project() {
    local name="$1" github="$2" localpath="$3"
    if [ -z "$github" ]; then
        echo "No GitHub URL for $name - skipping"
        return
    fi
    if [ -d "$localpath/.git" ]; then
        echo "Pulling $name..."
        cd "$localpath" && git pull --ff-only
    else
        echo "Cloning $name..."
        git clone "$github" "$localpath"
    fi
}

while true; do
    clear
    echo "===== Project Switcher ====="

    i=0
    while IFS='|' read -r name role github localpath cloned; do
        i=$((i + 1))
        status=" "
        [ "$cloned" = "yes" ] && status="✓"
        role_txt=""
        [ -n "$role" ] && role_txt=" - $role"
        printf "%2d.[%s]%s%s\n" $i "$status" "$name" "$role_txt"
    done < "$TEMP_FILE"

    echo ""
    read -p "# " choice

    case "$choice" in
        q|Q) break ;;
        a|A)
            while IFS='|' read -r name role github localpath cloned; do
                sync_project "$name" "$github" "$localpath"
            done < "$TEMP_FILE"
            read -p "done, press enter..."
            ;;
        *)
            if [[ "$choice" =~ ^[0-9]+$ ]]; then
                idx=0
                while IFS='|' read -r name role github localpath cloned; do
                    idx=$((idx + 1))
                    if [ "$idx" -eq "$choice" ]; then
                        sync_project "$name" "$github" "$localpath"
                        cd "$localpath"
                        $SHELL
                        read -p "back, press enter..."
                        break
                    fi
                done < "$TEMP_FILE"
            else
                read -p "invalid, press enter..."
            fi
            ;;
    esac
done

rm -f "$TEMP_FILE"
