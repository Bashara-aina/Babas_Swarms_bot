"""Compatibility observability hooks for AgentOps and local metrics."""

from __future__ import annotations

from .observability import (
    get_metrics_snapshot,
    init_observability,
    render_metrics_html,
    track_agent,
)

__all__ = [
    "get_metrics_snapshot",
    "init_observability",
    "render_metrics_html",
    "track_agent",
]
