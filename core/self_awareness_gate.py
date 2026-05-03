"""Self-Awareness Gate — intercepts 'I don't know' responses and triggers search."""

import re

IGNORANCE_SIGNALS = [
    "gak punya info",
    "tidak punya informasi",
    "tidak ada di",
    "tidak ada dalam dataset",
    "gak ada di dataset",
    "tidak ada dalam pengetahuan",
    "belum familiar",
    "belum tahu",
    "tidak tahu siapa",
    "tidak mengenal",
    "tidak tahu",
    "gak tahu",
    "not in my",
    "don't have information",
    "no information about",
    "i don't know",
    "saya tidak tahu",
    "aku tidak tahu",
]

CORE_KNOWLEDGE_NAMES = [
    "bashara",
    "bashara aina",
    "cekwajar",
    "rumahlabuh",
    "legion",
    "babas",
]


def should_search_instead(response_draft: str, original_query: str) -> bool:
    """Returns True if Legion is about to say it doesn't know something and should search instead."""
    response_lower = response_draft.lower()
    query_lower = original_query.lower()

    # If about to admit ignorance
    is_ignorant = any(signal in response_lower for signal in IGNORANCE_SIGNALS)

    if not is_ignorant:
        return False

    # Critical: if asking about Bashara/core topics — ALWAYS search
    if any(name in query_lower for name in CORE_KNOWLEDGE_NAMES):
        return True

    # If query contains "siapa", "cari info", "cari tau" — search intent
    search_intent_keywords = [
        "siapa",
        "cari info",
        "cari tau",
        "cari tahu",
        "who is",
        "find info",
        "search for",
        "find out",
        "kesan",
        "review",
        "opinion about",
    ]
    return bool(any(kw in query_lower for kw in search_intent_keywords))


def get_search_trigger_message(original_query: str) -> str:
    """Returns a message to send to Telegram while search is running."""
    return "🔍 Lagi cari info..."


def build_search_query_from_message(message: str) -> str:
    """Converts user message to a web search query."""
    # Remove common filler
    query = message.strip()
    for filler in ["bisa", "coba", "tolong", "dong", "ga", "gak", "ya", "nih"]:
        query = re.sub(rf"\b{filler}\b", "", query, flags=re.IGNORECASE)

    # Common patterns
    patterns = [
        (r"cari info (.+) tuh siapa", r"\1 adalah siapa profil"),
        (r"siapa (?:itu |tuh )?(.+)", r"profil \1 Indonesia"),
        (r"kesan orang ke (.+)", r"\1 review pendapat orang"),
        (r"cari info (.+)", r"\1"),
        # Person search patterns: "cari siapa X" → "X researcher"
        (r"cari siapa (.+)", r"\1 researcher"),
        (r"google siapa (.+)", r"\1 researcher"),
        (r"search who is (.+)", r"\1 researcher"),
        (r"siapa(?: itu)? (.+)", r"\1"),
    ]

    for pattern, replacement in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE).strip()
            # For person searches, add academic/professional site suffix
            if any(kw in message.lower() for kw in ["cari siapa", "google siapa", "search who is"]):
                query = f"{query} site:linkedin.com OR site:researchgate.net OR site:scholar.google.com"
            return query

    return query.strip()
