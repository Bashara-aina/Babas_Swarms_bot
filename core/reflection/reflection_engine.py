"""Reflection engine for self-critique and opinion formation."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

OPINIONS_PATH = Path.home() / ".legionswarm" / "memory" / "opinions.json"
REFLECTIONS_PATH = Path.home() / ".legionswarm" / "memory" / "reflections.json"
REFLECTION_EVERY_N = 10


class ReflectionEngine:
    def __init__(self, memory_manager, llm_client) -> None:
        self.memory = memory_manager
        self.llm = llm_client
        self._opinions: dict[str, list[str]] = self._load_opinions()
        self._reflections: list[dict[str, Any]] = self._load_reflections()
        self._turn_count = 0

    def _load_opinions(self) -> dict[str, list[str]]:
        if OPINIONS_PATH.exists():
            return json.loads(OPINIONS_PATH.read_text(encoding="utf-8"))
        return {
            "technical": [],
            "about_user": [],
            "lessons": [],
            "disagreements": [],
        }

    def _load_reflections(self) -> list[dict[str, Any]]:
        if REFLECTIONS_PATH.exists():
            return json.loads(REFLECTIONS_PATH.read_text(encoding="utf-8"))
        return []

    def _save_opinions(self) -> None:
        OPINIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        OPINIONS_PATH.write_text(json.dumps(self._opinions, indent=2, ensure_ascii=False), encoding="utf-8")

    def _save_reflections(self) -> None:
        REFLECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        REFLECTIONS_PATH.write_text(json.dumps(self._reflections, indent=2, ensure_ascii=False), encoding="utf-8")

    async def post_turn_hook(self, user_msg: str, assistant_response: str) -> None:
        self._turn_count += 1
        await self._micro_reflect(user_msg, assistant_response)
        if self._turn_count % REFLECTION_EVERY_N == 0:
            await self._deep_reflect()

    async def _micro_reflect(self, user_msg: str, response: str) -> None:
        msg_lower = user_msg.lower()
        correction_signals = [
            "no, that's wrong",
            "actually",
            "that's not right",
            "incorrect",
            "you're wrong",
            "not quite",
            "wrong approach",
        ]

        for signal in correction_signals:
            if signal in msg_lower:
                lesson = f"[{datetime.now():%Y-%m-%d}] User corrected me on: '{user_msg[:100]}'"
                self._opinions["lessons"].append(lesson)
                if len(self._opinions["lessons"]) > 100:
                    self._opinions["lessons"].pop(0)
                await self.memory.save(
                    content=lesson,
                    summary="Legion was corrected by user",
                    tags=["correction", "lesson", "self-improvement"],
                    importance=0.85,
                    source="micro-reflection",
                )
                self._save_opinions()
                break
        _ = response

    async def _deep_reflect(self) -> None:
        try:
            recent = self.memory.recall.get_recent(n=30)
            if len(recent) < 5:
                return

            history_text = "\n".join(f"{t['role'].upper()}: {str(t['content'])[:200]}" for t in recent[-20:])
            existing = json.dumps(self._opinions.get("about_user", [])[-10:], ensure_ascii=False)

            reflection_prompt = f"""You are Legion, doing private self-reflection.
Review this recent conversation history with Bashara and generate insights.

RECENT HISTORY:
{history_text}

YOUR EXISTING OBSERVATIONS ABOUT BASHARA:
{existing}

Now generate JSON with keys:
- new_observation
- technical_opinion
- self_improvement
- concern (or null)

Be specific and evidence-based."""

            response = await self.llm.complete(
                messages=[{"role": "user", "content": reflection_prompt}],
                model="opencode-go/minimax-m3",
                temperature=0.7,
                max_tokens=500,
                skip_post_hooks=True,
            )

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if not match:
                return
            reflection = json.loads(match.group())

            obs = reflection.get("new_observation")
            if obs:
                self._opinions["about_user"].append(f"[{datetime.now():%Y-%m-%d}] {obs}")
                await self.memory.save(obs, tags=["reflection", "user-pattern"], importance=0.80, source="deep-reflection")

            tech = reflection.get("technical_opinion")
            if tech:
                self._opinions["technical"].append(f"[{datetime.now():%Y-%m-%d}] {tech}")
                await self.memory.save(tech, tags=["reflection", "technical-opinion"], importance=0.75, source="deep-reflection")

            imp = reflection.get("self_improvement")
            if imp:
                self._opinions["lessons"].append(f"[{datetime.now():%Y-%m-%d}] Self-improvement: {imp}")

            concern = reflection.get("concern")
            if concern:
                self._opinions["disagreements"].append(f"[{datetime.now():%Y-%m-%d}] CONCERN: {concern}")
                await self.memory.save(
                    f"I have a concern about Bashara's direction: {concern}",
                    tags=["concern", "disagreement"],
                    importance=0.90,
                    source="deep-reflection",
                )

            for key in self._opinions:
                if len(self._opinions[key]) > 50:
                    self._opinions[key] = self._opinions[key][-50:]

            self._save_opinions()
            self._reflections.append({"timestamp": datetime.now().isoformat(), "reflection": reflection})
            if len(self._reflections) > 200:
                self._reflections.pop(0)
            self._save_reflections()
            logger.info("[Reflection] Deep reflection complete. Turn %s.", self._turn_count)
        except Exception as exc:
            logger.warning("[Reflection] Deep reflect failed: %s", exc)

    def get_opinions_block(self) -> str:
        recent_observations = self._opinions.get("about_user", [])[-5:]
        recent_technical = self._opinions.get("technical", [])[-3:]
        concerns = self._opinions.get("disagreements", [])[-3:]
        lessons = self._opinions.get("lessons", [])[-3:]

        if not any([recent_observations, recent_technical, concerns, lessons]):
            return ""

        lines = ["[LEGION'S CURRENT THOUGHTS AND OPINIONS]"]
        if recent_observations:
            lines.append("Observations about Bashara:")
            lines.extend(f"  - {item}" for item in recent_observations)
        if recent_technical:
            lines.append("Technical opinions I hold:")
            lines.extend(f"  - {item}" for item in recent_technical)
        if concerns:
            lines.append("Active concerns I want to address:")
            lines.extend(f"  - {item}" for item in concerns)
        if lessons:
            lines.append("Recent lessons learned:")
            lines.extend(f"  - {item}" for item in lessons)
        lines.append("Use these organically when relevant.")
        return "\n".join(lines)
