# model_config.py — Single source of truth for Legion's model routing
# OpenCode Go (deepseek-v4-pro primary), OpenRouter nemotron free as emergency fallback.

import os

PRIMARY_MODEL = "deepseek-v4-pro"
PRIMARY_BASE_URL = "https://opencode.ai/zen/go/v1"
PRIMARY_API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

# Retry config — if OpenCode Go is slow, retry. Not switch provider.
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30
RETRY_ON_STATUS = [429, 503, 502]

# Temperature by task type
TEMPERATURE = {
    "conversation": 0.7,
    "code": 0.1,
    "research": 0.3,
    "creative": 0.9,
    "debate": 0.8,
}

# Context window
MAX_CONTEXT_TOKENS = 1_000_000
MAX_OUTPUT_TOKENS = 16_384

# Emergency fallback if OpenCode Go is completely down
EMERGENCY_FALLBACK = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"  # Free OpenRouter fallback


def get_client_config(task_type: str = "conversation") -> dict:
    return {
        "model": PRIMARY_MODEL,
        "base_url": PRIMARY_BASE_URL,
        "api_key": PRIMARY_API_KEY,
        "temperature": TEMPERATURE.get(task_type, 0.7),
        "max_tokens": MAX_OUTPUT_TOKENS,
    }
