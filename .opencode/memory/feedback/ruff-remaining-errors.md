---
name: ruff-remaining-errors
description: Remaining ruff lint errors across codebase
type: feedback
---

# Ruff Remaining Errors (2026-04-22)

## F841 (unused variables)
| File | Line | Variable |
|------|------|----------|
| `.claude/skills/session-status.py` | 114 | `jst` |
| `.claude/skills/swarm.py` | 98 | `task_tokens` |
| `.wiki/_scripts/batch_fix_wikilinks.py` | 138 | `target_parts` |
| `.wiki/_scripts/batch_fix_wikilinks.py` | 147 | `from_rel` |
| `.wiki/_scripts/session_synthesizer.py` | 332 | `frontmatter_raw` |

## E741 (ambiguous variable name)
| File | Line | Variable |
|------|------|----------|
| `.wiki/_scripts/session_synthesizer.py` | 182 | `l` |

## invalid-syntax (indentation error)
| File | Line | Issue |
|------|------|-------|
| `.wiki/tools/openaugi/tests/test_vault_adapter.py` | 32+ | Class body not indented — multiple functions |

## Quick Fix Commands

```bash
# F841 — remove unused variable assignments (these are simple deletes)
sed -i '/^    jst = /d' .claude/skills/session-status.py
sed -i '/^    task_tokens = /d' .claude/skills/swarm.py
sed -i '/^                target_parts = /d' .wiki/_scripts/batch_fix_wikilinks.py
sed -i '/^                    from_rel = /d' .wiki/_scripts/batch_fix_wikilinks.py
sed -i '/^        frontmatter_raw = /d' .wiki/_scripts/session_synthesizer.py

# E741 — rename `l` to `line_` in list comprehension
# session_synthesizer.py line 182: change `l` → `line_`

# invalid-syntax — fix indentation in test_vault_adapter.py
# Each method under TestRegexExtraction needs 4-space indent
```

**Why:** Keeps codebase clean and prevents CI failures on new PRs.
**How to apply:** Run `ruff check .` and fix each file. The `.wiki/` scripts are low-risk, the `.claude/skills/` files are part of the OpenCode system.