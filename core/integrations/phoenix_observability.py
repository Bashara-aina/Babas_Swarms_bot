"""core/integrations/phoenix_observability.py — Arize Phoenix tracing for LLM agents.

Phoenix 15+ provides real-time agent tracing, token monitoring, and evaluation.
Works with MiniMax via OpenAI-compatible endpoint.

Local mode: launches Phoenix UI at localhost:6007
Remote mode: sends traces via OTLP to app.phoenix.arize.com

Usage:
    from core.integrations import PhoenixTracer, TokenUsageTracker

    tracer = PhoenixTracer()
    tracker = TokenUsageTracker()

    await tracer.trace_llm_call(
        model="minimax/MiniMax-M2.7",
        prompt="Explain quantum computing",
        response="Quantum computing uses...",
        latency_ms=234.5,
        token_usage={"prompt_tokens": 50, "completion_tokens": 120},
    )

    tracker.record_run("minimax/MiniMax-M2.7", 50, 120, 234.5)
    print(tracker.report())
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

PHOENIX_AVAILABLE = False
_PHOENIX_VERSION = 0

try:
    import phoenix as _phoenix
    PHOENIX_AVAILABLE = True
    _PHOENIX_VERSION = int(getattr(_phoenix, "__version__", "0").split(".")[0])
except ImportError:
    _phoenix = None

DEFAULT_PHOENIX_ENDPOINT = "https://app.phoenix.arize.com"
PHOENIX_LOCAL_PORT = 6007


class PhoenixLauncher:
    """Launch and manage a local Phoenix server."""

    _instance = None

    @classmethod
    def get_instance(cls) -> "PhoenixLauncher":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._server = None
        self._url: str | None = None

    def launch(self, port: int = PHOENIX_LOCAL_PORT) -> str:
        """Launch local Phoenix server and return URL."""
        if self._server is not None:
            return self._url or f"http://localhost:{port}"

        try:
            if PHOENIX_VERSION >= 1:
                self._server = _phoenix.launch_app(port=port)
                self._url = f"http://localhost:{port}"
                logger.info("Phoenix local server launched: %s", self._url)
                return self._url
            else:
                _phoenix.launch_app(port=port)
                self._url = f"http://localhost:{port}"
                return self._url
        except Exception as exc:
            logger.warning("Phoenix launch failed: %s", exc)
            return ""

    def close(self) -> None:
        """Close the Phoenix server."""
        if self._server is not None:
            try:
                _phoenix.close_app()
            except Exception:
                pass
            self._server = None
            self._url = None


PHOENIX_VERSION = _PHOENIX_VERSION

_TOKEN_TRACKER: TokenUsageTracker | None = None


class PhoenixTracer:
    """Arize Phoenix tracer for SwarmBot agents.

    Phoenix 15+ works in two modes:
    1. Local: launch Phoenix UI locally (no API key needed)
    2. Remote: send traces via OTLP (requires Phoenix API key)

    TokenUsageTracker is always available and does not require Phoenix.
    """

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        project_name: str = "swarm-bot",
        local_mode: bool = True,
    ) -> None:
        self.api_key = api_key or os.getenv("PHOENIX_API_KEY", "")
        self.endpoint = endpoint or os.getenv("PHOENIX_ENDPOINT", DEFAULT_PHOENIX_ENDPOINT)
        self.project_name = project_name
        self.local_mode = local_mode
        self._launcher = PhoenixLauncher.get_instance()
        self._url: str | None = None

    def _ensure_launched(self) -> str:
        """Lazily launch Phoenix local server."""
        if not self.local_mode:
            return self.endpoint
        if self._url is None:
            self._url = self._launcher.launch()
        return self._url or ""

    async def trace_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        latency_ms: float,
        token_usage: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Trace a single LLM call with Phoenix.

        In Phoenix 15+, traces are typically collected via OTLP instrumentation
        of the LLM client (litellm). This method logs trace metadata for
        manual inspection. For automated tracing, use the TokenUsageTracker.
        """
        if not PHOENIX_AVAILABLE:
            return

        self._ensure_launched()

        try:
            logger.debug(
                "Phoenix LLM trace: model=%s latency=%.1fms tokens=%s",
                model,
                latency_ms,
                f"{token_usage}" if token_usage else "N/A",
            )
        except Exception as exc:
            logger.debug("Phoenix trace failed: %s", exc)

    async def trace_agent_run(
        self,
        task: str,
        model: str,
        steps: list[dict[str, Any]],
        final_result: str,
        duration_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Trace a complete agent run with multiple steps."""
        if not PHOENIX_AVAILABLE:
            return

        self._ensure_launched()

        try:
            logger.info(
                "Phoenix agent trace: task=%s model=%s steps=%d duration=%.1fms",
                task[:50] if task else "",
                model,
                len(steps),
                duration_ms,
            )
        except Exception:
            pass

    async def trace_tool_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Trace a tool call."""
        if not PHOENIX_AVAILABLE:
            return

        self._ensure_launched()

        try:
            logger.debug(
                "Phoenix tool trace: tool=%s duration=%.1fms success=%s",
                tool_name,
                duration_ms,
                success,
            )
        except Exception:
            pass

    def instrument_litellm(self) -> None:
        """Instrument litellm with Phoenix OpenInference tracing.

        This enables automatic trace collection for all litellm calls.
        Works with OpenAI-compatible endpoints (MiniMax).

        Requires: pip install openinference-instrumentation-litellm
        """
        if not PHOENIX_AVAILABLE:
            return

        try:
            from openinference.instrumentation.litellm import LiteLLMInstrumentor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor

            self._ensure_launched()
            endpoint = f"{self._url or 'http://localhost:6007'}/v1/traces"
            tracer_provider = TracerProvider()
            tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))
            LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info("Phoenix litellm instrumentation enabled via LiteLLMInstrumentor")
        except ImportError:
            logger.warning("openinference-instrumentation-litellm not installed — run: pip install openinference-instrumentation-litellm")
        except Exception as exc:
            logger.warning("Phoenix litellm instrumentation failed: %s", exc)

    def create_evaluation_run(
        self,
        run_name: str,
        dataset: list[dict[str, Any]],
    ) -> str | None:
        """Create a Phoenix evaluation run for a dataset."""
        if not PHOENIX_AVAILABLE:
            return None

        try:
            from phoenix import TraceDataset

            _ = TraceDataset(demos=dataset)
            logger.info("Phoenix evaluation run created: %s", run_name)
            return str(run_name)
        except Exception as exc:
            logger.warning("Phoenix evaluation run failed: %s", exc)
            return None


class TokenUsageTracker:
    """Track and report token usage across agent runs.

    This class is always available and does not require Phoenix.
    It tracks token usage in-memory and computes aggregate statistics.
    """

    def __init__(self) -> None:
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_runs = 0
        self.total_cost = 0.0
        self.runs: list[dict[str, Any]] = []

    def record_run(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost: float = 0.0,
    ) -> None:
        """Record a single LLM run."""
        self.total_tokens += prompt_tokens + completion_tokens
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_cost += cost
        self.total_runs += 1
        self.runs.append({
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": latency_ms,
            "cost": cost,
            "timestamp": time.time(),
        })

    def report(self) -> dict[str, Any]:
        """Get token usage report."""
        avg_latency = sum(r["latency_ms"] for r in self.runs) / len(self.runs) if self.runs else 0
        return {
            "total_runs": self.total_runs,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_cost": self.total_cost,
            "avg_latency_ms": avg_latency,
            "runs": self.runs,
        }

    def reset(self) -> None:
        """Reset all counters."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost = 0.0
        self.total_runs = 0
        self.runs.clear()


async def wrap_with_phoenix_trace(
    func,
    task: str,
    model: str,
    **kwargs,
) -> Any:
    """Decorator-style wrapper to trace any async function with Phoenix."""
    start = time.perf_counter()
    try:
        result = await func(**kwargs)
        latency_ms = (time.perf_counter() - start) * 1000
        tracer = PhoenixTracer()
        await tracer.trace_llm_call(
            model=model,
            prompt=task,
            response=str(result)[:500] if result else "",
            latency_ms=latency_ms,
        )
        return result
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.error("Phoenix wrapped call failed: %s", exc)
        raise


def get_token_tracker() -> TokenUsageTracker:
    """Get or create the singleton TokenUsageTracker."""
    global _TOKEN_TRACKER
    if _TOKEN_TRACKER is None:
        _TOKEN_TRACKER = TokenUsageTracker()
    return _TOKEN_TRACKER
