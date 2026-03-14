"""Tests for swarms_bot enterprise layer modules.

Tests:
- ChiefOfStaff task classification and routing
- SessionManager save/resume lifecycle
- CostMetricsCollector recording and alerts
- BudgetManager enforcement
- Autonomous loop control (pause/resume/status)
"""

import asyncio
import sys
import time
import unittest

# Add project root to path
sys.path.insert(0, ".")


class TestChiefOfStaff(unittest.TestCase):
    """Test ChiefOfStaff task classification and integration."""

    def setUp(self):
        from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff, Task, TaskType
        self.cos = ChiefOfStaff()
        self.Task = Task
        self.TaskType = TaskType

    def test_classify_code_generation(self):
        task = self.Task.create(
            user_id=1, chat_id=1,
            description="Write a Python function to calculate fibonacci numbers",
        )
        result = self.cos.classify_task(task)
        self.assertEqual(result, self.TaskType.CODE_GENERATION)

    def test_classify_debug(self):
        task = self.Task.create(
            user_id=1, chat_id=1,
            description="Fix this traceback error in my PyTorch training loop",
        )
        result = self.cos.classify_task(task)
        self.assertEqual(result, self.TaskType.DEBUG)

    def test_classify_math(self):
        task = self.Task.create(
            user_id=1, chat_id=1,
            description="Calculate the gradient of the tensor loss function",
        )
        result = self.cos.classify_task(task)
        self.assertEqual(result, self.TaskType.MATH)

    def test_classify_research(self):
        task = self.Task.create(
            user_id=1, chat_id=1,
            description="Research the latest papers on transformer architecture",
        )
        result = self.cos.classify_task(task)
        self.assertEqual(result, self.TaskType.RESEARCH)

    def test_classify_planning(self):
        task = self.Task.create(
            user_id=1, chat_id=1,
            description="Design the architecture for a distributed system",
        )
        result = self.cos.classify_task(task)
        self.assertEqual(result, self.TaskType.PLANNING)

    def test_classify_general(self):
        task = self.Task.create(
            user_id=1, chat_id=1,
            description="Hello, how are you?",
        )
        result = self.cos.classify_task(task)
        self.assertEqual(result, self.TaskType.GENERAL_QA)

    def test_classify_respects_explicit_type(self):
        task = self.Task.create(
            user_id=1, chat_id=1,
            description="some text",
            task_type=self.TaskType.TESTING,
        )
        result = self.cos.classify_task(task)
        self.assertEqual(result, self.TaskType.TESTING)

    def test_select_agent_key(self):
        self.assertEqual(
            self.cos.select_agent_key(self.TaskType.CODE_GENERATION, {}),
            "coding",
        )
        self.assertEqual(
            self.cos.select_agent_key(self.TaskType.DEBUG, {}),
            "debug",
        )
        self.assertEqual(
            self.cos.select_agent_key(self.TaskType.MATH, {}),
            "math",
        )

    def test_select_agent_override(self):
        result = self.cos.select_agent_key(
            self.TaskType.CODE_GENERATION,
            {"agent_override": "analyst"},
        )
        self.assertEqual(result, "analyst")

    def test_stats(self):
        stats = self.cos.get_stats()
        self.assertEqual(stats["total_tasks"], 0)
        self.assertEqual(stats["success_rate"], 0.0)

    def test_integration_setters(self):
        """Test that integration setters work without errors."""
        from swarms_bot.routing.budget_manager import BudgetManager
        from swarms_bot.observability.cost_metrics import CostMetricsCollector

        bm = BudgetManager()
        cm = CostMetricsCollector()

        self.cos.set_budget_manager(bm)
        self.cos.set_cost_metrics(cm)
        self.assertIs(self.cos._budget, bm)
        self.assertIs(self.cos._cost_metrics, cm)


class TestCostMetricsCollector(unittest.TestCase):
    """Test CostMetricsCollector recording and alerting."""

    def setUp(self):
        from swarms_bot.observability.cost_metrics import CostMetricsCollector
        self.collector = CostMetricsCollector(alert_hourly_rate=1.0)

    def test_record_basic(self):
        alert = self.collector.record(
            agent_name="coding",
            model="groq/llama-3.3-70b-versatile",
            cost_usd=0.001,
            tokens_used=100,
            latency_ms=500,
        )
        self.assertIsNone(alert)
        summary = self.collector.get_summary()
        self.assertEqual(summary["total_requests"], 1)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.001, places=4)

    def test_multiple_records(self):
        for i in range(10):
            self.collector.record(
                agent_name="coding" if i % 2 == 0 else "debug",
                model="groq/llama-3.3-70b-versatile",
                cost_usd=0.01,
                tokens_used=200,
                latency_ms=1000 + i * 100,
            )
        summary = self.collector.get_summary()
        self.assertEqual(summary["total_requests"], 10)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.1, places=3)
        self.assertIn("coding", summary["by_agent"])
        self.assertIn("debug", summary["by_agent"])

    def test_cost_alert(self):
        # Trigger alert by exceeding hourly rate ($1.0)
        alert = self.collector.record(
            agent_name="coding",
            model="gpt-4",
            cost_usd=1.5,
            tokens_used=5000,
            latency_ms=3000,
        )
        self.assertIsNotNone(alert)
        self.assertIn("Cost alert", alert)

    def test_hourly_rate(self):
        self.collector.record(
            agent_name="coding",
            model="gpt-4",
            cost_usd=0.5,
            tokens_used=1000,
            latency_ms=1000,
        )
        rate = self.collector.get_hourly_rate()
        self.assertAlmostEqual(rate, 0.5, places=2)

    def test_format_dashboard(self):
        self.collector.record(
            agent_name="coding",
            model="groq/llama-3.3-70b-versatile",
            cost_usd=0.001,
            tokens_used=100,
            latency_ms=500,
        )
        html = self.collector.format_dashboard_html()
        self.assertIn("Cost Metrics", html)
        self.assertIn("coding", html)


class TestBudgetManager(unittest.TestCase):
    """Test BudgetManager enforcement."""

    def setUp(self):
        from swarms_bot.routing.budget_manager import BudgetManager
        self.bm = BudgetManager(daily_limit=1.0, monthly_limit=10.0)

    def test_initial_budget(self):
        status = self.bm.check_budget()
        self.assertTrue(status["allowed"])
        self.assertEqual(status["daily_spent"], 0)

    def test_record_cost(self):
        self.bm.record_cost("coding", "gpt-4", 0.1, 100, 200)
        status = self.bm.check_budget()
        self.assertTrue(status["allowed"])
        self.assertGreater(status["daily_spent"], 0)

    def test_budget_exceeded(self):
        self.bm.record_cost("coding", "gpt-4", 1.5, 10000, 5000)
        status = self.bm.check_budget()
        self.assertFalse(status["allowed"])

    def test_cost_breakdown(self):
        self.bm.record_cost("coding", "gpt-4", 0.1, 100, 200, "code_gen")
        self.bm.record_cost("debug", "gpt-4", 0.2, 200, 300, "debug")
        breakdown = self.bm.get_cost_breakdown("day")
        self.assertEqual(breakdown["total_requests"], 2)
        self.assertIn("coding", breakdown["by_agent"])
        self.assertIn("debug", breakdown["by_agent"])


class TestCostAwareRouter(unittest.TestCase):
    """Test CostAwareRouter complexity classification."""

    def setUp(self):
        from swarms_bot.routing.cost_router import (
            CostAwareRouter, classify_complexity, TaskComplexity,
        )
        self.router = CostAwareRouter()
        self.classify = classify_complexity
        self.TC = TaskComplexity

    def test_trivial_classification(self):
        result = self.classify("What is 2+2?")
        self.assertEqual(result, self.TC.TRIVIAL)

    def test_simple_classification(self):
        result = self.classify("How do I sort a list in Python using the sorted function?")
        self.assertIn(result, [self.TC.TRIVIAL, self.TC.SIMPLE])

    def test_complex_classification(self):
        result = self.classify(
            "First, refactor the authentication module. "
            "Then, deploy the changes to staging. "
            "After that, run the integration tests with PyTorch models. "
            "Finally, commit everything to git."
        )
        self.assertIn(result, [self.TC.COMPLEX, self.TC.EXPERT])

    def test_expert_classification(self):
        task = (
            "Design the architecture for a distributed system with "
            "PyTorch training, Kubernetes deployment, async processing, "
            "and distributed optimization across multiple GPU nodes. " * 3
        )
        result = self.classify(task)
        self.assertEqual(result, self.TC.EXPERT)

    def test_router_stats(self):
        stats = self.router.get_routing_stats()
        self.assertEqual(stats["total_routes"], 0)


class TestSessionManager(unittest.TestCase):
    """Test SessionManager save/resume lifecycle."""

    def setUp(self):
        from swarms_bot.sessions.session_manager import SessionManager
        import tempfile
        from pathlib import Path
        self.tmp = tempfile.mkdtemp()
        self.sm = SessionManager(db_path=Path(self.tmp) / "test_sessions.db")

    def test_get_or_create_session(self):
        session = self.sm.get_or_create_session(user_id=1, chat_id=100)
        self.assertEqual(session.user_id, 1)
        self.assertEqual(session.chat_id, 100)
        self.assertEqual(session.status, "active")

    def test_same_session_returned(self):
        s1 = self.sm.get_or_create_session(user_id=1, chat_id=100)
        s2 = self.sm.get_or_create_session(user_id=1, chat_id=100)
        self.assertEqual(s1.session_id, s2.session_id)

    def test_track_task(self):
        session = self.sm.get_or_create_session(user_id=1, chat_id=100)
        self.sm.track_task(
            user_id=1,
            agent_name="coding",
            model="groq/llama-3.3-70b-versatile",
            cost_usd=0.001,
            tokens=100,
        )
        self.assertEqual(session.task_count, 1)
        self.assertAlmostEqual(session.total_cost_usd, 0.001, places=4)

    def _run(self, coro):
        """Helper to run async coroutines in sync tests."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    @unittest.skipUnless(
        __import__("importlib").util.find_spec("aiosqlite") is not None,
        "aiosqlite not installed",
    )
    def test_save_and_list(self):
        session = self.sm.get_or_create_session(user_id=1, chat_id=100)
        self.sm.track_task(1, "coding", "groq/llama", 0.01, 500)

        # Save
        saved = self._run(self.sm.save_session(1, "test_session"))
        self.assertIsNotNone(saved)
        self.assertEqual(saved.name, "test_session")

        # List
        sessions = self._run(self.sm.list_sessions(1))
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["name"], "test_session")

    @unittest.skipUnless(
        __import__("importlib").util.find_spec("aiosqlite") is not None,
        "aiosqlite not installed",
    )
    def test_save_and_resume(self):
        session = self.sm.get_or_create_session(
            user_id=1, chat_id=100, thread_id="thread_abc",
        )
        self.sm.track_task(1, "coding", "groq/llama", 0.05, 1000)

        self._run(self.sm.save_session(1, "my_session"))

        # Clear active and resume
        self.sm._active_sessions.clear()
        resumed = self._run(self.sm.resume_session(1, "my_session"))
        self.assertIsNotNone(resumed)
        self.assertEqual(resumed.name, "my_session")
        self.assertEqual(resumed.task_count, 1)
        self.assertAlmostEqual(resumed.total_cost_usd, 0.05, places=3)

    def test_format_sessions_html(self):
        html = self.sm.format_sessions_html([])
        self.assertIn("No saved sessions", html)

        sessions = [{
            "session_id": "abc123",
            "name": "test",
            "created_at": time.time(),
            "last_active": time.time(),
            "status": "saved",
            "total_cost_usd": 0.05,
            "total_tokens": 500,
            "task_count": 3,
            "tags": [],
        }]
        html = self.sm.format_sessions_html(sessions)
        self.assertIn("test", html)
        self.assertIn("3 tasks", html)


@unittest.skipUnless(
    __import__("importlib").util.find_spec("litellm") is not None,
    "litellm not installed",
)
class TestAutonomousLoopControl(unittest.TestCase):
    """Test autonomous loop control functions."""

    def test_no_active_loop(self):
        from tools.autonomous_loop import get_active_loop, get_loop_state
        self.assertIsNone(get_active_loop(999))
        self.assertIsNone(get_loop_state(999))

    def test_stop_no_loop(self):
        from tools.autonomous_loop import stop_loop
        self.assertFalse(stop_loop(999))

    def test_pause_no_loop(self):
        from tools.autonomous_loop import pause_loop
        self.assertFalse(pause_loop(999))

    def test_resume_no_loop(self):
        from tools.autonomous_loop import resume_loop
        self.assertFalse(resume_loop(999))

    def test_format_loop_status(self):
        from tools.autonomous_loop import LoopState, format_loop_status_html
        state = LoopState(
            goal="Test goal",
            iteration=5,
            start_time=time.time() - 300,
            estimated_cost_usd=0.1,
            model_used="groq/llama-3.3-70b",
            status="running",
            history=["Step 1", "Step 2"],
        )
        html = format_loop_status_html(state)
        self.assertIn("Loop Status", html)
        self.assertIn("Test goal", html)
        self.assertIn("running", html)
        self.assertIn("Step 1", html)

    def test_pause_resume_flow(self):
        from tools.autonomous_loop import (
            LoopState, _active_loops, pause_loop, resume_loop,
        )
        state = LoopState(goal="test", status="running")
        _active_loops[42] = state

        self.assertTrue(pause_loop(42))
        self.assertEqual(state.status, "paused")

        self.assertTrue(resume_loop(42))
        self.assertEqual(state.status, "running")

        # Cleanup
        del _active_loops[42]


class TestSwarmLogger(unittest.TestCase):
    """Test structured logging."""

    def test_logger_creation(self):
        from swarms_bot.observability.logging_config import SwarmLogger
        log = SwarmLogger("test_component")
        self.assertIsNotNone(log)

    def test_logger_bind(self):
        from swarms_bot.observability.logging_config import SwarmLogger
        log = SwarmLogger("test_component")
        bound = log.bind(session_id="abc123")
        self.assertNotEqual(id(log), id(bound))

    def test_log_methods(self):
        from swarms_bot.observability.logging_config import SwarmLogger
        log = SwarmLogger("test_component")
        # Should not raise
        log.info("test_event", agent_name="coding", latency_ms=100)
        log.warning("test_warning", error_type="timeout")
        log.error("test_error", exc_info=False)
        log.debug("test_debug")


if __name__ == "__main__":
    unittest.main()
