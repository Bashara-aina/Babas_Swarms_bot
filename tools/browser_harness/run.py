"""browser-harness CLI entry point."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add tools directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.browser_harness import helpers  # noqa: F401  — pre-import helpers into globals
from tools.browser_harness.admin import (
    _version,
    ensure_daemon,
    list_cloud_profiles,
    list_local_profiles,
    print_update_banner,
    restart_daemon,
    run_doctor,
    run_setup,
    run_update,
    start_remote_daemon,
    stop_remote_daemon,
    sync_local_profile,
)

HELP = """Browser Harness

Read tools/browser_harness/SKILL.md for the default workflow and examples.

Typical usage:
  browser-harness -c "print(page_info())"

Helpers are pre-imported. The daemon auto-starts and connects to the running browser.

Commands:
  browser-harness --version        print the installed version
  browser-harness --doctor         diagnose install, daemon, and browser state
  browser-harness --setup          interactively attach to your running browser
  browser-harness --update [-y]    pull the latest version (agents: pass -y)
  browser-harness --reload         stop the daemon so next call picks up code changes
"""


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print(HELP)
        return
    if args[0] == "--version":
        print(_version() or "unknown")
        return
    if args[0] == "--doctor":
        sys.exit(run_doctor())
    if args[0] == "--setup":
        sys.exit(run_setup())
    if args[0] == "--update":
        yes = any(a in {"-y", "--yes"} for a in args[1:])
        sys.exit(run_update(yes=yes))
    if args[0] == "--reload":
        restart_daemon()
        print("daemon stopped — will restart fresh on next call")
        return
    if args[0] == "--debug-clicks":
        os.environ["BH_DEBUG_CLICKS"] = "1"
        args = args[1:]
    if not args or args[0] != "-c" or len(args) < 2:
        sys.exit("Usage: browser-harness -c \"print(page_info())\"")
    print_update_banner()
    ensure_daemon()
    exec(args[1], {"__name__": "__main__", **vars(helpers)})  # noqa: S307 — user-provided code


if __name__ == "__main__":
    main()
