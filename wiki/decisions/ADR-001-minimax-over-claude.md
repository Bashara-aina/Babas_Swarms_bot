# ADR-001: MiniMax M2.7 over Claude Code
- Date: 2026-04-10
- Status: Accepted
- Context: Claude Code blocked third-party API OAuth on 2026-04-04
- Decision: Migrate to OpenCode + MiniMax M2.7 Token Plan
- Cost: ~95% cheaper ($0.30/M input vs $3.00/M)
- Benchmark: MiniMax M2.7 scored 87.4% GPQA, #2 agentic benchmark
- Consequences: No vendor lock-in, multi-model flexibility, 1M context window

## Fallback Chain (Updated 2026-04-11)

All 22 legacy agents now use a 3-tier fallback chain:

1. **Primary:** `minimax/MiniMax-M2.7` — fast, cheap, high quality
2. **Fallback 1:** `ollama_chat/llama3.3:70b` — local, no API cost
3. **Fallback 2:** `ollama_chat/gemma4:e4b` — local, alternative

Local models only activate when MiniMax fails or is unavailable. Retry uses exponential backoff + jitter (~30s → ~60s → ~120s).