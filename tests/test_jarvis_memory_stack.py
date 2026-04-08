"""Tests for working memory + cognition pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.cognition_pipeline import build_cognition_system_fragment, classify_intent_line
from core.working_memory import build_prompt_block, load_state, record_turn


def test_classify_intent_line() -> None:
    assert "code" in classify_intent_line("fix this import error in main.py").lower()
    hotel = classify_intent_line("hotel near me for tonight?").lower()
    assert "local" in hotel or "question" in hotel or "time-sensitive" in hotel


def test_cognition_fragment_not_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEGION_COGNITION_PIPELINE", raising=False)
    frag = build_cognition_system_fragment("1", "what is the best restaurant in Shibuya?", "location_advice")
    assert "COGNITION" in frag
    assert "location" in frag.lower() or "shape" in frag.lower()


def test_working_memory_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import core.working_memory as wm

    root = tmp_path / "wm"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(wm, "_ROOT", root)

    uid = "test_user_42"
    record_turn(uid, "help me debug pytorch dataloader oom?", assistant_snippet="Want batch size?")
    st = load_state(uid)
    assert st.get("current_focus")
    block = build_prompt_block(uid)
    assert "WORKING MEMORY" in block
