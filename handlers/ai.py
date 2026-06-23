"""AI agent handlers: /run /think /agent /swarm /multi_execute /orchestrate /multi_plan /loop* + NL."""  # type: ignore[reportOptionalMemberAccess]

from __future__ import annotations

import asyncio
import contextlib
import html as html_mod
import time

from aiogram import F, Router  # type: ignore[reportOptionalMemberAccess]
from aiogram.filters import Command  # type: ignore[reportOptionalMemberAccess]
from aiogram.types import Message  # type: ignore[reportOptionalMemberAccess]

import handlers.shared as _shared  # type: ignore[reportOptionalMemberAccess]
import router as agents

from .shared import (  # type: ignore[reportOptionalMemberAccess]
    _execute_chat,  # type: ignore[reportOptionalMemberAccess]
    _keep_typing,  # type: ignore[reportOptionalMemberAccess]
    _run_agent_loop,  # type: ignore[reportOptionalMemberAccess]
    _user_thread,  # type: ignore[reportOptionalMemberAccess]
    is_allowed,  # type: ignore[reportOptionalMemberAccess]
    send_chunked,  # type: ignore[reportOptionalMemberAccess]
)

router = Router()  # type: ignore[reportOptionalMemberAccess]


async def _send_swarm_visualization(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Send current swarm observability view for the calling user."""  # type: ignore[reportOptionalMemberAccess]
    if not msg.from_user:  # type: ignore[reportOptionalMemberAccess]
        return
    from tools.swarm_observability import (
        build_swarm_viz_html,  # type: ignore[reportOptionalMemberAccess]
    )

    report = build_swarm_viz_html(msg.from_user.id)  # type: ignore[reportOptionalMemberAccess]
    await send_chunked(msg, report, model_used="swarm-observability")  # type: ignore[reportOptionalMemberAccess]


# ── /think ────────────────────────────────────────────────────────────────────
@router.message(Command("think"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_think(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Handle /think command — layered extended thinking with adversarial critique."""  # type: ignore[reportOptionalMemberAccess]
    raw = (msg.text or "").removeprefix("/think").strip()  # type: ignore[reportOptionalMemberAccess]
    from core.agent import cmd_think_impl  # type: ignore[reportOptionalMemberAccess]

    await cmd_think_impl(  # type: ignore[reportOptionalMemberAccess]
        msg,  # type: ignore[reportOptionalMemberAccess]
        raw,  # type: ignore[reportOptionalMemberAccess]
        is_allowed_fn=is_allowed,  # type: ignore[reportOptionalMemberAccess]
        keep_typing_fn=_keep_typing,  # type: ignore[reportOptionalMemberAccess]
        send_chunked_fn=send_chunked,  # type: ignore[reportOptionalMemberAccess]
    )


# ── /run ──────────────────────────────────────────────────────────────────────
@router.message(Command("run"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_run(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Handle /run command — LLM chat only, no computer access."""  # type: ignore[reportOptionalMemberAccess]
    task = (msg.text or "").removeprefix("/run").strip()  # type: ignore[reportOptionalMemberAccess]
    from core.agent import cmd_run_impl  # type: ignore[reportOptionalMemberAccess]

    await cmd_run_impl(  # type: ignore[reportOptionalMemberAccess]
        msg,  # type: ignore[reportOptionalMemberAccess]
        task,  # type: ignore[reportOptionalMemberAccess]
        is_allowed_fn=is_allowed,  # type: ignore[reportOptionalMemberAccess]
        execute_chat_fn=_execute_chat,  # type: ignore[reportOptionalMemberAccess]
    )


# ── /agent ────────────────────────────────────────────────────────────────────
@router.message(Command("agent"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_agent(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    parts = (msg.text or "").split(maxsplit=2)  # type: ignore[reportOptionalMemberAccess]
    if len(parts) < 3:  # type: ignore[reportOptionalMemberAccess]
        valid = ", ".join(agents.AGENT_MODELS.keys())  # type: ignore[reportOptionalMemberAccess]
        await msg.answer(  # type: ignore[reportOptionalMemberAccess]
            f"usage: <code>/agent &lt;key&gt; &lt;task&gt;</code>\nkeys: <code>{valid}</code>",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )
        return
    key, task = parts[1].lower(), parts[2]  # type: ignore[reportOptionalMemberAccess]
    if key not in agents.AGENT_MODELS:  # type: ignore[reportOptionalMemberAccess]
        await msg.answer(f"unknown agent: <code>{key}</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return
    await _execute_chat(msg, task, forced_agent=key)  # type: ignore[reportOptionalMemberAccess]


# ── /swarm — multi-agent team execution ──────────────────────────────────────
@router.message(Command("swarm"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_swarm(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    raw = (msg.text or "").removeprefix("/swarm").strip()  # type: ignore[reportOptionalMemberAccess]
    if not raw:
        await msg.answer(  # type: ignore[reportOptionalMemberAccess]
            "usage: <code>/swarm [--sdk] [--topology auto|spreadsheet|mixture|graph|sequential|concurrent|debate] &lt;task&gt;</code>",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )
        return

    from core.swarm_args import parse_swarm_args  # type: ignore[reportOptionalMemberAccess]

    args = parse_swarm_args(raw)  # type: ignore[reportOptionalMemberAccess]
    use_sdk = args.use_sdk  # type: ignore[reportOptionalMemberAccess]
    topology = args.topology  # type: ignore[reportOptionalMemberAccess]
    task = args.task  # type: ignore[reportOptionalMemberAccess]
    if not task:
        await msg.answer("missing task after flags", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return

    status = await msg.answer("🧠 running swarm…")  # type: ignore[reportOptionalMemberAccess]
    typing_task = asyncio.create_task(_keep_typing(msg))  # type: ignore[reportOptionalMemberAccess]
    try:
        if use_sdk:
            from core.openai_agents_bridge import (
                run_with_handoffs,  # type: ignore[reportOptionalMemberAccess]
            )

            result = await run_with_handoffs(task=task, start_agent="general")  # type: ignore[reportOptionalMemberAccess]
            await status.delete()  # type: ignore[reportOptionalMemberAccess]
            await send_chunked(msg, result.final_output or "(empty output)", model_used="swarm/openai-agents")  # type: ignore[reportOptionalMemberAccess]
            return

        if topology == "auto":  # type: ignore[reportOptionalMemberAccess]
            try:
                from agents.mirofish_agent import (
                    MiroFishAgent,  # type: ignore[reportOptionalMemberAccess]
                )

                score = await MiroFishAgent().score_task_complexity(task)  # type: ignore[reportOptionalMemberAccess]
                if score >= 7:  # type: ignore[reportOptionalMemberAccess]
                    topology = "mixture"  # type: ignore[reportOptionalMemberAccess]
                elif score <= 3:  # type: ignore[reportOptionalMemberAccess]
                    topology = "sequential"  # type: ignore[reportOptionalMemberAccess]
                else:
                    topology = "concurrent"  # type: ignore[reportOptionalMemberAccess]
            except Exception:
                topology = "sequential"  # type: ignore[reportOptionalMemberAccess]

        from core.swarm_agent_selector import (
            get_selector,  # type: ignore[reportOptionalMemberAccess]
        )
        from core.swarm_topologies import run_topology  # type: ignore[reportOptionalMemberAccess]

        selector = get_selector()  # type: ignore[reportOptionalMemberAccess]
        team = selector.select(task, top_k=5, min_score=0.8)  # type: ignore[reportOptionalMemberAccess]
        agent_names = [a["key"] for a in team]  # type: ignore[reportOptionalMemberAccess]

        result = await run_topology(task=task, topology=topology, agent_names=agent_names)  # type: ignore[reportOptionalMemberAccess]
        await status.delete()  # type: ignore[reportOptionalMemberAccess]
        await send_chunked(msg, result.final_output or "(empty output)", model_used=f"swarm/{result.topology_used}")  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await status.edit_text(f"swarm error: <code>{html_mod.escape(str(e)[:400])}</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
    finally:
        typing_task.cancel()  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("owl"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_owl(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    task = (msg.text or "").removeprefix("/owl").strip()  # type: ignore[reportOptionalMemberAccess]
    if not task:
        await msg.answer("usage: <code>/owl &lt;task&gt;</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return
    status = await msg.answer("🦉 OWL Agent activated (GAIA-style specialist)…")  # type: ignore[reportOptionalMemberAccess]
    try:
        from agents.owl_agent import run_owl_task  # type: ignore[reportOptionalMemberAccess]

        result = await run_owl_task(task)  # type: ignore[reportOptionalMemberAccess]
        await status.delete()  # type: ignore[reportOptionalMemberAccess]
        await send_chunked(msg, result, model_used="owl")  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await status.edit_text(f"owl error: <code>{html_mod.escape(str(e)[:300])}</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("predict"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_predict(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    question = (msg.text or "").removeprefix("/predict").strip()  # type: ignore[reportOptionalMemberAccess]
    if not question:
        await msg.answer("usage: <code>/predict &lt;question&gt;</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return
    from agents.mirofish_agent import MiroFishAgent  # type: ignore[reportOptionalMemberAccess]

    result = await MiroFishAgent().predict(question)  # type: ignore[reportOptionalMemberAccess]
    text = (  # type: ignore[reportOptionalMemberAccess]
        "<b>🔮 Swarm Consensus</b>\n"
        f"Confidence: <code>{result.confidence_score:.2f}</code>\n\n"  # type: ignore[reportOptionalMemberAccess]
        f"{html_mod.escape(result.prediction)}\n\n"  # type: ignore[reportOptionalMemberAccess]
        f"Dissenting view: {html_mod.escape(' | '.join(result.dissenting_views[:3]))}"  # type: ignore[reportOptionalMemberAccess]
    )
    await send_chunked(msg, text, model_used="mirofish")  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("code_exec"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_code_exec(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    task = (msg.text or "").removeprefix("/code_exec").strip()  # type: ignore[reportOptionalMemberAccess]
    if not task:
        await msg.answer("usage: <code>/code_exec &lt;task&gt;</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return
    status = await msg.answer("⚙️ running code execution agent…")  # type: ignore[reportOptionalMemberAccess]
    try:
        from agents.code_agent import run_code_agent  # type: ignore[reportOptionalMemberAccess]

        result = await run_code_agent(task)  # type: ignore[reportOptionalMemberAccess]
        await status.delete()  # type: ignore[reportOptionalMemberAccess]
        payload = (  # type: ignore[reportOptionalMemberAccess]
            "<b>Code</b>\n<pre>" + html_mod.escape(result.code[:3500]) + "</pre>\n"  # type: ignore[reportOptionalMemberAccess]
            "<b>Stdout</b>\n<pre>" + html_mod.escape(result.stdout[:3000]) + "</pre>\n"  # type: ignore[reportOptionalMemberAccess]
            "<b>Stderr</b>\n<pre>" + html_mod.escape(result.stderr[:1200]) + "</pre>\n"  # type: ignore[reportOptionalMemberAccess]
            f"Exit: <code>{result.exit_code}</code> | Time: <code>{result.execution_time_ms:.1f} ms</code>"  # type: ignore[reportOptionalMemberAccess]
        )
        await send_chunked(msg, payload, model_used="code_exec")  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await status.edit_text(f"code_exec error: <code>{html_mod.escape(str(e)[:300])}</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("ag2"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_ag2(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    task = (msg.text or "").removeprefix("/ag2").strip()  # type: ignore[reportOptionalMemberAccess]
    if not task:
        await msg.answer("usage: <code>/ag2 &lt;task&gt;</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return
    status = await msg.answer("🧪 AG2 research swarm running…")  # type: ignore[reportOptionalMemberAccess]
    try:
        from agents.ag2_pipeline import (
            run_ag2_conversation,  # type: ignore[reportOptionalMemberAccess]
        )

        result = await run_ag2_conversation(task, max_turns=6)  # type: ignore[reportOptionalMemberAccess]
        await status.delete()  # type: ignore[reportOptionalMemberAccess]
        transcript = "\n\n".join(f"[{t.speaker}] {t.content}" for t in result.turns)  # type: ignore[reportOptionalMemberAccess]
        text = (  # type: ignore[reportOptionalMemberAccess]
            "<b>AG2 Output</b>\n"
            f"{html_mod.escape(result.output)}\n\n"  # type: ignore[reportOptionalMemberAccess]
            "<tg-spoiler>" + html_mod.escape(transcript[:8000]) + "</tg-spoiler>"  # type: ignore[reportOptionalMemberAccess]
        )
        await send_chunked(msg, text, model_used="ag2")  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await status.edit_text(f"ag2 error: <code>{html_mod.escape(str(e)[:300])}</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("swarm_viz"))  # type: ignore[reportOptionalMemberAccess]
@router.message(Command("agents_viz"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_swarm_viz(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Visualize departments, swarm thoughts, communication, and conclusion path."""  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    if not msg.from_user:  # type: ignore[reportOptionalMemberAccess]
        return
    try:
        await _send_swarm_visualization(msg)  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await msg.answer(  # type: ignore[reportOptionalMemberAccess]
            f"swarm visualization error: <code>{html_mod.escape(str(e)[:400])}</code>",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )


# ── /multi_execute — Same task, multiple agents ──────────────────────────────
@router.message(Command("multi_execute"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_multi_execute(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Execute same task with multiple agents and compare results."""  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    task = (msg.text or "").removeprefix("/multi_execute").strip()  # type: ignore[reportOptionalMemberAccess]
    if not task:
        await msg.answer(  # type: ignore[reportOptionalMemberAccess]
            "<b>usage:</b> <code>/multi_execute &lt;task&gt;</code>\n\n"
            "Runs the same task with 3 agents and compares results.\n"  # type: ignore[reportOptionalMemberAccess]
            "Optionally specify agents: <code>/multi_execute --agents=coding,debug,analyst &lt;task&gt;</code>",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )
        return

    # FIX #3: Safe --agents= parser — guard against ValueError when no space follows flag value  # type: ignore[reportOptionalMemberAccess]
    agent_keys = ["coding", "architect", "analyst"]  # type: ignore[reportOptionalMemberAccess]
    if "--agents=" in task:  # type: ignore[reportOptionalMemberAccess]
        parts = task.split("--agents=", 1)  # type: ignore[reportOptionalMemberAccess]
        remainder = parts[1]  # type: ignore[reportOptionalMemberAccess]
        if " " in remainder:
            agent_str, task = remainder.split(" ", 1)  # type: ignore[reportOptionalMemberAccess]
            task = task.strip()  # type: ignore[reportOptionalMemberAccess]
        else:
            # Flag present but no task after agent list
            agent_str = remainder  # type: ignore[reportOptionalMemberAccess]
            task = ""  # type: ignore[reportOptionalMemberAccess]
        agent_keys = [a.strip() for a in agent_str.split(",") if a.strip()]  # type: ignore[reportOptionalMemberAccess]

    if not task:
        await msg.answer(  # type: ignore[reportOptionalMemberAccess]
            "\u26a0\ufe0f No task provided after <code>--agents=</code>.\n"  # type: ignore[reportOptionalMemberAccess]
            "Usage: <code>/multi_execute --agents=coding,debug &lt;task&gt;</code>",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )
        return

    status_msg = await msg.answer(f"🧠 [Plan] preparing {len(agent_keys)} agents…")  # type: ignore[reportOptionalMemberAccess]
    started_at = time.time()  # type: ignore[reportOptionalMemberAccess]
    typing_task = asyncio.create_task(_keep_typing(msg))  # type: ignore[reportOptionalMemberAccess]

    async def _phase(text: str) -> None:  # type: ignore[reportOptionalMemberAccess]
        try:
            if text.startswith("💭"):  # type: ignore[reportOptionalMemberAccess]
                await msg.answer(f"<i>{html_mod.escape(text)}</i>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
            else:
                await status_msg.edit_text(html_mod.escape(text), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        except Exception:
            pass

    try:
        from llm_client import chat
        from tools.capability_metrics import (
            record_capability_run,  # type: ignore[reportOptionalMemberAccess]
        )
        from tools.quality_guard import (  # type: ignore[reportOptionalMemberAccess]
            analyze_answer_consistency,  # type: ignore[reportOptionalMemberAccess]
            build_evidence_envelope,  # type: ignore[reportOptionalMemberAccess]
            enforce_grounded_answer,  # type: ignore[reportOptionalMemberAccess]
            is_research_like,  # type: ignore[reportOptionalMemberAccess]
            verify_and_repair,  # type: ignore[reportOptionalMemberAccess]
        )

        user_id = str(msg.from_user.id) if msg.from_user else "0"  # type: ignore[reportOptionalMemberAccess]

        evidence_bundle = ""  # type: ignore[reportOptionalMemberAccess]
        if is_research_like(task):  # type: ignore[reportOptionalMemberAccess]
            await _phase("🌐 [Act] collecting fused evidence (web + arXiv + memory) for all agents")  # type: ignore[reportOptionalMemberAccess]
            try:
                from tools.quality_guard import (
                    gather_fused_evidence,  # type: ignore[reportOptionalMemberAccess]
                )

                fused = await gather_fused_evidence(  # type: ignore[reportOptionalMemberAccess]
                    task,  # type: ignore[reportOptionalMemberAccess]
                    user_id=user_id,  # type: ignore[reportOptionalMemberAccess]
                    min_sources=5,  # type: ignore[reportOptionalMemberAccess]
                    start_pages=8,  # type: ignore[reportOptionalMemberAccess]
                    max_pages=18,  # type: ignore[reportOptionalMemberAccess]
                    max_attempts=3,  # type: ignore[reportOptionalMemberAccess]
                )
                evidence_bundle = str(fused.get("evidence", "") or "")  # type: ignore[reportOptionalMemberAccess]
                await _phase("💭 collected live sources; grounding agent outputs with evidence")  # type: ignore[reportOptionalMemberAccess]
            except Exception as evidence_error:
                await _phase(f"💭 evidence retrieval failed, continuing with model-only pass: {evidence_error}")  # type: ignore[reportOptionalMemberAccess]

        augmented_task = task  # type: ignore[reportOptionalMemberAccess]
        if evidence_bundle:
            augmented_task = (  # type: ignore[reportOptionalMemberAccess]
                f"Task:\n{task}\n\n"
                "Use the following live evidence as grounding context. "  # type: ignore[reportOptionalMemberAccess]
                "Do not invent unsupported claims.\n\n"  # type: ignore[reportOptionalMemberAccess]
                f"Evidence:\n{evidence_bundle[:18000]}"
            )

        # Use _shared module references (not local copies) so enterprise objects are live  # type: ignore[reportOptionalMemberAccess]
        if _shared._chief_of_staff:  # type: ignore[reportOptionalMemberAccess]
            await _phase("⚙️ [Act] running multi-agent execution via Chief of Staff")  # type: ignore[reportOptionalMemberAccess]
            from swarms_bot.orchestrator.chief_of_staff import (
                Task as STask,  # type: ignore[reportOptionalMemberAccess]
            )

            stask = STask.create(  # type: ignore[reportOptionalMemberAccess]
                user_id=msg.from_user.id,  # type: ignore[reportOptionalMemberAccess]
                chat_id=msg.chat.id,  # type: ignore[reportOptionalMemberAccess]
                description=augmented_task,  # type: ignore[reportOptionalMemberAccess]
            )
            responses = await _shared._chief_of_staff.route_multi(stask, agent_keys)  # type: ignore[reportOptionalMemberAccess]

            lines = ["<b>Multi-Execute Comparison</b>\n"]  # type: ignore[reportOptionalMemberAccess]
            for resp in responses:
                icon = "\u2705" if resp.success else "\u274c"  # type: ignore[reportOptionalMemberAccess]
                model = resp.metadata.get("model", "unknown")  # type: ignore[reportOptionalMemberAccess]
                lines.append(  # type: ignore[reportOptionalMemberAccess]
                    f"\n{icon} <b>{resp.agent_name}</b> ({model}, {resp.execution_time_ms}ms):\n"  # type: ignore[reportOptionalMemberAccess]
                    f"{resp.result[:1000] if resp.result else 'No result'}\n"  # type: ignore[reportOptionalMemberAccess]
                )
            full = "\n".join(lines)  # type: ignore[reportOptionalMemberAccess]

            if _shared._audit_logger:  # type: ignore[reportOptionalMemberAccess]
                await _shared._audit_logger.log(  # type: ignore[reportOptionalMemberAccess]
                    user_id=msg.from_user.id,  # type: ignore[reportOptionalMemberAccess]
                    agent_name="multi_execute",  # type: ignore[reportOptionalMemberAccess]
                    action_type="multi_execute",  # type: ignore[reportOptionalMemberAccess]
                    success=any(r.success for r in responses),  # type: ignore[reportOptionalMemberAccess]
                    metadata={"agents": agent_keys},  # type: ignore[reportOptionalMemberAccess]
                )
        else:
            await _phase("⚙️ [Act] running multi-agent execution in parallel")  # type: ignore[reportOptionalMemberAccess]
            results = await asyncio.gather(  # type: ignore[reportOptionalMemberAccess]
                *(chat(augmented_task, agent_key=a, user_id=user_id) for a in agent_keys),  # type: ignore[reportOptionalMemberAccess]
                return_exceptions=True,  # type: ignore[reportOptionalMemberAccess]
            )
            lines = ["<b>Multi-Execute Comparison</b>\n"]  # type: ignore[reportOptionalMemberAccess]
            for agent_key, res in zip(agent_keys, results, strict=False):  # type: ignore[reportOptionalMemberAccess]
                if isinstance(res, Exception):  # type: ignore[reportOptionalMemberAccess]
                    lines.append(f"\n\u274c <b>{agent_key}</b>: {html_mod.escape(str(res)[:200])}\n")  # type: ignore[reportOptionalMemberAccess]
                else:
                    text_r, model = res  # type: ignore[reportOptionalMemberAccess]
                    lines.append(f"\n\u2705 <b>{agent_key}</b> ({model}):\n{text_r[:1000]}\n")  # type: ignore[reportOptionalMemberAccess]
            full = "\n".join(lines)  # type: ignore[reportOptionalMemberAccess]

        await _phase("🧪 [Verify] synthesizing best answer and quality-checking")  # type: ignore[reportOptionalMemberAccess]
        synthesis_prompt = (  # type: ignore[reportOptionalMemberAccess]
            "You are the lead reviewer. Synthesize the multi-agent outputs below into ONE final answer.\n\n"  # type: ignore[reportOptionalMemberAccess]
            f"Original task:\n{task}\n\n"
            f"Agent outputs:\n{full}\n\n"
            "Return with this structure:\n"
            "1) Status\n2) Best Answer\n3) Key Evidence\n4) Confidence (0-100%)\n5) Next Actions"  # type: ignore[reportOptionalMemberAccess]
        )
        synthesized, _ = await chat(synthesis_prompt, agent_key="architect", user_id=user_id)  # type: ignore[reportOptionalMemberAccess]
        verified, meta = await verify_and_repair(task, synthesized, user_id=user_id)  # type: ignore[reportOptionalMemberAccess]

        verifier_block = (  # type: ignore[reportOptionalMemberAccess]
            "\n\n### Verifier\n"
            f"- Pass: {'YES' if meta.get('pass') else 'NO'}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Confidence: {int(float(meta.get('confidence', 0.0)) * 100)}%\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Repairs: {int(meta.get('repairs', 0))}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Notes: {meta.get('notes', 'n/a')}"  # type: ignore[reportOptionalMemberAccess]
        )
        evidence_text = evidence_bundle or full  # type: ignore[reportOptionalMemberAccess]
        grounded, gate = enforce_grounded_answer(task, verified, evidence_text, min_sources=3)  # type: ignore[reportOptionalMemberAccess]
        gate_block = (  # type: ignore[reportOptionalMemberAccess]
            "\n\n### Grounding Gate\n"
            f"- Blocked: {'YES' if gate.get('blocked') else 'NO'}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Sources: {int(gate.get('source_count', 0))}/{int(gate.get('min_sources', 3))}"  # type: ignore[reportOptionalMemberAccess]
        )
        consistency = analyze_answer_consistency(grounded)  # type: ignore[reportOptionalMemberAccess]
        consistency_block = (  # type: ignore[reportOptionalMemberAccess]
            "\n\n### Consistency\n"
            f"- Contradictions: {int(consistency.get('count', 0))}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Score: {int(float(consistency.get('score', 0.0)) * 100)}%"  # type: ignore[reportOptionalMemberAccess]
        )
        final_report = (  # type: ignore[reportOptionalMemberAccess]
            grounded
            + build_evidence_envelope(evidence_text, grounded)  # type: ignore[reportOptionalMemberAccess]
            + verifier_block
            + gate_block
            + consistency_block
            + "\n\n---\n\n"
            + full
        )

        record_capability_run(  # type: ignore[reportOptionalMemberAccess]
            "multi_execute",  # type: ignore[reportOptionalMemberAccess]
            task,  # type: ignore[reportOptionalMemberAccess]
            verifier_pass=bool(meta.get("pass")),  # type: ignore[reportOptionalMemberAccess]
            confidence=float(meta.get("confidence", 0.0)),  # type: ignore[reportOptionalMemberAccess]
            source_count=int(gate.get("source_count", 0)),  # type: ignore[reportOptionalMemberAccess]
            unique_domains=int(gate.get("unique_domains", 0)),  # type: ignore[reportOptionalMemberAccess]
            diversity_score=float(gate.get("diversity_score", 0.0)),  # type: ignore[reportOptionalMemberAccess]
            blocked=bool(gate.get("blocked")),  # type: ignore[reportOptionalMemberAccess]
            contradiction_count=int(consistency.get("count", 0)),  # type: ignore[reportOptionalMemberAccess]
            latency_ms=int((time.time() - started_at) * 1000),  # type: ignore[reportOptionalMemberAccess]
        )

        await _phase("✅ [Finalize] sending verified result")  # type: ignore[reportOptionalMemberAccess]
        await send_chunked(msg, final_report, model_used="multi_execute/verified")  # type: ignore[reportOptionalMemberAccess]
        with contextlib.suppress(Exception):  # type: ignore[reportOptionalMemberAccess]
            await status_msg.delete()  # type: ignore[reportOptionalMemberAccess]

    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"error: <code>{html_mod.escape(str(e)[:400])}</code>",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )
    finally:
        typing_task.cancel()  # type: ignore[reportOptionalMemberAccess]


# ── /multi_plan ───────────────────────────────────────────────────────────────
@router.message(Command("multi_plan"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_multi_plan(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    task = (msg.text or "").removeprefix("/multi_plan").strip()  # type: ignore[reportOptionalMemberAccess]
    if not task:
        await msg.answer("usage: <code>/multi_plan &lt;task&gt;</code>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return
    status_msg = await msg.answer("🧠 [Plan] generating 3 approaches…")  # type: ignore[reportOptionalMemberAccess]
    started_at = time.time()  # type: ignore[reportOptionalMemberAccess]

    async def _phase(text: str) -> None:  # type: ignore[reportOptionalMemberAccess]
        try:
            if text.startswith("💭"):  # type: ignore[reportOptionalMemberAccess]
                await msg.answer(f"<i>{html_mod.escape(text)}</i>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
            else:
                await status_msg.edit_text(html_mod.escape(text), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        except Exception:
            pass

    try:
        from llm_client import chat
        from tools.capability_metrics import (
            record_capability_run,  # type: ignore[reportOptionalMemberAccess]
        )
        from tools.quality_guard import (  # type: ignore[reportOptionalMemberAccess]
            analyze_answer_consistency,  # type: ignore[reportOptionalMemberAccess]
            build_evidence_envelope,  # type: ignore[reportOptionalMemberAccess]
            enforce_grounded_answer,  # type: ignore[reportOptionalMemberAccess]
            verify_and_repair,  # type: ignore[reportOptionalMemberAccess]
        )

        await _phase("⚙️ [Act] running 3 planning agents in parallel")  # type: ignore[reportOptionalMemberAccess]
        agent_keys = ["architect", "coding", "analyst"]  # type: ignore[reportOptionalMemberAccess]
        user_id = str(msg.from_user.id) if msg.from_user else "0"  # type: ignore[reportOptionalMemberAccess]
        results = await asyncio.gather(  # type: ignore[reportOptionalMemberAccess]
            *(chat(task, agent_key=a, user_id=user_id) for a in agent_keys),  # type: ignore[reportOptionalMemberAccess]
            return_exceptions=True,  # type: ignore[reportOptionalMemberAccess]
        )
        lines = ["<b>Multi-Plan Comparison</b>\n"]  # type: ignore[reportOptionalMemberAccess]
        for agent_key, res in zip(agent_keys, results, strict=False):  # type: ignore[reportOptionalMemberAccess]
            if isinstance(res, Exception):  # type: ignore[reportOptionalMemberAccess]
                lines.append(f"\n<b>\u26a0\ufe0f {agent_key}</b>: error — {html_mod.escape(str(res)[:200])}\n")  # type: ignore[reportOptionalMemberAccess]
            else:
                text_r, model = res  # type: ignore[reportOptionalMemberAccess]
                lines.append(f"\n<b>\U0001f4cb {agent_key}</b> ({model}):\n{text_r[:1000]}\n")  # type: ignore[reportOptionalMemberAccess]
        full = "\n".join(lines)  # type: ignore[reportOptionalMemberAccess]

        await _phase("🧪 [Verify] synthesizing and quality-checking plan")  # type: ignore[reportOptionalMemberAccess]
        synthesis_prompt = (  # type: ignore[reportOptionalMemberAccess]
            "Synthesize the 3 plan candidates below into a single final strategic plan.\n\n"  # type: ignore[reportOptionalMemberAccess]
            f"Task:\n{task}\n\n"
            f"Candidates:\n{full}\n\n"
            "Return with structure:\n"
            "1) Status\n2) Recommended Plan\n3) Evidence/Rationale\n4) Confidence\n5) Next Actions"
        )
        synthesized, _ = await chat(synthesis_prompt, agent_key="architect", user_id=user_id)  # type: ignore[reportOptionalMemberAccess]
        verified, meta = await verify_and_repair(task, synthesized, user_id=user_id)  # type: ignore[reportOptionalMemberAccess]
        verifier_block = (  # type: ignore[reportOptionalMemberAccess]
            "\n\n### Verifier\n"
            f"- Pass: {'YES' if meta.get('pass') else 'NO'}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Confidence: {int(float(meta.get('confidence', 0.0)) * 100)}%\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Repairs: {int(meta.get('repairs', 0))}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Notes: {meta.get('notes', 'n/a')}"  # type: ignore[reportOptionalMemberAccess]
        )
        grounded, gate = enforce_grounded_answer(task, verified, full, min_sources=2)  # type: ignore[reportOptionalMemberAccess]
        gate_block = (  # type: ignore[reportOptionalMemberAccess]
            "\n\n### Grounding Gate\n"
            f"- Blocked: {'YES' if gate.get('blocked') else 'NO'}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Sources: {int(gate.get('source_count', 0))}/{int(gate.get('min_sources', 2))}"  # type: ignore[reportOptionalMemberAccess]
        )
        consistency = analyze_answer_consistency(grounded)  # type: ignore[reportOptionalMemberAccess]
        consistency_block = (  # type: ignore[reportOptionalMemberAccess]
            "\n\n### Consistency\n"
            f"- Contradictions: {int(consistency.get('count', 0))}\n"  # type: ignore[reportOptionalMemberAccess]
            f"- Score: {int(float(consistency.get('score', 0.0)) * 100)}%"  # type: ignore[reportOptionalMemberAccess]
        )
        final_report = (  # type: ignore[reportOptionalMemberAccess]
            grounded
            + build_evidence_envelope(full, grounded)  # type: ignore[reportOptionalMemberAccess]
            + verifier_block
            + gate_block
            + consistency_block
            + "\n\n---\n\n"
            + full
        )

        record_capability_run(  # type: ignore[reportOptionalMemberAccess]
            "multi_plan",  # type: ignore[reportOptionalMemberAccess]
            task,  # type: ignore[reportOptionalMemberAccess]
            verifier_pass=bool(meta.get("pass")),  # type: ignore[reportOptionalMemberAccess]
            confidence=float(meta.get("confidence", 0.0)),  # type: ignore[reportOptionalMemberAccess]
            source_count=int(gate.get("source_count", 0)),  # type: ignore[reportOptionalMemberAccess]
            unique_domains=int(gate.get("unique_domains", 0)),  # type: ignore[reportOptionalMemberAccess]
            diversity_score=float(gate.get("diversity_score", 0.0)),  # type: ignore[reportOptionalMemberAccess]
            blocked=bool(gate.get("blocked")),  # type: ignore[reportOptionalMemberAccess]
            contradiction_count=int(consistency.get("count", 0)),  # type: ignore[reportOptionalMemberAccess]
            latency_ms=int((time.time() - started_at) * 1000),  # type: ignore[reportOptionalMemberAccess]
        )

        await _phase("✅ [Finalize] sending verified plan")  # type: ignore[reportOptionalMemberAccess]
        await send_chunked(msg, final_report, model_used="multi_plan/verified")  # type: ignore[reportOptionalMemberAccess]

        with contextlib.suppress(Exception):  # type: ignore[reportOptionalMemberAccess]
            await status_msg.delete()  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"error: <code>{html_mod.escape(str(e)[:400])}</code>",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )


# ── /loop — Autonomous plan-execute loop ─────────────────────────────────────
@router.message(Command("loop"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_loop(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Autonomous plan-execute loop with safety bounds."""  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    goal = (msg.text or "").removeprefix("/loop").strip()  # type: ignore[reportOptionalMemberAccess]
    if not goal:
        await msg.answer(  # type: ignore[reportOptionalMemberAccess]
            "<b>usage:</b> <code>/loop &lt;goal&gt;</code>\n\n"
            "Runs an autonomous plan\u2192execute loop until the goal is done.\n"  # type: ignore[reportOptionalMemberAccess]
            "Safety bounds: 25 iterations, $0.50 cost ceiling, 30min timeout.\n"  # type: ignore[reportOptionalMemberAccess]
            "Stop anytime with /loop_stop",  # type: ignore[reportOptionalMemberAccess]
            parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
        )
        return

    from tools.autonomous_loop import (  # type: ignore[reportOptionalMemberAccess]
        LoopConfig,
        get_active_loop,
        run_autonomous_loop,
    )

    if get_active_loop(msg.from_user.id):  # type: ignore[reportOptionalMemberAccess]
        await msg.answer(  # type: ignore[reportOptionalMemberAccess]
            "A loop is already running. Use /loop_stop to cancel it first.",  # type: ignore[reportOptionalMemberAccess]
        )
        return

    thread_id = _user_thread.get(msg.from_user.id)  # type: ignore[reportOptionalMemberAccess]

    # FIX #8: msg.bot can be None in aiogram 3.x — guard before use  # type: ignore[reportOptionalMemberAccess]
    _bot = msg.bot  # type: ignore[reportOptionalMemberAccess]
    if not _bot:
        await msg.answer("Internal error: bot context unavailable.")  # type: ignore[reportOptionalMemberAccess]
        return

    await msg.answer(  # type: ignore[reportOptionalMemberAccess]
        f"<b>\U0001f504 Loop started</b>\n"
        f"Goal: <code>{html_mod.escape(goal[:200])}</code>\n\n"  # type: ignore[reportOptionalMemberAccess]
        f"Bounds: 25 iters | $0.50 cost cap | 30min timeout\n"  # type: ignore[reportOptionalMemberAccess]
        f"Progress updates every 5 iterations.\n"  # type: ignore[reportOptionalMemberAccess]
        f"Stop anytime: /loop_stop",  # type: ignore[reportOptionalMemberAccess]
        parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
    )

    async def notify(text: str) -> None:  # type: ignore[reportOptionalMemberAccess]
        try:
            await _bot.send_message(msg.chat.id, text, parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        except Exception:
            try:
                await _bot.send_message(msg.chat.id, html_mod.escape(text), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
            except Exception:
                await _bot.send_message(msg.chat.id, text[:4000])  # type: ignore[reportOptionalMemberAccess]

    asyncio.create_task(  # type: ignore[reportOptionalMemberAccess]
        run_autonomous_loop(  # type: ignore[reportOptionalMemberAccess]
            user_id=msg.from_user.id,  # type: ignore[reportOptionalMemberAccess]
            goal=goal,  # type: ignore[reportOptionalMemberAccess]
            notify_cb=notify,  # type: ignore[reportOptionalMemberAccess]
            config=LoopConfig(),  # type: ignore[reportOptionalMemberAccess]
            thread_id=thread_id,  # type: ignore[reportOptionalMemberAccess]
        )
    )


@router.message(Command("loop_stop"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_loop_stop(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Kill switch for the autonomous loop."""  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    from tools.autonomous_loop import stop_loop  # type: ignore[reportOptionalMemberAccess]

    if stop_loop(msg.from_user.id):  # type: ignore[reportOptionalMemberAccess]
        await msg.answer("Loop stop signal sent. It will halt after the current step.")  # type: ignore[reportOptionalMemberAccess]
    else:
        await msg.answer("No active loop running.")  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("loop_status"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_loop_status(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Show status of the current autonomous loop."""  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    from tools.autonomous_loop import (  # type: ignore[reportOptionalMemberAccess]
        format_loop_status_html,
        get_loop_state,
    )

    state = get_loop_state(msg.from_user.id)  # type: ignore[reportOptionalMemberAccess]
    if not state:
        await msg.answer("No loop found. Start one with /loop")  # type: ignore[reportOptionalMemberAccess]
        return
    await msg.answer(format_loop_status_html(state), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("loop_pause"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_loop_pause(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Pause the running autonomous loop."""  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    from tools.autonomous_loop import pause_loop  # type: ignore[reportOptionalMemberAccess]

    if pause_loop(msg.from_user.id):  # type: ignore[reportOptionalMemberAccess]
        await msg.answer("\u23f8\ufe0f Loop paused. Resume with /loop_resume")  # type: ignore[reportOptionalMemberAccess]
    else:
        await msg.answer("No running loop to pause.")  # type: ignore[reportOptionalMemberAccess]


@router.message(Command("loop_resume"))  # type: ignore[reportOptionalMemberAccess]
async def cmd_loop_resume(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    """Resume a paused autonomous loop."""  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    from tools.autonomous_loop import resume_loop  # type: ignore[reportOptionalMemberAccess]

    if resume_loop(msg.from_user.id):  # type: ignore[reportOptionalMemberAccess]
        await msg.answer("\u25b6\ufe0f Loop resumed.")  # type: ignore[reportOptionalMemberAccess]
    else:
        await msg.answer("No paused loop to resume.")  # type: ignore[reportOptionalMemberAccess]


# ── Keyboard button shortcuts ─────────────────────────────────────────────────
@router.message(F.text.in_({"\U0001f41b Debug", "\U0001f4bb Code"}))  # type: ignore[reportOptionalMemberAccess]
async def kbd_agent_hint(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return
    key = "debug" if "Debug" in msg.text else "coding"  # type: ignore[reportOptionalMemberAccess]
    await msg.answer(  # type: ignore[reportOptionalMemberAccess]
        f"<b>{key}</b> mode — just type your task:",  # type: ignore[reportOptionalMemberAccess]
        parse_mode="HTML",  # type: ignore[reportOptionalMemberAccess]
    )


# ── Natural language catch-all (must be registered last) ─────────────────────
@router.message(F.text)  # type: ignore[reportOptionalMemberAccess]
async def handle_nl(msg: Message) -> None:  # type: ignore[reportOptionalMemberAccess]
    if not is_allowed(msg):  # type: ignore[reportOptionalMemberAccess]
        return

    # === NIHONGO MODE INTERCEPT — runs FIRST, completely isolated ===  # type: ignore[reportOptionalMemberAccess]
    try:
        from handlers.nihongo_handler import (  # type: ignore[reportOptionalMemberAccess]
            handle_nihongo_command,
            handle_nihongo_message,
        )
        from skills.nihongo.mode_manager import (
            NihongoModeManager,  # type: ignore[reportOptionalMemberAccess]
        )

        user_id = msg.from_user.id if msg.from_user else 0  # type: ignore[reportOptionalMemberAccess]

        if msg.text and msg.text.strip().lower().startswith("/nihonko"):  # type: ignore[reportOptionalMemberAccess]
            handled = await handle_nihongo_command(msg, None)  # type: ignore[reportOptionalMemberAccess]
            if handled:
                return

        if NihongoModeManager.is_active(user_id):  # type: ignore[reportOptionalMemberAccess]
            await handle_nihongo_message(msg, None)  # type: ignore[reportOptionalMemberAccess]
            return
    except Exception:
        pass
    # === END NIHONGO MODE INTERCEPT ===  # type: ignore[reportOptionalMemberAccess]

    task = (msg.text or "").strip()  # type: ignore[reportOptionalMemberAccess]
    if not task or task.startswith("/"):  # type: ignore[reportOptionalMemberAccess]
        return

    # Threads campaign mode intercept — routes free-text prompts to computer workflow.  # type: ignore[reportOptionalMemberAccess]
    try:
        from handlers.threads_mode import (  # type: ignore[reportOptionalMemberAccess]
            handle_threads_mode_prompt,
            is_threads_mode_enabled,
        )

        if await is_threads_mode_enabled():  # type: ignore[reportOptionalMemberAccess]
            handled = await handle_threads_mode_prompt(msg, task, _run_agent_loop)  # type: ignore[reportOptionalMemberAccess]
            if handled:
                return
    except Exception:
        pass

    # ── PRIMARY PATH: Autonomous router (guaranteed attempt, not optional) ───  # type: ignore[reportOptionalMemberAccess]
    # The autonomous router handles NL intelligently — it's the default, not a fallback.  # type: ignore[reportOptionalMemberAccess]
    # Only drop to keyword matching below if the router module itself can't be imported.  # type: ignore[reportOptionalMemberAccess]
    _router_handled = False  # type: ignore[reportOptionalMemberAccess]
    try:
        from handlers.message_handler import (
            handle_plain_message,  # type: ignore[reportOptionalMemberAccess]
        )
        from llm_client import (  # type: ignore[reportOptionalMemberAccess]
            auto_router,  # type: ignore[reportAttributeAccessIssue]
            init_humanization_layer,
        )

        # Ensure router is initialized — try once if not ready
        if auto_router is None:
            init_humanization_layer()  # type: ignore[reportOptionalMemberAccess]

        # Re-import after potential init
        from llm_client import auto_router as _ar  # type: ignore[reportAttributeAccessIssue]

        if _ar is not None:
            await handle_plain_message(msg, _ar)  # type: ignore[reportOptionalMemberAccess]
            _router_handled = True  # type: ignore[reportOptionalMemberAccess]
    except Exception as _router_err:
        import logging as _log

        _log.getLogger(__name__).warning(  # type: ignore[reportOptionalMemberAccess]
            "autonomous router failed for NL message — falling back to keyword dispatch: %s",  # type: ignore[reportOptionalMemberAccess]
            _router_err,  # type: ignore[reportOptionalMemberAccess]
        )

    if _router_handled:
        return

    # ── FALLBACK: Keyword-based dispatch (only if autonomous router failed) ───  # type: ignore[reportOptionalMemberAccess]
    # This should be rare — if it triggers, check autonomous_router init logs.  # type: ignore[reportOptionalMemberAccess]
    task_lower = task.lower()  # type: ignore[reportOptionalMemberAccess]

    # Check OpenClaw delegation first
    try:
        from tools.openclaw_bridge import (  # type: ignore[reportOptionalMemberAccess]
            delegate_to_openclaw,  # type: ignore[reportOptionalMemberAccess]
            is_openclaw_running,  # type: ignore[reportOptionalMemberAccess]
            should_delegate_to_openclaw,  # type: ignore[reportOptionalMemberAccess]
        )

        if should_delegate_to_openclaw(task) and await is_openclaw_running():  # type: ignore[reportOptionalMemberAccess]
            result = await delegate_to_openclaw(task)  # type: ignore[reportOptionalMemberAccess]
            await send_chunked(msg, result, model_used="openclaw")  # type: ignore[reportOptionalMemberAccess]
            return
    except Exception:
        pass

    # Detect questions (knowledge queries -> chat mode, no tools)  # type: ignore[reportOptionalMemberAccess]
    question_starters = [  # type: ignore[reportOptionalMemberAccess]
        "apa ",  # type: ignore[reportOptionalMemberAccess]
        "berapa",  # type: ignore[reportOptionalMemberAccess]
        "bagaimana",  # type: ignore[reportOptionalMemberAccess]
        "kenapa",  # type: ignore[reportOptionalMemberAccess]
        "mengapa",  # type: ignore[reportOptionalMemberAccess]
        "siapa",  # type: ignore[reportOptionalMemberAccess]
        "dimana",  # type: ignore[reportOptionalMemberAccess]
        "kapan",  # type: ignore[reportOptionalMemberAccess]
        "gimana",  # type: ignore[reportOptionalMemberAccess]
        "apakah",  # type: ignore[reportOptionalMemberAccess]
        "bisakah",  # type: ignore[reportOptionalMemberAccess]
        "what ",  # type: ignore[reportOptionalMemberAccess]
        "how ",  # type: ignore[reportOptionalMemberAccess]
        "why ",  # type: ignore[reportOptionalMemberAccess]
        "when ",  # type: ignore[reportOptionalMemberAccess]
        "where ",  # type: ignore[reportOptionalMemberAccess]
        "which ",  # type: ignore[reportOptionalMemberAccess]
        "who ",  # type: ignore[reportOptionalMemberAccess]
        "is it",  # type: ignore[reportOptionalMemberAccess]
        "are there",  # type: ignore[reportOptionalMemberAccess]
        "does ",  # type: ignore[reportOptionalMemberAccess]
        "do you",  # type: ignore[reportOptionalMemberAccess]
        "can you",  # type: ignore[reportOptionalMemberAccess]
        "could you",  # type: ignore[reportOptionalMemberAccess]
        "would you",  # type: ignore[reportOptionalMemberAccess]
        "should ",  # type: ignore[reportOptionalMemberAccess]
        "ada berapa",  # type: ignore[reportOptionalMemberAccess]
        "apa saja",  # type: ignore[reportOptionalMemberAccess]
        "apa itu",  # type: ignore[reportOptionalMemberAccess]
        "ada apa",  # type: ignore[reportOptionalMemberAccess]
    ]
    is_question = task_lower.rstrip().endswith("?") or any(task_lower.startswith(q) for q in question_starters)  # type: ignore[reportOptionalMemberAccess]

    strong_computer = [  # type: ignore[reportOptionalMemberAccess]
        "screenshot",  # type: ignore[reportOptionalMemberAccess]
        "take screenshot",  # type: ignore[reportOptionalMemberAccess]
        "click on",  # type: ignore[reportOptionalMemberAccess]
        "click at",  # type: ignore[reportOptionalMemberAccess]
        "klik pada",  # type: ignore[reportOptionalMemberAccess]
        "drag",  # type: ignore[reportOptionalMemberAccess]
        "scroll down",  # type: ignore[reportOptionalMemberAccess]
        "scroll up",  # type: ignore[reportOptionalMemberAccess]
        "open whatsapp",  # type: ignore[reportOptionalMemberAccess]
        "buka whatsapp",  # type: ignore[reportOptionalMemberAccess]
        "open chrome",  # type: ignore[reportOptionalMemberAccess]
        "buka chrome",  # type: ignore[reportOptionalMemberAccess]
        "open browser",  # type: ignore[reportOptionalMemberAccess]
        "buka browser",  # type: ignore[reportOptionalMemberAccess]
        "open firefox",  # type: ignore[reportOptionalMemberAccess]
        "buka firefox",  # type: ignore[reportOptionalMemberAccess]
        "open vscode",  # type: ignore[reportOptionalMemberAccess]
        "buka vscode",  # type: ignore[reportOptionalMemberAccess]
        "open terminal",  # type: ignore[reportOptionalMemberAccess]
        "buka terminal",  # type: ignore[reportOptionalMemberAccess]
        "open supabase",  # type: ignore[reportOptionalMemberAccess]
        "open gmail",  # type: ignore[reportOptionalMemberAccess]
        "open spotify",  # type: ignore[reportOptionalMemberAccess]
        "open telegram",  # type: ignore[reportOptionalMemberAccess]
        "launch ",  # type: ignore[reportOptionalMemberAccess]
        "jalankan ",  # type: ignore[reportOptionalMemberAccess]
        "search for",  # type: ignore[reportOptionalMemberAccess]
        "search the web",  # type: ignore[reportOptionalMemberAccess]
        "cari di internet",  # type: ignore[reportOptionalMemberAccess]
        "browse to",  # type: ignore[reportOptionalMemberAccess]
        "go to website",  # type: ignore[reportOptionalMemberAccess]
        "scrape",  # type: ignore[reportOptionalMemberAccess]
        "read pdf",  # type: ignore[reportOptionalMemberAccess]
        "read excel",  # type: ignore[reportOptionalMemberAccess]
        "extract table",  # type: ignore[reportOptionalMemberAccess]
        "organize files",  # type: ignore[reportOptionalMemberAccess]
        "baca dokumen",  # type: ignore[reportOptionalMemberAccess]
        "git commit",  # type: ignore[reportOptionalMemberAccess]
        "git push",  # type: ignore[reportOptionalMemberAccess]
        "git pull",  # type: ignore[reportOptionalMemberAccess]
        "run tests",  # type: ignore[reportOptionalMemberAccess]
        "pytest",  # type: ignore[reportOptionalMemberAccess]
        "format code",  # type: ignore[reportOptionalMemberAccess]
        "disk space",  # type: ignore[reportOptionalMemberAccess]
        "check services",  # type: ignore[reportOptionalMemberAccess]
        "system cleanup",  # type: ignore[reportOptionalMemberAccess]
    ]

    soft_computer = [  # type: ignore[reportOptionalMemberAccess]
        "open",  # type: ignore[reportOptionalMemberAccess]
        "buka",  # type: ignore[reportOptionalMemberAccess]
        "show me",  # type: ignore[reportOptionalMemberAccess]
        "check on",  # type: ignore[reportOptionalMemberAccess]
        "cek langsung",  # type: ignore[reportOptionalMemberAccess]
        "tolong cek",  # type: ignore[reportOptionalMemberAccess]
        "lihat di",  # type: ignore[reportOptionalMemberAccess]
        "tampilkan",  # type: ignore[reportOptionalMemberAccess]
        "periksa",  # type: ignore[reportOptionalMemberAccess]
        "cari online",  # type: ignore[reportOptionalMemberAccess]
        "monitor",  # type: ignore[reportOptionalMemberAccess]
        "research",  # type: ignore[reportOptionalMemberAccess]
        "klik",  # type: ignore[reportOptionalMemberAccess]
        "ketik",  # type: ignore[reportOptionalMemberAccess]
    ]

    has_strong = any(kw in task_lower for kw in strong_computer)  # type: ignore[reportOptionalMemberAccess]
    has_soft = any(kw in task_lower for kw in soft_computer)  # type: ignore[reportOptionalMemberAccess]

    if has_strong:
        await _run_agent_loop(msg, task)  # type: ignore[reportOptionalMemberAccess]
    elif is_question:
        await _execute_chat(msg, task)  # type: ignore[reportOptionalMemberAccess]
    elif has_soft:
        await _run_agent_loop(msg, task)  # type: ignore[reportOptionalMemberAccess]
    else:
        await _execute_chat(msg, task)  # type: ignore[reportOptionalMemberAccess]
