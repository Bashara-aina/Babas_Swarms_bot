---
title: email-security-patterns
domain: communications
impact_score: 8
last_updated: 2026-04-12
injects_into: security, agents
tokens_estimated: 400
---

# Email Security Patterns

## ONE-LINE SUMMARY
Email display uses html.escape() for HTML injection prevention but has NO anti-phishing/content scanning — all email content trusted for display.

## HTML ESCAPE PATTERN

All email fields are escaped before Telegram HTML rendering:

```python
# handlers/communications.py cmd_emails()
sender = html.escape(str(e.get("from", e.get("sender", "Unknown")))[:60])
subject = html.escape(str(e.get("subject", "No subject")))[:80])
snippet = html.escape(str(e.get("snippet", e.get("body", "")))[:120])
lines.append(f"<b>From:</b> {sender}\n<b>Subject:</b> {subject}\n<i>{snippet}</i>\n")
```

This prevents:
- **HTML injection**: `<script>alert(1)</script>` in subject → rendered as text
- **XSS via email**: Malicious links displayed as plain text
- **Emoji/payload attacks**: HTML entities escaped

## WHAT IS ESCAPED

| Field | Source | Escaped |
|-------|--------|---------|
| `from` | Gmail `from`/`sender` field | ✅ html.escape() |
| `subject` | Gmail subject | ✅ html.escape() |
| `snippet` | Gmail snippet/body preview | ✅ html.escape() |
| URL links | If any appear in content | ⚠️ Not extracted/scanned |
| Attachments | File names/types | ❌ Not displayed |

## WHAT IS NOT PROTECTED

### No URL Scanning
Links in email body are NOT extracted or scanned:
- Phishing URLs in body text pass through as plain text
- No URL reputation check
- No warning for suspicious domains

### No Sender Verification
- `from` field displayed but not verified against known contacts
- No check against bashara's contact list
- No DMARC/SPF/DKIM verification display

### No Content Analysis
- No scanning for suspicious patterns (password requests, wire fraud indicators)
- No check for email thread anomalies (reply-chain manipulation)
- No detection of forward/redirect patterns

### No Attachment Handling
- Attachments not displayed (only snippet shown)
- No file type warnings
- No sandboxing of downloaded attachments

## SEND EMAIL SECURITY

`gmail_send()` has NO content filtering:
```python
async def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    return await gmail_send(to=to, subject=subject, body=body)
```

Any content can be sent:
- No subject line validation
- No recipient verification (except Gmail API format check)
- No content policy enforcement
- No rate limiting on sends

## WHATSAPP SECURITY

Same pattern — `send_whatsapp_message()` sends any content:
```python
async def send_whatsapp_message(to: str, message: str) -> dict[str, Any]:
    return await composio_action("WHATSAPP_SEND_MESSAGE", {"to": to, "message": message})
```

## COMPOSIO OAUTH SECURITY

Composio manages OAuth tokens securely:
- Tokens stored by Composio, not in code
- Token refresh automatic
- No plaintext credential storage
- Revocation: run `composio logout` on server

## RECOMMENDED ADDITIONS

### 1. URL Scanner
```python
async def scan_email_urls(email_body: str) -> list[dict]:
    """Extract and check URLs against known phishing patterns."""
    urls = re.findall(r'https?://[^\s<>"]+', email_body)
    # Check against threat intelligence feed
    # Return: [{url, status, reputation}]
```

### 2. Contact Verification
```python
def is_known_sender(sender_email: str) -> bool:
    """Check if sender is in Bashara's contact list."""
    # Compare against contacts from memory/supabase
```

### 3. Content Policy
```python
async def check_email_safe(subject: str, body: str) -> tuple[bool, str]:
    """Check email against security policy."""
    # Wire transfer keywords
    # Password reset patterns
    # Urgency manipulation
    # Return: (is_safe, reason)
```

### 4. Rate Limit on Sends
```python
SEND_RATE_LIMIT = 10  # max sends per hour
async def gmail_send_rate_limited(...):
    """Enforce rate limit before sending."""
```

## CURRENT RISKS

| Risk | Severity | Status |
|------|----------|--------|
| HTML injection in display | Low | ✅ Mitigated by html.escape() |
| Phishing URL display | Medium | ⚠️ Not scanned |
| Unauthorized send | High | ⚠️ No content policy |
| Reply-chain manipulation | Medium | ⚠️ No verification |
| OAuth token theft | Low | ✅ Composio manages |
| Rate limit abuse | Medium | ⚠️ No enforcement |

## DEBATE RECORD
Advocate: 8 | Skeptic: 7 | Judge: WRITE 8
Advocate note: Email security gap is real and actionable — html.escape is minimal protection.
Skeptic note: Most users won't encounter sophisticated email attacks; this is edge case.
Judge note: Security pages score high — documenting the gap is valuable even if unfixed.
