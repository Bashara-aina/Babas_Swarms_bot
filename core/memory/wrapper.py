"""
InfiniteMemoryLLM — transparent drop-in wrapper for any LLM client.

Usage:
    from core.memory.infinite.wrapper import InfiniteMemoryLLM
    client = InfiniteMemoryLLM(SomeClient(api_key=...), agent_id="my-agent")
    response = client.chat(messages)   # memory auto-injected + auto-stored
"""
from __future__ import annotations

import threading
from typing import Any

from .store import MemoryStore

_store = MemoryStore()
_store_lock = threading.Lock()


class InfiniteMemoryLLM:
    """
    Wraps any LLM client to give it infinite persistent memory.

    - Intercepts every .chat() / .complete() / .generate() call
    - Recalls relevant memories, injects into system prompt silently
    - After response, chunks and stores new knowledge automatically
    - Deduplication ensures memory stays clean forever
    - Thread-safe for concurrent Legion agents
    """

    def __init__(
        self,
        base_client: Any,
        agent_id: str = "shared",
        top_k: int = 10,
        min_score: float = 0.25,
        auto_store: bool = True,
        verbose: bool = False,
    ):
        self._client = base_client
        self.agent_id = agent_id
        self.top_k = top_k
        self.min_score = min_score
        self.auto_store = auto_store
        self.verbose = verbose

    def _extract_query(self, messages: list[dict]) -> str:
        """Get the last user message as recall query."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")[:512]
        return ""

    def _inject_memory(
        self,
        system_prompt: str,
        query: str,
    ) -> str:
        """Recall memories and prepend to system prompt."""
        memory_block = _store.recall_formatted(
            query=query,
            agent_id=self.agent_id,
            top_k=self.top_k,
        )
        if not memory_block:
            return system_prompt
        if self.verbose:
            count = len(memory_block.split("\n")) - 2
            print(f"[MEMORY:{self.agent_id}] Injected {count} memories")
        return f"{memory_block}\n\n{system_prompt}"

    def _store_response(self, response: str, session_id: str | None):
        """Non-blocking store of response content."""
        if not self.auto_store or not response or len(response) < 50:
            return

        def _store_async():
            with _store_lock:
                stored = _store.remember(
                    content=response,
                    agent_id=self.agent_id,
                    session_id=session_id,
                    memory_type="episodic",
                )
                if self.verbose and stored:
                    print(f"[MEMORY:{self.agent_id}] Stored {stored} new chunks")

        t = threading.Thread(target=_store_async, daemon=True)
        t.start()

    def chat(
        self,
        messages: list[dict],
        system_prompt: str = "",
        session_id: str | None = None,
        **kwargs,
    ) -> str:
        query = self._extract_query(messages)
        augmented_system = self._inject_memory(system_prompt, query)
        response = self._client.chat(
            messages,
            system_prompt=augmented_system,
            **kwargs,
        )
        self._store_response(str(response), session_id)
        return response

    def complete(self, prompt: str, **kwargs) -> str:
        augmented = self._inject_memory("", prompt[:512])
        if augmented:
            prompt = f"{augmented}\n\n{prompt}"
        response = self._client.complete(prompt, **kwargs)
        self._store_response(str(response), None)
        return response

    async def achat(
        self,
        messages: list[dict],
        system_prompt: str = "",
        session_id: str | None = None,
        **kwargs,
    ) -> str:
        query = self._extract_query(messages)
        augmented_system = self._inject_memory(system_prompt, query)
        response = await self._client.achat(
            messages,
            system_prompt=augmented_system,
            **kwargs,
        )
        self._store_response(str(response), session_id)
        return response

    async def agenerate(self, prompt: str, **kwargs) -> str:
        augmented = self._inject_memory("", prompt[:512])
        if augmented:
            prompt = f"{augmented}\n\n{prompt}"
        response = await self._client.agenerate(prompt, **kwargs)
        self._store_response(str(response), None)
        return response

    def __getattr__(self, name: str) -> Any:
        """Any attribute not defined above is forwarded to base client."""
        return getattr(self._client, name)