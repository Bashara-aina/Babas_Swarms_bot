---
name: security-scan
description: >-
  Security scan for Claude Code configuration files. Scans settings.json,
  hooks, and .env for dangerous patterns. Use when user mentions security
  audit, security review, or configuration hardening.
---

## Scan Checklist

### 1. Scan `.claude/settings.json`
- [ ] Check `permissions.allow` for wildcard entries (e.g., `Bash(*)`, `Edit(*)`)
- [ ] Check `permissions.deny` covers dangerous patterns (`~/.ssh/**`, `**/.env*`)
- [ ] Check `env` section for hardcoded secrets or API keys

### 2. Scan hook scripts (`.claude/hooks/*.sh`)
- [ ] Check for command injection via unvalidated input
- [ ] Check for `eval`, `base64 -d`, `curl | sh` patterns
- [ ] Check for data exfiltration (curl/wget to external hosts)

### 3. Scan `.env` files
- [ ] Check `.env` exists and is gitignored
- [ ] Check `.env.example` exists (if applicable)

### 4. Scan `.claude/settings.local.json` (if exists)
- [ ] Check for overrides that weaken security

## Report Format

Present findings in a table:

| Severity | File | Issue | Fix |
|----------|------|-------|-----|
| CRITICAL | settings.json | Wildcard Bash permission | Restrict to specific commands |
| HIGH | hook.sh | Unvalidated input | Validate before execution |
| MEDIUM | .env | No .env.example | Create template |
| LOW | - | - | - |

Exit with findings summary. Do not modify any files without user approval.
