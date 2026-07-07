---
name: jina-reader
description: >
  Convert any URL into LLM-friendly clean markdown. Web search via s.jina.ai.
  Self-hostable via Docker. Best for: reading articles, research, documentation.
---

# Jina Reader Skill

Jina Reader (Apache-2.0, Jina AI) converts web pages into clean markdown
optimized for LLM consumption. No ads, no navigation, just content.
Self-hostable via `ghcr.io/jina-ai/reader:oss`.

## Tools

| Tool | What It Does |
|------|-------------|
| `jina_read` | Convert URL → clean markdown. Supports PDF, Office docs, images. |
| `jina_search` | Search web → top 5 results as markdown (via s.jina.ai). |
| `jina_read_json` | Read URL → structured JSON (title, content, url, metadata). |
| `jina_batch` | Read multiple URLs concurrently (max 10). |

## Common Workflows

### Read an article for research
`jina_read` with default settings. Returns clean markdown.

### Search with full content
`jina_search` — unlike snippet-based search, each result is fetched
through the full Reader pipeline so you get complete page content.

### PDF-to-markdown
`jina_read` on a PDF URL. Reader parses PDFs via PDF.js.

### Compare multiple sources
`jina_batch` with 3-5 URLs. Each is fetched concurrently.

### Structured data extraction
`jina_read_json` when you need machine-parseable output.

## Configuration Headers (via tool params)

| Param | Effect |
|-------|--------|
| `engine: browser` | Force headless Chrome rendering (for JS-heavy sites) |
| `engine: curl` | Lightweight fetch (faster, static pages) |
| `no_cache: true` | Bypass cached response |
| `target_selector` | CSS selector to scope extraction |
| `wait_for_selector` | Wait for element before returning (SPAs) |
| `preset: research` | Pre-packaged config for AI research |

## Reference

- Full reference: `.claude/reference/jina-reader.md`
- MCP server: `tools/mcpServers/jina_reader_mcp/server.py`
- Upstream: https://github.com/jina-ai/reader (Apache-2.0)
- Docker: `ghcr.io/jina-ai/reader:oss`
