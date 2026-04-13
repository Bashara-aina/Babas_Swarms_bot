---
title: "ADR-003: Import Resilience — Lazy Import Strategy"
date: "2026-04-12"
decider: "@planner"
reviewer: "@reviewer"
status: "PROPOSED"
---
# ADR-003: Import Resilience — Lazy Import Strategy

**Date:** 2026-04-12  
**Status:** PROPOSED  
**Decider:** @planner  
**Reviewer:** @reviewer

## Context
Optional dependencies (browser-use, crawl4ai, yt-dlp, faster-whisper, etc.) are imported at module load time. If they're not installed, the bot crashes on startup rather than degrading gracefully.

## Decision
For optional dependencies, use lazy importing at function call site, not at module top-level.

### Before (crashes on import if dep missing):
```python
# At top of file
from tools.deep_research import deep_research  # crashes if crawl4ai missing
```

### After (gracefully degrades):
```python
async def run_deep_research(topic: str) -> str:
    try:
        from tools.deep_research import deep_research
    except ImportError:
        return "Deep research unavailable: crawl4ai not installed"
    return await deep_research(topic)
```

## Scope
Files with optional dependencies:
1. `tools/deep_research.py` — crawl4ai, browser-use
2. `tools/video.py` — yt-dlp, faster-whisper
3. `handlers/media_tools.py` — ffmpeg, yt-dlp
4. `core/skills/builtin/research.py` — brave-search
5. `tools/documents.py` — python-pptx, ebooklib, Pillow

## Required Dependencies (must be installed)
These should remain hard imports:
- aiogram
- litellm
- aiosqlite
- chromadb
- pytz

## Consequences
**Pros:**
- Bot starts even if some tools unavailable
- Clear error messages to users when feature is missing
- No cascade failures from missing optional deps

**Cons:**
- First call to optional feature has slight latency (import time)
- Error only surfaces at call time, not startup

## Quality Gate
Add startup check: `LEGION_OPTIONAL_DEPS_CHECK=1` to verify all optional deps and report status.
