#!/usr/bin/env python3
"""Claude Code command: threads-mode.

Examples:
  threads-mode status
  threads-mode on
  threads-mode off
  threads-mode toggle
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "threads_mode.py"
    cmd = [sys.executable, str(script), *sys.argv[1:]]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
