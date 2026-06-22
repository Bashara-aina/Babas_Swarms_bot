"""Coordinator — runs 20 agents in parallel via ThreadPoolExecutor, tracks deltas."""

from __future__ import annotations
import concurrent.futures
from typing import Any

from .base_agent import BaseAgent, AgentResult, Verdict


class Delta:
    """Tracks verdict changes between cycles for a single check."""
    __slots__ = ("uid", "prev", "curr")

    def __init__(self, uid: str, prev: str, curr: str):
        self.uid = uid
        self.prev = prev
        self.curr = curr

    @property
    def worsened(self) -> bool:
        return (
            (self.prev == Verdict.PASS and self.curr != Verdict.PASS)
            or (self.prev == Verdict.WARN and self.curr == Verdict.FAIL)
        )

    @property
    def improved(self) -> bool:
        return (
            (self.curr == Verdict.PASS and self.prev != Verdict.PASS)
            or (self.curr == Verdict.WARN and self.prev == Verdict.FAIL)
        )


class Coordinator:
    """Dispatches agents in parallel and tracks per-cycle deltas."""

    def __init__(self, agents: list[BaseAgent], max_workers: int = 40, agent_timeout: int = 60):
        self.agents = agents
        self.max_workers = max_workers
        self.agent_timeout = agent_timeout
        self._prev_results: dict[str, list[dict[str, Any]]] = {}  # agent_name → checks

    def run_cycle(self, ctx: dict[str, Any]) -> list[AgentResult]:
        """Execute all agents in parallel, return results."""
        ctx["prev_results"] = self._prev_results

        results: list[AgentResult] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            fut_map = {pool.submit(self._safe_run, a, ctx): a for a in self.agents}
            for fut in concurrent.futures.as_completed(fut_map, timeout=self.agent_timeout * 2):
                try:
                    results.append(fut.result(timeout=5))
                except Exception as exc:
                    agent = fut_map[fut]
                    results.append(AgentResult(agent.name, error=str(exc)))

        # build agent_name → list[check_dict] for next cycle's delta
        self._prev_results = {
            r.agent_name: [c.to_dict() for c in r.checks]
            for r in results
        }
        return results

    def compute_deltas(self, results: list[AgentResult]) -> list[Delta]:
        """Compare current results against previous cycle."""
        if not self._prev_results:
            return []
        deltas: list[Delta] = []
        for r in results:
            prev_checks = {c["uid"]: c["verdict"] for c in self._prev_results.get(r.agent_name, [])}
            for c in r.checks:
                prev_v = prev_checks.get(c.uid)
                if prev_v is not None and prev_v != c.verdict:
                    deltas.append(Delta(c.uid, prev_v, c.verdict))
        return deltas

    def _safe_run(self, agent: BaseAgent, ctx: dict[str, Any]) -> AgentResult:
        try:
            return agent.run(ctx)
        except Exception as exc:
            return AgentResult(agent.name, error=str(exc))
