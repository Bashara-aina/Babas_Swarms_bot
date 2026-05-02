# browser-harness install

Use this file only for first-time install, reconnect, or cold-start browser bootstrap. For day-to-day browser work, read `SKILL.md`.

## Quick setup

Chrome must have remote debugging enabled. The checkbox is per-profile sticky — if it was ever ticked on a profile, just launching Chrome is enough.

1. **Enable Chrome remote debugging:**
   - Open `chrome://inspect/#remote-debugging`
   - Tick "Discover network targets"
   - Click Allow if prompted

2. **Verify connection:**
   ```bash
   python3 -m tools.browser_harness.run --doctor
   ```

3. **Test with a simple page:**
   ```bash
   python3 -c "
   from tools.browser_harness.admin import ensure_daemon
   from tools.browser_harness.helpers import goto_url, page_info, wait_for_load
   ensure_daemon()
   new_tab('https://example.com')
   wait_for_load()
   print(page_info())
   "
   ```

## Architecture

```
Chrome (local or Browser Use cloud) -> CDP WS -> daemon.py -> /tmp/bu-<NAME>.sock -> helpers.py
```

- Protocol is one JSON line each way over Unix socket.
- `BU_NAME` namespaces socket, pid, and log files.
- `BU_CDP_WS` overrides local Chrome discovery for remote browsers.
- `BROWSER_USE_API_KEY` enables cloud browser support.

## Environment variables

```
BU_NAME=default           # daemon namespace (socket, pid, log)
BU_CDP_WS=                # override: direct CDP WebSocket URL (for remote browsers)
BU_CDP_URL=               # override: HTTP DevTools endpoint (auto-resolves to WS)
BU_BROWSER_ID=            # Browser Use cloud browser ID (set automatically by start_remote_daemon)
BROWSER_USE_API_KEY=      # Browser Use cloud API key (get from cloud.browser-use.com)
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `DevToolsActivePort not found` | Open `chrome://inspect/#remote-debugging`, tick checkbox, click Allow |
| `DevTools not live yet` | Chrome is starting up — wait up to 30s, don't restart |
| `connection refused` after Chrome is running | Remote debugging checkbox not ticked on this profile |
| stale websocket | Run `restart_daemon()` then retry |
| profile picker shown | Choose your normal Chrome profile, then retry |

## Daemon management

```python
from tools.browser_harness.admin import (
    ensure_daemon,      # idempotent start
    daemon_alive,       # check alive
    restart_daemon,     # stop
    run_setup,          # interactive attach
    run_doctor,         # diagnostics
)
```

## Remote browsers

For sub-agents or headless servers, use Browser Use cloud browsers:

```python
from tools.browser_harness.admin import start_remote_daemon, stop_remote_daemon

# Start cloud browser
browser = start_remote_daemon("work")  # returns {id, cdpUrl, liveUrl}
# liveUrl is auto-opened in local browser if GUI detected

# Use with BU_NAME
# BU_NAME=work python3 -c "..."
```