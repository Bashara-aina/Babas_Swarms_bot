"""Intent Router — classifies free-text messages into action categories.

No slash command needed. Bashara just talks naturally.
This complements (does NOT replace) core/autonomous_router.py — it runs as a
lightweight pre-pass that injects an intent hint into the system prompt so
the LLM leans towards the right mode.

Examples:
  "what's the weather in Tokyo tomorrow?" → WEATHER_QUERY
  "scrape this URL and give me the pricing table" → WEB_SCRAPE
  "my rumahlabuh site feels slow" → SITE_ANALYSIS
  "open spotify and play lofi" → COMPUTER_CONTROL
  "write a Python script to rename all files in a folder" → CODE_GENERATION
  "remind me tomorrow at 9am about the meeting" → SCHEDULE_TASK
  "translate this to Indonesian" → TRANSLATION
  "what did I tell you about my GPU last week?" → MEMORY_SEARCH
  "check if my Supabase tables are correct" → DATABASE_AUDIT
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Intent(Enum):
    COMPUTER_CONTROL = "computer_control"       # open apps, click, type, control OS
    CODE_GENERATION = "code_generation"         # write, fix, review code
    CODE_REVIEW = "code_review"                 # review/audit existing code
    WEB_RESEARCH = "web_research"               # search, research topics
    WEB_SCRAPE = "web_scrape"                   # scrape specific URL
    MEMORY_SEARCH = "memory_search"             # "what did I say about..."
    MEMORY_STORE = "memory_store"               # "remember that..."
    SCHEDULE_TASK = "schedule_task"             # reminders, cron-style tasks
    EMAIL_READ = "email_read"                   # read/summarize emails
    EMAIL_WRITE = "email_write"                 # draft/send email
    SITE_ANALYSIS = "site_analysis"             # rumahlabuh.com or any site audit
    DATABASE_AUDIT = "database_audit"           # Supabase / DB operations
    WEATHER_QUERY = "weather_query"             # weather, forecast
    LOCATION_QUERY = "location_query"           # restaurants, hotels, directions
    FILE_OPERATION = "file_operation"           # read, write, move files
    TRANSLATION = "translation"                 # translate text
    MATH_REASONING = "math_reasoning"           # calculations, proofs
    CREATIVE_WRITE = "creative_write"           # essays, posts, stories
    DATA_ANALYSIS = "data_analysis"             # CSV, JSON, stats analysis
    API_CALL = "api_call"                       # call an external API
    SELF_UPGRADE = "self_upgrade"               # check GitHub trending, upgrade self
    CASUAL_CHAT = "casual_chat"                 # conversation, opinions, jokes
    DEEP_REASONING = "deep_reasoning"           # complex multi-step thinking


# Keyword patterns per intent — fast heuristic before LLM classification
_PATTERNS: dict[Intent, list[str]] = {
    Intent.COMPUTER_CONTROL: [
        r"\bopen\b", r"\bclose\b.*\bapp\b", r"\bclick\b", r"\blaunch\b",
        r"\bscreenshot\b", r"\bwindow\b", r"\bdesktop\b",
        r"\bplay\b.*\b(spotify|youtube|vlc|music)\b", r"\bvolume\b",
        r"\bbuka\b", r"\btutup\b.*\bapp\b",
    ],
    Intent.CODE_GENERATION: [
        r"\bwrite\b.*\b(code|script|function|class)\b",
        r"\b(implement|build|create)\b.*\b(function|class|api|app|tool|module)\b",
        r"\badd\b.*\b(feature|method|endpoint)\b",
        r"\bfix\b.*\b(bug|error|issue)\b",
        r"\brefactor\b", r"\boptimize\b.*\bcode\b",
        r"\bbuatkan\b.*\b(kode|fungsi|script)\b",
        r"\btulis\b.*\b(kode|fungsi)\b",
    ],
    Intent.CODE_REVIEW: [
        r"\breview\b.*\bcode\b", r"\baudit\b.*\bcode\b",
        r"\bsecurity\b.*\b(check|review|scan)\b",
        r"\bcode\b.*\breview\b", r"\bcheck\b.*\bcode\b",
    ],
    Intent.WEB_RESEARCH: [
        r"\bresearch\b", r"\bwhat is\b", r"\bwho is\b", r"\bhow does\b",
        r"\bexplain\b", r"\bfind.*info\b", r"\blatest.*news\b",
        r"\btell me about\b", r"\blook up\b", r"\bsearch for\b",
        r"\bgoogle\b", r"\bcari tahu\b", r"\bjelaskan\b",
    ],
    Intent.WEB_SCRAPE: [
        r"\bscrape\b", r"\bextract.*from\b.*http",
        r"\bget.*data.*from\b.*http", r"\bparse\b.*\bhttp\b",
        r"\bwebsite.*data\b", r"\bget.*from.*url\b",
    ],
    Intent.MEMORY_SEARCH: [
        r"\bwhat did i.*say\b", r"\bdo you remember\b", r"\brecall\b",
        r"\blast.*time\b.*\b(i|we)\b", r"\bpreviously\b", r"\byou told me\b",
        r"\bi mentioned\b", r"\bkamu ingat\b", r"\bingat tidak\b",
        r"\bwe talked about\b", r"\bwe discussed\b",
    ],
    Intent.MEMORY_STORE: [
        r"\bremember (that|this)\b", r"\bsave (this|that)\b",
        r"\bnote that\b", r"\bingat ya\b", r"\bcatat\b",
        r"\bstore.*memory\b", r"\bdon't forget\b",
    ],
    Intent.SCHEDULE_TASK: [
        r"\bremind\b", r"\bset.*reminder\b", r"\bschedule\b.*\btask\b",
        r"\btomorrow\b.*\bat\b\s*\d", r"\bset.*alarm\b",
        r"\bevery (day|week|morning|night)\b", r"\bcron\b",
        r"\bingatkan\b", r"\bjadwalkan\b",
    ],
    Intent.EMAIL_READ: [
        r"\bcheck.*email\b", r"\bread.*email\b", r"\bmailbox\b",
        r"\binbox\b", r"\bunread.*email\b", r"\bemail.*today\b",
        r"\bany.*email\b", r"\bmy.*email\b",
    ],
    Intent.EMAIL_WRITE: [
        r"\bsend.*email\b", r"\bdraft.*email\b", r"\breply.*email\b",
        r"\bwrite.*email\b", r"\bkirim.*email\b", r"\bbalas.*email\b",
    ],
    Intent.SITE_ANALYSIS: [
        r"\brumahlabuh\b", r"\bmy.*site\b.*\b(slow|down|broken|check)\b",
        r"\bwebsite.*performance\b", r"\blighthouse\b", r"\bpage.*speed\b",
        r"\bseo\b", r"\banalyze.*site\b", r"\bsite.*health\b",
        r"\bcheck.*website\b",
    ],
    Intent.DATABASE_AUDIT: [
        r"\bsupabase\b", r"\bdatabase\b.*\b(check|audit|schema|query)\b",
        r"\btable\b.*\b(schema|structure|check)\b",
        r"\bsql\b.*\bquery\b", r"\bdb\b.*\b(check|audit)\b",
        r"\brows\b.*\btable\b",
    ],
    Intent.WEATHER_QUERY: [
        r"\bweather\b", r"\bforecast\b",
        r"\brain\b.*\b(today|tomorrow)\b",
        r"\btemperature\b.*\b(today|now)\b",
        r"\bcuaca\b", r"\bhujan\b.*\bhari\b",
    ],
    Intent.LOCATION_QUERY: [
        r"\brestaurants?\b", r"\bramen\b", r"\bsushi\b", r"\bcafes?\b",
        r"\bhotels?\b", r"\bwhere.*eat\b", r"\bfood.*near\b",
        r"\bdirections?\b.*\bto\b", r"\bnearby\b", r"\bnear me\b",
        r"\bnear\b.*\b(here|koto|tokyo|shibuya|shinjuku)\b",
        r"\brecommend.*place\b", r"\bgood.*\b(food|place|spot)\b.*\bnear\b",
        r"\bkafe\b", r"\bmakan.*dimana\b", r"\btempat.*rekomen\b",
        r"\bwhere.*\b(eat|drink|stay|sleep)\b",
    ],
    Intent.TRANSLATION: [
        r"\btranslate\b", r"\bin\b.*(english|indonesian|japanese|bahasa)\b",
        r"\bterjemahkan\b", r"\bartinya apa\b", r"\bke bahasa\b",
    ],
    Intent.MATH_REASONING: [
        r"\b(calculate|compute|solve|prove)\b",
        r"\b(gradient|derivative|integral|matrix|tensor|eigenvalue)\b",
        r"\b(formula|equation|probability)\b",
        r"\bhitung\b", r"\bbuktikan\b",
    ],
    Intent.DEEP_REASONING: [
        r"\bthink.*through\b", r"\banalyze.*deeply\b",
        r"\bstep.by.step\b", r"\btrade.?offs?\b", r"\bpros.*cons\b",
        r"\barchitecture.*decision\b", r"\bshould i\b.*\bor\b",
    ],
    Intent.SELF_UPGRADE: [
        r"\bgithub.*trending\b", r"\bupgrade.*yourself\b",
        r"\bnew.*tool\b.*\binstall\b", r"\bself.*update\b",
        r"\bcheck.*repo\b", r"\blatest.*library\b",
    ],
    Intent.CREATIVE_WRITE: [
        r"\bwrite.*\b(post|essay|story|poem|caption|tweet)\b",
        r"\bdraft\b.*\b(email|message|post)\b",
        r"\bblog.*post\b", r"\btulis.*artikel\b",
    ],
    Intent.DATA_ANALYSIS: [
        r"\banalyze.*data\b", r"\b(csv|json|excel)\b.*\banalyze\b",
        r"\bplot\b.*\b(graph|chart)\b", r"\bstats\b.*\b(for|of)\b",
        r"\banalisis\b.*\bdata\b",
    ],
    Intent.FILE_OPERATION: [
        r"\bread.*file\b", r"\bwrite.*file\b", r"\bopen.*file\b",
        r"\bdelete.*file\b", r"\brename.*file\b", r"\bmove.*file\b",
        r"\blist.*files\b", r"\bfind.*file\b",
    ],
    Intent.API_CALL: [
        r"\bcall.*api\b", r"\bapi.*endpoint\b", r"\bfetch.*from.*api\b",
        r"\bhttp.*request\b", r"\bpost.*to\b.*\bapi\b", r"\bget.*from\b.*\bapi\b",
    ],
}


_INTENT_TO_AGENT: dict[Intent, str] = {
    Intent.CODE_GENERATION: "coding",
    Intent.CODE_REVIEW: "reviewer",
    Intent.MATH_REASONING: "math",
    Intent.DEEP_REASONING: "think",
    Intent.DATA_ANALYSIS: "analyst",
    Intent.CREATIVE_WRITE: "general",
    Intent.WEB_RESEARCH: "researcher",
    Intent.COMPUTER_CONTROL: "computer",
    Intent.TRANSLATION: "general",
}

_INTENT_NEEDS_TOOLS: set[Intent] = {
    Intent.COMPUTER_CONTROL, Intent.FILE_OPERATION,
    Intent.EMAIL_READ, Intent.EMAIL_WRITE,
    Intent.WEB_SCRAPE, Intent.DATABASE_AUDIT,
    Intent.SCHEDULE_TASK, Intent.SELF_UPGRADE,
}

_INTENT_NEEDS_RESEARCH: set[Intent] = {
    Intent.WEB_RESEARCH, Intent.WEATHER_QUERY,
    Intent.LOCATION_QUERY, Intent.SITE_ANALYSIS,
}


@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    method: str          # "pattern"
    raw_message: str
    suggested_agent: str = ""
    needs_tools: bool = False
    needs_research: bool = False


def classify_intent_fast(message: str) -> IntentResult:
    """
    Fast pattern-based intent classification. Sub-millisecond.
    Returns highest-confidence match or CASUAL_CHAT as fallback.
    """
    msg_lower = message.lower()
    scores: dict[Intent, int] = {}

    for intent, patterns in _PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, msg_lower))
        if score > 0:
            scores[intent] = score

    if not scores:
        return IntentResult(
            Intent.CASUAL_CHAT, 0.5, "pattern", message,
            suggested_agent="general", needs_tools=False, needs_research=False,
        )

    best = max(scores, key=lambda k: scores[k])
    total_matches = scores[best]
    confidence = min(0.95, 0.5 + (total_matches * 0.15))

    return IntentResult(
        intent=best,
        confidence=confidence,
        method="pattern",
        raw_message=message,
        suggested_agent=_INTENT_TO_AGENT.get(best, "general"),
        needs_tools=best in _INTENT_NEEDS_TOOLS,
        needs_research=best in _INTENT_NEEDS_RESEARCH,
    )


def build_intent_hint(result: IntentResult) -> str:
    """Build a system prompt fragment hinting at the detected intent."""
    if result.intent == Intent.CASUAL_CHAT or result.confidence < 0.65:
        return ""
    parts = [
        f"[Detected intent: {result.intent.value} — confidence {result.confidence:.0%}."
    ]
    if result.needs_research:
        parts.append("This may need web research or live data — seek evidence before answering.")
    if result.needs_tools:
        parts.append("This likely requires tool use — suggest /do if direct action is needed.")
    parts.append("Lean towards this mode without announcing it.]")
    return " ".join(parts)
