# Session State: OpenCode Go Proxy — Claude-Style Role Presets

## What We Did
1. **Installed oc-cc-proxy** (v0.1.3) — LiteLLM proxy bridging Claude Code (Anthropic API) → OpenCode Go
2. **Replaced MiniMax direct API** with OpenCode Go passthrough via proxy on port 4001
3. **Configured 4 Claude-style role presets** mapping to Go's best 1M-context models
4. **Updated all API keys** across .env, .claude/settings.json, and mirofish backend
5. **Submitted feature request** to OpenCode Go: https://github.com/anomalyco/opencode/issues/31833

## Architecture
```
Claude Code → ANTHROPIC_BASE_URL=http://127.0.0.1:4001
              ↓
        oc-cc-proxy (:4001)
          ├── Haiku  → deepseek-v4-flash  (31,650 calls/5h)
          ├── Sonnet → deepseek-v4-pro    (3,450 calls/5h)
          ├── Opus   → minimax-m3         (3,200 calls/5h)
          └── Fable  → kimi-k2.6          (1,200 calls/5h)
              ↓
        OpenCode Go API (opencode.ai/zen/go/v1)
```

## Running Process
- **oc-cc-proxy** (litellm) on `:4001` — Anthropic→OpenAI wildcard passthrough to OpenCode Go
- Start: `scripts/start-oc-cc-proxy.sh` or `oc-cc-proxy --api-key $OPENCODE_GO_API_KEY --port 4001`

## Key Config
- `settings.json`: `ANTHROPIC_BASE_URL = http://127.0.0.1:4001`
- `settings.json`: `ANTHROPIC_API_KEY = dummy-key-for-claude-code` (proxy handles real auth)
- `.env`: `OPENCODE_GO_API_KEY = sk-RzkWr...` (real key for proxy)
- `.env`: `OC_PROXY_PORT = 4001`

## Validated Models (through proxy)
- `deepseek-v4-flash` ✅ (fast, high-volume)
- `deepseek-v4-pro` ✅ (workhorse, reasoning)
- `minimax-m3` ✅ (orchestrator)
- `kimi-k2.6` ✅ (hardest reasoning)
- `qwen3.6-plus` ✅ (alternative)
- `glm-5.1` ✅ (alternative)
- `MiniMax-M3` ❌ (not available on Go — use `minimax-m3` lowercase)
- `qwen3.7-max` ❌ (auth error on Go)
