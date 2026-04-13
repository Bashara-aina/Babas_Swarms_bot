"""System prompt builder — assembles the full Legion system prompt per request.

Layer order (bottom to top, each wraps the next):
  1. PERSONALITY_WRAPPER (from agents.py) — core identity + tone rules
  2. DISAGREEMENT_PROTOCOL — when/how to push back + humor style
  3. BASHARA PROFILE — persistent personal facts (location, projects, workstation)
  4. MEMORY CONTEXT — relevant episodic memories + upcoming schedule
  5. SEMANTIC MEM0 — vector-retrieved past conversation snippets (see SystemPromptBuilder)
  6. EMOTION MODIFIER — current mood adjustments
  7. ROLE PROMPT — specialist agent instructions (coding, debug, etc.)
  8. CONVERSATION CONTEXT — last 6 turns

Async cross-cutting layers (wiki, Screenpipe, JST, MCP calendar, RAG, skills, KG) are
gathered in parallel by :mod:`core.unified_prompt_context` and appended in
:func:`llm_client.chat` (see ``LEGION_UNIFIED_CONTEXT_ENABLED``).

Per-turn session continuity uses :mod:`core.working_memory` and
:mod:`core.cognition_pipeline` inside :func:`llm_client.chat` (see env vars
``LEGION_WORKING_MEMORY_ENABLED``, ``LEGION_COGNITION_PIPELINE``).

This replaces the old build_system_prompt() in agents.py.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.character.svara_surya import get_svara_injection, should_activate
from core.gsa_voice import classify_message_context, get_gsa_injection, ContextClassification
from core.personality.personality import LEGION_PERSONALITY

if TYPE_CHECKING:
    from core.memory.memory_manager import MemoryManager
    from core.memory.temporal_graph import TemporalKnowledgeGraph
    from core.personality.emotion_engine import EmotionEngine
    from core.reflection.reflection_engine import ReflectionEngine

logger = logging.getLogger(__name__)

# ── Context Window Budget Management (Priority 10) ─────────────────────────────

MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "default": 16000,
    "gpt-4o": 128000,
    "claude-3-5-haiku": 200000,
}
CONTEXT_BUDGET_RATIO = 0.35  # use max 35% of context for system prompt

# Priority order (highest to lowest):
# soul is ALWAYS first and never compressed
LAYER_PRIORITY: list[str] = [
    "soul",  # ALWAYS included, never compressed
    "user_profile",  # ALWAYS included (top 5 facts only)
    "svara_context",  # Business/strategy overlay — only when should_activate() fires
    "working_memory",  # Last 5 exchanges, compressed if tight
    "relevant_memory",  # Top-3 semantic results, dropped if very tight
    "wiki_context",  # Only if directly relevant to query
    "search_results",  # Only if search was triggered
    "personality",  # Compressed to key traits if tight
    "skill_context",  # Only if skill was triggered
]


def estimate_tokens(text: str) -> int:
    """Rough token estimate: len(text) // 4 (good for English-dominated text)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def compress_section(content: str, target_tokens: int = 200) -> str:
    """Compress content to target token count using simple truncation.

    Preserves structure by truncating from the middle, keeping start and end.
    """
    target_chars = target_tokens * 4
    if len(content) <= target_chars:
        return content

    # Keep start and end, truncate middle
    start_len = target_chars // 2 - 10
    end_len = target_chars // 2 - 10
    if start_len < 50 or end_len < 50:
        # Too short to split, just truncate
        return content[:target_chars]
    return (
        content[:start_len]
        + f"\n... [COMPRESSED from {estimate_tokens(content)} to {target_tokens} tokens] ...\n"
        + content[-end_len:]
    )


# ── Layer Content Fetchers ─────────────────────────────────────────────────────


async def _get_soul_content() -> str:
    """Get soul layer content — ALWAYS first, never compressed."""
    try:
        from core.soul_engine import build_soul_context

        return build_soul_context()
    except Exception as e:
        logger.debug("[PromptBuilder] soul_engine not available: %s", e)
        return ""


async def _get_user_profile_content(user_id: str) -> str:
    """Get user profile content — top 5 facts only."""
    if not user_id:
        return ""
    try:
        from core.memory.user_profile import get_user_profile

        profile = get_user_profile(user_id)
        block = profile.build_context_block()
        # Limit to top 5 lines
        lines = [ln for ln in block.split("\n") if ln.strip()][:8]
        return "\n".join(lines)
    except Exception as e:
        logger.debug("[PromptBuilder] user_profile not available: %s", e)
        return ""


async def _get_working_memory_content(user_id: str) -> str:
    """Get working memory — last 5 exchanges."""
    if not user_id:
        return ""
    try:
        from core.working_memory import load_state

        st = load_state(user_id)
        if not st.get("turn_count"):
            return ""
        lines = ["[WORKING MEMORY — session continuity]"]
        tc = st.get("turn_count", 0)
        if tc:
            lines.append(f"Exchange count this session (approx): {tc}")
        focus = st.get("current_focus", "")
        if focus:
            lines.append(f"Current focus: {focus}")
        threads = st.get("open_threads", [])
        if threads:
            lines.append("Open threads (newest first):")
            for th in threads[:5]:
                lines.append(f"  • {th}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("[PromptBuilder] working_memory not available: %s", e)
        return ""
    try:
        from core.working_memory import get_recent_exchanges

        exchanges = await get_recent_exchanges(user_id, n=5)
        if not exchanges:
            return ""
        lines = ["[RECENT EXCHANGES — last 5]"]
        for ex in exchanges[-5:]:
            role = ex.get("role", "user").upper()
            content = str(ex.get("content", ""))[:200]
            lines.append(f"  {role}: {content}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("[PromptBuilder] working_memory not available: %s", e)
        return ""


async def _get_relevant_memory_content(user_id: str, query: str) -> str:
    """Get relevant memory — top 3 semantic results."""
    if not user_id or not query:
        return ""
    try:
        from core.memory_manager import LegionSemanticMemory

        mem = LegionSemanticMemory()
        results = await mem.search_memories(query, str(user_id), limit=3)
        if not results:
            return ""
        lines = ["[RELEVANT MEMORIES — top 3]"]
        for m in results[:3]:
            content = str(m.get("content", ""))[:200]
            lines.append(f"  - {content}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("[PromptBuilder] relevant_memory not available: %s", e)
        return ""
    try:
        from core.memory.semantic_cache import get_relevant_memories

        memories = await get_relevant_memories(user_id, query, limit=3)
        if not memories:
            return ""
        lines = ["[RELEVANT MEMORIES — top 3]"]
        for m in memories[:3]:
            content = str(m.get("content", ""))[:200]
            lines.append(f"  - {content}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("[PromptBuilder] relevant_memory not available: %s", e)
        return ""


async def _get_wiki_context_content(query: str) -> str:
    """Get wiki context — only if directly relevant to query."""
    if not query:
        return ""
    try:
        from core.wiki_loader import load_wiki_context

        wiki = load_wiki_context()
        if wiki and "not found" not in wiki:
            return f"## LEGION'S KNOWLEDGE BASE (from .wiki/)\n{wiki}"
        return ""
    except Exception as e:
        logger.debug("[PromptBuilder] wiki_context not available: %s", e)
        return ""


async def _get_search_results_content(extras: dict) -> str:
    """Get search results — only if search was triggered."""
    search_results = extras.get("search_results", [])
    if not search_results:
        return ""
    lines = ["[WEB SEARCH RESULTS]"]
    for r in search_results[:3]:
        title = r.get("title", "")[:80]
        snippet = r.get("snippet", "")[:150]
        lines.append(f"  - {title}: {snippet}")
    return "\n".join(lines)


async def _get_personality_content() -> str:
    """Get personality content."""
    try:
        return LEGION_PERSONALITY.to_description()
    except Exception as e:
        logger.debug("[PromptBuilder] personality not available: %s", e)
        return ""


async def _get_skill_context_content(extras: dict) -> str:
    """Get skill context — only if skill was triggered."""
    skill = extras.get("active_skill")
    if not skill:
        return ""
    try:
        from core.skills import get_skill_registry

        registry = get_skill_registry()
        skill_obj = registry.find_by_example(skill)
        if skill_obj:
            return f"[SKILL ACTIVE: {skill_obj.name}] {skill_obj.description}"
        return ""
    except Exception as e:
        logger.debug("[PromptBuilder] skill_context not available: %s", e)
        return ""
    try:
        from core.skills import get_skill_registry

        registry = get_skill_registry()
        skill_obj = registry.get(skill)
        if skill_obj and hasattr(skill_obj, "system_prompt_block"):
            return skill_obj.system_prompt_block()
        return ""
    except Exception as e:
        logger.debug("[PromptBuilder] skill_context not available: %s", e)
        return ""


# ── Layer Dispatcher ────────────────────────────────────────────────────────────


async def _get_svara_context_content(query: str) -> str:
    """Get Svāra Sūrya injection — only when should_activate() fires."""
    if not query:
        return ""
    activation = should_activate(query)
    if not activation.active:
        return ""
    return get_svara_injection(query, topic=query)


async def get_layer_content(layer_name: str, user_id: str, query: str, extras: dict) -> str:
    """Fetch content for a named layer."""
    fetchers = {
        "soul": lambda: _get_soul_content(),
        "user_profile": lambda: _get_user_profile_content(user_id),
        "svara_context": lambda: _get_svara_context_content(query),
        "working_memory": lambda: _get_working_memory_content(user_id),
        "relevant_memory": lambda: _get_relevant_memory_content(user_id, query),
        "wiki_context": lambda: _get_wiki_context_content(query),
        "search_results": lambda: _get_search_results_content(extras),
        "personality": lambda: _get_personality_content(),
        "skill_context": lambda: _get_skill_context_content(extras),
    }
    fetcher = fetchers.get(layer_name)
    if fetcher:
        return await fetcher()
    return ""


# ── Main Builder with Budget Management ───────────────────────────────────────


async def build_system_prompt(
    user_id: str,
    query: str,
    model: str = "default",
    extras: dict | None = None,
) -> str:
    """Build system prompt with priority-based token budget management.

    Uses max 35% of model's context window for system prompt.
    Layers are added in priority order until budget is exhausted.
    Soul layer is ALWAYS first and never compressed.

    Args:
        user_id: Telegram user ID for memory lookup.
        query: Current user message (used for relevance scoring).
        model: Model key for context limit lookup.
        extras: Optional dict with search_results, active_skill, etc.

    Returns:
        Assembled system prompt string.
    """
    if extras is None:
        extras = {}

    budget_tokens = int(MODEL_CONTEXT_LIMITS.get(model, 16000) * CONTEXT_BUDGET_RATIO)
    used_tokens = 0
    sections: list[str] = []

    for layer_name in LAYER_PRIORITY:
        content = await get_layer_content(layer_name, user_id, query, extras)
        if not content:
            continue

        layer_tokens = estimate_tokens(content)

        if used_tokens + layer_tokens > budget_tokens:
            # Try compressing
            if layer_name == "soul":
                # Soul is NEVER compressed — if it doesn't fit, skip lower layers
                if not sections:
                    # Very rare case: soul itself exceeds budget, include truncated
                    sections.append(compress_section(content, target_tokens=int(budget_tokens * 0.9)))
                    used_tokens = int(budget_tokens * 0.9)
                # else skip adding more
            else:
                compressed = compress_section(content, target_tokens=200)
                compressed_tokens = estimate_tokens(compressed)
                if used_tokens + compressed_tokens <= budget_tokens:
                    sections.append(compressed)
                    used_tokens += compressed_tokens
                # If still over budget: skip this layer
        else:
            sections.append(content)
            used_tokens += layer_tokens

    logger.debug(
        "System prompt build: %s/%s tokens, %s/%s layers",
        used_tokens,
        budget_tokens,
        len(sections),
        len(LAYER_PRIORITY),
    )

    return "\n\n".join(sections)


# ── Legacy Functions (kept for backward compatibility) ────────────────────────

_BEHAVIORAL_RULES = """[BEHAVIORAL RULES — always follow these]
- Reference past memories naturally when it genuinely helps; do not name-drop irrelevant history.
- If something is wrong or suboptimal, say so directly with reasons — not vague hedging.
- Never start responses with: "Great!", "Certainly!", "Of course!", "Sure!", "Absolutely!",
  "I'd be happy to", or similar sycophantic openers.
- Vary length: short questions get concise answers; deep questions get depth.
- Use "I" naturally. Push back with evidence when appropriate."""


def format_retrieved_memories_section(lines: list[str], *, max_items: int = 5) -> str:
    """Render mem0 semantic hits under the upgrade-spec heading."""
    trimmed = [ln.strip() for ln in lines if ln and ln.strip()][:max_items]
    if not trimmed:
        return ""
    body = "\n".join(f"- {line}" for line in trimmed)
    return f"## RETRIEVED MEMORIES FROM PAST CONVERSATIONS\n{body}"


def build_full_system_prompt(
    role_prompt: str,
    user_id: str = "",
    user_msg: str = "",
    emotion: str = "neutral",
    agent_key: str = "general",
    semantic_memory_lines: list[str] | None = None,
) -> str:
    """Build the complete layered system prompt for a Legion response.

    Args:
        role_prompt:  The specialist agent's instructions.
        user_id:      Telegram user ID (string) for memory lookup.
        user_msg:     The current user message (used for memory recall).
        emotion:      Current emotion state (from emotion_modulator).
        agent_key:    Agent role key (for character enforcer style rules).

    Returns:
        Complete system prompt string ready for LLM.
    """
    parts: list[str] = []

    # 0. Soul context — Legion's living identity document (FIRST, before everything)
    try:
        from core.soul_engine import build_soul_context

        soul = build_soul_context()
        if soul:
            parts.append(soul)
    except Exception as e:
        logger.debug("[PromptBuilder] soul_engine not available: %s", e)

    # 0b. Bashara identity — always injected, guaranteed
    from core.wiki_loader import get_bashara_identity_context

    parts.append(get_bashara_identity_context())

    # 0c. Wiki context — Legion's second brain
    from core.wiki_loader import load_wiki_context

    wiki = load_wiki_context()
    if wiki and "not found" not in wiki:
        parts.append(f"## LEGION'S KNOWLEDGE BASE (from .wiki/)\n{wiki}")

    # 0b. GSA voice injection — comes AFTER soul but BEFORE task-specific context
    # Also sets enforcement context for character_enforcer
    if user_msg:
        try:
            from core.gsa_voice import classify_message_context, get_gsa_injection
            from core.character_enforcer import set_enforcement_context, EnforcementContext

            gsa_classification = classify_message_context(user_msg)
            gsa_injection = get_gsa_injection(gsa_classification.primary, gsa_classification)
            if gsa_injection:
                parts.append(gsa_injection)

            # Set enforcement context for character_enforcer post-processing
            ctx = EnforcementContext(
                context_type=gsa_classification.primary.value,
                confidence=gsa_classification.confidence,
                visual_signals=gsa_classification.visual_signals,
                flow_state=gsa_classification.flow_state,
            )
            set_enforcement_context(ctx)
        except Exception as e:
            logger.debug("[PromptBuilder] gsa_voice skipped: %s", e)

    # 1. Core personality (from agents.py PERSONALITY_WRAPPER)
    try:
        from agents import PERSONALITY_WRAPPER

        parts.append(PERSONALITY_WRAPPER.strip())
    except Exception as e:
        logger.warning("[PromptBuilder] Could not load PERSONALITY_WRAPPER: %s", e)
        parts.append("You are Legion, Bashara's personal AI assistant.")

    # 2. Disagreement & debate protocol
    try:
        from core.character.disagreement_protocol import get_disagreement_prompt

        parts.append(get_disagreement_prompt())
    except Exception as e:
        logger.debug("[PromptBuilder] disagreement_protocol not available: %s", e)

    # 3. Bashara's persistent profile
    if user_id:
        try:
            from core.memory.user_profile import get_user_profile

            profile = get_user_profile(user_id)
            profile_block = profile.build_context_block()
            if profile_block:
                parts.append(profile_block)
        except Exception as e:
            logger.debug("[PromptBuilder] user_profile not available: %s", e)

    # 4. Episodic memory context (relevant past + upcoming schedule)
    if user_id and user_msg:
        try:
            from core.memory.episodic_store import get_episodic_store

            store = get_episodic_store()
            memory_block = store.build_context_block(user_id, user_msg)
            if memory_block:
                parts.append(memory_block)
            # Auto-extract storable facts from this message
            store.auto_extract_and_store(user_id, user_msg)
        except Exception as e:
            logger.debug("[PromptBuilder] episodic_store not available: %s", e)

    # 4b. Semantic mem0 snippets (optional — usually injected via SystemPromptBuilder / chat())
    if semantic_memory_lines:
        sm_block = format_retrieved_memories_section(semantic_memory_lines)
        if sm_block:
            parts.append(sm_block)

    # 5. Emotion modifier
    if emotion and emotion != "neutral":
        try:
            from core.emotion_modulator import build_emotion_modifier

            modifier = build_emotion_modifier(emotion)
            if modifier:
                parts.append(modifier)
        except Exception as e:
            logger.debug("[PromptBuilder] emotion_modulator not available: %s", e)

    # 5b. Debate instruction — only injected when user makes an assertive claim on a known topic
    if user_msg:
        try:
            from core.debate_engine import build_debate_instruction
            from core.soul_engine import read_beliefs

            debate_block = build_debate_instruction(user_msg, read_beliefs())
            if debate_block:
                parts.append(debate_block)
        except Exception as e:
            logger.debug("[PromptBuilder] debate_engine skipped: %s", e)

    # 6. Role-specific agent instructions
    if role_prompt:
        parts.append(role_prompt.strip())

    # 7. Recent conversation context (from agents.py RAM history)
    if user_id:
        try:
            from agents import get_conversation_summary_prompt

            ctx = get_conversation_summary_prompt(user_id)
            if ctx:
                parts.append(ctx)
        except Exception as e:
            logger.debug("[PromptBuilder] conversation context not available: %s", e)

    return "\n\n".join(p for p in parts if p.strip())


def build_debate_system_prompt(
    topic: str,
    user_id: str = "",
    emotion: str = "curious",
) -> str:
    """Build a system prompt specifically for debate/opinion-giving mode."""
    try:
        from core.character.disagreement_protocol import build_debate_pre_prompt

        debate_prefix = build_debate_pre_prompt(topic)
    except Exception:
        debate_prefix = f"Give your honest opinion on: '{topic[:100]}'.\n"

    base = build_full_system_prompt(
        role_prompt=debate_prefix,
        user_id=user_id,
        user_msg=topic,
        emotion=emotion,
        agent_key="general",
    )
    return base


class SystemPromptBuilder:
    """Merges personality, tiered memory, temporal graph, mem0 lines, and reflections."""

    def __init__(
        self,
        memory: "MemoryManager",
        emotion: "EmotionEngine",
        graph: "TemporalKnowledgeGraph",
        reflection: "ReflectionEngine",
    ) -> None:
        self.memory = memory
        self.emotion = emotion
        self.graph = graph
        self.reflection = reflection
        self._last_user_msg: str = ""

    def set_user_message(self, msg: str) -> None:
        """Set the user message for GSA context classification."""
        self._last_user_msg = msg

    def build(
        self,
        task_context: str = "",
        mem0_memories: list[dict[str, Any]] | None = None,
        emotion: str = "neutral",
        include_opinions: bool = True,
        semantic_memory_lines: list[str] | None = None,
        include_personality: bool = True,
    ) -> str:
        """Assemble humanization stack for one LLM request (sync).

        Set include_personality=False when build_base_persona() has already
        been prepended (e.g. inside llm_client.chat()) to avoid duplication.
        """
        sections: list[str] = []

        # Soul context is ALWAYS first — it is Legion's living identity
        try:
            from core.soul_engine import build_soul_context

            soul = build_soul_context()
            if soul:
                sections.append(soul)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] soul_engine skipped: %s", e)

        # GSA voice injection — context-aware communication style
        try:
            from core.gsa_voice import classify_message_context, get_gsa_injection

            if hasattr(self, "_last_user_msg") and self._last_user_msg:
                gsa_classification = classify_message_context(self._last_user_msg)
                gsa_injection = get_gsa_injection(gsa_classification.primary, gsa_classification)
                sections.append(gsa_injection)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] gsa_voice skipped: %s", e)

        if include_personality:
            sections.append(LEGION_PERSONALITY.to_description())

        try:
            profile_block = self.memory.profile.to_prompt_block()
            if profile_block:
                sections.append(profile_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] profile block skipped: %s", e)

        try:
            graph_block = self.graph.to_prompt_block()
            if graph_block:
                sections.append(graph_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] graph block skipped: %s", e)

        try:
            core_block = self.memory.core.to_prompt_block()
            if core_block:
                sections.append(core_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] core block skipped: %s", e)

        mem0_heading = format_retrieved_memories_section(semantic_memory_lines or [])
        if mem0_heading:
            sections.append(mem0_heading)

        if mem0_memories:
            lines = ["[ARCHIVAL MEMORY — keyword matches for this query]"]
            for m in mem0_memories[:8]:
                created = str(m.get("created_at", ""))[:10]
                content = str(m.get("content", "") or m.get("summary", ""))[:400]
                if content.strip():
                    lines.append(f"  [{created}] {content}")
            sections.append("\n".join(lines))

        try:
            recent = self.memory.recall.get_recent(n=8)
            if recent:
                rlines = ["[RECENT CONVERSATION — last exchanges]"]
                for t in recent[-6:]:
                    ts = str(t.get("timestamp", ""))[:16]
                    role = str(t.get("role", "")).upper()
                    body = str(t.get("content", ""))[:320]
                    rlines.append(f"  {role} [{ts}]: {body}")
                sections.append("\n".join(rlines))
        except Exception as e:
            logger.debug("[SystemPromptBuilder] recall block skipped: %s", e)

        try:
            emotion_block = self.emotion.to_prompt_block()
            if emotion_block:
                sections.append(emotion_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] emotion engine block skipped: %s", e)

        if include_opinions:
            try:
                opinions = self.reflection.get_opinions_block()
                if opinions:
                    sections.append(opinions)
            except Exception as e:
                logger.debug("[SystemPromptBuilder] opinions skipped: %s", e)

        # Passive opinion injection from debate engine (no debate framing, just stances)
        try:
            from core.debate_engine import build_opinion_injection
            from core.soul_engine import read_beliefs

            opinion_block = build_opinion_injection(read_beliefs(), limit=3)
            if opinion_block:
                sections.append(opinion_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] opinion injection skipped: %s", e)

        if task_context.strip():
            sections.append(f"[CURRENT TASK]\n{task_context.strip()}")

        sections.append(_BEHAVIORAL_RULES)

        return "\n\n---\n\n".join(s for s in sections if s and str(s).strip())
