---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/workflows/n8n-documentation.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.834345"
}
---

# n8n Workflow Documentation
Generated: April 11, 2026
Source: tools/n8n_bridge.py

---

## Overview
n8n is configured as a workflow automation layer. The bridge runs as a webhook listener on port 7835.

---

## n8n Bridge (tools/n8n_bridge.py)

### Configuration
```python
N8N_PORT = int(os.getenv("N8N_WEBHOOK_PORT", "7835"))
N8N_BASE_URL = os.getenv("N8N_BASE_URL", f"http://127.0.0.1:{N8N_PORT}")
N8N_DATA_DIR = Path(os.path.expanduser("~/.legion/n8n"))
```

### Environment Variables
```
N8N_PORT=5678                    # Legacy port
N8N_WEBHOOK_PORT=7835           # Primary webhook port
N8N_BASE_URL=http://127.0.0.1:7835
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=
ENABLE_N8N_LISTENER=true        # Set to false to disable
ENABLE_N8N_AUTO_START=false      # Set to true to auto-start via docker
```

---

## Available Functions

### n8n_status()
```python
{"healthy": True/False, "status": 200, "base_url": "http://127.0.0.1:7835"}
```
Check if n8n webhook listener is reachable.

### start_n8n_webhook_listener()
Starts the webhook listener if `ENABLE_N8N_LISTENER=true`.
- Runs on port 7835
- Handles POST /webhook
- Logs payload and returns `{"ok": True}`

### ensure_n8n_running()
Attempts to start local n8n via `docker compose up -d n8n`.
- Only if `ENABLE_N8N_AUTO_START=true`
- Returns `{started: True/False, reason/returncode/error}`

---

## Workflows Status
**Current state**: n8n bridge exists but no documented workflows yet.
The webhook listener is active and ready to receive triggers.

### What Could Be Automated
- rumahlabuh.com booking → WhatsApp notification
- New tenant signup → welcome message
- Payment received → confirmation
- Monthly report generation

---

## Related Wiki Files
- `.wiki/projects/rumahlabuh-architecture.md` — rumahlabuh.com context
- `.wiki/profiles/BASHARA-MASTER-PROFILE.md` — business context
