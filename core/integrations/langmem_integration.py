"""core/integrations/langmem_integration.py — langmem long-term memory for LangGraph.  # type: ignore[reportOptionalMemberAccess]

langmem provides profile extraction, episodic recall, and semantic compression  # type: ignore[reportOptionalMemberAccess]
that complement mem0's semantic memory search.  # type: ignore[reportOptionalMemberAccess]

langmem integrates with LangGraph's BaseStore (the modern checkpoint/memory store)  # type: ignore[reportOptionalMemberAccess]
and uses any LangChain-compatible chat model — including MiniMax via litellm.  # type: ignore[reportOptionalMemberAccess]

Pipeline position: mem0 (semantic search) + langmem (profile extraction + episodic)  # type: ignore[reportOptionalMemberAccess]
Architecture:
    SwarmBot → MemoryManager (langmem) → LangGraph store → agent context  # type: ignore[reportOptionalMemberAccess]

Usage:
    from core.integrations.langmem_integration import SwarmBotMemoryManager, get_langmem_searcher  # type: ignore[reportOptionalMemberAccess]

    manager = SwarmBotMemoryManager()  # type: ignore[reportOptionalMemberAccess]
    searcher = get_langmem_searcher()  # type: ignore[reportOptionalMemberAccess]

    # In a LangGraph agent: extract memories from conversation
    memories = await manager.extract_memories(user_id, messages)  # type: ignore[reportOptionalMemberAccess]

    # Search memories for context
    results = await searcher.ainvoke({"messages": [(user, query)]})  # type: ignore[reportOptionalMemberAccess]
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypedDict  # type: ignore[reportOptionalMemberAccess]

logger = logging.getLogger(__name__)  # type: ignore[reportOptionalMemberAccess]

LANGMEM_AVAILABLE = True  # type: ignore[reportOptionalMemberAccess]

try:
    import langmem
except ImportError:
    LANGMEM_AVAILABLE = False  # type: ignore[reportOptionalMemberAccess]
    langmem = None  # type: ignore

DEFAULT_MODEL = "minimax/MiniMax-M2.7"  # type: ignore[reportOptionalMemberAccess]


class MemoryState(TypedDict, total=False):  # type: ignore[reportOptionalMemberAccess]
    messages: list[dict]
    user_id: str


class ExtractedMemory(TypedDict, total=False):  # type: ignore[reportOptionalMemberAccess]
    content: str
    type: str
    confidence: float


class SearchItem(TypedDict, total=False):  # type: ignore[reportOptionalMemberAccess]
    content: str
    relevance: float


def _build_langmem_llm(model: str | None = None) -> Any:  # type: ignore[reportOptionalMemberAccess]
    """Build a LangChain ChatOpenAI-compatible LLM for langmem.  # type: ignore[reportOptionalMemberAccess]

    langmem requires a LangChain chat model. We use langchain_openai's ChatOpenAI  # type: ignore[reportOptionalMemberAccess]
    with MiniMax's OpenAI-compatible endpoint.  # type: ignore[reportOptionalMemberAccess]
    """
    from langchain_openai import ChatOpenAI

    model_name = model or DEFAULT_MODEL  # type: ignore[reportOptionalMemberAccess]
    if "/" in model_name:
        model_name = "gpt-4o-mini"  # type: ignore[reportOptionalMemberAccess]

    api_key = os.getenv("MINIMAX_API_KEY", "dummy")  # type: ignore[reportOptionalMemberAccess]
    os.environ["OPENAI_API_KEY"] = api_key  # type: ignore[reportOptionalMemberAccess]
    os.environ["OPENAI_BASE_URL"] = "https://api.minimax.io/v1"  # type: ignore[reportOptionalMemberAccess]

    return ChatOpenAI(  # type: ignore[reportOptionalMemberAccess]
        model=model_name,  # type: ignore[reportOptionalMemberAccess]
        openai_api_key=api_key,  # type: ignore[reportOptionalMemberAccess]
        base_url="https://api.minimax.io/v1",  # type: ignore[reportOptionalMemberAccess]
        temperature=0.1,  # type: ignore[reportOptionalMemberAccess]
        timeout=60.0,  # type: ignore[reportOptionalMemberAccess]
    )


class SwarmBotMemoryManager:
    """langmem-based memory manager for SwarmBot.  # type: ignore[reportOptionalMemberAccess]

    Provides profile extraction and episodic recall via langmem's memory manager.  # type: ignore[reportOptionalMemberAccess]
    Complements mem0's semantic search with structured memory consolidation.  # type: ignore[reportOptionalMemberAccess]
    """

    def __init__(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        model: str | None = None,  # type: ignore[reportOptionalMemberAccess]
        namespace: tuple[str, ...] | None = None,  # type: ignore[reportOptionalMemberAccess]
    ) -> None:
        self.model = model or DEFAULT_MODEL  # type: ignore[reportOptionalMemberAccess]
        self.namespace = namespace or ("swarmbot", "memories")  # type: ignore[reportOptionalMemberAccess]
        self._manager = None  # type: ignore[reportOptionalMemberAccess]
        self._searcher = None  # type: ignore[reportOptionalMemberAccess]

    def _get_manager(self) -> Any:  # type: ignore[reportOptionalMemberAccess]
        """Lazily build the langmem memory manager."""  # type: ignore[reportOptionalMemberAccess]
        if not LANGMEM_AVAILABLE:
            raise ImportError("langmem not installed — pip install langmem")  # type: ignore[reportOptionalMemberAccess]

        if self._manager is None:  # type: ignore[reportOptionalMemberAccess]
            llm = _build_langmem_llm(self.model)  # type: ignore[reportOptionalMemberAccess]
            self._manager = langmem.create_memory_manager(  # type: ignore[reportOptionalMemberAccess]
                llm,  # type: ignore[reportOptionalMemberAccess]
                enable_inserts=True,  # type: ignore[reportOptionalMemberAccess]
                enable_updates=True,  # type: ignore[reportOptionalMemberAccess]
                enable_deletes=False,  # type: ignore[reportOptionalMemberAccess]
            )
            logger.info("langmem memory manager initialized: namespace=%s", self.namespace)  # type: ignore[reportOptionalMemberAccess]
        return self._manager  # type: ignore[reportOptionalMemberAccess]

    def _get_searcher(self) -> Any:  # type: ignore[reportOptionalMemberAccess]
        """Lazily build the langmem memory searcher."""  # type: ignore[reportOptionalMemberAccess]
        if not LANGMEM_AVAILABLE:
            raise ImportError("langmem not installed — pip install langmem")  # type: ignore[reportOptionalMemberAccess]

        if self._searcher is None:  # type: ignore[reportOptionalMemberAccess]
            llm = _build_langmem_llm(self.model)  # type: ignore[reportOptionalMemberAccess]
            self._searcher = langmem.create_memory_searcher(  # type: ignore[reportOptionalMemberAccess]
                llm,  # type: ignore[reportOptionalMemberAccess]
                "Search for distinct memories relevant to the user's query. "  # type: ignore[reportOptionalMemberAccess]
                "Return memories ranked by relevance, with confidence scores.",  # type: ignore[reportOptionalMemberAccess]
                namespace=self.namespace,  # type: ignore[reportOptionalMemberAccess]
            )
            logger.info("langmem memory searcher initialized")  # type: ignore[reportOptionalMemberAccess]
        return self._searcher  # type: ignore[reportOptionalMemberAccess]

    async def extract_memories(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        messages: list[dict[str, Any]],  # type: ignore[reportOptionalMemberAccess]
    ) -> list[ExtractedMemory]:
        """Extract structured memories from a conversation trajectory.  # type: ignore[reportOptionalMemberAccess]

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            List of ExtractedMemory dicts with content, type, confidence  # type: ignore[reportOptionalMemberAccess]
        """
        if not LANGMEM_AVAILABLE:
            return []

        try:
            manager = self._get_manager()  # type: ignore[reportOptionalMemberAccess]
            state: MemoryState = {"messages": messages, "user_id": ""}  # type: ignore[reportOptionalMemberAccess]
            result = await manager.ainvoke(state)  # type: ignore[reportOptionalMemberAccess]
            memories = []  # type: ignore[reportOptionalMemberAccess]
            for item in result:
                if isinstance(item, dict):  # type: ignore[reportOptionalMemberAccess]
                    memories.append(ExtractedMemory(  # type: ignore[reportOptionalMemberAccess]
                        content=item.get("content", str(item)),  # type: ignore[reportOptionalMemberAccess]
                        type=item.get("type", "unknown"),  # type: ignore[reportOptionalMemberAccess]
                        confidence=item.get("confidence", 0.5),  # type: ignore[reportOptionalMemberAccess]
                    ))
                else:
                    memories.append(ExtractedMemory(  # type: ignore[reportOptionalMemberAccess]
                        content=str(item),  # type: ignore[reportOptionalMemberAccess]
                        type="unknown",  # type: ignore[reportOptionalMemberAccess]
                        confidence=0.5,  # type: ignore[reportOptionalMemberAccess]
                    ))
            return memories
        except Exception as exc:
            logger.warning("langmem extract_memories failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
            return []

    async def search_memories(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        query: str,  # type: ignore[reportOptionalMemberAccess]
        messages: list[dict[str, Any]] | None = None,  # type: ignore[reportOptionalMemberAccess]
    ) -> list[SearchItem]:
        """Search memories for context relevant to a query.  # type: ignore[reportOptionalMemberAccess]

        Args:
            query: Search query string
            messages: Optional conversation context for disambiguation

        Returns:
            List of SearchItem dicts with content and relevance
        """
        if not LANGMEM_AVAILABLE:
            return []

        try:
            searcher = self._get_searcher()  # type: ignore[reportOptionalMemberAccess]
            search_messages = messages or [("user", query)]  # type: ignore[reportOptionalMemberAccess]
            state: MemoryState = {"messages": search_messages, "user_id": ""}  # type: ignore[reportOptionalMemberAccess]
            result = await searcher.ainvoke(state)  # type: ignore[reportOptionalMemberAccess]
            items = []  # type: ignore[reportOptionalMemberAccess]
            for item in result:
                if isinstance(item, dict):  # type: ignore[reportOptionalMemberAccess]
                    items.append(SearchItem(  # type: ignore[reportOptionalMemberAccess]
                        content=item.get("content", str(item)),  # type: ignore[reportOptionalMemberAccess]
                        relevance=item.get("relevance", 0.5),  # type: ignore[reportOptionalMemberAccess]
                    ))
                else:
                    items.append(SearchItem(content=str(item), relevance=0.5))  # type: ignore[reportOptionalMemberAccess]
            return items
        except Exception as exc:
            logger.warning("langmem search_memories failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
            return []


def get_langmem_searcher(namespace: tuple[str, ...] | None = None) -> Any | None:  # type: ignore[reportOptionalMemberAccess]
    """Get a standalone langmem memory searcher for use as a LangGraph tool."""  # type: ignore[reportOptionalMemberAccess]
    if not LANGMEM_AVAILABLE:
        return None

    ns = namespace or ("swarmbot", "memories")  # type: ignore[reportOptionalMemberAccess]
    llm = _build_langmem_llm()  # type: ignore[reportOptionalMemberAccess]
    return langmem.create_memory_searcher(model=llm, namespace=ns)  # type: ignore[reportOptionalMemberAccess]


def get_langmem_manager(namespace: tuple[str, ...] | None = None) -> Any | None:  # type: ignore[reportOptionalMemberAccess]
    """Get a standalone langmem memory manager for use as a LangGraph node."""  # type: ignore[reportOptionalMemberAccess]
    if not LANGMEM_AVAILABLE:
        return None

    llm = _build_langmem_llm()  # type: ignore[reportOptionalMemberAccess]
    return langmem.create_memory_manager(llm, enable_inserts=True, enable_updates=True, enable_deletes=False)  # type: ignore[reportOptionalMemberAccess]


def create_manage_memory_tool(namespace: tuple[str, ...] | str = ("swarmbot", "memories")) -> Any | None:  # type: ignore[reportOptionalMemberAccess]
    """Create a LangGraph-compatible manage_memory tool from langmem.  # type: ignore[reportOptionalMemberAccess]

    This tool can be injected into a LangGraph agent to allow it to
    proactively manage its own memory during conversations.  # type: ignore[reportOptionalMemberAccess]
    """
    if not LANGMEM_AVAILABLE:
        return None

    return langmem.create_manage_memory_tool(  # type: ignore[reportOptionalMemberAccess]
        namespace=namespace if isinstance(namespace, str) else namespace,  # type: ignore[reportOptionalMemberAccess]
        instructions=(  # type: ignore[reportOptionalMemberAccess]
            "Proactively call this tool when you:\n"
            "1. Identify a new USER preference or fact\n"  # type: ignore[reportOptionalMemberAccess]
            "2. Receive an explicit USER request to remember something\n"  # type: ignore[reportOptionalMemberAccess]
            "3. Are working and want to record important context\n"  # type: ignore[reportOptionalMemberAccess]
            "4. Identify that an existing MEMORY is incorrect or outdated\n"  # type: ignore[reportOptionalMemberAccess]
        ),  # type: ignore[reportOptionalMemberAccess]
        actions_permitted=("create", "update", "delete"),  # type: ignore[reportOptionalMemberAccess]
    )


async def wrap_langmem_context(  # type: ignore[reportOptionalMemberAccess]
    query: str,  # type: ignore[reportOptionalMemberAccess]
    messages: list[dict[str, Any]],  # type: ignore[reportOptionalMemberAccess]
    memories: list[dict[str, Any]],  # type: ignore[reportOptionalMemberAccess]
    max_chars: int = 3000,  # type: ignore[reportOptionalMemberAccess]
) -> str:
    """Build a context string from langmem memories + current messages.  # type: ignore[reportOptionalMemberAccess]

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

    lines = ["[Memory context from langmem:]"]  # type: ignore[reportOptionalMemberAccess]
    total = 0  # type: ignore[reportOptionalMemberAccess]
    for item in memories[:5]:
        content = item.get("content", "") or str(item)  # type: ignore[reportOptionalMemberAccess]
        relevance = item.get("relevance", 0.5)  # type: ignore[reportOptionalMemberAccess]
        line = f"- (relevance {relevance:.2f}) {content}"  # type: ignore[reportOptionalMemberAccess]
        if total + len(line) > max_chars:  # type: ignore[reportOptionalMemberAccess]
            break
        lines.append(line)  # type: ignore[reportOptionalMemberAccess]
        total += len(line)  # type: ignore[reportOptionalMemberAccess]

    lines.append("\n[Current conversation:]")  # type: ignore[reportOptionalMemberAccess]
    for msg in messages[-5:]:
        role = msg.get("role", "unknown")  # type: ignore[reportOptionalMemberAccess]
        content = msg.get("content", "")[:200]  # type: ignore[reportOptionalMemberAccess]
        lines.append(f"{role}: {content}")  # type: ignore[reportOptionalMemberAccess]
        total += len(content)  # type: ignore[reportOptionalMemberAccess]
        if total > max_chars:
            break

    lines.append("[End of context]")  # type: ignore[reportOptionalMemberAccess]
    return "\n".join(lines)  # type: ignore[reportOptionalMemberAccess]
