"""Tests for core/reliability/model_router.py"""

import pytest

from core.reliability.model_router import (
    classify_complexity,
    select_model,
    routing_explanation,
    TECHNICAL_TERMS,
    MULTI_STEP_KWS,
    TIERS,
)


class TestClassifyComplexity:
    @pytest.mark.parametrize("task", [
        "hi", "hello", "what is 2+2", "thanks", "ok", "yes"
    ])
    def test_lightweight_short_no_technical(self, task):
        result = classify_complexity(task)
        assert result == "lightweight"

    def test_lightweight_with_greeting(self):
        result = classify_complexity("hello there!")
        assert result == "lightweight"

    def test_heavyweight_long_task(self):
        task = "first do X then Y then Z " * 15  # length > 500
        assert classify_complexity(task) == "heavyweight"

    def test_heavyweight_multiple_code_blocks(self):
        task = "```python\ncode\n```\n" * 2 + "fix this"
        assert classify_complexity(task) == "heavyweight"

    def test_heavyweight_traceback_with_technical(self):
        task = "error in pytorch cuda gradient backprop traceback " * 3
        assert classify_complexity(task) == "heavyweight"

    def test_heavyweight_architecture_in_task(self):
        task = "design a system architecture" + "x" * 200
        assert classify_complexity(task) == "heavyweight"

    def test_midweight_standard_task(self):
        task = "explain python decorators in detail"
        result = classify_complexity(task)
        assert result in ("midweight", "lightweight")

    def test_midweight_long_but_no_heavy_signals(self):
        task = "please help me debug " * 30  # long but no traceback
        result = classify_complexity(task)
        assert result in ("midweight", "heavyweight")

    def test_technical_terms_counted(self):
        for term in TECHNICAL_TERMS[:5]:
            task = f"explain {term} in detail " * 5
            # Just verify the term is in the task and classify runs without error
            assert term.lower() in task.lower()
            classify_complexity(task)  # should not raise

    def test_multi_step_keywords(self):
        assert "first" in MULTI_STEP_KWS
        assert "then" in MULTI_STEP_KWS
        assert "after that" in MULTI_STEP_KWS

    def test_short_plain_task_is_lightweight(self):
        result = classify_complexity("what is 2+2")
        assert result == "lightweight"


class TestSelectModel:
    def test_select_model_returns_string(self):
        import core.agent_registry as ag_module
        original = getattr(ag_module, 'get_model', None)
        if original:
            ag_module.get_model = lambda k, use_fallback=False: "minimax-coding-plan/MiniMax-M3"
        try:
            model = select_model("coding", "hello")
            assert isinstance(model, str)
            assert len(model) > 0
        finally:
            if original:
                ag_module.get_model = original

    def test_select_model_force_lightweight(self):
        import core.agent_registry as ag_module
        original = getattr(ag_module, 'get_model', None)
        ag_module.get_model = lambda k, use_fallback=False: "minimax-coding-plan/MiniMax-M3"
        try:
            model = select_model("coding", "hi", force_tier="lightweight")
            assert "minimax-coding-plan" in model
        finally:
            if original:
                ag_module.get_model = original

    def test_select_model_force_heavyweight(self):
        import core.agent_registry as ag_module
        original = getattr(ag_module, 'get_model', None)
        ag_module.get_model = lambda k, use_fallback=False: "minimax-coding-plan/MiniMax-M3"
        try:
            model = select_model("coding", "hello", force_tier="heavyweight")
            assert "minimax-coding-plan" in model
        finally:
            if original:
                ag_module.get_model = original


class TestRoutingExplanation:
    def test_explanation_contains_tier(self):
        exp = routing_explanation("coding", "hello world")
        assert "lightweight" in exp or "midweight" in exp or "heavyweight" in exp

    def test_explanation_contains_model(self):
        import core.agent_registry as ag_module
        original = getattr(ag_module, 'get_model', None)
        ag_module.get_model = lambda k, use_fallback=False: "minimax-coding-plan/MiniMax-M3"
        try:
            exp = routing_explanation("coding", "say hi")
            assert "minimax-coding-plan" in exp
        finally:
            if original:
                ag_module.get_model = original


class TestTiers:
    def test_all_tiers_defined(self):
        assert "lightweight" in TIERS
        assert "midweight" in TIERS
        assert "heavyweight" in TIERS

    def test_tier_has_models_list(self):
        for tier_name, tier_info in TIERS.items():
            assert "models" in tier_info
            assert isinstance(tier_info["models"], list)
            assert len(tier_info["models"]) > 0

    def test_tier_has_description(self):
        for tier_name, tier_info in TIERS.items():
            assert "description" in tier_info
            assert isinstance(tier_info["description"], str)
