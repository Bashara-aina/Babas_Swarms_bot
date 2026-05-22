"""core/integrations/graphrag_integration.py — GraphRAG knowledge graph memory.  # type: ignore[reportOptionalMemberAccess]

GraphRAG turns Obsidian wiki into a queryable knowledge graph.  # type: ignore[reportOptionalMemberAccess]
Indexes documents into entity graphs and enables global/local search
over the knowledge graph for agent context.  # type: ignore[reportOptionalMemberAccess]

Pipeline position: mem0 (semantic search) + langmem (episodic) + graphrag (knowledge graph)  # type: ignore[reportOptionalMemberAccess]
Architecture:
    Obsidian vault → GraphRAG index → query → agent context

Usage:
    from core.integrations.graphrag_integration import (  # type: ignore[reportOptionalMemberAccess]
        SwarmBotGraphRAG,  # type: ignore[reportOptionalMemberAccess]
        index_wiki_knowledge_graph,  # type: ignore[reportOptionalMemberAccess]
        query_wiki_graph,  # type: ignore[reportOptionalMemberAccess]
    )

    # Index the wiki once
    await index_wiki_knowledge_graph("/path/to/vault")  # type: ignore[reportOptionalMemberAccess]

    # Query during agent run
    result = await query_wiki_graph("What is the architecture of system X?")  # type: ignore[reportOptionalMemberAccess]
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)  # type: ignore[reportOptionalMemberAccess]

GRAPHRAG_AVAILABLE = True  # type: ignore[reportOptionalMemberAccess]
_api = None  # lazily loaded


def _load_api():
    """Lazily load graphrag.api — importing it directly hangs (heavy sub-dependencies)."""
    global _api
    if _api is not None:
        return _api
    try:
        import graphrag.api as _api_local  # noqa: F401
        _api = _api_local
        return _api
    except ImportError as exc:
        logger.debug("graphrag.api lazy load failed (ImportError): %s", exc)
        _api = None
        return None
    except Exception as exc:
        logger.debug("graphrag.api lazy load failed: %s", exc)
        _api = None
        return None

DEFAULT_MODEL = "minimax-coding-plan/MiniMax-M2.7"  # type: ignore[reportOptionalMemberAccess]
GRAPHRAG_INDEX_DIR = os.path.expanduser("~/.legion/graphrag_index")  # type: ignore[reportOptionalMemberAccess]


def _keyword_search_text_units(query: str, index_dir: str | None = None, limit: int = 3) -> list[str]:
    """
    Direct keyword search over text_units.parquet — no LLM, no GraphRag SDK.
    Returns top matching snippets by keyword overlap score.
    """
    try:
        import pandas as pd

        idx = index_dir or GRAPHRAG_INDEX_DIR
        path = Path(idx) / "text_units.parquet"
        if not path.exists():
            return []

        df = pd.read_parquet(path)
        if df.empty:
            return []

        q_words = set(query.lower().split())

        def score(row) -> int:
            text = str(row.get("text", "")).lower()
            return sum(1 for w in q_words if w in text)

        df["_score"] = df.apply(score, axis=1)
        top = df.nlargest(limit, "_score")
        results = []
        for _, row in top.iterrows():
            txt = str(row["text"])[:300].replace("\n", " ")
            results.append(f"[graphrag|{row.get('document_id', '?')[:40]}] {txt}")
        return results
    except Exception as exc:
        logger.debug("graphrag keyword search failed: %s", exc)
        return []


class SwarmBotGraphRAG:
    """GraphRAG knowledge graph integration for SwarmBot."""  # type: ignore[reportOptionalMemberAccess]

    def __init__(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        index_dir: str | None = None,  # type: ignore[reportOptionalMemberAccess]
        model: str | None = None,  # type: ignore[reportOptionalMemberAccess]
    ) -> None:
        self.index_dir = index_dir or GRAPHRAG_INDEX_DIR  # type: ignore[reportOptionalMemberAccess]
        self.model = model or DEFAULT_MODEL  # type: ignore[reportOptionalMemberAccess]
        self._config = None  # type: ignore[reportOptionalMemberAccess]
        self._indexed = False  # type: ignore[reportOptionalMemberAccess]

    def _get_config(self) -> Any:  # type: ignore[reportOptionalMemberAccess]
        """Lazily build the GraphRAG config."""  # type: ignore[reportOptionalMemberAccess]
        if self._config is None:  # type: ignore[reportOptionalMemberAccess]
            self._config = _build_graphrag_config(self.index_dir, self.model)  # type: ignore[reportOptionalMemberAccess]
        return self._config  # type: ignore[reportOptionalMemberAccess]

    async def index_documents(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        documents: list[dict[str, Any]],  # type: ignore[reportOptionalMemberAccess]
        incremental: bool = False,  # type: ignore[reportOptionalMemberAccess]
    ) -> str:
        """Index a list of documents into GraphRAG.  # type: ignore[reportOptionalMemberAccess]

        Args:
            documents: List of {"text": "...", "source": "..."} dicts  # type: ignore[reportOptionalMemberAccess]
            incremental: If True, merge with existing index  # type: ignore[reportOptionalMemberAccess]

        Returns:
            Status message
        """
        if not GRAPHRAG_AVAILABLE:
            return "[GraphRAG not installed — pip install graphrag]"

        try:
            import pandas as pd

            df = pd.DataFrame(documents)  # type: ignore[reportOptionalMemberAccess]
            config = self._get_config()  # type: ignore[reportOptionalMemberAccess]
            graphrag_api = _load_api()  # type: ignore[reportOptionalMemberAccess]
            if graphrag_api is None:  # type: ignore[reportOptionalMemberAccess]
                return "[GraphRAG api load failed]"  # type: ignore[reportOptionalMemberAccess]
            await graphrag_api.build_index(  # type: ignore[reportOptionalMemberAccess]
                config=config,  # type: ignore[reportOptionalMemberAccess]
                input_documents=df,  # type: ignore[reportOptionalMemberAccess]
                is_update_run=incremental,  # type: ignore[reportOptionalMemberAccess]
            )
            self._indexed = True  # type: ignore[reportOptionalMemberAccess]
            return f"[GraphRAG indexed {len(documents)} documents]"  # type: ignore[reportOptionalMemberAccess]
        except Exception as exc:
            logger.error("GraphRAG index failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
            return f"[GraphRAG error: {exc}]"

    async def query(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        query: str,  # type: ignore[reportOptionalMemberAccess]
        mode: str = "local",  # type: ignore[reportOptionalMemberAccess]
        response_type: str = "Multiple Paragraphs",  # type: ignore[reportOptionalMemberAccess]
    ) -> str:
        """Query the knowledge graph.  # type: ignore[reportOptionalMemberAccess]

        Args:
            query: Natural language query
            mode: 'local', 'global', 'drift', or 'basic'  # type: ignore[reportOptionalMemberAccess]
            response_type: How detailed the response should be

        Returns:
            Query result string
        """
        if not GRAPHRAG_AVAILABLE:
            return "[GraphRAG not installed — pip install graphrag]"

        try:
            import pandas as pd

            def _load_artifact(name: str) -> pd.DataFrame:  # type: ignore[reportOptionalMemberAccess]
                path = Path(self.index_dir) / name  # type: ignore[reportOptionalMemberAccess]
                if path.exists():  # type: ignore[reportOptionalMemberAccess]
                    return pd.read_parquet(path)  # type: ignore[reportOptionalMemberAccess]
                return pd.DataFrame()  # type: ignore[reportOptionalMemberAccess]

            entities = _load_artifact("entities.parquet")  # type: ignore[reportOptionalMemberAccess]
            communities = _load_artifact("communities.parquet")  # type: ignore[reportOptionalMemberAccess]
            community_reports = _load_artifact("community_reports.parquet")  # type: ignore[reportOptionalMemberAccess]
            text_units = _load_artifact("text_units.parquet")  # type: ignore[reportOptionalMemberAccess]
            relationships = _load_artifact("relationships.parquet")  # type: ignore[reportOptionalMemberAccess]

            if text_units.empty and entities.empty:  # type: ignore[reportOptionalMemberAccess]
                return "[GraphRAG index not found — run index_wiki_knowledge_graph first]"

            config = self._get_config()  # type: ignore[reportOptionalMemberAccess]
            graphrag_api = _load_api()  # type: ignore[reportOptionalMemberAccess]
            if graphrag_api is None:  # type: ignore[reportOptionalMemberAccess]
                return "[GraphRAG api load failed]"  # type: ignore[reportOptionalMemberAccess]

            if mode == "global":  # type: ignore[reportOptionalMemberAccess]
                result, _ = await graphrag_api.global_search(  # type: ignore[reportOptionalMemberAccess]
                    config,  # type: ignore[reportOptionalMemberAccess]
                    entities=entities,  # type: ignore[reportOptionalMemberAccess]
                    communities=communities,  # type: ignore[reportOptionalMemberAccess]
                    community_reports=community_reports,  # type: ignore[reportOptionalMemberAccess]
                    community_level=1,  # type: ignore[reportOptionalMemberAccess]
                    dynamic_community_selection=False,  # type: ignore[reportOptionalMemberAccess]
                    response_type=response_type,  # type: ignore[reportOptionalMemberAccess]
                    query=query,  # type: ignore[reportOptionalMemberAccess]
                )
            elif mode == "drift":  # type: ignore[reportOptionalMemberAccess]
                result, _ = await graphrag_api.drift_search(  # type: ignore[reportOptionalMemberAccess]
                    config,  # type: ignore[reportOptionalMemberAccess]
                    entities=entities,  # type: ignore[reportOptionalMemberAccess]
                    communities=communities,  # type: ignore[reportOptionalMemberAccess]
                    community_reports=community_reports,  # type: ignore[reportOptionalMemberAccess]
                    text_units=text_units,  # type: ignore[reportOptionalMemberAccess]
                    relationships=relationships,  # type: ignore[reportOptionalMemberAccess]
                    community_level=1,  # type: ignore[reportOptionalMemberAccess]
                    response_type=response_type,  # type: ignore[reportOptionalMemberAccess]
                    query=query,  # type: ignore[reportOptionalMemberAccess]
                )
            elif mode == "basic":  # type: ignore[reportOptionalMemberAccess]
                result, _ = await graphrag_api.basic_search(  # type: ignore[reportOptionalMemberAccess]
                    config,  # type: ignore[reportOptionalMemberAccess]
                    text_units=text_units,  # type: ignore[reportOptionalMemberAccess]
                    response_type=response_type,  # type: ignore[reportOptionalMemberAccess]
                    query=query,  # type: ignore[reportOptionalMemberAccess]
                )
            else:
                result, _ = await graphrag_api.local_search(  # type: ignore[reportOptionalMemberAccess]
                    config,  # type: ignore[reportOptionalMemberAccess]
                    entities=entities,  # type: ignore[reportOptionalMemberAccess]
                    communities=communities,  # type: ignore[reportOptionalMemberAccess]
                    community_reports=community_reports,  # type: ignore[reportOptionalMemberAccess]
                    text_units=text_units,  # type: ignore[reportOptionalMemberAccess]
                    relationships=relationships,  # type: ignore[reportOptionalMemberAccess]
                    covariates=None,  # type: ignore[reportOptionalMemberAccess]
                    community_level=1,  # type: ignore[reportOptionalMemberAccess]
                    response_type=response_type,  # type: ignore[reportOptionalMemberAccess]
                    query=query,  # type: ignore[reportOptionalMemberAccess]
                )
            return str(result) if result else "(empty result)"  # type: ignore[reportOptionalMemberAccess]
        except Exception as exc:
            logger.warning("GraphRAG query failed: %s", exc)  # type: ignore[reportOptionalMemberAccess]
            return f"[GraphRAG query error: {exc}]"

    async def local_search(self, query: str) -> str:  # type: ignore[reportOptionalMemberAccess]
        """Local search over the knowledge graph."""  # type: ignore[reportOptionalMemberAccess]
        return await self.query(query, mode="local")  # type: ignore[reportOptionalMemberAccess]

    async def global_search(self, query: str) -> str:  # type: ignore[reportOptionalMemberAccess]
        """Global search over the knowledge graph."""  # type: ignore[reportOptionalMemberAccess]
        return await self.query(query, mode="global")  # type: ignore[reportOptionalMemberAccess]


async def index_wiki_knowledge_graph(  # type: ignore[reportOptionalMemberAccess]
    vault_path: str | None = None,  # type: ignore[reportOptionalMemberAccess]
    model: str | None = None,  # type: ignore[reportOptionalMemberAccess]
) -> str:
    """Index an Obsidian vault into GraphRAG.  # type: ignore[reportOptionalMemberAccess]

    Args:
        vault_path: Path to Obsidian vault (markdown files)  # type: ignore[reportOptionalMemberAccess]
        model: Model to use for indexing

    Returns:
        Status message
    """
    if not GRAPHRAG_AVAILABLE:
        return "[GraphRAG not installed — pip install graphrag]"

    vault = Path(vault_path) if vault_path else None  # type: ignore[reportOptionalMemberAccess]
    if not vault or not vault.exists():  # type: ignore[reportOptionalMemberAccess]
        return f"[Vault path not found: {vault_path}]"

    documents = []  # type: ignore[reportOptionalMemberAccess]
    for md_file in vault.rglob("*.md"):  # type: ignore[reportOptionalMemberAccess]
        try:
            content = md_file.read_text(encoding="utf-8")  # type: ignore[reportOptionalMemberAccess]
            documents.append({  # type: ignore[reportOptionalMemberAccess]
                "text": content[:10000],  # type: ignore[reportOptionalMemberAccess]
                "source": str(md_file.relative_to(vault)),  # type: ignore[reportOptionalMemberAccess]
            })
        except Exception as exc:
            logger.warning("Failed to read %s: %s", md_file, exc)  # type: ignore[reportOptionalMemberAccess]

    if not documents:
        return "[No markdown files found in vault]"

    rag = SwarmBotGraphRAG(index_dir=GRAPHRAG_INDEX_DIR, model=model)  # type: ignore[reportOptionalMemberAccess]
    return await rag.index_documents(documents)  # type: ignore[reportOptionalMemberAccess]


async def query_wiki_graph(  # type: ignore[reportOptionalMemberAccess]
    question: str,  # type: ignore[reportOptionalMemberAccess]
    mode: str = "local",  # type: ignore[reportOptionalMemberAccess]
    vault_path: str | None = None,  # type: ignore[reportOptionalMemberAccess]
) -> str:
    """Query the indexed wiki knowledge graph using direct keyword search.

    Uses _keyword_search_text_units (pure pandas, no LLM) for fast, reliable
    keyword-matching recall. The full GraphRAG LLM-based query is available
    via SwarmBotGraphRAG.query() for cases where the index is pre-loaded
    and graphrag.api is available.
    """
    if not GRAPHRAG_AVAILABLE:
        return "[GraphRAG not installed — pip install graphrag]"

    idx = vault_path or GRAPHRAG_INDEX_DIR
    results = _keyword_search_text_units(question, index_dir=idx, limit=5)
    if not results:
        return "(no wiki matches found)"
    return "\n".join(f"  • {r}" for r in results)
