# Nginx Reverse Proxy Consolidation

**Date:** 2026-06-23
**Status:** Design (pre-implementation)
**Goal:** Single nginx gateway (mc.simplyict.com.au) for all internal services, close all direct port exposures except SSH (22), HTTP (80), HTTPS (443), and Cockpit (9090).

## Current State

14 services running on the server. 3 already behind nginx (audit.simplyict.com.au, pwa.simplyclik.com, IP catch-all). 11 exposed directly on 0.0.0.0 with no firewall.

| Port | Service | Currently | Target |
|------|---------|-----------|--------|
| 22 | SSH | Open | Open |
| 80 | nginx HTTP | Open | Open |
| 443 | nginx HTTPS | Open | Open |
| 9090 | Cockpit | Direct | Open (by requirement) |
| 3001-3004 | SimplyClik backends | Direct + nginx | nginx only |
| 3010 | Project Hub | Direct | nginx only |
| 5001 | Credential System | Direct + stale nginx | nginx only |
| 6173 | Network Infrastructure | Direct | nginx only |
| 8000 | MC Site API | Direct | nginx only |
| 8095 | MC UI app | nginx only | nginx only |
| 8096 | Device Audit API | Direct | nginx only |
| 8097 | MC Site tracker | Direct | nginx only |
| 51999 | OpenCode MC Dashboard | Direct | nginx only |
| 61738 | Project Wizard | Direct | nginx only |

## Design

### 1. DNS

Point `mc.simplyict.com.au` A record to `208.87.135.84`.

### 2. Nginx Server Blocks

**`mc.simplyict.com.au`** — single server block with path-based proxying:

| Path | Upstream | Notes |
|------|----------|-------|
| `/` | `127.0.0.1:8095` | Mission Control UI (existing, move from audit) |
| `/hub/` | `127.0.0.1:3010` | Project Hub |
| `/credentials/` | `127.0.0.1:5001` | Credential System |
| `/network/` | `127.0.0.1:6173` | Network Infrastructure |
| `/devices/` | `127.0.0.1:8096` | Device Audit API |
| `/tracker/` | `127.0.0.1:8097` | MC Site tracker |
| `/mc/` | `127.0.0.1:51999` | OpenCode Mission Control |
| `/wizard/` | `127.0.0.1:61738` | Project Wizard |
| `/api/` | `127.0.0.1:8000` | MC Site API |

**`audit.simplyict.com.au`** — redirect (301) to mc.simplyict.com.au to preserve bookmarks.

**`pwa.simplyclik.com`** — unchanged, stays separate (client-facing).

**IP catch-all (wazuh-soc config)** — replace with 444 (close), since credential-system moves to mc.

### 3. Service Binding Changes

Every service changed from `--host 0.0.0.0` to `--host 127.0.0.1` (or equivalent bind address change). This requires service restarts.

### 4. SSL / Certificates

All paths under mc.simplyict.com.au use a single Let's Encrypt cert for `mc.simplyict.com.au`. `audit` gets replaced by a 301 redirect. The wazuh-soc self-signed cert is retired.

### 5. Firewall

UFW or iptables allowing only:
- 22/tcp (SSH)
- 80/tcp (HTTP)
- 443/tcp (HTTPS)
- 9090/tcp (Cockpit)

### 6. App-Level Path Awareness

Path-based routing means internal apps may need to know their path prefix for correct link generation. For example, Project Hub's login redirect and static asset paths must work under `/hub/`. Each app will be tested after deployment and adjusted if needed (base URL config, reverse-proxy headers).

## Implementation Order

1. Point `mc.simplyict.com.au` DNS
2. Get Let's Encrypt cert for mc.simplyict.com.au
3. Nginx server block for mc with all paths
4. Change each service from 0.0.0.0 to 127.0.0.1 (one at a time, test each)
5. Redirect audit.simplyict.com.au → mc.simplyict.com.au
6. Remove IP catch-all nginx block
7. Apply firewall rules
8. End-to-end testing of all routes

## Rollback

- Keep old nginx configs backed up in `/etc/nginx/sites-available/`
- Each service restart is reversible (change bind back to 0.0.0.0)
- Firewall can be disabled with `ufw disable`
