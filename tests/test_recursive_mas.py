"""Tests for core/recursive_mas.py — RecursiveMAS implementation based on arXiv:2604.25917."""

import pytest


class TestRecursiveLink:
    """Tests for RecursiveLink module."""

    def test_recursive_link_initialization(self):
        """RecursiveLink should initialize with correct dimensions."""
        from core.recursive_mas import RecursiveLink, RecursiveLinkConfig

        config = RecursiveLinkConfig(hidden_dim=512)
        link = RecursiveLink(config, "inner")

        assert link.link_type == "inner"
        assert link.config.hidden_dim == 512

    def test_recursive_link_forward_inner(self):
        """Inner link forward pass should preserve residual semantics."""
        from core.recursive_mas import RecursiveLink, RecursiveLinkConfig

        config = RecursiveLinkConfig(hidden_dim=128, use_residual=True)
        link = RecursiveLink(config, "inner")

        # Test with random hidden state
        import random

        random.seed(42)
        h = [random.uniform(-1, 1) for _ in range(128)]

        output = link.forward(h)

        # Output should have same dimension
        assert len(output) == 128

    def test_recursive_link_forward_outer(self):
        """Outer link forward pass should include cross-agent projection."""
        from core.recursive_mas import RecursiveLink, RecursiveLinkConfig

        config = RecursiveLinkConfig(hidden_dim=128)
        link = RecursiveLink(config, "outer")

        import random

        random.seed(42)
        h = [random.uniform(-1, 1) for _ in range(128)]

        output = link.forward(h)

        assert len(output) == 128
        # Outer link has W3 projection, so output differs from inner

    def test_recursive_link_config_parameters(self):
        """RecursiveLinkConfig should calculate correct parameter count."""
        from core.recursive_mas import RecursiveLinkConfig

        config = RecursiveLinkConfig(hidden_dim=1024)
        # 3 * hidden_dim * hidden_dim = 3 * 1024 * 1024
        assert config.num_parameters == 3 * 1024 * 1024


class TestCollaborationPattern:
    """Tests for CollaborationPattern enum."""

    def test_all_patterns_defined(self):
        """All 4 collaboration patterns from the paper should be defined."""
        from core.recursive_mas import CollaborationPattern

        patterns = list(CollaborationPattern)
        assert len(patterns) == 4
        assert CollaborationPattern.SEQUENTIAL.value == "sequential"
        assert CollaborationPattern.MIXTURE.value == "mixture"
        assert CollaborationPattern.DISTILLATION.value == "distillation"
        assert CollaborationPattern.DELIBERATION.value == "deliberation"


class TestAgentRole:
    """Tests for AgentRole dataclass."""

    def test_agent_role_creation(self):
        """AgentRole should store role information correctly."""
        from core.recursive_mas import AgentRole

        role = AgentRole(
            key="planner",
            name="Planner",
            role_type="planner",
            model="minimax-coding-plan/MiniMax-M2.7",
            instructions="Plan the approach",
            hidden_dim=4096,
        )

        assert role.key == "planner"
        assert role.role_type == "planner"
        assert role.hidden_dim == 4096


class TestRecursiveMASAgent:
    """Tests for RecursiveMASAgent wrapper."""

    def test_agent_initialization(self):
        """RecursiveMASAgent should initialize with links and role."""
        from core.recursive_mas import (
            AgentRole,
            RecursiveLink,
            RecursiveLinkConfig,
            RecursiveMASAgent,
        )

        role = AgentRole(
            key="test",
            name="Test",
            role_type="planner",
            model="test",
            instructions="Test instructions",
        )
        config = RecursiveLinkConfig(hidden_dim=512)
        inner = RecursiveLink(config, "inner")
        outer = RecursiveLink(config, "outer")

        agent = RecursiveMASAgent(role, inner, outer)

        assert agent.role.key == "test"
        assert agent.inner_link.link_type == "inner"
        assert agent.outer_link.link_type == "outer"
        assert len(agent.latent_history) == 0

    def test_generate_latent_thoughts(self):
        """generate_latent_thoughts should produce LatentState."""
        from core.recursive_mas import (
            AgentRole,
            RecursiveLink,
            RecursiveLinkConfig,
            RecursiveMASAgent,
        )

        role = AgentRole(
            key="test",
            name="Test",
            role_type="planner",
            model="test",
            instructions="Test",
            hidden_dim=256,
        )
        config = RecursiveLinkConfig(hidden_dim=256)
        inner = RecursiveLink(config, "inner")
        agent = RecursiveMASAgent(role, inner)

        state = agent.generate_latent_thoughts("test input", num_steps=2)

        assert state.agent_key == "test"
        assert len(state.thoughts) == 2
        assert state.recursion_round == 0


class TestRecursiveMASOrchestrator:
    """Tests for RecursiveMASOrchestrator."""

    def test_orchestrator_initialization(self):
        """Orchestrator should initialize with correct defaults."""
        from core.recursive_mas import (
            CollaborationPattern,
            RecursiveMASOrchestrator,
        )

        async def dummy_llm(model, system, user):
            return "dummy output"

        orch = RecursiveMASOrchestrator(
            llm_call=dummy_llm,
            collaboration_pattern=CollaborationPattern.SEQUENTIAL,
            recursion_depth=3,
        )

        assert orch.pattern == CollaborationPattern.SEQUENTIAL
        assert orch.recursion_depth == 3
        assert len(orch.agents) == 0  # Not set up until run()

    def test_setup_sequential_style(self):
        """Sequential style setup should create 3 agents."""
        from core.recursive_mas import (
            CollaborationPattern,
            RecursiveMASOrchestrator,
        )

        async def dummy_llm(model, system, user):
            return "dummy"

        orch = RecursiveMASOrchestrator(
            llm_call=dummy_llm,
            collaboration_pattern=CollaborationPattern.SEQUENTIAL,
        )
        orch.setup_sequential_style()

        assert len(orch.agents) == 3
        assert "planner" in orch.agents
        assert "critic" in orch.agents
        assert "solver" in orch.agents
        assert orch.agent_order == ["planner", "critic", "solver"]

    def test_setup_mixture_style(self):
        """Mixture style setup should create 4 agents."""
        from core.recursive_mas import (
            CollaborationPattern,
            RecursiveMASOrchestrator,
        )

        async def dummy_llm(model, system, user):
            return "dummy"

        orch = RecursiveMASOrchestrator(
            llm_call=dummy_llm,
            collaboration_pattern=CollaborationPattern.MIXTURE,
        )
        orch.setup_mixture_style()

        assert len(orch.agents) == 4
        assert "math" in orch.agents
        assert "code" in orch.agents
        assert "science" in orch.agents
        assert "summarizer" in orch.agents

    def test_setup_distillation_style(self):
        """Distillation style setup should create 2 agents."""
        from core.recursive_mas import (
            CollaborationPattern,
            RecursiveMASOrchestrator,
        )

        async def dummy_llm(model, system, user):
            return "dummy"

        orch = RecursiveMASOrchestrator(
            llm_call=dummy_llm,
            collaboration_pattern=CollaborationPattern.DISTILLATION,
        )
        orch.setup_distillation_style()

        assert len(orch.agents) == 2
        assert "expert" in orch.agents
        assert "learner" in orch.agents

    def test_setup_deliberation_style(self):
        """Deliberation style setup should create 2 agents."""
        from core.recursive_mas import (
            CollaborationPattern,
            RecursiveMASOrchestrator,
        )

        async def dummy_llm(model, system, user):
            return "dummy"

        orch = RecursiveMASOrchestrator(
            llm_call=dummy_llm,
            collaboration_pattern=CollaborationPattern.DELIBERATION,
        )
        orch.setup_deliberation_style()

        assert len(orch.agents) == 2
        assert "reflector" in orch.agents
        assert "tool_caller" in orch.agents

    def test_get_role_instructions(self):
        """Role instructions should be role-specific."""
        from core.recursive_mas import RecursiveMASOrchestrator

        async def dummy_llm(model, system, user):
            return "dummy"

        orch = RecursiveMASOrchestrator(llm_call=dummy_llm)

        planner_instructions = orch._get_role_instructions("planner")
        assert "Planner" in planner_instructions

        critic_instructions = orch._get_role_instructions("critic")
        assert "Critic" in critic_instructions

        solver_instructions = orch._get_role_instructions("solver")
        assert "Solver" in solver_instructions


class TestRunRecursiveMAS:
    """Tests for run_recursive_mas convenience function."""

    @pytest.mark.asyncio
    async def test_run_sequential(self):
        """run_recursive_mas should execute sequential pattern."""
        from core.orchestrator import run_recursive_mas

        result = await run_recursive_mas(
            task="What is 2+2?",
            pattern="sequential",
            recursion_depth=2,
        )

        assert result.success is True
        assert result.pattern.value == "sequential"
        assert result.num_recursion_rounds == 2

    @pytest.mark.asyncio
    async def test_run_mixture(self):
        """run_recursive_mas should execute mixture pattern."""
        from core.orchestrator import run_recursive_mas

        result = await run_recursive_mas(
            task="Analyze this code for bugs",
            pattern="mixture",
            recursion_depth=2,
        )

        assert result.success is True
        assert result.pattern.value == "mixture"

    @pytest.mark.asyncio
    async def test_run_deliberation(self):
        """run_recursive_mas should execute deliberation pattern."""
        from core.orchestrator import run_recursive_mas

        result = await run_recursive_mas(
            task="Search for the latest news on AI",
            pattern="deliberation",
            recursion_depth=2,
        )

        assert result.success is True
        assert result.pattern.value == "deliberation"

    @pytest.mark.asyncio
    async def test_invalid_pattern_falls_back_to_sequential(self):
        """Invalid pattern should fall back to sequential."""
        from core.orchestrator import run_recursive_mas

        result = await run_recursive_mas(
            task="Test task",
            pattern="invalid_pattern",
            recursion_depth=1,
        )

        assert result.success is True
        assert result.pattern.value == "sequential"


class TestRecursiveMASResult:
    """Tests for RecursiveMASResult dataclass."""

    def test_result_creation(self):
        """RecursiveMASResult should store all fields."""
        from core.recursive_mas import CollaborationPattern, RecursiveMASResult

        result = RecursiveMASResult(
            output="Final answer",
            num_recursion_rounds=3,
            total_latency_ms=1500.0,
            pattern=CollaborationPattern.SEQUENTIAL,
            agent_results={"planner": "step 1", "solver": "final"},
            latent_efficiency=0.75,
            success=True,
        )

        assert result.output == "Final answer"
        assert result.num_recursion_rounds == 3
        assert result.latent_efficiency == 0.75
        assert result.success is True
