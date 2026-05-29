#!/usr/bin/env python3
"""
ClaudeCode MCP Bridge — exposes Claude Code as an MCP tool server.
Enables Hermes to call Claude Code with full tool access via MCP protocol.
"""
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

VERSION = "1.0.0"
CLAUDE_BIN = "/home/newadmin/.local/bin/claude"
WORKSPACE = "/home/newadmin/swarm-bot"

TOOLS = [
    {
        "name": "claude_code_task",
        "description": "Execute a coding task using Claude Code CLI. Sends a prompt to Claude Code and returns the result. Use for building features, refactoring, code reviews, and iterative coding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The coding task or instruction for Claude Code"
                },
                "workspace": {
                    "type": "string",
                    "description": "Working directory for Claude Code (default: /home/newadmin/swarm-bot)",
                    "default": "/home/newadmin/swarm-bot"
                },
                "allowed_tools": {
                    "type": "string",
                    "description": "Comma-separated list of allowed tools (default: Read,Edit,Bash,Notebook,WebSearch)",
                    "default": "Read,Edit,Bash,Notebook,WebSearch"
                },
                "max_turns": {
                    "type": "integer",
                    "description": "Maximum conversation turns (default: 30)",
                    "default": 30
                },
                "model": {
                    "type": "string",
                    "description": "Model to use (default: MiniMax-M2.7 via MINIMAX_API_KEY)",
                    "default": ""
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format: text, json, stream-json (default: json)",
                    "default": "json",
                    "enum": ["text", "json", "stream-json"]
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "claude_code_read",
        "description": "Read and analyze files using Claude Code. Returns file contents and analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "string",
                    "description": "Space-separated list of file paths to read"
                },
                "workspace": {
                    "type": "string",
                    "description": "Working directory",
                    "default": "/home/newadmin/swarm-bot"
                },
                "include_errors": {
                    "type": "boolean",
                    "description": "Include error analysis",
                    "default": True
                }
            },
            "required": ["files"]
        }
    },
    {
        "name": "claude_code_search",
        "description": "Search code using Claude Code's grep and context understanding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "workspace": {
                    "type": "string",
                    "description": "Working directory",
                    "default": "/home/newadmin/swarm-bot"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "File pattern to search (e.g., '*.py')",
                    "default": "*.py"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "claude_code_git",
        "description": "Run git operations via Claude Code.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Git command to run (e.g., 'status', 'log --oneline -10', 'diff HEAD~1')"
                },
                "workspace": {
                    "type": "string",
                    "description": "Working directory",
                    "default": "/home/newadmin/swarm-bot"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "claude_code_agent",
        "description": "Run Claude Code in agent mode for autonomous multi-step tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "High-level task description"
                },
                "workspace": {
                    "type": "string",
                    "description": "Working directory",
                    "default": "/home/newadmin/swarm-bot"
                },
                "agent_type": {
                    "type": "string",
                    "description": "Agent type: coder, reviewer, architect (default: coder)",
                    "default": "coder"
                },
                "max_time": {
                    "type": "integer",
                    "description": "Maximum time in seconds (default: 300)",
                    "default": 300
                }
            },
            "required": ["task"]
        }
    }
]


def run_claude(args: List[str], timeout: int = 120) -> Dict[str, Any]:
    """Run Claude CLI and return parsed output."""
    try:
        result = subprocess.run(
            [CLAUDE_BIN] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE,
            env={
                **os.environ.copy(),
                "CLAUDE_CODE_SIMPLE": "1",
                "ANTHROPIC_API_KEY": os.environ.get("MINIMAX_API_KEY", ""),
            }
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "stdout": "", "stderr": "Command timed out", "returncode": -1, "success": False}
    except Exception as e:
        return {"error": str(e), "stdout": "", "stderr": str(e), "returncode": -1, "success": False}


def handle_initialize() -> Dict[str, Any]:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "claude-code-bridge", "version": VERSION}
    }


def handle_list_tools() -> Dict[str, Any]:
    return {"tools": TOOLS}


def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    workspace = arguments.get("workspace", WORKSPACE)
    output_format = arguments.get("output_format", "json")

    if name == "claude_code_task":
        prompt = arguments["prompt"]
        allowed_tools = arguments.get("allowed_tools", "Read,Edit,Bash,Notebook,WebSearch")
        max_turns = arguments.get("max_turns", 30)

        cmd = [
            "-p", prompt,
            "--output-format", output_format,
            "--allowedTools", allowed_tools,
            "--max-turns", str(max_turns),
            "--no-session-persistence"
        ]

        model = arguments.get("model", "")
        if model:
            cmd.extend(["--model", model])

        result = run_claude(cmd, timeout=180)
        return result

    elif name == "claude_code_read":
        files = arguments["files"]
        include_errors = arguments.get("include_errors", True)

        prompt = f"Read and analyze these files: {files}. "
        if include_errors:
            prompt += "Check for errors, TODOs, and code quality issues."
        else:
            prompt += "Provide a summary of each file's contents."

        cmd = ["-p", prompt, "--output-format", output_format, "--no-session-persistence"]
        return run_claude(cmd, timeout=60)

    elif name == "claude_code_search":
        query = arguments["query"]
        file_pattern = arguments.get("file_pattern", "*.py")

        prompt = f"Search the codebase for: '{query}' in files matching '{file_pattern}'. Use grep and read relevant files to find matches. Report what you find with file paths and line numbers."
        cmd = ["-p", prompt, "--output-format", output_format, "--no-session-persistence"]
        return run_claude(cmd, timeout=60)

    elif name == "claude_code_git":
        command = arguments["command"]
        prompt = f"Run this git command and explain the output: git {command}"
        cmd = ["-p", prompt, "--output-format", output_format, "--no-session-persistence"]
        return run_claude(cmd, timeout=30)

    elif name == "claude_code_agent":
        task = arguments["task"]
        agent_type = arguments.get("agent_type", "coder")
        max_time = arguments.get("max_time", 300)

        prompt = f"You are a {agent_type}. {task}. Work autonomously until complete. Use appropriate tools, run tests, and commit your changes."
        cmd = ["-p", prompt, "--agent", agent_type, "--output-format", output_format, "--no-session-persistence"]
        return run_claude(cmd, timeout=max_time)

    else:
        return {"error": f"Unknown tool: {name}", "success": False}


def handle_jsonrpc(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = message.get("method", "")
    msg_id = message.get("id")

    if method == "initialize":
        result = handle_initialize()
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    elif method == "tools/list":
        result = handle_list_tools()
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    elif method == "tools/call":
        name = message.get("params", {}).get("name", "")
        arguments = message.get("params", {}).get("arguments", {})
        result = handle_call_tool(name, arguments)
        # Return in MCP tool response format
        if result.get("success"):
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": result.get("stdout", result.get("stderr", ""))}]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": result.get("stderr", result.get("error", "Unknown error"))}
            }

    return None


def main():
    # Skip banner lines until JSON-RPC begins
    for line in sys.stdin:
        line = line.strip()
        if line.startswith("{"):
            msg = json.loads(line)
            resp = handle_jsonrpc(msg)
            if resp:
                print(json.dumps(resp), flush=True)
            break

    # Process rest of messages
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            resp = handle_jsonrpc(msg)
            if resp:
                print(json.dumps(resp), flush=True)
        except json.JSONDecodeError:
            pass


if __name__ == "__main__":
    main()