#!/usr/bin/env bash
# browser-use safe wrapper — enforces MiniMax-only policy for all browser automation
set -euo pipefail

# ── Path setup ─────────────────────────────────────────────────────────────
export PATH="$HOME/.local/bin:$HOME/.local/node18/bin:$PATH"

# ── Timeout / output controls ─────────────────────────────────────────────
export BROWSER_USE_TIMEOUT_MS="${BROWSER_USE_TIMEOUT_MS:-60000}"
export BROWSER_USE_MAX_OUTPUT="${BROWSER_USE_MAX_OUTPUT:-50000}"
export BROWSER_USE_HEADLESS="${BROWSER_USE_HEADLESS:-true}"

# ── MiniMax LLM settings ────────────────────────────────────────────────────
# Route through local LiteLLM proxy (port 4000)
export BROWSER_USE_LLM_PROVIDER="${BROWSER_USE_LLM_PROVIDER:-litellm}"
export BROWSER_LLM_URL="${BROWSER_LLM_URL:-http://localhost:4000}"
export BROWSER_LLM_MODEL="${BROWSER_LLM_MODEL:-minimax-primary}"
export BROWSER_LLM_CRED="${BROWSER_LLM_CRED:-placeholder}"

# ── MiniMax-only policy enforcement ───────────────────────────────────────
_forbidden_pattern='claude|anthropic|gpt-4|gpt-5|openai|gemini|groq|together|o1-|o3-|o4-'
if [[ "${BROWSER_LLM_MODEL}" =~ $_forbidden_pattern ]]; then
  echo "ERROR: Forbidden model in BROWSER_LLM_MODEL: ${BROWSER_LLM_MODEL}" >&2
  echo "       browser-use is locked to MiniMax only. Aborting." >&2
  exit 1
fi

# ── Run the actual command ─────────────────────────────────────────────────
exec "$@"
