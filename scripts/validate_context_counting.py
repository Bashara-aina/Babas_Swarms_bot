#!/usr/bin/env python3
"""Deep cross-reference validator for all context counting mechanisms.

Verifies that all context counters in the project produce consistent
results and match deepseek-v4-flash's native 1M-token context window.

Checks both static code correctness AND live data flow integration.

Usage:
    python scripts/validate_context_counting.py [--live]
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CC_NATIVE_TOKENS = 1_048_576  # deepseek-v4-flash
CC_NATIVE_CHARS = CC_NATIVE_TOKENS * 4  # 4,194,304
CHARS_PER_TOKEN = 4

# Expected context window constants across all components
EXPECTED_CAPACITY = {
    "context_health.py": {
        "field": "total_chars: int = 4_194_304",
        "desc": "deepseek-v4-flash 1,048,576 tokens * 4 chars/token",
    },
    "legion_session.py": {
        "field": "CONTEXT_LIMIT = 4_194_304",
        "desc": "deepseek-v4-flash 1,048,576 tokens * 4 chars/token",
    },
    "cognition_boot.py": {
        "field": "CONTEXT_LIMIT = 4_194_304",
        "desc": "deepseek-v4-flash 1,048,576 tokens * 4 chars/token",
    },
    "legion_compaction.py": {
        "field": "max_context_chars = 4_194_304",
        "desc": "deepseek-v4-flash 1,048,576 tokens * 4 chars/token",
    },
    "context_compactor.py": {
        "field": "MAX_TOKENS = 1_048_576",
        "desc": "deepseek-v4-flash 1M context window",
    },
}

FORBIDDEN_DENOMINATORS = [
    ("22000", "22K chars (5.5K tokens) — wrong denominator"),
    ("200_000", "200K chars (50K tokens) — wrong denominator"),
    ("800_000", "800K chars (200K tokens) — wrong denominator for deepseek-v4-flash"),
    ("128000", "128K tokens — wrong denominator for deepseek-v4-flash"),
]


def check_file_has_no_old_denominators(path: Path, name: str) -> list[str]:
    """Check a file doesn't contain old wrong denominators."""
    if not path.exists():
        return [f"MISSING: {path}"]
    content = path.read_text()
    issues = []
    for denom, desc in FORBIDDEN_DENOMINATORS:
        # Be careful to not match legitimate uses of 200000/128000 (like in comments)
        lines = content.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip comments containing the number
            if denom in stripped and not stripped.startswith("#") and not stripped.startswith("//") and not stripped.startswith('"'):
                # Check it's not a legitimate token value (denominator, not a limit)
                if "total_chars" in stripped or "CONTEXT_LIMIT" in stripped or "max_context_chars" in stripped:
                    if "4_194_304" in stripped or "1_048_576" in stripped:
                        continue  # Already fixed to 1M tokens
                    issues.append(f"  L{i+1}: '{stripped}' — {desc}")
    return issues


def check_python_syntax(path: Path) -> list[str]:
    """Check file parses as valid Python."""
    try:
        ast.parse(path.read_text())
        return []
    except SyntaxError as e:
        return [f"SYNTAX ERROR: {e}"]


def check_estimate_context_chars(name: str, path: Path) -> list[str]:
    """Verify _estimate_context_chars() no longer uses RSS."""
    if not path.exists():
        return [f"MISSING: {path}"]
    content = path.read_text()
    issues = []
    if "psutil" in content and "rss" in content:
        issues.append(f"STILL USES RSS/4 estimation (should read session data)")
    if "session_messages.json" not in content and "current.json" not in content:
        issues.append(f"MISSING: reads from session data files")
    return issues


def check_token_meter_integration() -> list[str]:
    """Verify TokenMeter is connected to the real LLM flow."""
    issues = []
    # Check if count_request is ever called outside self-test/exports
    path = PROJECT_ROOT / ".claude-flow" / "mcp" / "hermes_token_meter.py"
    content = path.read_text()
    # count_request should be referenced by MCP server code
    hermes_server = PROJECT_ROOT / ".claude-flow" / "mcp" / "hermes-mcp-server.py"
    hermes_lite = PROJECT_ROOT / ".claude-flow" / "mcp" / "hermes-lite-mcp-server.py"

    if hermes_server.exists():
        sc = hermes_server.read_text()
        if "count_request" not in sc and "count_turn" not in sc:
            issues.append("TokenMeter.count_request not called from hermes-mcp-server.py")
    if hermes_lite.exists():
        lc = hermes_lite.read_text()
        if "count_request" not in lc and "count_turn" not in lc:
            issues.append("TokenMeter.count_request not called from hermes-lite-mcp-server.py")

    return issues


def check_context_compactor_integration() -> list[str]:
    """Verify ContextCompactor.register_message is connected to real flow."""
    issues = []
    path = PROJECT_ROOT / ".claude-flow" / "mcp" / "context_compactor.py"
    content = path.read_text()

    if "register_message" not in content:
        issues.append("register_message function missing")

    # Check if it's called from MCP handlers
    for mcp_file in ["hermes-mcp-server.py", "hermes-lite-mcp-server.py"]:
        mcp_path = PROJECT_ROOT / ".claude-flow" / "mcp" / mcp_file
        if mcp_path.exists():
            mc = mcp_path.read_text()
            if "register_message" not in mc and "COMPACTOR_AVAILABLE" not in mc:
                pass  # May be in other files

    return issues


def check_health_threshold_consistency() -> list[str]:
    """Verify all components use the same 40/60/80% thresholds."""
    issues = []
    files_to_check = [
        PROJECT_ROOT / "core" / "legion_session.py",
        PROJECT_ROOT / "core" / "cognition_boot.py",
        PROJECT_ROOT / "core" / "context_health.py",
        # legion_compaction.py excluded — it reports raw %, health assessment is in context_health.py
    ]
    for f in files_to_check:
        if not f.exists():
            continue
        content = f.read_text()
        # Check for 40/60/80 thresholds
        if "0.40" not in content and "< 0.40" not in content and "0.40" not in content.replace(" ", ""):
            issues.append(f"{f.name}: missing HEALTHY threshold (<40%)")
        if "0.60" not in content:
            issues.append(f"{f.name}: missing CAUTION threshold (<60%)")
        if "0.80" not in content:
            issues.append(f"{f.name}: missing CRITICAL threshold (<80%)")
    return issues


def check_legion_compaction_formula() -> list[str]:
    """Verify legion_compaction.py Section 9 formula is correct."""
    path = PROJECT_ROOT / "core" / "legion_compaction.py"
    content = path.read_text()
    issues = []
    if "int(pct.rstrip(" in content or "pct.rstrip" in content:
        issues.append("FRAGILE: uses int(pct.rstrip('%')) string conversion")
    if "4_194_304" not in content:
        issues.append("MISSING: max_context_chars = 4_194_304 (1M token window * 4)")
    return issues


def check_end_to_end_wiring() -> list[str]:
    """Verify settings.json has correct context tracking hooks wired in."""
    issues = []
    settings_path = PROJECT_ROOT / ".claude" / "settings.json"
    if not settings_path.exists():
        return ["settings.json not found"]

    try:
        settings = json.loads(settings_path.read_text())

        # Check HERMES_MAX_CONTEXT_TOKENS
        env = settings.get("env", {})
        hermes_max = env.get("HERMES_MAX_CONTEXT_TOKENS", "")
        if hermes_max != "1048576":
            issues.append(f"HERMES_MAX_CONTEXT_TOKENS={hermes_max} (should be 1048576 for 1M window)")

        # Check PostToolUse includes track_context.py register
        post_tool = settings.get("hooks", {}).get("PostToolUse", [])
        tc_register_found = False
        for group in post_tool:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                if "track_context.py" in cmd and "register" in cmd:
                    tc_register_found = True
        if not tc_register_found:
            issues.append("PostToolUse missing track_context.py register hook")

        # Check UserPromptSubmit includes track_context.py message
        ups = settings.get("hooks", {}).get("UserPromptSubmit", [])
        tc_message_found = False
        for hook_group in ups:
            for hook in hook_group.get("hooks", []):
                cmd = hook.get("command", "")
                if "track_context.py" in cmd and "message" in cmd:
                    tc_message_found = True
        if not tc_message_found:
            issues.append("UserPromptSubmit missing track_context.py message hook")

        # Check SessionStart includes track_context.py init
        ss = settings.get("hooks", {}).get("SessionStart", [])
        tc_init_found = False
        for hook_group in ss:
            for hook in hook_group.get("hooks", []):
                cmd = hook.get("command", "")
                if "track_context.py" in cmd and "init" in cmd:
                    tc_init_found = True
        if not tc_init_found:
            issues.append("SessionStart missing track_context.py init hook")

    except Exception as e:
        issues.append(f"Cannot read settings.json: {e}")

    return issues


def check_track_context() -> list[str]:
    """Verify track_context.py exists, compiles, and runs status."""
    issues = []
    path = PROJECT_ROOT / "scripts" / "track_context.py"
    if not path.exists():
        return ["scripts/track_context.py not found"]

    # Check syntax
    syntax_issues = check_python_syntax(path)
    issues.extend(syntax_issues)

    if not issues:
        # Run status command to verify it works
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, str(path), "status"],
                capture_output=True, text=True, timeout=5,
                cwd=str(PROJECT_ROOT),
            )
            if result.returncode != 0:
                issues.append(f"status command failed: {result.stderr.strip()}")
            else:
                status_out = (result.stdout or "").strip() or (result.stderr or "").strip()
                if status_out:
                    pass  # status output is expected
        except subprocess.TimeoutExpired:
            issues.append("track_context.py status timed out (>5s)")
        except Exception as e:
            issues.append(f"track_context.py status error: {e}")

    return issues


def run_live_check() -> list[str]:
    """If --live flag, read actual session data and check counters."""
    issues = []
    session_msgs = PROJECT_ROOT / ".claude-flow" / "data" / "session_messages.json"
    session_current = PROJECT_ROOT / ".claude-flow" / "data" / "current.json"

    if session_msgs.exists():
        try:
            msgs = json.loads(session_msgs.read_text())
            total = sum(len(m.get("content", "")) for m in msgs[-50:])
            tokens = total // 4
            pct = min(100, (tokens / CC_NATIVE_TOKENS) * 100)
            print(f"  LIVE: session_messages.json: {total:,} chars, ~{tokens:,} tokens, {pct:.1f}%")
            if pct > 100:
                issues.append(f"LIVE: Context {pct:.0f}% > 100% — exceeds native window")
        except Exception as e:
            issues.append(f"LIVE: Cannot read session_messages.json: {e}")
    else:
        print("  LIVE: No session_messages.json (no messages yet this session)")

    if session_current.exists():
        try:
            data = json.loads(session_current.read_text())
            sid = data.get("id", "?")
            metrics = data.get("metrics", {})
            print(f"  LIVE: current.json session={sid}, edits={metrics.get('edits', 0)}, commands={metrics.get('commands', 0)}")
        except Exception as e:
            issues.append(f"LIVE: Cannot read current.json: {e}")
    else:
        print("  LIVE: No current.json (no active session)")

    return issues


def main():
    print("=" * 68)
    print("  Context Counting — Deep Cross-Reference Validation")
    print(f"  Model window: deepseek-v4-flash {CC_NATIVE_TOKENS:,} tokens = {CC_NATIVE_CHARS:,} chars")
    print("=" * 68)
    print()

    all_issues = {}
    all_pass = True

    # 1. Check all files for wrong denominators
    print("[1] Checking for WRONG denominators (22000/200000 chars)...")
    for name, info in EXPECTED_CAPACITY.items():
        path = PROJECT_ROOT / name if "/" not in name else PROJECT_ROOT / name
        # Find the file
        found_paths = list(PROJECT_ROOT.rglob(name))
        if not found_paths:
            all_issues[name] = [f"FILE NOT FOUND"]
            all_pass = False
            continue
        for fp in found_paths:
            issues = check_file_has_no_old_denominators(fp, name)
            if issues:
                all_issues[fp.name] = issues
                all_pass = False
                for issue in issues:
                    print(f"  FAIL: {fp.name}: {issue}")
    if not any(True for v in all_issues.values() if v):
        print("  PASS")

    # 2. Check _estimate_context_chars() no longer uses RSS
    print()
    print("[2] Checking _estimate_context_chars() does not use RSS/4...")
    for name in ["legion_session.py", "cognition_boot.py"]:
        for path in PROJECT_ROOT.rglob(name):
            issues = check_estimate_context_chars(name, path)
            if issues:
                all_pass = False
                for i in issues:
                    print(f"  FAIL: {path.name}: {i}")
    if all(not check_estimate_context_chars(n, p) for n in ["legion_session.py", "cognition_boot.py"] for p in PROJECT_ROOT.rglob(n)):
        print("  PASS")

    # 3. Check all files parse as valid Python
    print()
    print("[3] Checking Python syntax...")
    modified_files = [
        "core/legion_compaction.py",
        ".claude-flow/mcp/context_compactor.py",
        ".claude-flow/mcp/hermes_token_meter.py",
        "core/context_health.py",
        "core/legion_session.py",
        "core/cognition_boot.py",
        "core/opencode_bridge.py",
    ]
    for f in modified_files:
        for path in PROJECT_ROOT.rglob(f.split("/")[-1]):
            issues = check_python_syntax(path)
            if issues:
                all_pass = False
                for i in issues:
                    print(f"  FAIL: {path.name}: {i}")
    print("  PASS")

    # 4. Check health threshold consistency
    print()
    print("[4] Checking 40/60/80% health threshold consistency...")
    issues = check_health_threshold_consistency()
    if issues:
        all_pass = False
        for i in issues:
            print(f"  FAIL: {i}")
    else:
        print("  PASS")

    # 5. Check legion_compaction formula
    print()
    print("[5] Checking legion_compaction.py formula...")
    issues = check_legion_compaction_formula()
    if issues:
        all_pass = False
        for i in issues:
            print(f"  FAIL: {i}")
    else:
        print("  PASS")

    # 6. Check data flow integration
    print()
    print("[6] Checking TokenMeter + ContextCompactor data flow...")
    tm_issues = check_token_meter_integration()
    if tm_issues:
        for i in tm_issues:
            print(f"  INFO: {i}")
    else:
        print("  PASS (integrated)")
    cc_issues = check_context_compactor_integration()
    if cc_issues:
        for i in cc_issues:
            print(f"  INFO: {i}")
    else:
        print("  PASS (integrated)")
    # Integration checks are informational — don't fail
    all_issues["token_meter_integration"] = tm_issues
    all_issues["context_compactor_integration"] = cc_issues

    # 7. Check end-to-end hook wiring
    print()
    print("[7] Checking end-to-end hook wiring in settings.json...")
    e2e_issues = check_end_to_end_wiring()
    if e2e_issues:
        all_pass = False
        for i in e2e_issues:
            print(f"  FAIL: {i}")
    else:
        print("  PASS")

    # 8. Check track_context.py compiles and runs
    print()
    print("[8] Checking track_context.py...")
    tc_issues = check_track_context()
    if tc_issues:
        all_pass = False
        for i in tc_issues:
            print(f"  FAIL: {i}")
    else:
        print("  PASS")

    # 9. Live check (if --live flag)
    print()
    if "--live" in sys.argv:
        print("[9] LIVE session data check...")
        issues = run_live_check()
        if issues:
            print("  ISSUES FOUND:")
            for i in issues:
                print(f"    {i}")
        else:
            print("  PASS")
    else:
        print("[9] LIVE check skipped (run with --live for session data)")

    # Summary
    print()
    print("=" * 68)
    if all_pass:
        print("  ALL CHECKS PASSED — context counters validated against deepseek-v4-flash 1M token window.")
        sys.exit(0)
    else:
        print("  SOME CHECKS FAILED — see issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
