"""core/memory/bridges/_base.py — Bridge protocol + per-bridge idempotency state."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import aiosqlite

logger = logging.getLogger(__name__)

STATE_DB = Path(__file__).parent.parent.parent.parent / "data" / "bridges_state.db"
STATE_DB.parent.mkdir(parents=True, exist_ok=True)


class ObservationBridge(Protocol):
    """Contract every bridge implements."""

    name: str

    async def push(self, obs_id: int, obs_payload: dict[str, Any]) -> None:
        """Push a single observation. Idempotent — safe to retry."""
        ...

    async def health(self) -> dict[str, Any]:
        """Return a dict describing bridge health (for verify-memory-pipeline)."""
        ...


@dataclass
class BridgeState:
    """Per-bridge idempotency state, persisted in `data/bridges_state.db`."""

    name: str
    last_pushed_id: int = 0

    async def _conn(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(str(STATE_DB))
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bridge_state (
                bridge_name TEXT PRIMARY KEY,
                last_pushed_id INTEGER NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL
            )
            """
        )
        await conn.commit()
        return conn

    async def load(self) -> None:
        conn = await self._conn()
        try:
            cur = await conn.execute(
                "SELECT last_pushed_id FROM bridge_state WHERE bridge_name = ?", (self.name,)
            )
            row = await cur.fetchone()
            self.last_pushed_id = int(row[0]) if row else 0
        finally:
            await conn.close()

    async def advance_to(self, obs_id: int) -> None:
        if obs_id <= self.last_pushed_id:
            return
        conn = await self._conn()
        try:
            await conn.execute(
                """INSERT INTO bridge_state (bridge_name, last_pushed_id, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(bridge_name) DO UPDATE SET
                     last_pushed_id = MAX(last_pushed_id, excluded.last_pushed_id),
                     updated_at = excluded.updated_at""",
                (self.name, obs_id, time.time()),
            )
            await conn.commit()
            self.last_pushed_id = obs_id
        finally:
            await conn.close()


async def init_state(name: str) -> BridgeState:
    s = BridgeState(name=name)
    await s.load()
    return s
