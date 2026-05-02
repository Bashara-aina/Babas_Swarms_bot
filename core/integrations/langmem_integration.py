"""core/integrations/langmem_integration.py — langmem long-term memory for LangGraph.

langmem provides profile extraction, episodic recall, and semantic compression
that complement mem0's semantic memory search.

langmem integrates with LangGraph's BaseStore (the modern checkpoint/memory store)
and uses any LangChain-compatible chat model — including MiniMax via litellm.

Pipeline position: mem0 (semantic search) + langmem (profile extraction + episodic)
Architecture:
    SwarmBot → MemoryManager (langmem) → LangGraph store → agent context

Usage:
    from core.integrations.langmem_integration import SwarmBotMemoryManager, get_langmem_searcher

    manager = SwarmBotMemoryManager()
    searcher = get_langmem_searcher()

    # In a LangGraph agent: extract memories from conversation
    memories = await manager.extract_memories(user_id, messages)

    # Search memories for context
    results = await searcher.ainvoke({"messages": [(user, query)]})
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypedDict

logger = logging.getLogger(__name__)

LANGMEM_AVAILABLE = True

try:
    import langmem
except ImportError:
    LANGMEM_AVAILABLE = False
    langmem = None  # type: ignore

DEFAULT_MODEL = "minimax/MiniMax-M2.7"


class MemoryState(TypedDict, total=False):
    messages: list[dict]
    user_id: str


class ExtractedMemory(TypedDict, total=False):
    content: str
    type: str
    confidence: float


class SearchItem(TypedDict, total=False):
    content: str
    relevance: float


def _build_langmem_llm(model: str | None = None) -> Any:
    """Build a LangChain ChatOpenAI-compatible LLM for langmem.

    langmem requires a LangChain chat model. We use langchain_openai's ChatOpenAI
    with MiniMax's OpenAI-compatible endpoint.
    """
    from langchain_openai import ChatOpenAI

    model_name = model or DEFAULT_MODEL
    if "/" in model_name:
        model_name = "gpt-4o-mini"

    api_key = os.getenv("MINIMAX_API_KEY", "dummy")
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = "https://api.minimax.io/v1"

    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        base_url="https://api.minimax.io/v1",
        temperature=0.1,
        timeout=60.0,
    )


class SwarmBotMemoryManager:
    """langmem-based memory manager for SwarmBot.

    Provides profile extraction and episodic recall via langmem's memory manager.
    Complements mem0's semantic search with structured memory consolidation.
    """

    def __init__(
        self,
        model: str | None = None,
        namespace: tuple[str, ...] | None = None,
    ) -> None:
        self.model = model or DEFAULT_MODEL
        self.namespace = namespace or ("swarmbot", "memories")
        self._manager = None
        self._searcher = None

    def _get_manager(self) -> Any:
        """Lazily build the langmem memory manager."""
        if not LANGMEM_AVAILABLE:
            raise ImportError("langmem not installed — pip install langmem")

        if self._manager is None:
            llm = _build_langmem_llm(self.model)
            self._manager = langmem.create_memory_store_manager(
                llm,
                namespace=self.namespace,
                instructions=(
                    "You are a long-term memory manager for SwarmBot. "
                    "Extract facts about user preferences, agent capabilities, "
                    "conversation context, and procedural knowledge. "
                    "Store memories with confidence levels and reasoning."
                ),
                enable_inserts=True,
                enable_deletes=True,
            )
            logger.info("langmem memory manager initialized: namespace=%s", self.namespace)
        return self._manager

    def _get_searcher(self) -> Any:
        """Lazily build the langmem memory searcher."""
        if not LANGMEM_AVAILABLE:
            raise ImportError("langmem not installed — pip install langmem")

        if self._searcher is None:
            llm = _build_langmem_llm(self.model)
            self._searcher = langmem.create_memory_searcher(
                llm,
                "Search for distinct memories relevant to the user's query. "
                "Return memories ranked by relevance, with confidence scores.",
                namespace=self.namespace,
            )
            logger.info("langmem memory searcher initialized")
        return self._searcher

    async def extract_memories(
        self,
        messages: list[dict[str, Any]],
    ) -> list[ExtractedMemory]:
        """Extract structured memories from a conversation trajectory.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            List of ExtractedMemory dicts with content, type, confidence
        """
        if not LANGMEM_AVAILABLE:
            return []

        try:
            manager = self._get_manager()
            state: MemoryState = {"messages": messages, "user_id": ""}
            result = await manager.ainvoke(state)
            memories = []
            for item in result:
                if isinstance(item, dict):
                    memories.append(ExtractedMemory(
                        content=item.get("content", str(item)),
                        type=item.get("type", "unknown"),
                        confidence=item.get("confidence", 0.5),
                    ))
                else:
                    memories.append(ExtractedMemory(
                        content=str(item),
                        type="unknown",
                        confidence=0.5,
                    ))
            return memories
        except Exception as exc:
            logger.warning("langmem extract_memories failed: %s", exc)
            return []

    async def search_memories(
        self,
        query: str,
        messages: list[dict[str, Any]] | None = None,
    ) -> list[SearchItem]:
        """Search memories for context relevant to a query.

        Args:
            query: Search query string
            messages: Optional conversation context for disambiguation

        Returns:
            List of SearchItem dicts with content and relevance
        """
        if not LANGMEM_AVAILABLE:
            return []

        try:
            searcher = self._get_searcher()
            search_messages = messages or [("user", query)]
            state: MemoryState = {"messages": search_messages, "user_id": ""}
            result = await searcher.ainvoke(state)
            items = []
            for item in result:
                if isinstance(item, dict):
                    items.append(SearchItem(
                        content=item.get("content", str(item)),
                        relevance=item.get("relevance", 0.5),
                    ))
                else:
                    items.append(SearchItem(content=str(item), relevance=0.5))
            return items
        except Exception as exc:
            logger.warning("langmem search_memories failed: %s", exc)
            return []


def get_langmem_searcher(namespace: tuple[str, ...] | None = None) -> Any | None:
    """Get a standalone langmem memory searcher for use as a LangGraph tool."""
    if not LANGMEM_AVAILABLE:
        return None

    ns = namespace or ("swarmbot", "memories")
    llm = _build_langmem_llm()
    return langmem.create_memory_searcher(model=llm, namespace=ns)


def get_langmem_manager(namespace: tuple[str, ...] | None = None) -> Any | None:
    """Get a standalone langmem memory manager for use as a LangGraph node."""
    if not LANGMEM_AVAILABLE:
        return None

    llm = _build_langmem_llm()
    return langmem.create_memory_manager(llm, enable_inserts=True, enable_updates=True, enable_deletes=False)


def create_manage_memory_tool(namespace: tuple[str, ...] | str = ("swarmbot", "memories")) -> Any | None:
    """Create a LangGraph-compatible manage_memory tool from langmem.

    This tool can be injected into a LangGraph agent to allow it to
    proactively manage its own memory during conversations.
    """
    if not LANGMEM_AVAILABLE:
        return None

    return langmem.create_manage_memory_tool(
        namespace=namespace if isinstance(namespace, str) else namespace,
        instructions=(
            "Proactively call this tool when you:\n"
            "1. Identify a new USER preference or fact\n"
            "2. Receive an explicit USER request to remember something\n"
            "3. Are working and want to record important context\n"
            "4. Identify that an existing MEMORY is incorrect or outdated\n"
        ),
        actions_permitted=("create", "update", "delete"),
    )


async def wrap_langmem_context(
    query: str,
    messages: list[dict[str, Any]],
    memories: list[dict[str, Any]],
    max_chars: int = 3000,
) -> str:
    """Build a context string from langmem memories + current messages.

    Args:
        query: Current user query
        messages: Current conversation messages
        memories: Memories retrieved from langmem search
        max_chars: Maximum characters to include

    Returns:
        Formatted context string for LLM prompt injection
    """
    if not memories and not messages:
        return ""

    lines = ["[Memory context from langmem:]"]
    total = 0
    for item in memories[:5]:
        content = item.get("content", "") or str(item)
        relevance = item.get("relevance", 0.5)
        line = f"- (relevance {relevance:.2f}) {content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)

    lines.append("\n[Current conversation:]")
    for msg in messages[-5:]:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:200]
        lines.append(f"{role}: {content}")
        total += len(content)
        if total > max_chars:
            break

    lines.append("[End of context]")
    return "\n".join(lines)
