---
title: Review 2026 04 14 Wiki Path Fix
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Loop: #1 (first review)'
wikilinks: []
confidence: medium
source: research
---
## Review: wiki-path-fix (split-brain wiki path wiki/ → .wiki/)
Date: 2026-04-14
Reviewer: @reviewer
Loop: #1 (first review)

### Independent Verification

```bash
$ git diff --stat HEAD
 core/wiki_loader.py         | 4 ++--
 core/wiki_quality_gate.py   | 2 +-
 core/wiki_scheduler.py      | 8 ++++++--
 [plus workspace state files: .obsidian, submodules, etc.]

$ python -m py_compile core/wiki_loader.py core/wiki_quality_gate.py core/wiki_scheduler.py
Syntax OK
```

**Verified line-level changes:**
- `core/wiki_loader.py:12` → `WIKI_DIR = Path("/home/newadmin/swarm-bot/.wiki")`
- `core/wiki_quality_gate.py:28` → `WIKI_DIR = Path("/home/newadmin/swarm-bot/.wiki")`
- `core/wiki_scheduler.py:30` → `WIKI_DIR = Path("/home/newadmin/swarm-bot/.wiki")`

**Import sorting verified** (wiki_loader.py lines 6-10):
```python
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional
```
stdlib sorted correctly.

**No remaining old wiki/ paths found:**
```bash
$ grep -r "swarm-bot/wiki" --include="*.py"
(No matches)
```

### ✅ Passed
- [x] All 3 Python files compile without syntax errors
- [x] All 3 WIKI_DIR constants correctly point to `/home/newadmin/swarm-bot/.wiki`
- [x] Imports properly sorted (stdlib → third-party → local pattern, though all stdlib here)
- [x] No hardcoded API keys, tokens, or secrets
- [x] No `.env` files modified
- [x] No remaining references to old `wiki/` path in Python files
- [x] `.opencode/agents/wikibot.md` verified unchanged (pre-existing correct state)

### ⚠️ Warnings (non-blocking)
- **Workspace state noise**: git status shows `.wiki/.obsidian/`, submodules, and `data/user_profile.json` as modified. These are NOT code changes from this task — they appear to be pre-existing workspace state (Obsidian editor files, uncommitted submodule content). While not blockers, @worker should not commit these.

### ❌ Blockers
None.

### Decision
**APPROVED ✅** — All 3 targeted files correctly fixed. Task complete.

---

### Loop Status
This is loop **#1** of 3 maximum. No blockers found.

### Post-Approval Reminder
Ready for git commit. Run:
```bash
git add -A && git commit -m "fix: unify wiki path from wiki/ to .wiki/ across core modules"
```

**Note**: Consider using `git add core/wiki_loader.py core/wiki_quality_gate.py core/wiki_scheduler.py` to commit ONLY the code changes, excluding workspace noise (.obsidian, submodules, user_profile.json).
