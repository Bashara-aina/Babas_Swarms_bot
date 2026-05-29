#!/usr/bin/env python3
"""Obsidian MCP stdio filter — strips startup spam so MCP Python SDK gets clean JSON-RPC.

node prints dotenvx startup messages to stdout (fd 1). We intercept node's stdout
and only pass through lines that look like JSON-RPC. stdin is forwarded unchanged.
"""

import sys
import os


def main():
    node_bin = os.environ.get("OBSIDIAN_NODE", "/home/newadmin/.local/node18/bin/node")
    script = os.environ.get("OBSIDIAN_SCRIPT", "/home/newadmin/swarm-bot/mcp_servers/obsidian-patched/index.js")

    import subprocess
    proc = subprocess.Popen(
        [node_bin, script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env={**os.environ},
    )

    import threading
    stderr_drained = []

    def drain_stderr():
        try:
            while True:
                chunk = proc.stderr.read(4096)
                if not chunk:
                    break
        except Exception:
            pass

    t = threading.Thread(target=drain_stderr, daemon=True)
    t.start()

    # Stream filtering: node stdout → filter → our stdout
    buf = b""
    while True:
        chunk = proc.stdout.read(4096)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            decoded = line.decode().strip()
            if decoded.startswith("{"):
                sys.stdout.write(decoded + "\n")
                sys.stdout.flush()

    proc.wait()


if __name__ == "__main__":
    main()