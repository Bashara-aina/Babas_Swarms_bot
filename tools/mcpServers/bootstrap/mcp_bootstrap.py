#!/usr/bin/env python3
"""MCP Bootstrap - Filters npx/npm startup messages from MCP servers.

This wrapper solves the problem where npx-based servers print startup messages
to stdout before the JSON-RPC protocol begins, breaking Python's MCP client.

Usage as command:
    python3 /path/to/mcp_bootstrap.py <npx_command> [args...]

For filesystem server:
    python3 mcp_bootstrap.py npx -y @modelcontextprotocol/server-filesystem /home/newadmin

For sequential-thinking:
    python3 mcp_bootstrap.py npx -y @modelcontextprotocol/server-sequential-thinking
"""

import asyncio
import sys
import os
import os.path


async def run_bootstrap():
    if len(sys.argv) < 2:
        print("Usage: mcp_bootstrap.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]  # noqa: F841 -- preserved for clarity; args below is the used subset
    args = sys.argv[1:]  # includes cmd itself

    # Determine which npx command to use
    npx_bin = "/home/newadmin/.local/node18/bin/npx"

    proc = await asyncio.create_subprocess_exec(
        npx_bin, *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ}
    )

    # Filter stdout - skip non-JSON lines until we hit JSON-RPC
    async def pump_out():
        while True:
            try:
                line = await proc.stdout.readline()
            except Exception:
                break
            if not line:
                # EOF
                break
            decoded = line.decode().strip()
            # Skip lines that don't look like JSON-RPC
            if decoded.startswith('{'):
                # First JSON-RPC message - write to real stdout
                sys.stdout.write(decoded + '\n')
                sys.stdout.flush()
                break
            # Otherwise skip (startup message)
        # Pump remaining stdout directly to our stdout
        try:
            while True:
                data = await proc.stdout.read(8192)
                if not data:
                    break
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
        except Exception:
            pass

    async def pump_err():
        # Forward stderr (for debugging)
        try:
            while True:
                data = await proc.stderr.read(8192)
                if not data:
                    break
                sys.stderr.buffer.write(data)
                sys.stderr.buffer.flush()
        except Exception:
            pass

    async def pump_in():
        # Forward stdin to server
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    proc.stdin.close()
                    break
                proc.stdin.write(line.encode())
                await proc.stdin.drain()
        except Exception:
            pass

    await asyncio.gather(
        asyncio.create_task(pump_out()),
        asyncio.create_task(pump_err()),
        asyncio.create_task(pump_in()),
    )


if __name__ == "__main__":
    asyncio.run(run_bootstrap())