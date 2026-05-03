"""Lightweight cognition layer — intent hints + reasoning contract for each turn.

Runs synchronously (regex/heuristics) so it adds negligible latency. When
``LEGION_COGNITION_PIPELINE`` is off, returns an empty string.
"""

from __future__ import annotations

import os
import re

_FACUAL_HINTS = re.compile(
    r"\b(restaurant|hotel|flight|harga|price|cuaca|weather|terbaru|latest|news|"
    r"berapa|jadwal|schedule|libur|holiday|near me|terdekat|review|stock|crypto)\b",
    re.I,
)
_CODE_HINTS = re.compile(
    r"\b(def |class |import |async def|```|npm |pip |git |pytest|docker |supabase|"
    r"migration|sql|typescript|error traceback)\b",
    re.I,
)
_RESEARCH_VERBS = re.compile(
    r"\b(research|find out|look up|search|cari tahu|bandingkan|compare|analyze|"
    r"investigate|verify|sources?|evidence)\b",
    re.I,
)
_AUTOMATION_HINTS = re.compile(
    r"\b(scrape|cron|schedule|every day|every week|webhook|api|n8n|automation|"
    r"remind me|ingatkan)\b",
    re.I,
)
_ID_CASUAL = re.compile(
    r"\b(dong|nih|sih|kali|nggak|gak|gak\?|wkwk|haha|mantap|sip|oke|deh|lah)\b",
    re.I,
)
_ID_TASK_VERBS = re.compile(
    r"\b(tolong|bantu|bisa|tolongin|minta|butuh|mau|pengen|gimana|bagaimana)\b",
    re.I,
)
_HIGH_IMPACT_ROUTE = re.compile(
    r"(computer_control|jarvis|business_query|whatsapp|email_management|"
    r"system_control|runbook|github_intel|jarvis_orchestrate)",
    re.I,
)


def classify_intent_line(user_message: str) -> str:
    t = (user_message or "").strip()
    if len(t) < 4:
        return "ambient / short"
    labels: list[str] = []
    if _CODE_HINTS.search(t):
        labels.append("code/technical")
    if _FACUAL_HINTS.search(t):
        labels.append("time-sensitive or local facts")
    if _RESEARCH_VERBS.search(t):
        labels.append("needs verification / sources")
    if _AUTOMATION_HINTS.search(t):
        labels.append("automation or recurring job")
    if _ID_TASK_VERBS.search(t):
        labels.append("Bahasa request — answer clearly, stay warm")
    if _ID_CASUAL.search(t) and len(t.split()) < 22:
        labels.append("casual ID tone — mirror lightly, no lecturing")
    if "?" in t:
        labels.append("question")
    if not labels:
        if len(t.split()) <= 5:
            labels.append("conversational / casual")
        else:
            labels.append("general task")
    return ", ".join(labels)


def build_cognition_system_fragment(
    _user_id: str,
    user_message: str,
    routing_hint: str | None = None,
) -> str:
    """Return a system-prompt fragment (may be empty)."""
    if os.getenv("LEGION_COGNITION_PIPELINE", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return ""

    intent = classify_intent_line(user_message)
    lines = [
        "[COGNITION — this turn]",
        f"- Detected shape: {intent}",
    ]
    rh = (routing_hint or "").strip()
    if rh:
        lines.append(f"- Autonomous route hint: {rh}")
    if rh and _HIGH_IMPACT_ROUTE.search(rh):
        lines.append(
            "- Stakes: side-effects are plausible (desktop, email, WA, shell, or guest/biz data). "
            "Confirm destructive or outbound actions with the user unless they were explicit."
        )

    lines.extend(
        [
            "- Protocol: If the user needs live facts (places, prices, news, weather), "
            "you already have or will receive research blocks — ground answers there; "
            "otherwise mark uncertainty.",
            "- If the user is coding: prefer concrete steps, file paths, and verification; "
            "don't fake command output.",
            "- Maintain one coherent voice: you are the same Legion across tools and "
            "specialists; reference working memory naturally when relevant.",
            "- End with a human hook when it fits: one follow-up question, caveat, or "
            "next action — not a bullet wall.",
        ]
    )
    return "\n".join(lines)
