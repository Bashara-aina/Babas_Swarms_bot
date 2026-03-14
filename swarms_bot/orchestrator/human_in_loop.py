"""Human-in-the-loop approval system.

Before executing a complex plan, Legion sends the decomposed DAG plan
to the user and waits for explicit approval via Telegram inline buttons.
If the user rejects or modifies, the plan is updated before execution.

Also handles:
- Mid-execution clarification requests from agents
- Agent pause/resume/cancel controls
- Approval timeout (auto-approve after N seconds if configured)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class HumanApprovalGate:
    """Manages approval flow between the orchestrator and the Telegram user.

    Usage:
        gate = HumanApprovalGate(send_fn=msg.answer, timeout_seconds=120)
        approved = await gate.request_plan_approval(dag.to_text_plan())
        if not approved:
            return  # user rejected
    """

    def __init__(
        self,
        send_fn: Callable[[str, Any], Coroutine],  # async fn(text, reply_markup) -> Message
        timeout_seconds: int = 120,
        auto_approve: bool = False,
    ):
        self.send_fn = send_fn
        self.timeout_seconds = timeout_seconds
        self.auto_approve = auto_approve
        self._pending: dict[str, asyncio.Future] = {}

    async def request_plan_approval(
        self,
        plan_text: str,
        run_id: str = "run",
    ) -> bool:
        """Send plan to user, return True if approved."""
        if self.auto_approve:
            logger.info("Auto-approving plan for run %s", run_id)
            return True

        try:
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
            markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="✅ Approve & Execute",
                    callback_data=f"plan_approve:{run_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data=f"plan_reject:{run_id}"
                ),
            ]])
        except ImportError:
            markup = None

        await self.send_fn(
            f"{plan_text}\n\n"
            f"⏱ Auto-{'approving' if self.auto_approve else 'cancelling'} "
            f"in {self.timeout_seconds}s if no response.",
            markup,
        )

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[run_id] = future

        try:
            return await asyncio.wait_for(future, timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            logger.info("Approval timeout for run %s — auto-cancelling", run_id)
            self._pending.pop(run_id, None)
            return False

    def resolve(self, run_id: str, approved: bool) -> None:
        """Call this from the callback handler when user taps Approve/Cancel."""
        future = self._pending.pop(run_id, None)
        if future and not future.done():
            future.set_result(approved)

    async def request_clarification(
        self,
        question: str,
        run_id: str = "run",
    ) -> str:
        """Ask user a clarification question, return their text reply."""
        if self.auto_approve:
            return "proceed"

        await self.send_fn(
            f"🤔 <b>Agent needs clarification:</b>\n{question}\n\n"
            f"Reply in chat to continue (timeout: {self.timeout_seconds}s).",
            None,
        )

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[f"clarify:{run_id}"] = future

        try:
            return await asyncio.wait_for(future, timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            return "proceed"  # best-effort default

    def resolve_clarification(self, run_id: str, answer: str) -> None:
        """Call from message handler when user replies to a clarification."""
        key = f"clarify:{run_id}"
        future = self._pending.pop(key, None)
        if future and not future.done():
            future.set_result(answer)
