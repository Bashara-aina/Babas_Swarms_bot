#!/usr/bin/env bash
# Auto-start-services hook: verify and (re)start critical background services
# Used at SessionStart so MCP servers + SearXNG come up reliably.
#
# Runs in <2 seconds (parallel curl + systemctl). Never blocks the session.

set -uo pipefail

LOG=/home/newadmin/.cache/services-health.log
mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date --iso-8601=seconds)] $*" >> "$LOG"; }

# ─── SearXNG (HTTP at 127.0.0.1:8888) ────────────────────────────────────────
check_searxng() {
  if curl -sf --max-time 2 http://127.0.0.1:8888/healthz >/dev/null 2>&1; then
    return 0
  fi
  log "searxng: HEALTHZ failed, restarting"
  systemctl --user restart searxng.service 2>&1 || true
  return 1
}

# ─── textidote.jar (file existence check) ───────────────────────────────────
check_textidote() {
  local jar="${HOME}/swarm-bot/tools/textidote/textidote.jar"
  [ -f "${jar}" ] && return 0
  log "textidote: jar missing — run bin/build-textidote.sh when sudo is available"
  return 1
}

# ─── Playwright browsers (chromium-XXXX dirs) ────────────────────────────────
check_playwright() {
  # browser-use / crawl4ai need a chromium runtime directory
  if [ -d "${HOME}/.cache/ms-playwright" ] && \
     [ -n "$(ls -A "${HOME}/.cache/ms-playwright" 2>/dev/null | grep -E '^chromium' || true)" ]; then
    return 0
  fi
  log "playwright: no chromium browser found (~/.cache/ms-playwright empty)"
  return 1
}

# ─── Aggregate ──────────────────────────────────────────────────────────────
failures=0
check_searxng     || ((failures++))
check_textidote   || ((failures++))
check_playwright  || ((failures++))

if [ $failures -eq 0 ]; then
  log "all services healthy"
fi

exit 0  # never block the session
