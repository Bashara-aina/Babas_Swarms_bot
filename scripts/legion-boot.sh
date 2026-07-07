#!/bin/bash
# =============================================================================
# legion-boot.sh — Full system boot for Swarm-bot
# Auto-starts: OpenCode + all MCP servers + memory stack + optional Telegram bot
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
LOG_FILE="${HOME}/.legion/boot.log"
BOT_DIR="/home/newadmin/swarm-bot"
mkdir -p "$(dirname "$LOG_FILE")"

log()  { echo -e "${BLUE}[BOOT]${NC} $(date '+%H:%M:%S') $1" | tee -a "$LOG_FILE"; }
pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

log "══════════════════════════════════════════════════════════════"
log "  Legion Swarm-bot Boot Sequence"
log "══════════════════════════════════════════════════════════════"

# ── 1. System readiness ────────────────────────────────────────
log ""
log "═══ System Checks ═══"
if command -v python3 &>/dev/null; then
    pass "Python3: $(python3 --version | awk '{print $2}')"
else
    fail "Python3 not found"; exit 1
fi

if command -v ollama &>/dev/null; then
    OLLAMA_STATUS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'running ({len(d.get(\"models\",[]))} models)')" 2>/dev/null || echo "not responding")
    pass "Ollama: $OLLAMA_STATUS"
else
    warn "Ollama CLI not in PATH (may still be running as service)"
fi

# ── 2. ChromaDB check ────────────────────────────────────────────
log ""
log "═══ ChromaDB / Mem0 ═══"
CHROMA_DIR="${HOME}/.legion/mem0_chroma"
if [ -d "$CHROMA_DIR" ]; then
    pass "ChromaDB storage: $CHROMA_DIR"
else
    mkdir -p "$CHROMA_DIR"
    pass "ChromaDB storage created: $CHROMA_DIR"
fi

# ── 3. Memory health check (L1 + L2) ───────────────────────────
log ""
log "═══ Memory Stack ═══"
MEM_HEALTH=$(python3 -c "
import asyncio, sys
sys.path.insert(0, '$BOT_DIR')
from tools.memory import add_memory, search_memory
from tools.mem0_client import mem0_add, mem0_search

async def check():
    try:
        await add_memory('boot-check L1 - zagreb zebra', tags=['boot'], source='check')
        l1 = await search_memory('zagreb zebra', top_k=3)
        if len(l1) < 1:
            return 'L1_FAIL'
        await mem0_add('boot_user', 'boot-check L2 - zagreb zebra')
        l2 = await mem0_search('boot_user', 'zagreb zebra', limit=3)
        if len(l2) < 1:
            return 'L2_FAIL'
        return 'OK'
    except Exception as e:
        return f'ERR:{e}'

print(asyncio.run(check()))
" 2>&1 | grep -E 'OK|L1_FAIL|L2_FAIL|ERR:' | tail -1)

if [ "$MEM_HEALTH" = "OK" ]; then
    pass "Memory stack: L1 + L2 + ChromaDB operational"
else
    fail "Memory stack: $MEM_HEALTH"
fi

# ── 4. Ollama embeddings check ─────────────────────────────────
log ""
log "═══ Embeddings ═══"
EMBED_HEALTH=$(python3 -c "
import sys
sys.path.insert(0, '$BOT_DIR')
try:
    from core.memory.store import MemoryStore
    store = MemoryStore()
    status = store.status()
    if status.get('status') == 'healthy':
        print('OK')
    else:
        print(f'UNHEALTHY: {status}')
except Exception as e:
    print(f'ERR: {e}')
" 2>&1 | grep -E '^OK$|^ERR:|^UNHEALTHY' | tail -1)

if [ "$EMBED_HEALTH" = "OK" ]; then
    pass "Embeddings (nomic-embed-text via Ollama): operational"
else
    warn "Embeddings: $EMBED_HEALTH"
fi

# ── 5. LiteLLM Proxy ────────────────────────────────────────────
log ""
log "═══ LiteLLM Proxy ═══"
if curl -s --max-time 3 http://localhost:4001/health 2>/dev/null | python3 -c "import sys,json; json.load(sys.stdin); print('OK')" 2>/dev/null; then
    pass "LiteLLM proxy: responding on :4001"
else
    warn "LiteLLM proxy: not responding on :4001 (may need manual start)"
fi

# ── 6. OpenCode check ──────────────────────────────────────────
log ""
log "═══ OpenCode ═══"
if pgrep -f "opencode" &>/dev/null; then
    pass "OpenCode: already running (PID $(pgrep -f opencode | head -1))"
else
    log "OpenCode: not running — starting..."
    cd "$BOT_DIR"
    nohup opencode --dir "$BOT_DIR" > "$LOG_FILE" 2>&1 &
    sleep 3
    if pgrep -f "opencode" &>/dev/null; then
        pass "OpenCode: started (PID $(pgrep -f opencode | head -1))"
    else
        warn "OpenCode: may have failed to start — check $LOG_FILE"
    fi
fi

# ── 7. MCP Servers ─────────────────────────────────────────────
log ""
log "═══ MCP Servers ═══"
MCP_PIDS=""
for name in gitnexus browser-use crawl4ai hermes; do
    if pgrep -f "$name" &>/dev/null; then
        pass "MCP $name: running"
    else
        warn "MCP $name: not running"
    fi
done

# ── 8. SearXNG Metasearch ────────────────────────────────────
log ""
log "═══ SearXNG ═══"
if curl -s --max-time 2 http://127.0.0.1:8888/search?q=health 2>/dev/null | python3 -c "import sys,json; json.load(sys.stdin); print('OK')" 2>/dev/null; then
    pass "SearXNG: responding on :8888"
else
    log "SearXNG: not running — starting via systemd..."
    systemctl --user start searxng.service
    sleep 5
    if curl -s --max-time 2 http://127.0.0.1:8888/search?q=health 2>/dev/null | python3 -c "import sys,json; json.load(sys.stdin); print('OK')" 2>/dev/null; then
        pass "SearXNG: started on :8888"
    else
        warn "SearXNG: failed to start — check 'journalctl --user -u searxng.service'"
    fi
fi

# ── 9. Telegram bot ───────────────────────────────────────────
log ""
log "═══ Telegram Bot (main.py) ═══"
if pgrep -f "python.*main.py|python.*mini-swe" &>/dev/null; then
    pass "Telegram bot: running (PID $(pgrep -f 'python.*main.py' | head -1))"
else
    warn "Telegram bot: not running — starting..."
    cd "$BOT_DIR"
    nohup python3 main.py > ~/.legion/bot.log 2>&1 &
    sleep 8
    if pgrep -f "python.*main.py" &>/dev/null; then
        pass "Telegram bot: started (PID $(pgrep -f 'python.*main.py' | head -1))"
    else
        fail "Telegram bot: failed to start — check ~/.legion/bot.log"
    fi
fi

# ── Summary ────────────────────────────────────────────────────
log ""
log "══════════════════════════════════════════════════════════════"
log "  Boot Complete — $(date)"
log "══════════════════════════════════════════════════════════════"
log "  Full log: $LOG_FILE"
log "  Health check: bash $BOT_DIR/scripts/health_check.sh"
log "══════════════════════════════════════════════════════════════"
