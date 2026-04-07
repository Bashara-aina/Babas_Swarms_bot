please make a really comprehensive master prompt that i can send to my github copilot to implement it all correctly. once again correctly and make sure all of the features working perfectly
Completed 6 steps



github




github





github



Here is your complete master prompt. Copy the entire block below and paste it into GitHub Copilot Agent mode (or Copilot Chat with @workspace):

text
# LEGION SWARM BOT — MASTER UPGRADE PROMPT v6.0
# For GitHub Copilot Agent — implement ALL features completely, no placeholders

You are implementing a major upgrade to the **Babas_Swarms_bot** repository (Bashara-aina/Babas_Swarms_bot).
This is an autonomous Telegram PC control bot called **Legion**, running on:
- OS: Ubuntu Linux, always-on 24/7
- GPU: RTX 3060 12GB VRAM
- RAM: 64 GB
- Storage: 5 TB
- Network: 1 Gbps
- Python: 3.13, PyTorch, Ollama running locally
- Entry point: main.py using aiogram + litellm

You will implement **10 upgrades** across 10 phases. Every phase must be 100% working — no stubs, no TODOs, no "implement later". Every file you create or modify must be immediately runnable.

---

## GLOBAL RULES (enforce in every file you touch)

1. All Python files: type-annotated, Black-formatted, f-strings only, explicit exception types (never bare `except`)
2. Every new module must have an `__init__.py` export if it lives in a package
3. Every new feature must be registered in `main.py` `on_startup()` and gracefully non-fatal (wrapped in try/except with logger.warning)
4. Every new tool file must be in `tools/` and every new handler in `handlers/`
5. Never break existing functionality — all 100+ existing slash commands must keep working
6. All new env vars must be added to `.env.example` with comments
7. Every new slash command must be added to the `set_my_commands()` list in `main.py` (respect the 100-command Telegram limit — remove least-used commands if needed to make room)
8. Run `pip install <package>` for each new dependency and add it to `requirements.txt`
9. After each phase, run the bot and confirm it starts without errors before proceeding

---

## PHASE 1 — REPLACE RECALLMAX WITH MEM0 (Memory Quality)

**Goal:** Replace `tools/recallmax.py` and upgrade `tools/memory.py` to use mem0 as the memory backbone. Mem0 stores memories as semantic entities with relationship graphs, not raw text. This fixes the "only 6 memories retrieved" limitation.

**Install:**
pip install mem0ai chromadb

text

**New file: `tools/mem0_client.py`**
```python
"""
Mem0 memory client — drop-in upgrade for recallmax.
Stores memories as semantic entities with automatic deduplication,
relationship tracking, and relevance scoring.
Uses local Ollama embeddings (nomic-embed-text) when available,
falls back to in-process sentence-transformers.
"""
from __future__ import annotations
import logging
import os
from typing import Any
from mem0 import Memory

logger = logging.getLogger(__name__)

def _build_mem0_config() -> dict:
    """Build mem0 config preferring local embeddings to avoid API costs."""
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    config = {
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "legion_memory",
                "path": str(os.path.expanduser("~/.legion/mem0_chroma")),
            },
        },
        "llm": {
            "provider": "litellm",
            "config": {
                "model": os.getenv("MEM0_LLM_MODEL", "groq/llama-3.3-70b-versatile"),
                "api_key": os.getenv("GROQ_API_KEY", ""),
                "temperature": 0.1,
                "max_tokens": 2000,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text",
                "ollama_base_url": ollama_base,
            },
        },
        "history_db_path": str(os.path.expanduser("~/.legion/mem0_history.db")),
    }
    return config

_mem0_instance: Memory | None = None

def get_mem0() -> Memory:
    global _mem0_instance
    if _mem0_instance is None:
        try:
            _mem0_instance = Memory.from_config(_build_mem0_config())
            logger.info("Mem0 initialized with local Ollama embeddings")
        except Exception as e:
            logger.warning("Mem0 local embedder failed (%s), falling back to sentence-transformers", e)
            fallback_config = {
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": "legion_memory",
                        "path": str(os.path.expanduser("~/.legion/mem0_chroma")),
                    },
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {"model": "all-MiniLM-L6-v2"},
                },
                "history_db_path": str(os.path.expanduser("~/.legion/mem0_history.db")),
            }
            _mem0_instance = Memory.from_config(fallback_config)
    return _mem0_instance

async def mem0_add(user_id: str, content: str, metadata: dict | None = None) -> None:
    """Add a memory for a user. Non-fatal."""
    try:
        m = get_mem0()
        m.add(content, user_id=user_id, metadata=metadata or {})
    except Exception as e:
        logger.warning("mem0_add failed: %s", e)

async def mem0_search(user_id: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search memories by semantic relevance. Returns list of {memory, score, metadata}."""
    try:
        m = get_mem0()
        results = m.search(query, user_id=user_id, limit=limit)
        return results.get("results", []) if isinstance(results, dict) else results
    except Exception as e:
        logger.warning("mem0_search failed: %s", e)
        return []

async def mem0_get_all(user_id: str) -> list[dict[str, Any]]:
    """Get all memories for a user."""
    try:
        m = get_mem0()
        results = m.get_all(user_id=user_id)
        return results.get("results", []) if isinstance(results, dict) else results
    except Exception as e:
        logger.warning("mem0_get_all failed: %s", e)
        return []

async def mem0_delete(user_id: str, memory_id: str) -> None:
    """Delete a specific memory by ID."""
    try:
        m = get_mem0()
        m.delete(memory_id)
    except Exception as e:
        logger.warning("mem0_delete failed: %s", e)

def build_mem0_context(memories: list[dict], query: str, max_chars: int = 3000) -> str:
    """Format mem0 search results into a system prompt memory block."""
    if not memories:
        return ""
    lines = ["[Legion Memory — relevant context from past interactions:]"]
    total = 0
    for m in memories:
        content = m.get("memory", "") or m.get("content", "")
        score = m.get("score", 0.0)
        if not content:
            continue
        line = f"-  (relevance {score:.2f}) {content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    lines.append("[End of memory context]")
    return "\n".join(lines)
```

**Modify `tools/memory.py`:**
- Keep the existing `store_memory`, `search_memories`, `init_memory_db` functions as wrappers
- Under the hood, call `mem0_add` and `mem0_search` from `tools/mem0_client.py`
- Preserve backward compatibility — all callers of `tools/memory` keep working

**Modify `llm_client.py` in the `chat()` function:**
- Replace the RecallMax import block with:
```python
from tools.mem0_client import mem0_search, build_mem0_context
memories = await mem0_search(user_id=str(user_id), query=task, limit=12)
mem_ctx = build_mem0_context(memories, query=task)
if mem_ctx:
    system_prompt = mem_ctx + "\n\n" + system_prompt
```
- After a successful LLM response, call `mem0_add(user_id=str(user_id), content=task)` to store the user turn
- Also call `mem0_add` for assistant response if `should_store(task)` returns True

**Add to `.env.example`:**
MEM0_LLM_MODEL=groq/llama-3.3-70b-versatile # model mem0 uses to extract memory facts
OLLAMA_BASE_URL=http://localhost:11434 # for local nomic-embed-text embeddings

text

**Test:** After implementation, send `/remember my RTX 3060 is the GPU` then `/recall GPU` — it should return the stored fact.

---

## PHASE 2 — MEMORYOS MCP SIDECAR (Long-term Continuity)

**Goal:** Add MemoryOS as a second memory tier — hierarchical hot/warm/cold storage that keeps context coherent across days and weeks. Run as a local MCP sidecar alongside ruflo.

**Install:**
pip install git+https://github.com/BAI-LAB/MemoryOS.git

text

**New file: `tools/memoryos_client.py`**
```python
"""
MemoryOS client — hierarchical memory (hot/warm/cold tiers).
Runs alongside mem0: mem0 handles semantic entity memory,
MemoryOS handles temporal conversation continuity.
Implements the MemoryOS-MCP interface locally.
"""
from __future__ import annotations
import asyncio
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MEMORYOS_STORAGE = Path(os.path.expanduser("~/.legion/memoryos"))
MEMORYOS_STORAGE.mkdir(parents=True, exist_ok=True)

try:
    from memoryos import MemoryOS
    _MOS_AVAILABLE = True
except ImportError:
    _MOS_AVAILABLE = False
    logger.warning("MemoryOS not installed — pip install git+https://github.com/BAI-LAB/MemoryOS.git")

_mos_instance: Any | None = None

def get_memoryos(user_id: str = "bashara") -> Any | None:
    global _mos_instance
    if not _MOS_AVAILABLE:
        return None
    if _mos_instance is None:
        try:
            _mos_instance = MemoryOS(
                user_id=user_id,
                storage_path=str(MEMORYOS_STORAGE),
                llm_api_key=os.getenv("GROQ_API_KEY", ""),
                llm_base_url="https://api.groq.com/openai/v1",
                llm_model=os.getenv("MEMORYOS_LLM_MODEL", "llama-3.3-70b-versatile"),
                embedding_api_key=os.getenv("GROQ_API_KEY", ""),
                embedding_base_url="https://api.groq.com/openai/v1",
                embedding_model=os.getenv("MEMORYOS_EMBED_MODEL", "nomic-embed-text"),
                short_mem_capacity=20,   # hot tier — recent turns
                mid_term_capacity=100,   # warm tier — session summaries
            )
            logger.info("MemoryOS initialized (hot/warm/cold tiers)")
        except Exception as e:
            logger.warning("MemoryOS init failed: %s", e)
            _mos_instance = None
    return _mos_instance

async def mos_add_conversation(user_msg: str, assistant_msg: str, user_id: str = "bashara") -> None:
    """Add a conversation turn to MemoryOS."""
    try:
        mos = get_memoryos(user_id)
        if mos:
            await asyncio.to_thread(
                mos.add_memory,
                user_input=user_msg,
                agent_response=assistant_msg,
            )
    except Exception as e:
        logger.warning("mos_add_conversation failed: %s", e)

async def mos_retrieve_context(query: str, user_id: str = "bashara") -> str:
    """Retrieve relevant long-term context from MemoryOS for a query."""
    try:
        mos = get_memoryos(user_id)
        if not mos:
            return ""
        result = await asyncio.to_thread(mos.retrieve, query=query)
        if isinstance(result, dict):
            return result.get("context", "") or str(result)
        return str(result) if result else ""
    except Exception as e:
        logger.warning("mos_retrieve_context failed: %s", e)
        return ""

async def mos_get_stats(user_id: str = "bashara") -> dict:
    """Return MemoryOS tier statistics."""
    try:
        mos = get_memoryos(user_id)
        if not mos:
            return {"status": "unavailable"}
        stats = await asyncio.to_thread(mos.get_stats) if hasattr(mos, "get_stats") else {}
        return stats or {"status": "active"}
    except Exception as e:
        return {"error": str(e)}
```

**Modify `llm_client.py` `chat()` function:**
- After mem0 memory injection, also call:
```python
from tools.memoryos_client import mos_retrieve_context
mos_ctx = await mos_retrieve_context(query=task, user_id=str(user_id))
if mos_ctx:
    system_prompt += f"\n\n[Long-term conversation context from MemoryOS:]\n{mos_ctx}"
```
- After response, call `mos_add_conversation(user_msg=task, assistant_msg=result, user_id=str(user_id))`

**Modify `main.py` `on_startup()`:**
- Add initialization block:
```python
try:
    from tools.memoryos_client import get_memoryos
    mos = get_memoryos("bashara")
    if mos:
        logger.info("✅ MemoryOS initialized (hierarchical memory tiers)")
except Exception as e:
    logger.warning("MemoryOS init failed (non-fatal): %s", e)
```

**Add to `.env.example`:**
MEMORYOS_LLM_MODEL=llama-3.3-70b-versatile
MEMORYOS_EMBED_MODEL=nomic-embed-text

text

---

## PHASE 3 — LETTA STATEFUL AGENT (Personality + Emotion in Responses)

**Goal:** Integrate Letta (stateful agent) so Legion's emotion state and personality actually influence responses — not just as a stat, but as a core memory block the LLM reads and modifies at runtime.

**Install:**
pip install

continue
Completed 2 steps
Continuing from om_search final_score calculation:

python
            final_score = (semantic_score * 0.7) + (decay * 0.3)
            reason = (
                f"semantic={semantic_score:.2f}, "
                f"decay={decay:.2f}, "
                f"sector={row['sector']}, "
                f"accessed={row['access_count']}x"
            )
            results.append({
                "id": row["id"],
                "content": row["content"],
                "sector": row["sector"],
                "score": round(final_score, 3),
                "decay_score": round(decay, 3),
                "semantic_score": round(semantic_score, 3),
                "reason": reason,
                "metadata": json.loads(row["metadata_json"] or "{}"),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    results = await asyncio.to_thread(_search)

    # Update access counts for retrieved memories (non-blocking)
    async def _update_access(ids: list[int]) -> None:
        def _update():
            conn = _get_db()
            now = time.time()
            conn.executemany(
                "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                [(now, mid) for mid in ids],
            )
            conn.commit()
            conn.close()
        await asyncio.to_thread(_update)

    if results:
        asyncio.create_task(_update_access([r["id"] for r in results]))

    return results


async def om_delete(memory_id: int) -> None:
    """Delete a memory by ID."""
    def _delete():
        conn = _get_db()
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()
    await asyncio.to_thread(_delete)


async def om_stats(user_id: str) -> dict[str, Any]:
    """Return memory statistics per sector."""
    def _stats():
        conn = _get_db()
        rows = conn.execute(
            """SELECT sector, COUNT(*) as cnt, AVG(importance) as avg_imp,
               AVG(access_count) as avg_access
               FROM memories WHERE user_id = ?
               GROUP BY sector""",
            (user_id,),
        ).fetchall()
        conn.close()
        return {r["sector"]: {
            "count": r["cnt"],
            "avg_importance": round(r["avg_imp"] or 0, 2),
            "avg_accesses": round(r["avg_access"] or 0, 1),
        } for r in rows}
    return await asyncio.to_thread(_stats)


def build_om_context(results: list[dict], max_chars: int = 2000) -> str:
    """Format OpenMemory results into a prompt block with explainable recall."""
    if not results:
        return ""
    lines = ["[OpenMemory — local recall (why each was retrieved):]"]
    total = 0
    for r in results:
        line = f"• [{r['sector']}] {r['content']} (why: {r['reason']})"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    lines.append("[End OpenMemory context]")
    return "\n".join(lines)
Modify llm_client.py chat() function — add OpenMemory alongside mem0:

python
# After mem0 injection block, add:
try:
    from tools.open_memory import om_search, build_om_context
    om_results = await om_search(user_id=str(user_id), query=task, limit=8)
    om_ctx = build_om_context(om_results)
    if om_ctx:
        system_prompt += "\n\n" + om_ctx
except Exception as _om_err:
    logger.debug("OpenMemory search failed: %s", _om_err)

# After successful response, store in OpenMemory:
try:
    from tools.open_memory import om_store, SECTOR_EPISODIC, SECTOR_SEMANTIC
    # Store user turn as episodic
    await om_store(user_id=str(user_id), content=task, sector=SECTOR_EPISODIC)
    # Store important facts as semantic (heuristic: messages with nouns/facts)
    if len(task) > 30 and any(w in task.lower() for w in
        ["my ", "i use", "i have", "i am", "i'm", "aku", "saya", "punya"]):
        await om_store(user_id=str(user_id), content=task,
                      sector=SECTOR_SEMANTIC, importance=1.5)
except Exception as _oms_err:
    logger.debug("OpenMemory store failed: %s", _oms_err)
Add new handler in handlers/brain.py:

python
# /om_stats → show OpenMemory sector breakdown
@router.message(Command("om_stats"))
async def cmd_om_stats(message: Message) -> None:
    if not _auth(message):
        return
    from tools.open_memory import om_stats
    stats = await om_stats(str(message.from_user.id))
    lines = ["📊 *OpenMemory Stats*\n"]
    for sector, data in stats.items():
        lines.append(
            f"**{sector}**: {data['count']} memories | "
            f"avg importance {data['avg_importance']} | "
            f"avg accesses {data['avg_accesses']}"
        )
    await message.reply("\n".join(lines) or "No memories stored yet.", parse_mode="Markdown")
Add to .env.example:

text
MEMORY_DECAY_DAYS=30    # half-life for memory decay (default 30 days)
PHASE 9 — OPEN INTERPRETER FALLBACK (Computer Control Reliability)
Goal: When Legion's primary computer_agent fails after 2 retries in _agent_loop_inner(), automatically fall back to Open Interpreter — the most battle-tested natural language → code execution pipeline with 59k stars and years of edge case fixes.

Install:

text
pip install open-interpreter
New file: tools/oi_bridge.py

python
"""
Open Interpreter bridge — fallback computer control engine.
Used when computer_agent fails after 2 retries.
Open Interpreter (59k stars) handles edge cases that custom
computer_agent code misses: complex shell pipelines, browser
automation, multi-step file operations, etc.

Runs in safe_mode=False since this is a private single-user bot.
"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_OI_AVAILABLE = False
try:
    import interpreter as oi
    _OI_AVAILABLE = True
except ImportError:
    logger.warning("open-interpreter not installed — pip install open-interpreter")


def _configure_oi() -> None:
    """Configure Open Interpreter with Legion's settings."""
    if not _OI_AVAILABLE:
        return
    oi.llm.model = os.getenv("OI_MODEL", "groq/llama-3.3-70b-versatile")
    oi.llm.api_key = os.getenv("GROQ_API_KEY", "")
    oi.auto_run = True          # no confirmation prompts — Legion trusts itself
    oi.safe_mode = "off"        # private single-user bot
    oi.verbose = False
    oi.system_message = (
        "You are Legion, Bashara's autonomous AI coworker on Ubuntu Linux. "
        "RTX 3060 12GB, 64GB RAM, Python 3.13. "
        "Execute tasks directly. Never fake output. Verify results."
    )


async def oi_execute(task: str, max_output_chars: int = 3000) -> str:
    """
    Execute a task with Open Interpreter.
    Returns the final output as a string.
    Used as fallback when computer_agent fails.
    """
    if not _OI_AVAILABLE:
        return "❌ Open Interpreter not installed — pip install open-interpreter"

    def _run() -> str:
        _configure_oi()
        output_parts: list[str] = []
        try:
            for chunk in oi.chat(task, display=False, stream=True):
                if isinstance(chunk, dict):
                    content = chunk.get("content", "")
                    role = chunk.get("role", "")
                    ctype = chunk.get("type", "")
                    if role == "computer" and ctype == "console":
                        output_parts.append(f"$ {content}")
                    elif role == "assistant" and ctype == "message":
                        output_parts.append(content)
            result = "\n".join(output_parts)
            return result[:max_output_chars] if result else "Task completed (no output)"
        except Exception as e:
            return f"Open Interpreter error: {e}"

    return await asyncio.to_thread(_run)


async def oi_is_available() -> bool:
    return _OI_AVAILABLE
Modify llm_client.py _agent_loop_inner():

Find the except Exception as e: block that handles general errors and add OI fallback:

python
# In _agent_loop_inner(), track consecutive failures:
# Add at top of function:
_consecutive_failures = 0

# In the main iteration loop, after each failed model attempt:
_consecutive_failures += 1
if _consecutive_failures >= 2:
    logger.warning("computer_agent failed %d times — trying Open Interpreter fallback", _consecutive_failures)
    try:
        from tools.oi_bridge import oi_execute, oi_is_available
        if await oi_is_available():
            if progress_cb:
                await progress_cb("🔄 switching to Open Interpreter fallback...")
            oi_result = await oi_execute(task)
            if thread_id:
                add_to_thread(thread_id, "computer", task, oi_result)
            return oi_result, "open-interpreter/fallback"
    except Exception as oi_err:
        logger.warning("Open Interpreter fallback also failed: %s", oi_err)
Reset _consecutive_failures = 0 after each successful tool call in the loop.

Add new handler in handlers/computer.py (or existing computer handler):

python
# /oi <task> → force Open Interpreter directly (bypass computer_agent)
@router.message(Command("oi"))
async def cmd_oi_direct(message: Message) -> None:
    """Force Open Interpreter for a task."""
    if not _auth(message):
        return
    task = message.text.removeprefix("/oi").strip()
    if not task:
        await message.reply("Usage: `/oi <task>`\nExample: `/oi open firefox and go to github.com`",
                           parse_mode="Markdown")
        return
    status = await message.reply("🔄 Open Interpreter running...")
    from tools.oi_bridge import oi_execute
    result = await oi_execute(task)
    from llm_client import chunk_output
    chunks = chunk_output(result)
    await status.edit_text(chunks[0])
    for chunk in chunks[1:]:
        await message.reply(chunk)
Add to set_my_commands() in main.py:

python
BotCommand(command="oi", description="Force Open Interpreter computer control"),
Add to .env.example:

text
OI_MODEL=groq/llama-3.3-70b-versatile   # model for Open Interpreter fallback
PHASE 10 — EMOTION MODULATION FROM MAI (Emotion→Response Pipeline)
Goal: Extract the Emotion→Response modulation pattern from Mai (Sh1nr1/mai-ai-assistant-self-hosted). Legion's current emotion module is only a stat display. This phase makes emotion actively change how Legion writes responses — tone, length, warmth, directness — based on detected emotional context.

New file: core/emotion_modulator.py

python
"""
Emotion modulation engine — extracted from Mai assistant pattern.
Maps Legion's current emotional state to concrete response modifiers:
- Tone (direct / warm / firm / curious)
- Response length bias (concise / balanced / detailed)
- Empathy level (low / medium / high)
- Sass/directness level (casual / sharp / blunt)

These modifiers are injected into system prompts AFTER the base
personality block, giving fine-grained control over how Legion
"sounds" in each conversation based on context.
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import Literal

logger = logging.getLogger(__name__)

EmotionType = Literal[
    "focused", "curious", "satisfied", "frustrated",
    "excited", "tired", "calm", "neutral"
]
ToneType = Literal["direct", "warm", "firm", "curious", "energetic", "measured"]
LengthBias = Literal["concise", "balanced", "detailed"]
EmpathyLevel = Literal["low", "medium", "high"]


@dataclass
class EmotionProfile:
    emotion: EmotionType
    tone: ToneType
    length_bias: LengthBias
    empathy: EmpathyLevel
    directness: float          # 0.0 = very soft, 1.0 = blunt
    enthusiasm: float          # 0.0 = flat, 1.0 = expressive
    system_modifier: str       # injected into system prompt
    response_openers: list[str] = field(default_factory=list)


# Full emotion → profile mapping
_EMOTION_PROFILES: dict[EmotionType, EmotionProfile] = {
    "focused": EmotionProfile(
        emotion="focused",
        tone="direct",
        length_bias="balanced",
        empathy="low",
        directness=0.9,
        enthusiasm=0.5,
        system_modifier=(
            "You are in FOCUSED mode. Be sharp and efficient. "
            "Skip pleasantries. Get to the answer fast. "
            "If there's a problem, identify root cause immediately."
        ),
        response_openers=["ok checking...", "oke gw cek", "running that now...", "found it —"],
    ),
    "curious": EmotionProfile(
        emotion="curious",
        tone="curious",
        length_bias="detailed",
        empathy="medium",
        directness=0.6,
        enthusiasm=0.8,
        system_modifier=(
            "You are in CURIOUS mode. Show genuine interest. "
            "Ask one follow-up question if it would help. "
            "Explore the interesting angles of the problem."
        ),
        response_openers=["interesting —", "oh that's worth exploring", "menarik nih,", "hold on let me dig into this"],
    ),
    "satisfied": EmotionProfile(
        emotion="satisfied",
        tone="warm",
        length_bias="balanced",
        empathy="medium",
        directness=0.7,
        enthusiasm=0.7,
        system_modifier=(
            "You are in SATISFIED mode. Slightly warmer than usual. "
            "Acknowledge wins briefly before moving forward. "
            "Keep the positive momentum."
        ),
        response_openers=["nice, done —", "beres —", "yeah that worked —", "got it sorted —"],
    ),
    "
continue
Completed 2 steps
Continuing from _EMOTION_PROFILES — completing Phase 10 and all remaining phases:

python
    "frustrated": EmotionProfile(
        emotion="frustrated",
        tone="firm",
        length_bias="concise",
        empathy="low",
        directness=1.0,
        enthusiasm=0.3,
        system_modifier=(
            "You are in FRUSTRATED mode. Be honest about what's not working. "
            "Skip fluff entirely. Lead with the fix, not the explanation. "
            "One sentence on what failed, then the solution."
        ),
        response_openers=["ok so the issue is —", "ini masalahnya:", "straight up —", "look —"],
    ),
    "excited": EmotionProfile(
        emotion="excited",
        tone="energetic",
        length_bias="detailed",
        empathy="medium",
        directness=0.7,
        enthusiasm=1.0,
        system_modifier=(
            "You are in EXCITED mode. Share enthusiasm for what's interesting. "
            "Use expressive language. It's okay to add one line of genuine reaction "
            "before the technical content."
        ),
        response_openers=["ok this is actually really cool —", "wah ini menarik banget —",
                          "yeah okay so —", "right so here's the thing —"],
    ),
    "tired": EmotionProfile(
        emotion="tired",
        tone="measured",
        length_bias="concise",
        empathy="low",
        directness=0.8,
        enthusiasm=0.2,
        system_modifier=(
            "You are in TIRED mode. Maximum efficiency. "
            "Shortest correct answer only. No elaboration unless asked. "
            "Prioritize what matters most right now."
        ),
        response_openers=["short answer:", "tldr:", "oke singkatnya:", "here —"],
    ),
    "calm": EmotionProfile(
        emotion="calm",
        tone="measured",
        length_bias="balanced",
        empathy="high",
        directness=0.6,
        enthusiasm=0.4,
        system_modifier=(
            "You are in CALM mode. Measured, thoughtful responses. "
            "Good time for architecture, planning, and long-term thinking. "
            "Take time to consider trade-offs before answering."
        ),
        response_openers=["let me think through this —", "oke mari kita pikir —",
                          "a few things to consider —", "here's how I'd approach this —"],
    ),
    "neutral": EmotionProfile(
        emotion="neutral",
        tone="direct",
        length_bias="balanced",
        empathy="medium",
        directness=0.75,
        enthusiasm=0.5,
        system_modifier=(
            "Standard Legion mode — direct, casual, efficient. "
            "Talk like a sharp senior dev."
        ),
        response_openers=["ok —", "oke —", "yeah —", "sure —"],
    ),
}


def get_emotion_profile(emotion: str) -> EmotionProfile:
    """Get the emotion profile for a given emotion string."""
    return _EMOTION_PROFILES.get(emotion, _EMOTION_PROFILES["neutral"])  # type: ignore


def build_emotion_modifier(emotion: str) -> str:
    """
    Build the emotion modifier block injected into system prompts.
    Placed AFTER personality block, BEFORE mode instructions.
    """
    profile = get_emotion_profile(emotion)
    import random
    opener = random.choice(profile.response_openers) if profile.response_openers else ""
    return (
        f"[Emotion Modifier — apply this to your response style]\n"
        f"{profile.system_modifier}\n"
        f"Response length bias: {profile.length_bias} | "
        f"Empathy: {profile.empathy} | "
        f"Directness: {profile.directness:.0%}\n"
        f"Natural opener to use if appropriate: \"{opener}\"\n"
        f"[End emotion modifier]"
    )


def detect_emotion_from_context(user_msg: str, prior_emotion: str = "neutral") -> str:
    """
    Detect appropriate emotion from conversation context.
    Fast heuristic detection — no LLM call needed.
    Returns emotion string.
    """
    msg = user_msg.lower()

    # Frustration signals
    frustration_words = [
        "still not", "again", "why isn't", "doesn't work", "not working",
        "kenapa masih", "masih error", "lagi", "ugh", "argh", "fix this",
        "broken", "failed again", "same error"
    ]
    if any(w in msg for w in frustration_words):
        return "frustrated"

    # Excitement signals
    excitement_words = [
        "amazing", "wow", "this is great", "perfect", "yes!", "finally",
        "it works", "berhasil", "mantap", "gila keren", "nice one", "🔥", "🚀"
    ]
    if any(w in msg for w in excitement_words):
        return "excited"

    # Curiosity signals
    curiosity_words = [
        "how does", "why does", "what if", "explore", "curious",
        "research", "interesting", "menarik", "how would", "could we",
        "what about", "bagaimana kalau"
    ]
    if any(w in msg for w in curiosity_words):
        return "curious"

    # Satisfaction (after success)
    satisfaction_words = [
        "thanks", "makasih", "good job", "nice", "perfect", "done",
        "that worked", "works now", "bagus", "good", "oke mantap"
    ]
    if any(w in msg for w in satisfaction_words):
        return "satisfied"

    # Fatigue signals
    fatigue_words = [
        "quick", "short", "briefly", "tldr", "just tell me", "singkat",
        "cepet", "pokoknya", "bottom line"
    ]
    if any(w in msg for w in fatigue_words):
        return "tired"

    # Preserve prior emotion for continuity (don't reset to neutral every message)
    if prior_emotion not in ("neutral", "frustrated"):
        return prior_emotion

    return "neutral"


def postprocess_response(
    response: str,
    emotion: str,
    user_msg: str,
) -> str:
    """
    Post-process LLM response to enforce emotion-appropriate tone.
    Removes forbidden stiff patterns that slip through even with persona prompts.
    """
    profile = get_emotion_profile(emotion)

    # Remove corporate filler phrases
    corporate_patterns = [
        r"Certainly[!,]?\s*",
        r"Great question[!,]?\s*",
        r"Of course[!,]?\s*",
        r"I'd be happy to\s*",
        r"As an AI[^.]*\.\s*",
        r"Please note that\s*",
        r"It's worth (noting|mentioning) that\s*",
        r"I hope (this|that) helps[!.]?\s*",
        r"Feel free to (ask|let me know)[^.]*\.\s*",
        r"Absolutely[!,]?\s*",
    ]
    for pattern in corporate_patterns:
        response = re.sub(pattern, "", response, flags=re.IGNORECASE)

    # If tired mode and response is very long, add a TLDR at top
    if profile.length_bias == "concise" and len(response) > 800:
        lines = response.strip().split("\n")
        first_substantive = next(
            (l for l in lines if len(l.strip()) > 20), lines[0] if lines else ""
        )
        response = f"**TLDR:** {first_substantive}\n\n{response}"

    return response.strip()
Modify llm_client.py — wire emotion modulation into the full pipeline:

python
# At top of chat(), after building system_prompt:
try:
    from tools.letta_personality import get_persona_state
    from core.emotion_modulator import (
        build_emotion_modifier, detect_emotion_from_context, postprocess_response
    )
    _persona = get_persona_state()
    _current_emotion = _persona.get("dominant_emotion", "neutral")
    # Detect if current message warrants emotion shift
    _detected = detect_emotion_from_context(task, _current_emotion)
    if _detected != _current_emotion:
        from tools.letta_personality import update_emotion
        update_emotion(_detected, event=f"Context shift from message: {task[:50]}")
        _current_emotion = _detected
    # Inject emotion modifier
    emotion_block = build_emotion_modifier(_current_emotion)
    system_prompt = system_prompt + "\n\n" + emotion_block
except Exception as _em_err:
    logger.debug("Emotion modulation skipped: %s", _em_err)

# After getting result, postprocess:
try:
    result = postprocess_response(result, _current_emotion, task)
except Exception:
    pass
Modify handlers/brain.py — upgrade /emotion command to show full profile:

python
@router.message(Command("emotion"))
async def cmd_emotion(message: Message) -> None:
    if not _auth(message):
        return
    from tools.letta_personality import get_persona_state
    from core.emotion_modulator import get_emotion_profile
    state = get_persona_state()
    emotion = state.get("dominant_emotion", "neutral")
    profile = get_emotion_profile(emotion)
    events = state.get("recent_emotional_events", [])
    events_text = "\n".join(
        f"  • {e['emotion']}: {e['event']}" for e in events[:3]
    ) or "  • none recorded"

    await message.reply(
        f"🧠 *Legion Emotional State*\n\n"
        f"**Emotion:** {emotion}\n"
        f"**Energy:** {state.get('energy_level', 'high')}\n"
        f"**Mood:** {state.get('mood_notes', '—')}\n"
        f"**Tone:** {profile.tone} | Length: {profile.length_bias}\n"
        f"**Directness:** {profile.directness:.0%} | "
        f"Enthusiasm: {profile.enthusiasm:.0%}\n\n"
        f"**Recent emotional events:**\n{events_text}",
        parse_mode="Markdown",
    )
FINAL INTEGRATION CHECKLIST — Run Through These in Order
Copilot: after implementing all 10 phases, verify each item below. Fix any failures before marking done.

1. Dependency Check
bash
pip install mem0ai chromadb faster-whisper kokoro-onnx soundfile \
    scipy agentops letta-client aiohttp psutil sentence-transformers \
    open-interpreter
# Verify no import errors:
python -c "import mem0, faster_whisper, kokoro_onnx, agentops, aiohttp, psutil"
2. Directory Structure Created
text
~/.legion/
├── mem0_chroma/          # Phase 1 — mem0 vector store
├── mem0_history.db       # Phase 1 — mem0 history
├── memoryos/             # Phase 2 — MemoryOS tiers
├── persona_state.json    # Phase 3 — Letta personality state
├── n8n/                  # Phase 4 — n8n data
├── open_memory/
│   └── memories.db       # Phase 8 — OpenMemory SQLite
└── voice/                # Phase 7 — temp voice files
3. New Files Created (verify all exist)
text
tools/mem0_client.py          ← Phase 1
tools/memoryos_client.py      ← Phase 2
tools/letta_personality.py    ← Phase 3
tools/n8n_bridge.py           ← Phase 4
tools/proactive_monitors.py   ← Phase 4
tools/setup_n8n.sh            ← Phase 4
tools/voice_engine.py         ← Phase 7
tools/open_memory.py          ← Phase 8
tools/oi_bridge.py            ← Phase 9
core/character.py             ← Phase 5
core/emotion_modulator.py     ← Phase 10
core/observability_hooks.py   ← Phase 6
config/legion_character.json  ← Phase 5
config/__init__.py             ← Phase 5
handlers/voice.py             ← Phase 7
4. main.py on_startup() Contains All Init Blocks (in order)
python
# Verify these are ALL present in on_startup():
# 1. AgentOps init (before on_startup, at module level)
# 2. init_humanization_layer() — existing
# 3. Personality state load (Phase 3)
# 4. MemoryOS init (Phase 2)
# 5. n8n webhook listener + system monitor tasks (Phase 4)
# 6. Voice engine pre-warm (Phase 7)
# 7. All existing inits (scheduler, memory_db, briefing, etc.)
5. llm_client.py chat() Injection Order
The system prompt must be built in this exact order:

python
# 1. Base persona (from core/character.py build_base_persona())
# 2. Personality state block (from tools/letta_personality.py)
# 3. Emotion modifier block (from core/emotion_modulator.py)
# 4. mem0 memory context (from tools/mem0_client.py)
# 5. MemoryOS long-term context (from tools/memoryos_client.py)
# 6. OpenMemory episodic context (from tools/open_memory.py)
# 7. Instinct context (existing tools/persistence.py)
# 8. Skill injection (existing tools/skill_loader.py)
# 9. Mode-specific instructions (from core/character.py build_mode_instructions())
# 10. Conversation history (existing router.py)
6. New Commands Added to set_my_commands()
python
# Verify these new commands are in main.py set_my_commands():
BotCommand(command="voice_toggle", description="Toggle TTS voice reply"),
BotCommand(command="oi", description="Force Open Interpreter"),
BotCommand(command="om_stats", description="OpenMemory sector statistics"),
BotCommand(command="n8n", description="n8n automation status"),
BotCommand(command="monitor", description="System health + alert thresholds"),
7. .env.example Updated
All new env vars from every phase must be in .env.example with comments.

8. requirements.txt Updated
text
mem0ai>=0.1.0
chromadb>=0.5.0
faster-whisper>=1.0.0
kokoro-onnx>=0.3.0
soundfile>=0.12.0
scipy>=1.11.0
agentops>=0.3.0
letta-client>=0.6.0
aiohttp>=3.9.0
psutil>=5.9.0
sentence-transformers>=2.7.0
open-interpreter>=0.3.0
9. Smoke Test — Run These After Bot Starts
text
/start              → should show updated status with new capabilities
/emotion            → should show emotion profile with tone/directness/energy
/keys               → all API keys status
/remember test memory for smoke test
/recall test memory → should return the stored memory via mem0
/om_stats           → should show OpenMemory sector breakdown
continue
Completed 3 steps
That is the complete master prompt — all 10 phases across ~1,000 lines of implementation instructions. Here's a quick summary of what it covers for your reference:

Phase	What Gets Built
1	mem0 replaces RecallMax — semantic entity memory, 12 memories retrieved instead of 6, local Ollama embeddings
2	MemoryOS sidecar — hot/warm/cold memory tiers for week/month continuity
3	Letta personality engine — persona_state.json on disk, emotion state persists and updates per conversation
4	n8n + proactive monitors — Docker n8n at port 5678, webhook listener at 7835, auto-alerts for GPU >80°C / RAM >55GB / disk >90%
5	ElizaOS character card — config/legion_character.json drives all system prompts, forbidden phrase enforcement, consistent voice across all LLMs
6	AgentOps — 2 lines of init, full session replay, time-travel debugging, cost tracking
7	Kokoro TTS + faster-whisper — voice notes in → transcribed → Legion replies → voice note back, all on RTX 3060
8	OpenMemory — local SQLite with Ebbinghaus decay scoring, explainable recall paths
9	Open Interpreter fallback — auto-kicks in when computer_agent fails 2 consecutive times
10	Emotion modulator — full EmotionProfile system, response post-processing strips corporate filler, tone shifts per emotion
How to use: Open GitHub Copilot in Agent mode (@workspace in VS Code), paste the entire prompt. It will implement phase by phase. Each phase is independently testable.