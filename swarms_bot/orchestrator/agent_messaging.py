"""Inter-agent structured messaging protocol.

Agents pass typed AgentMessage objects between each other instead of
plain strings. This enables downstream agents to consume structured
outputs: e.g. CodeAgent passes an AST + file list → ReviewAgent reads
that structure directly instead of re-parsing raw text.

Message bus is in-memory (per-orchestration-run) with optional
SQLite persistence for cross-restart recovery.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageType(Enum):
    TASK_RESULT    = "task_result"       # agent completed a task
    TOOL_OUTPUT    = "tool_output"       # agent ran a tool (shell, scrape, etc.)
    CODE_ARTIFACT  = "code_artifact"     # agent produced code
    PLAN           = "plan"              # planner produced a plan
    QUESTION       = "question"          # agent needs clarification
    APPROVAL_REQ   = "approval_req"      # agent needs human approval
    STATUS_UPDATE  = "status_update"     # progress notification
    ERROR          = "error"             # agent encountered an error
    FINAL_RESULT   = "final_result"      # orchestration complete


@dataclass
class AgentMessage:
    """Typed message passed between agents."""
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = ""                     # agent name or "user"
    recipient: str = ""                  # agent name or "broadcast"
    msg_type: MessageType = MessageType.TASK_RESULT
    content: str = ""                    # human-readable content
    payload: Dict[str, Any] = field(default_factory=dict)  # structured data
    timestamp: float = field(default_factory=time.time)
    run_id: str = ""                     # orchestration run ID
    parent_msg_id: Optional[str] = None  # for threaded conversations

    def to_context_str(self) -> str:
        """Compact string for injecting into LLM context."""
        return (
            f"[{self.msg_type.value} from {self.sender}]\n"
            f"{self.content}\n"
            f"{json.dumps(self.payload, indent=2) if self.payload else ''}"
        ).strip()


class AgentMessageBus:
    """In-memory pub/sub message bus for inter-agent communication.

    Each orchestration run gets an isolated message bus.
    Agents subscribe to message types; the orchestrator broadcasts results.
    """

    def __init__(self, run_id: str = "", persist_path: Optional[str] = None):
        self.run_id = run_id or uuid.uuid4().hex[:8]
        self._messages: List[AgentMessage] = []
        self._queues: Dict[str, asyncio.Queue] = {}  # recipient -> queue
        self._persist_path = persist_path
        self._lock = asyncio.Lock()

    async def publish(
        self,
        sender: str,
        msg_type: MessageType,
        content: str,
        payload: Optional[Dict] = None,
        recipient: str = "broadcast",
        parent_msg_id: Optional[str] = None,
    ) -> AgentMessage:
        """Publish a message to the bus."""
        msg = AgentMessage(
            sender=sender,
            recipient=recipient,
            msg_type=msg_type,
            content=content,
            payload=payload or {},
            run_id=self.run_id,
            parent_msg_id=parent_msg_id,
        )
        async with self._lock:
            self._messages.append(msg)
            # Route to recipient queue
            if recipient == "broadcast":
                for q in self._queues.values():
                    await q.put(msg)
            elif recipient in self._queues:
                await self._queues[recipient].put(msg)

        if self._persist_path:
            await self._persist(msg)

        logger.debug("Bus [%s]: %s → %s: %s", self.run_id, sender, recipient, content[:60])
        return msg

    def subscribe(self, agent_name: str) -> asyncio.Queue:
        """Subscribe an agent to receive messages."""
        if agent_name not in self._queues:
            self._queues[agent_name] = asyncio.Queue()
        return self._queues[agent_name]

    async def get_messages(
        self,
        sender: Optional[str] = None,
        msg_type: Optional[MessageType] = None,
        recipient: Optional[str] = None,
    ) -> List[AgentMessage]:
        """Query messages by filters."""
        async with self._lock:
            results = self._messages
            if sender:
                results = [m for m in results if m.sender == sender]
            if msg_type:
                results = [m for m in results if m.msg_type == msg_type]
            if recipient:
                results = [m for m in results if m.recipient in (recipient, "broadcast")]
            return list(results)

    def get_context_for_agent(self, agent_name: str, limit: int = 5) -> str:
        """Return recent messages as LLM-injectable context string."""
        relevant = [
            m for m in self._messages
            if m.recipient in (agent_name, "broadcast")
            and m.sender != agent_name
        ][-limit:]
        if not relevant:
            return ""
        return "\n\n".join(m.to_context_str() for m in relevant)

    async def _persist(self, msg: AgentMessage) -> None:
        try:
            import aiosqlite
            Path(self._persist_path).parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self._persist_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        msg_id TEXT PRIMARY KEY,
                        run_id TEXT,
                        sender TEXT,
                        recipient TEXT,
                        msg_type TEXT,
                        content TEXT,
                        payload_json TEXT,
                        timestamp REAL
                    )
                """)
                await db.execute(
                    "INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?,?,?)",
                    (
                        msg.msg_id, msg.run_id, msg.sender, msg.recipient,
                        msg.msg_type.value, msg.content,
                        json.dumps(msg.payload), msg.timestamp,
                    )
                )
                await db.commit()
        except Exception as e:
            logger.warning("Message persist failed: %s", e)

    @property
    def message_count(self) -> int:
        return len(self._messages)
