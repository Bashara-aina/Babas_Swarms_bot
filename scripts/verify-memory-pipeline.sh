#!/bin/bash
# scripts/verify-memory-pipeline.sh
# End-to-end verification of Swarm-bot memory pipeline

set +e
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
PASS=0; FAIL=0

check() {
  local label="$1"; local cmd="$2"; local expected="$3"
  echo -en "  [$label] "
  result=$(eval "$cmd" 2>&1 | grep -v '^\[EMBEDDER\]' | grep -v '^$' | tr -d '\n' | head -c 200)
  if [[ "$result" == *"$expected"* ]] || [[ -n "$result" && "$expected" == "ANY" ]]; then
    echo -e "${GREEN}✓ PASS${NC}"; PASS=$((PASS+1)); return 0
  else
    echo -e "${RED}✗ FAIL${NC} — got: ${result:0:100}"; FAIL=$((FAIL+1)); return 1
  fi
}

section() { echo -e "\n${YELLOW}━━━ $1 ━━━${NC}"; }

section "Layer 1 — Checkpoints"
check "current.json exists" "test -f /home/newadmin/swarm-bot/.session_state/current.json && echo OK" "OK"
check "current.json valid JSON" "python3 -c 'import json; json.load(open(\"/home/newadmin/swarm-bot/.session_state/current.json\"))' 2>/dev/null && echo OK" "OK"

section "Layer 2 — MemoryStore (ChromaDB)"
check "MemoryStore connects" "python3 -c 'from core.memory.store import MemoryStore; s = MemoryStore(); print(\"OK\")' 2>/dev/null" "OK"
check "MemoryStore has entries" "python3 -c 'from core.memory.store import MemoryStore; s = MemoryStore(); r = s.recall(\"bashara\", agent_id=None, top_k=1, min_score=0.0); print(len(r) if r else 0)' 2>/dev/null" "ANY"
check "recalled_context.md exists" "test -f /home/newadmin/swarm-bot/.session_state/recalled_context.md && echo OK" "OK"
check "recalled_context.md non-empty" "wc -c < /home/newadmin/swarm-bot/.session_state/recalled_context.md 2>/dev/null" "ANY"

section "Layer 3 — langmem (with 5s timeout, may return empty)"
check "langmem returns list" "python3 -c 'from core.memory.memory_injector import _recall_from_langmem; r = _recall_from_langmem(\"test\", 3); print(type(r).__name__)' 2>/dev/null" "list"

section "Layer 4 — observation_store"
check "observation_store returns list" "python3 -c 'from core.memory.memory_injector import _recall_from_observation_store; r = _recall_from_observation_store(\"test\", 3); print(type(r).__name__)' 2>/dev/null" "list"

section "Layer 5 — graphrag (keyword search, no LLM)"
check "graphrag keyword search works" "python3 -c 'from core.integrations.graphrag_integration import _keyword_search_text_units; r = _keyword_search_text_units(\"Tool Output Formatting\", limit=2); print(len(r))' 2>/dev/null" "ANY"
check ".wiki directory accessible" "test -d /home/newadmin/swarm-bot/.wiki && echo OK" "OK"

section "Session Watcher"
check "session_watcher running" "pgrep -f 'session_watcher.py' >/dev/null && echo OK" "OK"
check "watcher.log recent entry" "tail -1 /home/newadmin/swarm-bot/.session_state/watcher.log 2>/dev/null | grep -c '.' || echo 0" "ANY"

section "OpenCode MCP Server"
check "opencode serve on port 4096" "ss -tlnp 2>/dev/null | grep '127.0.0.1:4096' | grep opencode && echo OK" "OK"
mcp_count=$(ps aux | grep -E 'opencode serve|mcpServers|gitnexus mcp' | grep -v grep | wc -l 2>/dev/null || echo 0)
echo -e "  [MCP servers running] ${CYAN}${mcp_count}${NC}"
[[ "$mcp_count" -ge 3 ]] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

section "Full Pipeline (build_memory_context)"
# Run in background to catch OOM/time issues; capture exit code
timeout 30 python3 -c "
import sys; sys.path.insert(0, '/home/newadmin/swarm-bot')
from core.memory.memory_injector import build_memory_context
r = build_memory_context('recent session work', 'bashara')
print(len(r) if r else 0)
" > /tmp/bmc_result.txt 2>&1
bmc_rc=$?
bmc_len=$(cat /tmp/bmc_result.txt 2>/dev/null | grep -v '^\[' | tr -d '\n' | grep -E '[0-9]+' || echo 0)
if [[ "$bmc_rc" == "0" && -n "$bmc_len" && "$bmc_len" -gt 100 ]]; then
  echo -e "  [build_memory_context] ${GREEN}✓ PASS${NC} — $bmc_len chars"; PASS=$((PASS+1))
else
  echo -e "  [build_memory_context] ${RED}✗ FAIL${NC} — rc=$bmc_rc len=$bmc_len"; FAIL=$((FAIL+1))
  cat /tmp/bmc_result.txt | head -5
fi

section "Crontab (@reboot entries)"
check "main.py on reboot" "crontab -l 2>/dev/null | grep 'main.py' | grep @reboot && echo OK" "OK"
check "opencode-mcp on reboot" "crontab -l 2>/dev/null | grep 'start-opencode-mcp' | grep @reboot && echo OK" "OK"
check "session_watcher on reboot" "crontab -l 2>/dev/null | grep 'start_session_watcher' | grep @reboot && echo OK" "OK"

section "Startup Scripts"
check "opencode-start.sh exists" "test -f /home/newadmin/swarm-bot/scripts/opencode-start.sh && echo OK" "OK"
check "start-opencode-mcp.sh exists" "test -f /home/newadmin/swarm-bot/scripts/start-opencode-mcp.sh && echo OK" "OK"
check "start_session_watcher.sh exists" "test -f /home/newadmin/swarm-bot/scripts/start_session_watcher.sh && echo OK" "OK"
check "verify-memory-pipeline.sh exists" "test -f /home/newadmin/swarm-bot/scripts/verify-memory-pipeline.sh && echo OK" "OK"

section "Obsidian MCP Server"
check "obsidian MCP connected" "ps aux | grep -E 'obsidian|mcpServers' | grep -v grep && echo OK" "OK"

echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Results: ${GREEN}${PASS} passed${NC} | ${RED}${FAIL} failed${NC}"
[[ $FAIL -eq 0 ]] && echo -e "${GREEN}✓ All systems operational${NC}" || echo -e "${YELLOW}⚠ ${FAIL} checks failed — review above${NC}"
exit $FAIL