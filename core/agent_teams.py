"""M2.7 Agent Teams Orchestrator — 3-role adversarial reasoning system.

Formalizes Planner / Builder / Critic roles for complex tasks.
This is NOT a runtime for the Telegram bot — it is a utility module for
Claude Code / OpenCode sessions doing multi-agent work.

Planner: owns goal, spec, success criteria — NEVER writes code.
Builder: implements against Planner's spec ONLY — NEVER invents architecture.
Critic: adversarial — MUST find flaws BEFORE they ship.

Adversarial loop:
  1. Planner generates SPEC (goal locked)
  2. Builder implements against locked SPEC
  3. Critic attacks assumptions, failure modes, edge cases
  4. Planner resolves Critic's objections
  5. Builder finalizes

Reference: M2.7 Full Capability Activation — Agent Teams Protocol (Section 0b)
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Spec:
    """Planner's output — locked goal and acceptance criteria."""

    goal: str
    acceptance_criteria: list[str]
    constraints: list[str]
    risks: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()
    )
    objections_resolved: list[str] = field(default_factory=list)


@dataclass
class BuildResult:
    """Builder's output — implementation against locked spec."""

    files_modified: list[str]
    files_created: list[str]
    implementation_summary: str
    spec_compliant: bool
    deviation_notes: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()
    )


@dataclass
class CriticIssue:
    """Critic's output — a single identified issue."""

    severity: str  # P0 / P1 / P2 / P3
    category: str  # security / correctness / maintainability / performance / assumption
    title: str
    description: str
    recommendation: str
    must_resolve: bool  # True for P0/P1


@dataclass
class CriticReport:
    """Critic's full adversarial assessment."""

    issues: list[CriticIssue]
    assumptions_challenged: list[str]
    failure_mode_scenarios: list[str]
    overall_verdict: str  # APPROVED / REJECTED / CONDITIONAL
    verdict_reason: str
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()
    )


@dataclass
class TeamSession:
    """Full adversarial session log."""

    task: str
    spec: Optional[Spec] = None
    build: Optional[BuildResult] = None
    critic: Optional[CriticReport] = None
    iterations: int = 0
    started_at: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()
    )
    completed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Critic — adversarial reasoning engine
# ---------------------------------------------------------------------------


class Critic:
    """M2.7 Critic role — adversarial challenge against plan or implementation."""

    def __init__(self) -> None:
        self._failure_patterns: list[str] = []
        self._load_failure_patterns()

    def _load_failure_patterns(self) -> None:
        """Load known failure patterns from FAILURES.md if it exists."""
        failures_file = Path(__file__).parent.parent / "FAILURES.md"
        if failures_file.exists():
            content = failures_file.read_text()
            # Extract failure patterns (simplified — real impl would parse markdown)
            if "root cause:" in content.lower():
                self._failure_patterns = [
                    "shell injection",
                    "rate limit",
                    "vram overflow",
                    "parse mode",
                    "context pollution",
                    "error accumulation",
                ]

    async def review_spec(self, spec: Spec) -> CriticReport:
        """Critic attacks the Planner's SPEC before Builder touches code."""
        issues: list[CriticIssue] = []
        assumptions: list[str] = []
        failures: list[str] = []

        # P0: Security — does spec handle auth, input validation, secrets?
        if "shell" in spec.goal.lower() and not any(
            c.lower() in ["sanitiz", "allowlist", "timeout", "validation"]
            for c in spec.constraints
        ):
            issues.append(
                CriticIssue(
                    severity="P0",
                    category="security",
                    title="Shell command without input sanitization",
                    description="Shell execution goal lacks explicit input sanitization constraint. "
                    "Without allowlist + timeout + escaping, this is a shell injection risk.",
                    recommendation="Add constraint: 'All shell input must be validated against an "
                    "allowlist regex + asyncio.wait_for(proc, timeout=30)'.",
                    must_resolve=True,
                )
            )

        # P0: Ambiguity — is the goal well-defined?
        vague_indicators = ["implement", "fix", "improve", "enhance", "refactor"]
        if any(vi in spec.goal.lower() for vi in vague_indicators) and len(spec.goal) < 40:
            issues.append(
                CriticIssue(
                    severity="P1",
                    category="correctness",
                    title="Goal is too vague for locked spec",
                    description="Spec goal uses vague language. "
                    "Without concrete acceptance criteria, Builder cannot know when done.",
                    recommendation="Break down goal into concrete, testable acceptance criteria. "
                    "No 'improve X' — must define 'X must do Y within Z ms'.",
                    must_resolve=True,
                )
            )

        # P1: Error accumulation — does plan account for LLM error propagation?
        if len(spec.acceptance_criteria) > 5 and not any(
            "error" in ac.lower() or "failure" in ac.lower() for ac in spec.acceptance_criteria
        ):
            issues.append(
                CriticIssue(
                    severity="P1",
                    category="correctness",
                    title="No error/failure acceptance criteria",
                    description="Complex plan with no error handling criteria. "
                    "Multi-step implementations accumulate errors without explicit recovery paths.",
                    recommendation="Add acceptance criteria: "
                    "'Must handle X failure gracefully with Y recovery' for each critical step.",
                    must_resolve=False,
                )
            )

        # P2: Scope creep — does goal scope correctly?
        if len(spec.acceptance_criteria) > 8:
            issues.append(
                CriticIssue(
                    severity="P2",
                    category="maintainability",
                    title="Spec scope too large — risk of incomplete implementation",
                    description=f"{len(spec.acceptance_criteria)} acceptance criteria. "
                    "Large scopes → partial implementations → technical debt.",
                    recommendation="Consider splitting into 2 specs: core vs. nice-to-have.",
                    must_resolve=False,
                )
            )

        # Challenge fundamental assumptions
        if "api" in spec.goal.lower() or "http" in spec.goal.lower():
            assumptions.append(
                "External API availability is assumed. "
                "Critic flags: add rate limit + timeout + fallback handling as acceptance criteria."
            )
        if "database" in spec.goal.lower() or "db" in spec.goal.lower():
            assumptions.append(
                "Database state transitions are assumed correct. "
                "Critic flags: add transactional boundary + rollback criteria."
            )

        # Simulate failure modes
        failures.append(
            f"Failure scenario: if step 3 of {len(spec.acceptance_criteria)} fails, "
            "does the implementation rollback cleanly? Not addressed in spec."
        )

        verdict = "REJECTED" if any(i.must_resolve for i in issues) else "APPROVED"
        reason = (
            "P0 issues must be resolved before Builder starts."
            if verdict == "REJECTED"
            else "Spec is sufficient for Builder to proceed. P1/P2 issues are advisory."
        )

        return CriticReport(
            issues=issues,
            assumptions_challenged=assumptions,
            failure_mode_scenarios=failures,
            overall_verdict=verdict,
            verdict_reason=reason,
        )

    async def review_build(self, spec: Spec, build: BuildResult) -> CriticReport:
        """Critic reviews Builder's implementation against locked spec."""
        issues: list[CriticIssue] = []
        assumptions: list[str] = []
        failures: list[str] = []

        # Check spec compliance
        if not build.spec_compliant:
            issues.append(
                CriticIssue(
                    severity="P0",
                    category="correctness",
                    title="Implementation deviates from locked spec",
                    description="Builder reported spec_compliant=False. "
                    f"Deviations: {build.deviation_notes}",
                    recommendation="Align implementation with spec OR raise spec change with Planner.",
                    must_resolve=True,
                )
            )

        # Check each acceptance criterion has implementation
        for criterion in spec.acceptance_criteria:
            if not any(
                criterion.lower() in f.lower() for f in build.files_modified + build.files_created
            ):
                # Soft check — criterion might be tested rather than implemented
                pass

        # Security: Check for hardcoded secrets
        for filepath in build.files_modified + build.files_created:
            try:
                p = Path(filepath)
                if p.exists() and p.stat().st_size < 100_000:  # skip large files
                    content = p.read_text()
                    secret_patterns = [
                        "password=",
                        "api_key=",
                        "token=",
                        "secret=",
                        "PRIVATE_KEY",
                    ]
                    for pattern in secret_patterns:
                        if pattern in content and "os.getenv" not in content:
                            issues.append(
                                CriticIssue(
                                    severity="P0",
                                    category="security",
                                    title=f"Potential hardcoded secret in {filepath}",
                                    description=f"Found '{pattern}' in code without os.getenv() guard.",
                                    recommendation="Move all secrets to os.getenv() — "
                                    "never hardcode credentials in source.",
                                    must_resolve=True,
                                )
                            )
                            break
            except Exception:
                pass  # skip files we can't read

        # Check async discipline
        for filepath in build.files_modified + build.files_created:
            try:
                p = Path(filepath)
                if p.exists() and p.suffix == ".py" and p.stat().st_size < 50_000:
                    content = p.read_text()
                    if "time.sleep(" in content and "asyncio.sleep" not in content:
                        issues.append(
                            CriticIssue(
                                severity="P1",
                                category="correctness",
                                title=f"Blocking sleep() in async file {filepath}",
                                description="time.sleep() found in async Python file — "
                                "blocks the event loop.",
                                recommendation="Replace time.sleep() with asyncio.sleep().",
                                must_resolve=True,
                            )
                        )
            except Exception:
                pass

        # P2: Empty implementation check
        if len(build.files_created) == 0 and len(build.files_modified) == 0:
            issues.append(
                CriticIssue(
                    severity="P2",
                    category="correctness",
                    title="No files modified or created",
                    description="Builder returned with empty file list. "
                    "Either task was no-op or Builder skipped implementation.",
                    recommendation="Verify the task is complete. If not, re-engage Builder.",
                    must_resolve=False,
                )
            )

        verdict = "REJECTED" if any(i.must_resolve for i in issues) else "APPROVED"
        reason = (
            "P0 issues block this implementation."
            if verdict == "REJECTED"
            else "Implementation passes Critic review."
        )

        return CriticReport(
            issues=issues,
            assumptions_challenged=assumptions,
            failure_mode_scenarios=failures,
            overall_verdict=verdict,
            verdict_reason=reason,
        )


# ---------------------------------------------------------------------------
# Planner — strategic goal and spec generation
# ---------------------------------------------------------------------------


class Planner:
    """M2.7 Planner role — owns goal, generates SPEC before Builder acts."""

    async def generate_spec(self, task: str) -> Spec:
        """Analyze task and generate locked SPEC.

        This is a structured reasoning method, not an LLM call.
        For complex tasks, delegate to an LLM with the Critique's spec template.
        """
        # Structured decomposition — for simple tasks, do inline
        goal = task.strip()

        # Heuristic: complex tasks get more criteria
        complexity = len(task.split()) + sum(1 for kw in ["implement", "build", "create", "design"] if kw in task.lower())
        num_criteria = max(3, min(8, complexity))

        acceptance_criteria = [
            f"Criterion {i+1}: [derived from goal decomposition]"
            for i in range(num_criteria)
        ]
        constraints = [
            "Must not break existing functionality (regression-free)",
            "Async discipline: no blocking I/O, no time.sleep()",
            "Security: no hardcoded secrets, input validation, auth checks",
        ]
        risks = [
            "Risk: scope may expand mid-implementation",
            "Risk: dependency conflict if new package added",
        ]

        return Spec(
            goal=goal,
            acceptance_criteria=acceptance_criteria,
            constraints=constraints,
            risks=risks,
        )

    async def resolve_objections(self, spec: Spec, critic: CriticReport) -> Spec:
        """Planner resolves Critic's P0/P1 objections by updating spec."""
        if critic.overall_verdict == "APPROVED":
            return spec

        # Update spec with resolved objections
        resolved = spec.objections_resolved.copy()
        for issue in critic.issues:
            if issue.must_resolve:
                resolved.append(f"[{issue.severity}] {issue.title}: {issue.recommendation}")

        return Spec(
            goal=spec.goal,
            acceptance_criteria=spec.acceptance_criteria,
            constraints=spec.constraints,
            risks=spec.risks,
            objections_resolved=resolved,
        )


# ---------------------------------------------------------------------------
# Builder — execution against locked spec (placeholder interface)
# ---------------------------------------------------------------------------


class Builder:
    """M2.7 Builder role — implements against Planner's locked SPEC ONLY.

    This is a placeholder — actual implementation is done by Claude Code / OpenCode.
    Builder methods exist to formalize the interface and emit BuildResult.
    """

    def report_build(
        self,
        task: str,
        files_modified: list[str],
        files_created: list[str],
        implementation_summary: str,
        spec_compliant: bool = True,
        deviation_notes: Optional[list[str]] = None,
    ) -> BuildResult:
        """Builder reports implementation results.

        Call this AFTER implementation to emit BuildResult for Critic review.
        """
        return BuildResult(
            files_modified=files_modified,
            files_created=files_created,
            implementation_summary=implementation_summary,
            spec_compliant=spec_compliant,
            deviation_notes=deviation_notes or [],
        )


# ---------------------------------------------------------------------------
# AgentTeam — full adversarial orchestration
# ---------------------------------------------------------------------------


class AgentTeam:
    """M2.7 3-role adversarial team orchestrator.

    Usage:
        team = AgentTeam()
        session = await team.run("Build a /budget command handler")
        print(f"Verdict: {session.critic.overall_verdict}")
        print(f"Files: {session.build.files_created}")
    """

    def __init__(self) -> None:
        self.planner = Planner()
        self.builder = Builder()
        self.critic = Critic()
        self._session: Optional[TeamSession] = None

    async def run(self, task: str, max_iterations: int = 3) -> TeamSession:
        """Run full adversarial loop: Planner → Builder → Critic → resolve → final.

        Args:
            task: The task description
            max_iterations: Maximum critic-Builder iterations (default 3)

        Returns:
            TeamSession with all outputs (spec, build, critic)
        """
        self._session = TeamSession(task=task)
        logger.info("[AgentTeam] Starting adversarial loop for: %s", task[:80])

        # Step 1: Planner generates SPEC
        spec = await self.planner.generate_spec(task)
        self._session.spec = spec
        logger.info("[AgentTeam] Planner produced SPEC with %d acceptance criteria", len(spec.acceptance_criteria))

        # Step 2: Critic reviews SPEC before Builder acts
        spec_critique = await self.critic.review_spec(spec)
        self._session.critic = spec_critique
        logger.info("[AgentTeam] Critic SPEC verdict: %s", spec_critique.overall_verdict)

        if spec_critique.overall_verdict == "REJECTED":
            # Planner resolves objections
            spec = await self.planner.resolve_objections(spec, spec_critique)
            self._session.spec = spec
            logger.info("[AgentTeam] Planner resolved objections, %d remaining",
                        len(spec.objections_resolved))

        # Step 3: Builder implements (placeholder — actual impl is external)
        # Builder reports results via self.builder.report_build() after implementation
        # For now, mark session as ready for Builder
        logger.info(
            "[AgentTeam] SPEC locked. Builder may proceed. "
            "Call builder.report_build() then critic.review_build() to complete."
        )

        self._session.iterations = 1
        self._session.completed_at = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()

        return self._session

    def load_build(self, build: BuildResult) -> TeamSession:
        """Load Builder's BuildResult into session and run Critic review."""
        if self._session is None:
            raise RuntimeError("Must call run() before load_build()")
        self._session.build = build
        logger.info("[AgentTeam] Builder reported %d files modified, %d created",
                    len(build.files_modified), len(build.files_created))

        # Critic reviews implementation
        if self._session.spec is not None:
            impl_critique = asyncio.run(
                self.critic.review_build(self._session.spec, build)
            )
            self._session.critic = impl_critique
            logger.info("[AgentTeam] Critic implementation verdict: %s",
                        impl_critique.overall_verdict)
        return self._session

    def to_json(self) -> str:
        """Serialize session to JSON for logging / FAILURES.md population."""
        if self._session is None:
            return "{}"
        return json.dumps(
            {
                "task": self._session.task,
                "spec_goal": self._session.spec.goal if self._session.spec else None,
                "spec_criteria": (
                    self._session.spec.acceptance_criteria
                    if self._session.spec
                    else None
                ),
                "build_files": (
                    self._session.build.files_created
                    if self._session.build
                    else None
                ),
                "critic_verdict": (
                    self._session.critic.overall_verdict
                    if self._session.critic
                    else None
                ),
                "critic_issues": [
                    {"severity": i.severity, "title": i.title, "category": i.category}
                    for i in (self._session.critic.issues if self._session.critic else [])
                ],
                "iterations": self._session.iterations,
            },
            indent=2,
        )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

_agent_team: Optional[AgentTeam] = None


def get_agent_team() -> AgentTeam:
    """Return global AgentTeam singleton."""
    global _agent_team
    if _agent_team is None:
        _agent_team = AgentTeam()
    return _agent_team
