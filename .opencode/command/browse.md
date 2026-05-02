---
description: Quick browser open + snapshot. Alias for /browser for fast navigation and page inspection.
---

Quick navigation using agent-browser CLI:

```bash
# Open a URL
scripts/agent_browser_safe.sh open $1

# Get page snapshot as JSON
scripts/agent_browser_safe.sh snapshot -i --json

# Take a screenshot
scripts/agent_browser_safe.sh screenshot /tmp/page.png
```

For full autonomous browser tasks with AI reasoning, use /browser instead.

## Routing
| Task type | Tool |
|-----------|------|
| Quick page inspection | agent-browser CLI |
| Multi-step autonomous browsing | /browser (browser-use) |
| Static content extraction | crawl4ai |
| Bulk scraping | crawl4ai |