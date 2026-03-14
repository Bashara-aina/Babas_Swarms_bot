"""Tests for ModelRouter — per-task model selection."""
import pytest
from unittest.mock import patch
from swarms_bot.orchestrator.model_router import ModelRouter, TaskComplexity


class TestModelRouter:
    @pytest.fixture
    def router(self):
        return ModelRouter()

    def test_estimate_trivial(self, router):
        assert router.estimate_complexity("what is Python") == TaskComplexity.TRIVIAL

    def test_estimate_complex(self, router):
        assert router.estimate_complexity("implement a full-stack CRUD app with auth") == TaskComplexity.COMPLEX

    def test_estimate_critical(self, router):
        assert router.estimate_complexity("security audit of the production codebase") == TaskComplexity.CRITICAL

    def test_select_returns_string(self, router):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test"}):
            model, candidate = router.select("coding", TaskComplexity.MEDIUM)
        assert isinstance(model, str)
        assert len(model) > 0

    def test_prefers_local_for_privacy(self, router):
        with patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}):
            model, candidate = router.select("coding", prefer_privacy=True)
        assert "ollama" in model

    def test_fallback_when_no_keys(self, router):
        with patch.dict("os.environ", {}, clear=True):
            model, candidate = router.select("general")
        assert model == "groq/llama-3.3-70b-versatile"  # hardcoded fallback
