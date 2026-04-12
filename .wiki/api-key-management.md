---
title: API Key Management
domain: api-integrations
impact_score: 8
last_updated: 2026-04-12
injects_into: all tools, llm_client, swarms_bot
tokens_estimated: 590
---

# API Key Management

## ONE-LINE SUMMARY
All 17+ API keys stored as environment variables via `os.getenv()`; no key rotation automation, no secret scanning for exposures, no key scoping by environment.

## FACTS

### Key Inventory
| Key | Used By | Storage | Rotation |
|-----|---------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | main.py | env | manual |
| `OPENROUTER_API_KEY` | llm_client, browser_agent | env | manual |
| `ANTHROPIC_API_KEY` | llm_client | env | manual |
| `MINIMAX_API_KEY` | llm_client | env | manual |
| `GROQ_API_KEY` | llm_client, mem0_client, swarm_wire | env | manual |
| `GITHUB_TOKEN` / `GITHUB_API_TOKEN` | github.py, proactive_engine | env | manual |
| `BRAVE_SEARCH_API_KEY` | research.py | env | manual |
| `OPENWEATHERMAP_API_KEY` | productivity.py | env | manual |
| `GOOGLE_PLACES_API_KEY` | location_aware.py | env | manual |
| `COMPOSIO_API_KEY` | composio_hub.py | env | manual |
| `SUPABASE_URL` | supabase_client | env | manual |
| `SUPABASE_ANON_KEY` | supabase_client | env | manual |
| `SUPABASE_SERVICE_ROLE_KEY` | supabase_client, business_ops | env | manual |
| `FIRECRAWL_API_KEY` | scraper_tool.py | env | manual |
| `TAVILY_API_KEY` | search_tool.py | env | manual |
| `RAGFLOW_API_KEY` | rag_tool.py | env | manual |
| `TODOIST_API_KEY` | project_manager.py | env | manual |
| `LINEAR_API_KEY` | project_manager.py | env | manual |
| `OPENAI_API_KEY` | memoryos_client.py | env | manual |
| `AGENTOPS_API_KEY` | observability/__init__.py | env | manual |
| `SECRET_KEY` | scaffolder.py | env | manual |

### Storage Pattern (Universal)
```python
api_key = os.getenv("SERVICE_API_KEY", "")
if not api_key:
    logger.warning("[service] API key not set — feature disabled")
    return error_dict
```
- Every tool checks for key existence before attempting API calls
- Missing key → graceful degradation (logged warning + error return)
- No hardcoded fallbacks with real keys
- No keys stored in config files, only env

### Authentication Strategy
1. **Env-only storage** — keys never in code, config, or database
2. **Lazy initialization** — ComposioToolSet, SupabaseClient, etc. init on first use, not at import
3. **Graceful degradation** — missing key returns error dict, does not raise exception to user
4. **Security Guard scanning** — credential pattern detection on all input/output (`guard.py:75-85`):
   ```python
   _CREDENTIAL_PATTERNS = [
       r"sk-[A-Za-z0-9\-_]{8,}",
       r"sk-ant-[A-Za-z0-9-]{40,}",
       r"gsk_[A-Za-z0-9]{40,}",
       r"AIzaSy[A-Za-z0-9_-]{33}",
       r"ghp_[A-Za-z0-9]{36}",
       r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
   ]
   ```
5. **Output filtering** — `SecurityGuard.filter_output()` blocks any LLM response containing credential patterns

### Key Scoping
- **Production keys**: in `.env.production` (NEVER edit directly)
- **Development keys**: in `.env.local`
- **CI/secret management**: via environment injected at deploy time
- **No key rotation automation** — manual process, no cron, no expiration tracking
- **Supabase two-key pattern**: ANON_KEY (public, RLS-gated) + SERVICE_ROLE_KEY (bypass RLS, internal only)

### Supabase Key Pattern
```python
# supabase_client.py
_anon = anon_key or os.getenv("SUPABASE_ANON_KEY", "")
_svc = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# business_ops.py
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # Note: different env var name!
```
**Risk**: `business_ops.py` uses `SUPABASE_SERVICE_KEY` while `supabase_client.py` uses `SUPABASE_SERVICE_ROLE_KEY` — duplicate env var names may cause silent failures.

## LEGION BEHAVIOR RULES
1. All API keys via `os.getenv()` — no exceptions
2. Missing key → log warning, return error dict, never crash
3. Security Guard scans for credential patterns in all user I/O
4. Output filter blocks any response containing live API key patterns
5. No key rotation, expiration tracking, or automatic refresh
6. No key scope by IP/rate-limit in code

## EXAMPLES

Key check before LLM call:
```python
def verify_api_keys() -> dict[str, bool]:
    keys = {
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "minimax": bool(os.getenv("MINIMAX_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
    }
    return keys
```

Graceful Composio init:
```python
api_key = os.getenv("COMPOSIO_API_KEY", "")
if not api_key:
    logger.info("[ComposioHub] COMPOSIO_API_KEY not set — Composio features disabled")
    return None
_composio_toolset = ComposioToolSet(api_key=api_key)
```

## ANTI-PATTERNS
1. **Duplicate env var names** — `SUPABASE_SERVICE_ROLE_KEY` vs `SUPABASE_SERVICE_KEY` means one will silently not read
2. **No key expiration tracking** — expired API keys cause silent failures (no alerting)
3. **No key rotation automation** — rotation requires manual env update + bot restart
4. **No scope restrictions** — keys grant full access, not scoped to specific endpoints/rates
5. **No secret scanning in git** — no pre-commit hook to catch accidentally committed keys

## GAPS
1. **No automatic rotation** — keys must be manually updated in env
2. **No key expiration monitoring** — no check for expiring keys before they fail
3. **No scope/permissions documentation** — no record of what each key can access
4. **No secret scanning pre-commit** — credentials could be committed to git
5. **Duplicate env var names** — `SUPABASE_SERVICE_ROLE_KEY` vs `SUPABASE_SERVICE_KEY` causes ambiguity
6. **No key per-environment separation** — same keys used in dev and production

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 7
Judge note: API key management is solid on the "no hardcoding" rule but weak on rotation/expiration/duplicates. Security Guard is good. Duplicate env var names are a real risk. Score 7 — write, note duplicates as risk.