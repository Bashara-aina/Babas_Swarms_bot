---
title: Github Integration Guide
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- github-integration-guide.md
created: '2026-04-14'
updated: '2026-04-14'
summary: How Legion fetches GitHub data, which API endpoints are used, how rate limits
  are handled, and what error handling exists.
wikilinks: []
confidence: medium
source: research
---

# GitHub Integration Guide

## ONE-LINE SUMMARY
How Legion fetches GitHub data, which API endpoints are used, how rate limits are handled, and what error handling exists.

## FACTS

### API Endpoints Used

**GitHub Search API** (via `core/self_upgrade.py:_fetch_trending_repos`):
```
GET https://api.github.com/search/repositories?q=topic:{topic} stars:>100&sort=stars&order=desc&per_page={limit}
Headers: Accept: application/vnd.github.v3+json
Headers: Authorization: token {GITHUB_TOKEN}   (if GITHUB_TOKEN is set)
```

**GitHub Trending HTML Scraping** (via `tools/github_intel.py:fetch_trending`):
```
GET https://github.com/trending/{language}?since={daily|weekly|monthly}
Fallback: raw aiohttp GET if Playwright fails
```

**README Fetching** (via `tools/github_intel.py:fetch_readme`):
```
GET https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/main/README.md
Fallback: /master/README.md
Timeout: 15s per attempt
Max content: 6000 chars
```

### Composio GitHub Integration (via `tools/composio_hub.py`)
- Composio provides 850+ tool connectors including GitHub actions
- Composio wraps `GITHUB_*` actions via `composio_action("GITHUB_*")`
- Token management handled by Composio SDK — no direct token handling in composio_hub.py
- Graceful degradation if `COMPOSIO_API_KEY` not set

### GitHub Actions Supported
| Action | Source | What it does |
|--------|--------|--------------|
| `/github_intel` | `handlers/github_intel_handler.py` | Scrape trending Python repos + LLM evaluation |
| `/eval_repo <url>` | `handlers/github_intel_handler.py` | Fetch README, evaluate specific repo |
| `/upgrade_from <url>` | `handlers/github_intel_handler.py` | Fetch README → SelfUpgradeEngine pipeline |
| Trending scan | `tools/github_intel.py:run_daily_scan` | Daily scheduled scan + skill auto-discovery |
| GitHub search | `core/self_upgrade.py:scan_github_trending` | topic-based search for self-upgrade targeting |
| Composio GitHub | `tools/composio_hub.py:composio_action` | Generic GitHub actions via Composio SDK |

**No direct PR/issue/commit API calls** — all GitHub integration is via:
1. Trending HTML scrape
2. README content fetch
3. GitHub Search API (repos only)
4. Composio wrappers (external)

### Rate Limit Handling

**Current mitigations in code:**
- `tools/github_intel.py:evaluate_all`: max 5 parallel evaluations, 1s delay between batches
- `aiohttp.ClientTimeout(total=15)` on all HTTP calls — hard timeout prevents hang
- Playwright → aiohttp fallback chain — if trending page fails, falls back to raw GET
- `asyncio.to_thread()` wraps all blocking pip install in self-upgrade

**What happens on rate limit:**
- `self_upgrade.py:_fetch_trending_repos`: logs warning on non-200 response, returns empty list
- `github_intel.py:evaluate_all`: continues with successful results, logs failed evals
- No retry-with-backoff implemented — rate limit causes silent degradation (empty results)

**GitHub unauthenticated rate limit**: 10 requests/minute for search API
**GitHub authenticated rate limit**: 30 requests/minute for search API
**Solution**: `GITHUB_TOKEN` env var increases rate limit 3x

### Error Handling

| Error type | Response |
|------------|----------|
| GitHub scrape fails | Falls back to aiohttp raw GET → returns `[]` |
| README fetch fails | Returns empty string `""`, no crash |
| LLM eval fails | Logs warning, returns `RepoEvaluation` with score 0 |
| Rate limited | Returns empty results, logs warning |
| Invalid JSON from LLM | Falls back to `{}`, logs warning |
| Composio not configured | Returns `{"error": "Composio not configured..."}` |
| Token missing | Uses unauthenticated endpoints (lower rate limit) |

### No PR/Commit API Usage
Legion does NOT use:
- `GET /repos/{owner}/{repo}/pulls` — no PR status checking
- `GET /repos/{owner}/{repo}/commits` — no commit history analysis  
- `GET /repos/{owner}/{repo}/issues` — no issue tracking
- Webhooks — no webhook receiver configured

## ARCHITECTURE

```
handlers/github_intel_handler.py
  /github_intel     → GitHubIntelEngine.fetch_trending() → browse_url() → Playwright → html.parse
  /eval_repo        → GitHubIntelEngine.fetch_readme()   → raw.githubusercontent.com
  /upgrade_from    → GitHubIntelEngine.fetch_readme()  → SelfUpgradeEngine.upgrade()

tools/github_intel.py
  GitHubIntelEngine
    fetch_trending()       → Playwright or aiohttp fallback
    evaluate_all()        → litellm (5-parallel batched)
    _discover_skill()     → litellm draft → sandbox smoke test → write skills/*.md

core/self_upgrade.py
  SelfUpgradeEngine
    scan_github_trending()  → aiohttp GitHub Search API
    _llm_evaluate_repo()    → litellm structured eval

tools/composio_hub.py
  composio_action()         → ComposioToolSet (GitHub actions via Composio SDK)
```

## GAPS

1. **No retry-with-backoff** — rate limit hits cause empty results silently
2. **No PR/commit/issue API** — only repo-level and README data
3. **No repo permission check** — cannot detect if token lacks access to private repos
4. **Composio GitHub token** — managed by Composio, not visible/auditable in code
5. **README-only content** — no code files fetched, only top 6000 chars of README
6. **No commit/PR status** — cannot determine if a repo is active, stale, or maintained
