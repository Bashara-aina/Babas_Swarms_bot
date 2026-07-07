#!/bin/bash
# =============================================================================
# legion-system-check.sh — Comprehensive end-to-end system verification
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
BOT_DIR="/home/newadmin/swarm-bot"
PASS=0; FAIL=0; WARN=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo "══════════════════════════════════════════════════════════════"
echo "  Legion Swarm-bot — Comprehensive System Check"
echo "══════════════════════════════════════════════════════════════"

# ── L1 Memory (tools/memory.py → ChromaDB via mem0) ─────────
echo ""
echo "═══ L1 Memory ═══"
L1=$(python3 -c "
import asyncio, sys
sys.path.insert(0, '$BOT_DIR')
from tools.memory import add_memory, search_memory
async def t():
    await add_memory('syscheck L1 - chartreuse chameleon', tags=['syscheck'], source='check')
    r = await search_memory('chartreuse chameleon', top_k=5)
    return len(r)
n = asyncio.run(t())
print('PASS' if n >= 1 else 'FAIL')
" 2>&1 | grep -E '^PASS$|^FAIL$')
echo -n "L1 Memory: "; eval "$L1" || fail "L1 Memory: FAIL"

# ── L2 Memory (tools/mem0_client → Mem0 → ChromaDB) ─────────
echo ""
echo "═══ L2 Memory (Mem0 + ChromaDB) ═══"
L2=$(python3 -c "
import asyncio, sys
sys.path.insert(0, '$BOT_DIR')
from tools.mem0_client import mem0_add, mem0_search
async def t():
    await mem0_add('syscheck', 'syscheck L2 - chartreuse chameleon')
    r = await mem0_search('syscheck', 'chartreuse chameleon', limit=5)
    return len(r)
n = asyncio.run(t())
print('PASS' if n >= 1 else 'FAIL')
" 2>&1 | grep -E '^PASS$|^FAIL$')
echo -n "L2 Memory: "; eval "$L2" || fail "L2 Memory: FAIL"

# ── L3 Memory (core.memory.store → ChromaDB) ────────────────
echo ""
echo "═══ L3 Memory (MemoryStore) ═══"
L3=$(python3 -c "
import sys
sys.path.insert(0, '$BOT_DIR')
from core.memory.store import MemoryStore
store = MemoryStore()
s = store.status()
print('PASS' if s.get('status') == 'healthy' else 'FAIL')
" 2>&1 | grep -E '^PASS$|^FAIL$')
echo -n "L3 Memory: "; eval "$L3" || fail "L3 Memory: FAIL"

# ── LiteLLM Proxy ─────────────────────────────────────────────
echo ""
echo "═══ LiteLLM Proxy (:4001) ═══"
if curl -s --max-time 3 http://localhost:4001/health 2>/dev/null | python3 -c "import sys,json; json.load(sys.stdin); print('PASS')" 2>/dev/null; then
    pass "LiteLLM Proxy: responding"
else
    fail "LiteLLM Proxy: not responding"
fi

# ── Ollama ──────────────────────────────────────────────────
echo ""
echo "═══ Ollama (Embeddings) ═══"
OLLAMA=$(curl -s --max-time 3 http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); models=d.get('models',[]); print(f'PASS ({len(models)} models)' if models else 'WARN (0 models)')" 2>/dev/null || echo "FAIL")
if [[ "$OLLAMA" == PASS* ]]; then
    pass "Ollama: $OLLAMA"
elif [[ "$OLLAMA" == WARN* ]]; then
    warn "Ollama: $OLLAMA"
else
    fail "Ollama: not responding"
fi

# ── OpenCode ─────────────────────────────────────────────────
echo ""
echo "═══ OpenCode Agent ═══"
if pgrep -f "opencode" &>/dev/null; then
    OC_PID=$(pgrep -f opencode | head -1)
    pass "OpenCode: running (PID $OC_PID)"
else
    fail "OpenCode: not running"
fi

# ── MCP Servers ─────────────────────────────────────────────
echo ""
echo "═══ MCP Servers (via opencode mcp list) ═══"
MCP_OUTPUT=$(opencode mcp list 2>/dev/null)
CONNECTED=$(echo "$MCP_OUTPUT" | grep -c "✓" || echo "0")
TOTAL=$(echo "$MCP_OUTPUT" | grep -c "●" || echo "0")
echo "$MCP_OUTPUT" | grep -E "^●" | while read -r line; do
    if echo "$line" | grep -q "✓"; then
        NAME=$(echo "$line" | awk '{print $2}')
        pass "  MCP $NAME: connected"
    else
        NAME=$(echo "$line" | awk '{print $2}')
        warn "  MCP $NAME: not connected"
    fi
done

# ── Telegram Bot ─────────────────────────────────────────────
echo ""
echo "═══ Telegram Bot (main.py) ═══"
if pgrep -f "python.*main.py" &>/dev/null; then
    pass "Telegram Bot: running"
else
    fail "Telegram Bot: not running"
fi

# ── ChromaDB ─────────────────────────────────────────────────
echo ""
echo "═══ ChromaDB Storage ═══"
if [ -d "$HOME/.legion/mem0_chroma" ]; then
    pass "ChromaDB storage: $HOME/.legion/mem0_chroma"
else
    fail "ChromaDB storage: not found"
fi

# ── Session memory (Obsidian wiki) ─────────────────────────
echo ""
echo "═══ Obsidian Wiki ═══"
if [ -d "$BOT_DIR/.wiki" ]; then
    DOCS=$(find "$BOT_DIR/.wiki" -name "*.md" 2>/dev/null | wc -l)
    pass "Obsidian Wiki: $DOCS documents"
else
    warn "Obsidian Wiki: not found"
fi

# ── Summary ──────────────────────────────────────────────────
TOTAL_CHECKS=$((PASS + FAIL + WARN))
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  System Check Summary"
echo "══════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}PASS:${NC} $PASS   ${RED}FAIL:${NC} $FAIL   ${YELLOW}WARN:${NC} $WARN"
echo ""
if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
    echo -e "  ${GREEN}✓ ALL SYSTEMS OPERATIONAL${NC}"
elif [ "$FAIL" -eq 0 ]; then
    echo -e "  ${YELLOW}⚠ OPERATIONAL WITH WARNINGS${NC}"
else
    echo -e "  ${RED}✗ SOME SYSTEMS FAILED${NC}"
fi
echo "══════════════════════════════════════════════════════════════"
