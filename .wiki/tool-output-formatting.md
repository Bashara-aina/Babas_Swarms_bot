---
title: Tool Output Formatting
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- tool-output-formatting.md
created: '2026-04-14'
updated: '2026-04-14'
summary: How tool output should be formatted for Telegram display — truncation, HTML,
  chunking.
wikilinks: []
confidence: medium
source: research
---

# Tool Output Formatting

## ONE-LINE SUMMARY
How tool output should be formatted for Telegram display — truncation, HTML, chunking.

## FACTS
- Telegram message limit: 4096 chars per message
- _format_for_telegram_html() in handlers/shared.py converts markdown → HTML before sending
- chunk_output() in llm_client.py chunks at 4000 chars for Telegram safety
- send_chunked() in handlers/shared.py uses chunk_output() + result_keyboard() on last chunk
- Code blocks: ``` fences converted to \n by _format_for_telegram_html() — loses syntax highlighting
- Inline code: `backticks` converted to <code> tags — works correctly
- Headers: # ## ### converted to <b> bold — works but loses hierarchy
- Bullets: - and * normalized to • — works correctly
- Long output: truncated at 4000 chars with "..." appended
- Telegram HTML: supports <b>, <i>, <code>, <pre>; does NOT support arbitrary HTML
- Images: sent via send_photo() with FSInputFile — separate from text flow
- Output logging: trimmed to 1200 chars in bot.log to avoid log bloat

## LEGION BEHAVIOR RULES
1. Use send_chunked() for all tool outputs that may exceed 4000 chars
2. Wrap user content in html.escape() before adding HTML tags — prevent HTML injection
3. Code output: use <pre><code>...</code></pre> instead of bare ``` — Telegram supports this
4. Tables: Telegram doesn't support tables — convert to "col1 | col2 | col3" format with fixed widths
5. Max output before truncation: 4000 chars — send_chunked handles this automatically
6. Images: always include caption with image description — never send image alone
7. Chunk delay: 0.3s asyncio.sleep between chunks — prevents Telegram rate limiting
8. Error output: limit to 300 chars — humanize_error_for_display() handles this
9. Never log raw user input in tool output — scrub tokens, API keys, personal data

## EXAMPLES
Bashara message: "run ls -la /tmp"
Legion output: "<pre><code>total 4096 drwxr-xr-x  3 newadmin newadmin  4096 Apr 12 11:00 /tmp\ndrwxr-xr-x  2 newadmin newadmin  4096 Apr 12 10:30 /tmp/legion</code></pre>"

Bashara message: "extract text from this PDF"
Legion output: "[File: contract.pdf — 12 pages]\nPage 1: Lorem ipsum dolor sit amet...\n[... 8 more pages truncated ...]\nFull extraction: stored in memory. Want me to analyze specific sections?"

Bashara message: "show gpu status"
Legion output: "🔴 GPU: 83°C | VRAM: 10.2/12GB (85%) | Util: 94%\n⚠️ Above threshold — something training?"

Bashara message: "scrape this shopee link"
Legion output: "Product: [Name] | Price: Rp 128.000 | Store: [Seller] | Stock: [available]\nImage: [photo with caption]"

## ANTI-PATTERNS
1. HTML injection: user message contains <script> and gets reflected in output unescaped — FIX: always html.escape user content
2. Code fence corruption: ```python\nprint("hi")\n``` gets converted to newline-separated text, losing structure — FIX: use <pre><code>
3. Oversized output: tool returns 10k chars → exceeds Telegram limit and message fails silently — FIX: always use send_chunked()
4. Chunk flooding: 20+ chunks sent rapidly → triggers Telegram rate limit — FIX: 0.3s delay between chunks, batch small outputs

## DEBATE RECORD
Advocate: 7 | Skeptic: 6 | Judge: WRITE 7
Judge note: Telegram formatting is a persistent pain point — this page captures the standards.
