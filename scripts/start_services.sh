#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Swarm-bot Start Services Script
# Usage: ./scripts/start_services.sh [--no-systemd]
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_DIR="$(dirname "$SCRIPT_DIR")"
USE_SYSTEMD="${1:-}"

# Load .env if it exists
if [[ -f "$BOT_DIR/.env" ]]; then
    set -a
    source "$BOT_DIR/.env"
    set +a
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Check Python venv ────────────────────────────────────────
check_venv() {
    if [[ ! -d "$BOT_DIR/.venv" ]]; then
        log_error ".venv not found at $BOT_DIR/.venv"
        exit 1
    fi
    PYTHON="$BOT_DIR/.venv/bin/python3"
    if [[ ! -x "$PYTHON" ]]; then
        log_error "Python not executable at $PYTHON"
        exit 1
    fi
    log_info "Python venv: $PYTHON"
}

# ── Check dependencies ──────────────────────────────────────
check_deps() {
    log_info "Checking Python dependencies..."
    MISSING=""
    for pkg in aiogram aiosqlite python-dotenv; do
        if ! "$PYTHON" -c "import $pkg" 2>/dev/null; then
            MISSING="$MISSING $pkg"
        fi
    done
    if [[ -n "$MISSING" ]]; then
        log_warn "Missing packages:$MISSING"
        log_info "Installing..."
        "$PYTHON" -m pip install --quiet aiogram aiosqlite python-dotenv
    fi
}

# ── Check port availability ─────────────────────────────────
check_ports() {
    log_info "Checking critical ports..."
    PORTS=(8080 8743 7835)
    for PORT in "${PORTS[@]}"; do
        if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
            log_warn "Port $PORT is already in use (may be another service)"
        else
            log_info "Port $PORT is free"
        fi
    done
}

# ── Start via systemd ────────────────────────────────────────
start_systemd() {
    log_info "Starting swarm-bot via systemd..."
    if systemctl is-active --quiet swarm-bot 2>/dev/null; then
        log_warn "swarm-bot is already active"
        systemctl status swarm-bot --no-pager --length=50
    else
        sudo systemctl restart swarm-bot
        sleep 3
        if systemctl is-active --quiet swarm-bot; then
            log_info "swarm-bot is now active"
            systemctl status swarm-bot --no-pager --length=20
        else
            log_error "swarm-bot failed to start"
            systemctl status swarm-bot --no-pager --length=30
            exit 1
        fi
    fi
}

# ── Start directly ───────────────────────────────────────────
start_direct() {
    log_info "Starting swarm-bot directly (non-systemd)..."
    log_warn "Run 'sudo systemctl restart swarm-bot' for production use"
    cd "$BOT_DIR"
    exec "$PYTHON" main.py
}

# ── Main ─────────────────────────────────────────────────────
main() {
    echo "═══════════════════════════════════════"
    echo "  Swarm-bot Start Services"
    echo "═══════════════════════════════════════"
    echo ""

    check_venv
    check_deps
    check_ports

    if [[ "$USE_SYSTEMD" == "--no-systemd" ]]; then
        start_direct
    else
        # Try systemd first, fall back to direct
        if command -v systemctl &>/dev/null && [[ -f /etc/systemd/system/swarm-bot.service ]]; then
            start_systemd
        else
            log_warn "systemd not available or swarm-bot.service not found"
            start_direct
        fi
    fi

    log_info "Done."
}

main "$@"
