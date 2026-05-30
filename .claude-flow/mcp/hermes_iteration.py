#!/usr/bin/env python3
"""
Hermes Iteration Engine — Goal-driven loop / ralph-wiggum equivalent for MCP.

Provides:
  - GoalLoop:    loop until goal achieved or max iterations hit
  - RalphWiggum: structured "define done criteria, iterate until achieved"
  - Convergence detection (same result 3x, or 80%-similar 5x)
  - LLM-powered completion check (MiniMax at localhost:4000/v1)
  - State persisted to ~/.hermes/iteration_state/
  - DelegateOrchestrator integration for spawning sub-agents per iteration
"""

import asyncio
import difflib
import json
import os
import shutil
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── State Dir ─────────────────────────────────────────────────────────────────

_ITERATION_STATE_DIR = Path.home() / ".hermes" / "iteration_state"
_ITERATION_STATE_DIR.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()

# ── LLM Client (MiniMax local) ────────────────────────────────────────────────

LLM_URL = os.environ.get("MINIMAX_LLM_URL", "http://localhost:4000/v1")
LLM_API_KEY = os.environ.get("MINIMAX_API_KEY", "local")

def _llm_complete(prompt: str, max_tokens: int = 256) -> str:
    """Call MiniMax chat completion for goal evaluation."""
    import urllib.error
    import urllib.request

    payload = {
        "model": "MiniMax-Text-01",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    try:
        req = urllib.request.Request(
            LLM_URL + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LLM_API_KEY}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[llm_error: {e}]"

# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class IterationRecord:
    iteration: int
    context: str
    result: str
    goal_reached: bool = False
    timestamp: float = field(default_factory=time.time)
    convergence_score: float = 0.0  # 0-1 similarity to previous result

@dataclass
class LoopState:
    loop_id: str
    goal: str
    stop_condition: str  # "goal_reached" | "max_iterations" | "converged" | "stopped"
    max_iterations: int
    current_iteration: int = 0
    status: str = "active"  # active | converged | goal_reached | maxed | stopped
    iterations: list[IterationRecord] = field(default_factory=list)
    convergence_signals: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "loop_id": self.loop_id,
            "goal": self.goal,
            "stop_condition": self.stop_condition,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "status": self.status,
            "iterations": [
                {**asdict(r), "timestamp": r.timestamp}
                for r in self.iterations
            ],
            "convergence_signals": self.convergence_signals,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "LoopState":
        ls = LoopState(
            loop_id=d["loop_id"],
            goal=d["goal"],
            stop_condition=d["stop_condition"],
            max_iterations=d["max_iterations"],
            current_iteration=d.get("current_iteration", 0),
            status=d.get("status", "active"),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
        )
        ls.iterations = [
            IterationRecord(
                iteration=r["iteration"],
                context=r["context"],
                result=r["result"],
                goal_reached=r.get("goal_reached", False),
                timestamp=r.get("timestamp", time.time()),
                convergence_score=r.get("convergence_score", 0.0),
            )
            for r in d.get("iterations", [])
        ]
        ls.convergence_signals = d.get("convergence_signals", [])
        return ls


@dataclass
class RwCriterion:
    criterion: str
    satisfied: bool = False
    evidence: str = ""
    check_count: int = 0

@dataclass
class RwState:
    rw_id: str
    goal: str
    done_criteria: list[str]
    max_iters: int
    current_iteration: int = 0
    status: str = "active"  # active | done | maxed | stopped
    criteria: list[dict] = field(default_factory=list)  # serialized RwCriterion
    iterations: list[IterationRecord] = field(default_factory=list)
    convergence_signals: list[str] = field(default_factory=list)
    final_result: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "rw_id": self.rw_id,
            "goal": self.goal,
            "done_criteria": self.done_criteria,
            "max_iters": self.max_iters,
            "current_iteration": self.current_iteration,
            "status": self.status,
            "criteria": self.criteria,
            "iterations": [
                {**asdict(r), "timestamp": r.timestamp}
                for r in self.iterations
            ],
            "convergence_signals": self.convergence_signals,
            "final_result": self.final_result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "RwState":
        rs = RwState(
            rw_id=d["rw_id"],
            goal=d["goal"],
            done_criteria=d["done_criteria"],
            max_iters=d["max_iters"],
            current_iteration=d.get("current_iteration", 0),
            status=d.get("status", "active"),
            criteria=d.get("criteria", []),
            final_result=d.get("final_result", ""),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
        )
        rs.iterations = [
            IterationRecord(
                iteration=r["iteration"],
                context=r["context"],
                result=r["result"],
                goal_reached=r.get("goal_reached", False),
                timestamp=r.get("timestamp", time.time()),
                convergence_score=r.get("convergence_score", 0.0),
            )
            for r in d.get("iterations", [])
        ]
        rs.convergence_signals = d.get("convergence_signals", [])
        return rs


# ── State Storage ──────────────────────────────────────────────────────────────

def _loop_path(loop_id: str) -> Path:
    return _ITERATION_STATE_DIR / f"loop_{loop_id}.json"

def _rw_path(rw_id: str) -> Path:
    return _ITERATION_STATE_DIR / f"rw_{rw_id}.json"

def _save_loop(ls: LoopState) -> None:
    with _lock:
        _loop_path(ls.loop_id).write_text(json.dumps(ls.to_dict(), indent=2))

def _load_loop(loop_id: str) -> LoopState | None:
    path = _loop_path(loop_id)
    if not path.exists():
        return None
    try:
        return LoopState.from_dict(json.loads(path.read_text()))
    except Exception:
        return None

def _save_rw(rs: RwState) -> None:
    with _lock:
        _rw_path(rs.rw_id).write_text(json.dumps(rs.to_dict(), indent=2))

def _load_rw(rw_id: str) -> RwState | None:
    path = _rw_path(rw_id)
    if not path.exists():
        return None
    try:
        return RwState.from_dict(json.loads(path.read_text()))
    except Exception:
        return None

def _list_active_loops() -> list[dict]:
    results = []
    with _lock:
        for f in _ITERATION_STATE_DIR.glob("loop_*.json"):
            try:
                d = json.loads(f.read_text())
                if d.get("status") == "active":
                    results.append({
                        "loop_id": d["loop_id"],
                        "goal": d["goal"],
                        "current_iteration": d.get("current_iteration", 0),
                        "status": d.get("status", "active"),
                    })
            except Exception:
                pass
    return results

def _list_active_rws() -> list[dict]:
    results = []
    with _lock:
        for f in _ITERATION_STATE_DIR.glob("rw_*.json"):
            try:
                d = json.loads(f.read_text())
                if d.get("status") == "active":
                    results.append({
                        "rw_id": d["rw_id"],
                        "goal": d["goal"],
                        "current_iteration": d.get("current_iteration", 0),
                        "status": d.get("status", "active"),
                    })
            except Exception:
                pass
    return results

# ── Convergence Detection ──────────────────────────────────────────────────────

def _similarity(a: str, b: str) -> float:
    """Return 0-1 similarity score between two strings."""
    return difflib.SequenceMatcher(None, a, b).ratio()

def _check_convergence(records: list[IterationRecord]) -> tuple[bool, str]:
    """
    Check if results have converged.
    Returns (has_converged, signal_message).
    Convergence: same result 3x in a row OR 80%-similar results 5x in a row.
    """
    if len(records) < 3:
        return False, ""

    # Check exact repeat (same result 3x)
    last3 = records[-3:]
    if all(r.result == last3[0].result for r in last3):
        return True, f"exact_match_3x: '{last3[0].result[:80]}...'"

    # Check 80% similarity 5x
    if len(records) >= 5:
        last5 = records[-5:]
        if all(_similarity(r.result, last5[0].result) >= 0.80 for r in last5):
            return True, f"80pct_similarity_5x: last_result='{last5[0].result[:80]}...'"

    return False, ""

# ── LLM Goal Evaluation ────────────────────────────────────────────────────────

def _llm_evaluate_goal(goal: str, context: str, result: str) -> tuple[bool, str]:
    """
    Use MiniMax LLM to evaluate if the goal has been reached.
    Returns (goal_reached, explanation).
    """
    prompt = f"""You are a goal evaluation assistant. Determine if the goal has been achieved.

GOAL: {goal}

RECENT CONTEXT:
{context[:1000]}

CURRENT RESULT:
{result[:1000]}

Respond with ONLY a JSON object in this exact format (no extra text):
{{"goal_reached": true or false, "reason": "brief explanation why"}}

If the goal is clearly, completely, and verifiably achieved, set goal_reached to true.
If the goal is partially achieved, not achieved, or ambiguous, set goal_reached to false.
Be conservative — prefer false when uncertain."""

    try:
        raw = _llm_complete(prompt, max_tokens=256)
        # Parse JSON from response
        # Handle cases where model adds backticks or extra text
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                parsed = json.loads(line)
                return parsed.get("goal_reached", False), parsed.get("reason", "")
        # Fallback: try full parse
        parsed = json.loads(raw.strip())
        return parsed.get("goal_reached", False), parsed.get("reason", "")
    except Exception as e:
        return False, f"[llm_eval_error: {e}]"

# ── Delegate Orchestrator Integration ─────────────────────────────────────────

DELEGATE_ORCHESTRATOR_AVAILABLE = False
_delegate_handle = None

def _try_load_delegate():
    global DELEGATE_ORCHESTRATOR_AVAILABLE, _delegate_handle
    if DELEGATE_ORCHESTRATOR_AVAILABLE:
        return
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from delegate_orchestrator import handle_delegate_orchestrator
        _delegate_handle = handle_delegate_orchestrator
        DELEGATE_ORCHESTRATOR_AVAILABLE = True
    except Exception:
        DELEGATE_ORCHESTRATOR_AVAILABLE = False

def _delegate_goal(goal: str, context: str, iteration: int) -> str:
    """Spawn sub-agent via DelegateOrchestrator for a specific iteration."""
    _try_load_delegate()
    if _delegate_handle:
        try:
            result = _delegate_handle({
                "action": "execute",
                "goal": f"[Iteration {iteration}] {goal}",
                "coordinator_id": f"iter-{iteration}",
                "max_specialists": 3,
            })
            if isinstance(result, str):
                return result
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e), "delegate_fallback": True})
    return json.dumps({"error": "delegate_orchestrator not available", "goal": goal})

# ── GoalLoop Engine ────────────────────────────────────────────────────────────

def loop_start(goal: str, max_iterations: int = 10,
               stop_condition: str = "goal_reached") -> str:
    """
    Start a new GoalLoop iteration engine.

    Args:
        goal: Description of what to achieve
        max_iterations: Hard stop after this many iterations (default 10)
        stop_condition: When to stop — "goal_reached", "converged", "max_iterations" (default: goal_reached)

    Returns:
        JSON with loop_id and initial status
    """
    loop_id = f"loop-{uuid.uuid4().hex[:8]}"
    ls = LoopState(
        loop_id=loop_id,
        goal=goal,
        stop_condition=stop_condition,
        max_iterations=max_iterations,
    )
    _save_loop(ls)
    return json.dumps({
        "loop_id": loop_id,
        "goal": goal,
        "max_iterations": max_iterations,
        "stop_condition": stop_condition,
        "status": "active",
        "message": f"GoalLoop '{loop_id}' started. Use loop_iterate to advance.",
    })

def loop_iterate(loop_id: str, context: str) -> str:
    """
    Advance a GoalLoop by one iteration.

    Args:
        loop_id: The loop to advance
        context: Current work context / information from this iteration

    Returns:
        IterationResult with updated state
    """
    ls = _load_loop(loop_id)
    if not ls:
        return json.dumps({"error": f"loop '{loop_id}' not found"})
    if ls.status != "active":
        return json.dumps({
            "error": f"loop is {ls.status}, cannot iterate",
            "loop_id": loop_id,
            "status": ls.status,
        })

    ls.current_iteration += 1
    ls.updated_at = time.time()

    # Delegate the iteration work to a sub-agent
    iteration_result = _delegate_goal(ls.goal, context, ls.current_iteration)

    # Compute convergence score vs previous result
    convergence_score = 0.0
    if ls.iterations:
        prev = ls.iterations[-1].result
        convergence_score = _similarity(iteration_result, prev)

    record = IterationRecord(
        iteration=ls.current_iteration,
        context=context,
        result=iteration_result,
        convergence_score=convergence_score,
    )
    ls.iterations.append(record)

    # LLM goal evaluation
    goal_reached, reason = _llm_evaluate_goal(ls.goal, context, iteration_result)
    record.goal_reached = goal_reached

    # Convergence check
    converged, signal = _check_convergence(ls.iterations)
    if converged:
        ls.convergence_signals.append(signal)

    # Determine stop condition
    should_stop = False
    stop_reason = ""

    if goal_reached and ls.stop_condition == "goal_reached":
        ls.status = "goal_reached"
        should_stop = True
        stop_reason = f"goal_reached: {reason}"
    elif converged and ls.stop_condition == "converged":
        ls.status = "converged"
        should_stop = True
        stop_reason = signal
    elif ls.current_iteration >= ls.max_iterations:
        ls.status = "maxed"
        should_stop = True
        stop_reason = f"max_iterations ({ls.max_iterations}) reached"

    ls.updated_at = time.time()
    _save_loop(ls)

    return json.dumps({
        "loop_id": loop_id,
        "iteration": ls.current_iteration,
        "result": iteration_result,
        "goal_reached": goal_reached,
        "goal_reached_reason": reason,
        "converged": converged,
        "convergence_signal": signal,
        "convergence_score": round(convergence_score, 3),
        "should_stop": should_stop,
        "stop_reason": stop_reason,
        "status": ls.status,
        "iterations_remaining": max(0, ls.max_iterations - ls.current_iteration),
    })

def loop_status(loop_id: str) -> str:
    """Get current status of a GoalLoop."""
    ls = _load_loop(loop_id)
    if not ls:
        return json.dumps({"error": f"loop '{loop_id}' not found"})

    last_result = ls.iterations[-1].result if ls.iterations else ""
    last_goal_reached = ls.iterations[-1].goal_reached if ls.iterations else False

    return json.dumps({
        "loop_id": loop_id,
        "goal": ls.goal,
        "status": ls.status,
        "current_iteration": ls.current_iteration,
        "max_iterations": ls.max_iterations,
        "stop_condition": ls.stop_condition,
        "last_result": last_result[:500] if last_result else "",
        "last_goal_reached": last_goal_reached,
        "total_iterations": len(ls.iterations),
        "convergence_signals": ls.convergence_signals,
        "iteration_history": [
            {"iteration": r.iteration, "goal_reached": r.goal_reached,
             "convergence_score": round(r.convergence_score, 3)}
            for r in ls.iterations
        ],
        "created_at": ls.created_at,
        "updated_at": ls.updated_at,
    })

def loop_stop(loop_id: str) -> str:
    """Stop a GoalLoop early."""
    ls = _load_loop(loop_id)
    if not ls:
        return json.dumps({"error": f"loop '{loop_id}' not found"})
    ls.status = "stopped"
    ls.updated_at = time.time()
    _save_loop(ls)
    return json.dumps({
        "loop_id": loop_id,
        "status": "stopped",
        "message": f"Loop '{loop_id}' stopped at iteration {ls.current_iteration}",
        "total_iterations": len(ls.iterations),
    })

# ── RalphWiggum Structured Iteration ──────────────────────────────────────────

def rw_define(goal: str, done_criteria: list[str], max_iters: int = 20) -> str:
    """
    Define a RalphWiggum structured iteration: define done criteria upfront.

    Args:
        goal: What to achieve
        done_criteria: List of specific criteria that define "done"
        max_iters: Maximum iterations before giving up (default 20)

    Returns:
        JSON with rw_id and initial criteria status
    """
    rw_id = f"rw-{uuid.uuid4().hex[:8]}"
    rs = RwState(
        rw_id=rw_id,
        goal=goal,
        done_criteria=done_criteria,
        max_iters=max_iters,
    )
    # Initialize criteria
    rs.criteria = [{"criterion": c, "satisfied": False, "evidence": "", "check_count": 0} for c in done_criteria]
    _save_rw(rs)
    return json.dumps({
        "rw_id": rw_id,
        "goal": goal,
        "done_criteria": done_criteria,
        "max_iters": max_iters,
        "status": "active",
        "message": f"RalphWiggum '{rw_id}' defined. Use rw_check to evaluate or rw_iterate to run.",
    })

def _rw_criteria_prompt(goal: str, done_criteria: list[str], context: str, result: str) -> str:
    """Build the LLM prompt for checking all done criteria."""
    criteria_text = "\n".join(f"- {c}" for c in done_criteria)
    return f"""You are a structured completion-checker. Evaluate each done criterion for the given goal.

GOAL: {goal}

DONE CRITERIA:
{criteria_text}

CURRENT CONTEXT:
{context[:800]}

CURRENT RESULT:
{result[:800]}

For EACH criterion, respond with a JSON object:
{{
  "evaluations": [
    {{"criterion": "the criterion text", "satisfied": true or false, "evidence": "why it is or isn't satisfied"}},
    ...
  ]
}}

Be precise and conservative. A criterion is satisfied only if there is clear, unambiguous evidence."""

def rw_check(rw_id: str) -> str:
    """
    Check if all done_criteria are met for a RalphWiggum iteration.
    Uses LLM to evaluate each criterion against the current result.

    Args:
        rw_id: The RalphWiggum iteration ID

    Returns:
        DoneResult with per-criterion status
    """
    rs = _load_rw(rw_id)
    if not rs:
        return json.dumps({"error": f"rw '{rw_id}' not found"})
    if rs.status != "active":
        return json.dumps({"error": f"rw is {rs.status}", "rw_id": rw_id, "status": rs.status})

    last_context = rs.iterations[-1].context if rs.iterations else ""
    last_result = rs.iterations[-1].result if rs.iterations else ""

    prompt = _rw_criteria_prompt(rs.goal, rs.done_criteria, last_context, last_result)
    raw = _llm_complete(prompt, max_tokens=512)

    try:
        # Find JSON in response
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("{") and '"evaluations"' in line:
                parsed = json.loads(line)
                break
        else:
            parsed = json.loads(raw.strip())
        evals = parsed.get("evaluations", [])
    except Exception as e:
        evals = [{"criterion": c, "satisfied": False, "evidence": f"parse_error: {e}", "error": True}
                 for c in rs.done_criteria]

    # Update criteria state
    all_satisfied = True
    for ev in evals:
        for crit in rs.criteria:
            if crit["criterion"] == ev.get("criterion"):
                crit["satisfied"] = ev.get("satisfied", False)
                crit["evidence"] = ev.get("evidence", "")
                crit["check_count"] = crit.get("check_count", 0) + 1
                if not ev.get("satisfied", False):
                    all_satisfied = False
                break

    # Update status
    if all_satisfied and len(rs.iterations) > 0:
        rs.status = "done"

    rs.updated_at = time.time()
    _save_rw(rs)

    return json.dumps({
        "rw_id": rw_id,
        "goal": rs.goal,
        "status": rs.status,
        "all_satisfied": all_satisfied,
        "criteria": rs.criteria,
        "done_criteria_count": len(rs.done_criteria),
        "satisfied_count": sum(1 for c in rs.criteria if c["satisfied"]),
        "total_iterations": len(rs.iterations),
    })

def rw_iterate(rw_id: str, work_context: str) -> str:
    """
    Run one iteration of a RalphWiggum structured iteration.

    Args:
        rw_id: The RalphWiggum iteration ID
        work_context: Current work context / information from this iteration

    Returns:
        RwIteration result
    """
    rs = _load_rw(rw_id)
    if not rs:
        return json.dumps({"error": f"rw '{rw_id}' not found"})
    if rs.status != "active":
        return json.dumps({"error": f"rw is {rs.status}", "rw_id": rw_id, "status": rs.status})

    rs.current_iteration += 1
    rs.updated_at = time.time()

    # Delegate iteration work
    iteration_result = _delegate_goal(rs.goal, work_context, rs.current_iteration)

    # Convergence check
    convergence_score = 0.0
    if rs.iterations:
        convergence_score = _similarity(iteration_result, rs.iterations[-1].result)

    converged, signal = _check_convergence(rs.iterations)
    if converged:
        rs.convergence_signals.append(signal)

    record = IterationRecord(
        iteration=rs.current_iteration,
        context=work_context,
        result=iteration_result,
        convergence_score=convergence_score,
    )
    rs.iterations.append(record)

    # Auto-check criteria after each iteration
    prompt = _rw_criteria_prompt(rs.goal, rs.done_criteria, work_context, iteration_result)
    raw = _llm_complete(prompt, max_tokens=512)

    try:
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("{") and '"evaluations"' in line:
                parsed = json.loads(line)
                break
        else:
            parsed = json.loads(raw.strip())
        evals = parsed.get("evaluations", [])
    except Exception:
        evals = []

    all_satisfied = True
    for ev in evals:
        for crit in rs.criteria:
            if crit["criterion"] == ev.get("criterion"):
                crit["satisfied"] = ev.get("satisfied", False)
                crit["evidence"] = ev.get("evidence", "")
                crit["check_count"] = crit.get("check_count", 0) + 1
                if not ev.get("satisfied", False):
                    all_satisfied = False
                break

    should_stop = False
    stop_reason = ""

    if all_satisfied:
        rs.status = "done"
        rs.final_result = iteration_result
        should_stop = True
        stop_reason = "all_done_criteria_satisfied"
    elif rs.current_iteration >= rs.max_iters:
        rs.status = "maxed"
        should_stop = True
        stop_reason = f"max_iters ({rs.max_iters}) reached"
    elif converged:
        rs.status = "converged"
        should_stop = True
        stop_reason = signal

    rs.updated_at = time.time()
    _save_rw(rs)

    return json.dumps({
        "rw_id": rw_id,
        "iteration": rs.current_iteration,
        "result": iteration_result,
        "all_satisfied": all_satisfied,
        "converged": converged,
        "convergence_signal": signal,
        "should_stop": should_stop,
        "stop_reason": stop_reason,
        "status": rs.status,
        "iterations_remaining": max(0, rs.max_iters - rs.current_iteration),
        "criteria_status": [
            {"criterion": c["criterion"], "satisfied": c["satisfied"]}
            for c in rs.criteria
        ],
    })

def rw_status(rw_id: str) -> str:
    """Get current status of a RalphWiggum iteration."""
    rs = _load_rw(rw_id)
    if not rs:
        return json.dumps({"error": f"rw '{rw_id}' not found"})

    return json.dumps({
        "rw_id": rw_id,
        "goal": rs.goal,
        "status": rs.status,
        "done_criteria": rs.done_criteria,
        "current_iteration": rs.current_iteration,
        "max_iters": rs.max_iters,
        "all_satisfied": all(c.get("satisfied", False) for c in rs.criteria),
        "criteria": rs.criteria,
        "total_iterations": len(rs.iterations),
        "convergence_signals": rs.convergence_signals,
        "iteration_history": [
            {"iteration": r.iteration, "convergence_score": round(r.convergence_score, 3)}
            for r in rs.iterations
        ],
        "final_result": rs.final_result[:500] if rs.final_result else "",
        "created_at": rs.created_at,
        "updated_at": rs.updated_at,
    })

def rw_stop(rw_id: str) -> str:
    """Stop a RalphWiggum iteration early."""
    rs = _load_rw(rw_id)
    if not rs:
        return json.dumps({"error": f"rw '{rw_id}' not found"})
    rs.status = "stopped"
    rs.updated_at = time.time()
    _save_rw(rs)
    return json.dumps({
        "rw_id": rw_id,
        "status": "stopped",
        "message": f"RalphWiggum '{rw_id}' stopped at iteration {rs.current_iteration}",
        "total_iterations": len(rs.iterations),
    })

# ── MCP Handler ────────────────────────────────────────────────────────────────

def handle_hermes_iteration(action: str, goal: str = "", loop_id: str = "",
                             rw_id: str = "", context: str = "",
                             done_criteria: list[str] = None,
                             max_iterations: int = 10) -> str:
    """
    Unified MCP handler for the hermes_iteration tool.

    Actions:
      loop_start     — Start a new GoalLoop
      loop_iterate   — Advance a GoalLoop by one iteration
      loop_status    — Get status of a GoalLoop
      loop_stop      — Stop a GoalLoop early
      rw_define      — Define a RalphWiggum structured iteration
      rw_check       — Check if done_criteria are satisfied
      rw_iterate     — Run one RalphWiggum iteration
      rw_status      — Get status of a RalphWiggum iteration
      rw_stop        — Stop a RalphWiggum iteration early
      list_active    — List all active loops and rws
    """
    if done_criteria is None:
        done_criteria = []

    if action == "loop_start":
        return loop_start(goal=goal, max_iterations=max_iterations, stop_condition="goal_reached")
    elif action == "loop_iterate":
        return loop_iterate(loop_id=loop_id, context=context)
    elif action == "loop_status":
        return loop_status(loop_id=loop_id)
    elif action == "loop_stop":
        return loop_stop(loop_id=loop_id)
    elif action == "rw_define":
        return rw_define(goal=goal, done_criteria=done_criteria, max_iters=max_iterations)
    elif action == "rw_check":
        return rw_check(rw_id=rw_id)
    elif action == "rw_iterate":
        return rw_iterate(rw_id=rw_id, work_context=context)
    elif action == "rw_status":
        return rw_status(rw_id=rw_id)
    elif action == "rw_stop":
        return rw_stop(rw_id=rw_id)
    elif action == "list_active":
        loops = _list_active_loops()
        rws = _list_active_rws()
        return json.dumps({"active_loops": loops, "active_rws": rws})
    else:
        return json.dumps({"error": f"unknown action: {action}"})

# ── Schema (for documentation / MCP tool registration) ─────────────────────────

HERMES_ITERATION_SCHEMA = {
    "name": "hermes_iteration",
    "description": (
        "Goal-driven iteration engine for Hermes (loop + ralph-wiggum equivalents). "
        "Use loop_start to begin a GoalLoop, loop_iterate to advance. "
        "Use rw_define to define done criteria upfront, rw_iterate to run iterations. "
        "Convergence detection stops loops that are stuck in repetitive results."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "loop_start", "loop_iterate", "loop_status", "loop_stop",
                    "rw_define", "rw_check", "rw_iterate", "rw_status", "rw_stop",
                    "list_active",
                ],
                "description": "The iteration action to perform",
            },
            "goal": {
                "type": "string",
                "description": "Goal description (for loop_start, rw_define)",
            },
            "loop_id": {
                "type": "string",
                "description": "Loop ID (for loop_iterate, loop_status, loop_stop)",
            },
            "rw_id": {
                "type": "string",
                "description": "RalphWiggum ID (for rw_check, rw_iterate, rw_status, rw_stop)",
            },
            "context": {
                "type": "string",
                "description": "Work context / iteration information (for loop_iterate, rw_iterate)",
            },
            "done_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of done criteria (for rw_define)",
            },
            "max_iterations": {
                "type": "integer",
                "default": 10,
                "description": "Max iterations (default 10 for loops, 20 for rw)",
            },
        },
        "required": ["action"],
    },
}