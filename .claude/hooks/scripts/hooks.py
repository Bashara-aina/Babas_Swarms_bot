#!/usr/bin/env python3
"""
Claude Code PostToolUse Hook Script
Automatically runs gitnexus analyze after git commit and git merge events.
Preserves existing embeddings when analyzing.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


def log(level: str, message: str, **kwargs):
    """Log with timestamp and level."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        **kwargs
    }
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)
    if kwargs:
        print(f"  Context: {kwargs}", file=sys.stderr)


def run_gitnexus_analyze():
    """
    Run npx gitnexus analyze --embeddings to update the code knowledge graph.
    Preserves existing embeddings if present.
    """
    try:
        log("INFO", "Running gitnexus analyze to update code knowledge graph...")

        result = subprocess.run(
            ["npx", "gitnexus", "analyze", "--embeddings"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for analyze
        )

        if result.returncode == 0:
            log("INFO", "gitnexus analyze completed successfully")
            if result.stdout:
                for line in result.stdout.strip().split('\n')[:5]:  # First 5 lines
                    log("DEBUG", f"gitnexus: {line}")
            return True
        else:
            log("WARNING", f"gitnexus analyze failed with code {result.returncode}")
            if result.stderr:
                for line in result.stderr.strip().split('\n')[:5]:
                    log("DEBUG", f"gitnexus error: {line}")
            return False

    except subprocess.TimeoutExpired:
        log("WARNING", "gitnexus analyze timed out after 120 seconds")
        return False
    except FileNotFoundError:
        log("WARNING", "npx not found - gitnexus may not be installed")
        return False
    except Exception as e:
        log("ERROR", f"Failed to run gitnexus analyze: {e}")
        return False


def detect_git_operation(input_data: dict) -> bool:
    """
    Detect if the tool call was a git commit or git merge.
    Returns True if we should run gitnexus analyze.
    """
    # Check if this is a Bash tool call
    tool_name = input_data.get("tool", "")

    # The hook receives tool_use_context with the tool that was used
    # For PostToolUse, we get the tool name and arguments
    if tool_name != "Bash":
        return False

    # Get the command that was executed
    args = input_data.get("args", {})
    command = args.get("command", "")

    if not command:
        return False

    # Check for git commit or git merge operations
    # git commit can be: git commit, git commit -m "...", git commit -am "..."
    # git merge can be: git merge, git merge --no-ff, etc.
    command_lower = command.lower().strip()

    is_commit = (
        command_lower.startswith("git commit") or
        "git commit" in command_lower
    )
    is_merge = (
        command_lower.startswith("git merge") or
        "git merge" in command_lower
    )

    if is_commit or is_merge:
        log("INFO", f"Detected git operation: {'commit' if is_commit else 'merge'}")
        log("DEBUG", f"Command: {command[:100]}...")
        return True

    return False


def parse_stdin_input() -> dict:
    """Parse the JSON input from stdin."""
    try:
        # Read all input from stdin
        input_text = sys.stdin.read()
        if not input_text:
            return {}

        # Claude Code hook input is JSON
        return json.loads(input_text)
    except json.JSONDecodeError as e:
        log("WARNING", f"Failed to parse stdin JSON: {e}")
        return {}
    except Exception as e:
        log("WARNING", f"Error reading stdin: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="Claude Code PostToolUse Hook Script")
    parser.add_argument("--event", type=str, help="Event type (e.g., PostToolUse)")
    parser.add_argument("--agent", type=str, default="default", help="Agent name")
    args = parser.parse_args()

    timestamp = datetime.now().isoformat()
    log("DEBUG", f"Hook fired: event={args.event}, agent={args.agent}")

    # Parse the hook input from stdin
    hook_input = parse_stdin_input()

    # Detect git operations
    if detect_git_operation(hook_input):
        log("INFO", "Git operation detected - running gitnexus analyze...")
        success = run_gitnexus_analyze()
        if success:
            log("INFO", "Post-git-operation gitnexus analyze completed")
        else:
            log("WARNING", "Post-git-operation gitnexus analyze failed (non-fatal)")
    else:
        log("DEBUG", "No git commit/merge detected - skipping gitnexus analyze")

    return 0


if __name__ == "__main__":
    sys.exit(main())