#!/usr/bin/env python3
"""
Run this at the END of every OpenCode session.

Usage:
  python scripts/opencode_session_end.py
  # Then type/paste your summary, press Ctrl+D when done

  python scripts/opencode_session_end.py --auto
  # Auto-generates session summary from available metadata
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory.store import MemoryStore

store = MemoryStore()


def auto_summary() -> str:
    """Generate a session summary from available metadata."""
    parts = ["OpenCode session summary"]

    # Session info
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts.append(f"Session time: {now}")

    # Git info if available
    try:
        import subprocess
        git_status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5,
            cwd=Path(__file__).parent.parent,
        )
        if git_status.stdout.strip():
            files = git_status.stdout.strip().split("\n")[:5]
            parts.append(f"Files changed ({len(files)}): {', '.join(f.split()[1] if len(f.split()) > 1 else f for f in files[:3])}")
    except Exception:
        pass

    # Check for session context
    ctx_file = Path("/tmp/legion_session_context.txt")
    if ctx_file.exists():
        try:
            ctx = ctx_file.read_text()[:200]
            if ctx.strip():
                parts.append(f"Session context: {ctx.strip()[:150]}")
        except Exception:
            pass

    return ". ".join(parts)


def main():
    content: str | None = None

    if "--auto" in sys.argv or "--quiet" in sys.argv:
        content = auto_summary()
        print(f"📝 Auto-generated summary: {content[:100]}...")
    else:
        print("📝 Enter session summary (what was accomplished, decisions made, bugs found, code written).")
        print("   Press Ctrl+D when done:\n")
        try:
            content = sys.stdin.read().strip()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)

    if not content or len(content) < 10:
        print("Summary too short, not stored.")
        sys.exit(0)

    n = store.remember(
        content=content,
        agent_id="opencode",
        memory_type="episodic",
        importance=1.5,
    )

    print(f"\n✅ Stored {n} memory chunk(s) from this session.")
    print(f"   Total memories: {store.count()}")
    print("   These will be recalled automatically in future sessions.")


if __name__ == "__main__":
    main()
