---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic>
description: "Security audit. Check for vulnerabilities, secret leaks, input validation, injection risks."
---

# /security — Security audit

Audit code for security vulnerabilities and best practices.

## Steps

1. If no args: run `bandit -r core/ handlers/ -ll` to find high-severity issues
2. If path args: run `bandit -r <path> -ll` on each
3. Scan for secrets: run the secret leak check (SECTOR 11B of audit)
4. Check input validation: grep for `eval|exec|compile|open(|subprocess` in user-facing files
5. Check SQL injection: look for f-string SQL queries without parameterized inputs
6. Check .env: verify `.env` is in `.gitignore`
7. Report findings with severity and fix instructions

## Usage
```
/security
/security handlers/user_input.py
/security llm_client.py
```

## Security Checklist

### Secrets Management
- [ ] No hardcoded API keys in code
- [ ] Secrets in .env files not committed
- [ ] os.getenv() used for all secrets
- [ ] No credentials in logs

### Input Validation
- [ ] User input validated before use
- [ ] SQL injection prevented (use parameterized queries)
- [ ] Command injection prevented (no shell injection)
- [ ] File path traversal prevented

### LLM Security
- [ ] Prompt injection defenses
- [ ] Output sanitization
- [ ] Rate limiting on LLM calls

### Telegram Security
- [ ] Bot token protected
- [ ] User data handled appropriately
- [ ] No sensitive data in messages

## Swarm-Bot Security Patterns
```python
# GOOD
api_key = os.getenv("TELEGRAM_BOT_TOKEN")
user_input = html.escape(user_text)

# BAD
api_key = "123456:ABC-DEF"  # hardcoded
user_input = user_text  # no escaping
```

## Output Format
```
## SECURITY_AUDIT
<scope of audit>

## VULNERABILITIES
- [CRITICAL] description — file:line
- [HIGH] description — file:line

## RECOMMENDATIONS
<fixes for each issue>

## COMPLIANCE
- OWASP Top 10 coverage
- GDPR considerations
```

## Constraints
- Do not commit while vulnerabilities exist
- Escalate critical issues immediately
