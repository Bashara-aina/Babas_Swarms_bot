#!/usr/bin/env bash
# oc-cc-proxy — LiteLLM proxy bridging Claude Code (Anthropic API) → OpenCode Go
# Port: 4001 (4000 is used by the AI gateway)
# Includes ToolSchemaStripperCallback to reduce context floor by ~60K tokens.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

PORT="${OC_PROXY_PORT:-4001}"
HOST="${OC_PROXY_HOST:-127.0.0.1}"
API_KEY="${OPENCODE_GO_API_KEY:-}"

if [ -z "$API_KEY" ]; then
  echo "ERROR: OPENCODE_GO_API_KEY is not set. Add it to .env or export it."
  exit 1
fi

# Kill any existing process on the target port so systemd doesn't loop forever
if lsof -ti :"$PORT" &>/dev/null; then
  echo "Killing existing process on port $PORT..."
  lsof -ti :"$PORT" | xargs kill 2>/dev/null || true
  sleep 1
  # Force kill if still alive
  if lsof -ti :"$PORT" &>/dev/null; then
    lsof -ti :"$PORT" | xargs kill -9 2>/dev/null || true
    sleep 0.5
  fi
fi

# Clean up stale temp directories (older than 1 hour)
find /tmp -maxdepth 1 -name 'oc-cc-proxy-*' -mmin +60 -exec rm -rf {} + 2>/dev/null || true

CONFIG_DIR=$(mktemp -d /tmp/oc-cc-proxy-XXXXXX)
CONFIG_PATH="$CONFIG_DIR/litellm.yaml"
CALLBACK_DIR="$CONFIG_DIR/oc_proxy"
mkdir -p "$CALLBACK_DIR"

# Start muse-responses-shim (chat-completions -> zen /responses translator for muse-spark)
MUSE_SHIM_PORT="${MUSE_SHIM_PORT:-4002}"
if lsof -ti :"$MUSE_SHIM_PORT" &>/dev/null; then
  echo "Killing existing process on port $MUSE_SHIM_PORT..."
  lsof -ti :"$MUSE_SHIM_PORT" | xargs kill 2>/dev/null || true
  sleep 1
fi
nohup python3 "$PROJECT_DIR/scripts/muse-responses-shim.py" > "$CONFIG_DIR/shim.log" 2>&1 &
for i in $(seq 1 20); do
  if curl -sf "http://127.0.0.1:${MUSE_SHIM_PORT}/healthz" &>/dev/null; then
    echo "muse-responses-shim healthy on :${MUSE_SHIM_PORT}"
    break
  fi
  sleep 1
  if [ "$i" = "20" ]; then
    echo "ERROR: muse shim failed to start. See $CONFIG_DIR/shim.log"
    tail -n 20 "$CONFIG_DIR/shim.log" || true
    exit 1
  fi
done

# Write callback modules
cat > "$CALLBACK_DIR/__init__.py" << 'PYEOF'
PYEOF

# Write max_effort callback — forces reasoning_effort: max on all deepseek requests
cat > "$CALLBACK_DIR/max_effort.py" << 'PYEOF'
"""LiteLLM callback: force reasoning_effort=max on deepseek models."""
from __future__ import annotations

from typing import Any
from litellm.integrations.custom_logger import CustomLogger
from litellm.types.utils import CallTypes


class MaxEffortCallback(CustomLogger):
    """Force reasoning_effort=max on all deepseek-v4 requests."""

    async def async_pre_call_deployment_hook(
        self, kwargs: dict[str, Any], call_type: CallTypes | None
    ) -> dict[str, Any]:
        if call_type not in {CallTypes.completion, CallTypes.acompletion}:
            return kwargs

        model = str(kwargs.get("model") or "")
        if not model.startswith(("deepseek-v4",)):
            return kwargs

        optional_params = kwargs.get("optional_params") or {}
        optional_params["reasoning_effort"] = "max"
        kwargs["optional_params"] = optional_params
        return kwargs


max_effort_callback = MaxEffortCallback()
PYEOF

# Copy reasoning callback from installed package
# (miniconda3 was on destroyed hard disk; local system path is the first check)
for candidate in \
  "/home/newadmin/.local/lib/python3.10/site-packages/oc_proxy/reasoning.py" \
  "/home/newadmin/miniconda3/lib/python3.13/site-packages/oc_proxy/reasoning.py"; do
  if [ -f "$candidate" ]; then
    cp "$candidate" "$CALLBACK_DIR/reasoning.py"
    REASONING_SRC="$candidate"
    break
  fi
done
if [ -z "${REASONING_SRC:-}" ]; then
  echo "WARNING: oc_proxy.reasoning not found — callback may fail"
fi

# Copy tool stripper callback (canonical: config/oc_proxy/, legacy: .claude-flow/mcp/)
if [ -f "$PROJECT_DIR/config/oc_proxy/tool_stripper.py" ]; then
  cp "$PROJECT_DIR/config/oc_proxy/tool_stripper.py" "$CALLBACK_DIR/tool_stripper.py"
elif [ -f "$PROJECT_DIR/.claude-flow/mcp/litellm_tool_stripper.py" ]; then
  cp "$PROJECT_DIR/.claude-flow/mcp/litellm_tool_stripper.py" "$CALLBACK_DIR/tool_stripper.py"
else
  echo "ERROR: tool_stripper.py not found in config/oc_proxy/ or .claude-flow/mcp/ — cannot start proxy."
  exit 1
fi

# Generate LiteLLM config
cat > "$CONFIG_PATH" << YAMLEOF
model_list:
  # Explicit entries with fallbacks for Claude Code model names
  - model_name: deepseek-v4-flash
    litellm_params:
      model: openai/deepseek-v4-flash
      api_base: https://opencode.ai/zen/go/v1
      api_key: ${API_KEY}
      extra_headers:
        x-opencode-session: "8f599165-54d8-415c-b58b-60ba1f421a7c"
      max_input_tokens: 1000000
      max_tokens: 1000000
  - model_name: deepseek-v4-pro
    litellm_params:
      model: openai/deepseek-v4-pro
      api_base: https://opencode.ai/zen/go/v1
      api_key: ${API_KEY}
      extra_headers:
        x-opencode-session: "8f599165-54d8-415c-b58b-60ba1f421a7c"
      max_input_tokens: 1000000
      max_tokens: 1000000
  - model_name: muse-spark-1.3-contributor
    litellm_params:
      model: openai/muse-spark-1.3-contributor
      # via local shim: zen serves muse ONLY on the Responses API (see docs/go)
      api_base: http://127.0.0.1:${MUSE_SHIM_PORT:-4002}/v1
      api_key: dummy-key-for-local-shim
      reasoning_effort: "xhigh"
      max_input_tokens: 1000000
      max_tokens: 1000000
  # MiniMax direct (for opus tier)
  - model_name: minimax-m3
    litellm_params:
      model: anthropic/MiniMax-M3[1m]
      api_base: https://api.minimax.io/anthropic
      api_key: ${MINIMAX_API_KEY}
      max_input_tokens: 1000000
      max_tokens: 1000000

  # Wildcard catch-all for any other model requests
  - model_name: '*'
    litellm_params:
      model: openai/*
      api_base: https://opencode.ai/zen/go/v1
      api_key: ${API_KEY}
      extra_headers:
        x-opencode-session: "8f599165-54d8-415c-b58b-60ba1f421a7c"
      max_input_tokens: 1000000
      max_tokens: 1000000

router_settings:
  num_retries: 3
  retry_after: 1
  allowed_fails: 3
  cooldown_time: 30
  fallbacks:
    - deepseek-v4-flash: [muse-spark-1.3-contributor]
    - muse-spark-1.3-contributor: [deepseek-v4-flash]
    - deepseek-v4-pro: [deepseek-v4-flash]
    - "*": [deepseek-v4-flash]
  default_fallbacks: [deepseek-v4-flash]

litellm_settings:
  callbacks:
    - oc_proxy.reasoning.deepseek_reasoning_content_callback
    - oc_proxy.tool_stripper.tool_schema_stripper_callback
    - oc_proxy.max_effort.max_effort_callback
  drop_params: true
  set_verbose: false
  use_chat_completions_url_for_anthropic_messages: true
YAMLEOF

echo "🚀 Starting oc-cc-proxy on http://${HOST}:${PORT}"
echo "   Models → OpenCode Go wildcard passthrough"
echo "   Tool schema stripping → enabled (saves ~60K tokens/req)"

export PYTHONPATH="$CONFIG_DIR${PYTHONPATH:+:$PYTHONPATH}"
export PATH="/home/newadmin/miniconda3/bin:/home/newadmin/.local/bin:/usr/bin:$PATH"

# Use system litellm (conda version has incompatible guardrail deps)
LITELLM_BIN="/home/newadmin/.local/bin/litellm"
if [ ! -x "$LITELLM_BIN" ]; then
  LITELLM_BIN="litellm"
fi
exec "$LITELLM_BIN" --config "$CONFIG_PATH" --host "$HOST" --port "$PORT"
