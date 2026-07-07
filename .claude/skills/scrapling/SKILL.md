---
name: scrapling
description: >
  Skill for adaptive web scraping. Provides MCP tools for HTTP/stealth/dynamic
  fetch, CSS/XPath extraction, HTML parsing, and batch crawling via Scrapling.
---

# Scrapling Skill

Scrapling is an adaptive Python web scraping framework (67.9k stars) that
handles everything from single HTTP requests to full-scale concurrent crawls.
This skill brings all of Scrapling's capabilities into native MCP tools.

## Tools Available

| Tool | What It Does |
|------|-------------|
| `scrapling_fetch` | Fast HTTP GET with browser TLS fingerprint impersonation. Best for static HTML. |
| `scrapling_stealth` | Stealth mode: bypasses Cloudflare, Turnstile, interstitial protections. |
| `scrapling_dynamic` | Full browser automation via Playwright for JS-rendered content. |
| `scrapling_extract` | Fetch + CSS/XPath extraction in one call. The primary workhorse. |
| `scrapling_extract_multi` | Batch extract from multiple URLs concurrently. |
| `scrapling_parse` | Parse raw HTML locally with CSS/XPath/filter/text search. |
| `scrapling_find_selectors` | Given HTML and target text, returns robust CSS selectors. |

## Common Workflows

### Extract article text from a page

Use `scrapling_extract` with CSS selector `article::text` or `.content p::text`.

### Scrape a list page

`scrapling_extract` with `all_matches: true` on repeating elements (e.g.
`.listing-item .title::text`, `.listing-item .price::text`).

### Get all links from a page

`scrapling_extract` with `css: "a::attr(href)"`.

### Bypass Cloudflare

Use `scrapling_stealth` with `solve_cloudflare: true`.

### Batch monitor multiple pages

`scrapling_extract_multi` with the same CSS selector applied to all URLs.

## Reference

- Full reference: `.claude/reference/scrapling.md`
- MCP server: `tools/mcpServers/scrapling_mcp/server.py`
- Upstream: https://github.com/d4vinci/Scrapling
