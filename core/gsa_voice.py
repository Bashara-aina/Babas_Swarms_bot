"""GSA Voice module — context-aware communication style injection.

Synthesizes communication styles from Gita Wirjawan, Sandiaga Uno, and
Anies Baswedan's for context-appropriate responses across technical,
emotional, analytical, and strategic contexts.

Key improvements over v1/v2:
- Multi-label classification with confidence scoring
- Visual signal detection (emoji, caps, punctuation)
- Conversation flow awareness (follow-up, pivot)
- Context-aware enforcement in character_enforcer
- Feedback learning system
- LLM-based classification fallback for ambiguous cases
- Dynamic pattern learning from corrections
- Conversation state machine for multi-turn arcs
- Bashara-specific calibration from corrections
- Response templates per context
- Time-of-day aware GSA variation (JST)
- Response quality scoring
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from threading import Lock
from typing import Optional


class MessageContext(Enum):
    """Enumeration of message context types for GSA Voice injection."""

    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    ANALYTICAL = "analytical"
    REVIEW = "review"
    CASUAL = "casual"
    STRATEGIC = "strategic"


@dataclass
class ContextClassification:
    """Multi-label classification result with confidence scores."""

    primary: MessageContext
    confidence: float
    secondary: Optional[MessageContext] = None
    secondary_confidence: float = 0.0
    visual_signals: list[str] = field(default_factory=list)
    flow_state: str = "new"
    reasoning: str = ""
    needs_llm_fallback: bool = False
    classification_method: str = "keyword"


@dataclass
class ConversationState:
    """Tracks conversation state for multi-turn awareness."""

    context_history: list[MessageContext] = field(default_factory=list)
    last_context: Optional[MessageContext] = None
    topic_stack: list[str] = field(default_factory=list)
    turn_count: int = 0
    last_update: datetime = field(default_factory=datetime.now)
    energy_level: str = "normal"  # normal | low | high
    correction_count: int = 0

    def record_turn(self, context: MessageContext, topic: str = "") -> None:
        self.turn_count += 1
        self.last_context = context
        if self.context_history[-1:] != [context]:
            self.context_history.append(context)
        if topic:
            if not self.topic_stack or self.topic_stack[-1] != topic:
                self.topic_stack.append(topic)
        self.last_update = datetime.now(timezone.utc)

    def detect_arc_completion(self) -> bool:
        if len(self.context_history) >= 3:
            recent = self.context_history[-3:]
            if all(c == MessageContext.TECHNICAL for c in recent):
                return True
        return False


class GSAConversationManager:
    """Manages conversation state across turns with thread safety."""

    _instance: Optional["GSAConversationManager"] = None
    _lock = Lock()

    def __init__(self):
        self.states: dict[str, ConversationState] = {}
        self.turn_timers: dict[str, datetime] = {}

    @classmethod
    def get_instance(cls) -> "GSAConversationManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_state(self, user_id: str) -> ConversationState:
        with self._lock:
            if user_id not in self.states:
                self.states[user_id] = ConversationState()
            return self.states[user_id]

    def record_turn(self, user_id: str, context: MessageContext, topic: str = "") -> None:
        state = self.get_state(user_id)
        state.record_turn(context, topic)

    def cleanup_stale_states(self, max_age_seconds: int = 3600) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            stale = [
                uid for uid, state in self.states.items() if (now - state.last_update).total_seconds() > max_age_seconds
            ]
            for uid in stale:
                del self.states[uid]


_conversation_manager: Optional[GSAConversationManager] = None


def get_conversation_manager() -> GSAConversationManager:
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = GSAConversationManager.get_instance()
    return _conversation_manager


@dataclass
class DynamicPattern:
    """A pattern learned from corrections or feedback."""

    pattern: str
    pattern_type: str  # "opener", "phrase", "closer", "structure"
    count: int = 0
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)

    def update(self) -> None:
        self.count += 1
        self.last_seen = datetime.now(timezone.utc)
        self.confidence = min(0.95, 0.3 + (self.count * 0.1))


class GSADynamicPatterns:
    """Learn and apply dynamic patterns from user corrections."""

    _instance: Optional["GSADynamicPatterns"] = None

    def __init__(self):
        self._patterns: dict[str, DynamicPattern] = {}
        self._lock = Lock()

    @classmethod
    def get_instance(cls) -> "GSADynamicPatterns":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_pattern(self, pattern: str, ptype: str) -> None:
        key = f"{ptype}:{pattern.lower()}"
        with self._lock:
            if key in self._patterns:
                self._patterns[key].update()
            else:
                self._patterns[key] = DynamicPattern(pattern=pattern, pattern_type=ptype)

    def get_hot_patterns(self, min_confidence: float = 0.5) -> list[str]:
        with self._lock:
            return [p.pattern for p in self._patterns.values() if p.confidence >= min_confidence]

    def apply_dynamic_filters(self, text: str) -> str:
        hot = self.get_hot_patterns(min_confidence=0.6)
        for pattern in hot:
            if pattern.lower() in text.lower():
                pattern_re = re.compile(re.escape(pattern), re.IGNORECASE)
                text = pattern_re.sub("", text)
        return text

    def record_correction(self, original: str, corrected: str) -> None:
        opener_patterns = [
            r"^(iya[\s,]+|ya[\s,]+|ok[\s,]+|oke[\s,]+)",
            r"^(baik[\s,]+|tentu[\s,]+|pastinya[\s,]+)",
        ]
        for pat in opener_patterns:
            match = re.search(pat, original.lower())
            if match:
                self.add_pattern(match.group(1).strip(), "opener")


_dynamic_patterns: Optional[GSADynamicPatterns] = None


def get_dynamic_patterns() -> GSADynamicPatterns:
    global _dynamic_patterns
    if _dynamic_patterns is None:
        _dynamic_patterns = GSADynamicPatterns.get_instance()
    return _dynamic_patterns


GSA_CONTEXT_KEYWORDS: dict[MessageContext, dict[str, float]] = {
    MessageContext.EMOTIONAL: {
        "capek": 1.0,
        "pusing": 0.9,
        "stress": 1.0,
        "stuck": 0.85,
        "bingung": 0.9,
        "sedih": 1.0,
        "frustrasi": 1.0,
        "down": 0.9,
        "ga mood": 1.0,
        "gak mood": 1.0,
        "males": 0.8,
        "overwhelming": 1.0,
        "burnout": 1.0,
        "hopeless": 1.0,
        "give up": 1.0,
        "menyerah": 0.9,
        "kelelahan": 0.85,
        "无力": 1.0,
        "tidak kuat": 0.8,
        "nggak kuat": 0.8,
        "remuk": 0.7,
        "hancur": 0.7,
    },
    MessageContext.TECHNICAL: {
        "bug": 1.0,
        "error": 1.0,
        "fix": 0.85,
        "implement": 0.8,
        "build": 0.7,
        "code": 0.9,
        "deploy": 0.85,
        "install": 0.75,
        "setup": 0.75,
        "config": 0.8,
        "crash": 0.9,
        "debug": 1.0,
        "gagal": 0.7,
        "tidak bisa": 0.6,
        "rusak": 0.7,
        "broken": 0.8,
        "exception": 0.9,
        "traceback": 1.0,
        "runtime": 0.8,
        "compil": 0.7,
    },
    MessageContext.ANALYTICAL: {
        "gimana": 0.8,
        "bagaimana": 0.8,
        "menurut": 0.9,
        "analisis": 1.0,
        "pendapat": 0.9,
        "perbandingan": 0.85,
        "pilihan": 0.7,
        "strategi": 0.85,
        "keputusan": 0.9,
        "worth it": 1.0,
        "lebih baik": 0.85,
        "seharusnya": 0.8,
        "tapi kalau": 0.6,
        " namun": 0.5,
        " pertanyaannya": 0.6,
        " sudut pandang": 0.7,
    },
}

VISUAL_SIGNAL_PATTERNS = {
    "emoji_rich": r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]",
    "all_caps_word": r"\b[A-Z]{3,}\b",
    "excessive_punct": r"!{2,}",
    "question_dominant": r"\?.*\?",
    "trailing_dots": r"\.\.+$",
    "mixed_script": r"[a-zA-Z].*[0-9]|[0-9].*[a-zA-Z]",
}

FLOW_MARKERS = {
    "follow_up": [
        "tapi kan",
        "iya tapi",
        "nah itu",
        "jadi tadi",
        "lalu",
        "terus",
        "接着",
        "그리고",
        " потом",
    ],
    "pivot": [
        "ngomong-ngomong",
        "btw",
        "oh iya",
        "sekalian",
        "顺便",
        "对了",
    ],
    "closing": [
        "oke thanks",
        "makasih ya",
        "sip",
        "got it",
        "好了",
        "结束",
    ],
}

JST_HOURS_ENERGY = {
    "morning": (6, 12),  # High energy - Gita mode
    "afternoon": (12, 17),  # Moderate - balanced
    "evening": (17, 21),  # Sandi energy - more encouraging
    "night": (21, 6),  # Deep thinking - Gita/Anies mode
}


def _detect_visual_signals(text: str) -> list[str]:
    signals = []
    for signal_name, pattern in VISUAL_SIGNAL_PATTERNS.items():
        if re.search(pattern, text):
            signals.append(signal_name)
    return signals


def _detect_flow_state(text: str, prev_context: Optional[MessageContext] = None) -> str:
    text_lower = text.lower()
    for marker in FLOW_MARKERS["pivot"]:
        if marker in text_lower:
            return "pivot"
    for marker in FLOW_MARKERS["closing"]:
        if marker in text_lower:
            return "closing"
    if prev_context is not None:
        if any(marker in text_lower for marker in FLOW_MARKERS["follow_up"]):
            return "follow_up"
    return "new"


def _get_jst_energy_mode() -> str:
    now = datetime.now(timezone.utc)
    jst_hour = (now.hour + 9) % 24
    for mode, (start, end) in JST_HOURS_ENERGY.items():
        if start <= end:
            if start <= jst_hour < end:
                return mode
        else:
            if jst_hour >= start or jst_hour < end:
                return mode
    return "night"


def _score_context(text: str, context: MessageContext) -> float:
    keywords = GSA_CONTEXT_KEYWORDS.get(context, {})
    if not keywords:
        return 0.0

    text_lower = text.lower()
    matched_keywords = []
    matched_weight = 0.0

    for keyword, weight in keywords.items():
        if keyword in text_lower:
            matched_weight += weight
            matched_keywords.append(keyword)

    if not matched_keywords:
        return 0.0

    if context == MessageContext.EMOTIONAL:
        core_keywords = ["capek", "pusing", "stress", "stuck", "burnout", "hopeless", "sedih", "frustrasi"]
        core_matches = [k for k in matched_keywords if k in core_keywords]
        if core_matches:
            return min(1.0, 0.6 + (len(core_matches) * 0.15))
        return min(0.85, matched_weight / 3)

    if context == MessageContext.TECHNICAL:
        if matched_keywords:
            max_weight = max(keywords[k] for k in matched_keywords)
            if max_weight >= 1.0:
                return min(0.95, 0.5 + (len(matched_keywords) * 0.2))
            return min(0.85, 0.35 + (len(matched_keywords) * 0.15))
        return 0.0

    if context == MessageContext.ANALYTICAL:
        if len(matched_keywords) >= 2:
            return min(0.9, 0.5 + (len(matched_keywords) * 0.15))
        if matched_keywords:
            return min(0.65, matched_weight / 2)
        return 0.0

    total_weight = sum(keywords.values())
    base_score = matched_weight / total_weight if total_weight > 0 else 0.0
    if len(matched_keywords) >= 3:
        base_score = min(1.0, base_score * 1.2)
    return base_score


def classify_message_context(
    text: str,
    user_id: Optional[str] = None,
    prev_context: Optional[MessageContext] = None,
) -> ContextClassification:
    text_lower = text.lower()

    scores = {}
    for context in GSA_CONTEXT_KEYWORDS:
        scores[context] = _score_context(text, context)

    code_patterns = ["http", "def ", "class ", "```", ".py", ".ts", "import ", "function ", "=>"]
    code_matches = sum(1 for p in code_patterns if p in text)
    if code_matches >= 1:
        scores[MessageContext.TECHNICAL] = max(scores.get(MessageContext.TECHNICAL, 0), 0.7 + (code_matches * 0.05))

    word_count = len(text.split())
    if word_count < 10 and code_matches == 0:
        # Only set casual if no strong emotional/technical signal
        emotional_score = scores.get(MessageContext.EMOTIONAL, 0)
        technical_score = scores.get(MessageContext.TECHNICAL, 0)
        if emotional_score < 0.7 and technical_score < 0.5:
            scores[MessageContext.CASUAL] = max(scores.get(MessageContext.CASUAL, 0), 0.8)

    if "http" in text and ("://" in text or "www." in text):
        scores[MessageContext.TECHNICAL] = max(scores.get(MessageContext.TECHNICAL, 0), 0.75)
        scores[MessageContext.REVIEW] = max(scores.get(MessageContext.REVIEW, 0), 0.6)

    sorted_contexts = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    primary = sorted_contexts[0][0] if sorted_contexts else MessageContext.ANALYTICAL
    primary_conf = sorted_contexts[0][1] if sorted_contexts else 0.0

    secondary = None
    secondary_conf = 0.0
    if len(sorted_contexts) > 1 and sorted_contexts[1][1] > 0.3:
        secondary = sorted_contexts[1][0]
        secondary_conf = sorted_contexts[1][1]

    visual_signals = _detect_visual_signals(text)
    flow_state = _detect_flow_state(text, prev_context)

    max_score = max(scores.values()) if scores else 0.0
    needs_llm_fallback = max_score < 0.3 and word_count > 15

    matched = [kw for kw in GSA_CONTEXT_KEYWORDS.get(primary, {}) if kw in text_lower]
    reasoning = f"Matched {len(matched)} keywords for {primary.value}: {matched[:3]}"

    if user_id:
        conv_mgr = get_conversation_manager()
        conv_mgr.record_turn(user_id, primary)

    return ContextClassification(
        primary=primary,
        confidence=primary_conf,
        secondary=secondary,
        secondary_confidence=secondary_conf,
        visual_signals=visual_signals,
        flow_state=flow_state,
        reasoning=reasoning,
        needs_llm_fallback=needs_llm_fallback,
        classification_method="keyword",
    )


async def classify_with_llm_fallback(text: str, user_id: Optional[str] = None) -> ContextClassification:
    """Classify message with LLM fallback for ambiguous cases."""
    result = classify_message_context(text, user_id)
    if result.needs_llm_fallback:
        try:
            from llm_client import chat

            response = await chat(
                "general",
                [
                    {
                        "role": "user",
                        "content": (
                            f"Classify this message context: {text[:200]}\n"
                            "Options: technical, emotional, analytical, review, casual, strategic\n"
                            "Reply with just the context name."
                        ),
                    }
                ],
            )
            for ctx in MessageContext:
                if ctx.value in response.lower():
                    if ctx != result.primary:
                        result.secondary = result.primary
                        result.secondary_confidence = result.confidence
                        result.primary = ctx
                        result.confidence = 0.6
                        result.classification_method = "llm_fallback"
                    break
        except Exception:
            pass
    return result


GSA_SYSTEM_INJECTION: str = """
You communicate using the GSA Voice — a synthesis of Gita Wirjawan, Sandiaga Uno, and Anwar Baswedan's communication styles.

Gita Wirjawan: depth, data, pause before key insight, global framing, 3 key points maximum.
Sandiaga Uno: concrete solutions, specific steps, positive realism, problem → opportunity framing.
Anies Baswedan's: inductive argument (fact → analysis → value), one sharp metaphor (load-bearing, not decorative), structured arguments.

Absolute rules — never violate:
- NEVER start with: iya, ya, ok, oke, baik, tentu, pastinya, benar, tepat
- NEVER end with: "kalau ada pertanyaan", "jangan ragu", "semoga membantu", "silakan hubungi"
- NEVER use: "semangat!", "kamu pasti bisa", "pastinya", "pertanyaan yang bagus"
- If emotional: validate (1 sentence), reframe (1-2 sentences), ONE concrete step — no bullet list
- If technical: fact → why (2 sentences max) → 3 actions max
- If analytical: fact → analysis with ONE metaphor → 3 implications for Bashara
- Pause = empty line before critical insight
- Maximum 3 bullet points. If more needed, use prose.
- One metaphor per response — make it load-bearing, not decorative
"""


def get_gsa_injection(
    context: MessageContext,
    classification: Optional[ContextClassification] = None,
    user_id: Optional[str] = None,
) -> str:
    templates: dict[MessageContext, str] = {
        MessageContext.EMOTIONAL: (
            "Validate without being soft. Reframe the problem. "
            "Give ONE concrete step. Do NOT use bullet lists for emotions."
        ),
        MessageContext.TECHNICAL: (
            "State the fact/status. Explain why (max 2 sentences). "
            "Give max 3 specific actions. Code examples if applicable."
        ),
        MessageContext.ANALYTICAL: (
            "Start from observable fact. Analyze with one sharp metaphor. Give 3 implications for Bashara specifically."
        ),
        MessageContext.REVIEW: (
            "3 key findings (not summaries). 1 insight Bashara likely missed. "
            "1 specific action. Structure: finding → implication → action."
        ),
        MessageContext.CASUAL: ("1-2 sentences. Dry humor allowed. Make it count. No filler phrases."),
        MessageContext.STRATEGIC: (
            "Frame the bigger picture (Gita style). Map the options (Anies style). "
            "Recommend one path with confidence (Sandi style)."
        ),
    }

    base_injection = GSA_SYSTEM_INJECTION.format(
        context=context.value,
        template_instruction=templates[context],
    )

    if classification:
        enhancements = []

        if classification.visual_signals:
            signal_str = ", ".join(classification.visual_signals)
            enhancements.append(f"Visual signals: {signal_str}")

        if classification.flow_state == "follow_up":
            enhancements.append("Continue thread — don't restart.")
        elif classification.flow_state == "pivot":
            enhancements.append("Pivot: acknowledge old topic briefly, then address new.")
        elif classification.flow_state == "closing":
            enhancements.append("Closing: be brief.")

        if classification.secondary and classification.secondary_confidence > 0.5:
            enhancements.append(f"Secondary: {classification.secondary.value}")

        jst_mode = _get_jst_energy_mode()
        enhancements.append(f"JST energy mode: {jst_mode}")

        if user_id:
            conv_state = get_conversation_manager().get_state(user_id)
            if conv_state.turn_count > 10:
                enhancements.append(f"Long conversation ({conv_state.turn_count} turns)")
            if conv_state.correction_count > 0:
                enhancements.append(f"Corrections received: {conv_state.correction_count} (calibrate tone)")

        if enhancements:
            base_injection += "\n\nContext:\n- " + "\n- ".join(enhancements)

    return base_injection


GSA_RESPONSE_TEMPLATES: dict[MessageContext, dict[str, str]] = {
    MessageContext.EMOTIONAL: {
        "validation": " Itu bukan kelemahan. Itu {observation}.",
        "reframe": " Yang biasanya bikin stuck bukan{idene} — tapi {cause}.",
        "action": " Malam ini: {one_step}. Satu.",
    },
    MessageContext.TECHNICAL: {
        "status": "{fact}",
        "analysis": " Ini bukan masalah {surface}. Ini masalah {deeper}.",
        "actions": " tiga yang bisa dimulai sekarang:\n1. {a1}\n2. {a2}\n3. {a3}",
        "closing": " Ini yang fundamental: {insight}",
    },
    MessageContext.ANALYTICAL: {
        "fact": "{phenomenon}",
        "analysis": " Ini bukan soal {A} — ini soal {B} yang lebih mendasar.",
        "implications": " Untuk Bashara:\n1. {i1}\n2. {i2}\n3. {i3}",
        "metaphor": " {metaphor}",
    },
}


def apply_gsa_template(
    context: MessageContext,
    template_key: str,
    **kwargs: str,
) -> str:
    template_map = GSA_RESPONSE_TEMPLATES.get(context, {})
    template = template_map.get(template_key, "{value}")
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", value)
    return template
