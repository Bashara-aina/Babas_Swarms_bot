# model_config.py — Single source of truth for Legion's model routing
# MiniMax M2.7 is the ONLY model. No fallbacks to broken APIs.

import os

PRIMARY_MODEL = "MiniMax-M2.7"
PRIMARY_BASE_URL = "https://api.minimax.io/v1"
PRIMARY_API_KEY = os.environ.get("MINIMAX_API_KEY", "")

# Retry config — if MiniMax is slow, retry MiniMax. Not switch provider.
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

# What to do if MiniMax is completely down (rare)
EMERGENCY_FALLBACK = None  # Set to "claude-3-5-sonnet" only if ANTHROPIC_API_KEY is valid


def get_client_config(task_type: str = "conversation") -> dict:
    return {
        "model": PRIMARY_MODEL,
        "base_url": PRIMARY_BASE_URL,
        "api_key": PRIMARY_API_KEY,
        "temperature": TEMPERATURE.get(task_type, 0.7),
        "max_tokens": MAX_OUTPUT_TOKENS,
    }
