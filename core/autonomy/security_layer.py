"""Security layer for the Autonomy Layer.

Implements Part VIII of the Autonomy Layer master prompt v2:
  - Always-on, invisible security scanning
  - Auto-triggers before git commit, API endpoints, PII data
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

ruflo_available = True
_mcp_client = None

try:
    from core.mcp_client import MCPClient
    _mcp_client = MCPClient()
except Exception:
    ruflo_available = False


async def _call_ruflo(tool: str, args: dict | None = None) -> dict:
    if not ruflo_available or _mcp_client is None:
        return {}
    try:
        result = await _mcp_client.call_tool("ruflo", tool, args or {})
        if isinstance(result, list) and len(result) > 0:
            import json
            return json.loads(result[0].text)
        return {}
    except Exception as e:
        logger.debug("ruflo %s failed: %s", tool, e)
        return {}


PII_PATTERNS = ["salary", "ktp", "nik", "npwp", "rekening", "phone"]
SECRET_PATTERNS = [
    r'api[_-]?key', r'secret', r'token', r'password', r'private[_-]?key',
    r'ghp_[a-zA-Z0-9]{36}', r'sk-[a-zA-Z0-9]{48}',
]


class SecurityIssue(Exception):
    """Raised when a security issue is detected and should block the operation."""
    def __init__(self, message: str, severity: str = "high"):
        self.message = message
        self.severity = severity
        super().__init__(message)


async def pre_git_commit_scan(staged_files: list[str]) -> tuple[bool, str]:
    """Run security + PII scan before git commit.

    Returns (clean, error_message).
    If not clean, commit should be blocked.
    """
    if not staged_files:
        return True, ""

    results = await asyncio.gather(
        _call_ruflo("pii_detect", {
            "input": ",".join(staged_files),
            "scan_type": "file",
        }),
        _call_ruflo("security_scan", {
            "checks": ["api_key_exposure", "hardcoded_credentials"],
            "depth": "standard",
        }),
    )

    pii_result, sec_result = results

    if pii_result and pii_result.get("pii_detected"):
        pii_types = pii_result.get("pii_types", [])
        return False, f"PII detected in staged files: {', '.join(pii_types)}. Remove or redact before committing."

    if sec_result and sec_result.get("issues_found", 0) > 0:
        severity = sec_result.get("issues", [{}])[0].get("severity", "medium")
        if severity in ("high", "critical"):
            msg = sec_result["issues"][0].get("message", "Security issue detected")
            return False, f"Security issue: {msg}. Fix before committing."

    return True, ""


async def pre_api_endpoint_scan(schema: str) -> tuple[bool, str]:
    """Validate new API endpoint schema and run security scan."""
    results = await asyncio.gather(
        _call_ruflo("validate_input", {
            "value": schema,
            "input_type": "query",
        }),
        _call_ruflo("security_scan", {
            "checks": ["sql_injection", "xss", "path_traversal"],
            "depth": "standard",
        }),
    )
    val_result, sec_result = results

    if val_result and not val_result.get("valid"):
        issues = val_result.get("issues", [])
        return False, f"Input validation failed: {', '.join(issues)}"

    if sec_result and sec_result.get("issues_found", 0) > 0:
        for issue in sec_result.get("issues", []):
            if issue.get("severity") in ("high", "critical"):
                return False, f"Security issue: {issue.get('message', 'unknown')}"

    return True, ""


async def pre_pii_data_scan(code_content: str) -> tuple[bool, str]:
    """Scan code that will handle salary/tax/KTP/bank data."""
    result = await _call_ruflo("pii_detect", {
        "input": code_content,
        "scan_type": "text",
    })

    if result and result.get("pii_detected"):
        pii_types = result.get("pii_types", [])
        return False, f"PII types detected in code: {', '.join(pii_types)}. Ensure no PII is logged or exposed in error messages."

    return True, ""


async def detect_secrets_in_pasted_code(code: str) -> tuple[bool, str | None]:
    """Check if pasted code contains API keys or secrets.

    Returns (has_secrets, warning_message).
    If has_secrets, do NOT store in memory or wiki.
    """
    for pat in SECRET_PATTERNS:
        if re.search(pat, code, re.IGNORECASE):
            return True, (
                f"Code appears to contain a secret (pattern: {pat}). "
                "Not storing in memory. Remove the secret before continuing."
            )
    return False, None


async def scan_file_for_secrets(file_path: str) -> tuple[bool, str]:
    """Scan a file for hardcoded secrets."""
    try:
        import subprocess
        result = subprocess.run(
            ["grep", "-E", "|".join(SECRET_PATTERNS), file_path],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            matches = result.stdout.strip().split("\n")[:5]
            return True, f"Potential secrets found in {file_path}: {', '.join(matches)}"
    except Exception:
        pass
    return False, ""