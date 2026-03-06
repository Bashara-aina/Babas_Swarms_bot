# /home/newadmin/swarm-bot/optimization/usage_tracker.py
"""API usage tracking and cost monitoring.

Tracks token usage and estimated costs per model.
Stores in Redis if available, otherwise in-memory dict.
Emits alerts when approaching daily rate limits.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (input/output) in USD — 0.0 = free tier
PRICING: dict[str, dict[str, float]] = {
    "ollama_chat/gemma3:12b":                           {"input": 0.0, "output": 0.0},
    "ollama_chat/qwen3.5:35b":                          {"input": 0.0, "output": 0.0},
    "ollama_chat/exaone-deep:32b":                      {"input": 0.0, "output": 0.0},
    "ollama_chat/phi4":                                 {"input": 0.0, "output": 0.0},
    "ollama_chat/llama3.3:70b":                         {"input": 0.0, "output": 0.0},
    "zai/glm-4":                                        {"input": 0.0, "output": 0.0},
    "cerebras/qwen3-235b-a22b":                         {"input": 0.0, "output": 0.0},
    "groq/moonshotai/kimi-k2-instruct":                 {"input": 0.0, "output": 0.0},
    "openrouter/mistralai/devstral-2512:free":          {"input": 0.0, "output": 0.0},
    "openrouter/qwen/qwen3-coder:free":                 {"input": 0.0, "output": 0.0},
    "openrouter/openai/gpt-oss-120b:free":              {"input": 0.0, "output": 0.0},
    "gemini/gemini-3.1-pro":                            {"input": 0.035, "output": 0.105},
    "gemini/gemma-3-27b-it":                            {"input": 0.0, "output": 0.0},
}

# Daily request limits (0 = unlimited)
DAILY_LIMITS: dict[str, int] = {
    "zai/glm-4": 1000,
    "cerebras/qwen3-235b-a22b": 14400,
    "groq/moonshotai/kimi-k2-instruct": 1000,
}

ALERT_THRESHOLD = 0.80   # Alert at 80% of daily limit


class UsageTracker:
    """Track per-model API usage and compute estimated costs.

    Backends: Redis (preferred) or in-memory dict (fallback).
    """

    def __init__(self) -> None:
        self._redis: object = None
        self._memory: dict = defaultdict(lambda: defaultdict(float))
        self._init_redis()

    def _init_redis(self) -> None:
        """Connect to Redis if available."""
        try:
            import redis as redis_lib
            import os
            r = redis_lib.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True,
                socket_connect_timeout=2,
            )
            r.ping()
            self._redis = r
            logger.info("UsageTracker connected to Redis")
        except Exception:
            logger.info("UsageTracker: Redis unavailable, using in-memory tracking")

    def _today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _redis_key(self, model: str) -> str:
        return f"swarm:usage:{model}:{self._today()}"

    def record(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        requests: int = 1,
    ) -> Optional[str]:
        """Record token usage for a model.

        Args:
            model: Model string (e.g. 'zai/glm-4').
            input_tokens: Number of input/prompt tokens.
            output_tokens: Number of output/completion tokens.
            requests: Number of requests (default 1).

        Returns:
            Alert message string if approaching limit, else None.
        """
        pricing = PRICING.get(model, {"input": 0.0, "output": 0.0})
        cost = (
            (input_tokens / 1_000_000) * pricing["input"]
            + (output_tokens / 1_000_000) * pricing["output"]
        )

        if self._redis:
            key = self._redis_key(model)
            pipe = self._redis.pipeline()
            pipe.hincrbyfloat(key, "input_tokens", input_tokens)
            pipe.hincrbyfloat(key, "output_tokens", output_tokens)
            pipe.hincrbyfloat(key, "requests", requests)
            pipe.hincrbyfloat(key, "cost_usd", cost)
            pipe.expire(key, 86400 * 7)   # Keep 7 days
            pipe.execute()

            current_requests = float(self._redis.hget(key, "requests") or 0)
        else:
            key = f"{model}:{self._today()}"
            self._memory[key]["input_tokens"] += input_tokens
            self._memory[key]["output_tokens"] += output_tokens
            self._memory[key]["requests"] += requests
            self._memory[key]["cost_usd"] += cost
            current_requests = self._memory[key]["requests"]

        logger.debug("Recorded usage: model=%s requests=%d cost=$%.4f", model, requests, cost)

        # Check limit
        limit = DAILY_LIMITS.get(model, 0)
        if limit and current_requests >= limit * ALERT_THRESHOLD:
            pct = int(current_requests / limit * 100)
            return (
                f"⚠️ <b>Rate limit warning:</b> <code>{model}</code> "
                f"at {pct}% of daily limit ({int(current_requests)}/{limit} requests)"
            )
        return None

    def get_today(self, model: str) -> dict:
        """Get today's usage stats for a model.

        Args:
            model: Model string.

        Returns:
            Dict with input_tokens, output_tokens, requests, cost_usd.
        """
        if self._redis:
            key = self._redis_key(model)
            raw = self._redis.hgetall(key)
            return {k: float(v) for k, v in raw.items()} if raw else {}
        key = f"{model}:{self._today()}"
        return dict(self._memory.get(key, {}))

    def daily_report(self) -> str:
        """Generate HTML-formatted daily usage report.

        Returns:
            Telegram-safe HTML report string.
        """
        today = self._today()
        lines = [f"<b>Usage Report — {today}</b>\n"]
        total_cost = 0.0
        total_requests = 0

        all_models = list(PRICING.keys())

        for model in all_models:
            stats = self.get_today(model)
            if not stats:
                continue

            req = int(stats.get("requests", 0))
            cost = float(stats.get("cost_usd", 0))
            total_requests += req
            total_cost += cost

            limit = DAILY_LIMITS.get(model, 0)
            limit_str = f"/{limit}" if limit else ""
            cost_str = f"${cost:.4f}" if cost > 0 else "free"

            lines.append(f"  <code>{model.split('/')[-1][:20]}</code>: {req}{limit_str} reqs, {cost_str}")

        if total_requests == 0:
            return "No API usage recorded today."

        lines.append(f"\n<b>Total:</b> {total_requests} requests, ${total_cost:.4f}")
        return "\n".join(lines)


# Singleton
_tracker: UsageTracker | None = None


def get_tracker() -> UsageTracker:
    """Return global UsageTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
