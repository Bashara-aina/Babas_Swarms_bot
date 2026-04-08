"""Jarvis bundle gather — no LLM (layers disabled via env)."""

from __future__ import annotations

import asyncio

import pytest


def test_gather_jarvis_bundle_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEGION_JARVIS_MEMORY", "0")
    monkeypatch.setenv("SCREENPIPE_ENABLED", "0")
    monkeypatch.setenv("LEGION_JARVIS_WHATSAPP", "0")
    monkeypatch.setenv("LEGION_JARVIS_MCP_WHATSAPP", "0")
    monkeypatch.setenv("LEGION_JARVIS_CALENDAR", "0")
    monkeypatch.setenv("LEGION_JARVIS_EMOTION", "0")

    from core.jarvis_orchestrator import gather_jarvis_bundle

    b = asyncio.run(gather_jarvis_bundle("fix the training script", "4242"))
    assert b["goal"] == "fix the training script"
    assert b["memory"] == ""
    assert b["screenpipe"] == ""
    assert b["whatsapp"] == ""
    assert b["calendar"] == ""
    assert b["emotion"] == ""
