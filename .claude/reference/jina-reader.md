---
name: jina-reader
description: >
  Convert any URL into LLM-friendly clean markdown. Web search via s.jina.ai.
  Self-hostable via Docker. Config headers: engine, preset, timeout, selectors.
---

Jina Reader (Jina AI, Apache-2.0) converts URLs into clean markdown for
LLM consumption. Provides 4 MCP tools for reading, searching, and batch
content extraction.

## Quick Reference

```
# Read a URL → clean markdown
jina_read:
  url: "https://example.com/article"
  format: "markdown"              # or html, text, screenshot, frontmatter
  engine: "auto"                  # or browser, curl
  no_cache: true                  # bypass cache

# Search the web → full-content results
jina_search:
  query: "latest AI research 2026"
  site: "arxiv.org"               # restrict to domain

# Structured JSON output  
jina_read_json:
  url: "https://example.com"

# Batch read
jina_batch:
  urls: ["url1", "url2", "url3"]
```

## Tools

| Tool | Description |
|------|-------------|
| `jina_read` | URL → markdown. Supports PDFs, Office docs, images with captioning. |
| `jina_search` | Web search → top 5 results as clean markdown. Full content, not snippets. |
| `jina_read_json` | URL → structured JSON (title, content, url, description). |
| `jina_batch` | Multiple URLs concurrently (max 10). |

## Key Parameters

| Parameter | Options | Effect |
|-----------|---------|--------|
| format | `markdown`, `html`, `text`, `screenshot`, `frontmatter` | Output format |
| engine | `auto`, `browser`, `curl` | Rendering engine |
| preset | `reader`, `index`, `research`, `agent`, `spider` | Pre-packaged config bundle |
| target_selector | CSS selector | Scope extraction to one element |
| wait_for_selector | CSS selector | Wait for element (SPA support) |
| timeout | 1-180 seconds | Max wait time |
| proxy | `auto` or custom URL | Route through proxy pool |

## Presets

- **reader** — human-readable display
- **index** — semantic indexing pipelines
- **research** — structured, citable output for AI agents
- **agent** — everyday browsing for AI agents
- **spider** — recursive crawling with full link inventory

## Architecture

```
LLM → MCP Router → jina_reader MCP server → r.jina.ai / s.jina.ai
                                              ├── headless Chrome (browser)
                                              ├── curl-impersonate (lightweight)
                                              └── PDF.js / LibreOffice (documents)
```

## Self-Hosting

```bash
docker pull ghcr.io/jina-ai/reader:oss
docker run --rm -p 3000:8081 ghcr.io/jina-ai/reader:oss
export JINA_READER_URL=http://localhost:3000
```

## Reference

- Upstream: https://github.com/jina-ai/reader (Apache-2.0, Jina AI)
- Docker: `ghcr.io/jina-ai/reader:oss`
- Server: `tools/mcpServers/jina_reader_mcp/server.py`
