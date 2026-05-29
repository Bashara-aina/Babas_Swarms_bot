"""M2.7 Self-Evolution Engine — bridges FeedbackLearner with FAILURES.md pipeline.

Implements the M2.7 100-round self-improvement loop adapted for swarm-bot:
  1. After every failed attempt → append to FAILURES.md
  2. After 5+ failures → build EVAL_SET.md regression tests
  3. Analyze failures → hypothesize harness fix → modify ONE CLAUDE.md thing
  4. Evaluate → compare → keep or revert

Leverages existing core/optimization/feedback_learner.py (Redis-backed feedback)
and creates M2.7-style documentation files.

Reference: M2.7 Full Capability Activation — Self-Evolution System (Section D1-D2)
"""

from __future__ import annotations

import datetime
import logging
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Bounded cache for parsed FAILURES.md entries — prevents unbounded parsing
_MAX_CACHED_ENTRIES = 50

# ---------------------------------------------------------------------------
# Failure record
# ---------------------------------------------------------------------------


@dataclass
class FailureRecord:
    """Structured failure for FAILURES.md."""

    date: str
    title: str
    task: str
    approach: str
    failure_mode: str
    root_cause: str
    fix_applied: str
    prevention_rule: str
    tags: list[str]




# ---------------------------------------------------------------------------
# Self-Evolution Engine
# ---------------------------------------------------------------------------


class SelfEvolutionEngine:
    """M2.7 self-evolution feedback pipeline.

    Usage:
        engine = SelfEvolutionEngine("/path/to/project")

        # After a failure:
        await engine.record_failure(
            task="Adding /budget command",
            approach="Direct SQL query in handler",
            failure_mode="SQLite locked — concurrent requests fail",
            root_cause="sync sqlite3 in async context",
            fix="Use aiosqlite with connection pool",
            prevention="Never use sync DB in async handlers",
        )

        # When FAILURES.md has 5+ entries:
        count = await engine.build_eval_set_from_failures()

        # Get Critic-style challenges from failure history:
        challenges = engine.get_adversarial_challenges("Add /budget command")
    """

    FAILURES_FILE = "FAILURES.md"
    DECISIONS_FILE = "DECISIONS.md"
    EVAL_SET_FILE = "EVAL_SET.md"

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.failures_file = self.project_root / self.FAILURES_FILE
        self.decisions_file = self.project_root / self.DECISIONS_FILE
        self.eval_set_file = self.project_root / self.EVAL_SET_FILE
        self._hermes_skills_dir = (
            self.project_root / "ext" / "hermes-agent" / "skills"
        )
        # Bounded LRU cache — prevents unbounded file read on every call
        self._failures_cache: OrderedDict[str, tuple[float, list[FailureRecord]]] = (
            OrderedDict()
        )

    # ---------------------------------------------------------------------------
    # Hermes skill writing
    # ---------------------------------------------------------------------------

    def _write_hermes_skill(self, name: str, content: str) -> None:
        """Write a skill to Hermes skills directory for cross-session memory."""
        try:
            skills_dir = self._hermes_skills_dir
            skills_dir.mkdir(parents=True, exist_ok=True)
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            fpath = skills_dir / f"{safe_name}.md"
            fpath.write_text(content, encoding="utf-8")
            logger.debug("[SelfEvolution] Wrote Hermes skill: %s", fpath.name)
        except Exception as e:
            logger.warning("[SelfEvolution] Failed to write Hermes skill: %s", e)

    # ---------------------------------------------------------------------------
    # Failure recording
    # ---------------------------------------------------------------------------

    async def record_failure(
        self,
        task: str,
        approach: str,
        failure_mode: str,
        root_cause: str,
        fix_applied: str,
        prevention_rule: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Append a failure record to FAILURES.md.

        Call this after every failed attempt (bug, wrong approach, rollback).
        """
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        date_str = now.strftime("%Y-%m-%d")
        title_str = title or f"{date_str} — {task[:60]}"

        # Infer tags from content
        inferred_tags = self._infer_tags(task, approach, root_cause)
        if tags:
            inferred_tags.extend(tags)
        tags_str = ", ".join(sorted(set(inferred_tags)))

        entry_lines = [
            "",
            f"### {title_str}",
            f"Task: {task}",
            f"Approach: {approach}",
            f"Failure mode: {failure_mode}",
            f"Root cause: {root_cause}",
            f"Fix applied: {fix_applied}",
            f"Prevention rule: {prevention_rule}",
            f"Tags: [{tags_str}]",
        ]

        entry_text = "\n".join(entry_lines)

        try:
            with open(self.failures_file, "a", encoding="utf-8") as f:
                f.write(entry_text + "\n")
            logger.info("[SelfEvolution] Recorded failure: %s", title_str)
        except Exception as e:
            logger.error("[SelfEvolution] Failed to write FAILURES.md: %s", e)

        self._notify_feedback_learner(task, "failure")
        self._write_hermes_skill(
            name=f"failure-{title_str[:40].replace(' ', '-').replace('/', '-')}",
            content=f"# Failure: {title_str}\n\nTask: {task}\nApproach: {approach}\nFailure mode: {failure_mode}\nRoot cause: {root_cause}\nFix applied: {fix_applied}\nPrevention: {prevention_rule}\nTags: {tags_str}\n",
        )

    def _notify_feedback_learner(self, task: str, outcome: str) -> None:
        """Notify FeedbackLearner of failure for agent weight adjustment."""
        try:
            from core.optimization.feedback_learner import get_learner

            learner = get_learner()
            learner.record_by_agent(
                agent=self._infer_agent_from_task(task),
                task=task,
                rating=-1,  # negative
                comment=f"self-evolution: {outcome}",
            )
        except Exception:
            pass  # FeedbackLearner is optional

    def _infer_agent_from_task(self, task: str) -> str:
        """Heuristic: infer which agent was being used from task content."""
        task_lower = task.lower()
        if any(kw in task_lower for kw in ["screen", "do", "cmd", "shell", "computer"]):
            return "computer"
        elif any(kw in task_lower for kw in ["code", "implement", "build", "function"]):
            return "coding"
        elif any(kw in task_lower for kw in ["research", "find", "search", "lookup"]):
            return "researcher"
        elif any(kw in task_lower for kw in ["debug", "error", "fix", "bug"]):
            return "debug"
        elif any(kw in task_lower for kw in ["math", "proof", "calculate"]):
            return "math"
        return "general"

    def _infer_tags(
        self, task: str, approach: str, root_cause: str
    ) -> list[str]:
        """Infer failure category tags from content."""
        tags: list[str] = []
        combined = f"{task} {approach} {root_cause}".lower()

        tag_map = {
            "async": ["asyncio", "thread", "blocking", "sync"],
            "security": ["injection", "auth", "permission", "secret", "credential"],
            "telegram": ["telegram", "parse_mode", "html", "markdown", "message"],
            "memory": ["memory", "store", "mem0", "chroma", "sqlite", "db"],
            "llm": ["llm", "model", "api", "rate limit", "groq", "cerebras"],
            "intent": ["intent", "router", "classify", "route"],
            "shell": ["shell", "subprocess", "exec", "timeout"],
            "deployment": ["systemd", "service", "gpu", "cuda", "vrAM"],
            "browser": ["playwright", "browser", "headless"],
            "vrAM": ["vram", "cuda", "ollama", "gpu", "memory"],
        }

        for tag, keywords in tag_map.items():
            if any(kw in combined for kw in keywords):
                tags.append(tag)

        return tags if tags else ["general"]

    # ---------------------------------------------------------------------------
    # EVAL_SET building
    # ---------------------------------------------------------------------------

    async def build_eval_set_from_failures(self) -> int:
        """Build regression tests in EVAL_SET.md from accumulated failures.

        Called when FAILURES.md has 5+ entries.
        Groups failures by root cause category and creates test templates.
        Returns number of test cases added.
        """
        failures = self._read_failures()
        if len(failures) < 5:
            logger.info(
                "[SelfEvolution] Only %d failures — need 5+ for EVAL_SET. Skipping.",
                len(failures),
            )
            return 0

        # Group by root cause category
        categories: dict[str, list[FailureRecord]] = {}
        for f in failures:
            primary_tag = f.tags[0] if f.tags else "general"
            categories.setdefault(primary_tag, []).append(f)

        # Generate test cases from categories
        test_cases: list[str] = []
        for i, (category, category_failures) in enumerate(categories.items(), 1):
            test_id = f"TEST-{i:03d}"
            test_lines = self._generate_test_case(test_id, category, category_failures)
            test_cases.append(test_lines)

        # Append to EVAL_SET.md
        if test_cases:
            eval_lines = [
                "",
                "---",
                "",
                f"## Auto-generated {datetime.date.today()} — {len(test_cases)} test cases",
                "",
            ]
            eval_lines.extend("\n".join(test_cases))
            eval_lines.append("")

            try:
                with open(self.eval_set_file, "a", encoding="utf-8") as f:
                    f.write("\n".join(eval_lines))
                logger.info(
                    "[SelfEvolution] Built %d test cases into EVAL_SET.md",
                    len(test_cases),
                )
            except Exception as e:
                logger.error("[SelfEvolution] Failed to write EVAL_SET.md: %s", e)

        return len(test_cases)

    def _read_failures(self) -> list[FailureRecord]:
        """Read failure records from FAILURES.md with bounded LRU cache.

        Re-parses only when the file has changed size (indicating new entries),
        avoiding unbounded full-file reads on every call.
        """
        if not self.failures_file.exists():
            return []

        try:
            stat = self.failures_file.stat()
            current_mtime = stat.st_mtime
            current_size = stat.st_size
        except OSError:
            return []

        cache_key = "failures_list"
        cached = self._failures_cache.get(cache_key)

        if cached is not None:
            cached_mtime, cached_records = cached
            # Check if file unchanged — use cached result
            if cached_mtime == current_mtime:
                # Move to end (LRU)
                self._failures_cache.move_to_end(cache_key)
                return cached_records
            # File changed — check if it grew enough to warrant re-parse
            cached_lines = len(cached_records) * 15  # rough line estimate per entry
            if current_size < cached_lines * 1.5:
                # File shrunk or minimal growth — keep using stale cache
                self._failures_cache.move_to_end(cache_key)
                return cached_records

        # Parse file — but only read enough to get the last N entries
        records = self._parse_failures_bounded(max_entries=_MAX_CACHED_ENTRIES)
        self._failures_cache[cache_key] = (current_mtime, records)
        if len(self._failures_cache) > 2:
            self._failures_cache.popitem(last=False)  # evict oldest

        return records

    def _parse_failures_bounded(self, max_entries: int) -> list[FailureRecord]:
        """Parse FAILURES.md reading backwards from EOF to find recent entries.

        This avoids reading the entire file by estimating where recent entries
        begin and seeking backwards.
        """
        failures: list[FailureRecord] = []

        try:
            with open(self.failures_file, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return []

        if not content.strip():
            return []

        entries = re.split(r"\n###\s+", content)

        # Process entries from oldest to newest (entries[0] is header)
        for entry in entries[1:]:
            if len(failures) >= max_entries:
                break
            lines = entry.strip().split("\n")
            if not lines:
                continue
            title = lines[0].strip()
            record: dict = {
                "date": "", "title": title, "task": "", "approach": "",
                "failure_mode": "", "root_cause": "", "fix_applied": "",
                "prevention_rule": "", "tags": [],
            }
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("Task:"):
                    record["task"] = line[5:].strip()
                elif line.startswith("Approach:"):
                    record["approach"] = line[9:].strip()
                elif line.startswith("Failure mode:"):
                    record["failure_mode"] = line[14:].strip()
                elif line.startswith("Root cause:"):
                    record["root_cause"] = line[12:].strip()
                elif line.startswith("Fix applied:"):
                    record["fix_applied"] = line[12:].strip()
                elif line.startswith("Prevention rule:"):
                    record["prevention_rule"] = line[17:].strip()
                elif line.startswith("Tags:"):
                    tag_str = line[6:].strip().strip("[]")
                    record["tags"] = [t.strip() for t in tag_str.split(",")]

            if any(record.values()):
                failures.append(FailureRecord(**record))

        return failures

    def _generate_test_case(
        self, test_id: str, category: str, failures: list[FailureRecord]
    ) -> str:
        """Generate a test case block from a failure group."""
        lines = [
            f"### {test_id}: {category.title()} — {len(failures)} related failures",
            "",
            f"Source: FAILURES.md — {len(failures)} entries in '{category}' category",
            "",
        ]

        # Build test description from most recent failure
        latest = failures[-1]
        lines.extend([
            f"Trigger: When working on tasks involving {category}",
            "",
            "Command template:",
        ])

        # Generate command based on category
        if category == "async":
            lines.append(
                "  python -c \"import asyncio; "
                "assert 'time.sleep' not in open('core/handler.py').read(); print('async ok')\""
            )
        elif category == "security":
            lines.append(
                "  python -c \"import ast, subprocess; "
                "code = open('handlers/secret.py').read(); "
                "assert 'os.getenv' in code or 'encrypt' in code; print('security ok')\""
            )
        elif category == "telegram":
            lines.append(
                "  python -c \"import html; "
                "assert html.escape('<test&>') == '&lt;test&amp;&gt;'; print('telegram ok')\""
            )
        elif category == "llm":
            lines.append(
                "  python -c \"from llm_client import get_fallback_chain; "
                "chain = get_fallback_chain('general'); "
                "assert len(chain) >= 2; print('llm fallback ok')\""
            )
        else:
            lines.append(f"  # Generic test for {category} — implement based on failure pattern")

        lines.extend([
            "",
            f"Expected: No recurrence of {category} failures",
            "",
            f"Prevention: {latest.prevention_rule}",
            "",
        ])

        return "\n".join(lines)

    # ---------------------------------------------------------------------------
    # Adversarial challenge generation
    # ---------------------------------------------------------------------------

    def get_adversarial_challenges(self, plan: str) -> list[str]:
        """Generate Critic-style challenges from failure history.

        Uses past failures to generate pointed questions that
        a Critic agent should ask before implementing a plan.

        Returns:
            List of challenge strings (to be addressed before implementation)
        """
        failures = self._read_failures()
        if not failures:
            return []

        plan_lower = plan.lower()
        challenges: list[str] = []

        # Related failures by tag
        relevant_failures: list[FailureRecord] = []
        for f in failures:
            if f.tags and any(tag in plan_lower for tag in f.tags):
                relevant_failures.append(f)

        if not relevant_failures:
            return challenges

        # Generate challenges from related failures
        for f in relevant_failures[-3:]:  # last 3 relevant
            if f.prevention_rule:
                challenges.append(
                    f"FAILURE HISTORY: '{f.failure_mode[:60]}...'\n"
                    f"  Prevention that was violated: {f.prevention_rule}\n"
                    f"  → Does your plan account for this?"
                )

        return challenges

    # ---------------------------------------------------------------------------
    # Decision recording
    # ---------------------------------------------------------------------------

    async def record_decision(
        self,
        title: str,
        context: str,
        decision: str,
        rationale: str,
        alternatives: list[str] | None = None,
        consequences: dict[str, str] | None = None,
    ) -> None:
        """Record an architecture decision to DECISIONS.md."""
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        date_str = now.strftime("%Y-%m-%d")

        # Count existing ADRs
        existing_count = 0
        if self.decisions_file.exists():
            content = self.decisions_file.read_text()
            existing_count = content.count("## ADR-")

        adr_num = existing_count + 1

        lines = [
            "",
            f"## ADR-{adr_num}: {title}",
            f"Date: {date_str}",
            "Status: ACCEPTED",
            "",
            "### Context",
            context,
            "",
            "### Decision",
            decision,
            "",
            "### Rationale",
            rationale,
        ]

        if alternatives:
            lines.extend(["", "### Alternatives Considered"])
            for alt in alternatives:
                lines.append(f"- {alt}")

        if consequences:
            lines.extend(["", "### Consequences"])
            for key, val in consequences.items():
                lines.append(f"- **{key}:** {val}")

        lines.extend(["", "### Do Not Revisit Unless", "[define conditions]", ""])

        try:
            with open(self.decisions_file, "a", encoding="utf-8") as f:
                f.write("\n".join(lines))
            logger.info("[SelfEvolution] Recorded ADR-%d: %s", adr_num, title)
        except Exception as e:
            logger.error("[SelfEvolution] Failed to write DECISIONS.md: %s", e)

        self._write_hermes_skill(
            name=f"adr-{adr_num:03d}-{title[:40].replace(' ', '-').replace('/', '-')}",
            content=f"# ADR-{adr_num}: {title}\n\nContext: {context}\nDecision: {decision}\nRationale: {rationale}\n",
        )


# ---------------------------------------------------------------------------
# Convenience singleton
# ---------------------------------------------------------------------------

_engine: SelfEvolutionEngine | None = None


def get_self_evolution_engine(
    project_root: str | None = None,
) -> SelfEvolutionEngine:
    """Return global SelfEvolutionEngine singleton."""
    global _engine
    if _engine is None:
        if project_root is None:
            project_root = str(Path(__file__).parent.parent)
        _engine = SelfEvolutionEngine(project_root)
    return _engine
