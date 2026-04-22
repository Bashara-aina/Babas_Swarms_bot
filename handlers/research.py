"""Research handlers: /scrape /research /paper /ask_paper /workernet_papers."""

from __future__ import annotations

import asyncio
import html as html_mod
import logging
import os
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from llm_client import run_shell_command

from .shared import (
    _keep_typing,
    _last_screenshot,
    is_allowed,
    send_chunked,
)

router = Router()


# ── /scrape ───────────────────────────────────────────────────────────────────
@router.message(Command("scrape"))
async def cmd_scrape(msg: Message) -> None:
    if not is_allowed(msg):
        return
    url = (msg.text or "").removeprefix("/scrape").strip()
    if not url:
        await msg.answer("usage: <code>/scrape &lt;url&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer(f"🔍 scraping <code>{url}</code>…", parse_mode="HTML")
    typing_task = asyncio.create_task(_keep_typing(msg))
    typing_task.add_done_callback(
        lambda t: logging.getLogger(__name__).error("%s", t.exception()) if t.exception() else None
    )

    try:
        from tools.web_browser import browse_url

        result = await browse_url(url)
        typing_task.cancel()
        await status_msg.delete()
        title = result.get("title", "")
        text = result.get("text", "")[:3500]
        screenshot_path = result.get("screenshot_path", "")

        if screenshot_path and Path(screenshot_path).exists():
            _last_screenshot[msg.from_user.id] = screenshot_path
            await msg.answer_photo(
                photo=FSInputFile(screenshot_path),
                caption=f"🌐 {title[:100]}" if title else "🌐 page screenshot",
            )

        output = {"success": True, "data": {"title": title, "text": text}, "error": None}
        await msg.answer(
            f"<b>🌐 {title}</b>\n\n<pre>{text}</pre>",
            parse_mode="HTML",
        )
    except Exception:
        typing_task.cancel()
        try:
            await status_msg.delete()
        except Exception:
            pass
        output = await run_shell_command(
            f"curl -sL --max-time 15 --user-agent 'Mozilla/5.0' '{url}' | "
            'python3 -c "'
            "import sys; from html.parser import HTMLParser\n"
            "class P(HTMLParser):\n"
            "    def __init__(self): super().__init__(); self.d=[]; self.skip=False\n"
            "    def handle_starttag(self,t,a): self.skip=t in('script','style','head')\n"
            "    def handle_endtag(self,t): self.skip=False\n"
            "    def handle_data(self,d):\n"
            "        if not self.skip and d.strip(): self.d.append(d.strip())\n"
            "p=P(); p.feed(sys.stdin.read()); print('\\n'.join(p.d[:100]))"
            '"',
            timeout=25,
        )
        output = {"success": True, "data": {"title": url, "text": output}, "error": None}
        await msg.answer(
            f"<b>🌐 {url}</b>\n\n<pre>{output['data']['text'][:3500]}</pre>",
            parse_mode="HTML",
        )


# ── /research ────────────────────────────────────────────────────────────────
@router.message(Command("research"))
async def cmd_research(msg: Message) -> None:
    if not is_allowed(msg):
        return
    topic = (msg.text or "").removeprefix("/research").strip()
    if not topic:
        await msg.answer(
            "usage: <code>/research &lt;topic&gt;</code>\n\n"
            "deep multi-page web research — searches, visits pages, "
            "extracts and compiles findings.\n\n"
            "examples:\n"
            "<code>/research latest pytorch transformer architectures</code>\n"
            "<code>/research padang food delivery market jakarta 2026</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer(f"🧠 [Plan] researching: <i>{topic[:80]}</i>…", parse_mode="HTML")
    typing_task = asyncio.create_task(_keep_typing(msg))
    typing_task.add_done_callback(
        lambda t: logging.getLogger(__name__).error("%s", t.exception()) if t.exception() else None
    )

    if os.getenv("LEGION_RESEARCH_USE_PIPELINE", "0").strip().lower() in ("1", "true", "yes", "on"):
        try:
            from agents.research_agent import run_research_pipeline

            out = await run_research_pipeline(
                topic,
                user_id=str(msg.from_user.id) if msg.from_user else None,
            )
            output = {"success": True, "data": out, "error": None}
        finally:
            typing_task.cancel()
        try:
            await status_msg.delete()
        except Exception:
            pass
        await send_chunked(msg, out or "(empty)")
        return

    # GPT-Researcher integration
    if os.getenv("LEGION_RESEARCH_USE_GPTR", "0").strip().lower() in ("1", "true", "yes", "on"):
        try:
            from core.skills.deep_research import execute as gptr_execute

            typing_task.cancel()
            await status_msg.edit_text(f"🔬 GPT-Researcher: {topic[:40]}…", parse_mode="HTML")
            result = await gptr_execute(topic)
            output = {"success": True, "data": result, "error": None}
            await send_chunked(msg, result)
            return
        except Exception as e:
            await msg.answer(f"GPT-Researcher error: {e}")
            output = {"success": False, "data": None, "error": str(e)}
            return

    async def _phase(text: str) -> None:
        try:
            if text.startswith("💭"):
                await msg.answer(f"<i>{html_mod.escape(text)}</i>", parse_mode="HTML")
            else:
                await status_msg.edit_text(html_mod.escape(text), parse_mode="HTML")
        except Exception:
            pass

    try:
        from agents.ag2_pipeline import ResearchSwarm
        from llm_client import chat
        from tools.quality_guard import (
            build_evidence_envelope,
            format_verifier_block,
            gather_fused_evidence,
            verify_and_repair,
        )

        await _phase("🌐 [Act] collecting fused evidence (web + arXiv + memory)")
        evidence_meta = await gather_fused_evidence(
            topic,
            user_id=str(msg.from_user.id) if msg.from_user else "0",
            min_sources=5,
            start_pages=8,
            max_pages=20,
            max_attempts=3,
        )

        evidence = evidence_meta.get("evidence", "")
        source_count = int(evidence_meta.get("source_count", 0))
        min_sources = int(evidence_meta.get("min_sources", 5))

        if source_count < min_sources:
            await _phase(
                f"💭 source gate warning: got {source_count}/{min_sources} sources; continuing with explicit low-confidence warning"
            )
        else:
            await _phase(f"💭 source gate passed: {source_count} sources collected")

        await _phase("🧪 [Verify] synthesizing with AG2 research swarm")
        user_id = str(msg.from_user.id) if msg.from_user else "0"
        synthesis_prompt = (
            "You are a deep research analyst. Use ONLY the supplied evidence to answer. "
            "If evidence is insufficient, say that explicitly.\n\n"
            f"Research question:\n{topic}\n\n"
            f"Evidence corpus:\n{evidence[:22000]}\n\n"
            "Return this structure:\n"
            "1) Executive Summary\n"
            "2) Key Findings (numbered)\n"
            "3) Source-backed Evidence\n"
            "4) Risks / Unknowns\n"
            "5) Actionable Next Steps"
        )
        draft = ""
        try:
            convo = await ResearchSwarm().run(synthesis_prompt, max_turns=6)
            draft = convo.output
        except Exception:
            draft, _ = await chat(synthesis_prompt, agent_key="analyst", user_id=user_id)
        verified, verify_meta = await verify_and_repair(topic, draft, user_id=user_id)

        source_gate_block = (
            "\n\n### Source Gate\n"
            f"- Required sources: {min_sources}\n"
            f"- Collected sources: {source_count}\n"
            f"- Status: {'PASS' if source_count >= min_sources else 'WARN'}"
        )
        result = (
            verified
            + build_evidence_envelope(evidence, verified)
            + source_gate_block
            + format_verifier_block(verify_meta)
        )

        typing_task.cancel()
        await status_msg.delete()
        output = {"success": True, "data": result, "error": None}
        await send_chunked(msg, result, model_used="deep-research/verified")
    except Exception as e:
        typing_task.cancel()
        try:
            await status_msg.edit_text(
                f"research failed: <code>{e}</code>\n\n"
                "make sure Playwright is installed:\n"
                "<code>/install playwright</code> then <code>playwright install chromium</code>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        output = {"success": False, "data": None, "error": str(e)}


# ── /paper — arXiv paper search ────────────────────────────────────────────────
@router.message(Command("paper"))
async def cmd_paper(msg: Message) -> None:
    if not is_allowed(msg):
        return
    query = (msg.text or "").removeprefix("/paper").strip()
    if not query:
        await msg.answer(
            "usage: <code>/paper &lt;query&gt;</code>\n\n"
            "searches arXiv and returns top 3 results.\n\n"
            "examples:\n"
            "<code>/paper Kendall multi-task learning uncertainty</code>\n"
            "<code>/paper FiLM visual reasoning conditioning</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer(f"searching arXiv: {query[:50]}...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    typing_task.add_done_callback(
        lambda t: logging.getLogger(__name__).error("%s", t.exception()) if t.exception() else None
    )
    try:
        from tools.arxiv import search_arxiv

        papers = await search_arxiv(query, max_results=3)
        typing_task.cancel()
        await status_msg.delete()
        output = {"success": True, "data": {"papers": papers}, "error": None}
        if not papers:
            await msg.answer("No papers found.")
            return
        for p in papers:
            text = (
                f"<b>{p['title'][:200]}</b>\n"
                f"<i>{p['authors']}</i> | {p['published']}\n\n"
                f"{p['abstract'][:400]}...\n\n"
                f"ID: <code>{p['arxiv_id']}</code>\n"
                f"PDF: {p['pdf_url']}"
            )
            try:
                await msg.answer(text, parse_mode="HTML")
            except Exception:
                await msg.answer(text)
    except Exception as e:
        typing_task.cancel()
        try:
            await status_msg.edit_text(f"arXiv error: <code>{e}</code>", parse_mode="HTML")
        except Exception:
            pass
        output = {"success": False, "data": None, "error": str(e)}


# ── /ask_paper — question about a specific paper ──────────────────────────────
@router.message(Command("ask_paper"))
async def cmd_ask_paper(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/ask_paper").strip()
    if not text:
        await msg.answer(
            "usage: <code>/ask_paper &lt;arxiv_id&gt; &lt;question&gt;</code>\n\n"
            "example:\n"
            "<code>/ask_paper 1705.07115 is clamping log_var justified?</code>",
            parse_mode="HTML",
        )
        return
    parts = text.split(maxsplit=1)
    arxiv_id = parts[0]
    question = parts[1] if len(parts) > 1 else "Summarize the key contributions."
    status_msg = await msg.answer(f"downloading {arxiv_id}...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    typing_task.add_done_callback(
        lambda t: logging.getLogger(__name__).error("%s", t.exception()) if t.exception() else None
    )
    try:
        from tools.arxiv import analyze_paper, download_paper, extract_paper_text

        pdf_path = await download_paper(arxiv_id)
        await status_msg.edit_text("extracting text...")
        paper_text = extract_paper_text(pdf_path)
        await status_msg.edit_text("analyzing...")
        analysis = await analyze_paper(paper_text, question)
        typing_task.cancel()
        await status_msg.delete()
        output = {"success": True, "data": analysis, "error": None}
        await send_chunked(msg, analysis, model_used="debug/paper-analysis")
        try:
            from tools.memory import auto_save_research

            await auto_save_research(analysis, arxiv_id)
        except Exception:
            pass
    except Exception as e:
        typing_task.cancel()
        try:
            await status_msg.edit_text(f"paper error: <code>{e}</code>", parse_mode="HTML")
        except Exception:
            pass
        output = {"success": False, "data": None, "error": str(e)}


# ── /workernet_papers — DEPRECATED ────────────────────────────────────────────
@router.message(Command("workernet_papers"))
async def cmd_workernet_papers(msg: Message) -> None:
    """Deprecated: /workernet_papers has been replaced."""
    await msg.answer(
        "⚠️ <b>Deprecated:</b> /workernet_papers is no longer available.\n\n"
        "替代方案 / Alternatives:\n"
        "• <code>/research &lt;topic&gt;</code> — deep multi-source research\n"
        "• <code>/paper &lt;query&gt;</code> — search arXiv for specific papers\n"
        "• <code>/ask_paper &lt;arxiv_id&gt; &lt;question&gt;</code> — analyze a specific paper\n\n"
        "The 6 WorkerNet papers are now available via <code>/paper</code> individually.",
        parse_mode="HTML",
    )
