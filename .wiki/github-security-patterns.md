---
title: github-security-patterns
domain: git-version-control
impact_score: 8
last_updated: 2026-04-12
injects_into: handlers/github_intel_handler.py, tools/composio_hub.py, core/self_upgrade.py, tools/github_intel.py
tokens_estimated: 510
---

# GitHub Security Patterns

## ONE-LINE SUMMARY
Token storage, repo permissions, authentication failure handling, and webhook security for GitHub integrations.

## FACTS

### Token Storage

**GITHUB_TOKEN** (used in `core/self_upgrade.py:_fetch_trending_repos`):
```python
token = os.getenv("GITHUB_TOKEN", "")
headers = {"Accept": "application/vnd.github.v3+json"}
if token:
    headers["Authorization"] = f"token {token}"
```
- Stored as env var — NEVER hardcoded
- Optional — code works unauthenticated (with lower rate limits)
- Only used for GitHub Search API calls in `self_upgrade.py`
- NOT used in `tools/github_intel.py` (which uses Playwright scraping instead)

**COMPOSIO_API_KEY** (used in `tools/composio_hub.py:_get_composio_toolset`):
```python
api_key = os.getenv("COMPOSIO_API_KEY", "")
# Passed to ComposioToolSet(api_key=api_key)
```
- Stored as env var — NEVER hardcoded
- Optional — graceful degradation if missing
- Used for all Composio actions (Gmail, Calendar, GitHub, WhatsApp)
- Managed by Composio SDK — token refresh handled by Composio

**TELEGRAM_BOT_TOKEN**:
- From `os.getenv("TELEGRAM_BOT_TOKEN", "")`
- Logged in plaintext in `bot.log` if `_trim_log_text()` doesn't catch it — see `security-audit.md`
- Must be scrubbed from all log output

### No Token in URL / Query String
All API calls use HTTP headers for auth:
- GitHub: `Authorization: token {GITHUB_TOKEN}` header
- Composio: api_key passed to SDK constructor (not in URL)
- No tokens in query parameters or URL paths

### Repo Permissions

**Public repos**: Fully accessible via GitHub Search API and raw README URLs
**Private repos**: NO ACCESS — Legion only fetches public trending and public READMEs

No permission checks exist:
- `self_upgrade.py:_fetch_trending_repos` has no permission check
- `github_intel.py:fetch_readme` has no permission check  
- `composio_hub.py:composio_action` cannot audit Composio's repo permissions

**GITHUB_TOKEN scope**: Unclear what scope the token has — no scope validation in code.

### Authentication Failures

| Scenario | What happens |
|----------|--------------|
| `GITHUB_TOKEN` missing | Uses unauthenticated GitHub Search API (10 req/min limit) — works but slow |
| `GITHUB_TOKEN` invalid | GitHub API returns 401 — logged as warning, returns `[]` — silent degradation |
| `COMPOSIO_API_KEY` missing | Returns `{"error": "Composio not configured..."}` — graceful error dict |
| `COMPOSIO_API_KEY` invalid | Composio SDK init fails — logged as warning, returns error dict |
| README fetch 404 | Returns empty string `""` — no crash, no error to user |
| GitHub API 403 rate limit | Returns `[]` — silent degradation |
| Network timeout | `aiohttp.ClientTimeout(total=15)` — hard timeout, returns empty |

**No auth failure alert to user**: Authentication failures are logged but users get no Telegram message.

### Webhook Security

**No webhook receiver configured** — Legion does NOT receive GitHub webhooks.

This means:
- No webhook signature verification (`X-Hub-Signature-256` header not checked)
- No webhook endpoint in handlers/ — `github_intel_handler.py` has no webhook routes
- No real-time PR/issue/comment updates

**Security implication**: Attackers cannot send fake GitHub webhook payloads to Legion because no webhook endpoint exists. This is a security positive but a capability gap.

### Composio Token Security

Composio manages GitHub OAuth tokens internally:
- No GitHub App token visible in code
- No user OAuth token stored by Legion
- Composio SDK handles token refresh automatically

**Risk**: If Composio is compromised, all connected GitHub repos could be accessed. Mitigation: Composio is a hosted service with its own security posture.

### Secret Scanning

**No secret scanning in code** — `self_upgrade.py` does NOT scan generated code for embedded secrets.

Security checks performed on generated code:
1. `ast.parse()` — syntax validation only
2. Pattern blocklist (`_BLOCKED_PATTERNS`) — blocks dangerous patterns like `os.system`, `subprocess.call`, `eval`, `exec`, `rm -rf`, `shutil.rmtree`
3. Path validation — blocks `../` and absolute paths

**NOT checked**: embedded API keys, tokens, passwords in generated code.

### Allowed User Restriction

GitHub commands (`/github_intel`, `/eval_repo`, `/upgrade_from`) are restricted to `ALLOWED_USER_ID`:
```python
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

def _is_allowed(msg: Message) -> bool:
    return msg.from_user is not None and msg.from_user.id == ALLOWED_USER_ID
```
- If user not allowed: silent return (no message sent)
- `ALLOWED_USER_ID` has 4 separate sources of truth — see `security-audit.md`

## GAPS

1. **No webhook receiver** — real-time GitHub updates not possible
2. **No secret scanning** in self-upgrade generated code
3. **No GitHub token scope validation** — cannot confirm what the token can access
4. **4 separate ALLOWED_USER_ID sources** — inconsistency risk
5. **No auth failure notification** — silent degradation, user doesn't know GitHub API failed
6. **Private repo detection** — no check if a repo is private before attempting fetch
7. **Composio GitHub permissions** — opaque, cannot audit what Composio has access to
