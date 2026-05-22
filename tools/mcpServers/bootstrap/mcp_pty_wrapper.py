#!/usr/bin/env python3
"""PTY-based MCP server wrapper: handles TTY-needed servers, strips echoed requests."""
import sys
import os
import pty
import select
import signal
import threading

def main():
    if len(sys.argv) < 2:
        print("Usage: mcp_pty_wrapper.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1:]
    master_fd, slave_fd = pty.openpty()

    # Lock for thread-safe echo tracking
    sent_requests = []
    lock = threading.Lock()

    pid = os.fork()
    if pid == 0:
        # Child
        os.close(master_fd)
        os.setsid()
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        os.close(slave_fd)
        os.execvp(cmd[0], cmd)
    else:
        # Parent
        os.close(slave_fd)

        def is_echo_request(line, sent_list):
            """Return True if line is a request we sent (server echoed it back)."""
            try:
                import json
                if not line.strip().startswith('{'):
                    return False
                d = json.loads(line.strip())
                # It's an echo if: has id, has method, has params, and matches a sent request
                if d.get('id') is not None and d.get('method') and d.get('params') is not None:
                    for sent in sent_list:
                        if sent.get('id') == d.get('id') and sent.get('method') == d.get('method'):
                            return True
            except:
                pass
            return False

        def cleanup():
            try:
                os.close(master_fd)
            except:
                pass
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                pass
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass  # Already reaped

        signal.signal(signal.SIGTERM, lambda s, f: cleanup())

        # Thread to forward stdin -> master (non-blocking)
        def pump_stdin():
            try:
                while True:
                    r, _, _ = select.select([sys.stdin], [], [], 0.5)
                    if r:
                        chunk = os.read(sys.stdin.fileno(), 4096)
                        if not chunk:
                            break
                        # Track sent JSON-RPC requests for echo filtering
                        try:
                            text = chunk.decode('utf-8', errors='replace')
                            for line in text.split('\n'):
                                line = line.strip()
                                if line.startswith('{'):
                                    import json
                                    try:
                                        d = json.loads(line)
                                        # Only track requests (has method, has id)
                                        if 'method' in d and 'id' in d:
                                            with lock:
                                                sent_requests.append(d)
                                    except:
                                        pass
                        except:
                            pass
                        os.write(master_fd, chunk)
            except:
                pass

        pump_thread = threading.Thread(target=pump_stdin, daemon=True)
        pump_thread.start()

        while True:
            try:
                r, _, _ = select.select([master_fd], [], [], 0.5)
                if not r:
                    continue

                wpid = os.waitpid(pid, os.WNOHANG)
                if wpid[0] != 0:
                    break

                for fd in r:
                    if fd == master_fd:
                        try:
                            chunk = os.read(master_fd, 4096)
                            if chunk:
                                text = chunk.decode('utf-8', errors='replace')
                                with lock:
                                    # Filter out echoed requests
                                    for line in text.split('\n'):
                                        line_stripped = line.strip()
                                        if line_stripped.startswith('{'):
                                            # Check if this is an echo we should drop
                                            should_drop = False
                                            try:
                                                import json
                                                d = json.loads(line_stripped)
                                                if d.get('id') is not None and d.get('method') and d.get('params') is not None:
                                                    for sent in sent_requests:
                                                        if sent.get('id') == d.get('id') and sent.get('method') == d.get('method'):
                                                            # It's echoed - remove from tracking and drop
                                                            sent_requests.remove(sent)
                                                            should_drop = True
                                                            break
                                            except:
                                                pass
                                            if not should_drop:
                                                os.write(1, (line + '\n').encode('utf-8'))
                                        elif line_stripped:
                                            os.write(1, (line + '\n').encode('utf-8'))
                                # Write raw chunk for non-JSON lines
                                # (above writes individual lines, below for binary data)
                        except OSError:
                            break
            except KeyboardInterrupt:
                break

        cleanup()

if __name__ == "__main__":
    main()