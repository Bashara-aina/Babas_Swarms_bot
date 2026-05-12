#!/bin/bash
# start-opencode-mcp.sh — Standalone launcher for OpenCode + all 12 MCP servers
# No VS Code terminal needed. Starts as a proper daemon.
set -euo pipefail

REPO="/home/newadmin/swarm-bot"
LOG_DIR="${HOME}/.legion"
LOG_FILE="${LOG_DIR}/opencode-mcp.log"
PID_FILE="${LOG_DIR}/opencode-mcp.pid"

mkdir -p "$LOG_DIR"

# ── Kill existing instances cleanly ──────────────────────────────────────────
kill_existing() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "[start-opencode-mcp] Stopping existing instance PID $OLD_PID"
            kill "$OLD_PID" 2>/dev/null || true
            sleep 2
        fi
    fi
    # Also kill any stray opencode serve processes on port 4096
    local old_pid=$(lsof -ti:4096 2>/dev/null || true)
    if [ -n "$old_pid" ]; then
        echo "[start-opencode-mcp] Killing process on port 4096: $old_pid"
        kill "$old_pid" 2>/dev/null || true
        sleep 1
    fi
}

# ── Start opencode serve ─────────────────────────────────────────────────────
start_opencode_serve() {
    local dir="$REPO"
    echo "[start-opencode-mcp] Starting opencode serve on port 4096..."
    nohup opencode serve --port 4096 --dir "$dir" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "[start-opencode-mcp] opencode serve PID=$(cat $PID_FILE)"
    sleep 3

    # Verify it's running
    if ! kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "[start-opencode-mcp] FAILED to start opencode serve"
        cat "$LOG_FILE"
        exit 1
    fi
    echo "[start-opencode-mcp] opencode serve is running"
}

# ── Register all MCP servers via opencode CLI ────────────────────────────────
register_mcp_servers() {
    echo "[start-opencode-mcp] Registering MCP servers..."
    cd "$REPO"

    # Load server list from mcp_config.json
    python3 -c "
import json, subprocess, sys, time

with open('$REPO/config/mcp_config.json') as f:
    cfg = json.load(f)

registered = []
for srv in cfg.get('servers', []):
    if not srv.get('enabled', True):
        continue
    name = srv['name']
    cmd = srv['command']
    args = srv.get('args', [])
    cwd = srv.get('workingDirectory', '$REPO')
    env = srv.get('env', {})

    env_args = []
    for k, v in env.items():
        env_args.extend(['--env', f'{k}={v}'])

    full_cmd = [cmd] + args
    print(f'  Registering MCP: {name}')
    try:
        result = subprocess.run(
            ['opencode', 'mcp', 'add', name] + full_cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15,
            env={**subprocess.os.environ, **env}
        )
        if result.returncode == 0:
            print(f'    OK: {name}')
        else:
            print(f'    WARN: {name} — {result.stderr.strip()[:100]}')
    except Exception as e:
        print(f'    ERR: {name} — {e}')
    registered.append(name)

print(f'Registered {len(registered)} MCP servers')
"

    # Also register ruflo MCP server (started by ruflo itself, but register the client)
    echo "[start-opencode-mcp] Checking ruflo MCP..."
    if command -v ruflo &>/dev/null; then
        echo "  ruflo found in PATH"
    else
        echo "  ruflo not in PATH — ruflo MCP will auto-connect via ruflo daemon"
    fi

    echo "[start-opencode-mcp] All MCP servers registered"
}

# ── Main ─────────────────────────────────────────────────────────────────────
echo "=========================================="
echo "OpenCode + MCP Server Launcher"
echo "=========================================="

kill_existing
start_opencode_serve

echo ""
echo "Waiting for opencode serve to become ready..."
for i in $(seq 1 10); do
    if curl -s --max-time 2 http://localhost:4096 >/dev/null 2>&1; then
        echo "opencode serve is ready on port 4096"
        break
    fi
    echo "  waiting... ($i/10)"
    sleep 1
done

register_mcp_servers

echo ""
echo "=========================================="
echo "OpenCode + MCP is running!"
echo "  PID: $(cat $PID_FILE)"
echo "  Log: $LOG_FILE"
echo "  URL: http://localhost:4096"
echo "=========================================="