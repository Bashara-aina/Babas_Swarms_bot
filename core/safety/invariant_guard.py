"""
Phase 5: Invariant Safety Guard — Agent Safety Guardrails

Intercepts all tool calls BEFORE execution and blocks policy violations.
Last line of defense for 169 MCP tools + 297 agents running autonomously.

Note: invariant-sdk is a cloud API client. This implementation is a local
policy enforcement engine that provides the safety functionality described
in the Phase 5 spec.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

import yaml

_policy_engine = None


def _load_policies() -> dict[str, Any]:
    """Load safety policies from YAML config."""
    policy_path = Path(__file__).parent.parent.parent / "config" / "agent_policies.yaml"
    if not policy_path.exists():
        return {"policies": {}}

    with open(policy_path) as f:
        return yaml.safe_load(f)


class PolicyCheck:
    """Result of a policy check."""

    def __init__(self, allowed: bool, reason: str = "", suggestion: str = ""):
        self.allowed = allowed
        self.reason = reason
        self.suggestion = suggestion
        self.sanitized_args: dict | None = None


class LegionSafetyGuard:
    """
    Intercepts all MCP tool calls before execution.
    Blocks policy violations with clear explanations.

    GAP-23: Per-file granular permissions enforced here.
    GAP-24: Network call policy enforced here.
    GAP-25: Tool argument schema validation enforced here.
    """

    def __init__(self):
        self.config = _load_policies()
        self.policies = self.config.get("policies", {})
        self._call_count: dict[str, int] = {}
        self._blocked_history: list[dict] = []

    _ARG_SCHEMAS: ClassVar[dict[str, dict]] = {
        "bash": {
            "command": {"type": "string", "max_len": 5000},
        },
        "git_git_push": {
            "branch": {"type": "string", "max_len": 256},
            "force": {"type": "boolean"},
            "force_with_lease": {"type": "boolean"},
            "remote": {"type": "string", "max_len": 128},
        },
        "git_git_reset": {
            "mode": {"type": "string", "enum": ["soft", "mixed", "hard", "merge", "keep"]},
            "commit": {"type": "string", "max_len": 64},
        },
        "delete_file": {
            "path": {"type": "string", "max_len": 512},
        },
        "move_file": {
            "source": {"type": "string", "max_len": 512},
            "destination": {"type": "string", "max_len": 512},
        },
        "filesystem_delete": {
            "path": {"type": "string", "max_len": 512},
        },
        "filesystem_move": {
            "source": {"type": "string", "max_len": 512},
            "destination": {"type": "string", "max_len": 512},
        },
    }

    def _match_path(self, path: str, pattern: str) -> bool:
        """Match path against glob pattern."""
        regex = pattern.replace(".", "\\.").replace("**/", ".*/").replace("**", ".*")
        if regex.endswith(".*") and not regex.endswith("/.*"):
            regex = regex + "/.*"
        return bool(re.match(regex, path))

    _FS_TOOL_NAMES = frozenset({
        "read_file", "write_file", "edit_file", "move_file", "delete_file",
        "filesystem_read_file", "filesystem_write_file", "filesystem_edit_file",
        "filesystem_move_file", "filesystem_delete_file", "filesystem_list_directory",
        "glob", "grep", "bash", "shell", "run_bash", "exec",
    })

    def _check_filesystem_policy(self, tool_name: str, args: dict) -> PolicyCheck:
        """GAP-23: Enforce per-file granular permissions for all filesystem tools."""
        if tool_name not in self._FS_TOOL_NAMES:
            return PolicyCheck(allowed=True)

        path = args.get("path", "") or args.get("source", "") or args.get("destination", "")
        if not path:
            return PolicyCheck(allowed=True)

        fs_policy = self.policies.get("filesystem", {})
        allow_rules = fs_policy.get("allow", [])
        deny_rules = fs_policy.get("deny", [])

        action = None
        if any(x in tool_name for x in ("write", "edit", "create")):
            action = "write"
        elif any(x in tool_name for x in ("delete", "remove")):
            action = "delete"
        elif "read" in tool_name or tool_name in ("glob", "grep", "bash", "shell", "run_bash", "exec"):
            action = "read"

        if not action:
            return PolicyCheck(allowed=True)

        allow_matched = None
        for rule in allow_rules:
            if action in rule and self._match_path(path, rule[action]):
                allow_matched = rule[action]
                break

        if allow_matched is None:
            return PolicyCheck(
                allowed=False,
                reason=f"No allow rule matched for {action} on {path}",
                suggestion="Path must match an explicit allow rule"
            )

        for rule in deny_rules:
            if action in rule and self._match_path(path, rule[action]):
                if allow_matched and self._more_specific(path, allow_matched, rule[action]):
                    continue
                return PolicyCheck(
                    allowed=False,
                    reason=f"{action.title()} to {path} denied by policy",
                    suggestion="This path is explicitly denied"
                )

        return PolicyCheck(allowed=True)

    def _more_specific(self, path: str, allow_pattern: str, deny_pattern: str) -> bool:
        """Check if allow pattern is more specific than deny pattern."""
        allow_depth = allow_pattern.count("/")
        deny_depth = deny_pattern.count("/")
        return allow_depth > deny_depth

    def _check_tool_arg_schema(self, tool_name: str, args: dict) -> PolicyCheck:
        """GAP-25: Validate tool arguments against known schemas."""
        schema = self._ARG_SCHEMAS.get(tool_name)
        if not schema:
            return PolicyCheck(allowed=True)

        for field, rules in schema.items():
            if field not in args:
                continue
            value = args[field]
            ftype = rules.get("type")

            if ftype == "string":
                if not isinstance(value, str):
                    return PolicyCheck(
                        allowed=False,
                        reason=f"Argument '{field}' for {tool_name} must be string, got {type(value).__name__}",
                        suggestion=f"Convert {field} to a string"
                    )
                max_len = rules.get("max_len", 10000)
                if len(value) > max_len:
                    return PolicyCheck(
                        allowed=False,
                        reason=f"Argument '{field}' for {tool_name} exceeds max length {max_len}",
                        suggestion=f"Truncate {field} to {max_len} chars"
                    )
            elif ftype == "boolean":
                if not isinstance(value, bool):
                    return PolicyCheck(
                        allowed=False,
                        reason=f"Argument '{field}' for {tool_name} must be boolean",
                        suggestion=f"Pass true/false for {field}"
                    )
            elif ftype == "enum":
                allowed = rules.get("enum", [])
                if value not in allowed:
                    return PolicyCheck(
                        allowed=False,
                        reason=f"Argument '{field}' for {tool_name} must be one of {allowed}, got '{value}'",
                        suggestion=f"Use one of: {allowed}"
                    )

        return PolicyCheck(allowed=True)

    def _check_network_policy(self, tool_name: str, args: dict) -> PolicyCheck:
        """GAP-24: Enforce network call domain allowlisting."""
        net_policy = self.policies.get("network", {})
        if not net_policy:
            return PolicyCheck(allowed=True)

        deny_domains: list[str] = net_policy.get("deny_domains", [])
        allow_domains: list[str] = net_policy.get("allow_domains", [])

        if not deny_domains and not allow_domains:
            return PolicyCheck(allowed=True)

        url = ""
        if tool_name == "exa_web_search_exa":
            url = args.get("url", "") or ""
        elif tool_name == "exa_web_fetch_exa":
            urls = args.get("urls", [])
            if isinstance(urls, list) and urls:
                url = urls[0]
        elif tool_name in ("crawl4ai_crawl", "webfetch"):
            url = args.get("url", "") or ""

        if not url:
            return PolicyCheck(allowed=True)

        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
        except Exception:
            return PolicyCheck(allowed=True)

        for pattern in deny_domains:
            if pattern.startswith("*."):
                tld = pattern[2:]
                if domain.endswith(tld) or domain == tld:
                    return PolicyCheck(
                        allowed=False,
                        reason=f"Network call to {domain} denied: matches blocklist pattern '{pattern}'",
                        suggestion="Use an allowed domain or disable this network call"
                    )
            elif domain == pattern or domain.endswith(f".{pattern}"):
                return PolicyCheck(
                    allowed=False,
                    reason=f"Network call to {domain} denied: matches blocklist pattern '{pattern}'",
                    suggestion="Use an allowed domain"
                )

        if allow_domains:
            allowed = False
            for pattern in allow_domains:
                if pattern.startswith("*."):
                    tld = pattern[2:]
                    if domain.endswith(tld) or domain == tld:
                        allowed = True
                        break
                elif domain == pattern or domain.endswith(f".{pattern}"):
                    allowed = True
                    break
            if not allowed:
                return PolicyCheck(
                    allowed=False,
                    reason=f"Network call to {domain} not in allowlist",
                    suggestion=f"Domain must be one of: {', '.join(allow_domains[:5])}"
                )

        return PolicyCheck(allowed=True)

    def _check_git_policy(self, tool_name: str, args: dict) -> PolicyCheck:
        """Check git-related policies."""
        if "git" not in tool_name.lower() and tool_name not in ("git_git_push", "git_git_reset", "git_git_force"):
            return PolicyCheck(allowed=True)

        git_policy = self.policies.get("git", {})
        deny_rules = git_policy.get("deny", [])

        for rule in deny_rules:
            action = next(iter(rule.keys()))
            pattern = rule[action]

            if action == "push_force":
                if args.get("force") or args.get("force_with_lease"):
                    return PolicyCheck(
                        allowed=False,
                        reason="Force push denied by policy",
                        suggestion="Use regular push instead of force push"
                    )
            elif action == "delete_branch":
                branch = args.get("branch", "")
                if re.match(pattern.replace("*", ".*"), branch):
                    return PolicyCheck(
                        allowed=False,
                        reason=f"Delete branch '{branch}' denied by policy",
                        suggestion="Cannot delete protected branches (main/master)"
                    )

        return PolicyCheck(allowed=True)

    def _check_shell_policy(self, tool_name: str, args: dict) -> PolicyCheck:
        """Check shell command safety policies."""
        if tool_name not in ("bash", "shell", "run_bash", "exec", "shell_execute"):
            return PolicyCheck(allowed=True)

        command = args.get("command", "") or args.get("cmd", "") or ""
        if not command:
            return PolicyCheck(allowed=True)

        shell_policy = self.policies.get("shell", {})
        deny_patterns = shell_policy.get("deny", [])
        allow_overrides = shell_policy.get("allow", [])

        for override in allow_overrides:
            pattern = override.get("pattern", "")
            if pattern and re.search(pattern, command):
                return PolicyCheck(allowed=True)

        for rule in deny_patterns:
            pattern = rule.get("pattern", "")
            if pattern and re.search(pattern, command, re.IGNORECASE):
                return PolicyCheck(
                    allowed=False,
                    reason=f"Shell command denied: matched dangerous pattern '{pattern}'",
                    suggestion="Use a safer alternative or split the command"
                )

        return PolicyCheck(allowed=True)

    def _check_rate_limit(self, tool_name: str) -> PolicyCheck:
        """Check rate limit policies."""
        exa_policy = self.policies.get("exa", {})
        rate_limits = exa_policy.get("rate_limit", [])

        for limit in rate_limits:
            if tool_name in limit:
                limit_str = limit[tool_name]
                match = re.match(r"(\d+)/hour", limit_str)
                if match:
                    max_per_hour = int(match.group(1))
                    current = self._call_count.get(tool_name, 0)
                    if current >= max_per_hour:
                        return PolicyCheck(
                            allowed=False,
                            reason=f"Rate limit exceeded for {tool_name}: {max_per_hour}/hour",
                            suggestion=f"Wait before making more {tool_name} calls"
                        )

        return PolicyCheck(allowed=True)

    def _check_pii(self, args: dict) -> PolicyCheck:
        """Check for PII in tool arguments."""
        if not self.policies.get("global", {}).get("pii_detection", False):
            return PolicyCheck(allowed=True)

        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{16}\b",  # Credit card
            r"api[_-]?key['\"]?\s*[:=]\s*['\"]?\w+",  # API key
        ]

        args_str = str(args)
        for pattern in pii_patterns:
            if re.search(pattern, args_str, re.IGNORECASE):
                return PolicyCheck(
                    allowed=False,
                    reason="PII detected in tool arguments",
                    suggestion="Remove sensitive data before calling tools"
                )

        return PolicyCheck(allowed=True)

    def check_tool_call(self, tool_name: str, args: dict, agent: str = "unknown") -> dict:
        """
        Call this BEFORE every MCP tool execution.

        Returns: {"allowed": True/False, "reason": str, "modified_args": dict}
        """
        global _policy_engine

        if _policy_engine is None:
            _policy_engine = self

        result = PolicyCheck(allowed=True)

        result = self._check_filesystem_policy(tool_name, args)
        if not result.allowed:
            return self._blocked_response(tool_name, args, agent, result)

        result = self._check_shell_policy(tool_name, args)
        if not result.allowed:
            return self._blocked_response(tool_name, args, agent, result)

        result = self._check_git_policy(tool_name, args)
        if not result.allowed:
            return self._blocked_response(tool_name, args, agent, result)

        result = self._check_tool_arg_schema(tool_name, args)
        if not result.allowed:
            return self._blocked_response(tool_name, args, agent, result)

        result = self._check_network_policy(tool_name, args)
        if not result.allowed:
            return self._blocked_response(tool_name, args, agent, result)

        result = self._check_pii(args)
        if not result.allowed:
            return self._blocked_response(tool_name, args, agent, result)

        self._call_count[tool_name] = self._call_count.get(tool_name, 0) + 1

        return {
            "allowed": True,
            "reason": "",
            "modified_args": args
        }

    def _blocked_response(self, tool_name: str, args: dict, agent: str, result: PolicyCheck) -> dict:
        """Generate blocked response and log the block."""
        block_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "args": str(args)[:200],
            "agent": agent,
            "reason": result.reason,
        }
        self._blocked_history.append(block_entry)

        return {
            "allowed": False,
            "reason": result.reason,
            "suggestion": result.suggestion,
            "modified_args": args
        }

    def wrap_mcp_call(self, tool_fn):
        """Decorator to add safety checks to any MCP tool call."""
        def wrapped(tool_name, args, agent="unknown"):
            check = self.check_tool_call(tool_name, args, agent)
            if not check["allowed"]:
                return {"error": f"BLOCKED by safety policy: {check['reason']}"}
            return tool_fn(tool_name, check["modified_args"])
        return wrapped

    def get_blocked_history(self, limit: int = 100) -> list[dict]:
        """Get history of blocked calls."""
        return self._blocked_history[-limit:]

    def get_safety_stats(self) -> dict:
        """Get safety statistics."""
        return {
            "total_blocks": len(self._blocked_history),
            "calls_by_tool": dict(self._call_count),
            "recent_blocks": len([b for b in self._blocked_history if datetime.utcnow().timestamp() - datetime.fromisoformat(b["timestamp"]).timestamp() < 86400])
        }


_guard: LegionSafetyGuard | None = None


def get_safety_guard() -> LegionSafetyGuard:
    """Get or create the global safety guard singleton."""
    global _guard
    if _guard is None:
        _guard = LegionSafetyGuard()
    return _guard


if __name__ == "__main__":
    print("Testing Invariant Safety Guard...")

    guard = get_safety_guard()
    print(f"  Policies loaded: {len(guard.policies)} policy groups")

    test_block = guard.check_tool_call("write_file", {"path": "/home/newadmin/.ssh/config"}, "worker")
    print(f"  Block ssh config: {'BLOCKED' if not test_block['allowed'] else 'ALLOWED'}")

    test_allow = guard.check_tool_call("write_file", {"path": "/home/newadmin/swarm-bot/test.py"}, "worker")
    print(f"  Allow swarm-bot write: {'ALLOWED' if test_allow['allowed'] else 'BLOCKED'}")

    test_force_push = guard.check_tool_call("git_git_push", {"branch": "main", "force": True}, "worker")
    print(f"  Block force push: {'BLOCKED' if not test_force_push['allowed'] else 'ALLOWED'}")

    print(f"\n  Safety stats: {guard.get_safety_stats()}")

    print("\n  Invariant Safety Guard: READY")
