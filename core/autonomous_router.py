"""Autonomous skill selection for plain-text requests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillMatch:
    skill_name: str
    confidence: float
    reasoning: str


SKILL_PATTERNS = {
    "computer_control": {
        "keywords": ["open", "click", "type", "screenshot", "run this", "launch", "navigate to", "go to", "show me my screen", "check my"],
        "description": "Control Linux desktop",
        "handler": "/do",
    },
    "deep_research": {
        "keywords": ["research", "find out", "search for", "look up", "what is", "explain", "compare", "analyze", "investigate", "survey"],
        "description": "Multi-source research",
        "handler": "/research",
    },
    "code_generation": {
        "keywords": ["write", "code", "implement", "build", "create a script", "function", "class", "module", "refactor", "debug"],
        "description": "Code generation/review",
        "handler": "/run",
    },
    "deep_reasoning": {
        "keywords": ["why", "should i", "is it better", "trade-off", "pros and cons", "what do you think", "your opinion", "advise", "recommend", "evaluate", "critique", "review"],
        "description": "Deep analytical reasoning",
        "handler": "/think",
    },
    "multi_agent_swarm": {
        "keywords": ["complex", "full system", "end-to-end", "architecture", "design the", "plan the", "complete", "comprehensive", "multiple steps", "pipeline", "workflow"],
        "description": "Multi-agent execution",
        "handler": "/swarm",
    },
    "memory_search": {
        "keywords": ["remember", "recall", "what did i say", "last time", "previously", "before", "history", "you mentioned"],
        "description": "Search persistent memory",
        "handler": "memory_recall",
    },
    "system_control": {
        "keywords": ["gpu", "cpu", "ram", "memory usage", "processes", "systemctl", "service", "install", "upgrade", "pip", "apt"],
        "description": "System monitoring/control",
        "handler": "/cmd",
    },
    "conversation": {
        "keywords": [],
        "description": "Natural conversation",
        "handler": "chat",
    },
}


class AutonomousRouter:
    def __init__(self, memory_manager, reflection_engine) -> None:
        self.memory = memory_manager
        self.reflection = reflection_engine
        self._skill_performance: dict[str, list[float]] = {}

    def analyze(self, message: str) -> SkillMatch:
        msg_lower = message.lower().strip()
        scores: dict[str, float] = {}

        for skill, config in SKILL_PATTERNS.items():
            if skill == "conversation":
                continue
            score = 0.0
            for keyword in config["keywords"]:
                if keyword in msg_lower:
                    score += len(keyword.split()) * 0.25
            scores[skill] = score

        if not scores or max(scores.values()) < 0.25:
            return SkillMatch(
                skill_name="conversation",
                confidence=0.9,
                reasoning="No specific skill keywords detected",
            )

        best_skill = max(scores, key=scores.get)
        confidence = min(0.95, scores[best_skill] / 2.0)
        return SkillMatch(
            skill_name=best_skill,
            confidence=confidence,
            reasoning=f"Matched '{best_skill}' pattern with score {scores[best_skill]:.2f}",
        )

    def record_performance(self, skill: str, success: bool) -> None:
        if skill not in self._skill_performance:
            self._skill_performance[skill] = []
        self._skill_performance[skill].append(1.0 if success else 0.0)
        if len(self._skill_performance[skill]) > 20:
            self._skill_performance[skill].pop(0)

    def get_skill_stats(self) -> dict:
        return {
            skill: {
                "avg_success": (sum(scores) / len(scores)) if scores else 0.0,
                "total_uses": len(scores),
            }
            for skill, scores in self._skill_performance.items()
        }
