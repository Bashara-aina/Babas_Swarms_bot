"""Resilient HTTP client with DNS failover for rumahlabuh tools.

Provides an async context manager that wraps aiohttp ClientSession with
DNS-resilient TCPConnector using Cloudflare (1.1.1.1) and Google (8.8.8.8)
DNS servers, with graceful fallback to the system resolver.
"""

from __future__ import annotations

import logging
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aiodns
import aiohttp

logger = logging.getLogger(__name__)

# Cloudflare and Google DNS servers for resilient lookups
RESILIENT_DNS_SERVERS = ("1.1.1.1", "8.8.8.8")


@asynccontextmanager
async def get_resilient_session(
    timeout: aiohttp.ClientTimeout | float = aiohttp.ClientTimeout(total=30),
    dns_servers: tuple[str, ...] = RESILIENT_DNS_SERVERS,
    **session_kwargs: Any,
) -> AsyncIterator[aiohttp.ClientSession]:
    """Return an aiohttp ClientSession with DNS-resilient TCPConnector.

    The connector uses AF_UNSPEC (both IPv4 and IPv6) and enables DNS caching.
    If the custom DNS resolver fails, it falls back to the system resolver
    silently.

    Args:
        timeout: ClientTimeout or total seconds for requests.
        dns_servers: Tuple of DNS server addresses to use.
        **session_kwargs: Additional arguments passed to ClientSession.

    Yields:
        An aiohttp ClientSession instance.

    Example:
        async with get_resilient_session() as session:
            async with session.get("https://rumahlabuh.com") as resp:
                print(resp.status)
    """
    connector: aiohttp.TCPConnector | None = None
    resolver: aiohttp.resolver.AbstractResolver | None = None

    try:
        # Use AsyncResolver with aiodns backend and custom DNS servers
        resolver = aiohttp.resolver.AsyncResolver(
            nameservers=dns_servers,
        )
        connector = aiohttp.TCPConnector(
            family=socket.AF_UNSPEC,
            use_dns_cache=True,
            resolver=resolver,
        )
    except (OSError, aiohttp.ClientError) as e:
        # Graceful fallback: create connector without custom resolver
        logger.warning(
            "Failed to configure custom DNS resolver (%s): %s. Falling back to system resolver.",
            dns_servers,
            e,
        )
        connector = aiohttp.TCPConnector(
            family=socket.AF_UNSPEC,
            use_dns_cache=True,
        )

    timeout_val = timeout if isinstance(timeout, aiohttp.ClientTimeout) else aiohttp.ClientTimeout(total=timeout)

    try:
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_val,
            **session_kwargs,
        ) as session:
            yield session
    finally:
        # Explicitly close resolver if we created one (async method)
        if resolver is not None and hasattr(resolver, "close"):
            await resolver.close()
