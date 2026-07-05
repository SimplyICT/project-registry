#!/bin/bash
# Lock down firewall: only allow SSH (22), HTTP (80), HTTPS (443), Cockpit (9090)
# Run as root: sudo bash firewall-lockdown.sh

set -e

echo "=== Applying firewall rules ==="

# Reset
ufw --force reset

# Default deny
ufw default deny incoming
ufw default allow outgoing

# Allow specific ports
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 9090/tcp comment 'Cockpit'

# Enable
ufw --force enable

echo ""
echo "=== Firewall active ==="
echo "Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 9090 (Cockpit)"
echo "All other inbound ports blocked."
ufw status verbose
