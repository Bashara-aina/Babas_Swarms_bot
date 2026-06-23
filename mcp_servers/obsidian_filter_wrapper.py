#!/usr/bin/env python3
"""
Obsidian MCP filter wrapper — strips startup spam from node's stdout
so the MCP Python SDK only sees clean JSON-RPC.

Usage: python3 obsidian_filter_wrapper.py <node_binary> <script> [args...]
"""

import sys
import os
import subprocess
import selectors


def main():
    if len(sys.argv) < 2:
        print("Usage: obsidian_filter_wrapper.py <node_binary> <script> [args...]", file=sys.stderr)
        sys.exit(1)

    node_bin = sys.argv[1]
    args = sys.argv[2:]

    env = {**os.environ}
    env["DOTENV_CONFIG_QUIET"] = "true"
    env["DOTENV_CONFIG_DEBUG"] = "false"

    proc = subprocess.Popen(
        [node_bin] + args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    # Discard stderr asynchronously
    import threading

    def discard_stderr():
        try:
            while proc.stderr:
                chunk = proc.stderr.read(4096)
                if not chunk:
                    break
        except Exception:
            pass

    stderr_thread = threading.Thread(target=discard_stderr, daemon=True)
    stderr_thread.start()

    stdout = proc.stdout
    if stdout is None:
        sys.exit(1)

    # Use a selector to watch both stdout and stdin simultaneously
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    selector.register(sys.stdin, selectors.EVENT_READ)

    buf = b""

    while True:
        events = selector.select(timeout=30)
        if not events:
            continue  # timeout, keep polling

        for key, _ in events:
            if key.fileobj == proc.stdout:
                chunk = stdout.read(4096)
                if not chunk:
                    selector.unregister(proc.stdout)
                    break
                buf += chunk
                # Flush complete lines
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    decoded = line.decode().strip()
                    if decoded.startswith("{"):
                        sys.stdout.write(decoded + "\n")
                        sys.stdout.flush()
                # If no newline yet, keep buffering
            elif key.fileobj == sys.stdin:
                chunk = sys.stdin.read(4096)
                if not chunk:
                    proc.stdin.close()
                    selector.unregister(sys.stdin)
                else:
                    proc.stdin.write(chunk.encode())
                    proc.stdin.flush()

    proc.wait()


if __name__ == "__main__":
    main()
