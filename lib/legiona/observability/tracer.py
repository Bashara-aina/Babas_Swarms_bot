"""
lib/legiona/observability/tracer.py
OpenTelemetry tracing for every M2.7 call and tool loop round.
Export to Jaeger (local) or stdout (CI/default).

Setup for local dev:
    docker run -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one
    Then open: http://localhost:16686
"""

from __future__ import annotations

import os
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

# Use OTEL_EXPORTER_OTLP_ENDPOINT env var for Jaeger/Grafana
# Default: console output (works in CI with no setup)
_provider = TracerProvider()

_exporter_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
if _exporter_endpoint:
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        _provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=_exporter_endpoint))
        )
    except ImportError:
        _provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )
else:
    _provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

trace.set_tracer_provider(_provider)
tracer = trace.get_tracer("legiona.m2_7")


@contextmanager
def trace_call(name: str, **attrs):
    with tracer.start_as_current_span(name) as span:
        for k, v in attrs.items():
            span.set_attribute(k, str(v))
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise
