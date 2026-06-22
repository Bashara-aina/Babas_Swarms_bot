# 4-Tier Model Routing (OpenCode Go via oc-cc-proxy on :4001)

| Role | Model | Calls/5h | Use Cases |
|------|-------|----------|-----------|
| Haiku | deepseek-v4-flash | 31,650 | Review, search, autocomplete, refactors (~80% of traffic) |
| Sonnet | deepseek-v4-pro | 3,450 | Feature builds, 3-5 file edits, debugging |
| Opus | deepseek-v4-flash | 3,200 | Complex orchestrator, multi-file long runs |
| Fable | kimi-k2.6 | 1,200 | Hardest architecture & long-horizon reasoning |

## Tier Detection
- Model name contains `flash` → Haiku
- Model name contains `pro` → Sonnet
- Model name contains `opus` or `kimi` → Opus
- Model name contains `fable` or `glm` → Fable
