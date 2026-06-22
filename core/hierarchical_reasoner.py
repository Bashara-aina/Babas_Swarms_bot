"""M3 Hierarchical Reasoner — 3-layer reasoning decomposition.

ReasonFlux-inspired: decompose every complex task into 3 distinct layers
that cannot "leak" upward. Layer 3 (execution) outputs cannot change Layer 1 goals.

LAYER 1 — MACRO (strategic): What are we trying to achieve? Why?
  - Goal restatement
  - Success criteria
  - Constraint mapping
  - Risk tolerance

LAYER 2 — MICRO (file-level): What components need to change?
  - File-by-file analysis
  - Interface changes
  - Data flow modifications
  - Test strategy

LAYER 3 — EXEC (line-level): What does the actual code look like?
  - Specific function signatures
  - Algorithmic choices
  - Edge case handling
  - Error handling

CRITICAL RULE: Layer 3 reasoning CANNOT change Layer 1 goals.
If Layer 3 discovers something that challenges Layer 1, it surfaces
via a "REVISIT FLAG" but does NOT modify Layer 1 directly.

Reference: M3 Full Capability Activation — Hierarchical Reasoning (Section D4)
Inspired by: ReasonFlux multi-level reasoning architecture
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import StrEnum

# ---------------------------------------------------------------------------
# Layer definitions
# ---------------------------------------------------------------------------


class ReasonLayer(StrEnum):
    MACRO = "MACRO"      # Layer 1: strategic, goal-level
    MICRO = "MICRO"     # Layer 2: file-level technical
    EXEC = "EXEC"       # Layer 3: line-level code


class RevisitFlag(StrEnum):
    """Flags raised when lower-layer reasoning challenges upper-layer assumptions."""
    NONE = "NONE"
    GOAL_CHALLENGED = "GOAL_CHALLENGED"        # L3 → L1: execution reveals goal flaw
    CONSTRAINT_REMOVED = "CONSTRAINT_REMOVED"   # L3 → L1: constraint was wrong
    RISK_REASSESSED = "RISK_REASSESSED"        # L2 → L1: risk level changed
    APPROACH_INVALID = "APPROACH_INVALID"      # L3 → L2: file approach won't work


@dataclass
class Layer1Macro:
    """Layer 1: MACRO — strategic reasoning."""

    # Goal restatement
    goal: str
    original_user_request: str
    success_criteria: list[str]
    measurable_outcomes: list[str]

    # Constraints and boundaries
    hard_constraints: list[str] = field(default_factory=list)   # Must satisfy
    soft_constraints: list[str] = field(default_factory=list)  # Should satisfy
    deal_breakers: list[str] = field(default_factory=list)     # Failure conditions

    # Risk
    risk_tolerance: str = "MEDIUM"  # LOW / MEDIUM / HIGH
    irreversible_changes: list[str] = field(default_factory=list)

    # Why this goal matters
    motivation: str = ""
    stakeholder: str = "Bashara"  # Who cares about this outcome

    # Cross-cutting concerns
    non_negotiables: list[str] = field(default_factory=list)  # Security, privacy, etc.

    def goal_changed_by(self, lower_layer_insight: str) -> bool:
        """Returns True if lower layer has challenged the goal itself."""
        return False  # Only set to True via explicitRevisitFlag

    def challenge_goal(self, reason: str) -> None:
        """Called by lower layer when goal is challenged — creates revisit flag."""
        self._has_revisit = True
        self._revisit_reason = reason


@dataclass
class Layer2Micro:
    """Layer 2: MICRO — file-level reasoning."""

    # What files/components are involved
    files_to_create: list[str] = field(default_factory=list)
    files_to_modify: list[str] = field(default_factory=list)
    files_to_delete: list[str] = field(default_factory=list)

    # Interface contracts
    new_interfaces: list[str] = field(default_factory=list)   # New public APIs
    modified_interfaces: list[str] = field(default_factory=list)  # Changed signatures
    deleted_interfaces: list[str] = field(default_factory=list)  # Removed/changed

    # Data flow
    data_flow_changes: list[str] = field(default_factory=list)
    new_dependencies: list[str] = field(default_factory=list)
    removed_dependencies: list[str] = field(default_factory=list)

    # Test strategy
    test_files_needed: list[str] = field(default_factory=list)
    integration_points: list[str] = field(default_factory=list)
    mocking_strategy: str = ""  # How to isolate components for testing

    # Risk at micro level
    high_risk_files: list[str] = field(default_factory=list)   # Files with many side effects
    blast_radius: str = "LOCAL"  # LOCAL / MODERATE / WIDE

    def approach_invalidated_by(self, file: str, reason: str) -> None:
        """Called by L3 when a micro-level approach won't work."""
        self._has_revisit = True
        self._revisit_reason = reason
        self._invalidated_file = file


@dataclass
class Layer3Exec:
    """Layer 3: EXEC — line-level execution reasoning."""

    # Specific implementation decisions
    function_signatures: list[str] = field(default_factory=list)
    algorithm_choices: list[str] = field(default_factory=list)
    data_structures: list[str] = field(default_factory=list)

    # Code generation
    code_blocks_needed: list[str] = field(default_factory=list)  # Descriptions of code to write
    code_skeletons: list[str] = field(default_factory=list)        # SoT-style skeletons

    # Edge cases
    edge_cases_identified: list[str] = field(default_factory=list)
    error_handling_strategy: str = ""
    fallback_strategy: str = ""

    # L3 output — CANNOT leak to L1/L2 as changes
    execution_insights: list[str] = field(default_factory=list)   # Observations only
    execution_warnings: list[str] = field(default_factory=list)   # Flagged concerns
    revisit_flags: list[str] = field(default_factory=list)        # Must surface, not change

    # What L3 learned that L2 should know
    micro_feedback_to_layer2: list[str] = field(default_factory=list)

    def cannot_change_goal(self, insight: str) -> str:
        """Record an insight that L3 noticed but CANNOT change L1 goals.

        L3 can flag: 'This goal seems impossible given current architecture'
        L3 CANNOT do: silently change the goal to 'something achievable'
        """
        self.execution_insights.append(f"[L3-OBSERVED] {insight}")
        return insight

    def flag_for_revisit(self, flag: RevisitFlag, detail: str) -> None:
        """Raise a revisit flag — surfaces to upper layer but doesn't auto-change."""
        self.revisit_flags.append(f"{flag.value}: {detail}")
        # L3 CANNOT modify Layer1/Layer2 state — only flag


# ---------------------------------------------------------------------------
# Hierarchical Reasoner
# ---------------------------------------------------------------------------


@dataclass
class HierarchicalReasoningResult:
    """Complete result from 3-layer hierarchical reasoning."""

    task: str
    layer1: Layer1Macro
    layer2: Layer2Micro
    layer3: Layer3Exec

    # Flags from lower → upper
    revisit_flags: list[str] = field(default_factory=list)
    goal_is_challenged: bool = False

    # Whether reasoning is complete
    reasoning_complete: bool = False
    confidence: float = 0.0  # 0.0–1.0

    # Recommendations
    should_proceed: bool = True
    blockers: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    checked_at: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()
    )


class HierarchicalReasoner:
    """3-layer hierarchical reasoning engine.

    Usage:
        reasoner = HierarchicalReasoner("/home/newadmin/swarm-bot")

        # Before implementing any complex multi-file task:
        result = await reasoner.reason(
            task="Add aiosqlite connection pool to BudgetManager",
            original_request="I want /budget to handle 10+ concurrent users without SQLite busy errors",
            context_chars=60000,  # for confidence scoring
        )

        # Check revisit flags
        if result.goal_is_challenged:
            print("🚨 LOWER LAYER CHALLENGED THE GOAL — STOP AND RECONSIDER")
            for flag in result.revisit_flags:
                print(f"  {flag}")

        # L2 output tells you what files to touch
        print(f"Files to modify: {result.layer2.files_to_modify}")

        # L3 output tells you what the code should look like
        print(f"Code skeletons: {result.layer3.code_skeletons}")

        # Proceed only if reasoning is complete
        if result.reasoning_complete and result.should_proceed:
            print("✅ Ready to implement")
    """

    def __init__(self, project_root: str | None = None) -> None:
        from pathlib import Path
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent

    # ---------------------------------------------------------------------------
    # Main entry point
    # ---------------------------------------------------------------------------

    async def reason(
        self,
        task: str,
        original_request: str,
        context: str | None = None,
        context_chars: int = 0,
    ) -> HierarchicalReasoningResult:
        """Run full 3-layer hierarchical reasoning.

        Args:
            task: Short task description (1 sentence)
            original_request: Full original user request (for L1 motivation)
            context: Additional context (e.g., current conversation)
            context_chars: Context fill % — used for confidence scoring

        Returns:
            HierarchicalReasoningResult with all 3 layers populated
        """
        # Layer 1: MACRO — understand the goal at strategic level
        layer1 = self._reason_layer1(task, original_request)

        # Layer 2: MICRO — map task to file-level components
        layer2 = self._reason_layer2(layer1, task)

        # Layer 3: EXEC — reason about specific code structure
        layer3 = self._reason_layer3(layer1, layer2, task)

        # Propagate revisit flags upward
        revisit_flags = []
        revisit_flags.extend(layer3.revisit_flags)
        if getattr(layer2, '_has_revisit', False):
            revisit_flags.append(f"APPROACH_INVALID: {getattr(layer2, '_revisit_reason', '')}")
        if getattr(layer1, '_has_revisit', False):
            revisit_flags.append(f"GOAL_CHALLENGED: {getattr(layer1, '_revisit_reason', '')}")

        goal_challenged = any(
            f in layer3.revisit_flags
            for f in [RevisitFlag.GOAL_CHALLENGED.value, RevisitFlag.CONSTRAINT_REMOVED.value]
        ) or getattr(layer2, '_has_revisit', False)

        # Compute confidence based on layers + context
        confidence = self._compute_confidence(layer1, layer2, layer3, context_chars)

        # Determine if should proceed
        blockers = self._identify_blockers(layer1, layer2, layer3)
        should_proceed = (
            not goal_challenged
            and confidence >= 0.70
            and not blockers
        )

        return HierarchicalReasoningResult(
            task=task,
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            revisit_flags=revisit_flags,
            goal_is_challenged=goal_challenged,
            reasoning_complete=True,
            confidence=confidence,
            should_proceed=should_proceed,
            blockers=blockers,
            recommendations=self._build_recommendations(layer1, layer2, layer3, should_proceed),
        )

    # ---------------------------------------------------------------------------
    # Layer 1: MACRO reasoning
    # ---------------------------------------------------------------------------

    def _reason_layer1(
        self, task: str, original_request: str
    ) -> Layer1Macro:
        """Layer 1: Understand what we're trying to achieve at strategic level."""
        goal = task
        success_criteria = self._derive_success_criteria(task)
        measurable_outcomes = self._derive_measurable_outcomes(task, success_criteria)

        # Derive constraints from project context
        hard_constraints, soft_constraints = self._derive_constraints(task)

        # Identify deal-breakers
        deal_breakers = self._identify_deal_breakers(task)

        # Risk tolerance
        risk_tolerance = self._assess_risk_tolerance(task)

        # What is the motivation?
        motivation = self._derive_motivation(original_request, task)

        # Non-negotiables (from project rules)
        non_negotiables = self._derive_non_negotiables(task)

        return Layer1Macro(
            goal=goal,
            original_user_request=original_request,
            success_criteria=success_criteria,
            measurable_outcomes=measurable_outcomes,
            hard_constraints=hard_constraints,
            soft_constraints=soft_constraints,
            deal_breakers=deal_breakers,
            risk_tolerance=risk_tolerance,
            irreversible_changes=self._identify_irreversible_changes(task),
            motivation=motivation,
            non_negotiables=non_negotiables,
        )

    def _derive_success_criteria(self, task: str) -> list[str]:
        """Derive success criteria from task description."""
        criteria = []
        task_lower = task.lower()

        # Generic success criteria
        if "add" in task_lower or "implement" in task_lower:
            criteria.append("Feature is implemented and functional")
        if "fix" in task_lower or "bug" in task_lower:
            criteria.append("Issue is resolved without regression")
        if "refactor" in task_lower:
            criteria.append("Code is cleaner without changing behavior")
        if "add" in task_lower and "test" not in task_lower:
            criteria.append("Tests added/updated for new code")

        # Always-on success criteria for swarm-bot
        criteria.append("No new _old directories created")
        criteria.append("Smoke tests pass (Section 12 of CLAUDE.md)")
        criteria.append("Async/aiosqlite patterns respected")

        return criteria

    def _derive_measurable_outcomes(
        self, task: str, success_criteria: list[str]
    ) -> list[str]:
        """Derive objectively measurable outcomes."""
        outcomes = []
        task_lower = task.lower()

        if "performance" in task_lower or "speed" in task_lower:
            outcomes.append("Response time improves by measurable amount")
        if "concurrent" in task_lower or "parallel" in task_lower:
            outcomes.append("Handles N concurrent requests without error")
        if "database" in task_lower or "sqlite" in task_lower:
            outcomes.append("No 'database locked' errors under load")
        if "error" in task_lower or "fix" in task_lower:
            outcomes.append("Error no longer appears in same scenario")

        # Always: bot remains responsive
        outcomes.append("/start still responds within 5 seconds")

        return outcomes

    def _derive_constraints(self, task: str) -> tuple[list[str], list[str]]:
        """Derive hard and soft constraints from task and project rules."""
        hard = []
        soft = []

        task_lower = task.lower()

        # Project-mandated hard constraints
        hard.append("Must use async/aiosqlite patterns (never sync sqlite3)")
        hard.append("Cannot break existing Telegram handlers")
        hard.append("TELEGRAM_BOT_TOKEN and ALLOWED_USER_ID never logged")
        hard.append("No new threading or blocking I/O")

        # Task-specific soft constraints
        if "database" in task_lower or "sqlite" in task_lower:
            soft.append("aiosqlite connection pool where appropriate")
        if "telegram" in task_lower or "bot" in task_lower:
            soft.append("Messages chunked at 4000 chars before sending")
        if "api" in task_lower or "web" in task_lower:
            soft.append("Use parse_mode='HTML' not Markdown")

        return hard, soft

    def _identify_deal_breakers(self, task: str) -> list[str]:
        """Identify conditions that would make this task a failure."""
        deal_breakers = []
        task_lower = task.lower()

        if "auth" in task_lower or "permission" in task_lower:
            deal_breakers.append("Security regression — existing auth broken")
        if "database" in task_lower or "data" in task_lower:
            deal_breakers.append("Data loss or corruption")
        if "concurrent" in task_lower or "async" in task_lower:
            deal_breakers.append("Race conditions introduced")

        # Universal deal-breakers
        deal_breakers.append("Bot stops responding to /start")
        deal_breakers.append("Memory leak introduced")
        deal_breakers.append("New hardcoded secrets or credentials")

        return deal_breakers

    def _assess_risk_tolerance(self, task: str) -> str:
        """Assess appropriate risk tolerance for this task."""
        task_lower = task.lower()

        if any(k in task_lower for k in ["security", "auth", "permission", "credential"]):
            return "LOW"
        if any(k in task_lower for k in ["database", "migration", "schema", "data"]):
            return "LOW"
        if any(k in task_lower for k in ["refactor", "cleanup", "rename"]):
            return "MEDIUM"
        if any(k in task_lower for k in ["add feature", "new", "experiment"]):
            return "MEDIUM"
        if any(k in task_lower for k in ["test", "mock", "stub"]):
            return "HIGH"  # Tests are easily revertable

        return "MEDIUM"

    def _identify_irreversible_changes(self, task: str) -> list[str]:
        """Identify changes that cannot be easily undone."""
        irreversible = []
        task_lower = task.lower()

        if "database" in task_lower or "schema" in task_lower:
            irreversible.append("Database migrations — hard to roll back in production")
        if "api" in task_lower and ("break" in task_lower or "change" in task_lower):
            irreversible.append("API contract changes — clients may break")
        if "delete" in task_lower:
            irreversible.append("File deletion — version control can restore but it's a hassle")

        return irreversible

    def _derive_motivation(self, original_request: str, task: str) -> str:
        """Derive why this task matters."""
        if original_request != task:
            # User gave more context — extract the 'why'
            return f"Bashara's original request: {original_request[:200]}"
        return f"Task: {task}"

    def _derive_non_negotiables(self, task: str) -> list[str]:
        """Derive non-negotiable requirements from project rules."""
        return [
            "Never log user message content (privacy)",
            "All LLM calls go through llm_client.chat() — never direct provider calls",
            "No new global mutable state without good justification",
        ]

    # ---------------------------------------------------------------------------
    # Layer 2: MICRO reasoning
    # ---------------------------------------------------------------------------

    def _reason_layer2(
        self, layer1: Layer1Macro, task: str
    ) -> Layer2Micro:
        """Layer 2: Map Layer 1 goals to file-level components."""
        task_lower = task.lower()

        files_to_create = []
        files_to_modify = []
        files_to_delete = []

        new_interfaces = []
        modified_interfaces = []
        data_flow_changes = []
        new_dependencies = []
        removed_dependencies = []

        test_files_needed = []
        integration_points = []

        high_risk_files = []
        blast_radius = "LOCAL"

        # Task-type specific micro reasoning
        if "add" in task_lower and any(k in task_lower for k in ["database", "sqlite", "db"]):
            files_to_modify.extend(self._suggest_db_files(task))
            new_dependencies.append("aiosqlite (already in requirements)")
            test_files_needed.append("tests/test_db_*.py")

        if "handler" in task_lower or "command" in task_lower or "telegram" in task_lower:
            files_to_modify.extend(self._suggest_handler_files(task))
            integration_points.append("main.py router registration")

        if "refactor" in task_lower:
            # Refactors touch more files — wider blast radius
            blast_radius = "MODERATE"
            files_to_modify.extend(self._suggest_refactor_files(task))
            # Deleted code goes to _old for safety
            files_to_delete.append("[any deleted files go to _old/]")

        if "agent" in task_lower or "llm" in task_lower:
            files_to_modify.extend(self._suggest_agent_files(task))
            new_interfaces.append("[LLM-facing interface]")

        if "memory" in task_lower:
            files_to_modify.append("core/memory/memory_manager.py")
            integration_points.append("memory_manager facade")

        # Add new files go to core/ not handlers/
        if "new feature" in task_lower or "add" in task_lower:
            # Suggest a new core/ file
            files_to_create.append("core/[new_feature]/")

        # Risk assessment at file level
        for f in files_to_modify:
            if any(k in f for k in ["main.py", "llm_client", "auth", "security"]):
                high_risk_files.append(f)

        # Build mocking strategy
        mocking_strategy = "Mock file I/O and network calls for unit tests"

        return Layer2Micro(
            files_to_create=files_to_create,
            files_to_modify=files_to_modify,
            files_to_delete=files_to_delete,
            new_interfaces=new_interfaces,
            modified_interfaces=modified_interfaces,
            deleted_interfaces=[],
            data_flow_changes=data_flow_changes,
            new_dependencies=new_dependencies,
            removed_dependencies=removed_dependencies,
            test_files_needed=test_files_needed,
            integration_points=integration_points,
            mocking_strategy=mocking_strategy,
            high_risk_files=high_risk_files,
            blast_radius=blast_radius,
        )

    def _suggest_db_files(self, task: str) -> list[str]:
        """Suggest database-related files that might need modification."""
        files = []
        task_lower = task.lower()
        if "budget" in task_lower:
            files.append("swarms_bot/routing/budget_manager.py")
        if "memory" in task_lower:
            files.append("core/memory/memory_manager.py")
            files.append("core/memory/episodic_store.py")
        files.append("[relevant store file]")
        return files

    def _suggest_handler_files(self, task: str) -> list[str]:
        """Suggest handler files that might need modification."""
        files = ["handlers/shared.py"]  # Always check shared utilities
        task_lower = task.lower()
        if "ai" in task_lower or "run" in task_lower:
            files.append("handlers/ai.py")
        if "computer" in task_lower or "shell" in task_lower:
            files.append("handlers/computer.py")
        if "memory" in task_lower or "remember" in task_lower:
            files.append("handlers/memory_commands.py")
        files.append("[relevant handler file]")
        return files

    def _suggest_refactor_files(self, task: str) -> list[str]:
        """Suggest files relevant to a refactoring task."""
        task_lower = task.lower()
        files = []
        if "orchest" in task_lower:
            files.append("core/nexus_orchestrator.py")
        if "agent" in task_lower:
            files.append("core/agent_registry.py")
        if "memory" in task_lower:
            files.append("core/memory/memory_manager.py")
        if "router" in task_lower or "intent" in task_lower:
            files.append("core/intent_router.py")
        files.append("[files identified by grep or codebase analysis]")
        return files

    def _suggest_agent_files(self, task: str) -> list[str]:
        """Suggest agent/LLM-related files."""
        return [
            "agents.py",
            "llm_client.py",
            "[relevant agent file]",
        ]

    # ---------------------------------------------------------------------------
    # Layer 3: EXEC reasoning
    # ---------------------------------------------------------------------------

    def _reason_layer3(
        self,
        layer1: Layer1Macro,
        layer2: Layer2Micro,
        task: str,
    ) -> Layer3Exec:
        """Layer 3: Reason about specific code structure.

        CRITICAL: L3 output CANNOT change L1 goals. Any challenges to L1
        must be surfaced via revisit_flags, not by modifying Layer1 state.
        """
        task_lower = task.lower()
        function_signatures = []
        algorithm_choices = []
        code_skeletons = []
        edge_cases = []
        execution_insights = []
        execution_warnings = []
        micro_feedback = []

        # ---- Function signatures based on task type ----
        if "database" in task_lower or "sqlite" in task_lower:
            function_signatures.extend([
                "async def get_connection(pool: ConnectionPool) -> aiosqlite.Connection",
                "async def close_connection(conn: aiosqlite.Connection) -> None",
                "async def execute_with_retry(query: str, max_retries: int = 3) -> Any",
            ])
            edge_cases.extend([
                "SQLite LOCKED error under concurrent writes",
                "Connection leak if close_connection not called",
                "Database file not found on first run",
            ])
            execution_warnings.append(
                "Use aiosqlite ConnectionPool — never bare connect/disconnect in async context"
            )

        if "handler" in task_lower or "telegram" in task_lower:
            function_signatures.extend([
                "async def handle_{command}(message: Message) -> None: ...",
                "async def validate_input(text: str) -> bool: ...",
                "# Parse mode: parse_mode='HTML' — escape < > & in user text",
            ])
            edge_cases.extend([
                "Message too long (>4000 chars) — need split_and_send",
                "User not in ALLOWED_USER_ID — reject silently",
                "parse_mode HTML error on special characters",
            ])

        if "agent" in task_lower or "llm" in task_lower:
            function_signatures.extend([
                "async def call_agent(agent_key: str, prompt: str) -> str: ...",
                "# Model string: provider/model format (e.g., 'opencode-go/deepseek-v4-pro')",
            ])
            edge_cases.extend([
                "Rate limit error — fall back to next provider in chain",
                "Empty response from LLM — return error message",
                "Tool call parsing failure — log and graceful degrade",
            ])

        # ---- SoT-style code skeletons (from core/sot_engine.py integration) ----
        # Layer 3 produces skeletons that Layer 2 maps to files
        if layer2.files_to_create:
            for f in layer2.files_to_create:
                if f.endswith("/") or "core/" in f:
                    code_skeletons.append(
                        f"# Generate skeleton for {f}\n"
                        "# Use SoTEngine.generate_component_skeleton() for guidance"
                    )

        # ---- Algorithm choices ----
        if "concurrent" in task_lower or "parallel" in task_lower:
            algorithm_choices.extend([
                "asyncio.gather() for parallel async operations",
                "asyncio.Semaphore for concurrency limiting",
                "Connection pool with bounded size",
            ])

        if "cache" in task_lower or "memo" in task_lower:
            algorithm_choices.extend([
                "functools.lru_cache for function-level memoization",
                "TTL cache for time-sensitive data",
            ])

        # ---- L3 observations that CANNOT change L1 ----
        # These are insights L3 noticed but must flag, not act on
        goal_keywords = set(layer1.goal.lower().split())
        for keyword in goal_keywords:
            if keyword in task_lower and keyword not in goal_keywords:
                # L3 noticed the task contains something not in the goal
                insight = (
                    f"L3 observed: task mentions '{keyword}' "
                    f"but goal doesn't explicitly include it. "
                    f"Is this scope creep? Flag for L1 review."
                )
                execution_insights.append(insight)
                micro_feedback.append(
                    f"[TO-L2] '{keyword}' in task but not in goal — confirm scope"
                )

        # ---- L3 cannot challenge L1 directly ----
        # If L3 discovers the goal is wrong, it raises a flag:
        if "impossible" in task_lower or "cannot" in task_lower:
            self._raise_revisit_flag(
                RevisitFlag.GOAL_CHALLENGED,
                "L3 execution analysis suggests goal may be impossible with current architecture",
                execution_warnings,
            )

        return Layer3Exec(
            function_signatures=function_signatures,
            algorithm_choices=algorithm_choices,
            data_structures=[],
            code_blocks_needed=[],  # Filled by SoT engine
            code_skeletons=code_skeletons,
            edge_cases_identified=edge_cases,
            error_handling_strategy="try/except with specific exceptions, log and degrade gracefully",
            fallback_strategy="Return informative error, never crash silently",
            execution_insights=execution_insights,
            execution_warnings=execution_warnings,
            revisit_flags=[],
            micro_feedback_to_layer2=micro_feedback,
        )

    def _raise_revisit_flag(
        self,
        flag: RevisitFlag,
        detail: str,
        warnings_list: list[str],
    ) -> None:
        """Helper to raise revisit flags in L3."""
        warnings_list.append(f"[REVISIT-{flag.value}] {detail}")

    # ---------------------------------------------------------------------------
    # Confidence and blockers
    # ---------------------------------------------------------------------------

    def _compute_confidence(
        self,
        layer1: Layer1Macro,
        layer2: Layer2Micro,
        layer3: Layer3Exec,
        context_chars: int,
    ) -> float:
        """Compute overall confidence in the reasoning."""
        # Base confidence from layers
        l1_confidence = 0.9 if layer1.success_criteria else 0.5
        l2_confidence = 0.9 if layer2.files_to_modify else 0.5
        l3_confidence = 0.9 if layer3.function_signatures else 0.5

        # Revisit flags reduce confidence
        revisit_penalty = 0.1 * len(layer3.revisit_flags)

        # Context pressure reduces confidence
        context_penalty = 0.0
        if context_chars > 100_000:
            context_penalty = 0.15
        elif context_chars > 80_000:
            context_penalty = 0.1

        # High-risk tasks reduce confidence
        risk_penalty = 0.0
        if layer1.risk_tolerance == "LOW":
            risk_penalty = 0.1

        confidence = (
            l1_confidence * 0.3
            + l2_confidence * 0.35
            + l3_confidence * 0.35
            - revisit_penalty
            - context_penalty
            - risk_penalty
        )

        return max(0.0, min(1.0, confidence))

    def _identify_blockers(
        self,
        layer1: Layer1Macro,
        layer2: Layer2Micro,
        layer3: Layer3Exec,
    ) -> list[str]:
        """Identify blockers that prevent proceeding."""
        blockers = []

        # L1 blockers
        if layer1.deal_breakers and not layer1.success_criteria:
            blockers.append("No success criteria defined — can't verify completion")

        # L2 blockers
        if not layer2.files_to_modify and not layer2.files_to_create:
            blockers.append("No files identified for modification — is this task real?")
        if len(layer2.files_to_modify) > 15:
            blockers.append("Scope too large — >15 files to modify. Break into smaller tasks.")

        # L3 blockers
        if not layer3.function_signatures and not layer3.code_skeletons:
            blockers.append("No execution plan from L3 — reasoning incomplete")

        return blockers

    def _build_recommendations(
        self,
        layer1: Layer1Macro,
        layer2: Layer2Micro,
        layer3: Layer3Exec,
        should_proceed: bool,
    ) -> list[str]:
        """Build actionable recommendations."""
        recs = []

        if not should_proceed:
            recs.append("Fix blockers before proceeding")
            return recs

        if layer1.risk_tolerance == "LOW":
            recs.append("LOW risk tolerance — add integration tests before deploying")

        if layer2.blast_radius == "WIDE":
            recs.append("WIDE blast radius — consider feature flag for gradual rollout")

        if layer3.revisit_flags:
            recs.append(f"L3 raised {len(layer3.revisit_flags)} revisit flags — review before L1/L2 lock")

        if layer3.execution_warnings:
            recs.append(f"L3 execution warnings: {len(layer3.execution_warnings)} — address in implementation")

        if not recs:
            recs.append("Ready to implement — proceed with Layer 2 file mapping")

        return recs

    # ---------------------------------------------------------------------------
    # Formatting
    # ---------------------------------------------------------------------------

    def format_result(self, result: HierarchicalReasoningResult) -> str:
        """Format reasoning result as human-readable string for Telegram."""
        lines = [
            f"🧠 Hierarchical Reasoning: {result.task}",
            "",
        ]

        # L1 summary
        lines.append(f"📌 LAYER 1 (MACRO) — Goal: {result.layer1.goal[:60]}")
        if result.layer1.motivation:
            lines.append(f"   Motivation: {result.layer1.motivation[:80]}")
        lines.append(f"   Risk: {result.layer1.risk_tolerance} | Deal-breakers: {len(result.layer1.deal_breakers)}")
        lines.append(f"   Success criteria: {', '.join(result.layer1.success_criteria[:3])}")

        # L2 summary
        lines.append("")
        lines.append(f"📁 LAYER 2 (MICRO) — {result.layer2.blast_radius} blast radius")
        if result.layer2.files_to_create:
            lines.append(f"   Create: {', '.join(result.layer2.files_to_create[:3])}")
        if result.layer2.files_to_modify:
            lines.append(f"   Modify: {', '.join(result.layer2.files_to_modify[:4])}")
        if result.layer2.integration_points:
            lines.append(f"   Integration: {', '.join(result.layer2.integration_points[:2])}")

        # L3 summary
        lines.append("")
        lines.append("⚙️ LAYER 3 (EXEC)")
        if result.layer3.function_signatures:
            for sig in result.layer3.function_signatures[:2]:
                lines.append(f"   {sig[:70]}")
        if result.layer3.edge_cases_identified:
            lines.append(f"   Edge cases: {len(result.layer3.edge_cases_identified)} identified")
        if result.layer3.revisit_flags:
            lines.append(f"   ⚠️ Revisit flags: {len(result.layer3.revisit_flags)}")

        # Status
        lines.append("")
        badge = "✅" if result.should_proceed else "🚫"
        lines.append(
            f"{badge} Confidence: {result.confidence:.0%} | "
            f"Proceed: {result.should_proceed}"
        )

        if result.blockers:
            lines.append("")
            lines.append("🚫 Blockers:")
            for b in result.blockers:
                lines.append(f"  • {b}")

        if result.recommendations:
            lines.append("")
            for r in result.recommendations:
                lines.append(f"  → {r}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience singleton
# ---------------------------------------------------------------------------

_reasoner: HierarchicalReasoner | None = None


def get_hierarchical_reasoner(
    project_root: str | None = None,
) -> HierarchicalReasoner:
    """Return global HierarchicalReasoner singleton."""
    global _reasoner
    if _reasoner is None:
        _reasoner = HierarchicalReasoner(project_root)
    return _reasoner
