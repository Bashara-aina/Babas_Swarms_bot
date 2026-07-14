#!/usr/bin/env python3
"""ref_read MCP server — retrieves offloaded tool outputs on demand.
Part of the TencentDB Agent Memory concept for Claude Code.
"""
from __future__ import annotations
import os, json, glob
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool
import mcp.server.stdio

REFS_DIR = os.path.expanduser("~/.claude-flow/refs")
server = Server("ref_read")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="ref_read",
            description="Retrieve previously-offloaded tool output by reference ID. Use when a tool result preview isn't enough. The ref_id is shown in brackets like [ref_abc123] in the conversation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref_id": {
                        "type": "string",
                        "description": "Reference ID from the offloaded content, e.g. ref_abc123 (without brackets)",
                    }
                },
                "required": ["ref_id"],
            },
        ),
        Tool(
            name="ref_list",
            description="List all available offloaded references with their metadata. Use to discover what's available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Optional filter by tool name (bash, read, grep, etc.)",
                    }
                },
            },
        ),
        Tool(
            name="ref_stats",
            description="Show stats about the offloaded context store",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "ref_read":
        ref_id = arguments.get("ref_id", "").strip()
        if not ref_id:
            return [TextContent(type="text", text="Error: ref_id is required")]
        if not ref_id.startswith("ref_"):
            ref_id = f"ref_{ref_id}"

        # Find the file
        for fname in os.listdir(REFS_DIR):
            if fname.startswith(ref_id) and fname.endswith(".md"):
                path = os.path.join(REFS_DIR, fname)
                with open(path) as f:
                    content = f.read()
                # Return only the content after the --- marker
                if "---\n" in content:
                    content = content.split("---\n", 1)[1]
                return [TextContent(type="text", text=content)]

        return [TextContent(type="text", text=f"Error: ref_id '{ref_id}' not found")]

    elif name == "ref_list":
        tool_filter = arguments.get("tool_name", "").strip().lower()
        results = []
        for fname in sorted(os.listdir(REFS_DIR)):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(REFS_DIR, fname)
            with open(path) as f:
                header = f.read(500)
            metadata = {}
            for line in header.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
            ref_id = fname.replace(".md", "")
            tool_n = metadata.get("tool", "?")
            if tool_filter and tool_filter not in tool_n.lower():
                continue
            size = metadata.get("content_size", "?")
            stored = metadata.get("stored", "?")
            results.append(f"  {ref_id:30s} tool={tool_n:12s} size={size:>8s}  stored={stored}")

        if not results:
            return [TextContent(type="text", text="No offloaded references found.")]
        return [TextContent(type="text", text=f"Available references:\n" + "\n".join(results))]

    elif name == "ref_stats":
        total = len([f for f in os.listdir(REFS_DIR) if f.endswith(".md")])
        total_size = sum(os.path.getsize(os.path.join(REFS_DIR, f)) for f in os.listdir(REFS_DIR) if f.endswith(".md"))
        return [TextContent(type="text", text=f"Context Store Stats:\n  Total refs: {total}\n  Total size: {total_size:,} bytes\n  Refs dir: {REFS_DIR}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            InitializationOptions(
                server_name="ref_read",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
