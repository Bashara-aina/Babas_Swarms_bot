#!/usr/bin/env bash
# ECC Desktop Notify: Send desktop notification on session end/stop
# Supports macOS (terminal-notifier) and Linux (notify-send)
set -euo pipefail

if [ "${HOOK_PROFILE:-standard}" != "strict" ]; then
  exit 0
fi

MESSAGE="${1:-Claude Code session ended}"

if command -v terminal-notifier &>/dev/null; then
  terminal-notifier -title "Claude Code" -message "$MESSAGE" -sound default 2>/dev/null || true
elif command -v notify-send &>/dev/null; then
  notify-send "Claude Code" "$MESSAGE" 2>/dev/null || true
fi

exit 0
