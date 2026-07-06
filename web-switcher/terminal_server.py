#!/usr/bin/env python3
"""WebSocket terminal server — provides browser-based SSH/local shell sessions."""
import asyncio, json, os, pty, signal, struct, fcntl, termios, subprocess
from pathlib import Path

import websockets

REGISTRY_FILE = Path(__file__).resolve().parent.parent / "registry.json"
TERMINAL_PORT = int(os.environ.get("TERMINAL_PORT", "8766"))

SERVERS = {"84": "aiagent@208.87.135.84", "183": "aiagent@208.87.135.183"}

def load_registry():
    with open(REGISTRY_FILE) as f:
        return json.load(f)

def find_project(projects, name):
    for p in projects:
        if p["name"] == name:
            return p
    for p in projects:
        if name.lower() in p["name"].lower():
            return p
    return None

def get_ssh(project):
    if project.get("ssh"):
        return project["ssh"]
    server = str(project.get("server", ""))
    for key in ("84", "183"):
        if key in server:
            return SERVERS[key]
    return ""

def build_cmd(project):
    """Build the shell command to run for this project."""
    same = get_ssh(project) == SERVERS.get("84") or not get_ssh(project)
    if same:
        return ["/bin/bash", "-c", f"cd {project['path']} && exec $SHELL -l"]
    else:
        ssh = get_ssh(project)
        return ["ssh", "-t", ssh, f"cd {project['path']} && exec $SHELL -l"]

def set_winsize(fd, cols, rows):
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

async def terminal_handler(websocket):
    """Handle a WebSocket terminal session."""
    try:
        msg = await asyncio.wait_for(websocket.recv(), timeout=10)
    except asyncio.TimeoutError:
        await websocket.close(4000, "Timeout waiting for project info")
        return

    try:
        info = json.loads(msg)
    except json.JSONDecodeError:
        await websocket.close(4000, "Invalid project info")
        return

    name = info.get("name", "")
    registry = load_registry()
    project = find_project(registry.get("projects", []), name)
    if not project:
        await websocket.close(4004, f"Project '{name}' not found")
        return

    cmd = build_cmd(project)
    cols = info.get("cols", 80)
    rows = info.get("rows", 24)

    # Open PTY
    master_fd, slave_fd = pty.openpty()
    set_winsize(master_fd, cols, rows)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=os.setsid,
        close_fds=True,
    )
    os.close(slave_fd)

    stopped = False

    async def read_pty():
        nonlocal stopped
        loop = asyncio.get_event_loop()
        while not stopped:
            try:
                data = await loop.run_in_executor(None, os.read, master_fd, 65536)
                if not data:
                    break
                await websocket.send(data)
            except (BrokenPipeError, OSError, ConnectionError):
                break
        stopped = True

    async def write_pty():
        nonlocal stopped
        try:
            async for message in websocket:
                if stopped:
                    break
                if isinstance(message, str):
                    if message.startswith("resize:"):
                        parts = message[7:].split(",")
                        if len(parts) == 2:
                            try:
                                c, r = int(parts[0]), int(parts[1])
                                set_winsize(master_fd, c, r)
                            except ValueError:
                                pass
                    else:
                        os.write(master_fd, message.encode())
                else:
                    os.write(master_fd, message)
        except (ConnectionError, OSError):
            pass
        stopped = True

    await asyncio.gather(read_pty(), write_pty())

    # Cleanup
    try:
        os.close(master_fd)
    except OSError:
        pass
    if proc.returncode is None:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=3)
        except asyncio.TimeoutError:
            proc.kill()

async def main():
    print(f"Terminal server on ws://0.0.0.0:{TERMINAL_PORT}")
    async with websockets.serve(terminal_handler, "0.0.0.0", TERMINAL_PORT,
                                ping_interval=30, ping_timeout=10):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
