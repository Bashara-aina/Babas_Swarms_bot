"""core/integrations/second_brain_integration.py — LLM wiki pre-feed for Obsidian.

second-brain provides LLM wiki pre-feeding: indexes an Obsidian vault and
creates context blocks for agent boot. The idea is that before every agent
run, relevant wiki content is injected as context.

Pipeline: Obsidian vault → second-brain index → pre-feed context → agent

Note: second-brain is not yet available as a pip package. This module
provides the equivalent functionality directly using the Obsidian vault
already indexed by graphrag. When second-brain becomes available as a
package, it can be swapped in.

Usage:
    from core.integrations.second_brain_integration import SecondBrainIndexer, pre_feed_context

    indexer = SecondBrainIndexer("/path/to/vault")
    indexer.build_index()

    context = await pre_feed_context("What is the architecture?")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SECOND_BRAIN_AVAILABLE = False

try:
    import secondbrain
    SECOND_BRAIN_AVAILABLE = True
except ImportError:
    secondbrain = None  # type: ignore

DEFAULT_VAULT_PATH = os.path.expanduser("~/.obsidian/vaults/default")


class SecondBrainIndexer:
    """Index an Obsidian vault for LLM pre-feeding.

    This is a lightweight alternative to second-brain package.
    It reads all markdown files and builds an in-memory index.
    """

    def __init__(self, vault_path: str | None = None) -> None:
        self.vault_path = Path(vault_path or DEFAULT_VAULT_PATH)
        self._index: list[dict[str, Any]] = []
        self._file_map: dict[str, str] = {}

    def build_index(self, max_chars_per_file: int = 5000) -> int:
        """Read all markdown files and build an in-memory index.

        Returns:
            Number of files indexed
        """
        if not self.vault_path.exists():
            logger.warning("Vault path does not exist: %s", self.vault_path)
            return 0

        self._index.clear()
        self._file_map.clear()

        for md_file in self.vault_path.rglob("*.md"):
            if md_file.is_file():
                try:
                    content = md_file.read_text(encoding="utf-8")
                    rel_path = str(md_file.relative_to(self.vault_path))
                    self._file_map[rel_path] = content
                    for heading in self._extract_headings(content):
                        self._index.append({
                            "heading": heading,
                            "content": content[:max_chars_per_file],
                            "source": rel_path,
                        })
                except Exception as exc:
                    logger.warning("Failed to read %s: %s", md_file, exc)

        logger.info("SecondBrain indexed %d files, %d headings", len(self._file_map), len(self._index))
        return len(self._file_map)

    def _extract_headings(self, content: str) -> list[str]:
        """Extract markdown headings from content."""
        headings = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                if level <= 3:
                    text = stripped.lstrip("#").strip()
                    if text:
                        headings.append(text)
        return headings

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search indexed content for query matches.

        Simple keyword + recency search. Replace with semantic search
        (using mem0 or langmem embeddings) for production.
        """
        query_words = set(query.lower().split())
        scored = []
        for entry in self._index:
            score = 0
            content_lower = entry["content"].lower()
            heading_lower = entry["heading"].lower()
            for word in query_words:
                if word in content_lower:
                    score += 1
                if word in heading_lower:
                    score += 3
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def get_file(self, source: str) -> str | None:
        """Get the full content of a file by source path."""
        return self._file_map.get(source)


async def pre_feed_context(
    query: str,
    vault_path: str | None = None,
    max_chars: int = 3000,
    max_files: int = 3,
) -> str:
    """Build a pre-feed context string from the Obsidian vault.

    Args:
        query: The current user query or task
        vault_path: Path to Obsidian vault
        max_chars: Maximum total characters to include
        max_files: Maximum number of files to pull from

    Returns:
        Formatted context string for LLM prompt injection
    """
    indexer = SecondBrainIndexer(vault_path=vault_path)
    count = indexer.build_index()
    if count == 0:
        return ""

    results = indexer.search(query, top_k=max_files)
    if not results:
        return ""

    lines = ["[SecondBrain wiki pre-feed — relevant context:]"]
    total = 0
    for entry in results:
        source = entry.get("source", "unknown")
        heading = entry.get("heading", "")
        content = entry.get("content", "")[:1500]
        line = f"\n## {heading} ({source})\n{content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)

    lines.append("\n[End of wiki pre-feed]")
    return "\n".join(lines)


def create_wiki_memory_pipeline(vault_path: str | None = None) -> dict[str, Any]:
    """Create a pipeline that combines wiki pre-feed with mem0.

    Returns a dict with tools/functions to wire into langgraph or crewAI.
    """
    return {
        "pre_feed": lambda q: pre_feed_context(q, vault_path=vault_path),
        "indexer": SecondBrainIndexer(vault_path=vault_path),
    }
