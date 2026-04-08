"""
Structured knowledge layer — optional graph (networkx) + cognee hook.

Cognee is optional; without it, stores a small in-memory adjacency for tags.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_STATE_PATH = Path.home() / ".legionswarm" / "memory" / "knowledge_graph.json"


class KnowledgeManager:
    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[tuple[str, str, str]] = []
        self._load()

    def _load(self) -> None:
        if not _STATE_PATH.exists():
            return
        try:
            raw = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
            self._nodes = raw.get("nodes") or {}
            self._edges = [(e[0], e[1], e[2]) for e in raw.get("edges") or []]
        except Exception as exc:
            logger.debug("knowledge graph load failed: %s", exc)

    def _save(self) -> None:
        try:
            _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            _STATE_PATH.write_text(
                json.dumps(
                    {"nodes": self._nodes, "edges": self._edges},
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug("knowledge graph save failed: %s", exc)

    def link(self, a: str, rel: str, b: str) -> None:
        a, b, rel = a.strip(), b.strip(), rel.strip()
        if not a or not b:
            return
        self._nodes.setdefault(a, {"tag": a})
        self._nodes.setdefault(b, {"tag": b})
        self._edges.append((a, rel, b))
        self._edges = self._edges[-500:]
        self._save()

    def neighbors(self, tag: str, limit: int = 12) -> list[str]:
        tag = tag.strip().lower()
        out: list[str] = []
        for x, _rel, y in self._edges:
            if x.lower() == tag and y not in out:
                out.append(y)
            elif y.lower() == tag and x not in out:
                out.append(x)
            if len(out) >= limit:
                break
        return out

    def prompt_snippet(self, topic: str) -> str:
        if not topic.strip():
            return ""
        n = self.neighbors(topic.split()[0], limit=8)
        if not n:
            return ""
        return "[KNOWLEDGE GRAPH — related]\n" + ", ".join(n)

    async def cognee_ingest(self, text: str, *, _meta: dict[str, Any] | None = None) -> str:
        """If cognee is installed and COGNEE_ENABLED=1, forward; else no-op."""
        if os.getenv("COGNEE_ENABLED", "0").strip().lower() not in ("1", "true", "yes", "on"):
            return ""
        try:
            import inspect

            import cognee  # type: ignore

            add_fn = getattr(cognee, "add", None) or getattr(cognee, "add_data", None)
            if callable(add_fn):
                r = add_fn(text)
                if inspect.isawaitable(r):
                    await r
                return "cognee: ingested"
        except Exception as exc:
            logger.debug("cognee ingest skipped: %s", exc)
        return ""


_km: KnowledgeManager | None = None


def get_knowledge_manager() -> KnowledgeManager:
    global _km
    if _km is None:
        _km = KnowledgeManager()
    return _km
