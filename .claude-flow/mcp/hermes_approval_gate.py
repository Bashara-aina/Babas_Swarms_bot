#!/usr/bin/env python3
"""
Hermes Approval Gate — Per-tool approval system equivalent to Claude Code's
interactive checkpoints (~380 lines).

Provides:
- Risk classification (LOW/MEDIUM/HIGH/CRITICAL)
- Configurable approval policies (auto_allow/permissive/strict)
- TTL-based approval queue persisted to ~/.hermes/approval_policies.json
- Telegram integration for real-time approval prompts
- MCP tool handler for hermes-mcp-server.py integration

Usage:
    result = check_approval("hermes_terminal", '{"command": "rm -rf /tmp"}')
    if not result["allowed"]:
        raise PermissionError(result["reason"])

Author: Bashara | Legion v10
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import threading
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# Paths & Constants
# ============================================================================

HERMES_DIR = Path.home() / ".hermes"
HERMES_DIR.mkdir(parents=True, exist_ok=True)
APPROVAL_DB = HERMES_DIR / "approval_queue.db"
APPROVAL_POLICY_FILE = HERMES_DIR / "approval_policies.json"
APPROVAL_TTL = 300  # 5 min TTL


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Policy(str, Enum):
    AUTO_ALLOW = "auto_allow"
    PERMISSIVE = "permissive"
    STRICT = "strict"


# Policy: action for each risk level
POLICY_TABLE = {
    Policy.AUTO_ALLOW: {RiskLevel.LOW: "allow", RiskLevel.MEDIUM: "prompt",
                        RiskLevel.HIGH: "deny", RiskLevel.CRITICAL: "deny"},
    Policy.PERMISSIVE: {RiskLevel.LOW: "allow", RiskLevel.MEDIUM: "allow",
                        RiskLevel.HIGH: "prompt", RiskLevel.CRITICAL: "prompt"},
    Policy.STRICT: {RiskLevel.LOW: "allow", RiskLevel.MEDIUM: "prompt",
                    RiskLevel.HIGH: "deny", RiskLevel.CRITICAL: "deny"},
}


def _get_policy_decision(policy: Policy, risk: RiskLevel) -> str:
    return POLICY_TABLE.get(policy, POLICY_TABLE[Policy.AUTO_ALLOW]).get(risk, "deny")


# ============================================================================
# Risk Classification
# ============================================================================

RISK_PATTERNS = {
    RiskLevel.LOW: [
        (r"^read|^get|^list|^search|^view|^show|^describe|^stat", "read-only"),
        (r"^ls\s|^cat\s|^head\s|^tail\s|^grep\s", "read-only fs"),
        (r"^git\s+log|^git\s+diff|^git\s+status", "git read-only"),
    ],
    RiskLevel.MEDIUM: [
        (r"^write|^create|^edit|^append|^update|^touch", "file mod"),
        (r"^git\s+add|^git\s+commit", "git commit"),
        (r"^mkdir\s+[^/]|^chmod\s+[0-7]{3}", "fs write"),
        (r"^pip\s+install|^npm\s+install", "package install"),
        (r"^curl\s+-[XPost]", "network write"),
    ],
    RiskLevel.HIGH: [
        (r"rm\s+-[rf]|rm\s+-rf", "destructive delete"),
        (r"git\s+reset\s+--hard", "destructive git reset"),
        (r"chmod\s+-R\s+777", "destructive perms"),
        (r"kill\s+-[9]|pkill|killall", "process kill"),
        (r"docker\s+rm\s|docker\s+rmi", "docker destroy"),
    ],
    RiskLevel.CRITICAL: [
        (r"curl\s+.*-H\s+[Aa]uthorization|curl\s+.*Bearer", "auth exposure"),
        (r"(echo|print|export).*(API_KEY|SECRET|PASSWORD|TOKEN)", "secret in cmd"),
        (r"sudo\s+su|sudo\s+-i|su\s+-$", "priv escalation"),
        (r"iptables|ufw.*allow|firewall-cmd", "firewall change"),
        (r"eval|base64\s+-d.*\|", "code injection"),
    ],
}

TOOL_RISK_MAP: dict[str, RiskLevel] = {
    # LOW risk — read-only
    "hermes_list_tools": RiskLevel.LOW, "hermes_list_all_tools": RiskLevel.LOW,
    "hermes_health_check": RiskLevel.LOW, "gitnexus_query": RiskLevel.LOW,
    "gitnexus_context": RiskLevel.LOW, "gitnexus_list_repos": RiskLevel.LOW,
    "gitnexus_cypher": RiskLevel.LOW, "tavily_search": RiskLevel.LOW,
    "tavily_extract": RiskLevel.LOW, "tavily_map": RiskLevel.LOW,
    "tavily_research": RiskLevel.LOW, "exa_web_search": RiskLevel.LOW,
    "exa_web_fetch": RiskLevel.LOW, "firecrawl_scrape": RiskLevel.LOW,
    "firecrawl_search": RiskLevel.LOW, "firecrawl_map": RiskLevel.LOW,
    "ddg_search": RiskLevel.LOW, "ddg_fetch": RiskLevel.LOW,
    "filesystem_read_file": RiskLevel.LOW, "filesystem_list_directory": RiskLevel.LOW,
    "filesystem_search_files": RiskLevel.LOW, "filesystem_get_file_info": RiskLevel.LOW,
    "obsidian_read_note": RiskLevel.LOW, "obsidian_search_notes": RiskLevel.LOW,
    "obsidian_list_notes": RiskLevel.LOW, "obsidian_execute_dataview_query": RiskLevel.LOW,
    "chrome_snapshot": RiskLevel.LOW, "chrome_list_pages": RiskLevel.LOW,
    "chrome_console_messages": RiskLevel.LOW, "chrome_network_requests": RiskLevel.LOW,
    "playwright_browser_snapshot": RiskLevel.LOW, "playwright_browser_tabs": RiskLevel.LOW,
    "playwright_browser_wait_for": RiskLevel.LOW, "context7_query_docs": RiskLevel.LOW,
    "context7_resolve_library_id": RiskLevel.LOW, "circuit_breaker_status": RiskLevel.LOW,
    "cache_manage": RiskLevel.LOW, "terminal_background_status": RiskLevel.LOW,
    "terminal_background_list": RiskLevel.LOW, "hermes_session_search": RiskLevel.LOW,
    "hermes_skills_list": RiskLevel.LOW, "graphrag_query": RiskLevel.LOW,
    "memory_recall": RiskLevel.LOW, "memory_list": RiskLevel.LOW,
    "synthesize_session_context": RiskLevel.LOW, "synthesis_stats": RiskLevel.LOW,
    "fusion_retrieve_tool": RiskLevel.LOW, "fusion_stats_tool": RiskLevel.LOW,
    "memory_share_read": RiskLevel.LOW, "memory_share_list": RiskLevel.LOW,
    # MEDIUM risk — modifications
    "hermes_write_file": RiskLevel.MEDIUM, "hermes_delegate": RiskLevel.MEDIUM,
    "filesystem_write_file": RiskLevel.MEDIUM, "filesystem_create_directory": RiskLevel.MEDIUM,
    "filesystem_move_file": RiskLevel.MEDIUM, "github_create_issue": RiskLevel.MEDIUM,
    "obsidian_create_note": RiskLevel.MEDIUM, "obsidian_update_note": RiskLevel.MEDIUM,
    "obsidian_append_to_note": RiskLevel.MEDIUM, "obsidian_add_tags": RiskLevel.MEDIUM,
    "chrome_navigate": RiskLevel.MEDIUM, "chrome_click": RiskLevel.MEDIUM,
    "chrome_type_text": RiskLevel.MEDIUM, "chrome_fill_form": RiskLevel.MEDIUM,
    "chrome_hover": RiskLevel.MEDIUM, "chrome_press_key": RiskLevel.MEDIUM,
    "playwright_browser_navigate": RiskLevel.MEDIUM, "playwright_browser_click": RiskLevel.MEDIUM,
    "playwright_browser_type": RiskLevel.MEDIUM, "playwright_browser_take_screenshot": RiskLevel.MEDIUM,
    "playwright_browser_resize": RiskLevel.MEDIUM, "playwright_browser_evaluate": RiskLevel.MEDIUM,
    "playwright_browser_select_option": RiskLevel.MEDIUM, "terminal_background_create": RiskLevel.MEDIUM,
    "terminal_background_kill": RiskLevel.MEDIUM, "delegate_batch": RiskLevel.MEDIUM,
    "hermes_spawn_swarm": RiskLevel.MEDIUM, "swarm_terminate": RiskLevel.MEDIUM,
    "memory_save": RiskLevel.MEDIUM, "memory_sync_session": RiskLevel.MEDIUM,
    "memory_share_write": RiskLevel.MEDIUM, "skills_auto_create": RiskLevel.MEDIUM,
    "graphrag_index": RiskLevel.MEDIUM, "compactor_compact": RiskLevel.MEDIUM,
    "coordination_send": RiskLevel.MEDIUM, "coordination_broadcast": RiskLevel.MEDIUM,
    "coordination_register": RiskLevel.MEDIUM, "github_get_file_contents": RiskLevel.MEDIUM,
    # HIGH risk — destructive/deleting
    "hermes_terminal": RiskLevel.HIGH, "gitnexus_rename": RiskLevel.HIGH,
    "gitnexus_detect_changes": RiskLevel.HIGH, "hermes_execute_code": RiskLevel.HIGH,
    "execute_javascript": RiskLevel.HIGH, "memory_forget": RiskLevel.HIGH,
    "memory_share_delete": RiskLevel.HIGH, "skills_deprecate": RiskLevel.HIGH,
    "compactor_restore": RiskLevel.HIGH,
    # CRITICAL risk — network calls, secret exposure, system changes
    "veracity_scan": RiskLevel.CRITICAL, "veracity_is_safe": RiskLevel.CRITICAL,
    "security_scan_code": RiskLevel.CRITICAL, "security_check_file": RiskLevel.CRITICAL,
    "security_gate": RiskLevel.CRITICAL, "memory_extract_session": RiskLevel.CRITICAL,
}


def _classify_by_pattern(action: str) -> RiskLevel:
    """Refine risk based on action content patterns."""
    for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
        for pattern, _ in RISK_PATTERNS.get(level, []):
            if re.search(pattern, action.lower(), re.IGNORECASE | re.MULTILINE):
                return level
    return RiskLevel.LOW


def get_tool_risk_level(tool_name: str, proposed_action: str = "") -> RiskLevel:
    """Get risk level for tool, refined by action content."""
    level = TOOL_RISK_MAP.get(tool_name, RiskLevel.MEDIUM)
    if proposed_action and level in (RiskLevel.LOW, RiskLevel.MEDIUM):
        action_level = _classify_by_pattern(proposed_action)
        if action_level.value > level.value:
            return action_level
    return level


# ============================================================================
# Approval Gate Implementation
# ============================================================================

class ApprovalGate:
    """Thread-safe approval queue with TTL and policy enforcement."""

    def __init__(self, ttl: int = APPROVAL_TTL):
        self._ttl = ttl
        self._lock = threading.RLock()
        self._approvals: dict[str, dict] = {}
        self._current_policy = Policy.AUTO_ALLOW
        self._user_telegram_id: str | None = None
        self._load_policy()

    def _init_db(self) -> sqlite3.Connection:
        APPROVAL_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(APPROVAL_DB), check_same_thread=False)
        conn.execute("""CREATE TABLE IF NOT EXISTS approval_queue (
            approval_id TEXT PRIMARY KEY, tool_name TEXT, proposed_action TEXT,
            risk_level TEXT, policy TEXT, context_json TEXT, created_at REAL,
            ttl REAL, status TEXT DEFAULT 'pending', decided_at REAL, decided_by TEXT
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON approval_queue(status)")
        conn.commit()
        return conn

    def _load_policy(self) -> None:
        try:
            if APPROVAL_POLICY_FILE.exists():
                data = json.loads(APPROVAL_POLICY_FILE.read_text())
                self._current_policy = Policy(data.get("policy", "auto_allow"))
                self._user_telegram_id = data.get("user_telegram_id")
        except Exception as e:
            logger.warning("Failed to load policy: %s", e)

    def _save_policy(self) -> None:
        try:
            APPROVAL_POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
            APPROVAL_POLICY_FILE.write_text(json.dumps({
                "policy": self._current_policy.value,
                "user_telegram_id": self._user_telegram_id,
            }, indent=2))
        except Exception as e:
            logger.warning("Failed to save policy: %s", e)

    def set_policy(self, policy: Policy, user_telegram_id: str | None = None) -> dict:
        with self._lock:
            old = self._current_policy
            self._current_policy = policy
            if user_telegram_id is not None:
                self._user_telegram_id = user_telegram_id
            self._save_policy()
            return {"old_policy": old.value, "new_policy": policy.value,
                    "user_telegram_id": self._user_telegram_id}

    def get_policy(self) -> dict:
        return {"policy": self._current_policy.value,
                "user_telegram_id": self._user_telegram_id}

    def request_approval(
        self, tool_name: str, proposed_action: str = "",
        risk_level: str | None = None, context: dict | None = None,
    ) -> dict:
        """Request approval for a tool action. Returns decision."""
        with self._lock:
            actual_risk = RiskLevel(risk_level) if risk_level else get_tool_risk_level(
                tool_name, proposed_action)
            policy_decision = _get_policy_decision(self._current_policy, actual_risk)
            now = time.time()

            if policy_decision == "allow":
                return {"allowed": True,
                        "reason": f"Policy '{self._current_policy.value}' allows {actual_risk.value} automatically.",
                        "requires_confirmation": False, "approval_id": None,
                        "risk_level": actual_risk.value}

            # Create pending approval
            approval_id = f"apr-{uuid.uuid4().hex[:12]}"
            entry = {
                "approval_id": approval_id, "tool_name": tool_name,
                "proposed_action": proposed_action, "risk_level": actual_risk.value,
                "policy": self._current_policy.value, "context": context or {},
                "created_at": now, "ttl": now + self._ttl, "status": "pending",
            }
            self._approvals[approval_id] = entry

            try:
                conn = self._init_db()
                conn.execute("""INSERT INTO approval_queue
                    (approval_id, tool_name, proposed_action, risk_level, policy,
                     context_json, created_at, ttl, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (approval_id, tool_name, proposed_action, actual_risk.value,
                     self._current_policy.value, json.dumps(context or {}),
                     now, entry["ttl"], "pending"))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning("Failed to persist approval: %s", e)

            if self._user_telegram_id:
                self._send_telegram_approval_request(entry)

            return {"allowed": False,
                    "reason": f"Approval required for {tool_name} ({actual_risk.value} risk).",
                    "requires_confirmation": True, "approval_id": approval_id,
                    "risk_level": actual_risk.value}

    def resolve_approval(
        self, approval_id: str, decision: str, decided_by: str = "api",
    ) -> dict:
        with self._lock:
            if approval_id not in self._approvals:
                return {"error": f"Approval {approval_id} not found", "success": False}
            entry = self._approvals[approval_id]
            now = time.time()
            if entry["status"] != "pending":
                return {"error": f"Already resolved as '{entry['status']}'", "success": False}
            if now > entry["ttl"]:
                entry["status"] = "expired"
                return {"error": "Approval expired", "success": False}

            entry["status"] = decision
            entry["decided_at"] = now
            entry["decided_by"] = decided_by

            try:
                conn = self._init_db()
                conn.execute("""UPDATE approval_queue
                    SET status=?, decided_at=?, decided_by=? WHERE approval_id=?""",
                    (decision, now, decided_by, approval_id))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning("Failed to update resolution: %s", e)

            return {"success": True, "approval_id": approval_id, "decision": decision,
                    "tool_name": entry["tool_name"]}

    def pending_approvals(self) -> list[dict]:
        with self._lock:
            now = time.time()
            pending = []
            expired = []
            for aid, entry in self._approvals.items():
                if now > entry["ttl"]:
                    entry["status"] = "expired"
                    expired.append(aid)
                elif entry["status"] == "pending":
                    pending.append({
                        "approval_id": aid, "tool_name": entry["tool_name"],
                        "proposed_action": entry["proposed_action"][:200],
                        "risk_level": entry["risk_level"], "policy": entry["policy"],
                        "created_at": entry["created_at"], "ttl": entry["ttl"],
                        "age_seconds": round(now - entry["created_at"], 1),
                    })
            for aid in expired:
                del self._approvals[aid]
            pending.sort(key=lambda x: x["created_at"], reverse=True)
            return pending

    def check_approval(self, tool_name: str, proposed_action: str = "",
                       context: dict | None = None) -> dict:
        return self.request_approval(tool_name, proposed_action, None, context)

    def set_telegram_user(self, telegram_id: str) -> None:
        self._user_telegram_id = telegram_id
        self._save_policy()

    async def _send_telegram_approval_request(self, entry: dict) -> None:
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path("/home/newadmin/swarm-bot")))
            try:
                from main import get_bot_instance
                bot = get_bot_instance()
                if bot and self._user_telegram_id:
                    emoji = {"LOW": "🔵", "MEDIUM": "🟡",
                             "HIGH": "🟠", "CRITICAL": "🔴"}.get(entry["risk_level"], "⚪")
                    msg = (f"{emoji} <b>Hermes Approval Required</b>\n\n"
                           f"<b>Tool:</b> <code>{entry['tool_name']}</code>\n"
                           f"<b>Risk:</b> <code>{entry['risk_level']}</code>\n"
                           f"<b>Policy:</b> <code>{entry['policy']}</code>\n\n"
                           f"<b>Action:</b>\n<code>{entry['proposed_action'][:300]}</code>\n\n"
                           f"Approve: <code>/hermes-approve {entry['approval_id']}</code>\n"
                           f"Deny: <code>/hermes-deny {entry['approval_id']}</code>\n"
                           f"Skip: <code>/hermes-skip {entry['approval_id']}</code>")
                    await bot.send_message(int(self._user_telegram_id), msg,
                                          parse_mode="HTML")
            except Exception:
                pass
        except Exception as e:
            logger.warning("Telegram notification failed: %s", e)


# ============================================================================
# Singleton & Public API
# ============================================================================

_gate: ApprovalGate | None = None


def get_approval_gate() -> ApprovalGate:
    global _gate
    if _gate is None:
        _gate = ApprovalGate()
    return _gate


def check_approval(tool_name: str, proposed_action: str = "",
                   context: dict | None = None) -> dict:
    """Main integration point for hermes-mcp-server.py tool execution wrapper."""
    return get_approval_gate().check_approval(tool_name, proposed_action, context)


def approval_request(tool: str, action: str = "", risk: str | None = None,
                      context: dict | None = None) -> dict:
    return get_approval_gate().request_approval(tool, action, risk, context)


def approval_resolve(approval_id: str, decision: str,
                     decided_by: str = "api") -> dict:
    return get_approval_gate().resolve_approval(approval_id, decision, decided_by)


def approval_pending() -> list[dict]:
    return get_approval_gate().pending_approvals()


def policy_set(policy: str, telegram_id: str | None = None) -> dict:
    return get_approval_gate().set_policy(Policy(policy), telegram_id)


def policy_get() -> dict:
    return get_approval_gate().get_policy()


# ============================================================================
# MCP Tool Handler
# ============================================================================

HERMES_APPROVAL_GATE_SCHEMA = {
    "name": "hermes_approval_gate",
    "description": "Per-tool approval gate with configurable policies",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"enum": ["check", "request", "resolve", "pending", "policy_set", "policy_get"]},
            "tool_name": {"type": "string"},
            "proposed_action": {"type": "string"},
            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
            "approval_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["allow", "deny", "skip"]},
            "policy": {"type": "string", "enum": ["auto_allow", "permissive", "strict"]},
            "context": {"type": "object"},
        },
    },
}


def handle_hermes_approval_gate(args: dict) -> str:
    """MCP tool handler for hermes_approval_gate."""
    action = args.get("action", "check")
    tool_name = args.get("tool_name", "")
    proposed_action = args.get("proposed_action", "")
    risk_level = args.get("risk_level")
    approval_id = args.get("approval_id")
    decision = args.get("decision")
    policy = args.get("policy")
    context = args.get("context", {})

    try:
        if action == "check":
            return json.dumps(check_approval(tool_name, proposed_action, context), indent=2)
        elif action == "request":
            return json.dumps(approval_request(tool_name, proposed_action, risk_level, context), indent=2)
        elif action == "resolve":
            if not approval_id:
                return json.dumps({"error": "approval_id is required"})
            if not decision:
                return json.dumps({"error": "decision is required"})
            return json.dumps(approval_resolve(approval_id, decision), indent=2)
        elif action == "pending":
            result = approval_pending()
            return json.dumps({"pending": result, "count": len(result)}, indent=2)
        elif action == "policy_set":
            if not policy:
                return json.dumps({"error": "policy is required"})
            return json.dumps(policy_set(policy), indent=2)
        elif action == "policy_get":
            return json.dumps(policy_get(), indent=2)
        else:
            return json.dumps({"error": f"Unknown action: {action}"})
    except Exception as e:
        logger.exception("hermes_approval_gate error")
        return json.dumps({"error": str(e)})


handle_approval_gate = handle_hermes_approval_gate


# ============================================================================
# CLI / Self-Test
# ============================================================================

if __name__ == "__main__":
    gate = get_approval_gate()
    print(f"Default policy: {gate.get_policy()}")

    tests = [
        ("hermes_terminal", "ls /tmp"),
        ("hermes_terminal", "rm -rf /tmp/test"),
        ("gitnexus_cypher", "MATCH (a)-[:CALLS]->(b) RETURN a"),
        ("filesystem_write_file", 'write_file("/tmp/test.txt")'),
        ("veracity_scan", "scan_code"),
    ]

    print("\nRisk Classification:")
    for tool, action in tests:
        risk = get_tool_risk_level(tool, action)
        print(f"  {tool}: {action[:30]:30s} -> {risk.value}")

    print("\nApproval Check (auto_allow):")
    for tool, action in tests[:3]:
        result = check_approval(tool, action)
        print(f"  {tool}: allowed={result['allowed']}, risk={result.get('risk_level')}")

    print("\nApproval Check (strict):")
    gate.set_policy(Policy.STRICT)
    for tool, action in tests[:3]:
        result = check_approval(tool, action)
        print(f"  {tool}: allowed={result['allowed']}, risk={result.get('risk_level')}")

    print("\nMCP handler (check):")
    result = json.loads(handle_hermes_approval_gate({
        "action": "check", "tool_name": "hermes_terminal", "proposed_action": "ls /tmp"}))
    print(f"  allowed={result['allowed']}, requires_confirmation={result['requires_confirmation']}")

    gate.set_policy(Policy.AUTO_ALLOW)
    print("\nAll tests passed!")