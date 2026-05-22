---
title: "Observability Stack"
created: 2026-05-03
updated: 2026-05-17
tags: [observability, monitoring, operations, phoenix, opentelemetry, langsmith]
wikilinks: [.wiki/concepts/memory-architecture.md, .wiki/architecture/integration-layer.md]
---

# Observability Stack

> Operational runbook for SwarmBot's observability infrastructure.
> Updated 2026-05-17 based on `core/integrations/phoenix_observability.py` audit.

## Stack Overview

| Component | Version | Purpose |
|-----------|---------|---------|
| **Arize Phoenix** | 15.1.0 | LLM tracing, agent monitoring, evaluation |
| **OpenTelemetry** | — | Distributed tracing, span collection |
| **LangSmith** | 0.7.30 | LLM eval & feedback (env-gated, not active) |
| **TokenUsageTracker** | — | In-memory token accounting (always-on) |

---

## Arize Phoenix

### Local Mode (default)

Phoenix UI launches at `http://localhost:6007` — no API key required.
Span data written to console (`ConsoleSpanExporter`) or OTLP endpoint.

```python
from core.integrations import PhoenixTracer
tracer = PhoenixTracer(local_mode=True)
```

### Remote Mode

Sends spans via OTLP to `https://app.phoenix.arize.com` or custom endpoint.

```python
tracer = PhoenixTracer(
    api_key=os.getenv("PHOENIX_API_KEY"),
    endpoint=os.getenv("PHOENIX_ENDPOINT", "https://app.phoenix.arize.com"),
    local_mode=False
)
```

### Available Instrumentation

- `PhoenixTracer.trace_llm_call()` — single LLM call span
- `PhoenixTracer.trace_agent_run()` — multi-step agent run
- `PhoenixTracer.trace_tool_call()` — individual tool execution
- `PhoenixTracer.instrument_litellm()` — auto-instrument all litellm calls (requires `pip install openinference-instrumentation-litellm`)
- `PhoenixTracer.create_evaluation_run()` — Phoenix evaluation dataset
- `TokenUsageTracker` — always-on in-memory token counter (no Phoenix needed)

### Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `PHOENIX_API_KEY` | — | For remote Phoenix |
| `PHOENIX_ENDPOINT` | `https://app.phoenix.arize.com` | Remote OTLP target |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `localhost:4317` | OTLP collector (GRPC) |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | — | Override for traces only |

### Fallback Chain

`_get_otel_tracer()` (phoenix_observability.py:54-90):
1. Read `OTEL_EXPORTER_OTLP_ENDPOINT` env var
2. If set → try `OTLPSpanExporter(endpoint=otlp_endpoint)` with `BatchSpanProcessor`
3. If fails → fallback to `ConsoleSpanExporter()`
4. If not set → use `ConsoleSpanExporter()` directly

### Token Tracker

`TokenUsageTracker` (always available, no Phoenix required):
```python
from core.integrations import get_token_tracker
tracker = get_token_tracker()
tracker.record_run("minimax/MiniMax-M2.7", prompt_tokens=50, completion_tokens=120, latency_ms=234.5)
print(tracker.report())
```

### Known Issues

- OTLP collector at `localhost:4317` may not be reachable locally — spans fall back to console
- LangChain tracing not active (env vars not set)
- LiteLLM instrumentation requires optional `openinference-instrumentation-litellm` package

---

## OpenTelemetry

Single OTLP exporter reads `OTEL_EXPORTER_OTLP_ENDPOINT`.
If unset or unreachable, traces go to console only.

Span attributes set on LLM calls:
- `model` — model name
- `latency_ms` — response time
- `prompt_tokens` / `completion_tokens`
- `llm.response` — first 500 chars

---

## LangSmith

**Status: Installed but not active.** LangChain tracing env vars not set:
- `LANGCHAIN_TRACING_V2` — not set
- `LANGCHAIN_API_KEY` — not set
- `LANGCHAIN_PROJECT` — not set

To activate, set these in environment or `.env`:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-key>
LANGCHAIN_PROJECT=swarm-bot
```

---

## Performance Metrics

Ruflo `performance_metrics` tool exposes:
- `cpu` / `memory` / `latency` / `throughput` per component
- Aggregation: `avg` / `min` / `max` / `p50` / `p95` / `p99`
- Time ranges: `1h`, `24h`, `7d`

Ruflo `performance_bottleneck` detects system bottlenecks.

Ruflo `performance_benchmark` runs benchmark suites: `all`, `memory`, `neural`, `swarm`, `io`.

---

## See Also

- `core/integrations/phoenix_observability.py` — Phoenix + OTEL integration (423 lines)
- `core/integrations/token_tracker.py` — (referenced in doc, not yet audited)
- `.wiki/architecture/integration-layer.md` — full integration map
- `.wiki/concepts/memory-architecture.md` — ChromaDB + mem0 memory stack