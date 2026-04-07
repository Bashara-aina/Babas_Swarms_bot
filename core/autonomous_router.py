"""Autonomous skill selection for plain-text requests — Legion v6.

Two-tier routing:
  1. Fast keyword pre-filter with Indonesian synonyms (< 1 ms)
  2. LLM fallback via groq/llama-3.3-70b when confidence < 0.55 or message > 30 words
Performance history boosts/penalises skills based on rolling success rate.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SkillMatch:
    skill_name: str
    confidence: float
    reasoning: str


SKILL_PATTERNS = {
    "computer_control": {
        "keywords": [
            "open", "click", "type", "screenshot", "run this", "launch",
            "navigate to", "go to", "show me my screen", "check my",
            # Indonesian
            "buka", "klik", "ketik", "layar", "jalankan", "tampilkan layar",
            "ambil screenshot", "klik tombol",
        ],
        "description": "Control Linux desktop (mouse, keyboard, apps, files)",
        "handler": "/do",
    },
    "deep_research": {
        "keywords": [
            "research", "find out", "search for", "look up", "what is",
            "explain", "compare", "analyze", "investigate", "survey",
            # Indonesian
            "cari tahu", "cari informasi", "jelaskan", "bandingkan",
            "analisis", "apa itu", "bagaimana cara", "temukan", "riset",
        ],
        "description": "Multi-source web research with credibility scoring",
        "handler": "/research",
    },
    "code_generation": {
        "keywords": [
            "write", "code", "implement", "build", "create a script",
            "function", "class", "module", "refactor", "debug",
            # Indonesian
            "tulis kode", "buat fungsi", "buat script", "perbaiki kode",
            "implementasi", "buat class", "kode untuk", "program untuk",
        ],
        "description": "Code generation and review",
        "handler": "/run",
    },
    "deep_reasoning": {
        "keywords": [
            "why", "should i", "is it better", "trade-off", "pros and cons",
            "what do you think", "your opinion", "advise", "evaluate",
            "critique", "review",
            # Indonesian
            "kenapa", "mengapa", "menurut kamu", "pendapatmu", "saran",
            "pertimbangan", "lebih baik mana", "apa pendapat", "kelebihan kekurangan",
        ],
        "description": "Deep analytical reasoning with devil's advocate",
        "handler": "/think",
    },
    "multi_agent_swarm": {
        "keywords": [
            "complex", "full system", "end-to-end", "architecture",
            "design the", "plan the", "complete", "comprehensive",
            "multiple steps", "pipeline", "workflow",
            # Indonesian
            "sistem penuh", "rancang", "arsitektur", "alur kerja",
            "langkah-langkah", "rancangan sistem",
        ],
        "description": "Multi-agent swarm execution for complex tasks",
        "handler": "/swarm",
    },
    "memory_search": {
        "keywords": [
            "remember", "recall", "what did i say", "last time",
            "previously", "before", "history", "you mentioned",
            # Indonesian
            "ingat", "pernah", "dulu", "sebelumnya", "kemarin",
            "apa yang aku bilang", "kamu ingat", "pernah bilang",
        ],
        "description": "Search persistent memory across all sessions",
        "handler": "memory_recall",
    },
    "system_control": {
        "keywords": [
            "gpu", "cpu", "ram", "memory usage", "processes", "systemctl",
            "service", "install", "upgrade", "pip", "apt",
            # Indonesian
            "penggunaan memori", "proses", "layanan", "instal", "perbarui",
            "monitor sistem",
        ],
        "description": "System monitoring and shell control",
        "handler": "/cmd",
    },
    # ── New patterns ────────────────────────────────────────────────────────
    "email_management": {
        "keywords": [
            "email", "inbox", "mail", "reply to", "forward", "draft email",
            "check email", "send email", "unread email",
            # Indonesian
            "kirim email", "balas email", "cek inbox", "email masuk",
            "surat", "gmail", "baca email",
        ],
        "description": "Read, reply, and manage email via IMAP/SMTP",
        "handler": "email",
    },
    "business_query": {
        "keywords": [
            "rumahlabuh", "booking", "reservasi", "supabase",
            "revenue", "guest", "tamu", "penginapan", "kamar",
            "pemesanan", "pendapatan", "laporan bisnis", "site health",
            # Indonesian
            "data bisnis", "database bisnis", "cek booking", "laporan",
        ],
        "description": "Business management for rumahlabuh.com via Supabase",
        "handler": "business",
    },
    "location_advice": {
        "keywords": [
            "restaurant", "hotel", "where to", "near me", "recommend a",
            "near my", "nearby", "travel", "trip to", "visit",
            # Indonesian
            "makan", "dekat", "rekomendasi", "wisata", "tempat makan",
            "kuliner", "cafe", "kafe", "tempat bagus", "ke mana",
            "destinasi", "liburan", "jalan-jalan", "makanan enak",
        ],
        "description": "Location-based recommendations using your profile location",
        "handler": "location",
    },
    "whatsapp_action": {
        "keywords": [
            "whatsapp", "send wa", "whatsapp message",
            # Indonesian
            " wa ", "pesan wa", "balas wa", "chat wa", "kirim wa",
            "baca wa", "cek wa", "wa dari",
        ],
        "description": "Read and reply to WhatsApp messages",
        "handler": "whatsapp",
    },
    "github_intel": {
        "keywords": [
            "github trending", "trending repo", "new library",
            "upgrade legion", "scan github", "eval repo",
            # Indonesian
            "repo baru", "update diri", "library baru", "tools baru",
            "perbarui legion", "github terbaru",
        ],
        "description": "GitHub trending intelligence and self-evolution",
        "handler": "github_intel",
    },
    "conversation": {
        "keywords": [],
        "description": "Natural conversation, jokes, opinions, check-ins",
        "handler": "chat",
    },
}

# Skills eligible for LLM classification (all except conversation — it's the default)
_LLM_CLASSIFY_SKILLS = [s for s in SKILL_PATTERNS if s != "conversation"]


class AutonomousRouter:
    def __init__(self, memory_manager, reflection_engine) -> None:
        self.memory = memory_manager
        self.reflection = reflection_engine
        self._skill_performance: dict[str, list[float]] = {}

    def analyze(self, message: str) -> SkillMatch:
        """Route message to the best skill using keyword-match only.

        This synchronous fast path keeps test helpers and simple callers stable.
        Use `analyze_async()` when LLM fallback classification is desired.
        """
        msg_lower = message.lower().strip()
        scores: dict[str, float] = {}

        # ── Tier 1: keyword scoring ──────────────────────────────────────────
        for skill, config in SKILL_PATTERNS.items():
            if skill == "conversation":
                continue
            score = 0.0
            for keyword in config["keywords"]:
                if keyword in msg_lower:
                    # Multi-word keywords score higher
                    score += len(keyword.split()) * 0.25
            scores[skill] = score

        # Apply rolling performance history
        for skill in list(scores.keys()):
            perf = self._skill_performance.get(skill, [])
            if len(perf) >= 5:
                avg = sum(perf) / len(perf)
                if avg > 0.80:
                    scores[skill] *= 1.15   # boost well-performing skills
                elif avg < 0.50:
                    scores[skill] *= 0.85   # penalise underperforming skills

        max_score = max(scores.values()) if scores else 0.0

        if max_score < 0.25:
            # No keyword hit at all — treat as natural conversation
            return SkillMatch(
                skill_name="conversation",
                confidence=0.90,
                reasoning="No keyword match — defaulting to conversation",
            )

        best_skill = max(scores, key=scores.get)
        confidence = min(0.95, scores[best_skill] / 2.0)

        return SkillMatch(
            skill_name=best_skill,
            confidence=confidence,
            reasoning=f"Keyword match '{best_skill}' score={scores[best_skill]:.2f}",
        )

    async def analyze_async(self, message: str) -> SkillMatch:
        """Route message with keyword scoring and optional LLM fallback."""
        keyword_match = self.analyze(message)
        if keyword_match.skill_name == "conversation":
            return keyword_match

        word_count = len(message.split())
        # ── Tier 2: LLM fallback when confidence is low or message is long ───
        if keyword_match.confidence < 0.55 or word_count > 30:
            llm_match = await self._llm_classify(message)
            if llm_match is not None:
                logger.debug(
                    "[AutoRouter] LLM override: '%s...' -> %s (keyword had %s @ %.0f%%)",
                    message[:40],
                    llm_match.skill_name,
                    keyword_match.skill_name,
                    keyword_match.confidence * 100,
                )
                return llm_match

        return keyword_match

    async def _llm_classify(self, message: str) -> SkillMatch | None:
        """Call Groq Llama to classify the message into a skill category."""
        try:
            import litellm

            skill_desc = "\n".join(
                f"- {s}: {SKILL_PATTERNS[s]['description']}"
                for s in _LLM_CLASSIFY_SKILLS
            )
            prompt = (
                "You are a routing classifier for an AI assistant. "
                "Classify the user message into exactly ONE skill category.\n\n"
                f"Available skills:\n{skill_desc}\n\n"
                f'User message: "{message}"\n\n'
                "Reply with ONLY the skill name (e.g. location_advice). "
                "If the message is casual conversation, reply: conversation"
            )
            resp = await litellm.acompletion(
                model="groq/llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=20,
            )
            raw = resp.choices[0].message.content.strip().lower()
            # Normalise (strip markdown, replace spaces/dashes with underscore)
            skill_name = raw.replace("-", "_").replace(" ", "_").strip("`*")
            if skill_name not in SKILL_PATTERNS:
                skill_name = "conversation"
            return SkillMatch(
                skill_name=skill_name,
                confidence=0.80,
                reasoning=f"LLM classified as '{skill_name}'",
            )
        except Exception as exc:
            logger.warning("[AutoRouter] LLM classify failed: %s", exc)
            return None

    def record_performance(self, skill: str, success: bool) -> None:
        """Record success/failure for rolling performance tracking."""
        if skill not in self._skill_performance:
            self._skill_performance[skill] = []
        self._skill_performance[skill].append(1.0 if success else 0.0)
        if len(self._skill_performance[skill]) > 20:
            self._skill_performance[skill].pop(0)

    def get_skill_stats(self) -> dict:
        """Return per-skill success rate and usage count."""
        return {
            skill: {
                "avg_success": (sum(s) / len(s)) if s else 0.0,
                "total_uses": len(s),
            }
            for skill, s in self._skill_performance.items()
        }
