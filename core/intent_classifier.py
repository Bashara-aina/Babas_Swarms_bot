"""
Semantic intent classifier — replaces keyword detect_agent().
Fast regex pattern matching, no LLM call needed.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Literal

AgentKey = Literal["computer", "coding", "debug", "research", "math", "architect", "analyst", "think", "general", "rumahlabuh"]

@dataclass
class IntentResult:
    agent_key: AgentKey
    confidence: float
    required_skills: list[str] = field(default_factory=list)
    urgency: Literal["low", "medium", "high"] = "medium"
    domain: str = "general"
    reasoning: str = ""

_INTENT_PATTERNS: list[tuple[AgentKey, list[str], list[str]]] = [
    ("rumahlabuh", [
        r"rumahlabuh", r"villa", r"booking", r"tamu", r"guest", r"reservation",
        r"check.?in", r"check.?out", r"properti", r"penginapan",
    ], ["supabase", "rumahlabuh"]),
    ("computer", [
        r"open\s+\w+", r"click", r"screenshot", r"install", r"run\s+command",
        r"jalankan", r"buka\s+app", r"automate", r"cron", r"startup",
        r"my\s+(computer|laptop|pc|workstation)",
    ], ["shell", "computer"]),
    ("coding", [
        r"write\s+(a\s+)?\w+\.(py|ts|js|sh)", r"implement", r"create\s+(a\s+)?(function|class|api|endpoint)",
        r"buat\s+(fungsi|class|api)", r"tulis\s+code", r"kode", r"python\s+script",
        r"typescript", r"next\.?js",
    ], ["coding"]),
    ("debug", [
        r"error", r"bug", r"not\s+working", r"broken", r"crash", r"exception",
        r"traceback", r"kenapa\s+(ini|error)", r"fix\s+this",
    ], ["debug"]),
    ("research", [
        r"research", r"find\s+out", r"explain", r"cari\s+tau", r"apa\s+itu",
        r"bagaimana", r"compare", r"best\s+\w+\s+for", r"recommend", r"rekomendasi",
    ], ["web_research"]),
    ("analyst", [
        r"analyz", r"analisis", r"chart", r"graph", r"visualiz",
        r"metric", r"performance", r"training\s+(run|loss|curve)",
    ], ["analyst"]),
    ("math", [
        r"calculat", r"equation", r"formula", r"derivative", r"integral",
        r"tensor", r"matrix", r"gradient",
    ], ["math"]),
    ("architect", [
        r"architect", r"system\s+design", r"scalab", r"microservice",
        r"database\s+schema", r"api\s+design", r"infrastructure", r"arsitektur",
    ], ["architect"]),
    ("think", [
        r"think\s+(through|about|deeply)", r"pros\s+and\s+cons", r"trade.?off",
        r"should\s+i", r"pertimbang", r"pikir\s+matang",
    ], ["think"]),
]


def classify_intent(message: str, default_key: AgentKey = "general") -> IntentResult:
    """Classify intent. Fast, no LLM call."""
    msg_lower = message.lower()
    best_key: AgentKey = default_key
    best_score = 0.0
    best_skills: list[str] = []
    best_reason = "default"

    for agent_key, patterns, skills in _INTENT_PATTERNS:
        matches = sum(1 for p in patterns if re.search(p, msg_lower))
        if matches > 0:
            score = matches / (len(patterns) or 1)
            if score > best_score:
                best_score = score
                best_key = agent_key
                best_skills = skills
                matched = [p for p in patterns if re.search(p, msg_lower)]
                best_reason = f"matched {matches} patterns: {matched[:3]}"

    urgency: Literal["low", "medium", "high"] = "medium"
    if any(w in msg_lower for w in ["urgent", "asap", "now", "broken", "down", "cepet", "sekarang", "darurat"]):
        urgency = "high"
    elif any(w in msg_lower for w in ["later", "whenever", "no rush", "santai"]):
        urgency = "low"

    return IntentResult(
        agent_key=best_key,
        confidence=best_score if best_score > 0 else 0.5,
        required_skills=best_skills,
        urgency=urgency,
        domain=best_key,
        reasoning=best_reason,
    )
