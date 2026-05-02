"""core/integrations/graphrag_integration.py — GraphRAG knowledge graph memory.

GraphRAG turns Obsidian wiki into a queryable knowledge graph.
Indexes documents into entity graphs and enables global/local search
over the knowledge graph for agent context.

Pipeline position: mem0 (semantic search) + langmem (episodic) + graphrag (knowledge graph)
Architecture:
    Obsidian vault → GraphRAG index → query → agent context

Usage:
    from core.integrations.graphrag_integration import (
        SwarmBotGraphRAG,
        index_wiki_knowledge_graph,
        query_wiki_graph,
    )

    # Index the wiki once
    await index_wiki_knowledge_graph("/path/to/vault")

    # Query during agent run
    result = await query_wiki_graph("What is the architecture of system X?")
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

GRAPHRAG_AVAILABLE = True

try:
    import graphrag
    import graphrag.api as api
except ImportError:
    GRAPHRAG_AVAILABLE = False
    api = None  # type: ignore

DEFAULT_MODEL = "minimax/MiniMax-M2.7"
GRAPHRAG_INDEX_DIR = os.path.expanduser("~/.legion/graphrag_index")


def _build_graphrag_config(
    index_dir: str | None = None,
    model: str | None = None,
    llm_api_key: str | None = None,
) -> Any:
    """Build a GraphRagConfig for MiniMax LLM."""
    from graphrag.config.models.graph_rag_config import GraphRagConfig

    index_dir = index_dir or GRAPHRAG_INDEX_DIR
    model_name = model or DEFAULT_MODEL
    if "/" in model_name:
        model_name = "gpt-4o-mini"

    api_key = llm_api_key or os.getenv("MINIMAX_API_KEY", "dummy")
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = "https://api.minimax.io/v1"

    return GraphRagConfig(
        data={
            "input": {"type": "file", "path": index_dir},
            "embed_text": {
                "model": model_name,
                "api_key": api_key,
                "api_base": "https://api.minimax.io/v1",
            },
            "extract_graph": {
                "model": model_name,
                "api_key": api_key,
                "api_base": "https://api.minimax.io/v1",
            },
            "summarize_descriptions": {
                "model": model_name,
                "api_key": api_key,
                "api_base": "https://api.minimax.io/v1",
            },
            "community_reports": {
                "model": model_name,
                "api_key": api_key,
                "api_base": "https://api.minimax.io/v1",
            },
            "local_search": {
                "model": model_name,
                "api_key": api_key,
                "api_base": "https://api.minimax.io/v1",
            },
            "global_search": {
                "model": model_name,
                "api_key": api_key,
                "api_base": "https://api.minimax.io/v1",
            },
        }
    )


class SwarmBotGraphRAG:
    """GraphRAG knowledge graph integration for SwarmBot."""

    def __init__(
        self,
        index_dir: str | None = None,
        model: str | None = None,
    ) -> None:
        self.index_dir = index_dir or GRAPHRAG_INDEX_DIR
        self.model = model or DEFAULT_MODEL
        self._config = None
        self._indexed = False

    def _get_config(self) -> Any:
        """Lazily build the GraphRAG config."""
        if self._config is None:
            self._config = _build_graphrag_config(self.index_dir, self.model)
        return self._config

    async def index_documents(
        self,
        documents: list[dict[str, Any]],
        incremental: bool = False,
    ) -> str:
        """Index a list of documents into GraphRAG.

        Args:
            documents: List of {"text": "...", "source": "..."} dicts
            incremental: If True, merge with existing index

        Returns:
            Status message
        """
        if not GRAPHRAG_AVAILABLE:
            return "[GraphRAG not installed — pip install graphrag]"

        try:
            import pandas as pd

            df = pd.DataFrame(documents)
            config = self._get_config()
            await api.build_index(
                config=config,
                input_documents=df,
                is_update_run=incremental,
            )
            self._indexed = True
            return f"[GraphRAG indexed {len(documents)} documents]"
        except Exception as exc:
            logger.error("GraphRAG index failed: %s", exc)
            return f"[GraphRAG error: {exc}]"

    async def query(
        self,
        query: str,
        mode: str = "local",
        response_type: str = "Multiple Paragraphs",
    ) -> str:
        """Query the knowledge graph.

        Args:
            query: Natural language query
            mode: 'local', 'global', 'drift', or 'basic'
            response_type: How detailed the response should be

        Returns:
            Query result string
        """
        if not GRAPHRAG_AVAILABLE:
            return "[GraphRAG not installed — pip install graphrag]"

        try:
            import pandas as pd

            def _load_artifact(name: str) -> pd.DataFrame:
                path = Path(self.index_dir) / name
                if path.exists():
                    return pd.read_parquet(path)
                return pd.DataFrame()

            entities = _load_artifact("entities.parquet")
            communities = _load_artifact("communities.parquet")
            community_reports = _load_artifact("community_reports.parquet")
            text_units = _load_artifact("text_units.parquet")
            relationships = _load_artifact("relationships.parquet")

            if text_units.empty and entities.empty:
                return "[GraphRAG index not found — run index_wiki_knowledge_graph first]"

            config = self._get_config()

            if mode == "global":
                result, _ = await api.global_search(
                    config,
                    entities=entities,
                    communities=communities,
                    community_reports=community_reports,
                    community_level=1,
                    dynamic_community_selection=False,
                    response_type=response_type,
                    query=query,
                )
            elif mode == "drift":
                result, _ = await api.drift_search(
                    config,
                    entities=entities,
                    communities=communities,
                    community_reports=community_reports,
                    text_units=text_units,
                    relationships=relationships,
                    community_level=1,
                    response_type=response_type,
                    query=query,
                )
            elif mode == "basic":
                result, _ = await api.basic_search(
                    config,
                    text_units=text_units,
                    response_type=response_type,
                    query=query,
                )
            else:
                result, _ = await api.local_search(
                    config,
                    entities=entities,
                    communities=communities,
                    community_reports=community_reports,
                    text_units=text_units,
                    relationships=relationships,
                    covariates=None,
                    community_level=1,
                    response_type=response_type,
                    query=query,
                )
            return str(result) if result else "(empty result)"
        except Exception as exc:
            logger.warning("GraphRAG query failed: %s", exc)
            return f"[GraphRAG query error: {exc}]"

    async def local_search(self, query: str) -> str:
        """Local search over the knowledge graph."""
        return await self.query(query, mode="local")

    async def global_search(self, query: str) -> str:
        """Global search over the knowledge graph."""
        return await self.query(query, mode="global")


async def index_wiki_knowledge_graph(
    vault_path: str | None = None,
    model: str | None = None,
) -> str:
    """Index an Obsidian vault into GraphRAG.

    Args:
        vault_path: Path to Obsidian vault (markdown files)
        model: Model to use for indexing

    Returns:
        Status message
    """
    if not GRAPHRAG_AVAILABLE:
        return "[GraphRAG not installed — pip install graphrag]"

    vault = Path(vault_path) if vault_path else None
    if not vault or not vault.exists():
        return f"[Vault path not found: {vault_path}]"

    documents = []
    for md_file in vault.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            documents.append({
                "text": content[:10000],
                "source": str(md_file.relative_to(vault)),
            })
        except Exception as exc:
            logger.warning("Failed to read %s: %s", md_file, exc)

    if not documents:
        return "[No markdown files found in vault]"

    rag = SwarmBotGraphRAG(index_dir=str(vault), model=model)
    return await rag.index_documents(documents)


async def query_wiki_graph(
    question: str,
    mode: str = "local",
    vault_path: str | None = None,
) -> str:
    """Query the indexed wiki knowledge graph.

    Args:
        question: Natural language question
        mode: 'local', 'global', or 'basic'
        vault_path: Path to the vault (used if not yet indexed)

    Returns:
        Answer string from GraphRAG
    """
    if not GRAPHRAG_AVAILABLE:
        return "[GraphRAG not installed — pip install graphrag]"

    rag = SwarmBotGraphRAG(index_dir=vault_path or "/home/newadmin/swarm-bot/.wiki")
    return await rag.query(question, mode=mode)
