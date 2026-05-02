# Browser Stack Status — 2026-05-02

## Install Result
- browser-use: 0.12.6 (installed via pip)
- agent-browser: 0.26.0 (installed via npm)
- playwright: 1.58.0 (installed via pip)
- crawl4ai: 0.8.6 (already in stack)
- steel-browser: NOT AVAILABLE (Docker not accessible on this host)

## Integration Result
- MCP server: browser-use registered in opencode.json
- MCP tools: browser_open, browser_click, browser_fill, browser_scroll, browser_wait, browser_screenshot, browser_get_text, browser_get_html, browser_close, browser_run_task
- Slash commands: /browser (existing), /browse (new)
- Agents: browser department created at .opencode/agents/browser/ with browser-automation and web-researcher agents
- AGENTS.md: already has browser section (no update needed)
- CLAUDE.md: already has browser section (no update needed)
- Wiki: .wiki/architecture/browser-stack.md written
- WORKFLOW.md: created for symphony integration
- browser_task_router.py: created at tools/browser_task_router.py

## MiniMax Policy
- Guard script: scripts/browser_use_safe.sh (blocks forbidden models at exit 1)
- Guard script: scripts/agent-browser-safe.sh (blocks forbidden models at exit 1)
- Forbidden models: claude, anthropic, gpt-4, gpt-5, openai, gemini, groq, together, o1-, o3-, o4-
- Active model: minimax/MiniMax-M2.7 @ http://localhost:4000

## Verification
See: .opencode/logs/browser-e2e-test.txt

## Next Commands
```bash
# Quick health check
agent-browser --version

# Test browser-use MCP
echo '{"tool":"browser_health","args":{}}' | python3 -m tools.mcpServers.browser_use_mcp.server

# Smoke test with agent-browser
scripts/agent-browser-safe.sh open https://example.com
scripts/agent-browser-safe.sh snapshot -i --json
scripts/agent-browser-safe.sh screenshot /tmp/page.png

# Run browser task via Python
python3 tools/browser_task_router.py https://example.com "extract main content"
```
