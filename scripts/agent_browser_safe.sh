#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$HOME/.local/node18/bin:$PATH"
export AGENT_BROWSER_DEFAULT_TIMEOUT="${AGENT_BROWSER_DEFAULT_TIMEOUT:-25000}"
export AGENT_BROWSER_MAX_OUTPUT="${AGENT_BROWSER_MAX_OUTPUT:-50000}"
export AGENT_BROWSER_CONTENT_BOUNDARIES="${AGENT_BROWSER_CONTENT_BOUNDARIES:-1}"
export AGENT_BROWSER_SESSION_NAME="${AGENT_BROWSER_SESSION_NAME:-opencode}"

# MiniMax-only lock
export AI_GATEWAY_MODEL="${AI_GATEWAY_MODEL:-minimax/MiniMax-M3}"
export AI_GATEWAY_URL="${AI_GATEWAY_URL:-http://localhost:4000}"
export AI_GATEWAY_API_KEY="${AI_GATEWAY_API_KEY:-dummy}"

# Hard fail if a forbidden model is requested
if [[ "${AI_GATEWAY_MODEL}" =~ claude|anthropic|gpt|openai|gemini|groq|together ]]; then
  echo "ERROR: Forbidden browser-chat model: ${AI_GATEWAY_MODEL}" >&2
  exit 1
fi

exec agent-browser "$@"