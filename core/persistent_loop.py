"""Persistent autonomous loop — survives bot restarts via SQLite state.

Fixes the 30-minute wall-clock cap by persisting loop state to SQLite
and resuming via APScheduler on bot startup.

Usage in handlers/ai.py:
    from core.persistent_loop import PersistentLoop
    loop = PersistentLoop(db_path="data/loops.db")
    await loop.start(user_id, goal, max_iterations=100, cost_ceiling=5.0)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import aiosqlite

logger = logging.getLogger(__name__)

DB_DEFAULT = "data/loops.db"


@dataclass
class LoopState:
    user_id: int
    goal: str
    thread_id: Optional[str]
    iteration: int = 0
    max_iterations: int = 100
    cost_ceiling: float = 5.0
    cost_so_far: float = 0.0
    status: str = "running"      # running | paused | done | failed
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result_summary: str = ""


class PersistentLoop:
    """Manages long-running autonomous loops with SQLite persistence."""

    def __init__(self, db_path: str = DB_DEFAULT):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def _init_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS loops (
                    user_id     INTEGER PRIMARY KEY,
                    state_json  TEXT NOT NULL,
                    updated_at  REAL NOT NULL
                )
            """)
            await db.commit()

    async def save(self, state: LoopState) -> None:
        state.updated_at = time.time()
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO loops (user_id, state_json, updated_at) VALUES (?, ?, ?)",
                (state.user_id, json.dumps(asdict(state)), state.updated_at),
            )
            await db.commit()

    async def load(self, user_id: int) -> Optional[LoopState]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT state_json FROM loops WHERE user_id = ?", (user_id,)
            ) as cur:
                row = await cur.fetchone()
                if row:
                    return LoopState(**json.loads(row[0]))
        return None

    async def delete(self, user_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM loops WHERE user_id = ?", (user_id,))
            await db.commit()

    async def list_running(self) -> list[LoopState]:
        await self._init_db()
        states = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT state_json FROM loops WHERE state_json LIKE '%\"running\"%'"
            ) as cur:
                async for row in cur:
                    states.append(LoopState(**json.loads(row[0])))
        return states

    async def run(
        self,
        state: LoopState,
        step_fn: Callable[[str, LoopState], Coroutine[Any, Any, tuple[str, float]]],
        notify_fn: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
    ) -> LoopState:
        """
        Execute the loop. step_fn(goal, state) -> (result_text, cost_this_step).
        notify_fn(message) sends a Telegram update to the user.
        Persists state after every iteration so restarts can resume.
        """
        await self.save(state)

        while (
            state.status == "running"
            and state.iteration < state.max_iterations
            and state.cost_so_far < state.cost_ceiling
        ):
            state.iteration += 1
            logger.info(
                "Loop user=%d iter=%d/%d cost=%.4f",
                state.user_id, state.iteration, state.max_iterations, state.cost_so_far,
            )

            try:
                result_text, step_cost = await step_fn(state.goal, state)
                state.cost_so_far += step_cost
                state.result_summary = result_text
            except asyncio.CancelledError:
                state.status = "paused"
                await self.save(state)
                if notify_fn:
                    await notify_fn("⏸ Loop paused (CancelledError). Use /loop_resume to continue.")
                return state
            except Exception as e:
                state.status = "failed"
                state.result_summary = str(e)
                await self.save(state)
                if notify_fn:
                    await notify_fn(f"❌ Loop failed at iteration {state.iteration}: {e}")
                return state

            # Persist after every step
            await self.save(state)

            # Notify every 5 iterations
            if notify_fn and state.iteration % 5 == 0:
                await notify_fn(
                    f"🔄 Loop progress: iter {state.iteration}/{state.max_iterations} "
                    f"| cost ${state.cost_so_far:.4f}/${state.cost_ceiling:.2f}"
                )

            # Small yield to avoid blocking event loop
            await asyncio.sleep(0.1)

        state.status = "done"
        await self.save(state)

        if notify_fn:
            await notify_fn(
                f"✅ Loop complete!\n"
                f"Iterations: {state.iteration} | Cost: ${state.cost_so_far:.4f}\n"
                f"Result: {state.result_summary[:500]}"
            )

        return state
