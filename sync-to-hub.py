#!/usr/bin/env python3
"""Sync projects from registry.json to Project Hub's projects.json."""
import json
import os
import uuid
import sys
from datetime import datetime, timezone

REGISTRY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry.json")
HUB_DATA_FILE = "/home/aiagent/project-hub/projects.json"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def main():
    if not os.path.exists(REGISTRY_FILE):
        print(f"Error: registry.json not found at {REGISTRY_FILE}")
        sys.exit(1)
    if not os.path.exists(HUB_DATA_FILE):
        print(f"Error: Hub data file not found at {HUB_DATA_FILE}")
        sys.exit(1)

    registry = load_json(REGISTRY_FILE)
    hub_data = load_json(HUB_DATA_FILE)

    registry_projects = {p["name"]: p for p in registry.get("projects", [])}
    hub_projects = {p["name"]: p for p in hub_data.get("projects", []) if not p.get("archived")}

    added = 0
    skipped = 0
    max_sort = max((p.get("sort_order", 0) for p in hub_data.get("projects", [])), default=0)

    for name, rp in registry_projects.items():
        if name in hub_projects:
            skipped += 1
            continue

        ssh = rp.get("ssh", "")
        ssh_user = ssh.split("@")[0] if "@" in ssh else ""
        ssh_host = ssh.split("@")[1] if "@" in ssh else ""

        max_sort += 1
        entry = {
            "id": uuid.uuid4().hex[:12],
            "name": name,
            "description": rp.get("role", ""),
            "tracker_url": "",
            "server_host": ssh_host,
            "server_port": 22,
            "ssh_user": ssh_user,
            "ssh_auth_method": "key",
            "ssh_key_path": "/home/aiagent/.ssh/id_rsa",
            "folder_path": rp.get("path", ""),
            "has_tracker": False,
            "tracker_port": 3005,
            "archived": False,
            "github_repo": "",
            "github_branch": "main",
            "last_backup_at": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "sort_order": max_sort,
            "status_values": ["not_started", "in_progress", "blocked", "review", "done"],
            "tasks": []
        }
        hub_data.setdefault("projects", []).append(entry)
        added += 1
        print(f"  + Added: {name}")

    if added:
        save_json(HUB_DATA_FILE, hub_data)
        print(f"\nAdded {added} project(s) to Project Hub. {skipped} already present.")
    else:
        print(f"No new projects to add. {skipped} already present.")

if __name__ == "__main__":
    main()
