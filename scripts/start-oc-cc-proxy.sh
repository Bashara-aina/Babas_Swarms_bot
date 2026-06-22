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

CONFIG_DIR=$(mktemp -d /tmp/oc-cc-proxy-XXXXXX)
CONFIG_PATH="$CONFIG_DIR/litellm.yaml"
CALLBACK_DIR="$CONFIG_DIR/oc_proxy"
mkdir -p "$CALLBACK_DIR"

# Write callback modules
cat > "$CALLBACK_DIR/__init__.py" << 'PYEOF'
PYEOF

# Copy reasoning callback from installed package
REASONING_SRC="/home/newadmin/miniconda3/lib/python3.13/site-packages/oc_proxy/reasoning.py"
if [ -f "$REASONING_SRC" ]; then
  cp "$REASONING_SRC" "$CALLBACK_DIR/reasoning.py"
else
  echo "WARNING: reasoning.py not found at $REASONING_SRC"
fi

# Copy tool stripper callback
cp "$PROJECT_DIR/.claude-flow/mcp/litellm_tool_stripper.py" "$CALLBACK_DIR/tool_stripper.py"

# Generate LiteLLM config
cat > "$CONFIG_PATH" << YAMLEOF
model_list:
  - model_name: '*'
    litellm_params:
      model: openai/*
      api_base: https://opencode.ai/zen/go/v1
      api_key: ${API_KEY}
      max_input_tokens: 1000000
      max_tokens: 65536

litellm_settings:
  callbacks:
    - oc_proxy.reasoning.deepseek_reasoning_content_callback
    - oc_proxy.tool_stripper.tool_schema_stripper_callback
  drop_params: true
  set_verbose: false
  use_chat_completions_url_for_anthropic_messages: true
YAMLEOF

echo "🚀 Starting oc-cc-proxy on http://${HOST}:${PORT}"
echo "   Models → OpenCode Go wildcard passthrough"
echo "   Tool schema stripping → enabled (saves ~60K tokens/req)"

export PYTHONPATH="$CONFIG_DIR:$PYTHONPATH"
export PATH="/home/newadmin/miniconda3/bin:/home/newadmin/.local/bin:$PATH"

exec litellm --config "$CONFIG_PATH" --host "$HOST" --port "$PORT"
