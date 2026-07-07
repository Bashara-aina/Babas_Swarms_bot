---
name: scrapling
description: >
  Adaptive web scraping framework — HTTP/stealth/dynamic fetchers, CSS/XPath
  parser (780x faster than BS4), spider crawler. Use for scraping, extraction,
  data collection, and web research.
---

Exposes Scrapling (67.9k stars, BSD-3-Clause) as native MCP tools for
AI-assisted web scraping. Covers the full pipeline: fetch → parse → extract.

## Tools

| Tool | Use Case |
|------|----------|
| `scrapling_fetch` | Fast HTTP GET with browser TLS fingerprint. Static HTML pages. |
| `scrapling_stealth` | Cloudflare bypass, anti-bot evasion, protected pages. |
| `scrapling_dynamic` | Full browser automation for JS-rendered content. |
| `scrapling_extract` | **Killer feature**: fetch + extract specific elements via CSS/XPath in one call. |
| `scrapling_extract_multi` | Batch extract from multiple URLs concurrently. |
| `scrapling_parse` | Parse HTML text locally (no network) — CSS/XPath/filter/text search. |
| `scrapling_find_selectors` | Given HTML + target text, generate robust CSS selectors. |

## Quick Usage

```
scrapling_extract:
  url: "https://example.com/page"
  css: ".article .title::text"          # ::text for text, ::attr(href) for links
  all_matches: true                     # true = all matches, false = first only

scrapling_fetch:
  url: "https://example.com"
  impersonate: "chrome131"             # or edge, safari, firefox, with version
  extract_text: true                    # strip HTML tags

scrapling_stealth:
  url: "https://protected-site.com"
  solve_cloudflare: true
  adaptive: true                        # survive site redesigns
```

## Selector Syntax (use with extract/parse tools)

- `tag` — element by tag name
- `.classname` — by class
- `#id` — by ID
- `div p` — descendant
- `div > p` — direct child
- `::text` — extract text content
- `::attr(href)` — extract attribute value
- `:nth-child(n)` — positional

## When to Use Which

- **Static pages** → `scrapling_fetch` or `scrapling_extract` (fastest)
- **Cloudflare/DDOS protected** → `scrapling_stealth`
- **JS-rendered (React, Vue, SPAs)** → `scrapling_dynamic`
- **Batch data collection** → `scrapling_extract_multi`
- **Parse saved/cached HTML** → `scrapling_parse`
- **Find what selector to use** → `scrapling_find_selectors`

## Architecture

```
LLM → MCP Router → scrapling MCP server → scrapling library
                                              ├── Fetcher (HTTP+SSL)
                                              ├── StealthyFetcher (browser)
                                              ├── DynamicFetcher (Playwright)
                                              └── Selector (parser)
```

## Reference

- Upstream: https://github.com/d4vinci/Scrapling (BSD-3-Clause, v0.4.9)
- Docs: https://scrapling.readthedocs.io/en/latest/
- Server: `tools/mcpServers/scrapling_mcp/server.py`
