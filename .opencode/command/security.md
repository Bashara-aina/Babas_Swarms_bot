---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic>
description: "Security audit. Check for vulnerabilities, secret leaks, input validation, injection risks."
---

# /security — Security audit

Audit code for security vulnerabilities and best practices.

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
