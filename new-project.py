#!/usr/bin/env python3
import json, os, subprocess, uuid, threading, traceback
import requests as _requests
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

PORT = 61738
REGISTRY_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "registry.json")
HUB_DATA_FILE = "/home/aiagent/project-hub/projects.json"

SERVERS = {"server-a": "aiagent@208.87.135.84", "server-b": "aiagent@208.87.135.183"}

FORM_HTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>New Project Wizard</title>\n<style>\n*{box-sizing:border-box;margin:0;padding:0}\nbody{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0d1117;color:#c9d1d9;padding:40px 20px}\n.container{max-width:640px;margin:0 auto}\nh1{font-size:24px;margin-bottom:24px;color:#58a6ff}\n.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:24px;margin-bottom:16px}\nlabel{display:block;font-size:14px;font-weight:500;margin-bottom:6px;color:#8b949e}\ninput,select{width:100%;padding:10px 12px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:14px;margin-bottom:16px}\ninput:focus,select:focus{outline:none;border-color:#58a6ff}\n.checkbox-row{display:flex;align-items:center;gap:10px;margin-bottom:16px}\n.checkbox-row input{width:auto;margin-bottom:0}\nbutton{width:100%;padding:12px;background:#238636;border:none;border-radius:6px;color:#fff;font-size:16px;font-weight:600;cursor:pointer}\nbutton:hover{background:#2ea043}\nbutton:disabled{opacity:.6;cursor:not-allowed}\n#output{display:none;margin-top:16px;background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:16px;font-family:"SF Mono","Fira Code",monospace;font-size:13px;max-height:400px;overflow-y:auto;white-space:pre-wrap}\n#output .success{color:#3fb950}#output .error{color:#f85149}#output .warn{color:#d29922}#output .info{color:#8b949e}\n.summary{display:none;margin-top:16px;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:24px}\n.summary h2{color:#3fb950;font-size:18px;margin-bottom:12px}\n.summary dt{color:#8b949e;font-size:12px;text-transform:uppercase;letter-spacing:.5px}\n.summary dd{color:#c9d1d9;font-size:14px;margin-bottom:12px;font-family:"SF Mono",monospace}\n</style>\n</head>\n<body>\n<div class="container">\n<h1>New Project Wizard</h1>\n<div class="card">\n<form id="pf" action="create" method="POST">\n<label for="name">Project Name</label>\n<input type="text" id="name" name="name" required autofocus placeholder="My Cool Project">\n<div id="nameError" class="error-msg"></div>\n<label for="role">Role / Description</label>\n<input type="text" id="role" name="role" placeholder="Full Stack (React + Python)">\n<label for="server">Server</label>\n<select id="server" name="server">\n<option value="server-a">server-a (208.87.135.84)</option>\n<option value="server-b">server-b (208.87.135.183)</option>\n<option value="custom">Custom</option>\n</select>\n<div id="customServerGroup" style="display:none">\n<label for="customServer">Custom Server Label</label>\n<input type="text" id="customServer" name="customServer" placeholder="server-c">\n</div>\n<label for="ssh">SSH Address</label>\n<input type="text" id="ssh" name="ssh" required placeholder="user@host">\n<label for="path">Project Path</label>\n<input type="text" id="path" name="path" required placeholder="/home/aiagent/my-cool-project">\n<div id="pathError" class="error-msg"></div>\n<div class="checkbox-row"><input type="checkbox" id="hasGit" name="hasGit" checked><label for="hasGit" style="margin:0">Initialize Git repository</label></div>\n<div class="checkbox-row"><input type="checkbox" id="hasMemory" name="hasMemory" checked><label for="hasMemory" style="margin:0">Enable auto-save memory</label></div>\n<div class="checkbox-row"><input type="checkbox" id="hasRepo" name="hasRepo"><label for="hasRepo" style="margin:0">Create GitHub repository for this project</label></div>\n<div class="checkbox-row" style="margin-top:12px;padding-top:12px;border-top:1px solid #30363d;color:#3fb950"><span style="font-size:13px">Auto-registered in Project Hub</span></div>\n<button type="submit" id="sb">Create Project</button>\n</form>\n</div>\n<div id="output"></div>\n<div id="summary" class="summary"></div>\n</div>\n<script>\nvar SERVERS = {servers};\nfunction kebab(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,\'-\').replace(/^-|-$/g,\'\')}\ndocument.getElementById(\'name\').addEventListener(\'input\',function(){\nvar n=this.value.trim();var p=document.getElementById(\'path\');\nif(n)p.value=\'/home/aiagent/\'+kebab(n);\ndocument.getElementById(\'nameError\').style.display=\'none\';this.setCustomValidity(\'\')});\ndocument.getElementById(\'server\').addEventListener(\'change\',function(){\nvar c=document.getElementById(\'customServerGroup\');var s=document.getElementById(\'ssh\');\nif(this.value===\'custom\'){c.style.display=\'block\';s.value=\'\'}\nelse{c.style.display=\'none\';s.value=SERVERS[this.value]||\'\'}});\ndocument.getElementById(\'pf\').addEventListener(\'submit\',async function(e){\ne.preventDefault();\nvar btn=document.getElementById(\'sb\');var out=document.getElementById(\'output\');var sum=document.getElementById(\'summary\');\nsum.style.display=\'none\';out.style.display=\'block\';out.innerHTML=\'\';btn.disabled=true;btn.textContent=\'Creating...\';\nvar fd=new FormData(this);var p=new URLSearchParams(fd);\ntry{\nvar r=await fetch(\'create\',{method:\'POST\',headers:{\'Content-Type\':\'application/x-www-form-urlencoded\'},body:p.toString()});\nvar rd=r.body.getReader();var dec=new TextDecoder();var buf=\'\';\nwhile(true){\nvar dr=await rd.read();if(dr.done)break;\nbuf+=dec.decode(dr.value,{stream:true});\nvar lines=buf.split(\'\n\');buf=lines.pop()||\'\';\nfor(var i=0;i<lines.length;i++){var l=lines[i];\nif(l.startsWith(\'DATA:\')){\nvar d=JSON.parse(l.slice(5));\nvar dv=document.createElement(\'div\');dv.className=d.level||\'info\';dv.textContent=d.message;out.appendChild(dv);\nout.scrollTop=out.scrollHeight;\nif(d.level===\'success\'&&d.summary){\nsum.style.display=\'block\';sum.innerHTML=\'<h2>Project Created</h2><dl>\'+\nObject.entries(d.summary).map(function(kv){return\'<dt>\'+kv[0]+\'</dt><dd>\'+kv[1]+\'</dd>\'}).join(\'\')+\'</dl>\'}}}}}\ncatch(err){var dv=document.createElement(\'div\');dv.className=\'error\';dv.textContent=\'Error: \'+err.message;out.appendChild(dv)}\nfinally{btn.disabled=false;btn.textContent=\'Create Project\'}});\n</script>\n</body>\n</html>'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = FORM_HTML.replace("{servers}", json.dumps(SERVERS))
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/create":
            self.send_response(404)
            self.end_headers()
            return
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
        has_repo = params.get("hasRepo", [""])[0] == "on"
        if not name:  return self._err(400, "Project name is required")
        if not path:  return self._err(400, "Project path is required")
        if not ssh:   return self._err(400, "SSH address is required")
        if ".." in path.split("/"): return self._err(400, "Invalid path")
        if server == "custom" and custom_server:
            server = custom_server
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        def emit(level, msg, summary=None):
            d = {"level": level, "message": msg}
            if summary: d["summary"] = summary
            try:
                self.wfile.write(("DATA:" + json.dumps(d) + "\n").encode())
                self.wfile.flush()
            except: pass
        try:
            self._run(name, role, server, ssh, path, has_git, has_memory, has_repo, emit)
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            emit("error", "Failed: " + str(e) + "\n" + tb[:2000])
        emit("info", "Done.")
        try:
            self._register_in_super_memory(name, path, role, server, ssh)
        except Exception:
            pass

    def _err(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def _run(self, name, role, server, ssh, path, has_git, has_memory, has_repo, emit):
        if os.path.exists(path):
            emit("error", "Path already exists: " + path)
            return
        emit("info", "Creating project directory: " + path)
        os.makedirs(path, exist_ok=True)
        od = os.path.join(path, ".opencode")
        os.makedirs(od, exist_ok=True)
        emit("info", "Created .opencode/ directory")
        with open(os.path.join(od, "package.json"), "w") as f:
            json.dump({"dependencies": {"@opencode-ai/plugin": "1.17.9"}}, f, indent=2)
        emit("info", "Created .opencode/package.json")
        with open(os.path.join(od, "opencode.json"), "w") as f:
            json.dump({"plugin": ["superpowers@latest"]}, f, indent=2)
        emit("info", "Created .opencode/opencode.json")
        with open(os.path.join(od, ".gitignore"), "w") as f:
            f.write("node_modules\npackage.json\npackage-lock.json\nbun.lock\n.gitignore\n")
        emit("info", "Created .opencode/.gitignore")
        today = datetime.now().strftime("%Y-%m-%d")
        with open(os.path.join(od, "memory.md"), "w") as f:
            f.write("# " + name + "\n\nCreated: " + today + "\n\n## Server\n- SSH: `" + ssh + "`\n")
            if server: f.write("- Server label: `" + server + "`\n")
        emit("info", "Created .opencode/memory.md")
        with open(os.path.join(path, "AGENTS.md"), "w") as f:
            f.write("# " + name + "\n\n## Project Info\n- Role: " + (role or "TBD") + "\n- Server: " + server + "\n- SSH: " + ssh + "\n- Path: " + path + "\n\n## Memory\nThis project has a `memory/` folder for reviewed learnings and a `knowledge/` folder for domain knowledge.\nSee `../super-memory/` for cross-project memory and harness orientation.\n\n## OB1 Memory\nThis project has OB1 (Open Brain) memory available via the `ob1-memory` MCP server.\nUse `project=" + name.lower().replace(" ", "-") + "` when capturing memories.\n")
        emit("info", "Created AGENTS.md with Memory section")
        # ── Infinite Brain OS scaffolding ──
        emit("info", "Adding memory/ and knowledge/ scaffolding...")
        os.makedirs(os.path.join(path, "memory"), exist_ok=True)
        with open(os.path.join(path, "memory", "README.md"), "w") as f:
            f.write("# Memory\n\nReviewed learnings specific to this project.\nEach file is a memory node with YAML frontmatter.\n\n")
        os.makedirs(os.path.join(path, "knowledge"), exist_ok=True)
        with open(os.path.join(path, "knowledge", "README.md"), "w") as f:
            f.write("# Knowledge\n\nDomain knowledge, architecture decisions, and reference material.\n")
        os.makedirs(os.path.join(path, "_system"), exist_ok=True)
        with open(os.path.join(path, "_system", "validate.sh"), "w") as f:
            f.write("#!/usr/bin/env bash\necho \"project validate - TBD\"\n")
        os.chmod(os.path.join(path, "_system", "validate.sh"), 0o755)
        emit("success", "Created memory/, knowledge/, _system/ scaffolding")
        emit("info", "Running npm install (background)...")
        def _npm():
            try:
                r = subprocess.run(["npm","install","--no-audit","--no-fund","--loglevel=error"],
                                   cwd=od, capture_output=True, text=True, timeout=30)
                if r.returncode != 0: print("npm:", r.stderr[:200])
            except: pass
        t = threading.Thread(target=_npm, daemon=True)
        t.start()
        t.join(timeout=5)
        emit("success", "npm install started (background)")
        if has_git:
            emit("info", "Initializing git repository...")
            subprocess.run(["git","init"], cwd=path, capture_output=True, timeout=10)
            subprocess.run(["git","config","user.name","Project Wizard"], cwd=path, capture_output=True, timeout=5)
            subprocess.run(["git","config","user.email","wizard@project.local"], cwd=path, capture_output=True, timeout=5)
            gi = os.path.join(path, ".gitignore")
            if not os.path.exists(gi):
                with open(gi, "w") as f:
                    f.write("node_modules/\n.opencode/node_modules/\n.opencode/package.json\n.opencode/package-lock.json\n")
            emit("success", "Git repository initialized")
        if has_repo:
            emit("info", "Creating GitHub repository...")
            gh_token = os.environ.get("GITHUB_TOKEN", "")
            if not gh_token:
                emit("warn", "GITHUB_TOKEN not set - add to environment to enable repo creation")
            else:
                try:
                    slug = name.lower().replace(" ", "-").replace("_", "-")
                    slug = "".join(c for c in slug if c.isalnum() or c == "-")
                    headers = {"Authorization": "Bearer " + gh_token, "Accept": "application/vnd.github+json"}
                    payload = {"name": slug, "description": role or name, "private": True, "auto_init": False}
                    resp = _requests.post("https://api.github.com/user/repos", json=payload, headers=headers, timeout=15)
                    if resp.status_code in (200, 201):
                        repo_url = resp.json().get("html_url", "")
                        emit("success", "GitHub repo created: " + repo_url)
                        if has_git:
                            subprocess.run(["git","remote","add","origin",resp.json().get("clone_url","")],
                                          cwd=path, capture_output=True, timeout=10)
                            emit("info", "Added remote origin")
                    else:
                        emit("warn", "GitHub API: " + str(resp.status_code) + " " + (resp.text[:200]))
                except Exception as e:
                    emit("warn", "GitHub repo creation: " + str(e))
        emit("info", "Updating registry.json...")
        registry = {"projects": []}
        if os.path.exists(REGISTRY_FILE) and os.path.getsize(REGISTRY_FILE) > 0:
            try: registry = json.loads(open(REGISTRY_FILE).read())
            except: pass
        entry = {"name":name,"role":role or "Unknown","server":server,"path":path,"ssh":ssh,"hasGit":has_git,"hasMemory":has_memory}
        if has_repo: entry["github_repo"] = "pending"  # will be updated if created
        registry.setdefault("projects",[]).append(entry)
        with open(REGISTRY_FILE,"w") as f: json.dump(registry,f,indent=2)
        emit("success", "registry.json updated")
        emit("info", "Syncing registry to GitHub...")
        try:
            subprocess.run(["git","config","user.name","Project Wizard"], cwd=REGISTRY_DIR, capture_output=True, timeout=5)
            subprocess.run(["git","config","user.email","wizard@project.local"], cwd=REGISTRY_DIR, capture_output=True, timeout=5)
            subprocess.run(["git","add","registry.json"], cwd=REGISTRY_DIR, capture_output=True, timeout=10)
            subprocess.run(["git","commit","-m","add "+name], cwd=REGISTRY_DIR, capture_output=True, timeout=10)
            pr = subprocess.run(["git","push"], cwd=REGISTRY_DIR, capture_output=True, text=True, timeout=20)
            emit("success" if pr.returncode==0 else "warn",
                 "Registry pushed" if pr.returncode==0 else "Push: "+pr.stderr[:200])
        except subprocess.TimeoutExpired: emit("warn","Git push timed out")
        except Exception as e: emit("warn","Git push: "+str(e))
        emit("info", "Registering in Project Hub...")
        try:
            uh = ssh.split("@")[0] if "@" in ssh else ""
            hs = ssh.split("@")[1] if "@" in ssh else ""
            hub_entry = {
                "id": uuid.uuid4().hex[:12], "name": name, "description": role or "",
                "tracker_url": "", "server_host": hs, "server_port": 22,
                "ssh_user": uh, "ssh_auth_method": "key", "ssh_key_path": "/home/aiagent/.ssh/id_rsa",
                "folder_path": path, "has_tracker": False, "tracker_port": 3005,
                "archived": False, "github_repo": "", "github_branch": "main",
                "last_backup_at": "", "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(), "sort_order": 0,
                "status_values": ["not_started","in_progress","blocked","review","done"], "tasks": []
            }
            if os.path.exists(HUB_DATA_FILE):
                hd = json.loads(open(HUB_DATA_FILE).read())
                hd.setdefault("projects",[]).append(hub_entry)
                hub_entry["sort_order"] = len(hd["projects"])
                with open(HUB_DATA_FILE,"w") as f: json.dump(hd,f,indent=2)
                emit("success", "Registered in Project Hub")
            else: emit("warn", "Hub file not found")
        except Exception as e: emit("warn","Hub registration: "+str(e))
        emit("success","Project created!",summary={
            "Name":name,"Role":role or "Unknown","Server":server,
            "SSH":ssh,"Path":path,"Git":"Yes" if has_git else "No",
            "Memory":"Yes" if has_memory else "No",
            "GitHub Repo":"Yes" if has_repo else "No",
        })

    def _register_in_super_memory(self, name, path, role, server, ssh):
        try:
            slug = os.path.basename(path)
            rrd = os.path.expanduser("~/super-memory/repo-registry")
            if not os.path.isdir(rrd):
                return
            ef = os.path.join(rrd, slug + ".md")
            if os.path.exists(ef):
                return
            content = ("# Repo: " + slug + "\n\n" +
                "- repo: " + slug + "\n- path: ../" + slug + "\n- repo_kind: app\n" +
                "- primary_job: " + (role or "TBD") + "\n- status: active\n" +
                "- remote: local-only\n- added: " + datetime.now().strftime("%Y-%m-%d") + "\n" +
                "\n## Notes\nCreated by project wizard.\nServer: " + server + "\nSSH: " + ssh + "\n")
            with open(ef, "w") as f:
                f.write(content)
            try:
                for cmd in [["git","add","repo-registry/"+slug+".md"],
                            ["git","commit","-m","Register "+slug+" in repo-registry"]]:
                    subprocess.run(cmd, cwd=os.path.expanduser("~/super-memory"),
                                 capture_output=True, timeout=30)
            except Exception:
                pass
        except Exception:
            pass

if __name__ == "__main__":
    srv = HTTPServer(("0.0.0.0", PORT), Handler)
    print("Wizard on http://0.0.0.0:"+str(PORT))
    try: srv.serve_forever()
    except KeyboardInterrupt: srv.server_close()
