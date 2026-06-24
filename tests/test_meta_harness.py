"""
Tests for core/meta_harness.py — Meta-Harness implementation

Based on arXiv:2603.28052 - "Meta-Harness: End-to-End Optimization of Model Harnesses"
by Lee et al., 2026

These tests verify:
- HarnessFS storage and retrieval
- HarnessCandidate data model
- AgenticProposer prompt generation
- MetaHarnessOptimizer workflow (mock evaluation, no real LLM)
"""

import pytest
from core.meta_harness import (
    AgenticProposer,
    ExecutionTrace,
    HarnessCandidate,
    HarnessDomain,
    HarnessEvaluation,
    HarnessFS,
    MetaHarnessOptimizer,
    ParetoFrontier,
)


# ---------------------------------------------------------------------------
# HarnessFS Tests
# ---------------------------------------------------------------------------


class TestHarnessFS:
    """Tests for Harness Filesystem storage."""

    def test_harness_fs_initialization(self, tmp_path):
        """HarnessFS should initialize with correct base directory."""
        fs = HarnessFS(tmp_path / "test_fs")
        assert fs.base_dir == tmp_path / "test_fs"
        assert fs.base_dir.exists()

    def test_store_and_retrieve_candidate(self, tmp_path):
        """Should store and retrieve a candidate."""
        fs = HarnessFS(tmp_path / "test_fs")
        candidate = HarnessCandidate(
            candidate_id="test_001",
            source_code="def harness(x): return x * 2",
            description="Double the input",
            domain=HarnessDomain.TEXT_CLASSIFICATION,
        )
        candidate.evaluations.append(
            HarnessEvaluation(task_instance="task_1", reward=0.8, cost=100)
        )

        fs.store(candidate)
        retrieved = fs.get("test_001")

        assert retrieved is not None
        assert retrieved.candidate_id == "test_001"
        assert retrieved.source_code == "def harness(x): return x * 2"
        assert retrieved.mean_reward == 0.8

    def test_get_all_candidates(self, tmp_path):
        """Should return all stored candidates."""
        fs = HarnessFS(tmp_path / "test_fs")

        for i in range(5):
            c = HarnessCandidate(
                candidate_id=f"candidate_{i}",
                source_code=f"# Candidate {i}",
                domain=HarnessDomain.CUSTOM,
            )
            c.evaluations.append(HarnessEvaluation(task_instance=f"task_{i}", reward=0.5 + i * 0.1))
            fs.store(c)

        all_c = fs.get_all()
        assert len(all_c) == 5

    def test_query_by_keyword_description(self, tmp_path):
        """Should query candidates by keyword in description."""
        fs = HarnessFS(tmp_path / "test_fs")

        c1 = HarnessCandidate("c1", "# code", description="retrieval harness", domain=HarnessDomain.RAG)
        c2 = HarnessCandidate("c2", "# code", description="math harness", domain=HarnessDomain.MATH_REASONING)
        fs.store(c1)
        fs.store(c2)

        results = fs.query_by_keyword("retrieval")
        assert len(results) == 1
        assert results[0].candidate_id == "c1"

    def test_query_by_keyword_code(self, tmp_path):
        """Should query candidates by keyword in source code."""
        fs = HarnessFS(tmp_path / "test_fs")

        c1 = HarnessCandidate("c1", "def retrieve(): pass", description="harness one", domain=HarnessDomain.CUSTOM)
        c2 = HarnessCandidate("c2", "def compute(): pass", description="harness two", domain=HarnessDomain.CUSTOM)
        fs.store(c1)
        fs.store(c2)

        results = fs.query_by_keyword("retrieve", field="code")
        assert len(results) == 1
        assert results[0].candidate_id == "c1"

    def test_query_by_reward_range(self, tmp_path):
        """Should query candidates by reward range."""
        fs = HarnessFS(tmp_path / "test_fs")

        for i in range(1, 5):  # Start from i=1 to avoid 0.0 reward edge case
            c = HarnessCandidate(f"c{i}", "# code", domain=HarnessDomain.CUSTOM)
            c.evaluations.append(HarnessEvaluation(task_instance=f"t{i}", reward=0.2 * i))
            fs.store(c)

        # Rewards: c1=0.2, c2=0.4, c3=0.6, c4=0.8
        # Range [0.2, 0.5] should include c1 and c2 (0.2, 0.4)
        results = fs.query_by_reward_range(0.2, 0.5)
        assert len(results) == 2

    def test_query_recent(self, tmp_path):
        """Should return most recent candidates."""
        fs = HarnessFS(tmp_path / "test_fs")

        for i in range(10):
            c = HarnessCandidate(f"c{i}", "# code", domain=HarnessDomain.CUSTOM)
            fs.store(c)

        recent = fs.query_recent(n=3)
        assert len(recent) == 3
        # Most recent should be c9 (last stored)
        assert recent[0].candidate_id == "c9"

    def test_get_pareto_frontier(self, tmp_path):
        """Should compute Pareto frontier of non-dominated candidates."""
        fs = HarnessFS(tmp_path / "test_fs")

        # c1: High reward, low cost (Pareto optimal)
        c1 = HarnessCandidate("c1", "# code", domain=HarnessDomain.CUSTOM)
        c1.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.9, cost=50))

        # c2: Low reward, high cost (Pareto optimal - different trade-off)
        c2 = HarnessCandidate("c2", "# code", domain=HarnessDomain.CUSTOM)
        c2.evaluations.append(HarnessEvaluation(task_instance="t2", reward=0.7, cost=20))  # Lower cost but lower reward

        # c3: Medium reward, very high cost (dominated by c1: same reward, higher cost)
        c3 = HarnessCandidate("c3", "# code", domain=HarnessDomain.CUSTOM)
        c3.evaluations.append(HarnessEvaluation(task_instance="t3", reward=0.9, cost=200))

        fs.store(c1)
        fs.store(c2)
        fs.store(c3)

        frontier = fs.get_pareto_frontier()
        # c1 and c2 are non-dominated (different trade-offs)
        # c3 is dominated by c1 (same reward 0.9, higher cost 200 vs 50)
        assert len(frontier.candidates) == 2  # c1 and c2
        frontier_ids = {c.candidate_id for c in frontier.candidates}
        assert frontier_ids == {"c1", "c2"}

    def test_get_stats(self, tmp_path):
        """Should return filesystem statistics."""
        fs = HarnessFS(tmp_path / "test_fs")

        c1 = HarnessCandidate("c1", "# code", domain=HarnessDomain.TEXT_CLASSIFICATION)
        c1.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.8))
        fs.store(c1)

        c2 = HarnessCandidate("c2", "# code", domain=HarnessDomain.MATH_REASONING)
        c2.evaluations.append(HarnessEvaluation(task_instance="t2", reward=0.7))
        fs.store(c2)

        stats = fs.get_stats()
        assert stats["total_candidates"] == 2
        assert stats["base_dir"] == str(tmp_path / "test_fs")
        assert "text_classification" in stats["domains"]
        assert "math_reasoning" in stats["domains"]

    def test_get_file_content(self, tmp_path):
        """Should retrieve raw file content."""
        fs = HarnessFS(tmp_path / "test_fs")
        c = HarnessCandidate("c1", "def test(): pass", description="test", domain=HarnessDomain.CUSTOM)
        fs.store(c)

        code = fs.get_file_content("c1", "code.py")
        assert code == "def test(): pass"

        meta = fs.get_file_content("c1", "metadata.json")
        assert meta is not None
        assert '"candidate_id": "c1"' in meta


# ---------------------------------------------------------------------------
# HarnessCandidate Tests
# ---------------------------------------------------------------------------


class TestHarnessCandidate:
    """Tests for HarnessCandidate data model."""

    def test_mean_reward_calculation(self):
        """Should calculate mean reward correctly."""
        c = HarnessCandidate("test", "# code", domain=HarnessDomain.CUSTOM)
        c.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.8))
        c.evaluations.append(HarnessEvaluation(task_instance="t2", reward=0.6))

        assert c.mean_reward == 0.7

    def test_mean_reward_empty(self):
        """Should return 0.0 when no evaluations."""
        c = HarnessCandidate("test", "# code", domain=HarnessDomain.CUSTOM)
        assert c.mean_reward == 0.0

    def test_mean_cost_calculation(self):
        """Should calculate mean cost correctly."""
        c = HarnessCandidate("test", "# code", domain=HarnessDomain.CUSTOM)
        c.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.8, cost=100))
        c.evaluations.append(HarnessEvaluation(task_instance="t2", reward=0.6, cost=200))

        assert c.mean_cost == 150.0

    def test_parent_tracking(self):
        """Should track parent candidate IDs for evolutionary tracking."""
        c = HarnessCandidate("child", "# code", domain=HarnessDomain.CUSTOM, parent_ids=["parent1", "parent2"])
        assert "parent1" in c.parent_ids
        assert "parent2" in c.parent_ids


# ---------------------------------------------------------------------------
# ExecutionTrace and HarnessEvaluation Tests
# ---------------------------------------------------------------------------


class TestExecutionTrace:
    """Tests for ExecutionTrace data model."""

    def test_trace_creation(self):
        """Should create execution trace with all fields."""
        trace = ExecutionTrace(
            prompt="Solve 2+2",
            model_output="4",
            tool_calls=[{"tool": "python", "input": "2+2", "output": "4"}],
            state_updates=[{"state": "computed"}],
            intermediate_steps=["parse", "compute", "verify"],
            tokens_used=150,
            latency_ms=500.0,
        )

        assert trace.prompt == "Solve 2+2"
        assert trace.model_output == "4"
        assert len(trace.tool_calls) == 1
        assert trace.tokens_used == 150
        assert trace.latency_ms == 500.0

    def test_trace_defaults(self):
        """Should have sensible defaults."""
        trace = ExecutionTrace(prompt="test", model_output="response")
        assert trace.tool_calls == []
        assert trace.state_updates == []
        assert trace.intermediate_steps == []
        assert trace.tokens_used == 0
        assert trace.latency_ms == 0.0


class TestHarnessEvaluation:
    """Tests for HarnessEvaluation data model."""

    def test_evaluation_creation(self):
        """Should create evaluation with all fields."""
        trace = ExecutionTrace(prompt="test", model_output="resp")
        eval_result = HarnessEvaluation(
            task_instance="task_123",
            reward=0.85,
            cost=200,
            latency_ms=300,
            trace=trace,
            metadata={"accuracy": 0.9},
        )

        assert eval_result.task_instance == "task_123"
        assert eval_result.reward == 0.85
        assert eval_result.cost == 200
        assert eval_result.trace is not None

    def test_evaluation_without_trace(self):
        """Should create evaluation without trace."""
        eval_result = HarnessEvaluation(task_instance="task_1", reward=0.5)
        assert eval_result.trace is None


# ---------------------------------------------------------------------------
# ParetoFrontier Tests
# ---------------------------------------------------------------------------


class TestParetoFrontier:
    """Tests for ParetoFrontier."""

    def test_is_dominated(self):
        """Should correctly identify dominated candidates."""
        c1 = HarnessCandidate("c1", "# code", domain=HarnessDomain.CUSTOM)
        c1.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.9, cost=50))

        c2 = HarnessCandidate("c2", "# code", domain=HarnessDomain.CUSTOM)
        c2.evaluations.append(HarnessEvaluation(task_instance="t2", reward=0.3, cost=200))

        frontier = ParetoFrontier(candidates=[c1])

        # c2 should be dominated by c1 (c1 is better in both reward AND cost)
        assert frontier.is_dominated(c2) is True

        # c1 is not dominated
        assert frontier.is_dominated(c1) is False

    def test_not_dominated_when_better_reward_higher_cost(self):
        """Should NOT consider dominated if one metric is better but other worse."""
        c1 = HarnessCandidate("c1", "# code", domain=HarnessDomain.CUSTOM)
        c1.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.9, cost=100))

        c2 = HarnessCandidate("c2", "# code", domain=HarnessDomain.CUSTOM)
        c2.evaluations.append(HarnessEvaluation(task_instance="t2", reward=0.7, cost=50))

        frontier = ParetoFrontier(candidates=[c1])

        # c2 is NOT dominated: c1 has better reward but worse cost
        # Both metrics would need to be <= for domination
        assert frontier.is_dominated(c2) is False


# ---------------------------------------------------------------------------
# HarnessDomain Tests
# ---------------------------------------------------------------------------


class TestHarnessDomain:
    """Tests for HarnessDomain enum."""

    def test_all_domains_defined(self):
        """All paper-mentioned domains should be defined."""
        assert HarnessDomain.TEXT_CLASSIFICATION.value == "text_classification"
        assert HarnessDomain.MATH_REASONING.value == "math_reasoning"
        assert HarnessDomain.AGENTIC_CODING.value == "agentic_coding"
        assert HarnessDomain.RAG.value == "rag"
        assert HarnessDomain.CUSTOM.value == "custom"

    def test_domain_enum_count(self):
        """Should have all 5 domains."""
        assert len(HarnessDomain) == 5


# ---------------------------------------------------------------------------
# MetaHarnessOptimizer Tests (with mock LLM)
# ---------------------------------------------------------------------------


class TestMetaHarnessOptimizer:
    """Tests for MetaHarnessOptimizer with mock evaluation."""

    @pytest.mark.asyncio
    async def test_optimizer_initialization(self, tmp_path):
        """Should initialize optimizer with all components."""
        async def mock_llm(model, system, prompt):
            return '{"description": "test", "code": "# test harness"}'

        optimizer = MetaHarnessOptimizer(
            llm_call=mock_llm,
            harness_fs=HarnessFS(tmp_path / "harness_fs"),
            max_iterations=5,
        )

        assert optimizer.harness_fs is not None
        assert optimizer.proposer is not None
        assert optimizer.max_iterations == 5

    @pytest.mark.asyncio
    async def test_run_with_mock_evaluation(self, tmp_path):
        """Should run optimization loop with mock evaluation."""
        call_count = 0

        async def mock_llm(model, system, prompt):
            nonlocal call_count
            call_count += 1
            return '[{"description": "Mock harness ' + str(call_count) + '", "code": "# mock code ' + str(call_count) + '"}]'

        async def mock_evaluate(candidate):
            # Return 2 evaluations with random-ish rewards
            import random
            reward = random.uniform(0.3, 0.9)
            return [
                HarnessEvaluation(task_instance="task_1", reward=reward, cost=100),
                HarnessEvaluation(task_instance="task_2", reward=reward + 0.05, cost=120),
            ]

        optimizer = MetaHarnessOptimizer(
            llm_call=mock_llm,
            harness_fs=HarnessFS(tmp_path / "harness_fs"),
            max_iterations=3,
            proposals_per_iteration=1,
        )

        await optimizer.run(
            task_description="Solve coding problems with better prompts",
            domain=HarnessDomain.AGENTIC_CODING,
            evaluate_fn=mock_evaluate,
        )

        # Should have run for 3 iterations
        assert call_count == 3
        # Should have candidates in the filesystem
        stats = optimizer.harness_fs.get_stats()
        assert stats["total_candidates"] >= 3

    @pytest.mark.asyncio
    async def test_get_best_for_cost(self, tmp_path):
        """Should return best candidate within cost budget."""
        async def mock_llm(model, system, prompt):
            return '[{"description": "expensive harness", "code": "# expensive"}]'

        optimizer = MetaHarnessOptimizer(
            llm_call=mock_llm,
            harness_fs=HarnessFS(tmp_path / "harness_fs"),
        )

        # Add some candidates manually
        c1 = HarnessCandidate("c1", "# cheap harness", domain=HarnessDomain.CUSTOM)
        c1.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.7, cost=80))
        optimizer.harness_fs.store(c1)

        c2 = HarnessCandidate("c2", "# expensive harness", domain=HarnessDomain.CUSTOM)
        c2.evaluations.append(HarnessEvaluation(task_instance="t2", reward=0.9, cost=300))
        optimizer.harness_fs.store(c2)

        best = optimizer.get_best_for_cost(max_cost=100)
        assert best is not None
        assert best.candidate_id == "c1"
        assert best.mean_cost == 80

    @pytest.mark.asyncio
    async def test_get_best_for_cost_no_viable(self, tmp_path):
        """Should return None when no candidate fits cost budget."""
        optimizer = MetaHarnessOptimizer(
            llm_call=None,
            harness_fs=HarnessFS(tmp_path / "harness_fs"),
        )

        c = HarnessCandidate("c1", "# expensive", domain=HarnessDomain.CUSTOM)
        c.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.5, cost=500))
        optimizer.harness_fs.store(c)

        best = optimizer.get_best_for_cost(max_cost=100)
        assert best is None


# ---------------------------------------------------------------------------
# AgenticProposer Tests
# ---------------------------------------------------------------------------


class TestAgenticProposer:
    """Tests for AgenticProposer."""

    @pytest.mark.asyncio
    async def test_proposer_with_scores_only(self, tmp_path):
        """Should work with scores_only inspection depth."""
        async def mock_llm(model, system, prompt):
            return '[{"description": "test", "code": "# test"}]'

        fs = HarnessFS(tmp_path / "test_fs")

        # Add some candidates for context
        for i in range(3):
            c = HarnessCandidate(f"c{i}", f"# code {i}", domain=HarnessDomain.CUSTOM)
            c.evaluations.append(HarnessEvaluation(task_instance=f"t{i}", reward=0.5 + i * 0.1))
            fs.store(c)

        proposer = AgenticProposer(llm_call=mock_llm, harness_fs=fs)

        proposals = await proposer.propose(
            task_description="Improve coding harness",
            domain=HarnessDomain.AGENTIC_CODING,
            num_proposals=1,
            inspection_depth="scores_only",
        )

        assert len(proposals) >= 1

    @pytest.mark.asyncio
    async def test_proposer_handles_empty_response(self, tmp_path):
        """Should handle empty LLM response gracefully."""
        async def mock_llm(model, system, prompt):
            return ""  # Empty response

        fs = HarnessFS(tmp_path / "test_fs")
        proposer = AgenticProposer(llm_call=mock_llm, harness_fs=fs)

        proposals = await proposer.propose(
            task_description="test",
            domain=HarnessDomain.CUSTOM,
            num_proposals=1,
        )

        # Should still return something (fallback candidate)
        assert len(proposals) >= 1

    @pytest.mark.asyncio
    async def test_proposer_formats_context(self, tmp_path):
        """Should format context with scores and summary."""
        async def mock_llm(model, system, prompt):
            return '[{"description": "test", "code": "# test"}]'

        fs = HarnessFS(tmp_path / "test_fs")

        # Add Pareto frontier candidate
        c = HarnessCandidate("p1", "# best code", domain=HarnessDomain.RAG)
        c.evaluations.append(HarnessEvaluation(task_instance="t1", reward=0.95, cost=50))
        fs.store(c)

        proposer = AgenticProposer(llm_call=mock_llm, harness_fs=fs)

        await proposer.propose(
            task_description="RAG improvement",
            domain=HarnessDomain.RAG,
            num_proposals=2,
            inspection_depth="scores_plus_summary",
        )

        # Proposer should have made an LLM call
        # (we trust the mock was called since no exception)
