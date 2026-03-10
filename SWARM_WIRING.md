# 🐝 Swarm Wiring Guide

> How to activate the full swarm in `main.py`

## What was added

| File | What it does |
|------|--------------|
| `tools/swarm_wire.py` | Full swarm pipeline: 9 depts × 8 agents + 4-round debate |
| `agents/__init__.py` | Package init |
| `agents/*/\__init__.py` | One per department (9 total) |

## Agent count

| Layer | Count |
|-------|-------|
| Specialist agents (9 depts × 8) | 72 |
| Department leads (9) | 9 |
| Debate personas (6) | 6 |
| **Total per /swarm call** | **87** |
| **Total LLM calls (4 debate rounds)** | **~96** |

## Wire into main.py

Replace the current `cmd_swarm()` function body with:

```python
@dp.message(Command("swarm"))
async def cmd_swarm(msg: Message):
    if not is_allowed(msg):
        return
    task = msg.text.replace("/swarm", "", 1).strip()
    if not task:
        await msg.answer(
            "🐝 <b>Swarm Debate</b>\n\n"
            "Usage: <code>/swarm your question or topic</code>\n\n"
            "What happens:\n"
            "• 9 departments × 8 specialist agents analyse your topic in parallel\n"
            "• Each dept lead synthesizes their team into one position\n"
            "• 6 debate personas run a 4-round structured debate\n"
            "• A judge synthesizes the final verdict\n\n"
            f"Total: ~87 agents, ~96 LLM calls\n"
            "Use <code>/swarm_quick</code> to skip departments and just debate.",
            parse_mode="HTML"
        )
        return

    status = await msg.answer(
        f"🐝 Swarm activated for: <i>{html.escape(task[:100])}</i>\n"
        f"⏳ Launching 9 departments + 72 agents in parallel...",
        parse_mode="HTML"
    )

    async def progress(text: str):
        try:
            await status.edit_text(
                f"🐝 <b>Swarm running...</b>\n\n{text}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    try:
        from tools.swarm_wire import run_swarm_debate
        messages = await run_swarm_debate(task, progress_fn=progress)
        await status.delete()
        for chunk in messages:
            if chunk.strip():
                await msg.answer(chunk[:4096], parse_mode="HTML")
                await asyncio.sleep(0.3)  # avoid flood limits
    except Exception as e:
        logger.exception("Swarm error: %s", e)
        await status.edit_text(f"❌ Swarm error: {html.escape(str(e))}", parse_mode="HTML")


@dp.message(Command("swarm_quick"))
async def cmd_swarm_quick(msg: Message):
    """Skip departments, run only the 4-round debate (faster, 6 agents)."""
    if not is_allowed(msg):
        return
    task = msg.text.replace("/swarm_quick", "", 1).strip()
    if not task:
        await msg.answer("Usage: <code>/swarm_quick your question</code>", parse_mode="HTML")
        return

    status = await msg.answer(
        f"⚡ Quick swarm: 6 debate personas, 4 rounds...\n"
        f"<i>{html.escape(task[:100])}</i>",
        parse_mode="HTML"
    )

    async def progress(text: str):
        try:
            await status.edit_text(
                f"⚡ <b>Debate running...</b>\n\n{text}", parse_mode="HTML"
            )
        except Exception:
            pass

    try:
        from tools.swarm_wire import run_swarm_debate
        messages = await run_swarm_debate(task, progress_fn=progress, skip_departments=True)
        await status.delete()
        for chunk in messages:
            if chunk.strip():
                await msg.answer(chunk[:4096], parse_mode="HTML")
                await asyncio.sleep(0.3)
    except Exception as e:
        logger.exception("Swarm quick error: %s", e)
        await status.edit_text(f"❌ Error: {html.escape(str(e))}", parse_mode="HTML")


@dp.message(Command("swarm_stats"))
async def cmd_swarm_stats(msg: Message):
    """Show swarm capability overview."""
    if not is_allowed(msg):
        return
    from tools.swarm_wire import get_swarm_stats
    await msg.answer(get_swarm_stats(), parse_mode="HTML")
```

## How it works

```
/swarm <topic>
    │
    ├─ Phase 1: Department Sprint (asyncio.gather — ALL in parallel)
    │   ├─ ⚙️ Engineering dept ── 8 agents in parallel ── Lead Engineer synthesizes
    │   ├─ 🔬 Research dept    ── 8 agents in parallel ── Research Director synthesizes
    │   ├─ 📦 Product dept     ── 8 agents in parallel ── Head of Product synthesizes
    │   ├─ 📣 Marketing dept   ── 8 agents in parallel ── CMO synthesizes
    │   ├─ 🎨 Design dept      ── 8 agents in parallel ── Design Lead synthesizes
    │   ├─ 🏭 Operations dept  ── 8 agents in parallel ── COO synthesizes
    │   ├─ ✨ Creative dept    ── 8 agents in parallel ── Creative Director synthesizes
    │   ├─ ⚖️ Legal dept       ── 8 agents in parallel ── General Counsel synthesizes
    │   └─ 🧭 Strategy Nexus   ── 8 agents in parallel ── CSO synthesizes
    │
    ├─ Phase 2: 4-Round Debate (dept lead positions injected as context)
    │   ├─ Round 1: ⚔️ Strategist, 🔥 Devil, 📚 Researcher, 🔧 Pragmatist,
    │   │          🚀 Visionary, ✂️ Critic ── ALL in parallel
    │   ├─ Round 2: All 6 cross-examine each other ── ALL in parallel
    │   ├─ Round 3: Judge (Gemini) synthesizes ── consensus + verdict
    │   └─ Round 4: All 6 rate the verdict 1–10 ── ALL in parallel
    │
    └─ Phase 3: Format → 4 Telegram messages sent sequentially
```

## Quick commands

| Command | What it does | Agents | Time |
|---------|-------------|--------|------|
| `/swarm <topic>` | Full 9-dept + 4-round debate | ~87 | 60–120s |
| `/swarm_quick <topic>` | Just the 4-round debate | 6×4 = 24 | 15–30s |
| `/swarm_stats` | Show capability overview | — | instant |
