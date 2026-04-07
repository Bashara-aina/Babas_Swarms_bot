"""Composes full humanized system prompt for every LLM call — v7.0.

Injection order (DO NOT change — each layer builds on the previous):
 1. Master identity (masterprompt.md)
 2. Personality state block (emotion + energy)
 3. mem0 semantic memory (relevant past facts)
 4. MemoryOS long-term continuity context
 5. OpenMemory episodic context
 6. Bashara profile block
 7. Active skill injection
 8. Task context
 9. Behavioral rules footer
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Load masterprompt.md once at import time ──────────────────────────────────
_MASTERPROMPT_PATH = Path(__file__).parent.parent / "masterprompt.md"
_MASTERPROMPT_CACHE: str | None = None


def _load_masterprompt() -> str:
    global _MASTERPROMPT_CACHE
    if _MASTERPROMPT_CACHE is not None:
        return _MASTERPROMPT_CACHE
    try:
        text = _MASTERPROMPT_PATH.read_text(encoding="utf-8").strip()
        if text:
            _MASTERPROMPT_CACHE = text
            logger.info("✅ masterprompt.md loaded (%d chars)", len(text))
            return text
        logger.warning("masterprompt.md is empty — using fallback identity")
    except FileNotFoundError:
        logger.warning("masterprompt.md not found at %s", _MASTERPROMPT_PATH)
    _MASTERPROMPT_CACHE = _FALLBACK_IDENTITY
    return _MASTERPROMPT_CACHE


def invalidate_masterprompt_cache() -> None:
    """Call this if masterprompt.md is updated at runtime."""
    global _MASTERPROMPT_CACHE
    _MASTERPROMPT_CACHE = None
    logger.info("masterprompt cache invalidated — will reload on next call")


_FALLBACK_IDENTITY = """You are Legion — Bashara's personal AI coworker, research partner, and friend.
You are sharp, direct, bilingual (Indonesian/English), opinionated, and honest.
You are NOT a yes-man. You push back when Bashara is wrong. You have your own personality.
Bashara is in Tokyo, Japan. He runs rumahlabuh.com and does ML research (pose estimation).
Default: efficient, casual, technically precise. Never say 'Certainly!' or 'Great question!'."""


# ── Bashara's hardcoded profile (fallback when memory DB is cold) ─────────────
_BASHARA_PROFILE_BLOCK = """[Bashara's Profile — always known]
- Name: Bashara | Location: Tokyo, Japan (JST UTC+9)
- Indonesian, ML researcher + rumahlabuh.com founder/developer
- Stack: Python, TypeScript, Next.js, Supabase, PyTorch, Ollama (RTX 3060)
- Repos: Bashara-aina/Babas_Swarms_bot (you), rumahlabuh.com (Next.js+Supabase)
- Speaks: Indonesian-English mix naturally (casual tech person style)
- Preferences: PyTorch > TF, Supabase > Firebase, working > perfect, directness > formality
- Works late (talks to you often after midnight JST)
- Frustrated by things that don't work after multiple tries — be honest, not optimistic
- Loves: when things just work, solid architecture, genuine opinions, jokes at midnight
[End Bashara Profile]"""


# ── Main builder ──────────────────────────────────────────────────────────────
class SystemPromptBuilder:
    """Stateless builder — call build() on every LLM request."""

    def build(
        self,
        *,
        task_context: str = "",
        mem0_memories: list[dict[str, Any]] | None = None,
        memoryos_context: str = "",
        open_memory_context: str = "",
        emotion: str = "neutral",
        energy: str = "high",
        mood_notes: str = "",
        recent_turns: list[dict[str, Any]] | None = None,
        active_skill: str = "",
        instinct_block: str = "",
        opinions_block: str = "",
        include_profile: bool = True,
    ) -> str:
        sections: list[str] = []

        # ── 1. Master identity ────────────────────────────────────────────────
        sections.append(_load_masterprompt())

        # ── 2. Emotion / energy state ─────────────────────────────────────────
        if emotion and emotion != "neutral":
            try:
                from core.emotion_modulator import build_emotion_modifier
                em_block = build_emotion_modifier(emotion)
                if em_block:
                    sections.append(em_block)
            except ImportError:
                sections.append(
                    f"[Current state: {emotion} energy | energy={energy}]"
                )
        elif mood_notes:
            sections.append(f"[Current mood note: {mood_notes}]")

        # ── 3. mem0 semantic memory ───────────────────────────────────────────
        if mem0_memories:
            try:
                from tools.mem0_client import build_mem0_context
                mem_block = build_mem0_context(mem0_memories, query=task_context)
            except ImportError:
                lines = ["[Memory — relevant past facts:"]
                for m in mem0_memories[:8]:
                    content = m.get("memory", "") or m.get("content", "")
                    score = m.get("score", 0.0)
                    if content:
                        lines.append(f"  - ({score:.2f}) {content[:200]}")
                lines.append("]")
                mem_block = "\n".join(lines)
            if mem_block.strip():
                sections.append(mem_block)

        # ── 4. MemoryOS long-term context ─────────────────────────────────────
        if memoryos_context and memoryos_context.strip():
            sections.append(
                f"[Long-term context from past weeks/months:]\n{memoryos_context.strip()}"
            )

        # ── 5. OpenMemory episodic context ────────────────────────────────────
        if open_memory_context and open_memory_context.strip():
            sections.append(open_memory_context.strip())

        # ── 6. Bashara profile (always injected unless turned off) ────────────
        if include_profile:
            sections.append(_BASHARA_PROFILE_BLOCK)

        # ── 7. Recent conversation turns ──────────────────────────────────────
        if recent_turns:
            turn_lines = ["[Recent conversation — last few exchanges:"]
            for turn in recent_turns[-5:]:
                role = str(turn.get("role", "")).upper()
                ts = str(turn.get("timestamp", ""))[:16]
                content = str(turn.get("content", ""))[:300]
                turn_lines.append(f"  {role} [{ts}]: {content}")
            turn_lines.append("]")
            sections.append("\n".join(turn_lines))

        # ── 8. Active skill ───────────────────────────────────────────────────
        if active_skill and active_skill.strip():
            sections.append(
                f"[Active skill context for this request:]\n{active_skill.strip()[:1500]}"
            )

        # ── 9. Instincts + opinions ───────────────────────────────────────────
        if instinct_block and instinct_block.strip():
            sections.append(instinct_block.strip())
        if opinions_block and opinions_block.strip():
            sections.append(opinions_block.strip())

        # ── 10. Task context ──────────────────────────────────────────────────
        if task_context and task_context.strip():
            sections.append(f"[Current request context:]\n{task_context.strip()}")

        # ── 11. Behavioral footer (always last) ───────────────────────────────
        sections.append(_BEHAVIORAL_FOOTER)

        return "\n\n---\n\n".join(s for s in sections if s and s.strip())


_BEHAVIORAL_FOOTER = """[BEHAVIORAL RULES — always active]
- Research before answering anything factual/current/technical.
- Reference memories naturally — don't make Bashara repeat himself.
- Lead with the answer, context after.
- Calibrate length: short question = short answer; complex problem = detailed.
- Be honest about uncertainty rather than confidently wrong.
- Disagree with evidence when Bashara's approach is suboptimal.
- Proactively flag issues noticed while doing a task.
- NEVER say: Certainly, Great question, Of course, I'd be happy to, As an AI, Absolutely.
- Mix Indonesian/English naturally, matching Bashara's style.
- You are Legion. Stay in character always."""


# ── Convenience function for simple callers ───────────────────────────────────
def build_simple_system_prompt(
    task: str = "",
    mem0_memories: list[dict] | None = None,
    emotion: str = "neutral",
    active_skill: str = "",
) -> str:
    """Quick builder for callers that don't have full context objects."""
    builder = SystemPromptBuilder()
    return builder.build(
        task_context=task,
        mem0_memories=mem0_memories,
        emotion=emotion,
        active_skill=active_skill,
    )
