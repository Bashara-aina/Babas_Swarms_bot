# Doc 208 — Expectations and Gap Playbook

**Purpose:** Track implementation status of all configuration levers and infrastructure
improvements identified in doc 207 (POPW multi-task model analysis) and the broader
system reliability audit. Each lever is classified by status, with probe results
where available.

---

## Status Overview

| Category | Levers | Implemented | Running | Warnings |
|---|---|---|---|---|
| Multi-task model config | 8 | 8/8 | N/A (code) | -- |
| Web fallback resilience | 1 | 1/1 | Passive | Needs real-world credit exhaustion test |
| MCP router expansion | 2 | 2/2 | Active | -- |
| LiteLLM config cleanup | 1 | 1/1 | Active | Ensure old model_list entries purged |
| Hook/settings simplification | 6 | 6/6 | Active | Quality gate timeout reduced 30s->5s |
| Agent documentation | 18 | 18/18 | Active | Cosmetic only (description bumps) |
| Web tool prefix registration | 4 | 4/4 | Active | -- |
| Scrapling v1.1.0 | 1 | 1/1 | Active | -- |

---

## Lever Details

### 1. Multi-task Model Configuration (`src/config.py`)

| Lever | doc 207 Value | Old Value | Status | Probe Result |
|---|---|---|---|---|
| `LV_CLAMP_MAX_DET` | 1.5 | 4.0 | **IMPLEMENTED** | Verified weight floor changes from exp(-4)~0.018 to exp(-1.5)~0.22 |
| `LV_CLAMP_MAX_POSE` | 2.0 | 4.0 | **IMPLEMENTED** | -- |
| `BATCH_SIZE` | 2 | (undefined) | **IMPLEMENTED** | OOM mitigation per doc 207 |
| `VAL_BATCH_SIZE` | 4 | (undefined) | **IMPLEMENTED** | Safe with torch.no_grad() |
| `RAM_CACHE_MAX_IMAGES` | 0 | (undefined) | **IMPLEMENTED** | RAM cache disabled by default |
| `ACT_CLASS_GROUPING` | "none" | "hybrid" | **IMPLEMENTED** | -- |
| `PSR_TRANSITION_BOOST` | 3.0 | (undefined) | **IMPLEMENTED** | Opus 207 section 4.3 value |
| `PSR_COMP_WEIGHTS` | [1.0, 1.21, 1.20, 1.98, 5.03, 1.61, 1.66, 2.20, 2.20, 2.75, 4.61] | (undefined) | **IMPLEMENTED** | Component 4 gets 5.03x, component 10 gets 4.61x (inverse prevalence) |

**All 8 model config levers are implemented.** The old `src/config.py` was a bare PSR-only
transition config; it has been replaced with a complete POPW multi-task model configuration
covering detection, head pose, activity classification, and PSR.

### 2. Web Fallback Resilience (`core/web_fallback.py` + `llm_client/__init__.py`)

| Lever | Status | Details |
|---|---|---|
| Web credit exhaustion detection | **IMPLEMENTED** | 17 regex patterns matching quota/rate-limit/credit errors |
| Fallback chain: SEARCH | **IMPLEMENTED** | firecrawl_search -> searxng_web_search -> jina_search -> exa_web_search |
| Fallback chain: FETCH | **IMPLEMENTED** | firecrawl_scrape -> crawl4ai_crawl -> jina_read -> scrapling_fetch |
| Fallback chain: CRAWL | **IMPLEMENTED** | firecrawl_crawl -> crawl4ai_crawl -> searxng_web_search |
| Arg mapping | **IMPLEMENTED** | Search, fetch, crawl arg shapes mapped across tool APIs |
| MCP tool prefix registration | **IMPLEMENTED** | firecrawl_, jina_, scrapling_, searxng_ added to self-heal routing |

**Passive.** The fallback chain only activates when the MCP router returns a credit/rate-limit
error. Needs real-world credit exhaustion to validate.

### 3. MCP Router Expansion (`core/mcp/router.py`)

| Server | Status | Notes |
|---|---|---|
| `firecrawl` | **IMPLEMENTED** | Added to TOOL_PREFIXES (firecrawl_), server config, and boot sequence |
| `searxng` | **IMPLEMENTED** | Added to server config and boot sequence |

### 4. LiteLLM Config Cleanup (`config/litellm_proxy_config.yaml`)

| Change | Status |
|---|---|
| Removed `opencode-go/*` entry | **IMPLEMENTED** |
| Removed `deepseek-v4-flash` double entry | **IMPLEMENTED** |
| Removed `nemotron` / OpenRouter entries | **IMPLEMENTED** |
| Removed `openrouter/*` wildcard | **IMPLEMENTED** |
| Added `minimax-coding-plan/MiniMax-M3` | **IMPLEMENTED** |
| Added `minimax-m3` (short name) | **IMPLEMENTED** |
| Added `ollama-llama3.3` fallback | **IMPLEMENTED** |

**Consolidated from ~15 model entries to 6.** All OpenRouter routes removed
in favor of MiniMax-M3 direct Anthropic-compatible API.

### 5. Hook/Settings Simplification (`.claude/settings.json`)

| Change | Status |
|---|---|
| Removed post-edit hooks (Write/Edit hook handler) | **IMPLEMENTED** |
| Removed PreCompact hooks (manual matcher) | **IMPLEMENTED** |
| Removed redundant governance-capture on PostToolUse | **IMPLEMENTED** |
| Quality gate timeout reduced 30s -> 5s | **IMPLEMENTED** |
| Added `track_context.py` registration in PostToolUse | **IMPLEMENTED** |
| Reordered user query hooks (track_context before hook-handler) | **IMPLEMENTED** |

### 6. Agent Documentation (`.claude/agents/*.md`)

All 18 agent files received a minor update. Change is cosmetic only — the second
sentence of each agent's description was dropped for brevity. No functional changes.

### 7. CLAUDE.md Simplification

| File | Old Lines | New Lines | Delta |
|---|---|---|---|
| `/CLAUDE.md` (root) | 163 | 28 | -135 |
| `.claude/CLAUDE.md` | 47 | 8 | -39 |

Root `CLAUDE.md` trimmed: removed verbose on-demand reference list, Karpathy
principles section, Superpowers SDLC details. Kept core rules, swarm, GitNexus.
`.claude/CLAUDE.md` trimmed: removed graphify details, session management,
obsidian vault, cognee, design rules, Fable 5 patterns. Kept concise references.

### 8. Scrapling v1.1.0 (`tools/mcpServers/scrapling_mcp/server.py`)

Updated from v1.0.0 to v1.1.0. Changes:
- Trimmed module docstring (from 13 lines to 1)
- Added Scrapling v0.4.9 Response object compatibility
- Cleaned up helper functions
- Shortened internal comments

### 9. Tool Description Trimming (crawl4ai, searxng)

MCP tool descriptions shortened across crawl4ai (3 tools) and searxng (2 tools)
to reduce token overhead per tool listing.

### 10. VSCode MCP Configuration (`.vscode/mcp.json`)

Added 8 new MCP server definitions:
- scrapling_mcp, crawl4ai_mcp, jina_reader_mcp, searxng_mcp
- browser_use_mcp, textidote_mcp, paperpal_mcp, paperdebugger_mcp

---

## Gaps

1. **No end-to-end integration test for web fallback.** The `core/web_fallback.py`
   module has unit-testable helpers but no test file was created. Recommend adding
   `tests/test_web_fallback.py` covering:
   - Credit exhaustion detection (each regex pattern)
   - Fallback chain selection for each tool family
   - Argument mapping edge cases (missing query, missing URL, list vs string)
   - Full integration with `_execute_tool_with_self_heal`

2. **No validation run for new LV_CLAMP values.** The clamp changes from 4.0 to
   1.5/2.0 are theoretically correct per doc 207 but haven't been validated with
   a training run.

3. **No OOM stress test for BATCH_SIZE=2.** The reduction should mitigate OOM but
   hasn't been verified on the target GPU.

---

## Audit Trail

- Branch: `auto/2pct-training-fix-20260520-202419`
- Files changed: 34 (+547, -678)
- Core new file: `core/web_fallback.py`
- Core rewritten file: `src/config.py` (PSR-only -> full POPW multi-task config)
- Generated: 2026-07-11
