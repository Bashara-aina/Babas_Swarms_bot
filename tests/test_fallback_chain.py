"""Tests for core/reliability/fallback_chain.py"""

import pytest
from unittest.mock import patch

from core.reliability.fallback_chain import (
    FallbackChain,
    get_fallback_chain,
    get_best_provider,
    _FALLBACK_CHAINS,
)


class TestFallbackChain:
    def test_get_provider_chain_returns_list(self):
        chain = FallbackChain.get_provider_chain("coding")
        assert isinstance(chain, list)
        assert all(isinstance(t, tuple) and len(t) == 2 for t in chain)

    def test_get_provider_chain_coding_has_three_providers(self):
        chain = FallbackChain.get_provider_chain("coding")
        assert len(chain) == 3

    def test_get_provider_chain_chat_differs_from_coding(self):
        # chat and analysis use different model mixes
        analysis = FallbackChain.get_provider_chain("analysis")
        chat = FallbackChain.get_provider_chain("chat")
        # Analysis chain has llama3.3, chat chain has gemma4 - differ at position[2]
        assert analysis[2][0] != chat[2][0]

    def test_get_provider_chain_unknown_defaults_to_coding(self):
        unknown = FallbackChain.get_provider_chain("nonexistent")
        assert unknown == _FALLBACK_CHAINS["coding"]

    def test_get_provider_chain_analysis_has_llama(self):
        chain = FallbackChain.get_provider_chain("analysis")
        assert len(chain) == 3
        model_strings = [m for m, _ in chain]
        assert any("llama" in m.lower() for m in model_strings)

    @patch("core.reliability.fallback_chain.check_provider_health")
    def test_get_next_available_provider_skips_unhealthy(self, mock_health):
        mock_health.return_value = "unavailable"
        model, _name, idx = FallbackChain.get_next_available_provider("coding", skip_providers=set())
        # Should return emergency fallback (last in chain)
        assert "ollama" in model
        assert idx == len(_FALLBACK_CHAINS["coding"]) - 1

    @patch("core.reliability.fallback_chain.check_provider_health")
    def test_get_next_available_provider_respects_skip(self, mock_health):
        mock_health.return_value = "healthy"
        model, _name, _idx = FallbackChain.get_next_available_provider(
            "coding", skip_providers={"minimax-coding-plan"}
        )
        assert "minimax-coding-plan" not in model

    @patch("core.reliability.fallback_chain.check_provider_health")
    def test_get_optimal_provider_returns_first_healthy(self, mock_health):
        mock_health.side_effect = ["healthy", "unavailable", "unavailable"]
        model, name = FallbackChain.get_optimal_provider("coding")
        assert "minimax-coding-plan" in model

    @patch("core.reliability.fallback_chain.check_provider_health")
    def test_get_fallback_stats_returns_all_providers(self, mock_health):
        mock_health.return_value = "healthy"
        stats = FallbackChain.get_fallback_stats("coding")
        assert isinstance(stats, dict)
        assert len(stats) == 3

    def test_get_fallback_chain_returns_model_strings(self):
        chain = get_fallback_chain("coding")
        assert all(isinstance(s, str) for s in chain)
        assert len(chain) == 3

    @patch("core.reliability.fallback_chain.FallbackChain.get_optimal_provider")
    def test_get_best_provider_returns_model_string(self, mock_optimal):
        mock_optimal.return_value = ("minimax-coding-plan/MiniMax-M2.7", "MiniMax M2.7")
        model = get_best_provider("coding")
        assert model == "minimax-coding-plan/MiniMax-M2.7"


class TestFallbackChainEdgeCases:
    def test_empty_agent_key_defaults_to_coding(self):
        chain = FallbackChain.get_provider_chain("")
        assert chain == _FALLBACK_CHAINS["coding"]

    def test_all_chains_have_valid_model_strings(self):
        for key in _FALLBACK_CHAINS:
            chain = _FALLBACK_CHAINS[key]
            for model, name in chain:
                assert "/" in model or model.startswith("ollama")
                assert len(name) > 0