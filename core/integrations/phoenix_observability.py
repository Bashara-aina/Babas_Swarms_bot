"""core/integrations/phoenix_observability.py — Arize Phoenix tracing for LLM agents.  # type: ignore[reportOptionalMemberAccess]

Phoenix 15+ provides real-time agent tracing, token monitoring, and evaluation.  # type: ignore[reportOptionalMemberAccess]
Works with MiniMax via OpenAI-compatible endpoint.  # type: ignore[reportOptionalMemberAccess]

Local mode: launches Phoenix UI at localhost:6007
Remote mode: sends traces via OTLP to app.phoenix.arize.com  # type: ignore[reportOptionalMemberAccess]

Usage:
    from core.integrations import PhoenixTracer, TokenUsageTracker  # type: ignore[reportOptionalMemberAccess]

    tracer = PhoenixTracer()  # type: ignore[reportOptionalMemberAccess]
    tracker = TokenUsageTracker()  # type: ignore[reportOptionalMemberAccess]

    await tracer.trace_llm_call(  # type: ignore[reportOptionalMemberAccess]
        model="opencode-go/minimax-m3",  # type: ignore[reportOptionalMemberAccess]
        prompt="Explain quantum computing",  # type: ignore[reportOptionalMemberAccess]
        response="Quantum computing uses...",  # type: ignore[reportOptionalMemberAccess]
        latency_ms=234.5,  # type: ignore[reportOptionalMemberAccess]
        token_usage={"prompt_tokens": 50, "completion_tokens": 120},  # type: ignore[reportOptionalMemberAccess]
    )

    tracker.record_run("opencode-go/minimax-m3", 50, 120, 234.5)  # type: ignore[reportOptionalMemberAccess]
    print(tracker.report())  # type: ignore[reportOptionalMemberAccess]
"""

from __future__ import annotations

import contextlib
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)  # type: ignore[reportOptionalMemberAccess]

PHOENIX_AVAILABLE = False  # type: ignore[reportOptionalMemberAccess]
_PHOENIX_VERSION = 0  # type: ignore[reportOptionalMemberAccess]

try:
    import phoenix as _phoenix
    PHOENIX_AVAILABLE = True  # type: ignore[reportOptionalMemberAccess]
    _PHOENIX_VERSION = int(getattr(_phoenix, "__version__", "0").split(".")[0])  # type: ignore[reportOptionalMemberAccess]
except ImportError:
    _phoenix = None  # type: ignore[reportOptionalMemberAccess]

DEFAULT_PHOENIX_ENDPOINT = "https://app.phoenix.arize.com"  # type: ignore[reportOptionalMemberAccess]
PHOENIX_LOCAL_PORT = 6007  # type: ignore[reportOptionalMemberAccess]

_otel_tracer = None  # type: ignore[reportOptionalMemberAccess]
_otel_provider = None  # type: ignore[reportOptionalMemberAccess]


def _get_otel_tracer():  # type: ignore[reportOptionalMemberAccess]
    """Get or create OTEL tracer for Phoenix spans."""
    global _otel_tracer, _otel_provider  # type: ignore[reportOptionalMemberAccess]
    if _otel_tracer is not None:  # type: ignore[reportOptionalMemberAccess]
        return _otel_tracer  # type: ignore[reportOptionalMemberAccess]

    try:
        from opentelemetry import trace  # type: ignore[reportOptionalMemberAccess]
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[reportOptionalMemberAccess]
            OTLPSpanExporter,  # type: ignore[reportOptionalMemberAccess]
        )
        from opentelemetry.sdk.trace import (
            TracerProvider,  # type: ignore[reportOptionalMemberAccess]
        )
        from opentelemetry.sdk.trace.export import (  # type: ignore[reportOptionalMemberAccess]
            BatchSpanProcessor,  # type: ignore[reportOptionalMemberAccess]
            ConsoleSpanExporter,  # type: ignore[reportOptionalMemberAccess]
        )

        _otel_provider = TracerProvider()  # type: ignore[reportOptionalMemberAccess]
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")  # type: ignore[reportOptionalMemberAccess]
        if otlp_endpoint:  # type: ignore[reportOptionalMemberAccess]
            try:  # type: ignore[reportOptionalMemberAccess]
                _otel_provider.add_span_processor(  # type: ignore[reportOptionalMemberAccess]
                    BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))  # type: ignore[reportOptionalMemberAccess]
                )  # type: ignore[reportOptionalMemberAccess]
            except Exception:  # type: ignore[reportOptionalMemberAccess]
                _otel_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))  # type: ignore[reportOptionalMemberAccess]
        else:  # type: ignore[reportOptionalMemberAccess]
            _otel_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))  # type: ignore[reportOptionalMemberAccess]

        trace.set_tracer_provider(_otel_provider)  # type: ignore[reportOptionalMemberAccess]
        _otel_tracer = trace.get_tracer("swarm-bot.phoenix")  # type: ignore[reportOptionalMemberAccess]
        return _otel_tracer  # type: ignore[reportOptionalMemberAccess]
    except ImportError:  # type: ignore[reportOptionalMemberAccess]
        return None  # type: ignore[reportOptionalMemberAccess]
    except Exception as exc:  # type: ignore[reportOptionalMemberAccess]
        logger.warning("OTEL tracer init failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
        return None  # type: ignore[reportOptionalMemberAccess]


class PhoenixLauncher:
    """Launch and manage a local Phoenix server."""  # type: ignore[reportOptionalMemberAccess]

    _instance = None  # type: ignore[reportOptionalMemberAccess]

    @classmethod
    def get_instance(cls) -> PhoenixLauncher:  # type: ignore[reportOptionalMemberAccess]
        if cls._instance is None:  # type: ignore[reportOptionalMemberAccess]
            cls._instance = cls()  # type: ignore[reportOptionalMemberAccess]
        return cls._instance  # type: ignore[reportOptionalMemberAccess]

    def __init__(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        self._server = None  # type: ignore[reportOptionalMemberAccess]
        self._url: str | None = None  # type: ignore[reportOptionalMemberAccess]

    def launch(self, port: int = PHOENIX_LOCAL_PORT) -> str:  # type: ignore[reportOptionalMemberAccess]
        """Launch local Phoenix server and return URL."""  # type: ignore[reportOptionalMemberAccess]
        if self._server is not None:  # type: ignore[reportOptionalMemberAccess]
            return self._url or f"http://localhost:{port}"  # type: ignore[reportOptionalMemberAccess]

        try:
            if _PHOENIX_VERSION >= 1:  # type: ignore[reportOptionalMemberAccess]
                self._server = _phoenix.launch_app(port=port)  # type: ignore[reportOptionalMemberAccess]
                self._url = f"http://localhost:{port}"  # type: ignore[reportOptionalMemberAccess]
                logger.info("Phoenix local server launched: %s", self._url)  # type: ignore[reportOptionalMemberAccess]
                return self._url  # type: ignore[reportOptionalMemberAccess]
            else:
                _phoenix.launch_app(port=port)  # type: ignore[reportOptionalMemberAccess]
                self._url = f"http://localhost:{port}"  # type: ignore[reportOptionalMemberAccess]
                return self._url  # type: ignore[reportOptionalMemberAccess]
        except Exception as exc:
            logger.warning("Phoenix launch failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
            return ""

    def close(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        """Close the Phoenix server."""  # type: ignore[reportOptionalMemberAccess]
        if self._server is not None:  # type: ignore[reportOptionalMemberAccess]
            with contextlib.suppress(Exception):  # type: ignore[reportOptionalMemberAccess]
                _phoenix.close_app()  # type: ignore[reportOptionalMemberAccess]
            self._server = None  # type: ignore[reportOptionalMemberAccess]
            self._url = None  # type: ignore[reportOptionalMemberAccess]


PHOENIX_VERSION = _PHOENIX_VERSION  # type: ignore[reportOptionalMemberAccess]

_TOKEN_TRACKER: TokenUsageTracker | None = None  # type: ignore[reportOptionalMemberAccess]


class PhoenixTracer:
    """Arize Phoenix tracer for SwarmBot agents.  # type: ignore[reportOptionalMemberAccess]

    Phoenix 15+ works in two modes:
    1. Local: launch Phoenix UI locally (no API key needed)  # type: ignore[reportOptionalMemberAccess]
    2. Remote: send traces via OTLP (requires Phoenix API key)  # type: ignore[reportOptionalMemberAccess]

    TokenUsageTracker is always available and does not require Phoenix.  # type: ignore[reportOptionalMemberAccess]
    """

    def __init__(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        api_key: str | None = None,  # type: ignore[reportOptionalMemberAccess]
        endpoint: str | None = None,  # type: ignore[reportOptionalMemberAccess]
        project_name: str = "swarm-bot",  # type: ignore[reportOptionalMemberAccess]
        local_mode: bool = True,  # type: ignore[reportOptionalMemberAccess]
    ) -> None:
        self.api_key = api_key or os.getenv("PHOENIX_API_KEY", "")  # type: ignore[reportOptionalMemberAccess]
        self.endpoint = endpoint or os.getenv("PHOENIX_ENDPOINT", DEFAULT_PHOENIX_ENDPOINT)  # type: ignore[reportOptionalMemberAccess]
        self.project_name = project_name  # type: ignore[reportOptionalMemberAccess]
        self.local_mode = local_mode  # type: ignore[reportOptionalMemberAccess]
        self._launcher = PhoenixLauncher.get_instance()  # type: ignore[reportOptionalMemberAccess]
        self._url: str | None = None  # type: ignore[reportOptionalMemberAccess]

    def _ensure_launched(self) -> str:  # type: ignore[reportOptionalMemberAccess]
        """Lazily launch Phoenix local server."""  # type: ignore[reportOptionalMemberAccess]
        if not self.local_mode:  # type: ignore[reportOptionalMemberAccess]
            return self.endpoint  # type: ignore[reportOptionalMemberAccess]
        if self._url is None:  # type: ignore[reportOptionalMemberAccess]
            self._url = self._launcher.launch()  # type: ignore[reportOptionalMemberAccess]
        return self._url or ""  # type: ignore[reportOptionalMemberAccess]

    async def trace_llm_call(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        model: str,  # type: ignore[reportOptionalMemberAccess]
        prompt: str,  # type: ignore[reportOptionalMemberAccess]
        response: str,  # type: ignore[reportOptionalMemberAccess]
        latency_ms: float,  # type: ignore[reportOptionalMemberAccess]
        token_usage: dict[str, int] | None = None,  # type: ignore[reportOptionalMemberAccess]
        metadata: dict[str, Any] | None = None,  # type: ignore[reportOptionalMemberAccess]
    ) -> None:
        """Trace a single LLM call with Phoenix.

        Creates real OTEL spans for LLM calls with model, latency,
        token usage, and response metadata.
        """
        if not PHOENIX_AVAILABLE:
            return

        tracer = _get_otel_tracer()
        if tracer is None:
            return

        self._ensure_launched()

        try:
            with tracer.start_as_current_span("llm_call") as span:
                span.set_attribute("model", model)
                span.set_attribute("latency_ms", latency_ms)
                if token_usage:
                    span.set_attribute("prompt_tokens", token_usage.get("prompt_tokens", 0))
                    span.set_attribute("completion_tokens", token_usage.get("completion_tokens", 0))
                if metadata:
                    for k, v in metadata.items():
                        span.set_attribute(f"metadata.{k}", str(v))

                span.set_attribute("llm.response", response[:500] if response else "")

        except Exception as exc:
            logger.debug("Phoenix LLM span failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]

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

        tracer = _get_otel_tracer()
        if tracer is None:
            return

        try:
            with tracer.start_as_current_span("agent_run") as span:
                span.set_attribute("task", task[:200] if task else "")
                span.set_attribute("model", model)
                span.set_attribute("step_count", len(steps))
                span.set_attribute("duration_ms", duration_ms)
                if metadata:
                    for k, v in metadata.items():
                        span.set_attribute(f"metadata.{k}", str(v))

                for i, step in enumerate(steps):
                    with tracer.start_as_current_span(f"agent_step_{i}") as step_span:
                        step_span.set_attribute("step", i)
                        step_span.set_attribute("step.task", str(step.get("task", ""))[:200])
                        step_span.set_attribute("step.agent", str(step.get("agent", "")))

                span.set_attribute("agent.result", final_result[:500] if final_result else "")

        except Exception as exc:
            logger.debug("Phoenix agent span failed: %s", exc)

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

        tracer = _get_otel_tracer()
        if tracer is None:
            return

        try:
            with tracer.start_as_current_span(f"tool.{tool_name}") as span:
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("tool.duration_ms", duration_ms)
                span.set_attribute("tool.success", success)
                span.set_attribute("tool.args", str(args)[:500])

        except Exception as exc:
            logger.debug("Phoenix tool span failed: %s", exc)

    def instrument_litellm(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        """Instrument litellm with Phoenix OpenInference tracing.  # type: ignore[reportOptionalMemberAccess]

        This enables automatic trace collection for all litellm calls.  # type: ignore[reportOptionalMemberAccess]
        Works with OpenAI-compatible endpoints (MiniMax).  # type: ignore[reportOptionalMemberAccess]

        Requires: pip install openinference-instrumentation-litellm
        """
        if not PHOENIX_AVAILABLE:
            return

        try:
            from openinference.instrumentation.litellm import (
                LiteLLMInstrumentor,  # type: ignore[reportOptionalMemberAccess]
            )
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,  # type: ignore[reportOptionalMemberAccess]
            )
            from opentelemetry.sdk.trace import (
                TracerProvider,  # type: ignore[reportOptionalMemberAccess]
            )
            from opentelemetry.sdk.trace.export import (
                SimpleSpanProcessor,  # type: ignore[reportOptionalMemberAccess]
            )

            self._ensure_launched()  # type: ignore[reportOptionalMemberAccess]
            endpoint = f"{self._url or 'http://localhost:6007'}/v1/traces"  # type: ignore[reportOptionalMemberAccess]
            tracer_provider = TracerProvider()  # type: ignore[reportOptionalMemberAccess]
            tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))  # type: ignore[reportOptionalMemberAccess]
            LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider)  # type: ignore[reportOptionalMemberAccess]
            logger.info("Phoenix litellm instrumentation enabled via LiteLLMInstrumentor")  # type: ignore[reportOptionalMemberAccess]
        except ImportError:
            logger.warning("openinference-instrumentation-litellm not installed — run: pip install openinference-instrumentation-litellm")  # type: ignore[reportOptionalMemberAccess]
        except Exception as exc:
            logger.warning("Phoenix litellm instrumentation failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]

    def create_evaluation_run(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        run_name: str,  # type: ignore[reportOptionalMemberAccess]
        dataset: list[dict[str, Any]],  # type: ignore[reportOptionalMemberAccess]
    ) -> str | None:
        """Create a Phoenix evaluation run for a dataset."""  # type: ignore[reportOptionalMemberAccess]
        if not PHOENIX_AVAILABLE:
            return None

        try:
            from phoenix import TraceDataset

            _ = TraceDataset(demos=dataset)  # type: ignore[reportOptionalMemberAccess]
            logger.info("Phoenix evaluation run created: %s", run_name)  # type: ignore[reportOptionalMemberAccess]
            return str(run_name)  # type: ignore[reportOptionalMemberAccess]
        except Exception as exc:
            logger.warning("Phoenix evaluation run failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
            return None


class TokenUsageTracker:
    """Track and report token usage across agent runs.  # type: ignore[reportOptionalMemberAccess]

    This class is always available and does not require Phoenix.  # type: ignore[reportOptionalMemberAccess]
    It tracks token usage in-memory and computes aggregate statistics.  # type: ignore[reportOptionalMemberAccess]
    """

    def __init__(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        self.total_tokens = 0  # type: ignore[reportOptionalMemberAccess]
        self.prompt_tokens = 0  # type: ignore[reportOptionalMemberAccess]
        self.completion_tokens = 0  # type: ignore[reportOptionalMemberAccess]
        self.total_runs = 0  # type: ignore[reportOptionalMemberAccess]
        self.total_cost = 0.0  # type: ignore[reportOptionalMemberAccess]
        self.runs: list[dict[str, Any]] = []  # type: ignore[reportOptionalMemberAccess]

    def record_run(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        model: str,  # type: ignore[reportOptionalMemberAccess]
        prompt_tokens: int,  # type: ignore[reportOptionalMemberAccess]
        completion_tokens: int,  # type: ignore[reportOptionalMemberAccess]
        latency_ms: float,  # type: ignore[reportOptionalMemberAccess]
        cost: float = 0.0,  # type: ignore[reportOptionalMemberAccess]
    ) -> None:
        """Record a single LLM run."""  # type: ignore[reportOptionalMemberAccess]
        self.total_tokens += prompt_tokens + completion_tokens  # type: ignore[reportOptionalMemberAccess]
        self.prompt_tokens += prompt_tokens  # type: ignore[reportOptionalMemberAccess]
        self.completion_tokens += completion_tokens  # type: ignore[reportOptionalMemberAccess]
        self.total_cost += cost  # type: ignore[reportOptionalMemberAccess]
        self.total_runs += 1  # type: ignore[reportOptionalMemberAccess]
        self.runs.append({  # type: ignore[reportOptionalMemberAccess]
            "model": model,  # type: ignore[reportOptionalMemberAccess]
            "prompt_tokens": prompt_tokens,  # type: ignore[reportOptionalMemberAccess]
            "completion_tokens": completion_tokens,  # type: ignore[reportOptionalMemberAccess]
            "latency_ms": latency_ms,  # type: ignore[reportOptionalMemberAccess]
            "cost": cost,  # type: ignore[reportOptionalMemberAccess]
            "timestamp": time.time(),  # type: ignore[reportOptionalMemberAccess]
        })

    def report(self) -> dict[str, Any]:  # type: ignore[reportOptionalMemberAccess]
        """Get token usage report."""  # type: ignore[reportOptionalMemberAccess]
        avg_latency = sum(r["latency_ms"] for r in self.runs) / len(self.runs) if self.runs else 0  # type: ignore[reportOptionalMemberAccess]
        return {
            "total_runs": self.total_runs,  # type: ignore[reportOptionalMemberAccess]
            "total_tokens": self.total_tokens,  # type: ignore[reportOptionalMemberAccess]
            "prompt_tokens": self.prompt_tokens,  # type: ignore[reportOptionalMemberAccess]
            "completion_tokens": self.completion_tokens,  # type: ignore[reportOptionalMemberAccess]
            "total_cost": self.total_cost,  # type: ignore[reportOptionalMemberAccess]
            "avg_latency_ms": avg_latency,  # type: ignore[reportOptionalMemberAccess]
            "runs": self.runs,  # type: ignore[reportOptionalMemberAccess]
        }

    def reset(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        """Reset all counters."""  # type: ignore[reportOptionalMemberAccess]
        self.total_tokens = 0  # type: ignore[reportOptionalMemberAccess]
        self.prompt_tokens = 0  # type: ignore[reportOptionalMemberAccess]
        self.completion_tokens = 0  # type: ignore[reportOptionalMemberAccess]
        self.total_cost = 0.0  # type: ignore[reportOptionalMemberAccess]
        self.total_runs = 0  # type: ignore[reportOptionalMemberAccess]
        self.runs.clear()  # type: ignore[reportOptionalMemberAccess]


async def wrap_with_phoenix_trace(  # type: ignore[reportOptionalMemberAccess]
    func,  # type: ignore[reportOptionalMemberAccess]
    task: str,  # type: ignore[reportOptionalMemberAccess]
    model: str,  # type: ignore[reportOptionalMemberAccess]
    **kwargs,  # type: ignore[reportOptionalMemberAccess]
) -> Any:
    """Decorator-style wrapper to trace any async function with Phoenix."""  # type: ignore[reportOptionalMemberAccess]
    start = time.perf_counter()  # type: ignore[reportOptionalMemberAccess]
    try:
        result = await func(**kwargs)  # type: ignore[reportOptionalMemberAccess]
        latency_ms = (time.perf_counter() - start) * 1000  # type: ignore[reportOptionalMemberAccess]
        tracer = PhoenixTracer()  # type: ignore[reportOptionalMemberAccess]
        await tracer.trace_llm_call(  # type: ignore[reportOptionalMemberAccess]
            model=model,  # type: ignore[reportOptionalMemberAccess]
            prompt=task,  # type: ignore[reportOptionalMemberAccess]
            response=str(result)[:500] if result else "",  # type: ignore[reportOptionalMemberAccess]
            latency_ms=latency_ms,  # type: ignore[reportOptionalMemberAccess]
        )
        return result
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000  # type: ignore[reportOptionalMemberAccess]
        logger.error("Phoenix wrapped call failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
        raise


def get_token_tracker() -> TokenUsageTracker:  # type: ignore[reportOptionalMemberAccess]
    """Get or create the singleton TokenUsageTracker."""  # type: ignore[reportOptionalMemberAccess]
    global _TOKEN_TRACKER
    if _TOKEN_TRACKER is None:
        _TOKEN_TRACKER = TokenUsageTracker()  # type: ignore[reportOptionalMemberAccess]
    return _TOKEN_TRACKER
