"""
task_orchestrator.py

Parallel task execution and 4-round Swarm Debate Orchestrator.

SwarmDebateOrchestrator implements a structured expert panel debate:
  ROUND 1: Parallel divergence (all 6 agents simultaneously)
  ROUND 2: Cross-examination (each agent critiques + updates)
  ROUND 3: Judge synthesis (gemini-2.0-flash as judge)
  ROUND 4: Confidence ranking (parallel)
"""
from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Debate personas ──────────────────────────────────────────────────────
DEBATE_AGENTS = [
    {
        "key": "strategist",
        "emoji": "\u2694\ufe0f",
        "model": "gemini/gemini-2.0-flash",
        "persona": (
            "You are the STRATEGIST. You think in 10-year timeframes. You prize leverage "
            "and compounding advantages. You are skeptical of tactical solutions to strategic "
            "problems. You think about second and third-order effects."
        ),
    },
    {
        "key": "devil_advocate",
        "emoji": "\ud83d\udd25",
        "model": "groq/llama-3.3-70b-versatile",
        "persona": (
            "You are the DEVIL'S ADVOCATE. Your job is to be convinced of NOTHING. "
            "Attack every assumption. Find the fatal flaw in even the best ideas. "
            "Your success = you made everyone think harder."
        ),
    },
    {
        "key": "researcher",
        "emoji": "\ud83d\udcda",
        "model": "groq/moonshotai/kimi-k2-instruct",
        "persona": (
            "You are the RESEARCHER. You cite evidence. Every claim needs a source, precedent, "
            "or data point. You are uncomfortable with speculation presented as fact."
        ),
    },
    {
        "key": "pragmatist",
        "emoji": "\ud83d\udd27",
        "model": "cerebras/qwen-3-235b",
        "persona": (
            "You are the PRAGMATIST. You ask: what breaks first? Who builds it? "
            "How long does it actually take? You've seen 100 brilliant plans die in execution."
        ),
    },
    {
        "key": "visionary",
        "emoji": "\ud83d\ude80",
        "model": "cerebras/qwen-3-235b",
        "persona": (
            "You are the VISIONARY. You think 3 steps ahead. You see connections others miss. "
            "You're willing to sound crazy if the logic holds."
        ),
    },
    {
        "key": "critic",
        "emoji": "\u2702\ufe0f",
        "model": "groq/qwen-qwq-32b",
        "persona": (
            "You are the CRITIC. You are a world-class editor. You find redundancy, weak framing, "
            "missing context. You improve everything you touch."
        ),
    },
]

JUDGE_MODEL = "gemini/gemini-2.0-flash"


class SwarmDebateOrchestrator:
    """Runs a 4-round structured expert debate and returns formatted results."""

    async def _call_agent(self, llm_client, model: str, system: str, user: str, temperature: float = 0.7) -> str:
        """Call LLM with given model and return text response."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llm_client.complete(
                    model=model,
                    messages=[{"role": "user", "content": user}],
                    system=system,
                    temperature=temperature,
                    max_tokens=512,
                )
            )
            return (result or "").strip()
        except Exception as e:
            logger.error("Agent call failed (model=%s): %s", model, e)
            return f"[error: {e}]"

    async def run_debate(self, topic: str, llm_client) -> dict:
        """
        Run the full 4-round debate.
        Returns dict with round1, round2, round3_synthesis, round4_confidence.
        """
        try:
            from agents import PERSONALITY_WRAPPER
        except ImportError:
            PERSONALITY_WRAPPER = ""

        logger.info("SwarmDebate: starting for topic: %s", topic[:80])

        # ── ROUND 1: Parallel Divergence ───────────────────────────────────
        r1_tasks = []
        for agent in DEBATE_AGENTS:
            system = PERSONALITY_WRAPPER + "\n\n" + agent["persona"]
            user = (
                f"Topic for debate: {topic}\n\n"
                "State your INITIAL POSITION on this topic. "
                "Be direct, opinionated, and concise (2-3 sentences max). "
                "This is Round 1 — stake your ground boldly."
            )
            r1_tasks.append(self._call_agent(llm_client, agent["model"], system, user, 0.8))

        r1_responses = await asyncio.gather(*r1_tasks)
        round1 = {DEBATE_AGENTS[i]["key"]: r1_responses[i] for i in range(len(DEBATE_AGENTS))}

        # ── ROUND 2: Cross-Examination (sequential to avoid rate limits) ──────────
        round2: dict[str, str] = {}
        r1_summary = "\n\n".join(
            f"{DEBATE_AGENTS[i]['emoji']} {DEBATE_AGENTS[i]['key'].upper()}: {r1_responses[i]}"
            for i in range(len(DEBATE_AGENTS))
        )
        for agent in DEBATE_AGENTS:
            system = PERSONALITY_WRAPPER + "\n\n" + agent["persona"]
            user = (
                f"Topic: {topic}\n\n"
                f"All Round 1 positions:\n{r1_summary}\n\n"
                "You are now in Round 2 — Cross-Examination.\n"
                "Do TWO things:\n"
                "1. Identify the STRONGEST FLAW in ONE other agent's Round 1 argument (name them).\n"
                "2. DEFEND or UPDATE your own position in light of what you've read.\n"
                "Keep it punchy — 3-4 sentences total."
            )
            response = await self._call_agent(llm_client, agent["model"], system, user, 0.7)
            round2[agent["key"]] = response
            await asyncio.sleep(0.5)  # small delay between sequential calls

        # ── ROUND 3: Judge Synthesis ─────────────────────────────────────────
        r2_summary = "\n\n".join(
            f"{DEBATE_AGENTS[i]['emoji']} {DEBATE_AGENTS[i]['key'].upper()} (R2): {round2[DEBATE_AGENTS[i]['key']]}"
            for i in range(len(DEBATE_AGENTS))
        )
        judge_system = (
            "You are the JUDGE of this expert debate. You have read all arguments carefully. "
            "You are impartial, incisive, and brilliant. Your job is to synthesize, not please."
        )
        judge_user = (
            f"Topic: {topic}\n\n"
            f"ROUND 1 POSITIONS:\n{r1_summary}\n\n"
            f"ROUND 2 CROSS-EXAMINATION:\n{r2_summary}\n\n"
            "Provide your synthesis in this EXACT format:\n\n"
            "CONSENSUS: [what all or most agents agree on]\n"
            "BEST_ARGUMENT: [the single strongest argument made, attribute it to the agent]\n"
            "MINORITY_VIEW: [the dissenting view worth preserving]\n"
            "FINAL_RECOMMENDATION: [your verdict on the topic in 2-3 sentences]"
        )
        judge_raw = await self._call_agent(llm_client, JUDGE_MODEL, judge_system, judge_user, 0.4)
        synthesis = _parse_judge_output(judge_raw)

        # ── ROUND 4: Confidence Ranking (parallel) ──────────────────────────
        r4_tasks = []
        verdict = synthesis.get("FINAL_RECOMMENDATION", "")
        for agent in DEBATE_AGENTS:
            system = agent["persona"]
            user = (
                f"The judge's final verdict on '{topic}' is:\n"{verdict}"\n\n"
                "Rate this verdict from 1-10 and give ONE sentence of justification. "
                "Format: SCORE: X/10 | [your justification]"
            )
            r4_tasks.append(self._call_agent(llm_client, agent["model"], system, user, 0.5))

        r4_responses = await asyncio.gather(*r4_tasks)
        round4 = {DEBATE_AGENTS[i]["key"]: r4_responses[i] for i in range(len(DEBATE_AGENTS))}

        return {
            "topic": topic,
            "round1": round1,
            "round2": round2,
            "round3_synthesis": synthesis,
            "round3_raw": judge_raw,
            "round4_confidence": round4,
        }


def _parse_judge_output(raw: str) -> dict:
    """Parse judge's structured output into a dict."""
    keys = ["CONSENSUS", "BEST_ARGUMENT", "MINORITY_VIEW", "FINAL_RECOMMENDATION"]
    result: dict[str, str] = {}
    for key in keys:
        pattern = re.compile(rf"{key}:\s*(.+?)(?=\n(?:{chr(124).join(keys)}):|$)", re.DOTALL | re.IGNORECASE)
        m = pattern.search(raw)
        result[key] = m.group(1).strip() if m else ""
    if not any(result.values()):
        result["FINAL_RECOMMENDATION"] = raw.strip()
    return result


import re  # noqa: E402 (needed at module level for _parse_judge_output)


def format_debate_for_telegram(debate_result: dict, topic: str) -> list[str]:
    """
    Format the 4-round debate into a list of Telegram message strings.
    Each string is max 4096 chars. Send each as a separate message.
    """
    from tools.telegram_formatter import split_message

    r1 = debate_result.get("round1", {})
    r2 = debate_result.get("round2", {})
    synth = debate_result.get("round3_synthesis", {})
    conf = debate_result.get("round4_confidence", {})

    topic_short = topic[:50] + ("..." if len(topic) > 50 else "")

    # Build Round 1 block
    r1_block = f"\ud83e\udde0 **SWARM DEBATE — {topic_short}**\n" + "━" * 22 + "\n\n"
    agent_display = [
        ("strategist", "\u2694\ufe0f", "STRATEGIST"),
        ("devil_advocate", "\ud83d\udd25", "DEVIL'S ADVOCATE"),
        ("researcher", "\ud83d\udcda", "RESEARCHER"),
        ("pragmatist", "\ud83d\udd27", "PRAGMATIST"),
        ("visionary", "\ud83d\ude80", "VISIONARY"),
        ("critic", "\u2702\ufe0f", "CRITIC"),
    ]
    for key, emoji, label in agent_display:
        pos = r1.get(key, "*[no response]*")
        r1_block += f"{emoji} **{label}**: {pos}\n\n"

    # Build Round 2 block
    r2_block = "━" * 22 + "\n\ud83d\udcac **ROUND 2 — Cross-Examination**\n\n"
    for key, emoji, label in agent_display:
        update = r2.get(key, "*[no response]*")
        r2_block += f"{emoji} **{label}**: {update}\n\n"

    # Build synthesis block
    consensus = synth.get("CONSENSUS", "")
    best_arg = synth.get("BEST_ARGUMENT", "")
    minority = synth.get("MINORITY_VIEW", "")
    verdict = synth.get("FINAL_RECOMMENDATION", "")

    synth_block = "━" * 22 + "\n\ud83c\udfc6 **JUDGE'S SYNTHESIS**\n\n"
    synth_block += f"**Consensus**: {consensus}\n\n"
    synth_block += f"**Best argument**: {best_arg}\n\n"
    synth_block += f"**Minority view**: {minority}\n\n"
    synth_block += f"**VERDICT**: {verdict}\n\n"

    # Confidence scores
    def _extract_score(text: str) -> str:
        m = re.search(r'(\d+)/10', text or "")
        return f"{m.group(1)}/10" if m else "?/10"

    score_parts = [
        f"Strategist {_extract_score(conf.get('strategist', ''))}",
        f"Devil {_extract_score(conf.get('devil_advocate', ''))}",
        f"Researcher {_extract_score(conf.get('researcher', ''))}",
        f"Pragmatist {_extract_score(conf.get('pragmatist', ''))}",
        f"Visionary {_extract_score(conf.get('visionary', ''))}",
        f"Critic {_extract_score(conf.get('critic', ''))}",
    ]
    synth_block += "**Confidence**: " + " · ".join(score_parts)

    full_text = r1_block + r2_block + synth_block
    return split_message(full_text)


# ── Legacy parallel task execution (kept for backward compat) ─────────────────
class TaskOrchestrator:
    """Legacy parallel task decomposition orchestrator."""

    def __init__(self, agents: list = None, llm_client: Any = None):
        self.agents = agents or []
        self.llm_client = llm_client

    async def run_parallel(
        self, task: str, agent_keys: list[str] = None
    ) -> dict[str, str]:
        """Run the same task across multiple agents in parallel."""
        from agents import AGENT_MODELS
        keys = agent_keys or list(AGENT_MODELS.keys())

        async def _run_one(key: str) -> tuple[str, str]:
            try:
                model = AGENT_MODELS.get(key, AGENT_MODELS["general"])
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.llm_client.complete(
                        model=model,
                        messages=[{"role": "user", "content": task}],
                        max_tokens=512,
                    )
                )
                return key, (result or "").strip()
            except Exception as e:
                return key, f"[error: {e}]"

        results = await asyncio.gather(*[_run_one(k) for k in keys])
        return dict(results)
