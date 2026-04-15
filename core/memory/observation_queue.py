"""core/memory/observation_queue.py — Fire-and-forget async observation queue.

Design goals:
  1. NEVER block the hook — enqueue() must return immediately
  2. Background worker drains queue → observation_store
  3. Session-bound: observations carry session_id for later synthesis
  4. Graceful shutdown: drain remaining items before exit

This mirrors claude-mem's "fire-and-forget HTTP with 2-second timeouts"
but uses an in-process async queue instead (no network hop needed within a single host).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .observation_store import get_observation_store

logger = logging.getLogger(__name__)


@dataclass
class Observation:
    """A single observation captured from a hook."""

    session_id: str
    content: str
    title: str = ""
    type: str | None = None
    subtitle: str = ""
    narrative: str = ""
    facts: str = ""
    concepts: str = ""
    tags: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


class ObservationQueue:
    """Async queue that drains to observation_store in background.

    Hooks call enqueue() and immediately return — zero blocking.
    A background task drains the queue and writes to SQLite.
    """

    MAX_QUEUE_SIZE = 500  # Drop oldest if backed up
    BATCH_SIZE = 10       # Write in batches for efficiency
    FLUSH_INTERVAL = 2.0  # Flush every 2 seconds or when batch is full

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Observation] = asyncio.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self._worker_task: asyncio.Task[None] | None = None
        self._running = False
        self._dropped = 0

    def start(self) -> None:
        """Start the background drain worker. Idempotent."""
        if self._worker_task is not None:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._drain_loop())
        logger.info("[ObservationQueue] Started background drain worker")

    async def stop(self) -> None:
        """Graceful shutdown — drain remaining queue items."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        # Final drain
        await self._flush()
        logger.info("[ObservationQueue] Stopped (%d observations dropped during lifetime)", self._dropped)

    def enqueue(self, obs: Observation) -> bool:
        """Add an observation to the queue. Returns True if accepted, False if dropped."""
        try:
            self._queue.put_nowait(obs)
            return True
        except asyncio.QueueFull:
            # Drop oldest to make room
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(obs)
                self._dropped += 1
                return True
            except Exception:
                self._dropped += 1
                return False

    async def _drain_loop(self) -> None:
        """Background worker: batch observations and flush to store."""
        batch: list[Observation] = []
        last_flush = asyncio.get_event_loop().time()

        while self._running:
            try:
                # Wait for item or timeout
                try:
                    obs = await asyncio.wait_for(self._queue.get(), timeout=self.FLUSH_INTERVAL)
                    batch.append(obs)
                except asyncio.TimeoutError:
                    pass

                now = asyncio.get_event_loop().time()
                elapsed = now - last_flush

                # Flush if batch full or enough time elapsed
                if len(batch) >= self.BATCH_SIZE or (batch and elapsed >= self.FLUSH_INTERVAL):
                    await self._write_batch(batch)
                    batch.clear()
                    last_flush = now

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("[ObservationQueue] Drain loop error")

        # Final flush on shutdown
        if batch:
            await self._write_batch(batch)

    async def _write_batch(self, batch: list[Observation]) -> None:
        """Write a batch of observations to the store."""
        if not batch:
            return
        try:
            store = get_observation_store()
            for obs in batch:
                await store.add_observation(
                    session_id=obs.session_id,
                    content=obs.content,
                    title=obs.title,
                    type_=obs.type,
                    subtitle=obs.subtitle,
                    narrative=obs.narrative,
                    facts=obs.facts,
                    concepts=obs.concepts,
                    tags=obs.tags,
                    files_read=obs.files_read,
                    files_modified=obs.files_modified,
                )
            logger.debug("[ObservationQueue] Flushed %d observations", len(batch))
        except Exception:
            logger.exception("[ObservationQueue] Failed to write batch of %d", len(batch))

    async def _flush(self) -> None:
        """Drain everything remaining in the queue."""
        batch: list[Observation] = []
        while True:
            try:
                obs = self._queue.get_nowait()
                batch.append(obs)
            except asyncio.QueueEmpty:
                break
        if batch:
            await self._write_batch(batch)

    @property
    def pending(self) -> int:
        """Number of observations currently queued."""
        return self._queue.qsize()


# ── Singleton ─────────────────────────────────────────────────────────────────

_queue: ObservationQueue | None = None


def get_observation_queue() -> ObservationQueue:
    global _queue
    if _queue is None:
        _queue = ObservationQueue()
    return _queue
