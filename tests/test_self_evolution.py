"""Tests for core/self_evolution.py"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.self_evolution import FailureRecord, SelfEvolutionEngine


def _engine(tmp_path: Path) -> SelfEvolutionEngine:
    """Return a fresh engine with temp directories (no hermes dependencies)."""
    engine = SelfEvolutionEngine.__new__(SelfEvolutionEngine)
    engine.project_root = tmp_path
    engine.failures_file = tmp_path / "FAILURES.md"
    engine.decisions_file = tmp_path / "DECISIONS.md"
    engine.eval_set_file = tmp_path / "EVAL_SET.md"
    engine._hermes_skills_dir = tmp_path / "hermes_skills"
    return engine


class TestRecordFailure:
    def test_writes_to_failures_file(self, tmp_path):
        engine = _engine(tmp_path)
        asyncio.run(engine.record_failure(
            task="write a sort function",
            approach="used quicksort",
            failure_mode="wrong output",
            root_cause="off-by-one in partition",
            fix_applied="switched to builtin sorted",
            prevention_rule="always verify sort output against reference",
            title="sort function bug",
            tags=["algorithm", "testing"],
        ))
        assert engine.failures_file.exists()
        content = engine.failures_file.read_text()
        assert "sort function bug" in content
        assert "off-by-one in partition" in content
        assert "algorithm" in content

    def test_infer_tags_returns_list(self, tmp_path):
        engine = _engine(tmp_path)
        tags = engine._infer_tags(
            task="fix the api endpoint returns 500 on POST",
            approach="used sync sqlite3",
            root_cause="blocking call in async context",
        )
        assert isinstance(tags, list)
        assert len(tags) > 0

    def test_infer_tags_empty_input(self, tmp_path):
        engine = _engine(tmp_path)
        tags = engine._infer_tags("", "", "")
        assert tags == ["general"]

    def test_infer_agent_from_task_computer(self, tmp_path):
        engine = _engine(tmp_path)
        assert engine._infer_agent_from_task("run a shell command") == "computer"
        assert engine._infer_agent_from_task("do screen capture") == "computer"

    def test_infer_agent_from_task_coding(self, tmp_path):
        engine = _engine(tmp_path)
        assert engine._infer_agent_from_task("write a function") == "coding"
        assert engine._infer_agent_from_task("implement the API") == "coding"

    def test_infer_agent_from_task_researcher(self, tmp_path):
        engine = _engine(tmp_path)
        assert engine._infer_agent_from_task("research the paper") == "researcher"

    def test_infer_agent_from_task_debug(self, tmp_path):
        engine = _engine(tmp_path)
        assert engine._infer_agent_from_task("debug the error") == "debug"

    def test_infer_agent_from_task_general(self, tmp_path):
        engine = _engine(tmp_path)
        assert engine._infer_agent_from_task("process a request") == "general"


class TestRecordDecision:
    def test_writes_to_decisions_file(self, tmp_path):
        engine = _engine(tmp_path)
        asyncio.run(engine.record_decision(
            title="use litellm proxy",
            context="multiple llm providers needed",
            decision="use litellm proxy instead of direct api",
            rationale="uniform retry and logging across all llm calls",
        ))
        assert engine.decisions_file.exists()
        content = engine.decisions_file.read_text()
        assert "use litellm proxy" in content


class TestBuildEvalSet:
    def test_returns_zero_when_fewer_than_5_failures(self, tmp_path):
        engine = _engine(tmp_path)
        result = asyncio.run(engine.build_eval_set_from_failures())
        assert result == 0

    def test_writes_eval_set_when_5_plus_failures(self, tmp_path):
        engine = _engine(tmp_path)
        # Write 5 failure entries in the exact format record_failure produces:
        # starts with newline, then "### Title\n\nTask:...\nApproach:...\n..."
        failure_entries = []
        for i in range(5):
            failure_entries.append(f"""### Failure {i}

Task: task {i}
Approach: approach {i}
Failure mode: mode {i}
Root cause: root cause {i}
Fix applied: fix {i}
Prevention rule: rule {i}
Tags: [api]""")
        # Leading \n required so regex r"\n###\s+" finds a match at position 0
        failure_content = "\n" + "\n\n".join(failure_entries) + "\n"
        engine.failures_file.write_text(failure_content)
        result = asyncio.run(engine.build_eval_set_from_failures())
        assert result >= 1
        assert engine.eval_set_file.exists()
        eval_content = engine.eval_set_file.read_text()
        assert "TEST-" in eval_content or "test case" in eval_content.lower()


class TestAdversarialChallenges:
    def test_returns_list_of_strings(self, tmp_path):
        engine = _engine(tmp_path)
        challenges = engine.get_adversarial_challenges(plan="Write a sorting algorithm")
        assert isinstance(challenges, list)
        assert all(isinstance(c, str) for c in challenges)

    def test_non_empty_for_valid_plan(self, tmp_path):
        engine = _engine(tmp_path)
        # Pre-populate failures with matching tag so challenges are generated
        engine.failures_file.write_text(
            "\n### Auth bug\n\n"
            "Task: implement login\n"
            "Approach: used weak hashing\n"
            "Failure mode: passwords cracked\n"
            "Root cause: md5 is broken\n"
            "Fix applied: bcrypt\n"
            "Prevention rule: use strong hashing\n"
            "Tags: [security]\n"
        )
        challenges = engine.get_adversarial_challenges(plan="Implement authentication with security")
        assert len(challenges) > 0


class TestFailureRecord:
    def test_dataclass_creation(self):
        record = FailureRecord(
            date="2026-01-01",
            title="Test failure",
            task="write test",
            approach="used X",
            failure_mode="Y",
            root_cause="Z",
            fix_applied="W",
            prevention_rule="V",
            tags=["testing"],
        )
        assert record.task == "write test"
        assert record.tags == ["testing"]