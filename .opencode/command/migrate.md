---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [direction] | up | down | status
description: Run database migrations for episodic_store, graphiti, or mem0. NEVER run on production without backup.
---

# /migrate — Database Migration Command

## STEP 1 — Identify Migration System

Check which stores need migration:
```bash
ls core/memory/
grep -r "aiosqlite\|sqlite" --include="*.py" core/memory/ | head -5
```

## STEP 2 — Run Migration

For direction=up:
```bash
# Check current schema version
python -c "import sqlite3; c=sqlite3.connect('data/episodic.db'); print(c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())" 2>/dev/null

# Run any pending migrations
python -c "
import asyncio, aiosqlite
async def migrate():
    async with aiosqlite.connect('data/episodic.db') as db:
        # Add migration logic here
        pass
asyncio.run(migrate())
"
```

For direction=down:
- **NEVER run down migrations on production without explicit user confirmation**

For direction=status:
```bash
python -c "import sqlite3; c=sqlite3.connect('data/episodic.db'); print([r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()])"
```

## STEP 3 — Verify

After migration:
```bash
python -c "from core.memory.episodic_store import EpisodicStore; print('episodic_store ok')"
python -c "from core.memory.memory_manager import LegionMemoryFacade; print('memory_facade ok')"
```

## STEP 4 — Backup Before Production

On production:
```bash
cp data/episodic.db "data/episodic.db.backup-$(date +%Y%m%d-%H%M%S)"
cp data/beliefs.json "data/beliefs.json.backup-$(date +%Y%m%d-%H%M%S)"
```
