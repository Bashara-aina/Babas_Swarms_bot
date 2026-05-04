"""Web search tool using DuckDuckGo (no API key required)."""

import asyncio
import logging
import warnings
from typing import Any, Dict, List

logger = logging.getLogger(__name__)
warnings.filterwarnings(
    "ignore",
    message=r".*duckduckgo_search.*renamed to `ddgs`.*",
    category=RuntimeWarning,
)
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    module=r"duckduckgo_search.*",
)


async def search_web(query: str, max_results: int = 5) -> str:
    """Search the web and return formatted results.

    Uses DuckDuckGo via duckduckgo-search package — no API key required.
    Falls back gracefully if package not installed.
    Uses asyncio.to_thread() to avoid blocking the event loop.
    Includes 8-second timeout and retry with simplified query on failure.

    Wrapped in circuit breaker to fast-fail when the service is known-down.
    """
    try:
        from core.circuit_breaker import with_circuit

        async def _search() -> str:
            return await _search_raw(query, max_results)

        return await with_circuit("duckduckgo", _search(), failure_threshold=5, recovery_timeout=60.0)
    except Exception:
        # CircuitOpenError or any other error — try raw fallback
        return await _search_raw(query, max_results)


async def _search_raw(query: str, max_results: int = 5) -> str:
    """Core search implementation (no circuit breaker wrapper)."""
    try:
        try:
            from ddgs import DDGS  # type: ignore[import-not-found]
        except ImportError:
            from ddgs import DDGS

        def _sync_search(q: str) -> list[dict[str, Any]]:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with DDGS() as ddgs:
                    return list(ddgs.text(q, max_results=max_results))

        # Run sync search in thread pool to avoid blocking event loop
        results = await asyncio.wait_for(
            asyncio.to_thread(_sync_search, query),
            timeout=8.0,
        )

        if not results:
            return f"Tidak ada hasil untuk: {query}"

        formatted = []
        for i, r in enumerate(results[:max_results], 1):
            formatted.append(
                f"{i}. **{r.get('title', 'No title')}**\n"
                f"   {r.get('body', 'No snippet')[:200]}...\n"
                f"   Source: {r.get('href', '')}"
            )

        return "## WEB SEARCH\n" + "\n\n".join(formatted)

    except TimeoutError:
        # Try once more with simplified query
        simplified = " ".join(query.split()[:5])
        if simplified != query:
            logger.info("Search timeout, retrying with simplified query: %s", simplified)
            try:
                try:
                    from ddgs import DDGS  # type: ignore[import-not-found]
                except ImportError:
                    from ddgs import DDGS

                def _sync_search(q: str) -> list[dict[str, Any]]:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", RuntimeWarning)
                        with DDGS() as ddgs:
                            return list(ddgs.text(q, max_results=max_results))

                results = await asyncio.wait_for(
                    asyncio.to_thread(_sync_search, simplified),
                    timeout=8.0,
                )

                if not results:
                    return f"Tidak ada hasil untuk: {query}"

                formatted = []
                for i, r in enumerate(results[:max_results], 1):
                    formatted.append(
                        f"{i}. **{r.get('title', 'No title')}**\n"
                        f"   {r.get('body', 'No snippet')[:200]}...\n"
                        f"   Source: {r.get('href', '')}"
                    )

                return "## WEB SEARCH\n" + "\n\n".join(formatted)
            except Exception:
                return "[Search timeout dan retry gagal: server tidak merespon]"
        return "[Search timeout: server terlalu lambat, coba lagi nanti]"
    except ImportError:
        logger.warning("DDGS not installed — web search unavailable")
        return "[Web search tidak tersedia: install ddgs]"
    except Exception:
        return "[Search error: gagal mengambil hasil, coba lagi nanti]"
