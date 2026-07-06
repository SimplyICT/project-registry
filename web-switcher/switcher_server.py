#!/usr/bin/env python3
"""Web-based Project Switcher — .84:8765"""
import http.server, json, os, subprocess, sys, threading, urllib.parse, shutil

REGISTRY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "registry.json")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
PORT = int(os.environ.get("SWITCHER_PORT", "8765"))
TERMINAL_PORT = int(os.environ.get("TERMINAL_PORT", "8766"))
WS_TERMINAL_URL = f"ws://208.87.135.84:{TERMINAL_PORT}"

SERVERS = {"84": "aiagent@208.87.135.84", "183": "aiagent@208.87.135.183"}
HAS_OPENCODE = shutil.which("opencode") is not None

def load_registry():
    with open(REGISTRY_FILE) as f:
        return json.load(f)

def get_ssh(project):
    if project.get("ssh"):
        return project["ssh"]
    server = str(project.get("server", ""))
    for key in ("84", "183"):
        if key in server:
            return SERVERS[key]
    return ""

def find_project(projects, name):
    for p in projects:
        if p["name"].lower() == name.lower():
            return p
    for p in projects:
        if name.lower() in p["name"].lower():
            return p
    return None

def is_same_server(project):
    ssh = get_ssh(project)
    return ssh == SERVERS.get("84") or not ssh

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/projects":
            return self.send_json({"projects": load_registry().get("projects", []), "has_opencode": HAS_OPENCODE, "terminal_url": WS_TERMINAL_URL})
        elif path.startswith("/api/launch/"):
            name = urllib.parse.unquote(path[len("/api/launch/"):])
            registry = load_registry()
            project = find_project(registry["projects"], name)
            if not project:
                return self.send_json({"error": f"Project '{name}' not found"}, 404)
            return self.do_launch(project)
        elif path.startswith("/api/info/"):
            name = urllib.parse.unquote(path[len("/api/info/"):])
            registry = load_registry()
            project = find_project(registry["projects"], name)
            if not project:
                return self.send_json({"error": f"Project '{name}' not found"}, 404)
            ssh = get_ssh(project)
            return self.send_json({
                "name": project["name"],
                "role": project.get("role", ""),
                "path": project["path"],
                "server": project.get("server", ""),
                "ssh": ssh,
                "has_git": project.get("hasGit", False),
                "has_memory": project.get("hasMemory", False),
                "has_opencode": HAS_OPENCODE,
                "github": project.get("github", ""),
                "ssh_cmd": f"ssh {ssh} -t \"cd {project['path']} && exec \\$SHELL -l\"" if ssh else "",
                "terminal_url": WS_TERMINAL_URL
            })
        else:
            self.send_static("index.html")

    def do_launch(self, project):
        ssh = get_ssh(project)
        if not ssh:
            return self.send_json({"error": f"No SSH server for {project['name']}"}, 400)

        if not HAS_OPENCODE:
            return self.send_json({
                "error": None,
                "message": "opencode not installed — use SSH instead",
                "ssh_cmd": f"ssh {ssh} -t \"cd {project['path']} && exec \\$SHELL -l\"" if ssh else "",
                "name": project["name"],
                "path": project["path"],
                "server": ssh
            })

        if is_same_server(project):
            subprocess.Popen(
                f"cd {project['path']} && nohup opencode >/dev/null 2>&1 &",
                shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return self.send_json({"message": f"Launched opencode in {project['name']}"})
        else:
            subprocess.Popen(
                ["ssh", "-f"] + ssh.split() + [f"cd {project['path']} && nohup opencode >/dev/null 2>&1 &"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return self.send_json({"message": f"Launched opencode in {project['name']} on {ssh}"})

    def send_static(self, fn):
        fp = os.path.join(TEMPLATES_DIR, fn)
        if os.path.isfile(fp):
            with open(fp, "rb") as f:
                d = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(d)))
                self.end_headers()
                self.wfile.write(d)
        else:
            self.send_json({"error": "Not found"}, 404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def main():
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Project Switcher on http://0.0.0.0:{PORT}")
    if not HAS_OPENCODE:
        print("  opencode not installed — cards will show SSH command instead")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
