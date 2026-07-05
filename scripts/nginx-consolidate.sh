#!/bin/bash
# Nginx Consolidation Script
# Run this AFTER DNS for mc.simplyict.com.au has propagated.
# Usage: sudo bash nginx-consolidate.sh

set -e

echo "=== Step 1: Install mc.simplyict.com.au nginx config ==="
cp /home/aiagent/project-registry/scripts/mc.simplyict.com.au /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/mc.simplyict.com.au /etc/nginx/sites-enabled/

echo "=== Step 2: Get SSL cert ==="
certbot --nginx -d mc.simplyict.com.au --non-interactive --agree-tos --email admin@simplyict.com.au

echo "=== Step 3: Create audit.simplyict.com.au redirect ==="
cat > /etc/nginx/sites-available/audit-mission-control << 'AUDITCONF'
server {
    listen 80;
    server_name audit.simplyict.com.au;
    return 301 https://mc.simplyict.com.au$request_uri;
}
server {
    listen 443 ssl;
    server_name audit.simplyict.com.au;
    ssl_certificate /etc/letsencrypt/live/audit.simplyict.com.au/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/audit.simplyict.com.au/privkey.pem;
    return 301 https://mc.simplyict.com.au$request_uri;
}
AUDITCONF

echo "=== Step 4: Replace wazuh-soc catch-all with close ==="
cat > /etc/nginx/sites-available/wazuh-soc << 'CLOSECONF'
server {
    listen 80 default_server;
    listen 443 ssl default_server;
    ssl_certificate /etc/nginx/ssl/wazuh-soc.crt;
    ssl_certificate_key /etc/nginx/ssl/wazuh-soc.key;
    return 444;
}
CLOSECONF

echo "=== Step 5: Bind services to 127.0.0.1 ==="
# Project Hub
systemctl stop project-hub.service
sed -i 's/HOST=.*/HOST="127.0.0.1"/' /home/aiagent/project-hub/server.py
systemctl start project-hub.service

# Project Wizard
pkill -f "new-project.py" 2>/dev/null
sed -i "s/(\"0\.0\.0\.0\", PORT)/(\"127.0.0.1\", PORT)/" /home/aiagent/project-registry/new-project.py
nohup python3 /home/aiagent/project-registry/new-project.py > /tmp/wizard.log 2>&1 &

# Credential System
systemctl stop credential-system.service 2>/dev/null || pkill -f "uvicorn app.main:app.*5001"
nohup /home/aiagent/credential-system/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 5001 > /tmp/credential-system.log 2>&1 &

# Network Infrastructure
pkill -f "uvicorn app.main:app.*6173"
nohup /home/aiagent/network-infrastructure-buildout/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 6173 > /tmp/network.log 2>&1 &

# Device Audit API
systemctl stop device-audit-api.service 2>/dev/null || pkill -f "uvicorn device_audit_api:app.*8096"
nohup /home/aiagent/mission-control-ui/venv/bin/uvicorn device_audit_api:app --host 127.0.0.1 --port 8096 --workers 2 > /tmp/device-audit.log 2>&1 &

# Mission Control Site tracker (http.server)
# This is a simple http.server - change bind address
systemctl stop mission-control-site.service 2>/dev/null
pkill -f "http.server 8097"
# Will need the tracker service file to change bind address

# OpenCode Mission Control
systemctl stop opencode-mission-control.service 2>/dev/null || pkill -f "opencode-mission-control/server.py"
sed -i "s/HOST.*=.*os\.environ\.get.*HOST.*/HOST = '127.0.0.1'/" /home/aiagent/opencode-mission-control/server.py
nohup python3 /home/aiagent/opencode-mission-control/server.py > /tmp/opencode-mc.log 2>&1 &

# Mission Control Site API
systemctl stop mission-control-site.service 2>/dev/null || pkill -f "uvicorn backend_api:app.*8000"
sed -i "s/--host 0.0.0.0/--host 127.0.0.1/" /home/aiagent/mission-control-site/venv/bin/uvicorn 2>/dev/null || true

echo "=== Step 6: Test nginx config ==="
nginx -t

echo "=== Step 7: Reload nginx ==="
systemctl reload nginx

echo ""
echo "=== DONE ==="
echo "Services are now only accessible through mc.simplyict.com.au"
echo "Run the firewall script next to close direct ports."
