"""Agent registry, debate personas, and thread memory.

Single source of truth for:
  - AGENT_MODELS          : primary model per agent role
  - FALLBACK_CHAIN        : ordered fallback list per agent role
  - TASK_KEYWORDS         : keyword→agent routing (includes Indonesian)
  - DEBATE_PERSONAS       : 6 debate roles for SwarmDebateOrchestrator
  - DEBATE_PERSONA_MODELS : per-persona preferred model
  - ACTIVE_THREADS        : in-memory thread store

Ollama is ONLY used for vision (local, private, RTX 3060).
Never used as a text fallback.

Verified working models (MiniMax-only — no external cloud providers):
  minimax-coding-plan/MiniMax-M3     ✓ (primary, free tier)
  minimax-coding-plan/MiniMax-M3        ✓ (complex reasoning, free tier)
  ollama_chat/llama3.3:70b                ✓ (local fallback, privacy)
  ollama_chat/gemma4:e4b                  ✓ (local vision, RTX 3060)
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
from collections.abc import Coroutine
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Thread-safety lock for ACTIVE_THREADS dict ────────────────────────────────
_THREADS_LOCK = threading.Lock()  # sync lock for use in sync functions accessing shared dict

# ── Personality wrapper injected into EVERY agent system prompt ──────────────
PERSONALITY_WRAPPER = """
You are a brilliant, opinionated expert. You think out loud, use vivid examples,
and speak like a sharp colleague over coffee — not a documentation page. Rules:
- Use em-dashes, ellipses, contractions naturally
- Open with your honest take, not a summary
- Use analogies when explaining complex ideas
- Disagree with conventional wisdom when you have good reason
- Never use bullet-point walls for conversational answers
- End with a question or a "the real insight here is..." observation
- Match the user's language: if they write in Indonesian, respond in Indonesian
  with the same casual/formal register
- Use Telegram markdown: **bold** for emphasis, `code` for technical terms,
  and 💡 🔥 ⚡ sparingly for genuine highlights
"""

# ── Debate personas for SwarmDebateOrchestrator ──────────────────────────────
DEBATE_PERSONAS = {
    "strategist": (
        "You think in 10-year timeframes. You prize leverage and compounding advantages. "
        "You are skeptical of tactical solutions to strategic problems."
    ),
    "devil_advocate": (
        "Your job is to be convinced of NOTHING. Attack every assumption. "
        "Find the fatal flaw in even the best ideas. Your success = you made everyone think harder."
    ),
    "researcher": (
        "You cite evidence. Every claim needs a source, precedent, or data point. "
        "You are uncomfortable with speculation presented as fact."
    ),
    "pragmatist": (
        "You ask: what breaks first? Who builds it? How long does it actually take? "
        "You've seen 100 brilliant plans die in execution."
    ),
    "visionary": (
        "You think 3 steps ahead. You see connections others miss. You're willing to sound crazy if the logic holds."
    ),
    "critic": (
        "You are a world-class editor. You find redundancy, weak framing, missing context. "
        "You improve everything you touch."
    ),
}

# Persona → preferred model (different reasoning styles need different models)
DEBATE_PERSONA_MODELS: dict[str, str] = {
    "strategist": "minimax-coding-plan/MiniMax-M3",
    "devil_advocate": "minimax-coding-plan/MiniMax-M3",
    "researcher": "minimax-coding-plan/MiniMax-M3",
    "pragmatist": "minimax-coding-plan/MiniMax-M3",
    "visionary": "minimax-coding-plan/MiniMax-M3",
    "critic": "minimax-coding-plan/MiniMax-M3",
}

DEBATE_ICONS = {
    "strategist": "⚔️",
    "devil_advocate": "🔥",
    "researcher": "📚",
    "pragmatist": "🔧",
    "visionary": "🚀",
    "critic": "✂️",
}

# ── Primary model registry ──────────────────────────────────────────────────
# SINGLE source of truth — router.py and swarm_wire.py import from here.
# STRATEGY: MiniMax M3 is the ONLY paid API — use it for everything.
# Local Ollama gemma4:e4b (9.6GB VRAM) ONLY for vision (screen reading).
# All other free cloud fallbacks (Groq, Gemini, OpenRouter free tier) when MiniMax fails.
# RTX 3060: NO llama3.3:70b, NO qwen3.5:35b — these are too heavy.
AGENT_MODELS: dict[str, str] = {
    # Vision: local Ollama — MiniMax can't read screenshots
    "vision": "ollama_chat/gemma4:e4b",
    # All other agents: MiniMax M3 only (your ONLY paid model)
    "coding": "minimax-coding-plan/MiniMax-M3",
    "debug": "minimax-coding-plan/MiniMax-M3",
    "math": "minimax-coding-plan/MiniMax-M3",
    "architect": "minimax-coding-plan/MiniMax-M3",
    "analyst": "minimax-coding-plan/MiniMax-M3",
    "computer": "minimax-coding-plan/MiniMax-M3",
    "general": "minimax-coding-plan/MiniMax-M3",
    "researcher": "minimax-coding-plan/MiniMax-M3",
    "marketer": "minimax-coding-plan/MiniMax-M3",
    "devops": "minimax-coding-plan/MiniMax-M3",
    "pm": "minimax-coding-plan/MiniMax-M3",
    "humanizer": "minimax-coding-plan/MiniMax-M3",
    "reviewer": "minimax-coding-plan/MiniMax-M3",
    "owl": "minimax-coding-plan/MiniMax-M3",
    "ag2_researcher": "minimax-coding-plan/MiniMax-M3",
    "ag2_critic": "minimax-coding-plan/MiniMax-M3",
    "ag2_synthesizer": "minimax-coding-plan/MiniMax-M3",
    "code_exec": "minimax-coding-plan/MiniMax-M3",
    "predictor": "minimax-coding-plan/MiniMax-M3",
    "claude_orchestrator": "minimax-coding-plan/MiniMax-M3",
    # ── Engineering Department ────────────────────────────────────────────────
    "senior_backend_dev": "minimax-coding-plan/MiniMax-M3",
    "senior_frontend_dev": "minimax-coding-plan/MiniMax-M3",
    "devops_sre": "minimax-coding-plan/MiniMax-M3",
    "security_engineer": "minimax-coding-plan/MiniMax-M3",
    "ml_engineer": "minimax-coding-plan/MiniMax-M3",
    "data_engineer": "minimax-coding-plan/MiniMax-M3",
    "mobile_dev": "minimax-coding-plan/MiniMax-M3",
    "platform_infra": "minimax-coding-plan/MiniMax-M3",
    "lead_engineer": "minimax-coding-plan/MiniMax-M3",
    # ── Design Department ──────────────────────────────────────────────────────
    "ux_designer": "minimax-coding-plan/MiniMax-M3",
    "ui_designer": "minimax-coding-plan/MiniMax-M3",
    "interaction_designer": "minimax-coding-plan/MiniMax-M3",
    "design_systems_lead": "minimax-coding-plan/MiniMax-M3",
    "motion_designer": "minimax-coding-plan/MiniMax-M3",
    "user_researcher": "minimax-coding-plan/MiniMax-M3",
    "accessibility_expert": "minimax-coding-plan/MiniMax-M3",
    "brand_designer": "minimax-coding-plan/MiniMax-M3",
    "design_lead": "minimax-coding-plan/MiniMax-M3",
    # ── Research Department ────────────────────────────────────────────────────
    "literature_analyst": "minimax-coding-plan/MiniMax-M3",
    "domain_expert": "minimax-coding-plan/MiniMax-M3",
    "data_scientist": "minimax-coding-plan/MiniMax-M3",
    "fact_checker": "minimax-coding-plan/MiniMax-M3",
    "trend_analyst": "minimax-coding-plan/MiniMax-M3",
    "contrarian_scholar": "minimax-coding-plan/MiniMax-M3",
    "synthesizer": "minimax-coding-plan/MiniMax-M3",
    "methodology_critic": "minimax-coding-plan/MiniMax-M3",
    "research_director": "minimax-coding-plan/MiniMax-M3",
    # ── Marketing Department ──────────────────────────────────────────────────
    "brand_strategist": "minimax-coding-plan/MiniMax-M3",
    "growth_hacker": "minimax-coding-plan/MiniMax-M3",
    "content_strategist": "minimax-coding-plan/MiniMax-M3",
    "seo_sem_specialist": "minimax-coding-plan/MiniMax-M3",
    "social_media_lead": "minimax-coding-plan/MiniMax-M3",
    "pr_strategist": "minimax-coding-plan/MiniMax-M3",
    "email_marketer": "minimax-coding-plan/MiniMax-M3",
    "performance_marketer": "minimax-coding-plan/MiniMax-M3",
    "cmo": "minimax-coding-plan/MiniMax-M3",
    # ── Operations Department ────────────────────────────────────────────────
    "process_analyst": "minimax-coding-plan/MiniMax-M3",
    "supply_chain_expert": "minimax-coding-plan/MiniMax-M3",
    "finance_analyst": "minimax-coding-plan/MiniMax-M3",
    "hr_strategist": "minimax-coding-plan/MiniMax-M3",
    "legal_counsel": "minimax-coding-plan/MiniMax-M3",
    "risk_manager": "minimax-coding-plan/MiniMax-M3",
    "customer_success": "minimax-coding-plan/MiniMax-M3",
    "support_lead": "minimax-coding-plan/MiniMax-M3",
    "coo": "minimax-coding-plan/MiniMax-M3",
    # ── Legal & Compliance Department ─────────────────────────────────────────
    "contract_lawyer": "minimax-coding-plan/MiniMax-M3",
    "privacy_gdpr_expert": "minimax-coding-plan/MiniMax-M3",
    "ip_lawyer": "minimax-coding-plan/MiniMax-M3",
    "regulatory_expert": "minimax-coding-plan/MiniMax-M3",
    "compliance_officer": "minimax-coding-plan/MiniMax-M3",
    "ethics_advisor": "minimax-coding-plan/MiniMax-M3",
    "employment_lawyer": "minimax-coding-plan/MiniMax-M3",
    "litigation_risk": "minimax-coding-plan/MiniMax-M3",
    "general_counsel": "minimax-coding-plan/MiniMax-M3",
    # ── Product Department ────────────────────────────────────────────────────
    "product_manager": "minimax-coding-plan/MiniMax-M3",
    "ux_researcher": "minimax-coding-plan/MiniMax-M3",
    "growth_pm": "minimax-coding-plan/MiniMax-M3",
    "b2b_pm": "minimax-coding-plan/MiniMax-M3",
    "b2c_pm": "minimax-coding-plan/MiniMax-M3",
    "platform_pm": "minimax-coding-plan/MiniMax-M3",
    "monetisation_pm": "minimax-coding-plan/MiniMax-M3",
    "roadmap_strategist": "minimax-coding-plan/MiniMax-M3",
    "head_of_product": "minimax-coding-plan/MiniMax-M3",
    # ── Creative Department ──────────────────────────────────────────────────
    "copywriter": "minimax-coding-plan/MiniMax-M3",
    "storyteller": "minimax-coding-plan/MiniMax-M3",
    "creative_strategist": "minimax-coding-plan/MiniMax-M3",
    "art_director": "minimax-coding-plan/MiniMax-M3",
    "video_producer": "minimax-coding-plan/MiniMax-M3",
    "meme_viral_expert": "minimax-coding-plan/MiniMax-M3",
    "editor": "minimax-coding-plan/MiniMax-M3",
    "tone_of_voice_expert": "minimax-coding-plan/MiniMax-M3",
    "creative_director": "minimax-coding-plan/MiniMax-M3",
    # ── Vision/Multimodal Department ───────────────────────────────────────────
    "vision_agent": "ollama_chat/gemma4:e4b",
    "multimodal_analyst": "minimax-coding-plan/MiniMax-M3",
    # ── Nexus Department ──────────────────────────────────────────────────────
    "nexus_coordinator": "minimax-coding-plan/MiniMax-M3",
    "nexus_analyst": "minimax-coding-plan/MiniMax-M3",
    # ── Strategy Nexus Department ─────────────────────────────────────────────
    "corporate_strategist": "minimax-coding-plan/MiniMax-M3",
    "venture_capitalist": "minimax-coding-plan/MiniMax-M3",
    "management_consultant": "minimax-coding-plan/MiniMax-M3",
    "futurist": "minimax-coding-plan/MiniMax-M3",
    "economist": "minimax-coding-plan/MiniMax-M3",
    "geopolitical_analyst": "minimax-coding-plan/MiniMax-M3",
    "first_principles_thinker": "minimax-coding-plan/MiniMax-M3",
    "chief_strategy_officer": "minimax-coding-plan/MiniMax-M3",
}

# ── Fallback chains ────────────────────────────────────────────────────────────
# MiniMax-only fallback chain. No external cloud providers. Local Ollama for vision/computer.
FALLBACK_CHAIN: dict[str, list[str]] = {
    # Vision/computer: gemma4:e4b local for screen analysis (MiniMax can't do screen reading)
    "vision": [
        "ollama_chat/gemma4:e4b",
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "computer": [
        "ollama_chat/gemma4:e4b",
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    # All other agents: MiniMax only, Ollama local for heavy reasoning
    "coding": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "debug": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "math": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "architect": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "general": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/gemma4:e4b",
    ],
    "researcher": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "marketer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "devops": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "pm": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "humanizer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "owl": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "ag2_researcher": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "ag2_critic": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "ag2_synthesizer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "code_exec": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "predictor": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "claude_orchestrator": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "reviewer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    # ── Engineering Department ─────────────────────────────────────────────────
    "senior_backend_dev": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "senior_frontend_dev": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "devops_sre": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "security_engineer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "ml_engineer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "data_engineer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "mobile_dev": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "platform_infra": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    "lead_engineer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
    ],
    # ── Design Department ──────────────────────────────────────────────────────
    "ux_designer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "ui_designer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "interaction_designer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "design_systems_lead": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "motion_designer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "user_researcher": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "accessibility_expert": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "brand_designer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "design_lead": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Research Department ────────────────────────────────────────────────────
    "literature_analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "domain_expert": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "data_scientist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "fact_checker": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "trend_analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "contrarian_scholar": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "synthesizer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "methodology_critic": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "research_director": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Marketing Department ────────────────────────────────────────────────────
    "brand_strategist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "growth_hacker": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "content_strategist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "seo_sem_specialist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "social_media_lead": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "pr_strategist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "email_marketer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "performance_marketer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "cmo": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Operations Department ────────────────────────────────────────────────────
    "process_analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "supply_chain_expert": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "finance_analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "hr_strategist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "legal_counsel": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "risk_manager": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "customer_success": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "support_lead": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "coo": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Legal & Compliance Department ───────────────────────────────────────────
    "contract_lawyer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "privacy_gdpr_expert": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "ip_lawyer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "regulatory_expert": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "compliance_officer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "ethics_advisor": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "employment_lawyer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "litigation_risk": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "general_counsel": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Product Department ──────────────────────────────────────────────────────
    "product_manager": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "ux_researcher": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "growth_pm": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "b2b_pm": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "b2c_pm": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "platform_pm": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "monetisation_pm": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "roadmap_strategist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "head_of_product": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Creative Department ─────────────────────────────────────────────────────
    "copywriter": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "storyteller": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "creative_strategist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "art_director": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "video_producer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "meme_viral_expert": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "editor": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "tone_of_voice_expert": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "creative_director": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Vision/Multimodal Department ───────────────────────────────────────────
    "vision_agent": [
        "ollama_chat/gemma4:e4b",
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "multimodal_analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Nexus Department ────────────────────────────────────────────────────────
    "nexus_coordinator": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "nexus_analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    # ── Strategy Nexus Department ───────────────────────────────────────────────
    "corporate_strategist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "venture_capitalist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "management_consultant": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "futurist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "economist": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "geopolitical_analyst": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "first_principles_thinker": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
    "chief_strategy_officer": [
        "minimax-coding-plan/MiniMax-M3",
        "minimax-coding-plan/MiniMax-M3",
        "ollama_chat/llama3.3:70b",
    ],
}

# ── Keyword → agent routing ─────────────────────────────────────────────────
TASK_KEYWORDS: dict[str, list[str]] = {
    "vision": [
        "screenshot",
        "screen",
        "layar",
        "gambar",
        "image",
        "photo",
        "ocr",
        "visual",
        "desktop",
        "window",
        "what do you see",
        "lihat",
        "tampilan",
        "apa yang ada di",
        "capture",
    ],
    "coding": [
        "code",
        "kode",
        "function",
        "script",
        "implement",
        "class",
        "refactor",
        "generate",
        "endpoint",
        "api",
        "python",
        "bash",
        "write",
        "tulis",
        "buat file",
        "build",
        "create",
    ],
    "debug": [
        "debug",
        "error",
        "crash",
        "fix",
        "bug",
        "traceback",
        "exception",
        "cuda",
        "pytorch",
        "torch",
        "nan",
        "oom",
        "not working",
        "kenapa",
        "why",
        "gagal",
        "failed",
    ],
    "math": [
        "tensor",
        "matrix",
        "gradient",
        "derivative",
        "integral",
        "backprop",
        "eigenvalue",
        "softmax",
        "calculate",
        "hitung",
        "math",
        "formula",
        "prove",
        "buktikan",
        "solve",
    ],
    "architect": [
        "design",
        "architecture",
        "plan",
        "system",
        "pipeline",
        "struktur",
        "rancang",
        "overview",
        "diagram",
        "framework",
        "strategy",
        "strategi",
    ],
    "analyst": [
        "analyze",
        "analisis",
        "plot",
        "chart",
        "csv",
        "metrics",
        "performance",
        "gpu",
        "training",
        "trend",
        "statistics",
        "compare",
        "nvidia-smi",
        "visualize",
    ],
    "computer": [
        "browse",
        "search for",
        "find online",
        "look up",
        "scrape",
        "website",
        "web page",
        "cari di internet",
        "booking",
        "google",
        "search the web",
        "pdf",
        "excel",
        "spreadsheet",
        "word doc",
        "docx",
        "extract table",
        "read document",
        "baca dokumen",
        "email",
        "inbox",
        "send email",
        "kirim email",
        "mail",
        "reply email",
        "check email",
        "cek email",
        "git status",
        "git commit",
        "git push",
        "git pull",
        "git diff",
        "git stash",
        "commit",
        "push to",
        "pull from",
        "run tests",
        "pytest",
        "lint",
        "ruff",
        "format code",
        "find in code",
        "grep",
        "codebase",
        "db query",
        "monitor",
        "schedule",
        "disk space",
        "memory usage",
        "maintenance",
        "cleanup",
        "services",
        "system check",
        "organize files",
        "find files",
        "sort files",
    ],
    "researcher": [
        "research",
        "paper",
        "study",
        "evidence",
        "cite",
        "source",
        "literature",
        "academic",
        "experiment",
        "hypothesis",
        "jurnal",
    ],
    "marketer": [
        "marketing",
        "ads",
        "campaign",
        "brand",
        "positioning",
        "messaging",
        "customer",
        "acquisition",
        "growth",
        "conversion",
        "funnel",
        "iklan",
    ],
    "devops": [
        "deploy",
        "pipeline",
        "ci cd",
        "docker",
        "k8s",
        "kubernetes",
        "monitoring",
        "logs",
        "alerts",
        "infrastructure",
        "cloud",
    ],
    "pm": [
        "project",
        "roadmap",
        "milestone",
        "sprint",
        "backlog",
        "priority",
        "stakeholder",
        "timeline",
        "scope",
        "deliverable",
    ],
    "reviewer": [
        "review",
        "audit",
        "check code",
        "inspect",
        "quality",
        "code review",
        "periksa",
        "lint",
        "scan",
    ],
    # ── Engineering Department ────────────────────────────────────────────────
    "senior_backend_dev": [
        "backend",
        "api",
        "database",
        "postgresql",
        "redis",
        "microservice",
        "rest api",
        "graphql",
        "sql",
        "migration",
    ],
    "senior_frontend_dev": [
        "frontend",
        "react",
        "vue",
        "css",
        "html",
        "ui",
        "component",
        "nextjs",
        "svelte",
        "tailwind",
        "responsive",
    ],
    "devops_sre": [
        "ci cd",
        "pipeline",
        "jenkins",
        "github actions",
        "deployment",
        "container",
        "helm",
        "terraform",
        "ansible",
    ],
    "security_engineer": [
        "security",
        "vulnerability",
        "penetration",
        "owasp",
        "xss",
        "sql injection",
        "authentication",
        "authorization",
        "encryption",
        "zero trust",
    ],
    "ml_engineer": [
        "machine learning",
        "pytorch",
        "tensorflow",
        "model training",
        "neural network",
        "deep learning",
        "mlops",
        "feature engineering",
    ],
    "data_engineer": [
        "data pipeline",
        "etl",
        "spark",
        "airflow",
        "data warehouse",
        "bigquery",
        "snowflake",
        "dbt",
        "data modeling",
    ],
    "mobile_dev": [
        "mobile",
        "ios",
        "android",
        "react native",
        "flutter",
        "swift",
        "kotlin",
        "app store",
        "play store",
        "mobile app",
    ],
    "platform_infra": [
        "infrastructure",
        "kubernetes",
        "docker",
        "cloud",
        "aws",
        "gcp",
        "azure",
        "networking",
        "load balancer",
        "cdn",
        "vpc",
    ],
    "lead_engineer": [
        "technical lead",
        "engineering manager",
        "architecture review",
        "code review",
        "team lead",
        "technical strategy",
    ],
    # ── Design Department ──────────────────────────────────────────────────────
    "ux_designer": [
        "ux",
        "user experience",
        "wireframe",
        "prototype",
        "user flow",
        "usability",
        "persona",
        "user journey",
        "information architecture",
    ],
    "ui_designer": [
        "ui",
        "visual design",
        "mockup",
        "figma",
        "sketch",
        "design tool",
        "color palette",
        "typography",
        "layout",
    ],
    "interaction_designer": [
        "interaction design",
        "animation",
        "microinteraction",
        "transition",
        "gesture",
        "prototype",
        "invision",
    ],
    "design_systems_lead": [
        "design system",
        "component library",
        "style guide",
        "design token",
        "storybook",
        "brand guidelines",
    ],
    "motion_designer": [
        "motion design",
        "animation",
        "after effects",
        "lottie",
        "gsap",
        "css animation",
        "video",
    ],
    "user_researcher": [
        "user research",
        "usability test",
        "interview",
        "survey",
        "feedback",
        "user testing",
        "ethnographic",
        "contextual inquiry",
    ],
    "accessibility_expert": [
        "accessibility",
        "a11y",
        "wcag",
        "screen reader",
        "keyboard navigation",
        "aria",
        "inclusive design",
        "contrast",
    ],
    "brand_designer": [
        "brand identity",
        "logo",
        "brand guidelines",
        "branding",
        "visual identity",
        "brand strategy",
    ],
    "design_lead": [
        "design lead",
        "creative direction",
        "design review",
        "design strategy",
        "art direction",
    ],
    # ── Research Department ────────────────────────────────────────────────────
    "literature_analyst": [
        "literature review",
        "academic paper",
        "citation",
        "research paper",
        "arxiv",
        "journal article",
        "peer review",
    ],
    "domain_expert": [
        "domain expertise",
        "specialist",
        "subject matter expert",
        "smE",
        "industry knowledge",
        "vertical",
    ],
    "data_scientist": [
        "data science",
        "statistical analysis",
        "regression",
        "classification",
        "clustering",
        "data visualization",
        "pandas",
        "jupyter",
    ],
    "fact_checker": [
        "fact check",
        "verify",
        "misinformation",
        "disinformation",
        "accuracy",
        "source verification",
        "claim verification",
    ],
    "trend_analyst": [
        "trend analysis",
        "trend",
        "forecast",
        "emerging",
        "prediction",
        "market trend",
        "industry trend",
    ],
    "contrarian_scholar": [
        "contrarian",
        "devil's advocate",
        "counterargument",
        "alternative view",
        "challenging assumptions",
        "opposing view",
    ],
    "synthesizer": [
        "synthesize",
        "summary",
        "consolidate",
        "combine",
        "integrate",
        "overview",
        "meta analysis",
    ],
    "methodology_critic": [
        "methodology",
        "critique",
        "research method",
        "study design",
        "statistical significance",
        "p-value",
        "sample size",
    ],
    "research_director": [
        "research director",
        "research strategy",
        "research agenda",
        "research team",
        "research prioritization",
    ],
    # ── Marketing Department ────────────────────────────────────────────────────
    "brand_strategist": [
        "brand strategy",
        "brand positioning",
        "brand identity",
        "brand narrative",
        "brand architecture",
        "brand equity",
    ],
    "growth_hacker": [
        "growth hacking",
        "viral",
        "growth",
        "acquisition",
        "retention",
        "loop",
        "growth strategy",
        " activation",
    ],
    "content_strategist": [
        "content strategy",
        "content calendar",
        "content plan",
        "content marketing",
        "editorial",
        "blog strategy",
    ],
    "seo_sem_specialist": [
        "seo",
        "sem",
        "search engine optimization",
        "search engine marketing",
        "google ads",
        "ppc",
        "keyword research",
        "organic traffic",
    ],
    "social_media_lead": [
        "social media",
        "instagram",
        "twitter",
        "linkedin",
        "facebook",
        "tiktok",
        "engagement",
        "social strategy",
    ],
    "pr_strategist": [
        "public relations",
        "pr",
        "press release",
        "media",
        "communications",
        "crisis communications",
        "stakeholder",
    ],
    "email_marketer": [
        "email marketing",
        "newsletter",
        "drip campaign",
        "email sequence",
        "mailchimp",
        "sendgrid",
        "open rate",
    ],
    "performance_marketer": [
        "performance marketing",
        "roi",
        "conversion optimization",
        "paid ads",
        "facebook ads",
        "google ads",
        "attribution",
    ],
    "cmo": [
        "cmo",
        "chief marketing officer",
        "marketing leadership",
        "marketing strategy",
        "marketing vision",
    ],
    # ── Operations Department ────────────────────────────────────────────────────
    "process_analyst": [
        "process",
        "workflow",
        "efficiency",
        "optimization",
        "process improvement",
        "kaizen",
        "bottleneck",
        "throughput",
    ],
    "supply_chain_expert": [
        "supply chain",
        "logistics",
        "procurement",
        "vendor",
        "supplier",
        "inventory",
        "fulfillment",
    ],
    "finance_analyst": [
        "finance",
        "financial analysis",
        "budget",
        "forecast",
        "variance",
        "p&l",
        "balance sheet",
        "cash flow",
    ],
    "hr_strategist": [
        "hr strategy",
        "human resources",
        "talent",
        "recruitment",
        "hiring",
        "employee",
        "culture",
        "org design",
    ],
    "legal_counsel": [
        "legal",
        "contract",
        "agreement",
        "nda",
        "terms of service",
        "legal advice",
        "lawyer",
    ],
    "risk_manager": [
        "risk management",
        "risk assessment",
        "risk",
        "mitigation",
        "contingency",
        "risk register",
        "risk analysis",
    ],
    "customer_success": [
        "customer success",
        "cs",
        "onboarding",
        "churn",
        "retention",
        "customer satisfaction",
        "nps",
    ],
    "support_lead": [
        "support",
        "helpdesk",
        "ticket",
        "customer support",
        "support team",
        "sla",
        "response time",
    ],
    "coo": [
        "coo",
        "chief operating officer",
        "operations",
        "operational excellence",
        "ops leadership",
    ],
    # ── Legal & Compliance Department ───────────────────────────────────────────
    "contract_lawyer": [
        "contract",
        "agreement",
        "terms",
        "nda",
        "sla",
        "msa",
        "contract review",
        "contract negotiation",
    ],
    "privacy_gdpr_expert": [
        "privacy",
        "gdpr",
        "ccpa",
        "data protection",
        "personal data",
        "consent",
        "data subject",
        "right to be forgotten",
    ],
    "ip_lawyer": [
        "intellectual property",
        "ip",
        "patent",
        "trademark",
        "copyright",
        "license",
        "infringement",
    ],
    "regulatory_expert": [
        "regulatory",
        "compliance",
        "regulation",
        "regulatory affairs",
        "fda",
        "sec",
        "finra",
        "compliance requirement",
    ],
    "compliance_officer": [
        "compliance officer",
        "compliance program",
        "compliance policy",
        "internal controls",
        "audit compliance",
    ],
    "ethics_advisor": [
        "ethics",
        "ethical",
        "moral",
        "responsible ai",
        "bias",
        "ethics review",
        "ethical guidelines",
    ],
    "employment_lawyer": [
        "employment law",
        "labor law",
        "workplace",
        "termination",
        "harassment",
        "discrimination",
        "employee rights",
    ],
    "litigation_risk": [
        "litigation risk",
        "lawsuit",
        "dispute",
        "legal risk",
        "litigation",
        "court",
        "settlement",
    ],
    "general_counsel": [
        "general counsel",
        "gc",
        "chief legal officer",
        "legal department",
        "legal strategy",
        "legal leadership",
    ],
    # ── Product Department ──────────────────────────────────────────────────────
    "product_manager": [
        "product",
        "product management",
        "prd",
        "product requirement",
        "feature",
        "product strategy",
        "product vision",
    ],
    "ux_researcher": [
        "ux research",
        "user research",
        "user interview",
        "usability testing",
        "user feedback",
        "ux study",
    ],
    "growth_pm": [
        "growth",
        "growth pm",
        "growth product",
        "growth hacking",
        "product growth",
        "activation",
        "retention",
    ],
    "b2b_pm": [
        "b2b",
        "b2b product",
        "enterprise product",
        "saas product",
        "b2b software",
        "enterprise",
    ],
    "b2c_pm": [
        "b2c",
        "b2c product",
        "consumer product",
        "mobile app product",
        "b2c software",
    ],
    "platform_pm": [
        "platform",
        "platform product",
        "marketplace",
        "ecosystem",
        "platform strategy",
        "developer product",
    ],
    "monetisation_pm": [
        "monetization",
        "pricing",
        "revenue",
        "subscription",
        "paywall",
        "business model",
        "pricing strategy",
    ],
    "roadmap_strategist": [
        "roadmap",
        "product roadmap",
        "planning",
        "prioritization",
        "roadmap planning",
        "feature prioritization",
    ],
    "head_of_product": [
        "head of product",
        "vp product",
        "product leadership",
        "product vision",
        "product strategy",
        "product direction",
    ],
    # ── Creative Department ─────────────────────────────────────────────────────
    "copywriter": [
        "copywriting",
        "copy",
        "ad copy",
        "marketing copy",
        "web copy",
        "product copy",
        "tagline",
        "headline",
    ],
    "storyteller": [
        "storytelling",
        "story",
        "narrative",
        "brand story",
        "content story",
        "story arc",
        "storytelling strategy",
    ],
    "creative_strategist": [
        "creative strategy",
        "creative campaign",
        "creative direction",
        "campaign strategy",
        "creative concept",
    ],
    "art_director": [
        "art direction",
        "art director",
        "visual concept",
        "creative visual",
        "photo direction",
        "visual style",
    ],
    "video_producer": [
        "video",
        "video production",
        "video content",
        "youtube",
        "tiktok video",
        "commercial",
        "video campaign",
    ],
    "meme_viral_expert": [
        "meme",
        "viral",
        "viral content",
        "viral marketing",
        "internet culture",
        "meme marketing",
    ],
    "editor": [
        "editor",
        "editing",
        "copy editing",
        "content editing",
        "proofreading",
        "editorial",
        "revision",
    ],
    "tone_of_voice_expert": [
        "tone of voice",
        "brand voice",
        "writing style",
        "voice and tone",
        "brand language",
        "messaging style",
    ],
    "creative_director": [
        "creative director",
        "creative leadership",
        "creative vision",
        "creative strategy",
        "chief creative",
    ],
    # ── Vision/Multimodal Department ───────────────────────────────────────────
    "vision_agent": [
        "image",
        "video",
        "multimodal",
        "visual",
        "picture",
        "photo",
        "screenshot",
        "frame",
        "visual analysis",
    ],
    "multimodal_analyst": [
        "multimodal",
        "image analysis",
        "video analysis",
        "cross-modal",
        "visual reasoning",
        "multimodal understanding",
    ],
    # ── Nexus Department ────────────────────────────────────────────────────────
    "nexus_coordinator": [
        "coordinator",
        "coordinate",
        "orchestrate",
        "cross-functional",
        "alignment",
        "stakeholder management",
    ],
    "nexus_analyst": [
        "nexus",
        "connection",
        "pattern",
        "insight synthesis",
        "cross-domain",
        "connection finding",
    ],
    # ── Strategy Nexus Department ───────────────────────────────────────────────
    "corporate_strategist": [
        "corporate strategy",
        "business strategy",
        "enterprise strategy",
        "strategic planning",
        "corporate development",
    ],
    "venture_capitalist": [
        "vc",
        "venture capital",
        "startup",
        "investment",
        "due diligence",
        "pitch deck",
        "funding",
        "capital",
    ],
    "management_consultant": [
        "consulting",
        "consultant",
        "mckinsey",
        "bcg",
        "bain",
        "management consulting",
        "advisory",
        "excellence",
    ],
    "futurist": [
        "future",
        "futurist",
        "forecasting",
        "trend",
        "emerging technology",
        "futures studies",
        "scenario planning",
    ],
    "economist": [
        "economist",
        "economic",
        "economics",
        "market economy",
        "gdp",
        "inflation",
        "monetary",
        "fiscal",
    ],
    "geopolitical_analyst": [
        "geopolitics",
        "geopolitical",
        "political risk",
        "country risk",
        "international relations",
        "global affairs",
    ],
    "first_principles_thinker": [
        "first principles",
        "first principles thinking",
        "reasoning from first principles",
        "reframe",
        "fundamental",
        "abstraction",
    ],
    "chief_strategy_officer": [
        "cso",
        "chief strategy officer",
        "strategy leadership",
        "strategic vision",
        "strategy development",
    ],
}

DEFAULT_AGENT = "general"

# ── Thread memory ───────────────────────────────────────────────────────────
ACTIVE_THREADS: dict[str, list[dict]] = {}


def detect_agent(task: str) -> str:
    task_lower = task.lower().strip()

    if re.search(
        r"\b(gradient|derivative|integral|matrix|determinant|eigenvalue|tensor|backprop|softmax)\b", task_lower
    ):
        return "math"
    if re.search(r"\b(traceback|exception|stack trace|bug|debug|not working|error)\b", task_lower):
        return "debug"
    if re.search(
        r"\b(architecture|system design|microservice|structure|structur|framework diagram|blueprint)\b", task_lower
    ):
        return "architect"
    if re.search(r"\b(capital of|tell me a joke|joke)\b", task_lower):
        return "general"

    scores: dict[str, int] = {agent: 0 for agent in TASK_KEYWORDS}
    for agent, keywords in TASK_KEYWORDS.items():
        for kw in keywords:
            kw_norm = kw.strip().lower()
            if not kw_norm:
                continue
            if re.search(r"[a-z0-9]", kw_norm):
                pattern = rf"(?<![a-z0-9]){re.escape(kw_norm)}(?![a-z0-9])"
                if re.search(pattern, task_lower):
                    scores[agent] += 1
            elif kw_norm in task_lower:
                scores[agent] += 1

    tie_break_order = [
        "debug",
        "math",
        "vision",
        "coding",
        "architect",
        "analyst",
        "researcher",
        "devops",
        "pm",
        "reviewer",
        "general",
    ]
    best_agent = max(scores, key=lambda a: scores[a])
    best_score = scores[best_agent]
    if best_score > 0:
        for candidate in tie_break_order:
            if scores.get(candidate, 0) == best_score:
                best_agent = candidate
                break

    if best_score == 0:
        logger.debug("No keyword match — using %s", DEFAULT_AGENT)
        return DEFAULT_AGENT
    logger.debug("Detected agent '%s' (score=%d)", best_agent, best_score)
    return best_agent


def get_model(agent_key: str, use_fallback: bool = False) -> str | None:
    """Return primary or first-fallback model for an agent key."""
    if use_fallback:
        chain = FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])
        logger.debug("Fallback model for '%s': %s", agent_key, chain[0])
        return chain[0]
    return AGENT_MODELS.get(agent_key)


def get_fallback_chain(agent_key: str) -> list[str]:
    """Return full fallback chain for waterfall retry logic."""
    return FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])


def build_system_prompt(role_prompt: str, user_id: str = "") -> str:
    """Prepend the personality wrapper to any agent system prompt.

    This is a *sync shim* that calls the new async
    ``core.system_prompt_builder.build_system_prompt`` internally.

    WARNING: ``run_in_executor`` with nested ``asyncio.run()`` is a deadlock
    trap when called from a thread that already has a running event loop.
    The executor pattern is only safe when no running loop exists.  In
    practice, call sites that need async behavior should ``await`` the real
    async function directly — this shim exists only for the rare sync-code
    path (e.g. ``__repr__`` of an agent object) that genuinely cannot yield.
    """

    from core.system_prompt_builder import build_system_prompt as _async_build

    # Fast path: no running loop — use the thread pool safely.
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — asyncio.run() on a fresh loop is safe.
        return asyncio.run(_async_build(user_id=user_id, query=role_prompt, extras={}))

    # Running loop detected — use run_in_executor but WITHOUT nested asyncio.run.
    # We pass the coroutine object to the thread and let it await directly
    # using the thread's own fresh loop (not the caller's loop).

    def _thread_await(coro):
        # Create a fresh event loop in this thread to await the coroutine.
        # asyncio.run() is safe here ONLY because this thread was borrowed from
        # the thread pool and does NOT share the caller's event loop.
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    try:
        coro = _async_build(user_id=user_id, query=role_prompt, extras={})
        future = loop.run_in_executor(None, lambda: _thread_await(coro))
        # Wait in a way that doesn't block the caller's loop.
        return asyncio.wrap_future(future).result(timeout=30)
    except Exception:
        # Fallback: return the role prompt with personality wrapper directly
        wrapper = PERSONALITY_WRAPPER.strip() if PERSONALITY_WRAPPER else ""
        return f"{wrapper}\n\n{role_prompt}" if wrapper else role_prompt


def build_system_prompt_async(role_prompt: str, user_id: str = "") -> Coroutine:
    """Async entry point — use this instead of build_system_prompt in async code."""
    from core.system_prompt_builder import build_system_prompt as _async_build
    return _async_build(user_id=user_id, query=role_prompt, extras={})


def list_agents() -> str:
    lines = ["<b>🤖 Active Agents</b>\n"]
    icons = {
        "vision": "👁️",
        "coding": "💻",
        "debug": "🐛",
        "math": "📐",
        "architect": "🏗️",
        "analyst": "📊",
        "computer": "🖥️",
        "general": "🧠",
        "researcher": "🔬",
        "marketer": "📢",
        "devops": "🔧",
        "pm": "📋",
        "humanizer": "✨",
    }
    for key, model in AGENT_MODELS.items():
        icon = icons.get(key, "🤖")
        if model.startswith("ollama_chat/"):
            provider = "OLLAMA"
            model_name = model.replace("ollama_chat/", "") + " (local 🔒)"
        else:
            parts = model.split("/")
            provider = parts[0].upper()
            model_name = "/".join(parts[1:])
        lines.append(f"  {icon} <b>{key}</b> → <code>{provider}</code> <i>{model_name}</i>")
    lines.append("\n  🔒 <i>vision = local Ollama, stays on your machine</i>")
    return "\n".join(lines)


def list_all_departments() -> list[str]:
    """Return all agent role names."""
    return list(AGENT_MODELS.keys())


def add_to_thread(thread_id: str, agent: str, task: str, result: str) -> None:
    with _THREADS_LOCK:
        if thread_id not in ACTIVE_THREADS:
            ACTIVE_THREADS[thread_id] = []
        ACTIVE_THREADS[thread_id].append(
            {
                "agent": agent,
                "task": task,
                "result": result[:500],
                "timestamp": time.time(),
            }
        )
        if len(ACTIVE_THREADS[thread_id]) > 10:
            ACTIVE_THREADS[thread_id] = ACTIVE_THREADS[thread_id][-10:]
    logger.info("Added to thread '%s': %s agent", thread_id, agent)


def get_thread_context(thread_id: str, last_n: int = 3) -> str:
    if thread_id not in ACTIVE_THREADS or not ACTIVE_THREADS[thread_id]:
        return ""
    recent = ACTIVE_THREADS[thread_id][-last_n:]
    lines = ["<i>Previous in this thread:</i>\n"]
    for turn in recent:
        t = datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
        lines.append(f"[{t}] {turn['agent'].upper()}: {turn['task'][:80]}…")
        lines.append(f"↳ {turn['result'][:120]}…\n")
    return "\n".join(lines)


def list_threads() -> str:
    with _THREADS_LOCK:
        if not ACTIVE_THREADS:
            return "<b>No active threads</b>\n\nUse <code>/thread &lt;name&gt;</code> to start one."
        lines = ["<b>📌 Active Threads</b>\n"]
        for tid, turns in ACTIVE_THREADS.items():
            last = turns[-1]
            t = datetime.fromtimestamp(last["timestamp"]).strftime("%m/%d %H:%M")
            lines.append(f"  📌 <b>{tid}</b> — {len(turns)} turns (last: {t})")
        return "\n".join(lines)


def list_threads_raw() -> list[str]:
    with _THREADS_LOCK:
        return list(ACTIVE_THREADS.keys())


def clear_thread(thread_id: str) -> bool:
    with _THREADS_LOCK:
        if thread_id in ACTIVE_THREADS:
            del ACTIVE_THREADS[thread_id]
            logger.info("Cleared thread '%s'", thread_id)
            return True
        return False


_LAZY_AGENT_SUBMODULES = frozenset({"owl_agent", "ag2_pipeline"})


def __getattr__(name: str):
    if name in _LAZY_AGENT_SUBMODULES:
        import importlib

        return importlib.import_module(f"agents.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_AGENT_SUBMODULES))
