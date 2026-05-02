"""Graphiti client singleton for episodic memory storage and retrieval.

Provides remember(), recall(), and recall_as_context() methods for storing
and retrieving agent experiences from Graphiti (Neo4j-backed episodic memory).
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

logger = logging.getLogger(__name__)

GROUP_ID = "babas_swarms"

_CONTENT_TRUNCATE_LEN = 2000

_client_instance: Graphiti | None = None


async def _get_client() -> Graphiti | None:
    """Get or create the singleton Graphiti client instance.

    Returns None if LEGION_GRAPHITI_ENABLED is not set to 'true'.
    """
    global _client_instance

    if _client_instance is not None:
        return _client_instance

    enabled = os.getenv("LEGION_GRAPHITI_ENABLED", "").lower()
    if enabled != "true":
        logger.debug("Graphiti disabled via LEGION_GRAPHITI_ENABLED")
        return None

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        logger.warning(
            "Graphiti requires NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD env vars"
        )
        return None

    try:
        _client_instance = Graphiti(uri=uri, user=user, password=password)
        logger.info("Graphiti client singleton created")
    except Exception as e:
        logger.error(f"Failed to create Graphiti client: {e}")
        return None
    return _client_instance


async def async_init() -> None:
    """Initialize the Graphiti client (lazy, non-blocking).

    Indices are built on first use rather than at startup to avoid
    blocking the bot when Neo4j is unavailable.
    """
    client = await _get_client()
    if client is None:
        logger.debug("Graphiti init skipped (disabled or misconfigured)")
        return

    logger.info("Graphiti client ready (indices built on first use)")


async def close() -> None:
    """Close the Graphiti client gracefully."""
    global _client_instance

    if _client_instance is not None:
        try:
            await _client_instance.close()
            logger.info("Graphiti client closed")
        except Exception as e:
            logger.error(f"Error closing Graphiti client: {e}")
        finally:
            _client_instance = None


def _truncate_content(content: str) -> str:
    """Truncate content to maximum character length."""
    if len(content) <= _CONTENT_TRUNCATE_LEN:
        return content
    return content[:_CONTENT_TRUNCATE_LEN] + "..."


class GraphitiClient:
    """Singleton Graphiti client for episodic memory operations.

    Use _get_client() to obtain the singleton instance.
    """

    async def remember(
        self,
        agent_id: str,
        content: str,
        episode_type: EpisodeType = EpisodeType.text,
    ) -> bool:
        """Store an episode to Graphiti episodic memory.

        Args:
            agent_id: Identifier for the agent storing this episode.
            content: The content to store (will be truncated to 2000 chars).
            episode_type: Type of episode (message, json, text).

        Returns:
            True if stored successfully, False otherwise.
        """
        client = await _get_client()
        if client is None:
            return False

        truncated = _truncate_content(content)

        episode_name = f"{agent_id}_{datetime.utcnow().isoformat()}"

        try:
            await asyncio.wait_for(
                client.add_episode(
                    name=episode_name,
                    episode_body=truncated,
                    source_description=f"Agent {agent_id} episode",
                    reference_time=datetime.utcnow(),
                    source=episode_type,
                    group_id=GROUP_ID,
                ),
                timeout=5.0,
            )
            logger.debug(f"Stored episode for agent {agent_id}: {episode_name}")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Graphiti add_episode timed out for {agent_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to store episode for {agent_id}: {e}")
            return False

    async def recall(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search Graphiti for episodes matching the query.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of dicts with 'content', 'score', and 'metadata' keys.
            Returns empty list on error or when Graphiti is disabled.
        """
        client = await _get_client()
        if client is None:
            return []

        try:
            results = await asyncio.wait_for(
                client.search(
                    query=query,
                    group_ids=[GROUP_ID],
                    num_results=limit,
                ),
                timeout=5.0,
            )

            episodes = []
            for edge in results:
                episodes.append(
                    {
                        "content": edge.fact,
                        "score": 1.0,  # Graphiti search doesn't provide scores
                        "metadata": {
                            "uuid": edge.uuid,
                            "group_id": edge.group_id,
                            "created_at": (
                                edge.created_at.isoformat()
                                if edge.created_at
                                else None
                            ),
                            "source_node_uuid": edge.source_node_uuid,
                            "target_node_uuid": edge.target_node_uuid,
                        },
                    }
                )
            return episodes

        except asyncio.TimeoutError:
            logger.warning(f"Graphiti search timed out for query '{query}'")
            return []
        except Exception as e:
            logger.error(f"Failed to recall episodes for query '{query}': {e}")
            return []

    async def recall_as_context(
        self,
        query: str,
        limit: int = 5,
    ) -> str:
        """Search Graphiti and format results as LLM context string.

        Args:
            query: Search query string.
            limit: Maximum number of results to include.

        Returns:
            Formatted string suitable for injecting as LLM context.
            Returns empty string on error or when Graphiti is disabled.
        """
        episodes = await self.recall(query=query, limit=limit)

        if not episodes:
            return ""

        context_parts = []
        for i, ep in enumerate(episodes, start=1):
            context_parts.append(
                f"[Reference {i}]\n{ep['content']}\n"
            )

        return "\n---\n".join(context_parts)
