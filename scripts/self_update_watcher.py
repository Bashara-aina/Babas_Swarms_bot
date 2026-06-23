#!/usr/bin/env python3
"""
Poll git remote; print whether local main is behind origin.

Optional notify: set TELEGRAM_BOT_TOKEN + ALLOWED_USER_ID and SELF_UPDATE_NOTIFY=1
to send a short Telegram message when behind.
"""

from __future__ import annotations

import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> str:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    return (p.stdout or "").strip()


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    fetch = _run(["git", "fetch", "origin"], root)
    if "fatal" in fetch.lower():
        print(fetch or "git fetch failed")
    behind = _run(
        ["git", "rev-list", "HEAD..origin/main", "--count"],
        root,
    )
    try:
        n = int(behind)
    except ValueError:
        n = -1
    print(f"Commits behind origin/main: {n}")
    if n > 0 and os.getenv("SELF_UPDATE_NOTIFY", "0").strip() in ("1", "true", "yes"):
        token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        uid = (os.getenv("ALLOWED_USER_ID") or "").strip()
        if token and uid:
            text = urllib.parse.quote(f"Legion: repo is {n} commit(s) behind origin/main.")
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={uid}&text={text}"
            try:
                urllib.request.urlopen(url, timeout=15).read()
            except Exception as exc:
                print("notify failed:", exc)
    return 0 if n >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
