#!/usr/bin/env python3
"""MCP server wrapping the graphify CLI for OpenCode/Claude Code."""
from __future__ import annotations
import json, subprocess, sys, os
from typing import Any

GRAPHIFY_BIN = "/home/newadmin/.local/bin/graphify"
GRAPH_PATH = "/home/newadmin/swarm-bot/graphify-out/graph.json"

def run_graphify(args: list[str], timeout=30) -> str:
    try:
        result = subprocess.run(
            [GRAPHIFY_BIN] + args,
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PATH": "/home/newadmin/miniconda3/bin:" + os.environ.get("PATH", "")}
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error: {e}"

# Simple MCP server over stdin/stdout
def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    params = request.get("params", {})
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "graphify", "version": "1.0"}
            }
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "graphify_query",
                        "description": "Search the code knowledge graph with BFS traversal",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language question"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "graphify_explain",
                        "description": "Plain-language explanation of a concept/node in the graph",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Node/concept name"}
                            },
                            "required": ["name"]
                        }
                    },
                    {
                        "name": "graphify_path",
                        "description": "Find shortest path between two nodes in the graph",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"}
                            },
                            "required": ["source", "target"]
                        }
                    }
                ]
            }
        }
    elif method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        if tool == "graphify_query":
            output = run_graphify(["query", args.get("query", ""), "--graph", GRAPH_PATH])
        elif tool == "graphify_explain":
            output = run_graphify(["explain", args.get("name", ""), "--graph", GRAPH_PATH])
        elif tool == "graphify_path":
            output = run_graphify(["path", args.get("source", ""), args.get("target", ""), "--graph", GRAPH_PATH])
        else:
            output = f"Unknown tool: {tool}"
        return {
            "jsonrpc": "2.0", "id": request.get("id"),
            "result": {"content": [{"type": "text", "text": output}]}
        }
    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0"}
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}

if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
