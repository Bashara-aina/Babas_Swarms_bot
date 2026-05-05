#!/bin/bash
set -uo pipefail

# ─────────────────────────────────────────────────────────────
# Swarm-bot Health Check Script
# Usage: ./scripts/health_check.sh [--verbose]
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_DIR="$(dirname "$SCRIPT_DIR")"
VERBOSE="${1:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

log_pass()  { echo -e "${GREEN}[PASS]${NC}  $1"; PASS=$((PASS+1)); }
log_fail()  { echo -e "${RED}[FAIL]${NC}  $1"; FAIL=$((FAIL+1)); }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; WARN=$((WARN+1)); }
log_info()  { [[ -n "$VERBOSE" ]] && echo -e "       $1"; }

# ── Check systemd service ────────────────────────────────────
check_systemd_service() {
    echo "═══ Systemd Service ═══"
    if systemctl is-active --quiet swarm-bot 2>/dev/null; then
        log_pass "swarm-bot.service is active"
        log_info "PID: $(systemctl show swarm-bot --property MainPID --value 2>/dev/null)"
        log_info "Memory: $(systemctl show swarm-bot --property MemoryCurrent --value 2>/dev/null | numfmt --to=iec 2>/dev/null || echo 'N/A')"
    elif systemctl is-enabled --quiet swarm-bot 2>/dev/null; then
        log_fail "swarm-bot.service is not active"
    else
        log_warn "swarm-bot.service not found or not enabled"
    fi
}

# ── Check bot process ───────────────────────────────────────
check_bot_process() {
    echo ""
    echo "═══ Bot Process ═══"
    PYTHON_PID=$(pgrep -f "main.py" 2>/dev/null | head -1 || true)
    if [[ -n "$PYTHON_PID" ]]; then
        log_pass "main.py is running (PID $PYTHON_PID)"
        log_info "CPU: $(ps -p "$PYTHON_PID" -o %cpu= 2>/dev/null || echo 'N/A')%"
        log_info "MEM: $(ps -p "$PYTHON_PID" -o rss= 2>/dev/null | numfmt --to=iec 2>/dev/null || echo 'N/A')"
    else
        log_fail "main.py process not found"
    fi
}

# ── Check bot logs for polling ──────────────────────────────
check_polling() {
    echo ""
    echo "═══ Telegram Polling ═══"
    if command -v journalctl &>/dev/null; then
        LAST_POLL=$(journalctl -u swarm-bot.service --no-pager -n 200 2>/dev/null | grep "start_polling" | tail -1 || true)
        LAST_HEARTBEAT=$(journalctl -u swarm-bot.service --no-pager -n 50 2>/dev/null | grep "heartbeat" | tail -1 || true)
        if [[ -n "$LAST_POLL" ]]; then
            log_pass "Polling started: $(echo "$LAST_POLL" | xargs)"
        else
            log_warn "No polling confirmation in recent logs"
        fi
        if [[ -n "$LAST_HEARTBEAT" ]]; then
            log_pass "Heartbeat: $(echo "$LAST_HEARTBEAT" | xargs)"
        else
            log_warn "No heartbeat in recent logs"
        fi
    else
        log_warn "journalctl not available"
    fi
}

# ── Check memory system ──────────────────────────────────────
check_memory_system() {
    echo ""
    echo "═══ Memory System ═══"
    PYTHON="$BOT_DIR/.venv/bin/python3"
    if [[ -x "$PYTHON" ]]; then
        RESULT=$(\
            $PYTHON -c "
import asyncio
import aiosqlite
async def check():
    try:
        conn = await aiosqlite.connect('$BOT_DIR/data/memory.db')
        cur = await conn.execute('SELECT COUNT(*) FROM memories')
        count = await cur.fetchone()
        await conn.close()
        return count[0] if count else 0
    except Exception as e:
        return str(e)
print(asyncio.run(check()))
" 2>/dev/null || echo "ERROR"
        )
        if [[ "$RESULT" =~ ^[0-9]+$ ]]; then
            if [[ "$RESULT" -gt 0 ]]; then
                log_pass "Memory DB: $RESULT memories stored"
            else
                log_warn "Memory DB: 0 memories (may be empty)"
            fi
        else
            log_fail "Memory DB: $RESULT"
        fi
    else
        log_warn "Python venv not available for memory check"
    fi
}

# ── Check port bindings ─────────────────────────────────────
check_ports() {
    echo ""
    echo "═══ Port Status ═══"
    PORTS=(
        "8080:health"
        "8743:webhook"
        "7835:n8n_bridge"
    )
    for entry in "${PORTS[@]}"; do
        PORT="${entry%%:*}"
        NAME="${entry##*:}"
        if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
            log_pass "Port $PORT ($NAME) is bound"
        else
            log_info "Port $PORT ($NAME) is free (not currently bound)"
        fi
    done
}

# ── Check disk space ────────────────────────────────────────
check_disk() {
    echo ""
    echo "═══ Disk Space ═══"
    FREE=$(df -BG "$BOT_DIR" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo "0")
    if [[ "$FREE" -gt 5 ]]; then
        log_pass "Disk space: ${FREE}GB free"
    elif [[ "$FREE" -gt 1 ]]; then
        log_warn "Disk space: ${FREE}GB free (low)"
    else
        log_fail "Disk space: ${FREE}GB free (critical)"
    fi
}

# ── Check swap ──────────────────────────────────────────────
check_swap() {
    echo ""
    echo "═══ Swap Usage ═══"
    SWAP_TOTAL=$(free -b 2>/dev/null | awk 'NR==3 {print $2}' || echo "0")
    SWAP_USED=$(free -b 2>/dev/null | awk 'NR==3 {print $3}' || echo "0")
    if [[ "$SWAP_TOTAL" -gt 0 ]]; then
        SWAP_PCT=$(( SWAP_USED * 100 / SWAP_TOTAL ))
        if [[ "$SWAP_PCT" -lt 50 ]]; then
            log_pass "Swap: ${SWAP_PCT}% used"
        elif [[ "$SWAP_PCT" -lt 80 ]]; then
            log_warn "Swap: ${SWAP_PCT}% used (moderate)"
        else
            log_fail "Swap: ${SWAP_PCT}% used (high)"
        fi
    else
        log_info "Swap: not configured"
    fi
}

# ── Check recent errors ──────────────────────────────────────
check_errors() {
    echo ""
    echo "═══ Recent Errors ═══"
    if command -v journalctl &>/dev/null; then
        ERROR_COUNT=$(journalctl -u swarm-bot.service --no-pager -n 500 2>/dev/null | grep -cE "\[ERROR\]|\[CRITICAL\]" || echo "0")
        if [[ "$ERROR_COUNT" -eq 0 ]]; then
            log_pass "No errors in last 500 log lines"
        elif [[ "$ERROR_COUNT" -lt 5 ]]; then
            log_warn "$ERROR_COUNT errors in recent logs"
        else
            log_fail "$ERROR_COUNT errors in recent logs"
            log_info "Run: journalctl -u swarm-bot.service --no-pager -n 500 | grep ERROR"
        fi
    else
        log_info "journalctl not available"
    fi
}

# ── Summary ─────────────────────────────────────────────────
summary() {
    echo ""
    echo "═══════════════════════════════════════"
    echo "  Health Summary"
    echo "═══════════════════════════════════════"
    echo -e "  ${GREEN}PASS:${NC} $PASS   ${RED}FAIL:${NC} $FAIL   ${YELLOW}WARN:${NC} $WARN"
    echo ""

    if [[ "$FAIL" -gt 0 ]]; then
        echo -e "${RED}Some checks failed. Review above.${NC}"
        exit 1
    elif [[ "$WARN" -gt 0 ]]; then
        echo -e "${YELLOW}Some checks have warnings.${NC}"
        exit 0
    else
        echo -e "${GREEN}All checks passed!${NC}"
        exit 0
    fi
}

# ── Main ─────────────────────────────────────────────────────
main() {
    echo "═══════════════════════════════════════"
    echo "  Swarm-bot Health Check"
    echo "═══════════════════════════════════════"
    echo ""

    check_systemd_service
    check_bot_process
    check_polling
    check_memory_system
    check_ports
    check_disk
    check_swap
    check_errors
    summary
}

main "$@"
