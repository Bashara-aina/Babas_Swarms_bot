"""Legion task router — Manus-killer routing layer (v4).

Classifies plain-text tasks and runs **parallel** specialist :func:`llm_client.chat` paths
where useful. Sits *before* :class:`core.autonomous_router.AutonomousRouter` when
``LEGION_TASK_ROUTER_ENABLED=1``.

Returns ``None`` for ``simple_chat`` so existing chat + autonomous routing continue unchanged.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections.abc import Awaitable, Callable
from enum import StrEnum

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://[^\s<>\"']+")


class TaskType(StrEnum):
    SIMPLE_CHAT = "simple_chat"
    RESEARCH = "research"
    CODE = "code"
    BROWSER = "browser"
    DOCUMENT = "document"
    COMPUTER_CONTROL = "computer_control"
    SIMULATION = "simulation"
    MULTI_STEP = "multi_step"
    DEBATE = "debate"


# Order matters: first match wins (put more specific routes first).
KEYWORD_ROUTES: list[tuple[TaskType, tuple[str, ...]]] = [
    (
        TaskType.SIMULATION,
        (
            "what if ",
            "simulate ",
            "how would ",
            "market reaction",
            "pros and cons",
            "should i launch",
            "scenario ",
        ),
    ),
    (
        TaskType.DEBATE,
        (
            "devil's advocate",
            "argue for and against",
            "debate whether",
            "is this a good idea",
            "challenge my assumption",
        ),
    ),
    (
        TaskType.DOCUMENT,
        (
            "business plan",
            "technical spec",
            "investment analysis",
            "research report on",
            "prd for",
            "architecture design for",
            "competitive analysis",
            "market analysis of",
            "write a formal report",
        ),
    ),
    (
        TaskType.BROWSER,
        (
            "open https://",
            "go to https://",
            "go to http://",
            "fetch the page",
            "scrape https://",
            "check the site ",
            "look up on the website",
        ),
    ),
    (
        TaskType.COMPUTER_CONTROL,
        (
            "take a screenshot",
            "on my screen",
            "open terminal",
            "run on my machine",
            "click at ",
            "xdotool",
        ),
    ),
    (
        TaskType.CODE,
        (
            "traceback",
            "syntaxerror",
            "attributeerror",
            "pull request",
            "refactor this",
            "implement ",
            "write tests for",
            "github issue",
            "stack trace",
        ),
    ),
    (
        TaskType.RESEARCH,
        (
            "find papers on",
            "literature review",
            "compare vendors",
            "survey of ",
            "deep research on",
        ),
    ),
]


def keyword_task_type(message: str) -> TaskType | None:
    """Fast keyword-only classification; ``None`` if no strong signal."""
    low = (message or "").lower()
    for ttype, kws in KEYWORD_ROUTES:
        if any(k in low for k in kws):
            return ttype
    return None


class TaskRouter:
    """Route high-value tasks to specialist flows; return ``None`` → normal chat stack."""

    def __init__(self) -> None:
        self._classify_model = os.getenv(
            "LEGION_TASK_ROUTER_CLASSIFY_MODEL",
            "minimax/MiniMax-M2.7",
        )

    async def route(
        self,
        message: str,
        *,
        context: str = "",
        user_id: str = "0",
        stream_callback: Callable[[str], Awaitable[None]] | None = None,
    ) -> str | None:
        t = await self.classify(message)
        logger.info("[TaskRouter] classified as %s", t.value)

        if t == TaskType.SIMPLE_CHAT:
            return None

        if stream_callback:
            await stream_callback(f"Routed: {t.value.replace('_', ' ')}")

        if t == TaskType.RESEARCH:
            return await self._run_research(message, user_id, context)
        if t == TaskType.CODE:
            return await self._run_code(message, user_id, context)
        if t == TaskType.BROWSER:
            return await self._run_browser(message, user_id, context)
        if t == TaskType.DOCUMENT:
            return await self._run_document(message, user_id, context)
        if t == TaskType.COMPUTER_CONTROL:
            return await self._run_computer(message, context)
        if t == TaskType.SIMULATION:
            return await self._run_simulation(message, context)
        if t == TaskType.DEBATE:
            return await self._run_debate(message, user_id)
        if t == TaskType.MULTI_STEP:
            return await self._run_multi_step(message, user_id, context)
        return None

    async def classify(self, message: str) -> TaskType:
        msg = (message or "").strip()
        if not msg:
            return TaskType.SIMPLE_CHAT

        kw = keyword_task_type(msg)
        if kw is not None:
            return kw

        if len(msg) < 72 and "?" not in msg and "\n" not in msg:
            return TaskType.SIMPLE_CHAT

        return await self._llm_classify_task(msg)

    async def _llm_classify_task(self, message: str) -> TaskType:
        prompt = (
            "Classify the user message into exactly ONE task type.\n"
            "Allowed: simple_chat | research | code | browser | document | "
            "computer_control | simulation | multi_step | debate\n\n"
            "simple_chat: greetings, thanks, short opinion, casual <2 sentences.\n"
            "research: web/academic facts, competitors, deep 'what is X'.\n"
            "code: programming, bugs, APIs, repos.\n"
            "browser: must load a site or complex UI interaction.\n"
            "document: formal multi-section deliverable (PRD, memo, plan).\n"
            "computer_control: control Ubuntu desktop/apps.\n"
            "simulation: predict reactions, scenarios, what-if.\n"
            "multi_step: needs several capabilities (research+code+browser).\n"
            "debate: opposing arguments / devil's advocate.\n\n"
            f"Message:\n{message[:1800]}\n\nReply with ONLY the type word."
        )
        try:
            from litellm import acompletion

            resp = await acompletion(
                model=self._classify_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=24,
            )
            token = (resp.choices[0].message.content or "").strip().lower()
            token = token.replace("-", "_")
            if token:
                token = token.split()[0].strip("`*")
            if not token:
                return TaskType.SIMPLE_CHAT
            return TaskType(token)
        except ValueError:
            return TaskType.SIMPLE_CHAT
        except Exception as exc:
            logger.warning("[TaskRouter] LLM classify failed: %s", exc)
            return TaskType.RESEARCH

    async def _run_research(self, message: str, user_id: str, context: str) -> str:
        if os.getenv("LEGION_RESEARCH_USE_PIPELINE", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        ):
            try:
                from agents.research_agent import run_research_pipeline

                return await run_research_pipeline(message, user_id=user_id)
            except Exception as exc:
                logger.warning("[TaskRouter] research pipeline failed: %s", exc)
        from llm_client import chat

        enriched = f"{message}\n\n{context}" if context else message
        text, _ = await chat(enriched, agent_key="researcher", user_id=user_id)
        return text

    async def _run_code(self, message: str, user_id: str, context: str) -> str:
        from llm_client import chat

        enriched = f"{message}\n\n{context}" if context else message
        text, _ = await chat(enriched, agent_key="coding", user_id=user_id)
        return text

    async def _run_browser(self, message: str, user_id: str, context: str) -> str:
        urls = _URL_RE.findall(message)
        from llm_client import chat
        from tools.browser_tool import fetch_page_text

        parts: list[str] = []
        for url in urls[:3]:
            body = await fetch_page_text(url, max_chars=10000)
            parts.append(f"### {url}\n{body[:8000]}")
        if not parts:
            q = (message + ("\n\n" + context if context else ""))[:2000]
            text, _ = await chat(
                "User wants browser-like info but gave no URL. Explain you need a link, or use /scrape <url>.\n\n" + q,
                agent_key="general",
                user_id=user_id,
            )
            return text
        bundle = "\n\n".join(parts)
        prompt = (
            f"User request:\n{message}\n\nFetched page text:\n{bundle}\n\n"
            "Summarize what matters for the user. Say which URL each claim comes from."
        )
        text, _ = await chat(prompt, agent_key="researcher", user_id=user_id)
        return text

    async def _run_document(self, message: str, user_id: str, context: str) -> str:
        roles = (
            ("pm", "You are a product lead: goals, scope, success metrics."),
            ("architect", "You are a systems architect: components, risks, stack."),
            ("analyst", "You are an analyst: data, competitors, recommendations."),
            ("reviewer", "You are a sharp critic: gaps, counterpoints, pre-mortem."),
        )
        ctx = (context or "")[:600]

        async def one(role_key: str, instr: str) -> tuple[str, str]:
            from llm_client import chat

            body = f"{instr}\n\nRequest:\n{message}\n\nContext:\n{ctx}"
            out, _ = await chat(body, agent_key=role_key, user_id=user_id)
            return role_key, out

        results = await asyncio.gather(
            *[one(k, i) for k, i in roles],
            return_exceptions=True,
        )
        sections: list[str] = []
        for r in results:
            if isinstance(r, Exception):
                sections.append(f"## error\n{r}")
                continue
            role_key, content = r
            sections.append(f"## {role_key}\n{content}")

        from llm_client import chat

        synth_prompt = (
            "Merge these parallel expert sections into one polished markdown document "
            "(executive summary, unified narrative, recommendations, next steps). "
            "Remove redundancy.\n\n" + "\n\n".join(sections)
        )
        final, _ = await chat(synth_prompt, agent_key="architect", user_id=user_id)
        return final

    async def _run_computer(self, message: str, context: str) -> str:
        from tools.agent_s_tool import AgentSTool

        return await AgentSTool().execute_task(message, context=context or None)

    async def _run_simulation(self, message: str, context: str) -> str:
        from agents.simulation_agent import run_simulation_agent

        return await run_simulation_agent(message, context=context or "")

    async def _run_debate(self, message: str, user_id: str) -> str:
        from llm_client import chat

        prop = message[:1200]
        pro, con = await asyncio.gather(
            chat(
                f"Argue strongly FOR (bullet points, evidence):\n{prop}",
                agent_key="analyst",
                user_id=user_id,
            ),
            chat(
                f"Argue strongly AGAINST (bullet points, evidence):\n{prop}",
                agent_key="reviewer",
                user_id=user_id,
            ),
        )
        judge_prompt = (
            "Synthesize a balanced verdict.\n\n"
            f"FOR:\n{pro[0]}\n\nAGAINST:\n{con[0]}\n\n"
            "Give: verdict, key insights, recommended action."
        )
        final, _ = await chat(judge_prompt, agent_key="think", user_id=user_id)
        return final

    async def _run_multi_step(self, message: str, user_id: str, context: str) -> str:
        plan_raw = await self._decompose_json(message, context)
        subtasks = plan_raw.get("subtasks") or [{"agent": "research", "task": message}]
        max_p = int(os.getenv("LEGION_TASK_ROUTER_MAX_PARALLEL", "4"))
        if isinstance(subtasks, list):
            subtasks = subtasks[:max_p]
        else:
            subtasks = [{"agent": "research", "task": message}]

        async def run_one(st: object) -> str:
            if not isinstance(st, dict):
                st = {"agent": "research", "task": message}
            key = str(st.get("agent", "research")).lower()
            task = str(st.get("task", message))[:2000]
            agent_map = {
                "research": "researcher",
                "browser": "researcher",
                "code": "coding",
                "analyst": "analyst",
                "fact_checker": "reviewer",
            }
            agent_key = agent_map.get(key, "general")
            if key == "browser":
                urls = _URL_RE.findall(task)
                if urls:
                    from tools.browser_tool import fetch_page_text

                    chunks = [await fetch_page_text(u, max_chars=6000) for u in urls[:2]]
                    task = task + "\n\n" + "\n".join(chunks)[:10000]
            from llm_client import chat

            out, _ = await chat(
                f"{task}\n\nShared context:\n{(context or '')[:500]}",
                agent_key=agent_key,
                user_id=user_id,
            )
            return f"[{agent_key}] {out}"

        outs = await asyncio.gather(
            *[run_one(st) for st in subtasks],
            return_exceptions=True,
        )
        lines: list[str] = []
        for i, o in enumerate(outs):
            if isinstance(o, Exception):
                lines.append(f"Subtask {i + 1} error: {o}")
            else:
                lines.append(str(o))
        bundle = "\n\n---\n\n".join(lines)
        from llm_client import chat

        final, _ = await chat(
            f"User goal:\n{message}\n\nParallel results:\n{bundle}\n\n"
            "Write Legion's single cohesive answer. Do not mention 'subtasks'.",
            agent_key="architect",
            user_id=user_id,
        )
        return final

    async def _decompose_json(self, message: str, context: str) -> dict:
        schema = '{"subtasks":[{"agent":"research","task":"..."},{"agent":"code","task":"..."}]}'
        prompt = (
            "Decompose into parallel subtasks. Max 4. Reply with JSON only, no markdown.\n"
            f"Schema example: {schema}\n"
            "agent must be one of: research, browser, code, analyst, fact_checker\n\n"
            f"Task:\n{message[:1500]}\n\nContext:\n{(context or '')[:400]}"
        )
        try:
            from litellm import acompletion

            resp = await acompletion(
                model=self._classify_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=400,
            )
            raw = (resp.choices[0].message.content or "").strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            if isinstance(data, dict) and isinstance(data.get("subtasks"), list):
                return data
        except Exception as exc:
            logger.warning("[TaskRouter] decompose failed: %s", exc)
        return {"subtasks": [{"agent": "research", "task": message}]}


_task_router: TaskRouter | None = None


def get_task_router() -> TaskRouter:
    global _task_router
    if _task_router is None:
        _task_router = TaskRouter()
    return _task_router
