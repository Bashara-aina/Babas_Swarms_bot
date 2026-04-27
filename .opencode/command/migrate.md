---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <from-system> <to-system>
description: "Migrate code from one pattern or system to another. Args: source, target."
---

# /migrate — Pattern migration

Migrate code from one pattern or system to another in swarm-bot.

## Usage
```
/migrate print-based-logging to structlog
/migrate legacy-handler to aiogram-3
/migrate callback-based-async to await-async
```

## Migration Types

### Handler Pattern Migration
Old: callback-based Telegram handlers
New: aiogram 3.x router decorators

### Logging Migration
Old: `print()` statements
New: `structlog` with structured context

### Async Pattern Migration
Old: `asyncio.coroutine` + `@asyncio.coroutine`
New: `async def` + `await`

### LLM Pattern Migration
Old: direct openai calls
New: llm_client.py with fallback chain

## Workflow
```
1. Identify migration scope
2. Find all occurrences
3. Create migration map
4. Apply changes file by file
5. Verify tests still pass
```

## Constraints
- Always run tests after migration
- Migrate incrementally, not all at once
- Preserve existing test coverage
- Update wiki if architecture changes
