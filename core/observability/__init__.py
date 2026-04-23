from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

try:
    import agentops  # type: ignore
except Exception:
    agentops = None

_PROVIDER_STATS: dict[str, dict[str, float]] = defaultdict(lambda: {
    "calls": 0.0,
    "tokens": 0.0,
    "latency_ms": 0.0,
    "errors": 0.0,
})


def init_observability() -> None:
    if agentops is None:
        logger.info("AgentOps unavailable; using local observability only")
        return
    api_key = os.getenv("AGENTOPS_API_KEY", "")
    try:
        agentops.init(
            api_key=api_key,
            default_tags=["legionswarm", "telegram-bot", "rtx3060"],
            auto_start_session=True,
        )
        logger.info("AgentOps initialized")
    except Exception as exc:
        logger.warning("AgentOps init failed: %s", exc)


def _update_local(provider: str, tokens: int, latency_ms: float, success: bool) -> None:
    stats = _PROVIDER_STATS[provider]
    stats["calls"] += 1
    stats["tokens"] += max(0, float(tokens))
    stats["latency_ms"] += max(0.0, float(latency_ms))
    if not success:
        stats["errors"] += 1


def track_agent(agent_name: str) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.perf_counter()
            provider = str(kwargs.get("provider") or kwargs.get("agent_key") or agent_name)
            success = True
            tokens = 0
            try:
                result = await func(*args, **kwargs)
                if hasattr(result, "tokens_used"):
                    tokens = int(getattr(result, "tokens_used", 0) or 0)
                elif isinstance(result, dict):
                    tokens = int(result.get("tokens_used", 0) or 0)
                return result
            except Exception:
                success = False
                raise
            finally:
                latency_ms = (time.perf_counter() - started) * 1000.0
                _update_local(provider, tokens, latency_ms, success)
                if agentops is not None:
                    try:
                        agentops.record(
                            "agent_call",
                            {
                                "agent": agent_name,
                                "provider": provider,
                                "latency_ms": latency_ms,
                                "tokens": tokens,
                                "success": success,
                            },
                        )
                    except Exception:
                        pass
        return wrapper
    return decorator


def get_metrics_snapshot() -> dict[str, dict[str, float]]:
    return {k: dict(v) for k, v in _PROVIDER_STATS.items()}


async def notify_limit_warnings(send_fn: Callable[[str], Awaitable[None]], provider_limits: dict[str, float]) -> None:
    for provider, stats in get_metrics_snapshot().items():
        daily_limit = provider_limits.get(provider)
        if not daily_limit or daily_limit <= 0:
            continue
        used = stats.get("calls", 0.0)
        pct = used / daily_limit
        if pct >= 0.8:
            await send_fn(f"⚠️ provider {provider} at {pct*100:.1f}% of daily limit")


def render_metrics_html() -> str:
    data = get_metrics_snapshot()
    if not data:
        return "<b>📈 Metrics</b>\nNo data yet."
    lines = ["<b>📈 Agent Metrics</b>"]
    for provider, stats in sorted(data.items()):
        calls = int(stats.get("calls", 0))
        tokens = int(stats.get("tokens", 0))
        total_lat = float(stats.get("latency_ms", 0.0))
        err = int(stats.get("errors", 0))
        avg = total_lat / calls if calls else 0.0
        lines.append(
            f"• <b>{provider}</b> — calls: <code>{calls}</code>, tokens: <code>{tokens}</code>, avg latency: <code>{avg:.1f}ms</code>, errors: <code>{err}</code>"
        )
    return "\n".join(lines)


__all__ = [
    "init_observability",
    "track_agent",
    "get_metrics_snapshot",
    "notify_limit_warnings",
    "render_metrics_html",
]
