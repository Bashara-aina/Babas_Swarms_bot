"""Intent Classifier — fast heuristic intent detection without LLM call.

Detects which skill/agent to activate from natural language,
without requiring slash commands. Runs in <1ms.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

AgentKey = Literal[
    "computer", "coding", "research", "memory", "debate", "business", "creative", "general", "scheduler", "web"
]


@dataclass
class IntentResult:
    agent_key: AgentKey
    confidence: float
    detected_intent: str
    auto_tools: list[str]
    skip_cache: bool = False


_INTENT_RULES: list[tuple[list[str], AgentKey, float, str, list[str]]] = [
    (
        [
            "open ",
            "launch ",
            "run ",
            "execute ",
            "buka ",
            "jalankan ",
            "take screenshot",
            "screenshot",
            "close ",
            "kill process",
            "install ",
            "uninstall ",
            "download ",
            "copy file",
            "move file",
            "delete file",
            "create folder",
            "zip ",
            "unzip ",
        ],
        "computer",
        0.9,
        "computer_control",
        ["screenshot", "shell", "file_ops"],
    ),
    (
        [
            "write code",
            "fix ",
            "bug",
            "debug",
            "implement",
            "refactor",
            "add function",
            "create class",
            "write a script",
            "write me a",
            "buat code",
            "perbaiki bug",
            "bikin fungsi",
            "review code",
            "explain this function",
            "optimize",
            "make this faster",
            "the error is",
            "traceback",
            "TypeError",
            "ValueError",
            "ImportError",
            "python",
            "javascript",
            "typescript",
            "function ",
            "()",
            "=>",
            "const ",
            "let ",
            "var ",
            "import ",
        ],
        "coding",
        0.9,
        "coding_assistant",
        ["code_exec", "file_read"],
    ),
    (
        [
            "research ",
            "find out",
            "search for",
            "what is ",
            "who is ",
            "how does ",
            "explain ",
            "latest news",
            "what happened",
            "cari info",
            "jelaskan ",
            "apa itu ",
            "gimana caranya",
            "compare ",
            "difference between",
            "pros and cons",
            "is it true that",
            "fact check",
            "arxiv",
            "paper ",
            "journal",
        ],
        "research",
        0.85,
        "deep_research",
        ["web_search", "wiki_lookup"],
    ),
    (
        [
            "remember ",
            "recall ",
            "what did i say",
            "i told you",
            "do you remember",
            "my preference",
            "what was that",
            "simpan ",
            "ingat ",
            "kamu ingat ",
            "kemarin gw bilang",
        ],
        "memory",
        0.9,
        "memory_ops",
        ["mem0_search", "om_search"],
    ),
    (
        [
            "rumahlabuh",
            "cekwajar",
            "supabase",
            "database query",
            "check my site",
            "website down",
            "deployment",
            "vercel",
            "revenue",
            "listings",
            "users signed up",
            "analytics",
            "api endpoint",
            "midtrans",
            "payment",
            "booking",
        ],
        "business",
        0.95,
        "business_ops",
        ["supabase_query", "web_check"],
    ),
    (
        [
            "remind me",
            "schedule ",
            "set alarm",
            "every day",
            "at ",
            "tomorrow",
            "next week",
            "deadline",
            "thesis due",
            "ingatkan ",
            "jadwalkan ",
            "tiap hari",
            "cron",
            "recurring",
        ],
        "scheduler",
        0.85,
        "scheduling",
        ["cron", "calendar"],
    ),
    (
        [
            "do you agree",
            "what do you think",
            "is this a good idea",
            "should i ",
            "debate me",
            "challenge this",
            "play devil's advocate",
            "roast my idea",
            "kamu setuju",
            "menurut kamu",
            "ide gw bagus gak",
            "opinion ",
            "thoughts on",
        ],
        "debate",
        0.8,
        "debate_mode",
        [],
    ),
    (
        [
            "write a story",
            "poem ",
            "joke ",
            "buat cerita",
            "puisi",
            "creative ",
            "imagine ",
            "what if we",
            "generate ideas",
            "brainstorm ",
            "come up with",
            "创意",
            "rhyme",
        ],
        "creative",
        0.8,
        "creative_mode",
        [],
    ),
    (
        ["scrape ", "fetch ", "crawl ", "grab ", "extract data", "webpage", "url ", "http", "www."],
        "web",
        0.75,
        "web_fetch",
        ["http_request", "html_parse"],
    ),
    # System commands auto-route — 17 commands that map to computer_use_loop
    (
        [
            "/logs", "/ps ", "/kill ", "/sys ", "/ls ", "/find ", "/grep ",
            "/read ", "/write ", "/disk ", "/window ", "/screen ",
            "/clipboard ", "/type ", "/key ", "/service ", "/tree ",
            "tail log", "list processes", "kill process", "system stats",
            "disk usage", "process tree", "list windows", "screenshot",
            "clipboard", "type text", "key combo", "service status",
            "search files", "grep log", "read file", "write file",
        ],
        "computer",
        0.95,
        "system_command",
        ["computer_use_loop"],
    ),
]

_last_agent_key: dict[str, str] = {}


def classify_intent(message: str, prior_agent_key: str = "general") -> IntentResult:
    """Fast heuristic intent classification. Runs in <1ms."""
    msg_lower = message.lower()
    best_match: IntentResult | None = None
    best_score = 0.0

    for patterns, agent_key, base_confidence, label, tools in _INTENT_RULES:
        hits = sum(1 for p in patterns if p in msg_lower)
        if hits == 0:
            continue
        score = base_confidence * min(1.0, 0.5 + hits * 0.25)
        if score > best_score:
            best_score = score
            best_match = IntentResult(
                agent_key=agent_key,
                confidence=score,
                detected_intent=label,
                auto_tools=tools,
                skip_cache=agent_key in ("computer", "business", "scheduler"),
            )

    if best_match and best_match.confidence >= 0.45:
        return best_match

    if prior_agent_key not in ("general", "memory") and len(message.split()) < 8:
        return IntentResult(
            agent_key=prior_agent_key,
            confidence=0.5,
            detected_intent="continuation",
            auto_tools=[],
        )

    return IntentResult(
        agent_key="general",
        confidence=0.3,
        detected_intent="general_conversation",
        auto_tools=[],
    )
