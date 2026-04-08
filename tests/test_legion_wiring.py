"""Wiring tests for tier-3 agents, router skill, and LiveKit URL helper."""

from __future__ import annotations

import pytest

from agents.simulation_agent import should_trigger_simulation
from bridges.livekit_bridge import meet_join_url


def test_should_trigger_simulation() -> None:
    assert should_trigger_simulation("Simulate how guests react") is True
    assert should_trigger_simulation("hello") is False


def test_meet_join_url_empty_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LIVEKIT_URL", raising=False)
    assert meet_join_url("tok") == ""


def test_meet_join_url_builds_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVEKIT_URL", "ws://localhost:7880")
    url = meet_join_url("jwt-token", room="legion")
    assert "meet.livekit.io" in url
    assert "jwt-token" in url


def test_strategic_simulation_skill_registered() -> None:
    from core.autonomous_router import SKILL_PATTERNS

    assert "strategic_simulation" in SKILL_PATTERNS
    assert SKILL_PATTERNS["strategic_simulation"]["handler"] == "simulation"


def test_jarvis_orchestrate_skill_registered() -> None:
    from core.autonomous_router import SKILL_PATTERNS

    assert "jarvis_orchestrate" in SKILL_PATTERNS
    assert SKILL_PATTERNS["jarvis_orchestrate"]["handler"] == "jarvis"


def test_jarvis_keyword_routes_above_threshold() -> None:
    from core.autonomous_router import AutonomousRouter

    class _Mem:
        pass

    class _Ref:
        pass

    router = AutonomousRouter(_Mem(), _Ref())
    m = router.analyze(
        "Can you check what's on my screen and help with this error?"
    )
    assert m.skill_name == "jarvis_orchestrate"
    assert m.confidence >= 0.35
