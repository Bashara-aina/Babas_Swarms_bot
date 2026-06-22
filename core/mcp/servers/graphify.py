"""Graphify MCP server configuration.

Graphify exposes a knowledge graph over the codebase (graphify-out/graph.json)
as MCP tools. The server itself is implemented in the `graphifyy` PyPI package
(uv-tool install path) and started as a stdio MCP server via:

    python -m graphify.serve <graph.json>

The graph.json file is produced by either `/graphify` slash command
(full pipeline) or `graphify update . --no-cluster` (AST-only, no LLM).
"""

from __future__ import annotations

import os
from pathlib import Path


# Resolved at import time so the router can hot-swap the interpreter if needed.
_GRAPHIFY_PY = "/home/newadmin/.local/share/uv/tools/graphifyy/bin/python"
_GRAPH_JSON = "/home/newadmin/swarm-bot/graphify-out/graph.json"


def command() -> list[str]:
    """Return the command to start the Graphify MCP stdio server.

    Uses the uv-tool interpreter directly (not python3 on PATH) because the
    miniconda python3 does not see the `graphifyy` package's site-packages.
    """
    return [_GRAPHIFY_PY, "-m", "graphify.serve", _GRAPH_JSON]


def is_available() -> bool:
    """Check if the Graphify MCP server is available.

    Requirements:
      1. uv-tool interpreter exists at _GRAPHIFY_PY.
      2. `graphifyy` package is importable from that interpreter.
      3. The graph.json file exists (built by `/graphify` or `graphify update`).
    """
    if not os.path.exists(_GRAPHIFY_PY):
        return False
    try:
        import subprocess
        result = subprocess.run(
            [_GRAPHIFY_PY, "-c", "import graphify"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return False
    except (subprocess.TimeoutExpired, OSError):
        return False
    # The graph.json file is a soft requirement: the server itself can start
    # even without it (it just returns empty results). Report availability
    # based on the binary + package, not the data file, so the user gets
    # a clear error from the tool calls instead of a hidden absence.
    return True
