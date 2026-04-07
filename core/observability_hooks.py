"""Compatibility observability hooks for AgentOps and local metrics."""

from __future__ import annotations

from .observability import init_observability, get_metrics_snapshot, render_metrics_html, track_agent

__all__ = [
    "init_observability",
    "get_metrics_snapshot",
    "render_metrics_html",
    "track_agent",
]
