#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener, install_opener
from urllib.error import URLError, HTTPError

PORT = 61738
REGISTRY_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "registry.json")

SERVERS = {
    "server-a": "aiagent@208.87.135.84",
    "server-b": "aiagent@208.87.135.183",
}

FORM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>New Project Wizard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px 20px; }
  .container { max-width: 640px; margin: 0 auto; }
  h1 { font-size: 24px; margin-bottom: 24px; color: #58a6ff; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 24px; margin-bottom: 16px; }
  label { display: block; font-size: 14px; font-weight: 500; margin-bottom: 6px; color: #8b949e; }
  input, select { width: 100%; padding: 10px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 14px; margin-bottom: 16px; }
  input:focus, select:focus { outline: none; border-color: #58a6ff; }
  .checkbox-row { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
  .checkbox-row input { width: auto; margin-bottom: 0; }
  button { width: 100%; padding: 12px; background: #238636; border: none; border-radius: 6px; color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; }
  button:hover { background: #2ea043; }
  button:disabled { opacity: 0.6; cursor: not-allowed; }
  #output { display: none; margin-top: 16px; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 13px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; }
  #output .success { color: #3fb950; }
  #output .error { color: #f85149; }
  #output .warn { color: #d29922; }
  #output .info { color: #8b949e; }
  .summary { display: none; margin-top: 16px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 24px; }
  .summary h2 { color: #3fb950; font-size: 18px; margin-bottom: 12px; }
  .summary dt { color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  .summary dd { color: #c9d1d9; font-size: 14px; margin-bottom: 12px; font-family: 'SF Mono', monospace; }
  .error-msg { color: #f85149; font-size: 13px; margin-top: -12px; margin-bottom: 12px; display: none; }
  .hint { color: #8b949e; font-size: 12px; margin-top: -12px; margin-bottom: 12px; }
</style>
</head>
<body>
<div class="container">
  <h1>New Project Wizard</h1>
  <div class="card">
    <form id="projectForm">
      <label for="name">Project Name</label>
      <input type="text" id="name" name="name" required autofocus placeholder="My Cool Project">
      <div id="nameError" class="error-msg"></div>

      <label for="role">Role / Description</label>
      <input type="text" id="role" name="role" placeholder="Full Stack (React + Python)">

      <label for="server">Server</label>
      <select id="server" name="server">
        <option value="server-a">server-a (208.87.135.84)</option>
        <option value="server-b">server-b (208.87.135.183)</option>
        <option value="custom">Custom</option>
      </select>

      <div id="customServerGroup" style="display:none;">
        <label for="customServer">Custom Server Label</label>
        <input type="text" id="customServer" name="customServer" placeholder="server-c">
      </div>

      <label for="ssh">SSH Address</label>
      <input type="text" id="ssh" name="ssh" required placeholder="user@host">

      <label for="path">Project Path</label>
      <input type="text" id="path" name="path" required placeholder="/home/aiagent/my-cool-project">
      <div id="pathError" class="error-msg"></div>

      <div class="checkbox-row">
        <input type="checkbox" id="hasGit" name="hasGit" checked>
        <label for="hasGit" style="margin:0;">Initialize Git repository</label>
      </div>

      <div class="checkbox-row">
        <input type="checkbox" id="hasMemory" name="hasMemory" checked>
        <label for="hasMemory" style="margin:0;">Enable auto-save memory</label>
      </div>

      <div class="checkbox-row" style="margin-top:12px;padding-top:12px;border-top:1px solid #30363d;">
        <input type="checkbox" id="registerHub" name="registerHub" onchange="toggleHubFields()">
        <label for="registerHub" style="margin:0;font-weight:600;">Also register in Project Hub</label>
      </div>
      <div id="hubFields" style="display:none;">
        <label for="hubUrl">Hub URL</label>
        <input type="text" id="hubUrl" name="hubUrl" value="http://208.87.135.84:3010">
        <label for="hubUser">Hub Username</label>
        <input type="text" id="hubUser" name="hubUser" value="admin">
        <label for="hubPass">Hub Password</label>
        <input type="password" id="hubPass" name="hubPass" placeholder="admin123">
      </div>

      <button type="submit" id="submitBtn">Create Project</button>
    </form>
  </div>

  <div id="output"></div>
  <div id="summary" class="summary"></div>
</div>

<script>
function kebabCase(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

document.getElementById('name').addEventListener('input', function() {
  const name = this.value.trim();
  const pathInput = document.getElementById('path');
  if (name) {
    pathInput.value = '/home/aiagent/' + kebabCase(name);
  }
  document.getElementById('nameError').style.display = 'none';
  this.setCustomValidity('');
});

document.getElementById('server').addEventListener('change', function() {
  const customGroup = document.getElementById('customServerGroup');
  const sshInput = document.getElementById('ssh');
  if (this.value === 'custom') {
    customGroup.style.display = 'block';
    sshInput.value = '';
  } else {
    customGroup.style.display = 'none';
    const servers = {{SERVERS_JSON}};
    sshInput.value = servers[this.value] || '';
  }
});

function toggleHubFields() {
  const hubFields = document.getElementById('hubFields');
  const cb = document.getElementById('registerHub');
  hubFields.style.display = cb.checked ? 'block' : 'none';
}

document.getElementById('path').addEventListener('input', function() {
  document.getElementById('pathError').style.display = 'none';
});

document.getElementById('projectForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = document.getElementById('submitBtn');
  const output = document.getElementById('output');
  const summary = document.getElementById('summary');
  summary.style.display = 'none';
  output.style.display = 'block';
  output.innerHTML = '';
  btn.disabled = true;
  btn.textContent = 'Creating...';

  const formData = new FormData(this);
  const params = new URLSearchParams(formData);

  try {
    const res = await fetch('/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('DATA:')) {
          const data = JSON.parse(line.slice(5));
          const div = document.createElement('div');
          div.className = data.level || 'info';
          div.textContent = data.message;
          output.appendChild(div);
          output.scrollTop = output.scrollHeight;
          if (data.level === 'success' && data.summary) {
            summary.style.display = 'block';
            summary.innerHTML = '<h2>Project Created</h2>' +
              '<dl>' +
              Object.entries(data.summary).map(([k, v]) =>
                '<dt>' + k + '</dt><dd>' + v + '</dd>'
              ).join('') +
              '</dl>';
          }
        }
      }
    }
  } catch (err) {
    const div = document.createElement('div');
    div.className = 'error';
    div.textContent = 'Error: ' + err.message;
    output.appendChild(div);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create Project';
  }
});
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = FORM_HTML.replace("{{SERVERS_JSON}}", json.dumps(SERVERS))
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/create":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            params = parse_qs(body)

            name = (params.get("name", [""])[0]).strip()
            role = params.get("role", [""])[0].strip()
            server = params.get("server", [""])[0]
            custom_server = params.get("customServer", [""])[0].strip()
            ssh = params.get("ssh", [""])[0].strip()
            path = params.get("path", [""])[0].strip()
            has_git = params.get("hasGit", [""])[0] == "on"
            has_memory = params.get("hasMemory", [""])[0] == "on"
            register_hub = params.get("registerHub", [""])[0] == "on"
            hub_url = params.get("hubUrl", [""])[0].strip()
            hub_user = params.get("hubUser", [""])[0].strip()
            hub_pass = params.get("hubPass", [""])[0]

            if not name:
                self._send_error("Project name is required")
                return
            if not path:
                self._send_error("Project path is required")
                return
            if not ssh:
                self._send_error("SSH address is required")
                return

            if server == "custom" and custom_server:
                server = custom_server

            if ".." in path.split("/"):
                self._send_error("Path must not contain parent directory references")
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            def emit(level, message, summary=None):
                data = {"level": level, "message": message}
                if summary:
                    data["summary"] = summary
                line = f"DATA:{json.dumps(data)}\n"
                self.wfile.write(f"{len(line):x}\r\n{line}\r\n".encode())
                self.wfile.flush()

            try:
                self._create_project(name, role, server, ssh, path, has_git, has_memory, emit)
                if register_hub and hub_url and hub_user and hub_pass:
                    self._register_in_hub(name, role, ssh, path, hub_url, hub_user, hub_pass, emit)
            except Exception as e:
                emit("error", f"Failed: {e}")

            emit("info", "Done.")
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        else:
            self.send_response(404)
            self.end_headers()

    def _send_error(self, message):
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

    def _create_project(self, name, role, server, ssh, path, has_git, has_memory, emit):
        if os.path.exists(path):
            emit("error", f"Path already exists: {path}")
            return

        emit("info", f"Creating project directory: {path}")
        os.makedirs(path, exist_ok=True)

        opencode_dir = os.path.join(path, ".opencode")
        os.makedirs(opencode_dir, exist_ok=True)
        emit("info", "Created .opencode/ directory")

        pkg = {"dependencies": {"@opencode-ai/plugin": "1.17.9"}}
        with open(os.path.join(opencode_dir, "package.json"), "w") as f:
            json.dump(pkg, f, indent=2)
        emit("info", "Created .opencode/package.json")

        opencode_config = {"plugin": ["superpowers@latest"]}
        with open(os.path.join(opencode_dir, "opencode.json"), "w") as f:
            json.dump(opencode_config, f, indent=2)
        emit("info", "Created .opencode/opencode.json")

        gitignore_content = "node_modules\npackage.json\npackage-lock.json\nbun.lock\n.gitignore\n"
        with open(os.path.join(opencode_dir, ".gitignore"), "w") as f:
            f.write(gitignore_content)
        emit("info", "Created .opencode/.gitignore")

        memory_template = f"# {name} \u2014 Project Memory\n\n"
        memory_template += f"Created: {datetime.now().strftime('%Y-%m-%d')}\n"
        memory_template += "\n## Server\n"
        memory_template += f"- SSH: `{ssh}`\n"
        if server:
            memory_template += f"- Server label: `{server}`\n"
        with open(os.path.join(opencode_dir, "memory.md"), "w") as f:
            f.write(memory_template)
        emit("info", "Created .opencode/memory.md")

        agents_content = f"# {name}\n\n"
        agents_content += "## Project Info\n"
        agents_content += f"- Role: {role or 'TBD'}\n"
        agents_content += f"- Server: {server}\n"
        agents_content += f"- SSH: {ssh}\n"
        agents_content += f"- Path: {path}\n"
        with open(os.path.join(path, "AGENTS.md"), "w") as f:
            f.write(agents_content)
        emit("info", "Created AGENTS.md")

        emit("info", "Running npm install for opencode plugins...")
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=opencode_dir,
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                emit("success", "npm install completed")
            else:
                emit("warn", f"npm install warning: {result.stderr[:200]}")
        except FileNotFoundError:
            emit("warn", "npm not found, skipping npm install")

        if has_git:
            emit("info", "Initializing git repository...")
            subprocess.run(["git", "init"], cwd=path, capture_output=True, timeout=30)
            gitignore_path = os.path.join(path, ".gitignore")
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, "w") as f:
                    f.write("node_modules/\n.opencode/node_modules/\n.opencode/package.json\n.opencode/package-lock.json\n")
            emit("success", "Git repository initialized")

        emit("info", "Updating registry.json...")
        with open(REGISTRY_FILE, "r+") as f:
            registry = json.load(f)
            entry = {
                "name": name,
                "role": role or "Unknown",
                "server": server,
                "path": path,
                "ssh": ssh,
                "hasGit": has_git,
                "hasMemory": has_memory,
            }
            registry.setdefault("projects", []).append(entry)
            f.seek(0)
            json.dump(registry, f, indent=2)
            f.truncate()
        emit("success", "registry.json updated")

        summary = {
            "Name": name,
            "Role": role or "Unknown",
            "Server": server,
            "SSH": ssh,
            "Path": path,
            "Git": "Yes" if has_git else "No",
            "Memory": "Yes" if has_memory else "No",
        }
        emit("success", "Project created successfully!", summary=summary)

    def _register_in_hub(self, name, role, ssh, path, hub_url, hub_user, hub_pass, emit):
        emit("info", f"Logging into Project Hub at {hub_url}...")

        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = build_opener(NoRedirect)
        login_data = urlencode({"username": hub_user, "password": hub_pass}).encode()
        login_req = Request(f"{hub_url}/login", data=login_data, method="POST")
        login_req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            try:
                login_resp = opener.open(login_req, timeout=10)
                cookie_raw = login_resp.headers.get("Set-Cookie", "")
            except HTTPError as e:
                cookie_raw = e.headers.get("Set-Cookie", "")
            if not cookie_raw:
                emit("error", "Login failed — no session cookie returned")
                return
            cookie_value = cookie_raw.split(";")[0]
        except URLError as e:
            emit("error", f"Hub login failed: {e.reason}")
            return
        except Exception as e:
            emit("error", f"Hub login failed: {e}")
            return

        ssh_user = ssh.split("@")[0] if "@" in ssh else ""
        ssh_host = ssh.split("@")[1] if "@" in ssh else ""
        project_data = json.dumps({
            "name": name,
            "description": role or "",
            "folder_path": path,
            "server_host": ssh_host,
            "ssh_user": ssh_user,
            "ssh_auth_method": "key",
            "has_tracker": False,
        }).encode()

        emit("info", "Creating project in Project Hub...")
        try:
            create_req = Request(f"{hub_url}/api/projects", data=project_data, method="POST")
            create_req.add_header("Content-Type", "application/json")
            create_req.add_header("Cookie", cookie_value)
            create_resp = opener.open(create_req, timeout=10)
            result = json.loads(create_resp.read().decode())
            if result.get("project"):
                emit("success", "Project registered in Project Hub")
            else:
                emit("warn", f"Hub response: {result.get('error', 'unknown')}")
        except URLError as e:
            emit("error", f"Hub registration failed: {e.reason}")
        except Exception as e:
            emit("error", f"Hub registration failed: {e}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"New Project Wizard running on http://0.0.0.0:{PORT}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()
