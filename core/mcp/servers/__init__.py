"""MCP server configurations package."""

from core.mcp.servers.brave import is_available as brave_available
from core.mcp.servers.browser import is_available as browser_available
from core.mcp.servers.filesystem import is_available as filesystem_available
from core.mcp.servers.github import is_available as github_available
from core.mcp.servers.gitnexus import is_available as gitnexus_available
from core.mcp.servers.obsidian import is_available as obsidian_available
from core.mcp.servers.supabase import is_available as supabase_available

__all__ = [
    "brave_available",
    "github_available",
    "filesystem_available",
    "gitnexus_available",
    "obsidian_available",
    "supabase_available",
    "browser_available",
]
