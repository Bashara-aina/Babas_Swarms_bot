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

try:
    import graphrag
    import graphrag.api as api  # type: ignore[reportOptionalMemberAccess]
except ImportError:
    GRAPHRAG_AVAILABLE = False  # type: ignore[reportOptionalMemberAccess]
    api = None  # type: ignore

DEFAULT_MODEL = "minimax/MiniMax-M2.7"  # type: ignore[reportOptionalMemberAccess]
GRAPHRAG_INDEX_DIR = os.path.expanduser("~/.legion/graphrag_index")  # type: ignore[reportOptionalMemberAccess]


def _build_graphrag_config(  # type: ignore[reportOptionalMemberAccess]
    index_dir: str | None = None,  # type: ignore[reportOptionalMemberAccess]
    model: str | None = None,  # type: ignore[reportOptionalMemberAccess]
    llm_api_key: str | None = None,  # type: ignore[reportOptionalMemberAccess]
) -> Any:
    """Build a GraphRagConfig for MiniMax LLM."""  # type: ignore[reportOptionalMemberAccess]
    from graphrag.config.models.graph_rag_config import (
        GraphRagConfig,  # type: ignore[reportOptionalMemberAccess]
    )

    index_dir = index_dir or GRAPHRAG_INDEX_DIR  # type: ignore[reportOptionalMemberAccess]
    model_name = model or DEFAULT_MODEL  # type: ignore[reportOptionalMemberAccess]
    if "/" in model_name:
        model_name = "gpt-4o-mini"  # type: ignore[reportOptionalMemberAccess]

    api_key = llm_api_key or os.getenv("MINIMAX_API_KEY", "dummy")  # type: ignore[reportOptionalMemberAccess]
    os.environ["OPENAI_API_KEY"] = api_key  # type: ignore[reportOptionalMemberAccess]
    os.environ["OPENAI_BASE_URL"] = "https://api.minimax.io/v1"  # type: ignore[reportOptionalMemberAccess]

    return GraphRagConfig(  # type: ignore[reportOptionalMemberAccess]
        data={  # type: ignore[reportOptionalMemberAccess]
            "input": {"type": "file", "path": index_dir},  # type: ignore[reportOptionalMemberAccess]
            "embed_text": {
                "model": model_name,  # type: ignore[reportOptionalMemberAccess]
                "api_key": api_key,  # type: ignore[reportOptionalMemberAccess]
                "api_base": "https://api.minimax.io/v1",  # type: ignore[reportOptionalMemberAccess]
            },  # type: ignore[reportOptionalMemberAccess]
            "extract_graph": {
                "model": model_name,  # type: ignore[reportOptionalMemberAccess]
                "api_key": api_key,  # type: ignore[reportOptionalMemberAccess]
                "api_base": "https://api.minimax.io/v1",  # type: ignore[reportOptionalMemberAccess]
            },  # type: ignore[reportOptionalMemberAccess]
            "summarize_descriptions": {
                "model": model_name,  # type: ignore[reportOptionalMemberAccess]
                "api_key": api_key,  # type: ignore[reportOptionalMemberAccess]
                "api_base": "https://api.minimax.io/v1",  # type: ignore[reportOptionalMemberAccess]
            },  # type: ignore[reportOptionalMemberAccess]
            "community_reports": {
                "model": model_name,  # type: ignore[reportOptionalMemberAccess]
                "api_key": api_key,  # type: ignore[reportOptionalMemberAccess]
                "api_base": "https://api.minimax.io/v1",  # type: ignore[reportOptionalMemberAccess]
            },  # type: ignore[reportOptionalMemberAccess]
            "local_search": {
                "model": model_name,  # type: ignore[reportOptionalMemberAccess]
                "api_key": api_key,  # type: ignore[reportOptionalMemberAccess]
                "api_base": "https://api.minimax.io/v1",  # type: ignore[reportOptionalMemberAccess]
            },  # type: ignore[reportOptionalMemberAccess]
            "global_search": {
                "model": model_name,  # type: ignore[reportOptionalMemberAccess]
                "api_key": api_key,  # type: ignore[reportOptionalMemberAccess]
                "api_base": "https://api.minimax.io/v1",  # type: ignore[reportOptionalMemberAccess]
            },  # type: ignore[reportOptionalMemberAccess]
        }
    )


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
            await api.build_index(  # type: ignore[reportOptionalMemberAccess]
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

            if mode == "global":  # type: ignore[reportOptionalMemberAccess]
                result, _ = await api.global_search(  # type: ignore[reportOptionalMemberAccess]
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
                result, _ = await api.drift_search(  # type: ignore[reportOptionalMemberAccess]
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
                result, _ = await api.basic_search(  # type: ignore[reportOptionalMemberAccess]
                    config,  # type: ignore[reportOptionalMemberAccess]
                    text_units=text_units,  # type: ignore[reportOptionalMemberAccess]
                    response_type=response_type,  # type: ignore[reportOptionalMemberAccess]
                    query=query,  # type: ignore[reportOptionalMemberAccess]
                )
            else:
                result, _ = await api.local_search(  # type: ignore[reportOptionalMemberAccess]
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

    rag = SwarmBotGraphRAG(index_dir=str(vault), model=model)  # type: ignore[reportOptionalMemberAccess]
    return await rag.index_documents(documents)  # type: ignore[reportOptionalMemberAccess]


async def query_wiki_graph(  # type: ignore[reportOptionalMemberAccess]
    question: str,  # type: ignore[reportOptionalMemberAccess]
    mode: str = "local",  # type: ignore[reportOptionalMemberAccess]
    vault_path: str | None = None,  # type: ignore[reportOptionalMemberAccess]
) -> str:
    """Query the indexed wiki knowledge graph.  # type: ignore[reportOptionalMemberAccess]

    Args:
        question: Natural language question
        mode: 'local', 'global', or 'basic'  # type: ignore[reportOptionalMemberAccess]
        vault_path: Path to the vault (used if not yet indexed)  # type: ignore[reportOptionalMemberAccess]

    Returns:
        Answer string from GraphRAG
    """
    if not GRAPHRAG_AVAILABLE:
        return "[GraphRAG not installed — pip install graphrag]"

    rag = SwarmBotGraphRAG(index_dir=vault_path or "/home/newadmin/swarm-bot/.wiki")  # type: ignore[reportOptionalMemberAccess]
    return await rag.query(question, mode=mode)  # type: ignore[reportOptionalMemberAccess]
