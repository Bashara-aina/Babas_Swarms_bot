"""Tests for swarms_bot/routing/cost_router.py — CostAwareRouter."""

from unittest.mock import patch

import pytest


class TestCostAwareRouter:
    """Tests for CostAwareRouter initialization and routing."""

    def test_router_init(self):
        """Router should initialize with empty routing log."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        assert router.routing_log == []
        assert router._total_estimated_savings == 0.0

    def test_select_model_returns_tuple(self):
        """select_model should return (model_id, complexity, tier_name)."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        result = router.select_model("general", "hello world")
        assert isinstance(result, tuple)
        assert len(result) == 3
        model_id, complexity, tier = result
        assert isinstance(model_id, str)
        assert tier in ("free", "budget", "standard", "premium", "fallback", "local")

    def test_select_model_vision_agent(self):
        """Vision agent should always use local model."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        model_id, complexity, tier = router.select_model("vision", "analyze this screenshot")
        assert model_id == "ollama_chat/gemma4:e4b"
        assert tier == "local"

    def test_select_model_complexity_classification(self):
        """Long technical task should be classified as complex or higher."""
        from swarms_bot.routing.cost_router import CostAwareRouter, TaskComplexity

        router = CostAwareRouter()
        model_id, complexity, tier = router.select_model(
            "coding",
            "implement a distributed training pipeline with gradient checkpointing "
            "and mixed precision for a transformer model using PyTorch DDP. "
            "First do this, then do that, then deploy to kubernetes with docker.",
        )
        assert complexity in (TaskComplexity.MODERATE, TaskComplexity.COMPLEX, TaskComplexity.EXPERT)

    def test_select_model_trivial_task(self):
        """Short non-technical task should be trivial."""
        from swarms_bot.routing.cost_router import CostAwareRouter, TaskComplexity

        router = CostAwareRouter()
        model_id, complexity, tier = router.select_model("general", "hi")
        assert complexity == TaskComplexity.TRIVIAL

    def test_estimate_cost(self):
        """estimate_cost should return a float."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        cost = router.estimate_cost("test task", "gemini/gemini-1.5-pro")
        assert isinstance(cost, float)
        assert cost >= 0.0

    def test_estimate_cost_free_tier(self):
        """Free tier models should have zero cost."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        cost = router.estimate_cost("test task", "minimax/MiniMax-Text-01")
        assert cost == 0.0

    def test_get_routing_stats_empty(self):
        """Empty routing log should return basic stats."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        stats = router.get_routing_stats()
        assert stats["total_routes"] == 0

    def test_get_routing_stats_after_routing(self):
        """After routing, stats should reflect the routing."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        router.select_model("general", "hello world")
        stats = router.get_routing_stats()
        assert stats["total_routes"] == 1

    def test_format_stats_html(self):
        """format_stats_html should return HTML string."""
        from swarms_bot.routing.cost_router import CostAwareRouter

        router = CostAwareRouter()
        html = router.format_stats_html()
        assert isinstance(html, str)
        assert "Cost Router" in html or "No routes" in html


class TestClassifyComplexity:
    """Tests for classify_complexity()."""

    def test_classify_trivial(self):
        """Short non-technical phrases should be trivial."""
        from swarms_bot.routing.cost_router import TaskComplexity, classify_complexity

        result = classify_complexity("hi")
        assert result == TaskComplexity.TRIVIAL

    def test_classify_simple(self):
        """Basic questions should be simple or higher."""
        from swarms_bot.routing.cost_router import TaskComplexity, classify_complexity

        result = classify_complexity(
            "what is the difference between python and javascript in terms of "
            "performance and use cases for web development?"
        )
        assert result in (TaskComplexity.SIMPLE, TaskComplexity.MODERATE)

    def test_classify_complex_technical(self):
        """Multi-step technical tasks should be complex."""
        from swarms_bot.routing.cost_router import TaskComplexity, classify_complexity

        result = classify_complexity("first do X then Y then Z with docker and kubernetes deploy")
        assert result in (TaskComplexity.COMPLEX, TaskComplexity.EXPERT)

    def test_classify_expert_architecture(self):
        """Architecture + length should be expert."""
        from swarms_bot.routing.cost_router import TaskComplexity, classify_complexity

        result = classify_complexity(
            "design a comprehensive microservices architecture for a highly scalable distributed system "
            "with proper load balancing, fault tolerance, and graceful degradation patterns. "
            "The architecture should include service mesh integration, observability dashboards, "
            "distributed tracing with OpenTelemetry, centralized logging with ELK stack, "
            "container orchestration via Kubernetes with horizontal pod autoscaling, "
            "and comprehensive monitoring with Prometheus and Grafana. "
            "Each service should follow clean architecture principles with domain-driven design, "
            "CQRS pattern for read/write separation, and event sourcing for state management."
        )
        assert result == TaskComplexity.EXPERT
