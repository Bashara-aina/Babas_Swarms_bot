---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [scope] | full | api | secrets | dependencies
description: Security audit — check for exposed secrets, vulnerable dependencies, and OWASP Top 10 issues
---

# /security — Security Audit Command

## STEP 1 — Secrets Detection

Scan for hardcoded secrets:
```bash
grep -rn "TELEGRAM_BOT_TOKEN\|API_KEY\|SECRET\|PASSWORD" --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" . | grep -v ".env.example\|os.getenv\|getenv" | grep -v "# hardcoded\|# fake\|# test" | head -20
```

Check .env is properly configured:
```bash
grep -E "^[A-Z]" .env.example | sort > /tmp/expected_vars.txt
grep -E "^[A-Z]" .env 2>/dev/null | sort > /tmp/actual_vars.txt
diff /tmp/expected_vars.txt /tmp/actual_vars.txt || true
```

## STEP 2 — Dependency Audit

```bash
pip-audit 2>/dev/null || pip list --format=freeze | grep -iE "vuln|exploit" || echo "pip-audit not available"
```

## STEP 3 — OWASP Top 10 Checks

For scope=full or api:
```bash
# Injection (SQL, Command)
grep -rn "execute\|eval\|exec\|cursor.execute" --include="*.py" . | grep -v "safe\|sanitize" | head -10

# Broken Authentication
grep -rn "ALLOWED_USER_ID\|require_owner" --include="*.py" handlers/ | head -5
```

## STEP 4 — Report

Format:
```
SECURITY AUDIT: [scope]

✅ PASSED:
- [check that passed]

⚠️ WARNINGS:
- [potential issue, low severity]

🔴 FAILED:
- [critical issue requiring immediate fix]
```

Reference: OWASP Top 10 2021 — A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection
