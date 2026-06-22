#!/usr/bin/env bash
set -euo pipefail

# Claude Code wrapper for OpenRouter — routes Claude Code through OpenRouter
# Uses NVIDIA Nemotron model by default.
#
# Usage:
#   ./claude-openrouter-wrapper.sh          # launch in current dir
#   ./claude-openrouter-wrapper.sh <args>   # pass args to claude
#
# Environment (loaded from .env or already exported):
#   OPENROUTER_API_KEY  — Your OpenRouter API key (required)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load .env from project root if available
if [ -f "$PROJECT_DIR/.env" ]; then
  # shellcheck disable=SC1090
  set -a; source "$PROJECT_DIR/.env"; set +a
fi

# Load shell env as fallback
if [ -f "$HOME/.bashrc" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.bashrc" >/dev/null 2>&1 || true
fi

# Require OpenRouter API key
: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY is not set — add it to .env or export it}"

# --- OpenRouter Anthropic Skin Configuration ---
# Per OpenRouter docs: ANTHROPIC_BASE_URL must point to OpenRouter API
export ANTHROPIC_BASE_URL="https://openrouter.ai/api"
export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
# Important: Must be explicitly empty to prevent credential conflict (OpenRouter docs)
export ANTHROPIC_API_KEY=""

# --- Model Configuration ---
# Using DeepSeek V4 Flash
MODEL="${OPENROUTER_MODEL:-deepseek-v4-flash}"

export ANTHROPIC_MODEL="$MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$MODEL"
export CLAUDE_CODE_SUBAGENT_MODEL="$MODEL"

# --- Telemetry & Performance ---
export CLAUDE_CODE_SIMPLE="${CLAUDE_CODE_SIMPLE:-1}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:-1}"
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="1000000"

exec /home/newadmin/.local/bin/claude "$@"
