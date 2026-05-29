#!/usr/bin/env python3
"""
Security Gate — Pre-write security scanning layer for Hermes agent.

Scans code BEFORE it's written to detect:
- Hardcoded secrets (API keys, passwords, tokens)
- SQL injection patterns
- XSS vulnerability patterns
- Path traversal patterns
- Deserialization vulnerabilities
- Weak cryptography usage

Exposes MCP tools:
- security_scan_code(code_snippet)  — Scan code before writing
- security_check_file(file_path)    — Scan existing file
- security_gate(action, confidence) — Block if confidence < threshold
- security_report()                 — Get security status report
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# Paths
# ============================================================================

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
SECURITY_DB = PROJECT_ROOT / ".claude-flow" / "data" / "security_findings.db"
SECURITY_LOG = PROJECT_ROOT / ".claude-flow" / "logs" / "security_gate.log"

SECURITY_DB.parent.mkdir(parents=True, exist_ok=True)
SECURITY_LOG.parent.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Confidence Threshold
# ============================================================================

BLOCK_THRESHOLD = 0.9  # Block if confidence < 90%
REVIEW_THRESHOLD = 0.7  # Flag for review if < 70%

# ============================================================================
# Vulnerability Pattern Database
# ============================================================================

# --- Hardcoded Secrets ---
SECRET_PATTERNS = [
    (r'api[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-]{20,}', "hardcoded_api_key", 0.95),
    (r'secret["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-]{20,}', "hardcoded_secret", 0.9),
    (r'token["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-]{30,}', "hardcoded_token", 0.95),
    (r'password["\']?\s*[:=]\s*["\'][^"\']{8,}', "hardcoded_password", 0.9),
    (r'ghp_[a-zA-Z0-9]{36}', "github_pat", 0.99),
    (r'sk-[a-zA-Z0-9]{48}', "openai_sk", 0.99),
    (r'xox[baprs]-[a-zA-Z0-9]{10,}', "slack_token", 0.95),
    (r'AKIA[0-9A-Z]{16}', "aws_access_key", 0.99),
    (r'["\'][a-zA-Z0-9]{32,48}["\'][\s]*as\s+(api|secret|token|key)', "potential_creds", 0.85),
]

# --- OWASP Top 10 ---
SQLI_PATTERNS = [
    (r'execute\s*\(\s*["\'].*%s', "sql_injection_execute", 0.9),
    (r'["\'].*".format\s*\(', "sql_injection_format", 0.85),
    (r'"\s*\+\s*["\'].*SELECT|INSERT|UPDATE|DELETE', "sql_injection_concat", 0.9),
    (r'f["\'].*SELECT|INSERT|UPDATE|DELETE.*{', "sql_injection_fstring", 0.85),
    (r'cursor\.execute\s*\(\s*f["\']', "sql_injection_fstring_cursor", 0.9),
    (r'raw\s*\(\s*["\'].*(?:SELECT|INSERT|UPDATE|DELETE)', "sql_injection_raw", 0.9),
]

XSS_PATTERNS = [
    (r'innerHTML\s*=', "xss_innerHTML", 0.9),
    (r'dangerouslySetInnerHTML', "xss_react_dangerously", 0.85),
    (r'\.html\s*\(\s*(?:user|input|request)', "xss_jquery_html", 0.8),
    (r'eval\s*\(\s*(?:request\.|user|input)', "xss_eval", 0.95),
    (r'document\.write\s*\(', "xss_document_write", 0.9),
]

PATH_TRAVERSAL_PATTERNS = [
    (r'open\s*\([^,]*\+[^,]*\)', "path_traversal_concat", 0.8),
    (r'os\.path\.join\s*\([^)]*\+', "path_traversal_join", 0.75),
    (r'\.\./', "path_traversal_literal", 0.95),
    (r'Path\s*\([^)]*\+\s*[^)]*\)', "path_traversal_path_concat", 0.8),
    (r'send_file\s*\([^)]*\+', "path_traversal_send_file", 0.85),
]

DESERIALIZATION_PATTERNS = [
    (r'pickle\.loads?', "unsafe_pickle", 0.95),
    (r'yaml\.load\s*\([^)]*(?!Loader=)', "unsafe_yaml", 0.9),
    (r'marshal\.loads?', "unsafe_marshal", 0.9),
    (r'shelve\.open', "unsafe_shelve", 0.7),
    (r'jsonpickle\.decode', "unsafe_jsonpickle", 0.8),
    (r'eval\s*\(', "unsafe_eval", 0.95),
    (r'compile\s*\(', "unsafe_compile", 0.7),
]

WEAK_CRYPTO_PATTERNS = [
    (r'MD5\s*\(', "weak_crypto_md5", 0.9),
    (r'SHA1\s*\(', "weak_crypto_sha1", 0.85),
    (r'DES\s*\(', "weak_crypto_des", 0.9),
    (r'RC4\s*\(', "weak_crypto_rc4", 0.9),
    (r'Crypto\.Cipher\.ARC4', "weak_crypto_arc4", 0.9),
    (r'ssl\.wrap_socket', "weak_crypto_sslwrap", 0.95),
    (r'hashlib\.md5\s*\(', "weak_crypto_hashlib_md5", 0.85),
    (r'hashlib\.sha1\s*\(', "weak_crypto_hashlib_sha1", 0.8),
    (r'RAND_bytes\s*\(\s*1\s*\)', "weak_crypto_rand_bytes", 0.7),
]

# CWE Top 25 patterns
CWE_PATTERNS = [
    (r'os\.system\s*\(', "cwe_78_os_command_injection", 0.95),
    (r'subprocess\.\w+\s*\(\s*shell\s*=\s*True', "cwe_78_shell_true", 0.95),
    (r'eval\s*\(', "cwe_95_code_injection", 0.95),
    (r'exec\s*\(', "cwe_95_code_injection_exec", 0.95),
    (r'SQL\s+INJECTION|sql\s+injection', "cwe_89_sql_injection", 0.9),
    (r'XSS|cross\s*site\s*scripting', "cwe_79_xss", 0.9),
    (r'path\s*traversal|\.\.\/', "cwe_22_path_traversal", 0.9),
    (r'mkdir\s+777|chmod\s+777', "cwe_276_perm_misconfig", 0.85),
    (r'hardcoded\s*(pass|cred|secret|key)', "cwe_798_hardcoded_creds", 0.9),
    (r'request\.cookies\.get|cookie\s*=\s*request', "cwe_614_weak_cookie", 0.7),
]

# All patterns consolidated
ALL_VULN_PATTERNS = (
    [(p, cat, conf, "secret") for p, cat, conf in SECRET_PATTERNS]
    + [(p, cat, conf, "sqli") for p, cat, conf in SQLI_PATTERNS]
    + [(p, cat, conf, "xss") for p, cat, conf in XSS_PATTERNS]
    + [(p, cat, conf, "path") for p, cat, conf in PATH_TRAVERSAL_PATTERNS]
    + [(p, cat, conf, "deser") for p, cat, conf in DESERIALIZATION_PATTERNS]
    + [(p, cat, conf, "crypto") for p, cat, conf in WEAK_CRYPTO_PATTERNS]
    + [(p, cat, conf, "cwe") for p, cat, conf in CWE_PATTERNS]
)

# Irreversible actions that require high confidence
CRITICAL_ACTIONS = {
    "file_write": 0.9,
    "network_call": 0.9,
    "system_command": 0.95,
    "git_commit": 0.85,
    "env_write": 0.95,
    "db_delete": 0.95,
    "user_delete": 0.95,
}

# ============================================================================
# Database Setup
# ============================================================================

def _get_db() -> sqlite3.Connection:
    """Get SQLite connection for security findings."""
    conn = sqlite3.connect(str(SECURITY_DB), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS security_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            finding_type TEXT,
            category TEXT,
            pattern_id TEXT,
            confidence REAL,
            severity TEXT,
            description TEXT,
            code_snippet TEXT,
            file_path TEXT,
            line_number INTEGER,
            action TEXT,
            decision TEXT,
            reasoning TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS security_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            action TEXT,
            confidence REAL,
            decision TEXT,
            reasoning TEXT,
            blocked INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON security_findings(finding_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conf ON security_findings(confidence)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_time ON security_findings(timestamp)")
    conn.commit()
    return conn


# ============================================================================
# Core Scanning Logic
# ============================================================================

def _scan_patterns(code: str, file_path: str = "") -> List[Dict[str, Any]]:
    """Scan code against all vulnerability patterns."""
    findings = []
    lines = code.split("\n")

    for pattern_regex, pattern_id, confidence, category in ALL_VULN_PATTERNS:
        try:
            for match in re.finditer(pattern_regex, code, re.IGNORECASE | re.MULTILINE):
                start = match.start()
                line_num = code[:start].count("\n") + 1

                # Get surrounding context (up to 2 lines before/after)
                before = "\n".join(lines[max(0, line_num - 3):line_num - 1])
                after = "\n".join(lines[line_num:min(len(lines), line_num + 2)])
                snippet = "{}\n{}\n{}".format(before, match.group(), after)[:500]

                severity = "critical" if confidence >= 0.9 else "high" if confidence >= 0.8 else "medium"

                findings.append({
                    "type": "pattern_match",
                    "category": category,
                    "pattern_id": pattern_id,
                    "confidence": confidence,
                    "severity": severity,
                    "description": "Detected {}: {}".format(category, pattern_id),
                    "code_snippet": snippet,
                    "file_path": file_path,
                    "line_number": line_num,
                    "matched_text": match.group()[:100],
                })
        except re.error:
            continue

    return findings


def _scan_ast(code: str) -> List[Dict[str, Any]]:
    """Use AST parsing for deeper Python-specific analysis."""
    findings = []

    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return findings

    for node in ast.walk(tree):
        # Check for dangerous function calls
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            # Check os.system / subprocess with shell=True
            if func_name in ("system", "popen") and not _is_safe_subprocess(node):
                findings.append({
                    "type": "ast_dangerous_call",
                    "category": "cwe",
                    "pattern_id": "ast_{}".format(func_name),
                    "confidence": 0.95,
                    "severity": "critical",
                    "description": "Dangerous function call: os.{}()".format(func_name),
                    "line_number": getattr(node, "lineno", 0) or 0,
                })

        # Check for insecure SSL contexts
        if isinstance(node, ast.Attribute):
            if node.attr == "wrap_socket" and isinstance(node.value, ast.Name):
                if node.value.id == "ssl":
                    findings.append({
                        "type": "ast_insecure_ssl",
                        "category": "crypto",
                        "pattern_id": "insecure_ssl_context",
                        "confidence": 0.9,
                        "severity": "high",
                        "description": "Insecure SSL socket creation",
                        "line_number": getattr(node, "lineno", 0) or 0,
                    })

    return findings


def _is_safe_subprocess(node: ast.Call) -> bool:
    """Check if subprocess call has shell=False (safer)."""
    for keyword in node.keywords:
        if keyword.arg == "shell":
            if isinstance(keyword.value, ast.Constant) and not keyword.value.value:
                return True
    return False


def _aggregate_confidence(findings: List[Dict[str, Any]]) -> float:
    """Aggregate multiple findings into overall confidence score."""
    if not findings:
        return 1.0  # No issues = full confidence

    # Weight by severity
    severity_weights = {"critical": 1.0, "high": 0.75, "medium": 0.5}

    total_weight = 0.0
    weighted_sum = 0.0

    for f in findings:
        weight = severity_weights.get(f.get("severity", "medium"), 0.5)
        conf = f.get("confidence", 0.5)
        weighted_sum += weight * conf
        total_weight += weight

    if total_weight == 0:
        return 1.0

    # Average weighted confidence, inverted (lower is worse)
    avg_weighted = weighted_sum / total_weight
    return avg_weighted


# ============================================================================
# Main Security Functions
# ============================================================================

def security_scan_code(code_snippet: str, file_path: str = "") -> Dict[str, Any]:
    """
    Scan code snippet before writing. Returns findings + confidence.
    """
    findings = []
    findings.extend(_scan_patterns(code_snippet, file_path))
    findings.extend(_scan_ast(code_snippet))

    # Deduplicate by pattern_id + line_number
    seen = set()
    unique_findings = []
    for f in findings:
        key = (f.get("pattern_id"), f.get("line_number"))
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    # Sort by confidence (highest first)
    unique_findings.sort(key=lambda x: x.get("confidence", 0), reverse=True)

    # Calculate aggregate confidence
    aggregate_conf = _aggregate_confidence(unique_findings)

    # Determine severity
    if not unique_findings:
        severity = "none"
    elif any(f.get("severity") == "critical" for f in unique_findings):
        severity = "critical"
    elif any(f.get("severity") == "high" for f in unique_findings):
        severity = "high"
    else:
        severity = "medium"

    # Store findings in DB
    try:
        conn = _get_db()
        now = time.time()
        for f in unique_findings:
            conn.execute("""
                INSERT INTO security_findings
                (timestamp, finding_type, category, pattern_id, confidence,
                 severity, description, code_snippet, file_path, line_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now,
                f.get("type", "unknown"),
                f.get("category", "unknown"),
                f.get("pattern_id", "unknown"),
                f.get("confidence", 0.0),
                f.get("severity", "unknown"),
                f.get("description", ""),
                f.get("code_snippet", "")[:1000],
                file_path,
                f.get("line_number", 0),
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("Failed to store security findings: %s", e)

    return {
        "scan_time": datetime.now().isoformat(),
        "file_path": file_path,
        "findings_count": len(unique_findings),
        "aggregate_confidence": round(aggregate_conf, 4),
        "severity": severity,
        "findings": unique_findings,
        "blocked": aggregate_conf < BLOCK_THRESHOLD and len(unique_findings) > 0,
        "review_required": aggregate_conf < REVIEW_THRESHOLD and len(unique_findings) > 0,
    }


def security_check_file(file_path: str) -> Dict[str, Any]:
    """
    Scan an existing file for security issues.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found: {}".format(file_path)}

    try:
        code = path.read_text(errors="replace")
    except Exception as e:
        return {"error": "Cannot read file: {}".format(e)}

    return security_scan_code(code, file_path)


def security_gate(action: str, confidence: float = 1.0,
                   description: str = "") -> Dict[str, Any]:
    """
    Security checkpoint gate. Blocks actions with confidence < BLOCK_THRESHOLD.

    Args:
        action: Action type (file_write, network_call, system_command, etc.)
        confidence: Overall confidence score (0-1.0) for this action
        description: Human-readable description of the action

    Returns:
        Decision with reasoning
    """
    required_conf = CRITICAL_ACTIONS.get(action, BLOCK_THRESHOLD)
    effective_threshold = max(required_conf, BLOCK_THRESHOLD)

    now = time.time()
    decision = "allow"
    reasoning = "Action '{}' passed security gate".format(action)

    if confidence < effective_threshold:
        decision = "block"
        reasoning = (
            "BLOCKED: Action '{}' has confidence {:.2f} "
            "(threshold: {:.2f}). {}"
        ).format(action, confidence, effective_threshold, description)
    elif confidence < REVIEW_THRESHOLD:
        decision = "review"
        reasoning = (
            "REVIEW REQUIRED: Action '{}' has moderate confidence "
            "{:.2f} (review threshold: {:.2f}). {}"
        ).format(action, confidence, REVIEW_THRESHOLD, description)

    # Store decision
    try:
        conn = _get_db()
        conn.execute("""
            INSERT INTO security_decisions
            (timestamp, action, confidence, decision, reasoning, blocked)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (now, action, confidence, decision, reasoning, 1 if decision == "block" else 0))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("Failed to store security decision: %s", e)

    # Log decision
    try:
        SECURITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(SECURITY_LOG, "a") as f:
            f.write("[{}] {} | {} | conf={:.3f} | {}\n".format(
                datetime.now().isoformat(), decision.upper(), action,
                confidence, reasoning[:200]
            ))
    except Exception:
        pass

    return {
        "action": action,
        "confidence": confidence,
        "threshold": effective_threshold,
        "decision": decision,
        "reasoning": reasoning,
        "blocked": decision == "block",
        "review_required": decision == "review",
        "timestamp": now,
    }


def security_report() -> Dict[str, Any]:
    """
    Generate security status report from stored findings and decisions.
    """
    try:
        conn = _get_db()

        # Summary stats
        total_findings = conn.execute(
            "SELECT COUNT(*) FROM security_findings"
        ).fetchone()[0]

        by_category = conn.execute("""
            SELECT category, COUNT(*) as count,
                   AVG(confidence) as avg_conf,
                   MAX(severity) as max_severity
            FROM security_findings
            WHERE timestamp > ?
            GROUP BY category
        """, (time.time() - 86400,)).fetchall()

        by_severity = conn.execute("""
            SELECT severity, COUNT(*) as count
            FROM security_findings
            WHERE timestamp > ?
            GROUP BY severity
        """, (time.time() - 86400,)).fetchall()

        recent_decisions = conn.execute("""
            SELECT action, decision, confidence, reasoning, timestamp
            FROM security_decisions
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (time.time() - 86400,)).fetchall()

        recent_findings = conn.execute("""
            SELECT pattern_id, category, severity, confidence,
                   file_path, line_number, description
            FROM security_findings
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (time.time() - 86400,)).fetchall()

        blocked_count = conn.execute(
            "SELECT COUNT(*) FROM security_decisions WHERE blocked=1 AND timestamp>?"
        , (time.time() - 86400,)).fetchone()[0]

        conn.close()

        return {
            "report_time": datetime.now().isoformat(),
            "period_seconds": 86400,
            "summary": {
                "total_findings": total_findings,
                "blocked_actions": blocked_count,
                "by_category": [
                    {"category": r[0], "count": r[1], "avg_confidence": round(r[2], 3) if r[2] else 0, "max_severity": r[3]}
                    for r in by_category
                ],
                "by_severity": {r[0]: r[1] for r in by_severity},
            },
            "recent_findings": [
                {
                    "pattern_id": r[0],
                    "category": r[1],
                    "severity": r[2],
                    "confidence": round(r[3], 3) if r[3] else 0,
                    "file": r[4],
                    "line": r[5],
                    "description": r[6],
                }
                for r in recent_findings
            ],
            "recent_decisions": [
                {
                    "action": r[0],
                    "decision": r[1],
                    "confidence": round(r[2], 3) if r[2] else 0,
                    "reasoning": r[3],
                    "timestamp": r[4],
                }
                for r in recent_decisions
            ],
            "thresholds": {
                "block_threshold": BLOCK_THRESHOLD,
                "review_threshold": REVIEW_THRESHOLD,
                "critical_actions": CRITICAL_ACTIONS,
            },
        }
    except Exception as e:
        logger.error("Failed to generate security report: %s", e)
        return {"error": str(e)}


# ============================================================================
# MCP Tool Handlers
# ============================================================================

def handle_security_scan(args: Dict[str, Any]) -> str:
    """Handle security_scan_code tool invocation."""
    code = args.get("code_snippet", "")
    file_path = args.get("file_path", "")
    if not code:
        return json.dumps({"error": "code_snippet is required"})
    result = security_scan_code(code, file_path)
    return json.dumps(result, indent=2)


def handle_security_check(args: Dict[str, Any]) -> str:
    """Handle security_check_file tool invocation."""
    file_path = args.get("file_path", "")
    if not file_path:
        return json.dumps({"error": "file_path is required"})
    result = security_check_file(file_path)
    return json.dumps(result, indent=2)


def handle_security_gate(args: Dict[str, Any]) -> str:
    """Handle security_gate tool invocation."""
    action = args.get("action", "")
    confidence = args.get("confidence", 1.0)
    description = args.get("description", "")
    if not action:
        return json.dumps({"error": "action is required"})
    result = security_gate(action, confidence, description)
    return json.dumps(result, indent=2)


def handle_security_report(args: Dict[str, Any]) -> str:
    """Handle security_report tool invocation."""
    result = security_report()
    return json.dumps(result, indent=2)


# Aliases for MCP registration
security_scan_code_tool = handle_security_scan
security_check_file_tool = handle_security_check
security_gate_tool = handle_security_gate
security_report_tool = handle_security_report


# ============================================================================
# CLI Verification
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "scan":
            code = sys.stdin.read() if not sys.stdin.isatty() else "print('hello')"
            result = security_scan_code(code)
            print(json.dumps(result, indent=2))
        elif cmd == "check" and len(sys.argv) > 2:
            result = security_check_file(sys.argv[2])
            print(json.dumps(result, indent=2))
        elif cmd == "gate" and len(sys.argv) > 3:
            result = security_gate(sys.argv[2], float(sys.argv[3]))
            print(json.dumps(result, indent=2))
        elif cmd == "report":
            print(json.dumps(security_report(), indent=2))
        else:
            print("Usage: {} [scan|check <file>|gate <action> <conf>|report]".format(sys.argv[0]))
    else:
        # Self-test
        test_code = 'password = "super_secret_123"  # hardcoded'
        result = security_scan_code(test_code, "test.py")
        print("Self-test scan:")
        print(json.dumps(result, indent=2))
