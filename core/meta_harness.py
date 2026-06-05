"""
Meta-Harness: End-to-End Optimization of Model Harnesses

Based on arXiv:2603.28052 - "Meta-Harness: End-to-End Optimization of Model Harnesses"
by Lee et al., 2026

This module implements:
- HarnessFS: Filesystem-based storage for harness candidates (code, scores, traces)
- HarnessCandidate: Representation of a harness candidate with metadata
- MetaHarnessOptimizer: Outer-loop harness optimization with agentic proposer
- Integration with RecursiveMAS for inner-loop agent collaboration

Key concepts from the paper:
1. Harness = code that determines what to store, retrieve, and present to LLM
2. Agentic proposer with filesystem access to all prior candidates
3. Full history (code + scores + traces) enables causal diagnosis
4. Advantages over text optimizers: richer feedback, code-space search

Integration with RecursiveMAS:
- Meta-Harness optimizes the HARNESS (outer loop)
- RecursiveMAS provides the INNER reasoning mechanism
- Together: optimize harness for better multi-agent collaboration
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.recursive_mas import RecursiveMASOrchestrator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class HarnessDomain(Enum):
    """Domains where Meta-Harness has been evaluated."""

    TEXT_CLASSIFICATION = "text_classification"
    MATH_REASONING = "math_reasoning"
    AGENTIC_CODING = "agentic_coding"
    RAG = "rag"
    CUSTOM = "custom"


@dataclass
class ExecutionTrace:
    """Execution trace from harness evaluation."""

    prompt: str
    model_output: str
    tool_calls: list[dict] = field(default_factory=list)
    state_updates: list[dict] = field(default_factory=list)
    intermediate_steps: list[str] = field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0


@dataclass
class HarnessEvaluation:
    """Evaluation result for a harness candidate."""

    task_instance: str
    reward: float
    cost: float = 0.0
    latency_ms: float = 0.0
    trace: ExecutionTrace | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HarnessCandidate:
    """A harness candidate being optimized by Meta-Harness."""

    candidate_id: str
    source_code: str
    description: str = ""
    domain: HarnessDomain = HarnessDomain.CUSTOM
    evaluations: list[HarnessEvaluation] = field(default_factory=list)
    parent_ids: list[str] = field(default_factory=list)  # For evolutionary tracking
    created_at: float = field(default_factory=time.time)
    proposer_reasoning: str = ""  # What the proposer thought when creating
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mean_reward(self) -> float:
        """Mean reward across evaluations."""
        if not self.evaluations:
            return 0.0
        return sum(e.reward for e in self.evaluations) / len(self.evaluations)

    @property
    def mean_cost(self) -> float:
        """Mean cost across evaluations."""
        if not self.evaluations:
            return 0.0
        return sum(e.cost for e in self.evaluations) / len(self.evaluations)

    @property
    def pareto_dominated(self) -> bool:
        """Whether this candidate is Pareto dominated by others."""
        return False  # Calculated at population level


@dataclass
class ParetoFrontier:
    """Pareto frontier of non-dominated harness candidates."""

    candidates: list[HarnessCandidate]

    def is_dominated(self, candidate: HarnessCandidate) -> bool:
        """Check if a candidate is dominated by any in frontier."""
        for c in self.candidates:
            if c == candidate:
                continue
            # c dominates candidate if c is >= in all metrics and > in at least one
            c_ge = c.mean_reward >= candidate.mean_reward and c.mean_cost <= candidate.mean_cost
            c_gt = c.mean_reward > candidate.mean_reward or c.mean_cost < candidate.mean_cost
            if c_ge and c_gt:
                return True
        return False


# ---------------------------------------------------------------------------
# Assembler (A) and Verifier (V)
# ---------------------------------------------------------------------------


class HarnessAssembler:
    """
    Assembler for Meta-Harness — composes harness code from proposer output.

    From the paper, the Assembler takes the agentic proposer's output and
    produces a well-formed, validated harness module. Key responsibilities:
    1. Format validation — ensure proposed code is syntactically correct Python
    2. Import synthesis — inject necessary imports (json, time, re, etc.)
    3. Structure enforcement — enforce the harness interface (class with
       retrieve(), update(), assemble() methods)
    4. Safety guardrails — strip dangerous operations, validate eval criteria
    5. Multipart composition — for multi-call harnesses (e.g., Draft-Verification),
       assemble the full pipeline from parts

    Integration with swarm-bot:
    - Uses existing agent infrastructure to validate harness syntax
    - Ensures harnesses are safe to execute in the agent environment
    """

    def __init__(self, llm_call: Callable[[str, str, str], str] | None = None):
        self.llm_call = llm_call

    def assemble(
        self,
        raw_proposal: str,
        domain: HarnessDomain,
        context: str = "",
    ) -> HarnessCandidate:
        """
        Assemble a well-formed harness from a raw proposal.

        Args:
            raw_proposal: The raw text/code proposed by AgenticProposer
            domain: The harness domain
            context: Optional context about the task

        Returns:
            A validated HarnessCandidate ready for evaluation
        """
        candidate_id = f"harness_{uuid.uuid4().hex[:8]}"

        # Extract code block if present (proposer often returns markdown code)
        import re

        code_match = re.search(r"```(?:python)?\n(.*?)```", raw_proposal, re.DOTALL)
        if code_match:
            source_code = code_match.group(1).strip()
        else:
            # Try to extract just the code without markdown
            lines = raw_proposal.strip().split("\n")
            code_lines = []
            in_code = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code = not in_code
                    continue
                if in_code or (not line.startswith("#") and not line.startswith("//")):
                    if any(kw in line for kw in ["def ", "class ", "import ", "#", "="]):
                        code_lines.append(line)
            source_code = "\n".join(code_lines) if code_lines else raw_proposal.strip()

        # Fallback: if no code found, create a valid minimal harness
        if not source_code or len(source_code) < 10:
            source_code = self._default_harness(domain)

        # Apply safety guardrails
        source_code = self._apply_guardrails(source_code)

        # Ensure harness has required interface methods
        source_code = self._ensure_interface(source_code, domain)

        # Generate description from code
        description = self._generate_description(source_code, domain, context)

        return HarnessCandidate(
            candidate_id=candidate_id,
            source_code=source_code,
            description=description,
            domain=domain,
            metadata={"assembler": "HarnessAssembler", "raw_proposal_len": len(raw_proposal)},
        )

    def _default_harness(self, domain: HarnessDomain) -> str:
        """Generate a minimal valid harness for each domain."""
        if domain == HarnessDomain.TEXT_CLASSIFICATION:
            return '''"""Text classification harness discovered by Meta-Harness."""

import json
from typing import Any

class Harness:
    def __init__(self):
        self.memory = deque(maxlen=1000)

    def retrieve(self, query: str) -> list[dict]:
        """Retrieve relevant examples from memory."""
        if not self.memory:
            return []
        # Simple relevance: return all if memory is small
        return self.memory[-5:]

    def update(self, example: dict) -> None:
        """Update memory with a new example."""
        self.memory.append(example)

    def assemble(self, query: str, retrieved: list[dict]) -> str:
        """Assemble the final prompt."""
        if not retrieved:
            return f"Query: {query}\\nLabel:"
        context = "\\n".join(f"Input: {e.get('input', '')} Output: {e.get('label', '')}" for e in retrieved)
        return f"Given examples:\\n{context}\\n\\nQuery: {query}\\nLabel:"
'''
        elif domain == HarnessDomain.MATH_REASONING:
            return '''"""Math reasoning harness discovered by Meta-Harness."""

import json
from typing import Any

class Harness:
    def __init__(self):
        self.memory = deque(maxlen=1000)

    def retrieve(self, query: str) -> list[dict]:
        """Retrieve relevant math problems."""
        return self.memory[-3:] if self.memory else []

    def update(self, example: dict) -> None:
        """Update memory with a new problem."""
        self.memory.append(example)

    def assemble(self, query: str, retrieved: list[dict]) -> str:
        """Assemble prompt with retrieved examples."""
        if not retrieved:
            return f"Problem: {query}\\nSolution:"
        examples = "\\n".join(f"Problem: {e.get('input','')} Solution: {e.get('output','')}" for e in retrieved)
        return f"Examples:\\n{examples}\\n\\nProblem: {query}\\nSolution:"
'''
        elif domain == HarnessDomain.AGENTIC_CODING:
            return '''"""Agentic coding harness discovered by Meta-Harness."""

import json
from typing import Any

class Harness:
    def __init__(self):
        self.history = deque(maxlen=500)

    def retrieve(self, task: str) -> list[dict]:
        """Retrieve similar completed tasks."""
        return self.history[-3:] if self.history else []

    def update(self, result: dict) -> None:
        """Record task result."""
        self.history.append(result)

    def assemble(self, task: str, retrieved: list[dict]) -> str:
        """Assemble agentic coding prompt."""
        if not retrieved:
            return f"Task: {task}\\nStart:"
        history = "\\n".join(f"Task: {r.get('task','')} Result: {r.get('result','')}" for r in retrieved)
        return f"Past successful approaches:\\n{history}\\n\\nCurrent task: {task}\\nStart:"
'''
        else:
            return f'''"""Generic harness for {domain.value}."""

import json

class Harness:
    def __init__(self):
        self.state = {{}}

    def retrieve(self, query: str) -> list[dict]:
        return list(self.state.values())[-5:]

    def update(self, item: dict) -> None:
        self.state[item.get("id", len(self.state))] = item

    def assemble(_task: str, _retrieved: list[dict]) -> str:
        parts = ["Task: ", str(_task), "\\nContext: ", json.dumps(_retrieved)]
        return "".join(parts)
'''

    def _apply_guardrails(self, source_code: str) -> str:
        """Apply safety guardrails to harness code."""
        import re

        # Remove dangerous operations
        dangerous = [
            r"import\s+os\s*$",
            r"import\s+subprocess",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__\s*\(",
            r"open\s*\([^)]*['\"][wa]['\"]",
            r"rm\s+-rf",
            r"delete\s+.*file",
            r"\.remove\s*\(",
            r"\.unlink\s*\(",
        ]
        for pattern in dangerous:
            source_code = re.sub(pattern, "# REMOVED_BY_GUARDRAIL", source_code)

        # Ensure class name is Harness
        if "class " in source_code and "class Harness" not in source_code:
            source_code = re.sub(r"class\s+\w+", "class Harness", source_code)

        return source_code

    def _ensure_interface(self, source_code: str, domain: HarnessDomain) -> str:
        """Ensure the harness has the required interface methods."""
        required_methods = ["retrieve", "update", "assemble"]

        # Check if all required methods are present
        for method in required_methods:
            if f"def {method}" not in source_code:
                # Add the missing method
                if method == "retrieve":
                    source_code += "\n    def retrieve(self, query: str) -> list[dict]:\n        return []\n"
                elif method == "update":
                    source_code += "\n    def update(self, item: dict) -> None:\n        pass\n"
                elif method == "assemble":
                    source_code += "\n    def assemble(self, query: str, retrieved: list[dict]) -> str:\n        return f'Query: {{query}}'\n"

        return source_code

    def _generate_description(
        self, source_code: str, domain: HarnessDomain, context: str
    ) -> str:
        """Generate a description from the harness code."""
        import re

        # Extract first docstring
        docstring_match = re.search(r'"""(.*?)"""', source_code, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()[:200]

        # Fallback: summarize from method names
        methods = re.findall(r"def\s+(\w+)", source_code)
        return f"Harness with methods: {', '.join(methods)} for {domain.value}"

    def compose_multipart(
        self,
        parts: list[dict],
        domain: HarnessDomain,
    ) -> HarnessCandidate:
        """
        Compose a multi-stage harness from parts.

        From paper: harnesses like Draft-Verification use multiple LLM calls
        where the second call's retrieval depends on the first call's output.
        This method handles composing such multi-part pipelines.

        Args:
            parts: List of part specifications, each containing:
                   - stage_name: e.g., "draft", "verification"
                   - prompt_template: str with placeholders
                   - retrieval_config: how to get context for this stage
            domain: The harness domain

        Returns:
            A composed HarnessCandidate
        """
        candidate_id = f"harness_{uuid.uuid4().hex[:8]}"
        description = f"Multi-stage harness with {len(parts)} stages"

        # Build the composed harness code
        lines = ['"""Multi-stage harness from Meta-Harness Assembler."""', "", "from typing import Any, list", "", "class Harness:", "    def __init__(self):", "        self.stages = []", "        self.memory = deque(maxlen=1000)"]

        for i, part in enumerate(parts):
            stage_name = part.get("stage_name", f"stage_{i}")
            lines.append(f"        self.stages.append({stage_name!r})")

        lines.append("")
        lines.append("    def execute(self, query: str) -> str:")
        for i, part in enumerate(parts):
            stage_name = part.get("stage_name", f"stage_{i}")
            lines.append(f"        # Stage {i+1}: {stage_name}")

        lines.append("        return result")

        source_code = "\n".join(lines)

        return HarnessCandidate(
            candidate_id=candidate_id,
            source_code=source_code,
            description=description,
            domain=domain,
            metadata={"assembler": "HarnessAssembler", "multipart": True, "parts": parts},
        )


class HarnessVerifier:
    """
    Verifier for Meta-Harness — evaluates harness on held-out tasks.

    From the paper: The verifier runs training-signal evaluations on held-out
    task instances to determine which candidates to keep. Key responsibilities:
    1. Lightweight validation before expensive benchmarks
    2. Pass/fail on syntax and interface requirements
    3. Score aggregation across multiple task instances
    4. Domain-specific evaluation criteria

    Integration with swarm-bot:
    - Works with existing test/evaluation infrastructure
    - Can use RecursiveMAS for complex evaluation scenarios
    """

    def __init__(self, llm_call: Callable[[str, str, str], str] | None = None):
        self.llm_call = llm_call

    def validate_syntax(self, source_code: str) -> tuple[bool, str]:
        """
        Check if harness code is syntactically valid Python.

        Returns:
            (is_valid, error_message)
        """
        try:
            import ast

            ast.parse(source_code)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"

    def validate_interface(self, source_code: str) -> tuple[bool, str]:
        """
        Verify harness has required interface methods.

        Required methods: retrieve(query: str), update(item: dict), assemble(query: str, retrieved: list)

        Returns:
            (is_valid, error_message)
        """
        import re

        required = ["retrieve", "update", "assemble"]
        found = set(re.findall(r"def\s+(\w+)", source_code))

        missing = [m for m in required if m not in found]
        if missing:
            return False, f"Missing required methods: {', '.join(missing)}"

        return True, ""

    def validate_execution(
        self,
        source_code: str,
        test_cases: list[dict],
    ) -> tuple[bool, list[dict]]:
        """
        Execute harness on test cases and verify correct behavior.

        Args:
            source_code: The harness code to test
            test_cases: List of {input, expected_behavior} dicts

        Returns:
            (all_passed, results) where results has per-case info
        """
        import sys

        # Create a namespace to execute harness
        namespace = {"__name__": "__harness_test__"}
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        results = []

        try:
            # Compile the harness code
            compiled = compile(source_code, "<harness>", "exec")
            exec(compiled, namespace)

            # Find the Harness class
            if "Harness" not in namespace:
                return False, [{"error": "No 'Harness' class found"}]

            harness_class = namespace["Harness"]
            harness = harness_class()

            # Run test cases
            for tc in test_cases:
                result = {"input": tc.get("input"), "passed": False, "output": None}
                try:
                    query = tc.get("input", "")
                    retrieved = harness.retrieve(query)
                    output = harness.assemble(query, retrieved)
                    result["output"] = output
                    result["passed"] = True
                except Exception as e:
                    result["error"] = str(e)

                results.append(result)

        except Exception as e:
            return False, [{"error": f"Execution failed: {e}"}]
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        all_passed = all(r.get("passed", False) for r in results)
        return all_passed, results

    def evaluate(
        self,
        candidate: HarnessCandidate,
        eval_tasks: list[dict],
        metric_fn: Callable[[dict], float] | None = None,
    ) -> list[HarnessEvaluation]:
        """
        Full evaluation of a harness candidate on a set of tasks.

        From paper: Evaluation runs the harness on held-out task instances
        and produces reward signals for the outer-loop optimizer.

        Args:
            candidate: The harness candidate to evaluate
            eval_tasks: List of task instances to evaluate on
            metric_fn: Optional custom metric function (task_result) -> float

        Returns:
            List of HarnessEvaluation results
        """
        evaluations = []

        for task in eval_tasks:
            eval_result = self._evaluate_single(candidate, task, metric_fn)
            evaluations.append(eval_result)

        return evaluations

    def _evaluate_single(
        self,
        candidate: HarnessCandidate,
        task: dict,
        metric_fn: Callable[[dict], float] | None = None,
    ) -> HarnessEvaluation:
        """Evaluate a single task instance."""
        import time

        trace = ExecutionTrace(prompt=task.get("input", ""), model_output="")
        start = time.perf_counter()

        try:
            # Execute harness on task
            exec_namespace = {}
            exec(compile(candidate.source_code, "<harness>", "exec"), exec_namespace)

            if "Harness" not in exec_namespace:
                raise ValueError("No Harness class in candidate code")

            harness = exec_namespace["Harness"]()
            query = task.get("input", "")
            retrieved = harness.retrieve(query)
            output = harness.assemble(query, retrieved)

            trace.model_output = output
            trace.latency_ms = (time.perf_counter() - start) * 1000

            # Compute reward
            if metric_fn:
                reward = metric_fn({"task": task, "output": output, "retrieved": retrieved})
            else:
                # Default: reward = 1.0 if output is non-empty
                reward = 1.0 if output and len(output) > 0 else 0.0

        except Exception as exc:
            logger.error("Harness evaluation failed: %s", exc)
            reward = 0.0
            trace.model_output = f"Error: {exc}"

        return HarnessEvaluation(
            task_instance=task.get("input", task.get("id", "unknown")),
            reward=reward,
            cost=trace.tokens_used,
            latency_ms=trace.latency_ms,
            trace=trace,
            metadata={"domain": candidate.domain.value},
        )


# ---------------------------------------------------------------------------
# Harness Filesystem (D)
# ---------------------------------------------------------------------------


class HarnessFS:
    """
    Filesystem-based storage for harness candidates.

    Stores for each candidate:
    - source code
    - evaluation scores
    - execution traces

    The proposer queries via grep/cat rather than ingesting as a single prompt.
    In practice, proposer reads median 82 files per iteration.
    """

    def __init__(self, base_dir: str | Path = "/tmp/meta_harness_fs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, HarnessCandidate] = {}
        self._pareto_frontier: list[HarnessCandidate] = []

    def _candidate_dir(self, candidate_id: str) -> Path:
        """Get directory for a candidate."""
        return self.base_dir / candidate_id

    def _ensure_candidate_dir(self, candidate_id: str) -> Path:
        """Ensure candidate directory exists."""
        d = self._candidate_dir(candidate_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def store(self, candidate: HarnessCandidate) -> None:
        """Store a harness candidate with its evaluations and traces."""
        cdir = self._ensure_candidate_dir(candidate.candidate_id)

        # Store source code
        (cdir / "code.py").write_text(candidate.source_code)

        # Store metadata
        metadata = {
            "candidate_id": candidate.candidate_id,
            "description": candidate.description,
            "domain": candidate.domain.value,
            "parent_ids": candidate.parent_ids,
            "created_at": candidate.created_at,
            "proposer_reasoning": candidate.proposer_reasoning,
            "metadata": candidate.metadata,
        }
        (cdir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Store evaluations
        eval_data = []
        for eval_result in candidate.evaluations:
            eval_entry = {
                "task_instance": eval_result.task_instance,
                "reward": eval_result.reward,
                "cost": eval_result.cost,
                "latency_ms": eval_result.latency_ms,
                "tokens_used": eval_result.trace.tokens_used if eval_result.trace else 0,
                "metadata": eval_result.metadata,
            }
            if eval_result.trace:
                eval_entry["trace"] = {
                    "prompt": eval_result.trace.prompt,
                    "model_output": eval_result.trace.model_output,
                    "tool_calls": eval_result.trace.tool_calls,
                    "state_updates": eval_result.trace.state_updates,
                    "intermediate_steps": eval_result.trace.intermediate_steps,
                }
            eval_data.append(eval_entry)
        (cdir / "evaluations.jsonl").write_text(
            "\n".join(json.dumps(e) for e in eval_data)
        )

        # Update index
        self._index[candidate.candidate_id] = candidate
        self._update_pareto_frontier()

    def get(self, candidate_id: str) -> HarnessCandidate | None:
        """Retrieve a candidate by ID."""
        return self._index.get(candidate_id)

    def get_all(self) -> list[HarnessCandidate]:
        """Get all candidates."""
        return list(self._index.values())

    def query_by_keyword(
        self, keyword: str, field: str = "description"
    ) -> list[HarnessCandidate]:
        """Query candidates by keyword in description or code."""
        results = []
        for c in self._index.values():
            if (field == "description" and keyword.lower() in c.description.lower()) or \
               (field == "code" and keyword.lower() in c.source_code.lower()):
                results.append(c)
        return results

    def query_by_reward_range(
        self, min_reward: float, max_reward: float
    ) -> list[HarnessCandidate]:
        """Query candidates by reward range."""
        return [
            c
            for c in self._index.values()
            if min_reward <= c.mean_reward <= max_reward
        ]

    def query_recent(self, n: int = 10) -> list[HarnessCandidate]:
        """Get n most recent candidates."""
        sorted_candidates = sorted(
            self._index.values(), key=lambda c: c.created_at, reverse=True
        )
        return sorted_candidates[:n]

    def query_by_parents(self, parent_ids: list[str]) -> list[HarnessCandidate]:
        """Get candidates that have any of the given parent IDs."""
        return [c for c in self._index.values() if any(pid in c.parent_ids for pid in parent_ids)]

    def get_file_content(self, candidate_id: str, filename: str) -> str | None:
        """Get raw file content for a candidate (how proposer accesses traces)."""
        cdir = self._candidate_dir(candidate_id)
        filepath = cdir / filename
        if filepath.exists():
            return filepath.read_text()
        return None

    def _update_pareto_frontier(self) -> None:
        """Update Pareto frontier with current candidates."""
        non_dominated = []
        candidates = list(self._index.values())

        for candidate in candidates:
            is_dominated = False
            for other in candidates:
                if other == candidate:
                    continue
                # other dominates candidate if better in all metrics
                other_ge = (
                    other.mean_reward >= candidate.mean_reward
                    and other.mean_cost <= candidate.mean_cost
                )
                other_strict = (
                    other.mean_reward > candidate.mean_reward
                    or other.mean_cost < candidate.mean_cost
                )
                if other_ge and other_strict:
                    is_dominated = True
                    break
            if not is_dominated:
                non_dominated.append(candidate)

        self._pareto_frontier = non_dominated

    def get_pareto_frontier(self) -> ParetoFrontier:
        """Get current Pareto frontier."""
        return ParetoFrontier(candidates=self._pareto_frontier)

    def get_stats(self) -> dict[str, Any]:
        """Get filesystem statistics."""
        return {
            "total_candidates": len(self._index),
            "pareto_frontier_size": len(self._pareto_frontier),
            "base_dir": str(self.base_dir),
            "domains": list(set(c.domain.value for c in self._index.values())),
        }


# ---------------------------------------------------------------------------
# Agentic Proposer (P)
# ---------------------------------------------------------------------------


class AgenticProposer:
    """
    Agentic proposer for Meta-Harness.

    Key properties from the paper:
    1. Accesses source code, scores, and execution traces via filesystem
    2. Uses grep/cat to query rather than ingesting all as single prompt
    3. Reads median 82 files per iteration
    4. Can inspect 20+ prior candidates per step
    5. Forms causal hypotheses about failures (not just scalar scores)

    Integration with swarm-bot:
    - Uses existing agent infrastructure for the proposer
    - Can use RecursiveMAS for inner reasoning about harness improvements
    """

    def __init__(
        self,
        llm_call: Callable[[str, str, str], str],
        harness_fs: HarnessFS,
        recursive_mas: RecursiveMASOrchestrator | None = None,
    ):
        self.llm_call = llm_call
        self.harness_fs = harness_fs
        self.recursive_mas = recursive_mas

    async def propose(
        self,
        task_description: str,
        domain: HarnessDomain,
        num_proposals: int = 1,
        inspection_depth: str = "full",
    ) -> list[HarnessCandidate]:
        """
        Propose new harness candidates by inspecting prior experience.

        Args:
            task_description: Description of the task/harness domain
            domain: The harness domain
            num_proposals: Number of candidates to propose
            inspection_depth: "full", "scores_only", or "scores_plus_summary"

        Returns:
            List of proposed HarnessCandidate objects
        """
        candidates = []

        # Gather context based on inspection depth
        if inspection_depth == "full":
            context = await self._gather_full_context(domain)
        elif inspection_depth == "scores_only":
            context = self._gather_scores_only()
        else:  # scores_plus_summary
            context = await self._gather_scores_plus_summary()

        # Use agent to propose
        prompt = self._build_proposal_prompt(
            task_description, domain, context, num_proposals
        )

        system_prompt = self._get_proposer_system_prompt()

        try:
            response = await self.llm_call(
                "minimax-coding-plan/MiniMax-M3", system_prompt, prompt
            )

            # Parse response into candidates
            candidates = self._parse_proposals(response, domain, context)

        except Exception as exc:
            logger.error("Proposer failed: %s", exc)

        return candidates

    async def _gather_full_context(self, domain: HarnessDomain) -> str:
        """Gather full context including execution traces (key advantage)."""
        frontier = self.harness_fs.get_pareto_frontier()
        recent = self.harness_fs.query_recent(n=20)

        context_parts = ["=== PARETO FRONTIER (Best Candidates) ===\n"]

        for c in frontier.candidates[:5]:
            context_parts.append(f"\n--- Candidate: {c.candidate_id} ---")
            context_parts.append(f"Reward: {c.mean_reward:.4f}, Cost: {c.mean_cost:.4f}")
            context_parts.append(f"Description: {c.description}")

            # Get execution traces
            for eval_result in c.evaluations[:2]:  # Top 2 evals
                if eval_result.trace:
                    context_parts.append(f"\nTrace for task: {eval_result.task_instance}")
                    context_parts.append(f"Prompt:\n{eval_result.trace.prompt[:500]}")
                    context_parts.append(
                        f"Output:\n{eval_result.trace.model_output[:500]}"
                    )
                    if eval_result.trace.tool_calls:
                        context_parts.append(
                            f"Tool calls: {len(eval_result.trace.tool_calls)} calls"
                        )

        context_parts.append("\n\n=== RECENT CANDIDATES ===\n")
        for c in recent[:10]:
            context_parts.append(
                f"\n--- Candidate: {c.candidate_id} ---"
            )
            context_parts.append(
                f"Reward: {c.mean_reward:.4f}, Cost: {c.mean_cost:.4f}"
            )
            context_parts.append(f"Description: {c.description[:200]}")

        return "\n".join(context_parts)

    def _gather_scores_only(self) -> str:
        """Gather only scores ( ablation)."""
        frontier = self.harness_fs.get_pareto_frontier()
        recent = self.harness_fs.query_recent(n=20)

        lines = ["=== SCORES ===\n"]
        for c in frontier.candidates + recent:
            lines.append(f"{c.candidate_id}: reward={c.mean_reward:.4f}, cost={c.mean_cost:.4f}")

        return "\n".join(lines)

    async def _gather_scores_plus_summary(self) -> str:
        """Gather scores plus LLM-generated summaries (ablation)."""
        scores_context = self._gather_scores_only()

        # Generate summaries for top candidates
        frontier = self.harness_fs.get_pareto_frontier()
        summaries = []

        for c in frontier.candidates[:5]:
            summary_prompt = f"Summarize why this harness candidate succeeded:\n{c.source_code[:1000]}"
            try:
                summary = await self.llm_call(
                    "minimax-coding-plan/MiniMax-M3",
                    "You are a harness analyst.",
                    summary_prompt,
                )
                summaries.append(f"{c.candidate_id}: {summary[:200]}")
            except Exception:
                summaries.append(f"{c.candidate_id}: (summary failed)")

        return scores_context + "\n\n=== SUMMARIES ===\n" + "\n".join(summaries)

    def _build_proposal_prompt(
        self,
        task_description: str,
        domain: HarnessDomain,
        context: str,
        num_proposals: int,
    ) -> str:
        """Build prompt for harness proposal."""
        return f"""You are Meta-Harness, an expert at designing LLM harnesses.

A harness is the code that determines what to store, retrieve, and present to an LLM.
Your job is to propose improved harnesses based on analysis of prior attempts.

TASK: {task_description}
DOMAIN: {domain.value}

Prior candidates (your feedback channel):
{context}

Based on your analysis:
1. Identify failure patterns in prior harnesses
2. Form causal hypotheses about WHY they failed
3. Design targeted improvements

Generate {num_proposals} new harness candidate(s). For each provide:
1. Brief description of the approach
2. Python code implementing the harness

Format your response as:
```json
[
  {{
    "description": "what this harness does",
    "code": "python code here"
  }}
]
```

Focus on:
- Retrieval logic (what to fetch and when)
- Memory/state management (what to store between steps)
- Prompt construction (how to present context to the model)
- Tool integration (how to use external tools effectively)
"""

    def _get_proposer_system_prompt(self) -> str:
        """Get system prompt for the proposer agent."""
        return """You are Meta-Harness, an expert harness engineer.

You have access to a filesystem containing all prior harness candidates, their scores, and execution traces.
You can read files using standard terminal tools to inspect any candidate's code and traces.

Your approach:
1. Inspect prior candidates to understand what worked and what didn't
2. Form hypotheses about WHY failures occurred (causal reasoning)
3. Design targeted improvements based on your diagnosis

You are optimizing for:
- Higher reward (task performance)
- Lower cost (token usage, latency)
- Better generalization

Think carefully about causal relationships before proposing."""

    def _parse_proposals(
        self, response: str, domain: HarnessDomain, context: str
    ) -> list[HarnessCandidate]:
        """Parse LLM response into HarnessCandidate objects."""
        import re

        candidates = []

        # Try to extract JSON array from response
        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if json_match:
            try:
                proposals = json.loads(json_match.group())
                for p in proposals:
                    candidate = HarnessCandidate(
                        candidate_id=f"harness_{uuid.uuid4().hex[:8]}",
                        source_code=p.get("code", "# No code provided"),
                        description=p.get("description", ""),
                        domain=domain,
                        proposer_reasoning=f"Proposed based on analysis of {len(self.harness_fs.get_all())} prior candidates",
                    )
                    candidates.append(candidate)
            except json.JSONDecodeError:
                pass

        # Fallback: create candidate from raw response
        if not candidates and response.strip():
            candidate = HarnessCandidate(
                candidate_id=f"harness_{uuid.uuid4().hex[:8]}",
                source_code=response.strip() or "# No code provided",
                description="Harness candidate from proposer (fallback)",
                domain=domain,
            )
            candidates.append(candidate)

        # If still no candidates (empty response), create a minimal placeholder
        if not candidates:
            candidate = HarnessCandidate(
                candidate_id=f"harness_{uuid.uuid4().hex[:8]}",
                source_code="# Empty response from proposer",
                description="Placeholder harness from empty proposer response",
                domain=domain,
            )
            candidates.append(candidate)

        return candidates


# ---------------------------------------------------------------------------
# Meta-Harness Orchestrator
# ---------------------------------------------------------------------------


class MetaHarnessOptimizer:
    """
    Meta-Harness: Outer-loop harness optimization.

    Algorithm:
    1. Initialize population with baseline harnesses
    2. For N iterations:
       a. Proposer inspects filesystem of prior candidates
       b. Proposer proposes k new harnesses
       c. Evaluate proposed harnesses on task distribution
       d. Store all (code, scores, traces) in filesystem
    3. Return Pareto frontier

    Integration with RecursiveMAS:
    - Meta-Harness optimizes the HARNESS (outer loop)
    - RecursiveMAS provides inner reasoning for agentic tasks
    """

    def __init__(
        self,
        llm_call: Callable[[str, str, str], str],
        harness_fs: HarnessFS | None = None,
        recursive_mas: RecursiveMASOrchestrator | None = None,
        proposals_per_iteration: int = 2,
        max_iterations: int = 20,
    ):
        self.llm_call = llm_call
        self.harness_fs = harness_fs or HarnessFS()
        self.recursive_mas = recursive_mas
        self.proposals_per_iteration = proposals_per_iteration
        self.max_iterations = max_iterations

        # Initialize proposer
        self.proposer = AgenticProposer(
            llm_call=llm_call,
            harness_fs=self.harness_fs,
            recursive_mas=recursive_mas,
        )

    async def initialize_population(
        self, baseline_harnesses: list[HarnessCandidate]
    ) -> None:
        """Initialize search population with baseline harnesses."""
        for candidate in baseline_harnesses:
            self.harness_fs.store(candidate)

    async def run(
        self,
        task_description: str,
        domain: HarnessDomain,
        evaluate_fn: Callable[[HarnessCandidate], list[HarnessEvaluation]],
        progress_fn: Callable[[str], None] | None = None,
    ) -> ParetoFrontier:
        """
        Run Meta-Harness optimization loop.

        Args:
            task_description: Description of the task
            domain: Harness domain
            evaluate_fn: Function to evaluate a harness candidate
            progress_fn: Optional callback for progress updates

        Returns:
            Final Pareto frontier of optimized harnesses
        """
        async def progress(msg: str) -> None:
            if progress_fn:
                progress_fn(msg)
            logger.info("[MetaHarness] %s", msg)

        await progress(f"Starting Meta-Harness optimization for {domain.value}")

        for iteration in range(1, self.max_iterations + 1):
            await progress(f"\n=== Iteration {iteration}/{self.max_iterations} ===")

            # Check population size
            stats = self.harness_fs.get_stats()
            await progress(f"Population: {stats['total_candidates']} candidates, Pareto frontier: {stats['pareto_frontier_size']}")

            # Proposer inspects filesystem and proposes new candidates
            await progress("Proposer inspecting prior candidates...")
            new_candidates = await self.proposer.propose(
                task_description=task_description,
                domain=domain,
                num_proposals=self.proposals_per_iteration,
                inspection_depth="full",
            )

            if not new_candidates:
                await progress("No new candidates proposed, continuing...")
                continue

            # Evaluate proposed candidates
            for candidate in new_candidates:
                await progress(f"Evaluating candidate {candidate.candidate_id}...")

                try:
                    evaluations = await evaluate_fn(candidate)
                    candidate.evaluations = evaluations
                    self.harness_fs.store(candidate)

                    if evaluations:
                        avg_reward = sum(e.reward for e in evaluations) / len(evaluations)
                        await progress(f"  Reward: {avg_reward:.4f}")

                except Exception as exc:
                    logger.error("Evaluation failed for %s: %s", candidate.candidate_id, exc)
                    await progress(f"  Evaluation failed: {exc}")

        # Return final Pareto frontier
        frontier = self.harness_fs.get_pareto_frontier()
        await progress("\n=== Optimization Complete ===")
        await progress(f"Final Pareto frontier: {len(frontier.candidates)} candidates")

        return frontier

    def get_best_for_cost(
        self, max_cost: float
    ) -> HarnessCandidate | None:
        """Get best candidate within cost budget."""
        candidates = self.harness_fs.get_all()
        viable = [c for c in candidates if c.mean_cost <= max_cost]

        if not viable:
            return None

        return max(viable, key=lambda c: c.mean_reward)


# ---------------------------------------------------------------------------
# Harness Evaluation Utilities
# ---------------------------------------------------------------------------


async def evaluate_harness_on_task(
    harness_code: str,
    task_instance: str,
    llm_call: Callable[[str, str, str], str],
    max_tokens: int = 2048,
) -> HarnessEvaluation:
    """
    Evaluate a harness on a single task instance.

    This is a simplified evaluation - in practice, the harness code
    would be executed to wrap the LLM calls.
    """
    trace = ExecutionTrace(prompt=task_instance, model_output="")

    start = time.perf_counter()

    try:
        # Execute harness code to get prompt
        # In practice: execute the harness code with the task
        prompt = task_instance  # Simplified

        # Call LLM
        response = await llm_call(
            "minimax-coding-plan/MiniMax-M3",
            "You are a helpful assistant.",
            prompt,
        )

        trace.model_output = response
        trace.latency_ms = (time.perf_counter() - start) * 1000

        # Simple reward: response length as proxy (replace with actual metric)
        reward = len(response) / 1000.0

    except Exception as exc:
        logger.error("Harness evaluation failed: %s", exc)
        reward = 0.0
        trace.model_output = f"Error: {exc}"

    return HarnessEvaluation(
        task_instance=task_instance,
        reward=reward,
        cost=trace.tokens_used,
        latency_ms=trace.latency_ms,
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Convenience Factory
# ---------------------------------------------------------------------------


async def run_meta_harness(
    task_description: str,
    llm_call: Callable[[str, str, str], str],
    domain: str = "text_classification",
    max_iterations: int = 10,
    progress_fn: Callable[[str], None] | None = None,
) -> ParetoFrontier:
    """
    Convenience function to run Meta-Harness.

    Usage:
        frontier = await run_meta_harness(
            task_description="Classify text into categories...",
            llm_call=llm_client.call,
            domain="text_classification",
            max_iterations=10,
        )
        best = frontier.candidates[0]
        print(f"Best harness: {best.description}")
    """

    # Initialize optimizer
    optimizer = MetaHarnessOptimizer(
        llm_call=llm_call,
        max_iterations=max_iterations,
    )

    # Map domain string to enum
    domain_map = {
        "text_classification": HarnessDomain.TEXT_CLASSIFICATION,
        "math_reasoning": HarnessDomain.MATH_REASONING,
        "agentic_coding": HarnessDomain.AGENTIC_CODING,
        "rag": HarnessDomain.RAG,
    }
    harness_domain = domain_map.get(domain.lower(), HarnessDomain.CUSTOM)

    # Simple evaluation function
    async def evaluate(candidate: HarnessCandidate) -> list[HarnessEvaluation]:
        return [
            await evaluate_harness_on_task(
                candidate.source_code,
                task_description,
                llm_call,
            )
        ]

    return await optimizer.run(
        task_description=task_description,
        domain=harness_domain,
        evaluate_fn=evaluate,
        progress_fn=progress_fn,
    )
