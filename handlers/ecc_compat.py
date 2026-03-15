"""ECC compatibility handlers: best-of Everything-Claude-Code workflows for Legion.

Commands added (Telegram-safe underscore style):
  /harness_audit
  /model_route <task>
  /quality_gate <task>
  /verify <task>
  /plan <task>
  /checkpoint [name]
  /save_session [name]
  /resume_session <name_or_id>
  /instinct_status
  /instinct_export
  /instinct_import <json>
  /loop_start <goal>
"""

from __future__ import annotations

import asyncio
import html as html_mod
import json
import time
import uuid
from pathlib import Path
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import router as agents
import handlers.shared as _shared
from handlers.shared import _key_status, _user_thread, is_allowed, send_chunked
from llm_client import chat

router = Router()


def _extract_arg(text: str, cmd: str) -> str:
    return (text or "").removeprefix(f"/{cmd}").strip()


@router.message(Command("harness_audit"))
async def cmd_harness_audit(msg: Message) -> None:
    """Audit harness readiness: routing, fallbacks, keys, enterprise services."""
    if not is_allowed(msg):
        return

    models = agents.AGENT_MODELS
    chains = agents.FALLBACK_CHAIN
    missing_fallback = [k for k in models if not chains.get(k)]

    lines = [
        "<b>🧪 Harness Audit</b>",
        "",
        f"Agents configured: <b>{len(models)}</b>",
        f"Fallback chains: <b>{len(chains)}</b>",
        f"Missing fallback chains: <b>{len(missing_fallback)}</b>",
    ]

    if missing_fallback:
        joined = ", ".join(f"<code>{html_mod.escape(x)}</code>" for x in missing_fallback[:8])
        lines.append(f"Missing: {joined}")

    lines.extend(
        [
            "",
            "<b>Enterprise Layer</b>",
            f"Chief of Staff: {'✅' if _shared._chief_of_staff else '❌'}",
            f"Budget manager: {'✅' if _shared._budget_manager else '❌'}",
            f"Security guard: {'✅' if _shared._security_guard else '❌'}",
            f"Audit logger: {'✅' if _shared._audit_logger else '❌'}",
            f"Evaluator: {'✅' if _shared._evaluator else '❌'}",
            f"Session manager: {'✅' if _shared._session_manager else '❌'}",
            "",
            _key_status(),
            "",
            "<i>ECC parity implemented with Legion-native components and cloud-first routing.</i>",
        ]
    )
    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("model_route"))
async def cmd_model_route(msg: Message) -> None:
    """Show selected agent/model/fallback chain for a task."""
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "model_route")
    if not task:
        await msg.answer("usage: <code>/model_route &lt;task&gt;</code>", parse_mode="HTML")
        return

    agent_key = agents.detect_agent(task)
    primary = agents.get_model(agent_key) or "unknown"
    fallback = agents.get_fallback_chain(agent_key)

    lower_task = task.lower()
    matched = [kw for kw in agents.TASK_KEYWORDS.get(agent_key, []) if kw.lower() in lower_task][:8]

    lines = [
        "<b>🧭 Model Route</b>",
        f"Task: <i>{html_mod.escape(task[:180])}</i>",
        f"Agent: <code>{html_mod.escape(agent_key)}</code>",
        f"Primary: <code>{html_mod.escape(primary)}</code>",
        "",
        "<b>Fallback Chain</b>",
    ]
    lines.extend([f"{idx}. <code>{html_mod.escape(m)}</code>" for idx, m in enumerate(fallback, start=1)])
    if matched:
        lines.extend(["", "<b>Matched Keywords</b>", ", ".join(f"<code>{html_mod.escape(k)}</code>" for k in matched)])

    await msg.answer("\n".join(lines), parse_mode="HTML")


async def _run_quality_gate(msg: Message, task: str) -> None:
    """Generate + verify + ground an answer for the given task."""
    status_msg = await msg.answer("🧪 running quality gate…")
    try:
        from tools.quality_guard import (
            analyze_answer_consistency,
            build_evidence_envelope,
            enforce_grounded_answer,
            verify_and_repair,
        )

        agent_key = agents.detect_agent(task)
        user_id = str(msg.from_user.id) if msg.from_user else "0"
        draft, model_used = await chat(task, agent_key=agent_key, user_id=user_id)
        verified, meta = await verify_and_repair(task, draft, user_id=user_id)
        grounded, gate = enforce_grounded_answer(task, verified, draft, min_sources=2)
        consistency = analyze_answer_consistency(grounded)

        verifier_block = (
            "\n\n### Verifier\n"
            f"- Pass: {'YES' if meta.get('pass') else 'NO'}\n"
            f"- Confidence: {int(float(meta.get('confidence', 0.0)) * 100)}%\n"
            f"- Repairs: {int(meta.get('repairs', 0))}\n"
            f"- Notes: {meta.get('notes', 'n/a')}"
        )
        gate_block = (
            "\n\n### Grounding Gate\n"
            f"- Blocked: {'YES' if gate.get('blocked') else 'NO'}\n"
            f"- Sources: {int(gate.get('source_count', 0))}/{int(gate.get('min_sources', 2))}"
        )
        consistency_block = (
            "\n\n### Consistency\n"
            f"- Contradictions: {int(consistency.get('count', 0))}\n"
            f"- Score: {int(float(consistency.get('score', 0.0)) * 100)}%"
        )

        final = grounded + build_evidence_envelope(draft, grounded) + verifier_block + gate_block + consistency_block

        try:
            await status_msg.delete()
        except Exception:
            pass
        await send_chunked(msg, final, model_used=f"quality_gate/{model_used}")
    except Exception as e:
        await status_msg.edit_text(
            f"quality gate error: <code>{html_mod.escape(str(e)[:380])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("quality_gate"))
async def cmd_quality_gate(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "quality_gate")
    if not task:
        await msg.answer("usage: <code>/quality_gate &lt;task&gt;</code>", parse_mode="HTML")
        return
    await _run_quality_gate(msg, task)


@router.message(Command("verify"))
async def cmd_verify(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "verify")
    if not task:
        await msg.answer("usage: <code>/verify &lt;task&gt;</code>", parse_mode="HTML")
        return
    await _run_quality_gate(msg, task)


@router.message(Command("plan"))
async def cmd_plan(msg: Message) -> None:
    """ECC-style /plan command routed to architect planning pass."""
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "plan")
    if not task:
        await msg.answer("usage: <code>/plan &lt;goal&gt;</code>", parse_mode="HTML")
        return

    prompt = (
        "Create an execution plan with this structure:\n"
        "1) Objective\n2) Scope\n3) Phased Plan\n4) Risks\n5) Verification Checklist\n\n"
        f"Goal:\n{task}"
    )
    answer, model_used = await chat(prompt, agent_key="architect", user_id=str(msg.from_user.id))
    await send_chunked(msg, answer, model_used=f"plan/{model_used}")


async def _save_checkpoint(msg: Message, requested_name: str | None = None) -> None:
    from tools.persistence import save_session

    if not msg.from_user:
        return

    thread_id = _user_thread.get(msg.from_user.id, f"thread_{msg.from_user.id}")
    context = agents.get_thread_context(thread_id, max_turns=20)
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = requested_name or f"checkpoint-{ts}"
    session_id = f"sess_{uuid.uuid4().hex[:10]}"

    await save_session(
        session_id=session_id,
        name=name,
        thread_id=thread_id,
        agent_key="general",
        context_json=json.dumps(context, ensure_ascii=False),
    )
    await msg.answer(
        f"✅ Saved checkpoint <b>{html_mod.escape(name)}</b>\n"
        f"ID: <code>{session_id}</code>\n"
        f"Resume: <code>/resume_session {html_mod.escape(name)}</code>",
        parse_mode="HTML",
    )


@router.message(Command("checkpoint"))
async def cmd_checkpoint(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = _extract_arg(msg.text or "", "checkpoint")
    await _save_checkpoint(msg, requested_name=name or None)


@router.message(Command("save_session"))
async def cmd_save_session_alias(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = _extract_arg(msg.text or "", "save_session")
    await _save_checkpoint(msg, requested_name=name or None)


@router.message(Command("resume_session"))
async def cmd_resume_session_alias(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name_or_id = _extract_arg(msg.text or "", "resume_session")
    if not name_or_id:
        await msg.answer("usage: <code>/resume_session &lt;name_or_id&gt;</code>", parse_mode="HTML")
        return

    from tools.persistence import resume_session

    session = await resume_session(name_or_id)
    if not session:
        await msg.answer("Session not found.")
        return

    if msg.from_user:
        _user_thread[msg.from_user.id] = str(session.get("thread_id") or f"thread_{msg.from_user.id}")

    await msg.answer(
        f"✅ Resumed <b>{html_mod.escape(str(session.get('name', name_or_id)))}</b>\n"
        f"Thread: <code>{html_mod.escape(str(session.get('thread_id', 'n/a')))}</code>",
        parse_mode="HTML",
    )


@router.message(Command("instinct_status"))
async def cmd_instinct_status(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from tools.persistence import get_instincts

    instincts = await get_instincts(limit=500)
    if not instincts:
        await msg.answer("No instincts yet. Use <code>/learn ...</code>", parse_mode="HTML")
        return

    by_category: dict[str, int] = {}
    for item in instincts:
        cat = str(item.get("category") or "general")
        by_category[cat] = by_category.get(cat, 0) + 1

    lines = ["<b>🧠 Instinct Status</b>", f"Total instincts: <b>{len(instincts)}</b>", "", "<b>By category</b>"]
    for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"• <code>{html_mod.escape(category)}</code>: {count}")
    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("instinct_export"))
async def cmd_instinct_export(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from tools.persistence import get_instincts

    instincts = await get_instincts(limit=500)
    payload = [
        {
            "category": i.get("category", "general"),
            "content": i.get("content", ""),
            "source": i.get("source", "manual"),
            "weight": i.get("weight", 1.0),
        }
        for i in instincts
    ]
    raw = json.dumps(payload, ensure_ascii=False, indent=2)
    await send_chunked(msg, f"<b>Instinct Export</b>\n\n<pre>{html_mod.escape(raw)}</pre>", model_used="instinct/export")


@router.message(Command("instinct_import"))
async def cmd_instinct_import(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = _extract_arg(msg.text or "", "instinct_import")
    if not arg and msg.reply_to_message and msg.reply_to_message.text:
        arg = msg.reply_to_message.text.strip()
    if not arg:
        await msg.answer(
            "usage: <code>/instinct_import &lt;json_array&gt;</code>\n"
            "or reply to a JSON payload with <code>/instinct_import</code>",
            parse_mode="HTML",
        )
        return

    from tools.persistence import add_instinct

    try:
        parsed: Any = json.loads(arg)
    except json.JSONDecodeError as e:
        await msg.answer(f"invalid JSON: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")
        return

    items = parsed if isinstance(parsed, list) else [parsed]
    imported = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        category = str(item.get("category") or "general").strip()
        source = str(item.get("source") or "import").strip()
        await add_instinct(category=category, content=content, source=source)
        imported += 1

    await msg.answer(f"✅ Imported <b>{imported}</b> instincts.", parse_mode="HTML")


@router.message(Command("loop_start"))
async def cmd_loop_start(msg: Message) -> None:
    """ECC-style alias for /loop."""
    if not is_allowed(msg):
        return
    goal = _extract_arg(msg.text or "", "loop_start")
    if not goal:
        await msg.answer("usage: <code>/loop_start &lt;goal&gt;</code>", parse_mode="HTML")
        return

    from tools.autonomous_loop import LoopConfig, get_active_loop, run_autonomous_loop

    if not msg.from_user:
        return

    if get_active_loop(msg.from_user.id):
        await msg.answer("A loop is already running. Use /loop_stop first.")
        return

    thread_id = _user_thread.get(msg.from_user.id)
    _bot = msg.bot
    if not _bot:
        await msg.answer("Internal error: bot context unavailable.")
        return

    await msg.answer(
        f"<b>🔁 Loop started</b>\n"
        f"Goal: <code>{html_mod.escape(goal[:200])}</code>\n"
        f"Stop anytime: <code>/loop_stop</code>",
        parse_mode="HTML",
    )

    async def notify(text: str) -> None:
        try:
            await _bot.send_message(msg.chat.id, text, parse_mode="HTML")
        except Exception:
            await _bot.send_message(msg.chat.id, html_mod.escape(text), parse_mode="HTML")

    asyncio_task = run_autonomous_loop(
        user_id=msg.from_user.id,
        goal=goal,
        notify_cb=notify,
        config=LoopConfig(),
        thread_id=thread_id,
    )
    asyncio.create_task(asyncio_task)


@router.message(Command("code_review"))
async def cmd_code_review(msg: Message) -> None:
    """ECC alias for /review with file/code auto-detection."""
    if not is_allowed(msg):
        return
    arg = _extract_arg(msg.text or "", "code_review")
    if not arg and msg.reply_to_message and msg.reply_to_message.text:
        arg = msg.reply_to_message.text.strip()
    if not arg:
        await msg.answer("usage: <code>/code_review &lt;file_or_code&gt;</code>", parse_mode="HTML")
        return

    status = await msg.answer("🔍 running code review…")
    try:
        from tools.code_reviewer import review_code, review_file

        path = Path(arg)
        if path.exists() and path.is_file():
            result = await review_file(str(path), review_type="general")
        else:
            result = await review_code(arg, language="python", review_type="general")
        await status.delete()
        await send_chunked(msg, result, model_used="ecc/code_review")
    except Exception as e:
        await status.edit_text(f"review error: <code>{html_mod.escape(str(e)[:350])}</code>", parse_mode="HTML")


@router.message(Command("python_review"))
async def cmd_python_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = _extract_arg(msg.text or "", "python_review")
    if not arg and msg.reply_to_message and msg.reply_to_message.text:
        arg = msg.reply_to_message.text.strip()
    if not arg:
        await msg.answer("usage: <code>/python_review &lt;file_or_code&gt;</code>", parse_mode="HTML")
        return

    status = await msg.answer("🐍 running python review…")
    try:
        from tools.code_reviewer import review_code, review_file

        path = Path(arg)
        if path.exists() and path.is_file():
            result = await review_file(str(path), review_type="python")
        else:
            result = await review_code(arg, language="python", review_type="python")
        await status.delete()
        await send_chunked(msg, result, model_used="ecc/python_review")
    except Exception as e:
        await status.edit_text(f"python review error: <code>{html_mod.escape(str(e)[:350])}</code>", parse_mode="HTML")


@router.message(Command("refactor_clean"))
async def cmd_refactor_clean(msg: Message) -> None:
    """Format + review a file for cleanup recommendations."""
    if not is_allowed(msg):
        return
    arg = _extract_arg(msg.text or "", "refactor_clean")
    if not arg:
        await msg.answer("usage: <code>/refactor_clean &lt;file_path&gt;</code>", parse_mode="HTML")
        return

    target = Path(arg).expanduser()
    if not target.exists() or not target.is_file():
        await msg.answer(f"file not found: <code>{html_mod.escape(str(target))}</code>", parse_mode="HTML")
        return

    status = await msg.answer("🧹 running formatter + cleanup review…")
    try:
        from tools.code_reviewer import review_file
        from tools.dev_tools import format_code

        fmt = await format_code(str(target), tool="ruff")
        review = await review_file(str(target), review_type="python")
        out = (
            f"<b>Refactor/Clean Result</b>\n"
            f"Target: <code>{html_mod.escape(str(target))}</code>\n\n"
            f"<b>Formatter Output</b>\n<pre>{html_mod.escape(fmt[:1500])}</pre>\n\n"
            f"{review}"
        )
        await status.delete()
        await send_chunked(msg, out, model_used="ecc/refactor_clean")
    except Exception as e:
        await status.edit_text(f"refactor error: <code>{html_mod.escape(str(e)[:350])}</code>", parse_mode="HTML")


@router.message(Command("test_coverage"))
async def cmd_test_coverage(msg: Message) -> None:
    """Run pytest coverage report, fallback to regular pytest if cov plugin missing."""
    if not is_allowed(msg):
        return
    path = _extract_arg(msg.text or "", "test_coverage") or "."
    status = await msg.answer("🧪 running test coverage…")
    try:
        from tools.dev_tools import run_tests

        output = await run_tests(path=path, framework="pytest", args="--maxfail=1 --cov=. --cov-report=term-missing")
        if "unrecognized arguments: --cov" in output.lower() or "no module named pytest_cov" in output.lower():
            fallback = await run_tests(path=path, framework="pytest", args="--maxfail=1")
            output = (
                "[coverage plugin missing: install with pip install pytest-cov]\n\n"
                + fallback
            )
        await status.delete()
        await send_chunked(msg, f"<pre>{html_mod.escape(output)}</pre>", model_used="ecc/test_coverage")
    except Exception as e:
        await status.edit_text(f"test error: <code>{html_mod.escape(str(e)[:350])}</code>", parse_mode="HTML")


@router.message(Command("tdd"))
async def cmd_tdd(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "tdd")
    if not task:
        await msg.answer("usage: <code>/tdd &lt;feature_or_bug&gt;</code>", parse_mode="HTML")
        return

    prompt = (
        "Create a strict TDD plan for this request. Output sections:\n"
        "1) RED tests to write first\n"
        "2) GREEN minimal implementation\n"
        "3) REFACTOR steps\n"
        "4) Edge cases\n"
        "5) Verification commands\n\n"
        f"Request:\n{task}"
    )
    result, model = await chat(prompt, agent_key="reviewer", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/tdd/{model}")


@router.message(Command("prompt_optimize"))
async def cmd_prompt_optimize(msg: Message) -> None:
    if not is_allowed(msg):
        return
    raw = _extract_arg(msg.text or "", "prompt_optimize")
    if not raw:
        await msg.answer("usage: <code>/prompt_optimize &lt;prompt_text&gt;</code>", parse_mode="HTML")
        return

    prompt = (
        "Rewrite this prompt for stronger reliability and lower token usage. Return:\n"
        "- Optimized Prompt\n- Why it is better\n- Optional strict JSON output schema\n\n"
        f"Original:\n{raw}"
    )
    result, model = await chat(prompt, agent_key="architect", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/prompt_optimize/{model}")


@router.message(Command("learn_eval"))
async def cmd_learn_eval(msg: Message) -> None:
    """Evaluate instinct quality and coverage gaps."""
    if not is_allowed(msg):
        return
    from tools.persistence import get_instincts

    instincts = await get_instincts(limit=120)
    if not instincts:
        await msg.answer("No instincts yet. Add some via <code>/learn ...</code>", parse_mode="HTML")
        return

    serialized = "\n".join(
        f"- [{i.get('category','general')}] {str(i.get('content',''))[:220]}"
        for i in instincts
    )
    prompt = (
        "Evaluate these learned instincts for quality. Return:\n"
        "1) Strong instincts\n2) Redundant/noisy instincts\n3) Missing categories\n4) Top 10 keep-list\n\n"
        f"Instincts:\n{serialized}"
    )
    result, model = await chat(prompt, agent_key="analyst", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/learn_eval/{model}")


@router.message(Command("update_docs"))
async def cmd_update_docs(msg: Message) -> None:
    """Generate a docs update draft and save it under docs/ecc_updates/."""
    if not is_allowed(msg):
        return
    topic = _extract_arg(msg.text or "", "update_docs")
    if not topic:
        await msg.answer("usage: <code>/update_docs &lt;topic_or_change&gt;</code>", parse_mode="HTML")
        return

    prompt = (
        "Write a concise project documentation update in markdown with:\n"
        "- Summary\n- Changes\n- Impact\n- Verification\n- Rollback notes\n\n"
        f"Topic:\n{topic}"
    )
    result, model = await chat(prompt, agent_key="pm", user_id=str(msg.from_user.id))

    updates_dir = Path("/home/newadmin/swarm-bot/docs/ecc_updates")
    updates_dir.mkdir(parents=True, exist_ok=True)
    filename = f"update_{time.strftime('%Y%m%d_%H%M%S')}.md"
    out_path = updates_dir / filename
    out_path.write_text(result, encoding="utf-8")

    await msg.answer(
        f"✅ Docs draft generated by <code>{html_mod.escape(model)}</code>\n"
        f"Saved: <code>{html_mod.escape(str(out_path))}</code>",
        parse_mode="HTML",
    )


@router.message(Command("update_codemaps"))
async def cmd_update_codemaps(msg: Message) -> None:
    """Generate a lightweight codemap markdown from current workspace layout."""
    if not is_allowed(msg):
        return

    root = Path("/home/newadmin/swarm-bot")
    include_dirs = ["handlers", "tools", "swarms_bot", "core", "agents", "config"]
    lines = ["# Auto Codemap", "", "Generated by /update_codemaps", "", "## Topology"]
    for name in include_dirs:
        p = root / name
        if not p.exists():
            continue
        lines.append(f"- {name}/")
        try:
            children = sorted(p.iterdir(), key=lambda x: x.name)[:20]
            for c in children:
                suffix = "/" if c.is_dir() else ""
                lines.append(f"  - {c.name}{suffix}")
        except Exception:
            continue

    out_path = root / "docs" / "CODEMAP_AUTO.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    await msg.answer(f"✅ Codemap updated: <code>{html_mod.escape(str(out_path))}</code>", parse_mode="HTML")


@router.message(Command("skill_create"))
async def cmd_skill_create(msg: Message) -> None:
    """Create a new skill markdown file from name + brief description."""
    if not is_allowed(msg):
        return
    raw = _extract_arg(msg.text or "", "skill_create")
    if not raw:
        await msg.answer(
            "usage: <code>/skill_create &lt;name&gt; &lt;description&gt;</code>\n"
            "example: <code>/skill_create postgres-indexing optimize slow SQL queries</code>",
            parse_mode="HTML",
        )
        return

    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("please provide both skill name and description", parse_mode="HTML")
        return
    name, desc = parts[0].strip().lower(), parts[1].strip()
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in name).strip("-")
    if not safe_name:
        await msg.answer("invalid skill name", parse_mode="HTML")
        return

    prompt = (
        "Create a practical markdown skill file with sections:\n"
        "- Purpose\n- When to Use\n- Do\n- Don't\n- Step-by-step Workflow\n- Quality Checklist\n"
        f"Skill name: {safe_name}\n"
        f"Description: {desc}"
    )
    content, model = await chat(prompt, agent_key="architect", user_id=str(msg.from_user.id))

    skill_path = Path("/home/newadmin/swarm-bot/skills") / f"{safe_name}.md"
    if skill_path.exists():
        await msg.answer(f"skill already exists: <code>{html_mod.escape(str(skill_path))}</code>", parse_mode="HTML")
        return
    skill_path.write_text(content.strip() + "\n", encoding="utf-8")
    await msg.answer(
        f"✅ Skill created via <code>{html_mod.escape(model)}</code>\n"
        f"Path: <code>{html_mod.escape(str(skill_path))}</code>\n"
        f"Reload with <code>/skill_reload</code>",
        parse_mode="HTML",
    )


@router.message(Command("eval"))
async def cmd_eval_alias(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "eval")
    if not task:
        await msg.answer("usage: <code>/eval &lt;task_or_answer_to_evaluate&gt;</code>", parse_mode="HTML")
        return
    await _run_quality_gate(msg, task)


@router.message(Command("build_fix"))
async def cmd_build_fix(msg: Message) -> None:
    if not is_allowed(msg):
        return
    error_text = _extract_arg(msg.text or "", "build_fix")
    if not error_text and msg.reply_to_message and msg.reply_to_message.text:
        error_text = msg.reply_to_message.text.strip()
    if not error_text:
        await msg.answer("usage: <code>/build_fix &lt;build_error_log&gt;</code>", parse_mode="HTML")
        return

    prompt = (
        "Analyze this build/test failure and return:\n"
        "1) Root cause\n2) Minimal fix\n3) Command-by-command verification\n4) Rollback if fix fails\n\n"
        f"Error log:\n{error_text}"
    )
    result, model = await chat(prompt, agent_key="debug", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/build_fix/{model}")


@router.message(Command("projects"))
async def cmd_projects(msg: Message) -> None:
    """List top-level projects/workspace folders quickly."""
    if not is_allowed(msg):
        return
    root = Path("/home/newadmin/swarm-bot")
    folders = [p.name for p in sorted(root.iterdir(), key=lambda x: x.name) if p.is_dir() and not p.name.startswith(".")]
    files = [p.name for p in sorted(root.iterdir(), key=lambda x: x.name) if p.is_file() and p.suffix in {".py", ".md", ".yml", ".yaml", ".toml"}]
    lines = ["<b>📁 Workspace Projects</b>", "", "<b>Folders</b>"]
    lines.extend(f"• <code>{html_mod.escape(name)}</code>" for name in folders[:40])
    lines.extend(["", "<b>Key files</b>"])
    lines.extend(f"• <code>{html_mod.escape(name)}</code>" for name in files[:20])
    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("setup_pm"))
async def cmd_setup_pm(msg: Message) -> None:
    """ECC package-manager setup analogue for this Python-first repo."""
    if not is_allowed(msg):
        return
    root = Path("/home/newadmin/swarm-bot")
    has_pyproject = (root / "pyproject.toml").exists()
    has_requirements = (root / "requirements.txt").exists()
    has_venv = (root / ".venv").exists()

    lines = [
        "<b>🧰 Package Manager Setup</b>",
        f"pyproject.toml: {'✅' if has_pyproject else '❌'}",
        f"requirements.txt: {'✅' if has_requirements else '❌'}",
        f".venv: {'✅' if has_venv else '❌'}",
        "",
        "Recommended workflow:",
        "1) <code>source .venv/bin/activate</code>",
        "2) <code>python -m pip install -r requirements.txt</code>",
        "3) <code>python -m pytest -q</code>",
    ]
    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("claw"))
async def cmd_claw(msg: Message) -> None:
    """Direct bridge command to OpenClaw if available."""
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "claw")
    if not task:
        await msg.answer("usage: <code>/claw &lt;task&gt;</code>", parse_mode="HTML")
        return

    try:
        from tools.openclaw_bridge import delegate_to_openclaw, is_openclaw_running

        if not await is_openclaw_running():
            await msg.answer("OpenClaw is not reachable right now.")
            return
        result = await delegate_to_openclaw(task)
        await send_chunked(msg, result, model_used="ecc/claw")
    except Exception as e:
        await msg.answer(f"claw error: <code>{html_mod.escape(str(e)[:350])}</code>", parse_mode="HTML")


@router.message(Command("multi_backend"))
async def cmd_multi_backend(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "multi_backend")
    if not task:
        await msg.answer("usage: <code>/multi_backend &lt;task&gt;</code>", parse_mode="HTML")
        return
    prompt = f"Backend-focused execution plan and implementation checklist:\n\n{task}"
    result, model = await chat(prompt, agent_key="coding", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/multi_backend/{model}")


@router.message(Command("multi_frontend"))
async def cmd_multi_frontend(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "multi_frontend")
    if not task:
        await msg.answer("usage: <code>/multi_frontend &lt;task&gt;</code>", parse_mode="HTML")
        return
    prompt = f"Frontend-focused execution plan and implementation checklist:\n\n{task}"
    result, model = await chat(prompt, agent_key="architect", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/multi_frontend/{model}")


@router.message(Command("multi_workflow"))
async def cmd_multi_workflow(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = _extract_arg(msg.text or "", "multi_workflow")
    if not task:
        await msg.answer("usage: <code>/multi_workflow &lt;task&gt;</code>", parse_mode="HTML")
        return
    prompt = (
        "Create an end-to-end workflow across planning, implementation, testing, and deployment.\n\n"
        f"Task:\n{task}"
    )
    result, model = await chat(prompt, agent_key="pm", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/multi_workflow/{model}")


@router.message(Command("e2e"))
async def cmd_e2e_alias(msg: Message) -> None:
    """ECC alias command for e2e planning/execution."""
    if not is_allowed(msg):
        return
    arg = _extract_arg(msg.text or "", "e2e")
    if not arg:
        await msg.answer(
            "usage: <code>/e2e &lt;url&gt;</code>\n"
            "Legion equivalents: <code>/e2etest &lt;url&gt;</code> or <code>/e2eplan &lt;url&gt;</code>",
            parse_mode="HTML",
        )
        return
    await msg.answer(
        f"Use <code>/e2etest {html_mod.escape(arg)}</code> for full run or "
        f"<code>/e2eplan {html_mod.escape(arg)}</code> for dry-run planning.",
        parse_mode="HTML",
    )


@router.message(Command("pm2"))
async def cmd_pm2(msg: Message) -> None:
    """ECC /pm2 analogue: inspect PM2 availability and process list."""
    if not is_allowed(msg):
        return
    from computer_agent import run_shell

    status = await msg.answer("🔎 checking PM2 status…")
    which_out = await run_shell("command -v pm2 || true", timeout=10)
    if not which_out or "no output" in which_out.lower():
        await status.edit_text(
            "PM2 is not installed on this machine.\n"
            "Install with: <code>npm i -g pm2</code>",
            parse_mode="HTML",
        )
        return

    out = await run_shell("pm2 list", timeout=20)
    await status.delete()
    await send_chunked(msg, f"<b>PM2 Status</b>\n\n<pre>{html_mod.escape(out)}</pre>", model_used="ecc/pm2")


@router.message(Command("go_build"))
async def cmd_go_build(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from computer_agent import run_shell

    status = await msg.answer("🛠 running Go build…")
    has_go = await run_shell("command -v go || true", timeout=10)
    if not has_go or "no output" in has_go.lower():
        await status.edit_text("Go toolchain not installed.")
        return
    out = await run_shell("cd /home/newadmin/swarm-bot && go build ./...", timeout=120)
    await status.delete()
    await send_chunked(msg, f"<pre>{html_mod.escape(out)}</pre>", model_used="ecc/go_build")


@router.message(Command("go_test"))
async def cmd_go_test(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from computer_agent import run_shell

    status = await msg.answer("🧪 running Go tests…")
    has_go = await run_shell("command -v go || true", timeout=10)
    if not has_go or "no output" in has_go.lower():
        await status.edit_text("Go toolchain not installed.")
        return
    out = await run_shell("cd /home/newadmin/swarm-bot && go test ./...", timeout=120)
    await status.delete()
    await send_chunked(msg, f"<pre>{html_mod.escape(out)}</pre>", model_used="ecc/go_test")


@router.message(Command("go_review"))
async def cmd_go_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = _extract_arg(msg.text or "", "go_review")
    if not arg:
        await msg.answer("usage: <code>/go_review &lt;file_or_snippet&gt;</code>", parse_mode="HTML")
        return

    path = Path(arg).expanduser()
    if path.exists() and path.is_file():
        content = path.read_text(encoding="utf-8", errors="replace")[:12000]
        payload = f"Review this Go file for correctness, security, and idiomatic style:\n\n{content}"
    else:
        payload = f"Review this Go code for correctness, security, and idiomatic style:\n\n{arg}"
    result, model = await chat(payload, agent_key="reviewer", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/go_review/{model}")


@router.message(Command("gradle_build"))
async def cmd_gradle_build(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from computer_agent import run_shell

    status = await msg.answer("🏗 running Gradle build…")
    wrapper_check = await run_shell("cd /home/newadmin/swarm-bot && [ -f ./gradlew ] && echo yes || true", timeout=10)
    if "yes" in wrapper_check:
        out = await run_shell("cd /home/newadmin/swarm-bot && ./gradlew build", timeout=180)
    else:
        has_gradle = await run_shell("command -v gradle || true", timeout=10)
        if not has_gradle or "no output" in has_gradle.lower():
            await status.edit_text("No <code>gradlew</code> and Gradle is not installed.", parse_mode="HTML")
            return
        out = await run_shell("cd /home/newadmin/swarm-bot && gradle build", timeout=180)
    await status.delete()
    await send_chunked(msg, f"<pre>{html_mod.escape(out)}</pre>", model_used="ecc/gradle_build")


@router.message(Command("kotlin_build"))
async def cmd_kotlin_build(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(
        "Kotlin build mapped to Gradle build. Running <code>/gradle_build</code> equivalent.",
        parse_mode="HTML",
    )
    await cmd_gradle_build(msg)


@router.message(Command("kotlin_test"))
async def cmd_kotlin_test(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from computer_agent import run_shell

    status = await msg.answer("🧪 running Kotlin/Gradle tests…")
    wrapper_check = await run_shell("cd /home/newadmin/swarm-bot && [ -f ./gradlew ] && echo yes || true", timeout=10)
    if "yes" in wrapper_check:
        out = await run_shell("cd /home/newadmin/swarm-bot && ./gradlew test", timeout=180)
    else:
        has_gradle = await run_shell("command -v gradle || true", timeout=10)
        if not has_gradle or "no output" in has_gradle.lower():
            await status.edit_text("No <code>gradlew</code> and Gradle is not installed.", parse_mode="HTML")
            return
        out = await run_shell("cd /home/newadmin/swarm-bot && gradle test", timeout=180)
    await status.delete()
    await send_chunked(msg, f"<pre>{html_mod.escape(out)}</pre>", model_used="ecc/kotlin_test")


@router.message(Command("kotlin_review"))
async def cmd_kotlin_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = _extract_arg(msg.text or "", "kotlin_review")
    if not arg:
        await msg.answer("usage: <code>/kotlin_review &lt;file_or_snippet&gt;</code>", parse_mode="HTML")
        return

    path = Path(arg).expanduser()
    if path.exists() and path.is_file():
        content = path.read_text(encoding="utf-8", errors="replace")[:12000]
        payload = f"Review this Kotlin file for correctness, security, and idiomatic style:\n\n{content}"
    else:
        payload = f"Review this Kotlin code for correctness, security, and idiomatic style:\n\n{arg}"
    result, model = await chat(payload, agent_key="reviewer", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/kotlin_review/{model}")


@router.message(Command("promote"))
async def cmd_promote(msg: Message) -> None:
    """Generate release/promotion notes from a change summary."""
    if not is_allowed(msg):
        return
    change = _extract_arg(msg.text or "", "promote")
    if not change:
        await msg.answer("usage: <code>/promote &lt;change_summary&gt;</code>", parse_mode="HTML")
        return
    prompt = (
        "Create a production promotion note with:\n"
        "- Title\n- Summary\n- Risk level\n- Rollout steps\n- Rollback plan\n- Post-deploy checks\n\n"
        f"Change:\n{change}"
    )
    result, model = await chat(prompt, agent_key="pm", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/promote/{model}")


@router.message(Command("evolve"))
async def cmd_evolve(msg: Message) -> None:
    """Generate iterative system improvement roadmap."""
    if not is_allowed(msg):
        return
    topic = _extract_arg(msg.text or "", "evolve")
    if not topic:
        await msg.answer("usage: <code>/evolve &lt;system_or_feature&gt;</code>", parse_mode="HTML")
        return
    prompt = (
        "Design an evolution roadmap in 3 horizons (now/next/later) with metrics and risks.\n\n"
        f"Target:\n{topic}"
    )
    result, model = await chat(prompt, agent_key="architect", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/evolve/{model}")


@router.message(Command("aside"))
async def cmd_aside(msg: Message) -> None:
    """Quick side-note synthesizer for context switching."""
    if not is_allowed(msg):
        return
    note = _extract_arg(msg.text or "", "aside")
    if not note:
        await msg.answer("usage: <code>/aside &lt;note_or_context&gt;</code>", parse_mode="HTML")
        return
    prompt = (
        "Rewrite this as a compact teammate aside (2-4 bullets): objective, caveat, next step.\n\n"
        f"Input:\n{note}"
    )
    result, model = await chat(prompt, agent_key="humanizer", user_id=str(msg.from_user.id))
    await send_chunked(msg, result, model_used=f"ecc/aside/{model}")

