"""
Phase 4: Graphiti Temporal Knowledge Graph
Time-aware memory for Legion — stores WHAT happened + WHEN + WHO did it.

Integrates with existing graphiti_client.py which uses Neo4j.
Adds temporal search and session diff capabilities.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from graphiti_core import Graphiti

logger = logging.getLogger(__name__)

LEGION_GRAPHITI_ENABLED = os.getenv("LEGION_GRAPHITI_ENABLED", "").lower() == "true"

_client: Graphiti | None = None


def _get_graphiti_client() -> Graphiti | None:
    """Get or create Graphiti client using existing env var config."""
    global _client

    if _client is not None:
        return _client

    if not LEGION_GRAPHITI_ENABLED:
        logger.debug("Graphiti disabled via LEGION_GRAPHITI_ENABLED")
        return None

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        logger.warning("Graphiti requires NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        return None

    try:
        _client = Graphiti(uri=uri, user=user, password=password)
        logger.info("Graphiti temporal client created")
    except Exception as e:
        logger.error(f"Failed to create Graphiti client: {e}")
        return None

    return _client


async def add_episode(
    content: str,
    agent: str,
    task: str,
    reference_time: datetime | None = None,
) -> bool:
    """
    Add a session event to the temporal graph.

    Args:
        content: What happened
        agent: Which agent performed the action
        task: The parent task context
        reference_time: When it happened (defaults to now)

    Returns:
        True if stored successfully
    """
    client = _get_graphiti_client()
    if client is None:
        return False

    if reference_time is None:
        reference_time = datetime.utcnow()

    episode_name = f"{agent}_{reference_time.strftime('%Y%m%d_%H%M%S')}"

    try:
        await client.add_episode(
            name=episode_name,
            episode_body=content[:2000],
            source_description=f"Agent: {agent} | Task: {task}",
            reference_time=reference_time,
        )
        logger.debug(f"Stored temporal episode: {episode_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to add temporal episode: {e}")
        return False


async def search_temporal(
    query: str,
    since_days: int = 7,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search with time awareness.

    Args:
        query: What to search for
        since_days: Only return results from the last N days
        limit: Maximum number of results

    Returns:
        List of dicts with 'content', 'created_at', 'agent', 'task'
    """
    client = _get_graphiti_client()
    if client is None:
        return []

    cutoff = datetime.utcnow() - timedelta(days=since_days)

    try:
        results = await client.search(
            query=query,
            num_results=limit,
        )

        filtered = []
        for edge in results:
            if edge.created_at and edge.created_at >= cutoff:
                filtered.append({
                    "content": edge.fact,
                    "created_at": edge.created_at.isoformat() if edge.created_at else None,
                    "uuid": edge.uuid,
                    "source_node_uuid": edge.source_node_uuid,
                    "target_node_uuid": edge.target_node_uuid,
                })

        return filtered

    except Exception as e:
        logger.error(f"Temporal search failed: {e}")
        return []


async def get_session_diff(days_ago: int = 1) -> list[dict[str, Any]]:
    """
    What changed between now and N days ago?

    Args:
        days_ago: Compare now to N days ago

    Returns:
        List of changes/decisions from the period
    """
    client = _get_graphiti_client()
    if client is None:
        return []

    cutoff = datetime.utcnow() - timedelta(days=days_ago)

    try:
        results = await client.search(
            query=f"changes decisions actions from last {days_ago} days",
            num_results=20,
        )

        recent = []
        for edge in results:
            if edge.created_at and edge.created_at >= cutoff:
                recent.append({
                    "content": edge.fact,
                    "created_at": edge.created_at.isoformat() if edge.created_at else None,
                })

        return recent

    except Exception as e:
        logger.error(f"Session diff failed: {e}")
        return []


async def get_session_timeline(
    days: int = 7,
) -> list[dict[str, Any]]:
    """
    Get chronological timeline of all events.

    Args:
        days: How far back to look

    Returns:
        Chronologically sorted list of events
    """
    client = _get_graphiti_client()
    if client is None:
        return []

    cutoff = datetime.utcnow() - timedelta(days=days)

    try:
        results = await client.search(
            query="*",
            num_results=50,
        )

        timeline = []
        for edge in results:
            if edge.created_at and edge.created_at >= cutoff:
                timeline.append({
                    "content": edge.fact,
                    "created_at": edge.created_at.isoformat() if edge.created_at else None,
                })

        timeline.sort(key=lambda x: x.get("created_at", ""))
        return timeline

    except Exception as e:
        logger.error(f"Timeline failed: {e}")
        return []


class LegionTemporalMemory:
    """Temporal knowledge graph for Legion."""

    def __init__(self):
        self.client = _get_graphiti_client()

    async def add_episode(self, content: str, agent: str, task: str):
        """Add a session event to the temporal graph."""
        return await add_episode(content, agent, task)

    async def search_temporal(self, query: str, since_days: int = 7):
        """Search with time awareness."""
        return await search_temporal(query, since_days)

    async def get_session_diff(self, days_ago: int = 1):
        """What changed between now and N days ago?"""
        return await get_session_diff(days_ago)


if __name__ == "__main__":
    import sys

    async def test():
        print("Testing Graphiti temporal integration...")

        client = _get_graphiti_client()
        if client is None:
            print("  Graphiti not enabled (set LEGION_GRAPHITI_ENABLED=true)")
            print("  Using Neo4j env vars:", "NEO4J_URI" in os.environ)
            return

        print(f"  Graphiti client: {client}")

        result = await add_episode(
            content="Test episode from graphiti_integration",
            agent="test_agent",
            task="testing temporal graph",
        )
        print(f"  add_episode: {'OK' if result else 'FAILED'}")

        results = await search_temporal("test", since_days=1)
        print(f"  search_temporal: {len(results)} results")

        print("\n  Graphiti temporal integration: READY")

    if LEGION_GRAPHITI_ENABLED:
        asyncio.run(test())
    else:
        print("Graphiti temporal integration: DISABLED (LEGION_GRAPHITI_ENABLED not set)")
        print("Set LEGION_GRAPHITI_ENABLED=true and configure Neo4j to enable.")