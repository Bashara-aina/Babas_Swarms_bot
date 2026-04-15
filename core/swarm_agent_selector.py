"""core/swarm_agent_selector.py — Intelligent agent selection for swarm tasks."""

from __future__ import annotations

import re
from typing import TypedDict

import yaml


class AgentProfile(TypedDict):
    key: str
    department: str
    description: str
    capabilities: list[str]
    complexity_tier: str
    primary_model: str


class AgentSelector:
    """Scores and selects agents from departments.yaml based on task analysis."""

    def __init__(self, yaml_path: str = "config/departments.yaml"):
        self.yaml_path = yaml_path
        self._registry: dict[str, list[AgentProfile]] = {}
        self._load()

    def _load(self) -> None:
        with open(self.yaml_path) as f:
            data = yaml.safe_load(f)
        for dept, dept_data in data.items():
            if dept == "legacy":
                continue  # skip legacy
            agents = dept_data.get("agents", {})
            self._registry[dept] = []
            for name, cfg in agents.items():
                self._registry[dept].append(
                    AgentProfile(
                        key=name,
                        department=dept,
                        description=cfg.get("description", ""),
                        capabilities=cfg.get("capabilities", []),
                        complexity_tier=cfg.get("complexity_tier", "midweight"),
                        primary_model=cfg.get("primary_model", "general"),
                    )
                )

    def _tokenize(self, text: str) -> set[str]:
        """Lowercase, extract alphanumeric tokens + 2-char ngrams."""
        text = text.lower()
        tokens = set(re.findall(r"[a-z][a-z0-9]{1,}", text))
        # bigrams for multi-word concepts
        words = text.split()
        bigrams = {f"{a}_{b}" for a, b in zip(words, words[1:])}
        return tokens | bigrams

    def score_agent(self, agent: AgentProfile, task_tokens: set[str]) -> float:
        """Score an agent on how well it matches the task."""
        cap_tokens = self._tokenize(" ".join(agent["capabilities"]))
        desc_tokens = self._tokenize(agent["description"])

        cap_overlap = len(task_tokens & cap_tokens)
        desc_overlap = len(task_tokens & desc_tokens)

        # Weighted scoring
        score = cap_overlap * 3.0 + desc_overlap * 1.0

        # Bonus for exact capability matches
        for tok in task_tokens:
            if tok in cap_tokens:
                score += 0.5

        return score

    def select(self, task: str, top_k: int = 4, min_score: float = 1.0) -> list[AgentProfile]:
        """Select the top-k agents most suitable for the task."""
        task_tokens = self._tokenize(task)

        all_scores: list[tuple[float, AgentProfile]] = []
        for dept, agents in self._registry.items():
            for agent in agents:
                score = self.score_agent(agent, task_tokens)
                if score >= min_score:
                    all_scores.append((score, agent))

        all_scores.sort(key=lambda x: x[0], reverse=True)
        return [agent for _, agent in all_scores[:top_k]]

    def select_by_department(
        self, task: str, dept_counts: dict[str, int], min_score: float = 0.5
    ) -> list[AgentProfile]:
        """Select agents spread across specified departments."""
        task_tokens = self._tokenize(task)
        selected: list[AgentProfile] = []

        for dept, count in dept_counts.items():
            if dept not in self._registry:
                continue
            agents = self._registry[dept]
            scored = [(self.score_agent(a, task_tokens), a) for a in agents]
            scored.sort(key=lambda x: x[0], reverse=True)
            selected.extend([a for _, a in scored[:count] if _ >= min_score])

        return selected

    def get_team(self, task: str, size: int = 4) -> list[str]:
        """Return agent keys for a swarm team optimized for the task."""
        agents = self.select(task, top_k=size, min_score=1.0)
        return [a["key"] for a in agents]

    def get_department_team(
        self, task: str, size: int = 4, prefer: list[str] | None = None
    ) -> list[str]:
        """Return a team balanced across departments."""
        task_tokens = self._tokenize(task)
        selected: list[AgentProfile] = []

        # Prefer departments if specified
        if prefer:
            dept_order = [d for d in prefer if d in self._registry] + [
                d for d in self._registry if d not in prefer
            ]
        else:
            dept_order = list(self._registry.keys())

        per_dept = max(1, size // len(dept_order))
        remainder = size % len(dept_order)

        for i, dept in enumerate(dept_order):
            count = per_dept + (1 if i < remainder else 0)
            agents = self._registry[dept]
            scored = sorted(
                [(self.score_agent(a, task_tokens), a) for a in agents],
                key=lambda x: x[0],
                reverse=True,
            )
            selected.extend([a for _, a in scored[:count] if _ >= 0.5])

        # If we don't have enough, add best matches regardless of dept (min 0.8 score)
        if len(selected) < size:
            all_agents = [a for agents in self._registry.values() for a in agents]
            scored = sorted(
                [(self.score_agent(a, task_tokens), a) for a in all_agents],
                key=lambda x: x[0],
                reverse=True,
            )
            existing_keys = {a["key"] for a in selected}
            for score, a in scored:
                if score >= 0.8 and a["key"] not in existing_keys and len(selected) < size:
                    selected.append(a)

        return [a["key"] for a in selected[:size]]

    def explain_selection(self, task: str, top_k: int = 4) -> str:
        """Return a human-readable explanation of agent selection."""
        agents = self.select(task, top_k=top_k, min_score=0.5)
        lines = [f"Task: {task[:80]}...", "", "Selected agents:"]
        for i, a in enumerate(agents, 1):
            task_tokens = self._tokenize(task)
            cap_tokens = self._tokenize(" ".join(a["capabilities"]))
            matched = task_tokens & cap_tokens
            lines.append(
                f"  {i}. {a['key']} ({a['department']}) — "
                f"capabilities: {', '.join(a['capabilities'][:5])}"
            )
            if matched:
                lines[-1] += f" | matched: {', '.join(list(matched)[:5])}"
        return "\n".join(lines)


# Singleton
_selector: AgentSelector | None = None


def get_selector() -> AgentSelector:
    global _selector
    if _selector is None:
        _selector = AgentSelector()
    return _selector


async def select_swarm_team(task: str, size: int = 4) -> list[str]:
    """Async convenience function to select a team."""
    selector = get_selector()
    return selector.get_department_team(task, size=size)


if __name__ == "__main__":
    sel = AgentSelector()
    task = "debug a CUDA kernel that's causing OOM errors in my PyTorch training"
    print(sel.explain_selection(task))
    print("---")
    print("Team:", sel.get_department_team(task, size=5))