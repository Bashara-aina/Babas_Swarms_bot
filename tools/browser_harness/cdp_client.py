"""CDP WebSocket client using the `websockets` library.

Replaces cdp-use's CDPClient. Uses Python's websockets (15.x) which correctly
handles Chrome's origin requirements for CDP connections.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Optional

import websockets


class CDPClient:
    def __init__(self, ws_url: str) -> None:
        self.ws_url = ws_url
        self._ws: Optional[Any] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._pending: dict[int, asyncio.Future] = {}
        self._event_callback: Optional[Callable[[str, dict, Optional[str]], None]] = None
        self._next_id = 1
        self._lock: Optional[asyncio.Lock] = None

    async def start(self, timeout: float = 10.0) -> None:
        self._lock = asyncio.Lock()
        try:
            self._ws = await asyncio.wait_for(
                websockets.connect(self.ws_url, ping_interval=None, origin=None), timeout=timeout
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"CDP WS connection timed out after {timeout}s to {self.ws_url}")
        self._reader_task = asyncio.create_task(self._read_loop())

    async def _read_loop(self) -> None:
        while True:
            try:
                msg = await self._ws.recv()
            except Exception:
                break
            try:
                data = json.loads(msg)
            except Exception:
                continue
            msg_id = data.get("id")
            if msg_id is not None and msg_id in self._pending:
                fut = self._pending.pop(msg_id)
                if not fut.done():
                    fut.set_result(data)
            elif "method" in data:
                if self._event_callback:
                    session_id = data.get("sessionId")
                    self._event_callback(data["method"], data.get("params") or {}, session_id)

    async def send_raw(
        self,
        method: str,
        params: Optional[dict] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        if self._lock is None:
            self._lock = asyncio.Lock()
        await self._lock.acquire()
        try:
            msg_id = self._next_id
            self._next_id += 1
            payload: dict[str, Any] = {"id": msg_id, "method": method}
            if params:
                payload["params"] = params
            if session_id:
                payload["sessionId"] = session_id
            await self._ws.send(json.dumps(payload))
            fut: asyncio.Future = asyncio.get_event_loop().create_future()
            self._pending[msg_id] = fut
            try:
                result = await asyncio.wait_for(fut, timeout=30)
                if isinstance(result, dict) and "result" in result:
                    return result["result"]
                return result
            except asyncio.TimeoutError:
                self._pending.pop(msg_id, None)
                raise RuntimeError(f"CDP timeout: {method}")
        finally:
            self._lock.release()

    def set_event_callback(
        self,
        cb: Callable[[str, dict, Optional[str]], None],
    ) -> None:
        self._event_callback = cb

    async def close(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
