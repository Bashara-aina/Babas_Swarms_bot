"""GitHub bridge — thin wrapper exposing tools/github_intel as a bridge layer.

This lets handlers import from bridges.github_bridge instead of reaching
into tools/ directly.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from tools.github_intel import GitHubIntelEngine, RepoEvaluation, TrendingRepo

    __all__ = ["GitHubBridge", "GitHubIntelEngine", "RepoEvaluation", "TrendingRepo"]
except Exception as exc:
    logger.warning("[bridges] github_bridge unavailable: %s", exc)
    GitHubBridge = None  # type: ignore[assignment, misc]
    GitHubIntelEngine = None  # type: ignore[assignment, misc]
    TrendingRepo = None  # type: ignore[assignment, misc]
    RepoEvaluation = None  # type: ignore[assignment, misc]
    __all__ = []


class GitHubBridge:
    """Facade matching the bridge interface pattern, backed by GitHubIntelEngine."""

    def __init__(self) -> None:
        self._engine: GitHubIntelEngine | None = None

    async def initialize(self) -> None:
        if self._engine is None:
            self._engine = GitHubIntelEngine()

    async def get_trending(self, language: str = "", since: str = "daily") -> list[TrendingRepo]:
        if self._engine is None:
            await self.initialize()
        return await self._engine.fetch_trending(language=language, since=since)  # type: ignore[union-attr]

    async def evaluate_repo(self, repo: TrendingRepo) -> RepoEvaluation:
        if self._engine is None:
            await self.initialize()
        return await self._engine.evaluate_repo(repo)  # type: ignore[union-attr]

    async def fetch_readme(self, repo_url: str) -> str:
        if self._engine is None:
            await self.initialize()
        return await self._engine.fetch_readme(repo_url)  # type: ignore[union-attr]
