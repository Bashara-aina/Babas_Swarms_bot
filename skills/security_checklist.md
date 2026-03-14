# Security Checklist

## Input Validation
- Validate and sanitize all external input before processing
- Use parameterized queries for SQL (never string interpolation)
- Validate file paths to prevent directory traversal (`..`)
- Limit input sizes (max length, max file size)

## Secrets Management
- Never hardcode API keys, passwords, or tokens — use os.getenv()
- Never log secrets — redact before logging
- Use .env files excluded from git (.gitignore)
- Rotate compromised keys immediately

## Code Execution Safety
- Avoid eval(), exec(), compile() on user input
- Use subprocess with shell=False and explicit args list
- Sanitize shell arguments with shlex.quote()
- Set timeouts on all external calls

## Authentication & Authorization
- Verify user identity on every command (ALLOWED_USER_ID check)
- Use constant-time comparison for tokens (hmac.compare_digest)
- Rate limit sensitive operations

## Common Vulnerabilities (OWASP)
- Command injection: subprocess.run(["cmd", user_arg], shell=False)
- Path traversal: validate paths stay within allowed directory
- SSRF: validate URLs against allowlist before fetching
- Deserialization: never pickle.load() untrusted data — use JSON
